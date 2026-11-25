"""Piezas compartidas de la interfaz propia (D115): cabecera, glosario, figura de tasas con intervalos, tablas de detalle, tarjetas, notas, guía y curiosidades, y el documento exportable.

Aquí no se calcula ninguna cifra: cada número llega ya hecho por la API y se escribe con `formato`; las páginas aportan sus textos de `redaccion`. Lo único que se deriva es la posición en pantalla
(la escala de un eje sale de los límites de los datos). Todo texto que viene de los datos pasa por `html.escape` antes de entrar al HTML.
"""
import math
import re
from html import escape

from src.panel import componentes, formato, glosario, tema
from src.panel.frontend import activos

CLASES_MODOS = (("barras", "Barras"), ("puntos", "Puntos e intervalos"), ("tabla", "Tabla"))
PASOS_ESCALA = (1, 2, 5, 10, 20, 25)
MAXIMO_MARCAS = 6
ANCHO_LAMINA, X_LAMINA, PASO_Y, Y_INICIAL = 480, 168, 49, 74
X_ETIQUETA, X_VALOR, Y_TITULO, Y_EJE, RADIO, GROSOR, MEDIA_MARCA, ALTO_MARCA, AJUSTE_TEXTO = 8, 665, 15, 38, 6, 2, 6, 12, 5


def e(valor):
    return escape(str(valor))


def pct(fraccion):
    return None if fraccion is None else fraccion * 100


def negritas(texto):
    """Convierte las negritas de Markdown (**texto**) en <b>; el texto ya viene escapado."""
    return re.sub(r"\*\*(.+?)\*\*", lambda m: "<b>" + m.group(1) + "</b>", texto)


# ---------------------------------------------------------------- escalas
def escala(filas):
    """(tope, marcas) del eje horizontal en porcentaje, desde cero: el menor múltiplo de un paso redondo que cubre el mayor límite superior, con a lo sumo seis tramos."""
    mayor = max([pct(f.get("ic95_sup")) or 0 for f in filas] + [pct(f.get("valor")) or 0 for f in filas] + [0])
    for paso in PASOS_ESCALA:
        tope = max(paso, math.ceil(mayor / paso) * paso)
        if tope / paso <= MAXIMO_MARCAS:
            return tope, list(range(0, tope + 1, paso))
    return PASOS_ESCALA[-1], list(range(0, PASOS_ESCALA[-1] + 1, PASOS_ESCALA[-1]))


def escala_con_signo(minimo, maximo):
    """(inferior, superior, marcas) de un eje que incluye el cero y cubre [minimo, maximo], con a lo sumo seis tramos."""
    for paso in PASOS_ESCALA:
        inferior, superior = math.floor(min(minimo, 0) / paso) * paso, math.ceil(max(maximo, 0) / paso) * paso
        if superior == inferior:
            superior = inferior + paso
        if (superior - inferior) / paso <= MAXIMO_MARCAS:
            return inferior, superior, list(range(inferior, superior + 1, paso))
    paso = PASOS_ESCALA[-1]
    inferior, superior = math.floor(min(minimo, 0) / paso) * paso, max(math.ceil(max(maximo, 0) / paso) * paso, paso)
    return inferior, superior, list(range(inferior, superior + 1, paso))


# ---------------------------------------------------------------- textos de una fila
def frase_fila(fila):
    return (f"De {formato.numero(fila.get('denominador'))} construcciones con clasificación, {formato.numero(fila.get('numerador'))} presentan cambio satelital severo "
            f"({formato.porcentaje(fila.get('valor'))}).")


def lectura_de_fila(fila):
    return (f"{frase_fila(fila)} El intervalo de Wilson al 95 % va de {formato.porcentaje(fila.get('ic95_inf'))} a {formato.porcentaje(fila.get('ic95_sup'))}. "
            f"Faltan {formato.numero(fila.get('n_sin_datos'))} clasificaciones satelitales.")


