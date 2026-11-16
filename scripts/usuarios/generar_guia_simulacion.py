"""Genera los PDF de la guía de simulación (sesiones de uso del panel) desde sus fuentes en `docs/usuarios/guia_simulacion/`.

Uso, desde la raíz del repositorio:
    python scripts/usuarios/generar_guia_simulacion.py [--perfil completa|participante|ambas] [--salida CARPETA] [--solo-html]

Qué hace: une las partes de la guía (un archivo `.md` por parte), resuelve las inclusiones (`{{incluir: ruta#seccion}}`, `{{codigo: ruta}}`) que traen del resto de `docs/` los hechos que ya existen, convierte
el Markdown a HTML con un conversor propio (tablas, listas, bloques de código, imágenes con recorte y enlaces), arma un índice con enlaces y, con Edge en modo sin ventana, imprime a PDF A4 con la numeración
de páginas. Escribe `guia_simulacion_completa.pdf` (para quien facilita) y `guia_simulacion_participante.pdf` (solo las partes que no traen las tareas ni sus criterios) en `--salida` (por defecto, `dist/`,
que Git ignora) e imprime el sha256 de cada uno.
Por qué es así: (1) un hecho se escribe una sola vez y la guía lo trae por inclusión, porque dos copias se desactualizan; (2) el PDF del participante no lleva las tareas, porque quien las lee antes de su
sesión ya no puede responderlas de primera vez; (3) el conversor es propio y el PDF sale del navegador que ya trae Windows 11, porque así no se agrega ninguna dependencia a `requirements.txt`.
Qué NO hace: no modifica ningún archivo de `docs/`, no ejecuta el proyecto, no usa la red y no escribe nombres ni valores de configuración: lo que no esté en las fuentes no aparece en el PDF.
"""
import argparse
import base64
import hashlib
import html
import json
import mimetypes
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FUENTES = ROOT / "docs" / "usuarios" / "guia_simulacion"
TITULO = "Guía de simulación: sesiones de uso del panel"
PERFILES = {"completa": ("todos", "facilitador"), "participante": ("todos",)}
NOMBRE_PDF = {"completa": "guia_simulacion_completa.pdf", "participante": "guia_simulacion_participante.pdf"}
INCLUSION = re.compile(r"^\{\{(incluir|codigo): *([^}|#]+?)(?:#([^}|]+?))? *(?:\| *([^}]*))?\}\}[ \t]*$", re.M)
PARA = re.compile(r"^\{\{para: *(todos|facilitador)\}\}\s*\n", re.M)


class ErrorDeGuia(ValueError):
    """Una fuente de la guía tiene una inclusión, un enlace o una imagen que no se puede resolver."""


# ---------------------------------------------------------------------------------------------- utilidades de texto
def ancla(titulo):
    """Ancla de un título como la de los documentos del proyecto: minúsculas, sin signos y con guiones; conserva las tildes."""
    limpio = re.sub(r"[^\w\s-]", "", titulo.strip().lower().replace("`", ""))
    return re.sub(r"\s+", "-", limpio).strip("-")


def _escapar(texto):
    """Escapa `&`, `<` y `>` (las comillas no hace falta: el texto nunca va dentro de un atributo)."""
    return html.escape(texto, quote=False)


def _ruta_de_la_raiz(ruta):
    """`ruta` como texto relativo a la raíz del repositorio y con `/`."""
    return Path(ruta).resolve().relative_to(ROOT).as_posix()


def _normalizar(destino, base):
    """Destino de un enlace o una imagen relativo a `base` convertido a «/ruta desde la raíz»; las direcciones web y las anclas no se tocan."""
    if re.match(r"^(https?:|#|/)", destino):
        return destino
    ruta, almohadilla, ancla_ = destino.partition("#")
    absoluta = (Path(base) / ruta).resolve()
    try:
        return "/" + absoluta.relative_to(ROOT).as_posix() + (almohadilla + ancla_)
    except ValueError as e:
        raise ErrorDeGuia(f"el destino «{destino}» sale de la raíz del repositorio") from e


