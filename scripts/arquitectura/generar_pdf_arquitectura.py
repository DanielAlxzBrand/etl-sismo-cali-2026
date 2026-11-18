"""Genera el PDF del documento de arquitectura y de sus registros de decisión (ADR) desde los archivos de Markdown de `docs/arquitectura/`.

Uso, desde la raíz del repositorio:
    python scripts/arquitectura/generar_pdf_arquitectura.py [--salida CARPETA] [--nombre ARCHIVO.pdf] [--solo-html | --verificar]

Qué hace: une el documento (`arquitectura_del_sistema.md`) y los ADR (`adr/adr-nnn_*.md`) en una sola página HTML con el conversor de Markdown de la guía de simulación, arma una portada con los
metadatos de la sección 1, un índice con enlaces y un anexo con los ADR seguidos (el salto de página va solo antes del anexo), y con Edge en modo sin ventana imprime a PDF A4 (por el protocolo DevTools, con la biblioteca `websockets`
que ya está en `requirements.txt`). Escribe `arquitectura_del_sistema_y_adr.pdf` en `--salida` (por defecto `dist/`, que Git ignora) e imprime su sha256.
El PDF lleva marcadores (el esquema del documento: partes, secciones y ADR), enlaces internos entre secciones y ADR, y un pie con el título, la versión, el estado y «página x de y»; el pie sale
también en la portada porque el navegador lo imprime en todas las páginas.
Cómo se convierten los enlaces: un enlace a un ADR o a una sección del documento pasa a ser un enlace interno del PDF; un enlace a cualquier otro archivo del repositorio no sirve en un PDF y se
deja como texto con su ruta desde la raíz, en código.
Por qué es así: (1) el PDF sale del navegador que ya trae Windows 11, así que no se agrega ninguna dependencia a `requirements.txt` (ADR-007); (2) el texto sale de los mismos archivos que vigilan las
pruebas del documento: una sola fuente, sin copias; (3) los diagramas del documento son texto ASCII y se imprimen en monoespacio; además se incrustan dos figuras en gris, `docs/diagramas/arquitectura.png` en la sección 6 y
`docs/diagramas/flujo_dag.png` en la sección 9, con su leyenda «Figura N», sin cambiar los archivos de Markdown; los dos diagramas en color aportados (`docs/diagramas/*_nueva.png`) no se incrustan.
Determinismo: el navegador escribe la fecha de creación y de modificación con los segundos de la ejecución; el script las reescribe con la fecha de la versión del documento (misma longitud, así
que las posiciones del archivo no cambian). Con el mismo texto, el mismo Edge y las mismas fuentes de Windows, dos ejecuciones dan el mismo sha256. En otro equipo o con otro Edge el archivo
puede cambiar, aunque se vea igual (las fuentes quedan incrustadas).
Con `--verificar` genera el PDF dos veces en una carpeta temporal y comprueba que tenga marcadores (uno por título, más el del documento), enlaces internos, las fechas fijadas y el mismo sha256 en
las dos ejecuciones; termina con código 1 si algo falla. Es la comprobación que usan la evidencia EV-117 y la regeneración final: las pruebas del repositorio no abren ningún navegador.
Qué NO hace: no modifica ningún archivo de `docs/`, no usa la red, no incluye nada que no esté en los archivos de Markdown y no firma ni protege el PDF.
"""
import argparse
import base64
import hashlib
import json
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "usuarios"))
import generar_guia_simulacion as gen  # noqa: E402  (conversor de Markdown, índice y estilo de la guía)