# ---------------------------------------------------------------- cabecera
def alcance_html(metadata):
    """El mismo texto del recuadro de alcance del panel (`componentes.alcance_markdown`), con las negritas como `<b>`."""
    return '<aside class="alc">' + negritas(e(componentes.alcance_markdown(metadata))) + "</aside>"


def glosario_html(id_pagina, contenido):
    """Glosario de la página: cómo interpretar, los términos del glosario del panel tal como están y las precauciones."""
    conceptos = "".join(f"<b>{e(nombre)}</b><p>{e(definicion)}</p>" for nombre, definicion in glosario.entradas(id_pagina))
    return f"<h3>Cómo interpretar</h3><p>{e(contenido['interpretacion'])}</p><h3>Conceptos</h3>{conceptos}<h3>Precauciones</h3><p>{e(contenido['precauciones'])}</p>"


def cabecera(pagina, grupo, corte, metadata, resumen=""):
    """Barra de ruta, glosario, título, pregunta, resumen opcional (HTML ya armado) y alcance."""
    contenido = activos.contenido(pagina.id)
    return (f'<article class="vista prueba-v3"><header class="barra"><nav aria-label="Ruta actual">{e(grupo)} <span>/</span> <b>{e(pagina.titulo)}</b></nav>'
            f'<div class="util"><span class="corte">Corte de datos: {e(corte)}</span><details class="glos"><summary>Glosario de esta página</summary><div>{glosario_html(pagina.id, contenido)}</div></details></div></header>'
            f'<div class="titular"><div><h1>{e(pagina.titulo)}</h1><p>{e(pagina.pregunta)}</p></div>{resumen}</div>{alcance_html(metadata)}</article>')


# ---------------------------------------------------------------- figura de tasas con intervalos
def _fila_figura(i, fila, etiqueta, tope):
    baja = bool(fila.get("muestra_baja"))
    tasa, inf, sup = (pct(fila.get(k)) for k in ("valor", "ic95_inf", "ic95_sup"))
    grupo = e(etiqueta)
    aviso = componentes.ETIQUETA_BAJA if baja else componentes.ETIQUETA_SUFICIENTE
    marca = f"<small>{e(componentes.ETIQUETA_BAJA.capitalize())}</small>" if baja else ""
    if None in (tasa, inf, sup):
        pos = ""
    else:
        pos = f' style="--tasa:{100 * tasa / tope:.4f}%;--inf:{100 * inf / tope:.4f}%;--rango:{100 * (sup - inf) / tope:.4f}%"'
    ayuda = (f'<span class="ayuda" role="tooltip"><strong>{grupo} · {e(aviso)}</strong>{e(frase_fila(fila))}<br>Tasa {e(formato.porcentaje(fila.get("valor")))}'
             f'<br>Intervalo de Wilson {e(formato.intervalo(fila.get("ic95_inf"), fila.get("ic95_sup")))}<br>{e(formato.numero(fila.get("numerador")))} severos de {e(formato.numero(fila.get("denominador")))} con datos</span>')
    return (f'<label class="dato r{i}{" baja" if baja else ""}"><input type="radio" name="categoria" aria-label="Destacar {grupo}"><span class="etiqueta">{grupo} {marca}</span>'
            f'<span class="trama"{pos}><i class="barra-tasa"></i><i class="banda"></i><i class="intervalo"></i><i class="punto"></i></span>'
            f'<b>{e(formato.porcentaje(fila.get("valor")))}</b><span>{e(formato.intervalo(fila.get("ic95_inf"), fila.get("ic95_sup")))}</span>'
            f'<span>{e(formato.numero(fila.get("numerador")))} de {e(formato.numero(fila.get("denominador")))}</span>{ayuda}</label>')