def _reescribir_destinos(texto, base):
    """Convierte los destinos relativos de enlaces e imágenes de un texto incluido para que sigan valiendo fuera de su archivo."""
    return re.sub(r"(!?\[[^\]]*\]\()([^)\s]+)(\))", lambda m: m.group(1) + _normalizar(m.group(2), base) + m.group(3), texto)


# ---------------------------------------------------------------------------------------------- inclusiones
def seccion(texto, slug, origen=""):
    """Cuerpo de la sección cuyo título tiene ese ancla: desde la línea siguiente al título hasta el próximo título del mismo nivel o superior (o el fin)."""
    lineas, dentro, nivel, salida, en_codigo = texto.split("\n"), False, 0, [], False
    for linea in lineas:
        if linea.startswith("```"):
            en_codigo = not en_codigo
        m = None if en_codigo else re.match(r"^(#{1,6}) +(.*)$", linea)
        if m and not dentro and ancla(m.group(2)) == slug:
            dentro, nivel = True, len(m.group(1))
            continue
        if dentro and m and len(m.group(1)) <= nivel:
            break
        if dentro:
            salida.append(linea)
    if not dentro:
        raise ErrorDeGuia(f"no existe la sección «{slug}» en {origen or 'el texto'}")
    return "\n".join(salida).strip("\n")


def _filtrar_filas(cuerpo, filtros):
    """Deja de una tabla el encabezado y las filas que contienen alguno de los textos; el resto del cuerpo queda igual."""
    salida, vistas = [], 0
    for linea in cuerpo.split("\n"):
        if linea.startswith("|"):
            vistas += 1
            if vistas <= 2 or any(f in linea for f in filtros):
                salida.append(linea)
        else:
            vistas = 0
            salida.append(linea)
    if len(salida) <= 2 and any(l.startswith("|") for l in salida):
        raise ErrorDeGuia(f"ninguna fila de la tabla contiene {filtros}")
    return "\n".join(salida)


def _desplazar_titulos(cuerpo, n):
    """Baja `n` niveles los títulos de un texto incluido, para que no compitan con los de la parte que lo trae."""
    return re.sub(r"^(#{1,6}) ", lambda m: "#" * min(6, len(m.group(1)) + n) + " ", cuerpo, flags=re.M)


def resolver_inclusiones(texto, profundidad=0):
    """Reemplaza cada `{{incluir: ruta#seccion | filas: a; b | nivel: 2}}` y `{{codigo: ruta | lenguaje}}` por el contenido que traen; falla si algo no existe."""
    if profundidad > 3:
        raise ErrorDeGuia("inclusiones anidadas de más")

    def reemplazo(m):
        tipo, ruta, slug, opciones = m.group(1), m.group(2).strip(), m.group(3), (m.group(4) or "").strip()
        archivo = ROOT / ruta
        if not archivo.is_file():
            raise ErrorDeGuia(f"la inclusión apunta a un archivo que no existe: {ruta}")
        contenido = archivo.read_text(encoding="utf-8").replace("\r\n", "\n")
        if tipo == "codigo":
            # `{{codigo: ruta | lenguaje | lineas: 1-4}}`: el lenguaje y, si se pide, solo ese rango de líneas (la guía muestra el encabezado y un par de filas, no el archivo entero)
            piezas = [x.strip() for x in opciones.split("|")]
            lenguaje = next((x for x in piezas if x and ":" not in x), "")
            rango = next((x.split(":", 1)[1].strip() for x in piezas if x.startswith("lineas:")), None)
            lineas_archivo = contenido.rstrip("\n").split("\n")
            if rango:
                a, b = (int(v) for v in rango.split("-"))
                lineas_archivo = lineas_archivo[a - 1:b]
            return f"```{lenguaje}\n" + "\n".join(lineas_archivo) + "\n```"
        cuerpo = seccion(contenido, slug, ruta) if slug else contenido
        ajustes = dict(x.split(":", 1) for x in re.split(r" *\| *", opciones) if ":" in x)
        if ajustes.get("solo", "").strip() == "tablas":
            cuerpo = "\n".join(l for l in cuerpo.split("\n") if l.startswith("|"))      # a veces solo hace falta la tabla y no los párrafos que la rodean
        if "filas" in ajustes:
            cuerpo = _filtrar_filas(cuerpo, [f.strip() for f in ajustes["filas"].split(";") if f.strip()])
        if "nivel" in ajustes:
            cuerpo = _desplazar_titulos(cuerpo, int(ajustes["nivel"]))
        return resolver_inclusiones(_reescribir_destinos(cuerpo, archivo.parent), profundidad + 1)
    return INCLUSION.sub(reemplazo, texto)