DIRECTORIO = ROOT / "docs" / "arquitectura"
DOCUMENTO = DIRECTORIO / "arquitectura_del_sistema.md"
NOMBRE_PDF = "arquitectura_del_sistema_y_adr.pdf"
TITULO_DEL_ANEXO = "Anexo. Registros de decisión (ADR)"
CAMPOS_DE_PORTADA = ("Versión y fecha", "Estado", "Autor y owner técnico", "Revisión de la documentación", "Aprobadores", "Registros de decisión")
FIGURAS = (
    ("6-vista-de-alto-nivel", "docs/diagramas/arquitectura.png", "Arquitectura de alto nivel",
     "Figura 1. Arquitectura de alto nivel: fuentes, pipeline, almacenamiento, servicio y consumo, con Airflow arriba y la calidad y el monitoreo abajo (dibujo en gris generado desde `docs/diagramas/arquitectura.yaml`)."),
    ("9-flujos-detallados", "docs/diagramas/flujo_dag.png", "Flujo del DAG",
     "Figura 2. Flujo del DAG: las cuatro tareas en orden, el disparo con el parámetro `fallo_inducido`, el repositorio en solo lectura, la copia de trabajo y MySQL (dibujo en gris generado desde `docs/diagramas/flujo_dag.yaml`)."),
)
FECHA_DEL_PDF = re.compile(rb"/(CreationDate|ModDate) \(D:\d{14}\+00'00'\)")

ESTILO_EXTRA = """
.portada { page: portada; page-break-after: always; }
@page portada { size: A4; margin: 15mm 15mm 18mm 15mm; }
.portada h1.portada-titulo { font-size: 26pt; margin-top: 28mm; line-height: 1.2; }
.portada table { margin-top: 12mm; font-size: 10pt; }
.portada td:first-child { width: 42mm; font-weight: 600; }
nav.indice li.n2 { margin-left: 4mm; font-size: 9.5pt; }
h2.adr { font-size: 15pt; border-bottom: 1px solid #9aa5b1; padding-bottom: 1.5mm; margin-top: 9mm; }
figure { margin: 3mm 0 4mm; page-break-inside: avoid; }
figure img { display: block; width: 100%; border: 1px solid #c9d0d8; }
figcaption { font-size: 9pt; color: #444; margin-top: 1.5mm; }
pre { font-size: 7.4pt; line-height: 1.15; white-space: pre; overflow: hidden; }
pre code { font-size: 7.4pt; }
"""


# ---------------------------------------------------------------------------------------------- lectura de las fuentes
def archivos_adr(directorio=DIRECTORIO):
    return sorted((directorio / "adr").glob("adr-*.md"))


def metadatos(texto_del_documento):
    """Filas de la tabla de la sección 1 del documento como {campo: valor}."""
    seccion = re.search(r"(?ms)^## 1\. .*?(?=^## 2\. )", texto_del_documento)
    if not seccion:
        raise ValueError("el documento no tiene la sección 1")
    filas = re.findall(r"(?m)^\| ([^|]+?) \| (.+?) \|$", seccion.group(0))
    datos = {c: v for c, v in filas if c not in ("Campo", "---")}
    faltan = [c for c in CAMPOS_DE_PORTADA if c not in datos]
    if faltan:
        raise ValueError(f"la tabla de la sección 1 no trae: {faltan}")
    return datos


def version_y_estado(datos):
    """(versión, fecha, estado) de los metadatos: «0.2, 2026-11-18» y «Revisado»."""
    m = re.fullmatch(r"(\d+\.\d+), (\d{4}-\d{2}-\d{2})", datos["Versión y fecha"])
    if not m:
        raise ValueError(f"la versión y la fecha no tienen la forma «0.2, AAAA-MM-DD»: {datos['Versión y fecha']}")
    return m.group(1), m.group(2), datos["Estado"]


def titulo_de_adr(texto):
    return texto.splitlines()[0].lstrip("# ").strip()