def figura(filas, etiquetas, titulo, subtitulo):
    """Figura «barras, puntos y tabla» de tasas con su intervalo de Wilson. `filas` trae valor, ic95_inf, ic95_sup, numerador, denominador y muestra_baja."""
    tope, marcas = escala(filas)
    modos = "".join(f'<label><input type="radio" name="vista" value="{valor}"{" checked" if valor == "barras" else ""}><span>{e(texto)}</span></label>' for valor, texto in CLASES_MODOS)
    lineas = "".join(_fila_figura(i, f, etiqueta, tope) for i, (f, etiqueta) in enumerate(zip(filas, etiquetas)))
    ejes = "".join(f"<span>{e(formato.numero(v))}</span>" for v in marcas)
    return (f'<section class="panel figura"><div class="controles"><div><h2>{e(titulo)}</h2><p>{e(subtitulo)}</p></div>'
            f'<fieldset class="modos" aria-label="Vista de resultados">{modos}</fieldset></div>'
            f'<div class="grafico"><p class="leyenda"><span><i></i>{e(componentes.ETIQUETA_SUFICIENTE.capitalize())}</span><span><i></i>{e(componentes.ETIQUETA_BAJA.capitalize())}</span><span><i></i>Intervalo de Wilson 95 %</span></p>'
            f'<div class="rotulos"><span></span><span></span><span>Tasa</span><span>IC de Wilson 95 %</span><span>Severos / con datos</span></div>'
            f'<fieldset class="serie" aria-label="Destacar grupo en la tabla">{lineas}</fieldset>'
            f'<div class="eje"><div>{ejes}</div><b>Cambio satelital severo (%)</b></div></div><p class="pie-tabla">{e(componentes.PIE_INTERVALO)}</p></section>')


def resaltados(cantidad):
    """Reglas que destacan en el detalle la fila elegida en la figura (una por fila)."""
    return "<style>" + "".join(f".analisis:has(.r{i} input:checked) .d{i}{{background:#d9eee5;box-shadow:inset 3px 0 #087a6b}}" for i in range(cantidad)) + "</style>"


# ---------------------------------------------------------------- tablas, tarjetas, notas
def _aviso_ancho(columnas):
    return f'<p class="pie-tabla">{e(componentes.AVISO_TABLA_ANCHA)}</p>' if columnas >= componentes.UMBRAL_COLUMNAS_ANCHAS else ""


def detalle(tabla, filas, titulo, rotulo, clave_columnas, nota=""):
    """Tabla de detalle con las mismas celdas de texto que la del panel original (`tabla`, un DataFrame ya formateado) y la lectura de cada fila (`filas`) al desplegar su rótulo."""
    columnas = list(tabla.columns)
    cabeza = "".join(f'<th scope="col">{e(c)}</th>' for c in columnas)
    cuerpo = []
    for i, (_, fila_tabla) in enumerate(tabla.iterrows()):
        valores = [fila_tabla[c] for c in columnas]
        grupo = f'<details class="lectura-fila" data-fila="{i}"><summary>{e(valores[0])}</summary><p>{e(lectura_de_fila(filas[i]))}</p></details>'
        cuerpo.append(f'<tr class="d{i}"><th scope="row">{grupo}</th>' + "".join(f"<td>{e(v)}</td>" for v in valores[1:]) + "</tr>")
    clave = f'<details class="clave-tabla"><summary>Cómo leer las columnas</summary><p>{e(clave_columnas)}</p></details>'
    pie = f'<p class="pie-tabla">{e(nota)}</p>' if nota else ""
    return (f'<section class="panel detalle"><h2>{e(titulo)}</h2>{clave}{_aviso_ancho(len(columnas))}<div class="scroll" tabindex="0" aria-label="{e(rotulo)}"><table><thead><tr>{cabeza}</tr></thead>'
            f'<tbody>{"".join(cuerpo)}</tbody></table></div>{pie}</section>')