# ---------------------------------------------------------------------------------------------- Markdown a HTML
def _imagen(alt, destino, recorte, base):
    """Etiqueta `<img>` con la imagen incrustada (data URI); con `recorte=x,y,ancho,alto` solo se ve esa parte, sin librerías de imágenes."""
    ruta = (ROOT / destino[1:]) if destino.startswith("/") else (Path(base) / destino)
    ruta = ruta.resolve()
    if not ruta.is_file() or ROOT not in ruta.parents:
        raise ErrorDeGuia(f"la imagen no existe dentro del repositorio: {destino}")
    tipo = mimetypes.guess_type(ruta.name)[0] or "application/octet-stream"
    datos = f"data:{tipo};base64," + base64.b64encode(ruta.read_bytes()).decode("ascii")
    if recorte:
        x, y, w, h = (int(v) for v in recorte)
        return f'<span class="recorte" style="width:{w}px;height:{h}px"><img src="{datos}" alt="{_escapar(alt)}" style="left:-{x}px;top:-{y}px"></span>'
    return f'<img src="{datos}" alt="{_escapar(alt)}">'


def _enlace(texto, destino):
    """Enlace web o ancla interna; un enlace a un archivo del repositorio no sirve en un PDF y se deja como texto con su ruta."""
    if destino.startswith("#"):
        return f'<a href="#{destino[1:]}">{texto}</a>'
    if re.match(r"^https?:", destino):
        return f'<a href="{destino}">{texto}</a>'
    ruta = destino.partition("#")[0].lstrip("/")
    if not (ROOT / ruta).exists():
        raise ErrorDeGuia(f"el enlace apunta a algo que no existe: {destino}")
    return f'{texto} (<code>{_escapar(ruta)}</code>)'


def en_linea(texto, base=FUENTES):
    """Convierte el Markdown de una línea o un párrafo: código, imágenes, enlaces, negrita y cursiva."""
    codigos = []

    def guardar(m):
        codigos.append(m.group(1))
        return f"\x00{len(codigos) - 1}\x00"
    texto = _escapar(re.sub(r"`([^`]+)`", guardar, texto))
    texto = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)(?:\{recorte=(\d+),(\d+),(\d+),(\d+)\})?", lambda m: _imagen(m.group(1), m.group(2), m.groups()[2:] if m.group(3) else None, base), texto)
    texto = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: _enlace(m.group(1), _normalizar(m.group(2), base)), texto)
    texto = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", texto)
    texto = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", texto)
    texto = re.sub(r"(?<!\w)_(?!\s)(.+?)(?<!\s)_(?!\w)", r"<em>\1</em>", texto)
    return re.sub(r"\x00(\d+)\x00", lambda m: "<code>" + _escapar(codigos[int(m.group(1))]) + "</code>", texto)


def _celdas(linea):
    """Celdas de una fila de tabla; una barra dentro de un trozo de código o escrita como `\\|` no separa celdas."""
    linea, celdas, actual, en_codigo, i = linea.strip().strip("|"), [], "", False, 0
    while i < len(linea):
        c = linea[i]
        if c == "`":
            en_codigo = not en_codigo
        if c == "\\" and linea[i + 1:i + 2] == "|":
            actual += "|"
            i += 2
            continue
        if c == "|" and not en_codigo:
            celdas.append(actual.strip())
            actual = ""
        else:
            actual += c
        i += 1
    celdas.append(actual.strip())
    return celdas


def _tabla(lineas, base):
    """HTML de una tabla de Markdown (encabezado, separador y filas)."""
    cab = _celdas(lineas[0])
    filas = [_celdas(l) for l in lineas[2:]]
    out = ["<table>", "<thead><tr>" + "".join(f"<th>{en_linea(c, base)}</th>" for c in cab) + "</tr></thead>", "<tbody>"]
    out += ["<tr>" + "".join(f"<td>{en_linea(c, base)}</td>" for c in f) + "</tr>" for f in filas]
    return "\n".join(out + ["</tbody>", "</table>"])