# ---------------------------------------------------------------------------------------------- enlaces
def convertir_enlaces(texto, base, anclas_de_adr):
    """Enlaces relativos de un texto: a un ADR o a una sección del documento, ancla interna; a otro archivo, texto con su ruta en código. Los enlaces con ancla propia (`#...`) y los web no se tocan."""
    def cambiar(m):
        etiqueta, destino = m.group(1), m.group(2)
        if re.match(r"^(https?:|#)", destino):
            return m.group(0)
        ruta, _, ancla_ = destino.partition("#")
        real = (Path(base) / ruta).resolve()
        if real.name in anclas_de_adr and real.parent == (DIRECTORIO / "adr").resolve():
            return f"[{etiqueta}](#{anclas_de_adr[real.name]})"
        if real == DOCUMENTO.resolve():
            return f"[{etiqueta}](#{ancla_})" if ancla_ else f"[{etiqueta}](#titulo-del-documento)"
        if not real.exists():
            raise ValueError(f"el enlace apunta a algo que no existe: {destino}")
        relativa = real.relative_to(ROOT).as_posix() + ("/" if real.is_dir() else "") + (f"#{ancla_}" if ancla_ else "")
        visible = etiqueta.strip("`").rstrip("/")
        if visible in (relativa.rstrip("/"), Path(relativa.split("#")[0]).name, relativa.split("#")[0].rstrip("/")):
            return f"`{relativa}`"
        return f"{etiqueta} (`{relativa}`)"
    return re.sub(r"(?<!\!)\[([^\]]+)\]\(([^)\s]+)\)", cambiar, texto)


# ---------------------------------------------------------------------------------------------- HTML
def insertar_figuras(html_del_documento, figuras=FIGURAS):
    """Agrega cada figura justo después del título de su sección, con la imagen incrustada y su leyenda; falla si la sección no existe."""
    for id_seccion, ruta, alternativo, leyenda in figuras:
        patron = re.compile(rf'(<h2 id="{re.escape(id_seccion)}"[^>]*>.*?</h2>)')
        if not patron.search(html_del_documento):
            raise ValueError(f"no está la sección {id_seccion} para la figura {ruta}")
        figura = f'<figure>{gen._imagen(alternativo, "/" + ruta, None, ROOT)}<figcaption>{gen.en_linea(leyenda)}</figcaption></figure>'
        html_del_documento = patron.sub(lambda m: m.group(1) + figura, html_del_documento, count=1)
    return html_del_documento


def pie_del_pdf(datos):
    version, _, estado = version_y_estado(datos)
    return f"Arquitectura del sistema ETL del sismo de Cali · versión {version} · {estado}"


def portada_html(datos, anclas_de_adr, directorio=DIRECTORIO):
    filas = "".join(f"<tr><td>{gen._escapar(c)}</td><td>{gen.en_linea(convertir_enlaces(datos[c], directorio, anclas_de_adr), directorio)}</td></tr>" for c in CAMPOS_DE_PORTADA)
    return (f'<div class="portada"><h1 class="portada-titulo" id="titulo-de-la-guia">{gen._escapar(datos["Título"] if "Título" in datos else "Arquitectura del sistema")}</h1>'
            f'<p class="portada-sub">Documento de arquitectura y registros de decisión (ADR)</p><table><tbody>{filas}</tbody></table></div>')


def construir_html(directorio=DIRECTORIO, documento=DOCUMENTO):
    """HTML completo: portada, índice, documento y anexo con cada ADR en su página. El mismo texto produce siempre el mismo HTML."""
    texto = Path(documento).read_text(encoding="utf-8").replace("\r\n", "\n")
    datos = metadatos(texto)
    adrs = archivos_adr(directorio)
    textos_adr = {p.name: p.read_text(encoding="utf-8").replace("\r\n", "\n") for p in adrs}
    anclas = {n: gen.ancla(titulo_de_adr(t)) for n, t in textos_adr.items()}
    cuerpo_doc = convertir_enlaces(texto.replace("# Arquitectura del sistema ETL del sismo de Cali", "# Documento de arquitectura del sistema ETL del sismo de Cali", 1), directorio, anclas)
    ids = {"titulo-de-la-guia": 1}
    html_doc = gen.md_a_html(cuerpo_doc, directorio, ids)
    html_doc = html_doc.replace('<h1 id="documento-de-arquitectura-del-sistema-etl-del-sismo-de-cali"', '<h1 id="titulo-del-documento"', 1)
    html_doc = insertar_figuras(html_doc)
    partes = [html_doc, gen.md_a_html(f"# {TITULO_DEL_ANEXO}\n\nLos registros de decisión van uno a continuación del otro y cada uno trae, en este orden: contexto, decisión, consecuencias, las alternativas que se registraron entonces y las que hoy descartamos.", directorio, ids)]
    for nombre, t in textos_adr.items():
        convertido = gen._desplazar_titulos(convertir_enlaces(t, directorio / "adr", anclas), 1)
        html = gen.md_a_html(convertido, directorio / "adr", ids)
        partes.append(re.sub(r'<h2 id="(adr-[^"]+)"', r'<h2 id="\1" class="adr"', html, count=1))
    cuerpo = "\n".join(partes)
    titulo = datos.get("Título", "Arquitectura del sistema")
    return (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>{gen._escapar(titulo)}</title><style>{gen.ESTILO}{ESTILO_EXTRA}</style></head><body>'
            f"{portada_html(datos, anclas, directorio)}{gen.indice(cuerpo)}{cuerpo}</body></html>")