def tabla_simple(tabla, titulo, rotulo, introduccion="", nota=""):
    """Tabla de texto sin lectura por fila (composición, escenarios, catálogos): cada celda es la del DataFrame original."""
    columnas = list(tabla.columns)
    cabeza = "".join(f'<th scope="col">{e(c)}</th>' for c in columnas)
    filas = "".join("<tr>" + f'<th scope="row">{e(fila[columnas[0]])}</th>' + "".join(f"<td>{e(fila[c])}</td>" for c in columnas[1:]) + "</tr>" for _, fila in tabla.iterrows())
    intro = f"<p>{e(introduccion)}</p>" if introduccion else ""
    pie = f'<p class="pie-tabla">{e(nota)}</p>' if nota else ""
    return (f'<section class="panel detalle"><h2>{e(titulo)}</h2>{intro}{_aviso_ancho(len(columnas))}<div class="scroll" tabindex="0" aria-label="{e(rotulo)}"><table><thead><tr>{cabeza}</tr></thead>'
            f'<tbody>{filas}</tbody></table></div>{pie}</section>')


def notas(conclusion, como_leer, avisos=(), titulo_lectura="Lectura generada", titulo_guia="Cómo leer esta figura"):
    """Lectura generada con la regla de redacción del panel, cómo leer la figura y los avisos de los datos."""
    extra = "".join(f"<p>{e(a)}</p>" for a in avisos)
    return (f'<div class="notas"><aside><b>{e(titulo_lectura)}</b><p>{e(conclusion)}</p>{extra}</aside>'
            f'<aside><b>{e(titulo_guia)}</b><p>{e(como_leer)}</p></aside></div>')


def ficha(etiqueta, valor, detalle_texto, aviso=None):
    marca = f" · <em>{e(aviso)}</em>" if aviso else ""
    pie = f"<small>{e(detalle_texto)}</small>" if detalle_texto else ""
    return f'<div class="ficha">{e(etiqueta)}{marca}<b>{e(valor)}</b>{pie}</div>'


def fichas_html(items):
    """Tarjetas de cifras `(etiqueta, valor, detalle[, aviso])`; con tres tarjetas se reparten en tres columnas."""
    clase = "fichas fichas-tres" if len(items) == 3 else "fichas"
    return f'<div class="{clase}">' + "".join(ficha(*i) for i in items) + "</div>"


def tarjetas(items):
    """Tarjetas de cifras listas para dibujarse dentro de un contenedor nativo: llevan su propio artículo para recibir los estilos del diseño."""
    return '<article class="vista prueba-v3">' + fichas_html(items) + "</article>"


def pie_pagina():
    """Solo el pie con «Volver arriba», para las páginas cuyo cuerpo es nativo."""
    return envolver("", analisis=False)


def panel(clase, titulo, cuerpo, introduccion=""):
    intro = f"<p>{e(introduccion)}</p>" if introduccion else ""
    return f'<section class="panel {e(clase)}"><h2>{e(titulo)}</h2>{intro}{cuerpo}</section>'


def parrafos(textos):
    return "".join(f"<p>{e(t)}</p>" for t in textos if t)


def lista(textos):
    """Lista con viñetas; las negritas de Markdown (**texto**) pasan a <b> después de escapar el texto."""
    return "<ul>" + "".join(f"<li>{negritas(e(t))}</li>" for t in textos) + "</ul>"


def envolver(cuerpo_html, analisis=True):
    """Cuerpo de la página con su pie «Volver arriba»; `analisis` lo agrupa en el contenedor que coordina la figura y la tabla."""
    interior = f'<div class="analisis">{cuerpo_html}</div>' if analisis else cuerpo_html
    return f'<article class="vista prueba-v3">{interior}<footer class="pie-v3"><button type="button" data-accion="arriba">Volver arriba</button></footer></article>'


# ---------------------------------------------------------------- guía y curiosidades
def guia(id_pagina, ejemplo=None):
    """Seis pasos de la guía de lectura; el paso sin texto fijo usa `ejemplo`, una frase armada con datos de la API."""
    pasos = activos.contenido(id_pagina)["pasos"]
    return [dict(titulo=p["titulo"], region=p["region"], texto=p["texto"] if p["texto"] is not None else ejemplo) for p in pasos]