ITEM = re.compile(r"^(\s*)([-*]|\d+\.)\s+(.*)$")


def _lista(lineas, base):
    """HTML de una lista (con listas anidadas por sangría y casillas `[ ]`/`[x]`)."""
    pila, salida = [], []  # cada elemento de la pila: (sangría, etiqueta)

    def cerrar_hasta(sangria):
        while pila and pila[-1][0] > sangria:
            salida.append("</li></" + pila.pop()[1] + ">")
    abierto = False
    for linea in lineas:
        m = ITEM.match(linea)
        if m:
            sangria, marca, texto = len(m.group(1).replace("\t", "    ")), m.group(2), m.group(3)
            etiqueta = "ol" if marca[0].isdigit() else "ul"
            cerrar_hasta(sangria)
            if pila and pila[-1][0] == sangria and pila[-1][1] != etiqueta:
                salida.append("</li></" + pila.pop()[1] + ">")      # al mismo nivel cambia de viñetas a numerada (o al revés)
                salida.append(f"<{etiqueta}>")
                pila.append((sangria, etiqueta))
            elif pila and pila[-1][0] == sangria:
                salida.append("</li>")
            elif not pila or sangria > pila[-1][0]:
                salida.append(f"<{etiqueta}>")
                pila.append((sangria, etiqueta))
            casilla = re.match(r"^\[( |x)\] +(.*)$", texto)
            if casilla:
                salida.append('<li class="casilla"><span class="caja">' + ("&#9745;" if casilla.group(1) == "x" else "&#9744;") + "</span> " + en_linea(casilla.group(2), base))
            else:
                salida.append("<li>" + en_linea(texto, base))
            abierto = True
        elif abierto:
            salida.append(" " + en_linea(linea.strip(), base))
    cerrar_hasta(-1)
    return "\n".join(salida)


def md_a_html(texto, base=FUENTES, ids=None):
    """Convierte un texto Markdown a HTML: títulos con ancla, párrafos, listas, tablas, citas, bloques de código, reglas, saltos de página, imágenes y enlaces."""
    ids = ids if ids is not None else {}
    lineas, i, bloques, continuo = texto.replace("\r\n", "\n").split("\n"), 0, [], False
    while i < len(lineas):
        linea = lineas[i]
        if not linea.strip():
            i += 1
        elif linea.startswith("```"):
            lenguaje, i, codigo = linea[3:].strip(), i + 1, []
            while i < len(lineas) and not lineas[i].startswith("```"):
                codigo.append(lineas[i])
                i += 1
            i += 1
            cuerpo_codigo = _escapar("\n".join(codigo))
            if lenguaje == "csv":
                cuerpo_codigo = cuerpo_codigo.replace(",", ",<wbr>")      # una fila de CSV es una sola línea larga: así se corta después de una coma y no en mitad de una palabra
            bloques.append(f'<pre><code class="{_escapar(lenguaje)}">' + cuerpo_codigo + "</code></pre>")
        elif re.match(r"^#{1,6} ", linea):
            nivel, titulo = len(linea) - len(linea.lstrip("#")), linea.lstrip("#").strip()
            base_id = ancla(titulo) or "seccion"
            ids[base_id] = ids.get(base_id, 0) + 1
            id_ = base_id if ids[base_id] == 1 else f"{base_id}-{ids[base_id]}"
            clase = ' class="continuo"' if continuo else ""
            continuo = False
            bloques.append(f'<h{nivel} id="{id_}"{clase}>{en_linea(titulo, base)}</h{nivel}>')
            i += 1
        elif linea.strip() == "{{sin-salto}}":
            continuo = True      # la parte siguiente sigue en la misma página que la anterior: las partes cortas no dejan media hoja en blanco
            i += 1
        elif linea.strip() == "{{salto}}":
            bloques.append('<div class="salto"></div>')
            i += 1
        elif re.match(r"^(-{3,}|\*{3,})$", linea.strip()):
            bloques.append("<hr>")
            i += 1
        elif linea.startswith("|") and i + 1 < len(lineas) and re.match(r"^\|[\s:|-]+\|?$", lineas[i + 1].strip()):
            fin = i + 2
            while fin < len(lineas) and lineas[fin].startswith("|"):
                fin += 1
            bloques.append(_tabla(lineas[i:fin], base))
            i = fin
        elif linea.startswith(">"):
            citado = []
            while i < len(lineas) and lineas[i].startswith(">"):
                citado.append(lineas[i][1:].lstrip(" "))
                i += 1
            bloques.append("<blockquote>" + md_a_html("\n".join(citado), base, ids) + "</blockquote>")
        elif ITEM.match(linea):
            fin = i
            while fin < len(lineas) and lineas[fin].strip() and (ITEM.match(lineas[fin]) or lineas[fin].startswith((" ", "\t"))):
                fin += 1
            bloques.append(_lista(lineas[i:fin], base))
            i = fin
        else:
            parrafo = []
            while i < len(lineas) and lineas[i].strip() and not re.match(r"^(#{1,6} |```|>|\||\{\{salto\}\})", lineas[i]) and not (ITEM.match(lineas[i]) and parrafo):
                parrafo.append(lineas[i].rstrip("\n"))
                i += 1
            bloques.append("<p>" + "<br>".join(en_linea(p.strip(), base) for p in parrafo) + "</p>")
    return "\n".join(bloques)