# ---------------------------------------------------------------------------------------------- PDF con Edge
def parametros_del_pdf(pie):
    """Los de la guía de simulación (A4, fondos, pie con el texto y «página x de y») más los marcadores del documento."""
    return {**gen.parametros_pdf(pie), "generateDocumentOutline": True}


def fijar_fechas(datos_del_pdf, fecha):
    """Reescribe la fecha de creación y de modificación del PDF con `fecha` (AAAA-MM-DD, a medianoche UTC) sin cambiar su longitud; falla si no encuentra exactamente las dos."""
    nueva = f"D:{fecha.replace('-', '')}000000+00'00'".encode("ascii")
    encontradas = FECHA_DEL_PDF.findall(datos_del_pdf)
    if len(encontradas) != 2:
        raise ValueError(f"el PDF debía traer la fecha de creación y la de modificación y trae {len(encontradas)} fechas")
    resultado = FECHA_DEL_PDF.sub(lambda m: b"/" + m.group(1) + b" (" + nueva + b")", datos_del_pdf)
    assert len(resultado) == len(datos_del_pdf)
    return resultado


def imprimir_con_edge(ruta_html, pie):
    """Bytes del PDF que Edge imprime desde `ruta_html`, por DevTools y con los marcadores del documento."""
    from websockets.sync.client import connect
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        puerto = s.getsockname()[1]
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as perfil:
        proceso = subprocess.Popen([gen._edge(), "--headless=new", "--disable-gpu", f"--user-data-dir={perfil}", f"--remote-debugging-port={puerto}", "about:blank"],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
                        r = json.loads(ws.recv(timeout=180))
                        if r.get("id") == contador[0]:
                            if "error" in r:
                                raise SystemExit(f"{metodo}: {r['error'].get('message')}")
                            return r.get("result", {})
                llamar("Page.enable")
                llamar("Page.navigate", url=Path(ruta_html).resolve().as_uri())
                for _ in range(120):
                    if llamar("Runtime.evaluate", expression="document.readyState === 'complete'", returnByValue=True)["result"].get("value"):
                        break
                    time.sleep(0.5)
                time.sleep(1.0)
                return base64.b64decode(llamar("Page.printToPDF", **parametros_del_pdf(pie))["data"])
        finally:
            proceso.terminate()
            try:
                proceso.wait(timeout=15)
            except subprocess.TimeoutExpired:
                proceso.kill()


def generar(salida, solo_html=False, nombre=NOMBRE_PDF):
    """Escribe el HTML (y el PDF) en `salida`, con ese `nombre` de PDF, y devuelve (ruta, sha256, bytes)."""
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    html = construir_html()
    ruta_html = salida / nombre.replace(".pdf", ".html")
    ruta_html.write_text(html, encoding="utf-8", newline="\n")
    if solo_html:
        return ruta_html, hashlib.sha256(ruta_html.read_bytes()).hexdigest(), ruta_html.stat().st_size
    datos = metadatos(DOCUMENTO.read_text(encoding="utf-8"))
    _, fecha, _ = version_y_estado(datos)
    pdf = fijar_fechas(imprimir_con_edge(ruta_html, pie_del_pdf(datos)), fecha)
    ruta_pdf = salida / nombre
    ruta_pdf.write_bytes(pdf)
    return ruta_pdf, hashlib.sha256(pdf).hexdigest(), len(pdf)


def inspeccionar_pdf(datos):
    """Lo que se puede leer de un PDF sin una biblioteca de PDF: páginas, títulos (marcadores y el del documento), enlaces y fechas."""
    return {"paginas": len(re.findall(rb"/Type\s*/Page[^s]", datos)), "titulos": len(re.findall(rb"/Title", datos)),
            "enlaces": len(re.findall(rb"/Subtype\s*/Link", datos)), "esquema": b"/Outlines" in datos,
            "fechas": [m.decode("ascii") for m in re.findall(rb"/(?:CreationDate|ModDate) \(([^)]*)\)", datos)]}


def problemas_del_pdf(datos, html, fecha):
    """Lista de problemas de un PDF frente al HTML del que salió (vacía si está bien): marcadores, enlaces, fechas fijadas y páginas."""
    info, errores = inspeccionar_pdf(datos), []
    if not datos.startswith(b"%PDF-"):
        errores.append("no empieza como un PDF")
    if not info["esquema"]:
        errores.append("el PDF no trae marcadores")
    encabezados = len(re.findall(r"<h[1-6][ >]", html))
    if info["titulos"] != encabezados + 1:
        errores.append(f"los marcadores no son uno por título: {info['titulos']} títulos en el PDF y {encabezados} encabezados (más el título del documento)")
    internos = len(re.findall(r'href="#', html))
    if info["enlaces"] < internos:
        errores.append(f"faltan enlaces internos: {info['enlaces']} en el PDF y {internos} en el HTML")
    esperada = f"D:{fecha.replace('-', '')}000000+00'00'"
    if info["fechas"] != [esperada, esperada]:
        errores.append(f"las fechas del PDF no son la de la versión ({esperada}): {info['fechas']}")
    if info["paginas"] < 2:
        errores.append("el PDF tiene menos de dos páginas")
    return errores


def verificar():
    """Genera el PDF dos veces en carpetas temporales y devuelve (problemas, resumen). Cada ejecución abre Edge."""
    datos_doc = metadatos(DOCUMENTO.read_text(encoding="utf-8"))
    _, fecha, _ = version_y_estado(datos_doc)
    problemas, shas, info = [], [], None
    for _ in range(2):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as carpeta:
            ruta, sha, _ = generar(carpeta)
            pdf, html = ruta.read_bytes(), ruta.with_suffix(".html").read_text(encoding="utf-8")
            problemas += problemas_del_pdf(pdf, html, fecha)
            info, _ = inspeccionar_pdf(pdf), shas.append(sha)
    if len(set(shas)) != 1:
        problemas.append(f"dos ejecuciones dieron PDF distintos: {shas}")
    return problemas, {**info, "sha256": shas[0], "iguales": len(set(shas)) == 1}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--salida", type=Path, default=ROOT / "dist", help="carpeta donde se escribe el PDF (por defecto dist/, que Git ignora)")
    ap.add_argument("--nombre", default=NOMBRE_PDF, help="nombre del archivo PDF (por si el anterior está abierto en un visor y no se puede reemplazar)")
    grupo = ap.add_mutually_exclusive_group()
    grupo.add_argument("--solo-html", action="store_true", help="escribe solo el HTML, para revisarlo o imprimirlo desde otro navegador")
    grupo.add_argument("--verificar", action="store_true", help="genera el PDF dos veces en una carpeta temporal y comprueba marcadores, enlaces, fechas y que las dos salidas sean iguales")
    args = ap.parse_args(argv)
    if args.verificar:
        problemas, resumen = verificar()
        print(json.dumps(resumen, ensure_ascii=False))
        for p in problemas:
            print("PROBLEMA:", p)
        raise SystemExit(1 if problemas else 0)
    ruta, sha, tamano = generar(args.salida, args.solo_html, args.nombre)
    print(f"{ruta.name} | {tamano} bytes | sha256 {sha}")


if __name__ == "__main__":
    main()