def curiosidades(id_pagina):
    """Curiosidades de la página con su fundamento en el glosario del panel."""
    return [dict(titulo=f["titulo"], explicacion=f["explicacion"], categoria=f["categoria"], fundamento="Glosario del panel · " + glosario.TERMINOS[f["termino"]][0])
            for f in activos.contenido(id_pagina)["fichas"]]


# ---------------------------------------------------------------- documento exportable
def figura_svg(items, inferior, superior, marcas, titulo_eje, cero=False):
    """SVG de puntos con intervalo. `items` son diccionarios con etiqueta, texto, x, desde, hasta (en las unidades del eje) y baja; devuelve (svg, alto)."""
    colores = tema.colores()
    escala_x = ANCHO_LAMINA / (superior - inferior)

    def pos(v):
        return X_LAMINA + escala_x * (v - inferior)

    ejes = "".join(f'<text x="{pos(v):.1f}" y="{Y_EJE}" text-anchor="middle">{e(formato.numero(v))}</text>' for v in marcas)
    partes = [f'<g class="eje"><text x="{X_LAMINA}" y="{Y_TITULO}">{e(titulo_eje)}</text>{ejes}</g>']
    alto = Y_INICIAL + PASO_Y * len(items)
    if cero:
        partes.append(f'<path d="M{pos(0):.1f} {Y_EJE + AJUSTE_TEXTO}V{alto - ALTO_MARCA}" stroke="{colores["secundario"]}" stroke-width="{GROSOR}" stroke-dasharray="{RADIO} {RADIO}" fill="none"/>')
    for i, it in enumerate(items):
        y = Y_INICIAL + PASO_Y * i
        aviso = f" · {componentes.ETIQUETA_BAJA}" if it.get("baja") else ""
        texto = f'<text x="{X_ETIQUETA}" y="{y + AJUSTE_TEXTO}">{e(it["etiqueta"] + aviso)}</text><text x="{X_VALOR}" y="{y + AJUSTE_TEXTO}">{e(it["texto"])}</text>'
        if None in (it["x"], it["desde"], it["hasta"]):
            partes.append(f"<g>{texto}</g>")
            continue
        a, b, x = pos(it["desde"]), pos(it["hasta"]), pos(it["x"])
        color = colores["secundario"] if it.get("baja") else colores["principal"]
        relleno = "#ffffff" if it.get("baja") else color
        trazo = f"M{a:.1f} {y}H{b:.1f}M{a:.1f} {y - MEDIA_MARCA}v{ALTO_MARCA}M{b:.1f} {y - MEDIA_MARCA}v{ALTO_MARCA}"
        partes.append(f'<g>{texto}<path d="{trazo}" fill="none" stroke="{colores["texto"]}" stroke-width="{GROSOR}"/>'
                      f'<circle cx="{x:.1f}" cy="{y}" r="{RADIO}" fill="{relleno}" stroke="{color}" stroke-width="{GROSOR}"/></g>')
    return "".join(partes), alto


def documento(pagina, grupo, corte, metadata, cuerpo, lectura="", figura=None):
    """Documento HTML autónomo (sin scripts, sin recursos externos y con una política de contenido restrictiva): alcance, corte, fuente, `cuerpo` (HTML ya escapado) y, si hay,
    una figura `(svg, alto, descripción, pie)` y la lectura generada."""
    bloque = ""
    if figura:
        svg, alto, descripcion, pie = figura
        bloque = activos.plantilla("plantillas", "figura.html").substitute(alto=alto, descripcion=e(descripcion), svg=svg, pie=e(pie))
    html = activos.plantilla("plantillas", "lamina.html").substitute(
        titulo=e(pagina.titulo), ruta=e(f"{grupo} / {pagina.titulo}"), corte=e(corte), alcance=negritas(e(componentes.alcance_markdown(metadata))), figura=bloque,
        detalle=cuerpo.replace(' tabindex="0"', ""), lectura=e(lectura), fuente=e(componentes.texto_pie(metadata)))
    return html.encode("utf-8")