# ---------------------------------------------------------------------------------------------- partes, índice y documento
def partes(perfil):
    """[(nombre de archivo, texto con inclusiones resueltas)] de las partes que corresponden al perfil, en el orden de sus nombres."""
    permitido = PERFILES[perfil]
    salida = []
    for p in sorted(FUENTES.glob("*.md")):
        if p.name == "README.md":
            continue
        texto = p.read_text(encoding="utf-8").replace("\r\n", "\n")
        m = PARA.match(texto)
        para = m.group(1) if m else "todos"
        if para not in permitido:
            continue
        salida.append((p.name, resolver_inclusiones(texto[m.end():] if m else texto)))
    return salida


def version():
    """Texto de la versión para la portada y el pie: el commit corto si hay git; si no (por ejemplo, en el zip), lo dice."""
    try:
        # se exige que la raíz de git sea la del proyecto: un zip descomprimido dentro de otro repositorio no debe heredar su commit
        arriba = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
        if arriba.returncode != 0 or Path(arriba.stdout.strip()).resolve() != ROOT:
            return "sin versión de git"
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
        return f"commit {r.stdout.strip()}" if r.returncode == 0 and r.stdout.strip() else "sin versión de git"
    except (OSError, subprocess.SubprocessError):
        return "sin versión de git"


ESTILO = """
@page { size: A4; margin: 15mm 15mm 18mm 15mm; }
* { box-sizing: border-box; }
body { font-family: "Segoe UI", Arial, sans-serif; font-size: 10pt; line-height: 1.38; color: #1b1b1b; }
h1 { font-size: 18pt; margin: 0 0 4mm; padding-bottom: 2mm; border-bottom: 2px solid #1f4e79; color: #1f4e79; page-break-before: always; page-break-after: avoid; }
h1.continuo { page-break-before: auto; margin-top: 9mm; }
h1.portada-titulo { page-break-before: avoid; border: none; font-size: 24pt; margin-top: 8mm; }
nav.indice h1 { page-break-before: avoid; margin-top: 12mm; }
h2 { font-size: 13pt; margin: 5.5mm 0 1.8mm; color: #1f4e79; page-break-after: avoid; }
h3 { font-size: 11.5pt; margin: 5mm 0 1.5mm; page-break-after: avoid; }
p, li { orphans: 3; widows: 3; }
table { border-collapse: collapse; width: 100%; margin: 2.5mm 0; font-size: 9.2pt; page-break-inside: auto; }
tr { page-break-inside: avoid; }
th, td { border: 1px solid #9aa5b1; padding: 1.1mm 2mm; vertical-align: top; text-align: left; }
th { background: #e8eef5; }
pre { background: #f3f4f6; border: 1px solid #d0d5dc; border-radius: 3px; padding: 2.5mm 3mm; font-size: 9pt; white-space: pre-wrap; overflow-wrap: break-word; page-break-inside: avoid; }
code { font-family: Consolas, "Courier New", monospace; font-size: 9.3pt; background: #f1f2f4; padding: 0 1mm; border-radius: 2px; word-break: break-word; }
pre code { background: none; padding: 0; font-size: 9pt; }
blockquote { margin: 3mm 0; padding: 2mm 4mm; border-left: 4px solid #1f4e79; background: #f2f6fb; page-break-inside: avoid; }
blockquote p { margin: 1mm 0; }
img { max-width: 100%; border: 1px solid #c9d0d8; }
.recorte { display: inline-block; position: relative; overflow: hidden; border: 1px solid #c9d0d8; max-width: 100%; }
.recorte img { position: absolute; max-width: none; border: none; }
ul, ol { padding-left: 6mm; margin: 2mm 0; }
li.casilla { list-style: none; margin-left: -5mm; }
.caja { font-size: 13pt; line-height: 1; }
.salto { page-break-after: always; }
nav.indice ul { list-style: none; padding-left: 0; columns: 2; column-gap: 9mm; }
nav.indice li { break-inside: avoid; }
nav.indice li.n2 { margin-left: 6mm; font-size: 10pt; }
nav.indice a { text-decoration: none; color: #1b1b1b; }
.portada-sub { font-size: 12pt; color: #444; margin-top: 3mm; }
.portada-version { margin-top: 4mm; color: #555; font-size: 10pt; }
"""


def indice(html_cuerpo):
    """Índice con enlaces a partir de los títulos de nivel 1 y 2 del documento ya convertido."""
    items = []
    for m in re.finditer(r'<h([12]) id="([^"]+)"[^>]*>(.*?)</h\1>', html_cuerpo):      # el título puede llevar `class="continuo"` después del id
        if m.group(2) == "titulo-de-la-guia":
            continue
        items.append(f'<li class="n{m.group(1)}"><a href="#{m.group(2)}">{re.sub(r"<[^>]+>", "", m.group(3))}</a></li>')
    return '<nav class="indice"><h1 id="indice">Índice</h1><ul>' + "".join(items) + "</ul></nav>"


def construir_html(perfil, base=FUENTES):
    """Documento HTML completo (portada, índice y partes) de un perfil; el mismo texto produce siempre el mismo HTML."""
    ids, cuerpos = {}, []
    for _, texto in partes(perfil):
        cuerpos.append(md_a_html(texto, base, ids))
    cuerpo = "\n".join(cuerpos)
    para = "quien facilita las sesiones (incluye las tareas)" if perfil == "completa" else "quien participa en una sesión (sin las tareas)"
    portada = (f'<h1 class="portada-titulo" id="titulo-de-la-guia">{_escapar(TITULO)}</h1><p class="portada-sub">Para {para}.</p>'
               f'<p class="portada-sub">Sesiones de uso del panel entre las personas del equipo: modo mínimo del proyecto (pipeline, API y panel con SQLite).</p>'
               f'<p class="portada-version">Versión: {_escapar(version())}</p>')
    return f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>{_escapar(TITULO)}</title><style>{ESTILO}</style></head><body>{portada}{indice(cuerpo)}{cuerpo}</body></html>'


# ---------------------------------------------------------------------------------------------- PDF con Edge
def parametros_pdf(pie):
    """Parámetros de `Page.printToPDF`: A4, fondos, sin encabezado y con pie con el texto y «página x de y» (porque el navegador numera con su propia plantilla)."""
    plantilla = ('<div style="font-size:8px;width:100%;padding:0 16mm;color:#555;display:flex;justify-content:space-between;">'
                 f"<span>{_escapar(pie)}</span><span>Página <span class=\"pageNumber\"></span> de <span class=\"totalPages\"></span></span></div>")
    return {"displayHeaderFooter": True, "headerTemplate": "<div></div>", "footerTemplate": plantilla, "printBackground": True, "preferCSSPageSize": True}


def _edge():
    """Ruta de Edge (o de Chrome) a partir de las variables de entorno de Windows, sin escribir ninguna ruta local en el código."""
    for var in ("ProgramFiles(x86)", "ProgramFiles", "LocalAppData"):
        base = os.environ.get(var)
        for rel in (Path("Microsoft/Edge/Application/msedge.exe"), Path("Google/Chrome/Application/chrome.exe")):
            if base and (Path(base) / rel).is_file():
                return str(Path(base) / rel)
    raise SystemExit("no se encontró Edge ni Chrome; instale uno de los dos o use --solo-html y abra el HTML en un navegador")


def pdf_con_edge(ruta_html, ruta_pdf, pie):
    """Imprime un HTML a PDF con Edge sin ventana, por el protocolo de DevTools (la biblioteca `websockets` ya está en `requirements.txt`)."""
    from websockets.sync.client import connect
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        puerto = s.getsockname()[1]
    with tempfile.TemporaryDirectory() as perfil:
        proceso = subprocess.Popen([_edge(), "--headless=new", "--disable-gpu", f"--user-data-dir={perfil}", f"--remote-debugging-port={puerto}", "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            destino = None
            for _ in range(80):
                try:
                    destino = next(t for t in json.loads(urllib.request.urlopen(f"http://127.0.0.1:{puerto}/json/list", timeout=3).read()) if t["type"] == "page")
                    break
                except (OSError, StopIteration):
                    time.sleep(0.5)
            if destino is None:
                raise SystemExit("Edge no respondió por el puerto de depuración")
            with connect(destino["webSocketDebuggerUrl"], max_size=None, open_timeout=20) as ws:
                contador = [0]

                def llamar(metodo, **params):
                    contador[0] += 1
                    ws.send(json.dumps({"id": contador[0], "method": metodo, "params": params}))
                    while True:
                        r = json.loads(ws.recv(timeout=120))
                        if r.get("id") == contador[0]:
                            if "error" in r:
                                raise SystemExit(f"{metodo}: {r['error'].get('message')}")
                            return r.get("result", {})
                llamar("Page.enable")
                llamar("Page.navigate", url=Path(ruta_html).resolve().as_uri())
                for _ in range(120):
                    listo = llamar("Runtime.evaluate", expression="document.readyState === 'complete'", returnByValue=True)["result"].get("value")
                    if listo:
                        break
                    time.sleep(0.5)
                time.sleep(1.0)      # las imágenes incrustadas se decodifican justo después de `complete`
                pdf = llamar("Page.printToPDF", **parametros_pdf(pie))
            Path(ruta_pdf).write_bytes(base64.b64decode(pdf["data"]))
        finally:
            proceso.terminate()
            try:
                proceso.wait(timeout=15)
            except subprocess.TimeoutExpired:
                proceso.kill()


def main(argv=None):
    """Genera los PDF pedidos y escribe el sha256 de cada uno."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--perfil", choices=("completa", "participante", "ambas"), default="ambas", help="qué guía generar (por defecto, las dos)")
    ap.add_argument("--salida", type=Path, default=ROOT / "dist", help="carpeta de salida (por defecto, dist/, que Git ignora)")
    ap.add_argument("--solo-html", action="store_true", help="escribe solo el HTML (para revisarlo o imprimirlo desde otro navegador)")
    args = ap.parse_args(argv)
    args.salida.mkdir(parents=True, exist_ok=True)
    for perfil in (["completa", "participante"] if args.perfil == "ambas" else [args.perfil]):
        documento = construir_html(perfil)
        ruta_html = args.salida / NOMBRE_PDF[perfil].replace(".pdf", ".html")
        ruta_html.write_text(documento, encoding="utf-8", newline="\n")
        if args.solo_html:
            print(f"{ruta_html.name}: HTML escrito")
            continue
        ruta_pdf = args.salida / NOMBRE_PDF[perfil]
        pdf_con_edge(ruta_html, ruta_pdf, f"{TITULO} · {version()}")
        ruta_html.unlink()
        print(f"{ruta_pdf.name} | {ruta_pdf.stat().st_size} bytes | sha256 {hashlib.sha256(ruta_pdf.read_bytes()).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
