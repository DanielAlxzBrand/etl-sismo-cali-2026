"""Componentes comunes del panel: marco de página, recuadro de alcance, avisos de fallo, tarjetas, tablas y gráficos Altair.

Solo lectura: nada de aquí abre archivos ni bases; los datos llegan ya leídos por el cliente de la API. Sin HTML propio, sin JavaScript
y sin recursos externos: el HTML, el CSS y el JavaScript propios viven solo en `src/panel/frontend/` (D115). Ningún número se escribe en el código: todas las cifras vienen de los datos y se dan formato con `formato`.
"""
import altair as alt
import pandas as pd
import streamlit as st

from src.logger import get_logger
from src.panel import formato, glosario, registro, tema

log = get_logger(__name__)

ALTO_GRAFICO = 340
EXPRESION_COMA = "replace(format(datum.value, '.1f'), '.', ',')"
EXPRESION_GRADOS = "replace(format(datum.value, '.4f'), '.', ',')"   # F-13: cuatro decimales para que «3,440» no se lea como tres mil cuatrocientos cuarenta
LARGO_MAXIMO_ETIQUETA = 28    # caracteres que caben en una tarjeta de media pantalla a 1024 px sin que Streamlit los recorte con puntos suspensivos (F-01)
POR_FILA = 2                  # tarjetas por fila: con más, a 1024 px la caja de la cifra se queda corta y la recorta (F-01)
UMBRAL_COLUMNAS_ANCHAS = 4    # desde cuántas columnas una tabla puede no caber en una pantalla estrecha (F-03): a 390 px se cortó hasta la de cuatro columnas de Calidad
AVISO_TABLA_ANCHA = "Tabla ancha: en una pantalla estrecha, deslícela hacia los lados para ver todas las columnas."
ALTO_POR_BARRA = 52           # píxeles por barra en los gráficos horizontales, para que quepan las etiquetas de dos líneas (F-04)
ETIQUETA_BAJA = "muestra baja"
ETIQUETA_SUFICIENTE = "muestra suficiente"
PIE_INTERVALO = ("Cada barra es la tasa. La línea que la cruza va del límite inferior al superior del intervalo de confianza de Wilson al 95 % y las rayas de sus extremos marcan esos dos límites: "
                 "indican la incertidumbre de la tasa en esta muestra.")


def fallo(resultado):
    """Si la consulta falló, muestra un aviso claro en español (sin trazas ni rutas) y devuelve True."""
    if resultado.ok:
        return False
    estado = f" (código {resultado.error.estado})" if resultado.error.estado else ""
    st.warning(resultado.error.mensaje + estado, icon=":material/warning:")
    return True


def alcance_markdown(metadata=None):
    """Texto del recuadro de alcance (DP-4) en Markdown: proxy de daño, tasas condicionales a la muestra y estrato de 2015. Lo comparten el recuadro nativo y la interfaz propia (D115)."""
    alcance = " " + metadata["alcance_temporal"] if isinstance(metadata, dict) and "alcance_temporal" in metadata else " El estrato es anterior al evento y se asignó por lados de manzana al barrio."
    return ("**Alcance.** El cambio satelital severo (severo estricto) es un **proxy de daño**, no una evaluación estructural. "
            "Las tasas son **condicionales a esta muestra** y no son prevalencias de Cali." + alcance)


def recuadro_alcance(metadata=None):
    """Recuadro permanente de alcance (DP-4): proxy de daño, tasas condicionales a la muestra y estrato de 2015."""
    with st.container(border=True, key="alcance"):
        st.markdown(alcance_markdown(metadata))


def encabezado(salud):
    """Estado de la API, almacenamiento y fecha de corte, en una línea."""
    if salud is None or not salud.ok or not isinstance(salud.datos, dict):
        st.caption("API: sin conexión")
        return
    s = salud.datos
    estado = "en línea" if s.get("estado") == "ok" else "degradada"
    st.caption(f"API: {estado} · almacenamiento: {s.get('almacenamiento')} · fecha de corte: {s.get('fecha_corte') or formato.SIN_DATO}")


def texto_pie(metadata):
    """Texto del pie con la fuente y las licencias que informa la API."""
    if not isinstance(metadata, dict) or not isinstance(metadata.get("licencias"), dict):
        return "Fuente: datos publicados por la API del proyecto."
    licencias = "; ".join(f"{k}: {str(v).split(' (')[0]}" for k, v in metadata["licencias"].items())
    return f"Fuente: capa de edificaciones y estrato por barrio, procesados por este proyecto. Licencias: {licencias}."


def pie(metadata):
    """Pie con la fuente y las licencias que informa la API."""
    st.caption(texto_pie(metadata))


def marco(api, id_pagina, cuerpo):
    """Estructura común de cada página: título, pregunta, estado de la API, alcance, cuerpo y pie.

    Degradación: si la API no responde, el cuerpo no se ejecuta y se muestra el aviso; y si responde con una forma inesperada, se informa
    sin mostrar la excepción ni sus rutas. Nunca se muestra una traza.
    """
    pagina = registro.pagina(id_pagina)
    st.title(pagina.titulo)
    st.caption(pagina.pregunta)
    try:
        salud = api("/health")
        encabezado(salud)
        meta = api("/metadata")
        recuadro_alcance(meta.datos if meta.ok else None)
        if not salud.ok:
            fallo(salud)
        else:
            cuerpo()
            glosario.desplegable(id_pagina)
        pie(meta.datos if meta.ok else None)
    except (KeyError, TypeError, ValueError, AttributeError, IndexError):
        log.exception("la página %s recibió datos con un formato inesperado", id_pagina)
        st.warning("Los datos recibidos de la API no tienen el formato esperado; no se pueden mostrar.", icon=":material/warning:")


def tarjeta(etiqueta, valor, ayuda=None, clave=None):
    """Una tarjeta con una cifra y su etiqueta; la explicación larga va en `ayuda` (el signo de interrogación), no en la etiqueta (F-01).

    Streamlit recorta con puntos suspensivos una etiqueta que no cabe en una sola línea y no la parte en dos; por eso las etiquetas son cortas (`LARGO_MAXIMO_ETIQUETA`).
    No abrevia ni recorta la cifra.
    """
    st.metric(etiqueta, valor, help=ayuda, border=True)


def tarjetas(items, por_fila=POR_FILA):
    """Dibuja tarjetas `(etiqueta, valor, ayuda)` en filas de `por_fila` columnas (F-01, D87).

    Lo hicimos con dos por fila porque con cuatro, a 1024 px, la caja de la cifra medía unos 97 píxeles y Streamlit recortaba «6,33 %» y «2026-09-02». No hace que las columnas se adapten
    al ancho de la ventana: a menos de unos 640 px Streamlit las apila por su cuenta.
    """
    for i in range(0, len(items), por_fila):
        for columna, (etiqueta, valor, ayuda) in zip(st.columns(por_fila), items[i:i + por_fila]):
            with columna:
                tarjeta(etiqueta, valor, ayuda)


def tabla(df, clave=None, texto_largo=False, seleccion=False):
    """Tabla con texto ya formateado; sin índice. Con `texto_largo` se dibuja completa (el texto se parte en líneas) en lugar de una cuadrícula con desplazamiento.

    Si tiene `UMBRAL_COLUMNAS_ANCHAS` columnas o más, avisa antes de la tabla que puede deslizarse hacia los lados (F-03, D87): a 390 px la tabla se corta en el borde y no se notaba que había más columnas.
    El aviso no cambia la tabla ni la adapta al ancho; solo dice qué hacer.
    """
    if df.shape[1] >= UMBRAL_COLUMNAS_ANCHAS:
        st.caption(AVISO_TABLA_ANCHA)
    if texto_largo:
        st.table(df.style.hide(axis="index"))
    elif seleccion:
        return st.dataframe(df, hide_index=True, width="stretch", key=clave, on_select="rerun", selection_mode="single-row")   # D116: la fila elegida alimenta «Qué significa esta fila»
    else:
        st.dataframe(df, hide_index=True, width="stretch", key=clave)


def _eje_pct(titulo):
    """Eje cuantitativo con etiquetas de porcentaje con coma decimal."""
    return alt.Axis(title=titulo, labelExpr=EXPRESION_COMA, labelFontSize=12, titleFontSize=12)


def _con_texto_oscuro(grafico):
    """Pinta los rótulos y títulos de ejes y leyendas con el color `texto_secundario` de la configuración (F-12, D89).

    El gris por defecto de Streamlit daba 3,72 a 1 sobre el fondo; con este color el texto de los gráficos queda por encima de 4,5 a 1 (el cálculo está en `scripts/panel/contraste.py`).
    Se llama al final, porque `configure_*` solo se puede aplicar al gráfico completo.
    """
    c = tema.colores()["texto_secundario"]
    return grafico.configure_axis(labelColor=c, titleColor=c).configure_legend(labelColor=c, titleColor=c)


def grafico_tasas(df, x, titulo, descripcion, alto=ALTO_GRAFICO, titulo_x=None):
    """Barras HORIZONTALES de tasa con su intervalo de Wilson (F-04, F-05, D87). `df` debe traer: x, tasa_pct, inf_pct, sup_pct, muestra, tasa_txt, ic_txt.

    Eran verticales y a 390 px Vega solo dibujaba la primera y la última etiqueta; con las barras acostadas, cada etiqueta tiene su propia fila y se ven todas. La muestra baja se distingue
    por texto (en la leyenda y en la etiqueta de la fila), no solo por color (D74). Cada barra mide `ALTO_POR_BARRA` píxeles (un paso de Vega) y las etiquetas no se ocultan por solaparse: con un alto fijo, Vega achicaba el área y borraba las etiquetas de las barras de en medio. No ordena los grupos: respeta el orden de `df`.
    """
    col = tema.colores()
    orden = list(df[x])
    base = alt.Chart(df).encode(y=alt.Y(f"{x}:N", sort=orden, title=titulo_x or "", axis=alt.Axis(labelFontSize=12, titleFontSize=12, labelLimit=0, labelOverlap=False, labelExpr="split(datum.label, ' · ')")))
    barras = base.mark_bar().encode(
        x=alt.X("tasa_pct:Q", axis=_eje_pct("Tasa de cambio satelital severo (%)")),
        color=alt.Color("muestra:N", scale=alt.Scale(domain=[ETIQUETA_SUFICIENTE, ETIQUETA_BAJA], range=[col["principal"], col["secundario"]]),
                        legend=alt.Legend(title="Tamaño de la muestra", orient="bottom", labelFontSize=12, titleFontSize=12)),
        tooltip=[alt.Tooltip(f"{x}:N", title="Grupo"), alt.Tooltip("tasa_txt:N", title="Tasa"), alt.Tooltip("ic_txt:N", title="Intervalo de Wilson"), alt.Tooltip("muestra:N", title="Muestra")],
    )
    error = base.mark_errorbar(color=col["texto"], thickness=2, ticks=True).encode(x=alt.X("inf_pct:Q", title=""), x2="sup_pct:Q")
    chart = alt.layer(barras, error).properties(title=alt.TitleParams(titulo, fontSize=14, anchor="start", color=col["texto"]), height=alt.Step(ALTO_POR_BARRA),
                                                usermeta={"descripcion": descripcion}, description=descripcion)
    st.altair_chart(_con_texto_oscuro(chart), width="stretch")
    st.caption(PIE_INTERVALO)


RELLENO_GRAFICO_CON_TITULO = {"top": 16, "right": 5, "bottom": 5, "left": 5}   # el relleno de siempre de Vega (5 px) con más aire arriba: Vega mide el título de varias líneas con una altura menor que la que dibuja y recortaba la primera línea (D119)
LARGO_MAXIMO_LINEA_TITULO = 34   # caracteres por línea del título de un gráfico para que quepa a 390 px sin que Vega lo recorte con puntos suspensivos (D116)


def partir_titulo(titulo, maximo=LARGO_MAXIMO_LINEA_TITULO):
    """Parte un título largo en líneas, solo en los espacios y sin cambiar ninguna palabra: unidas con un espacio dan el texto original. Un título corto se devuelve tal cual."""
    lineas, actual = [], ""
    for palabra in str(titulo).split(" "):
        if actual and len(actual) + 1 + len(palabra) > maximo:
            lineas.append(actual)
            actual = palabra
        else:
            actual = f"{actual} {palabra}".strip()
    lineas.append(actual)
    return lineas if len(lineas) > 1 else lineas[0]


def grafico_diferencias(df, x, titulo, descripcion, alto=ALTO_GRAFICO):
    """Puntos con intervalo de Newcombe para la diferencia en puntos porcentuales por escenario. `df`: x, dif_pp, inf_pp, sup_pp, dif_txt, ic_txt.

    Cada punto es la diferencia observada, la línea vertical que lo cruza va de un límite del intervalo al otro y la línea discontinua marca la ausencia de diferencia (F-05, D87).
    No ordena los escenarios ni dice cuál es mejor.
    """
    col = tema.colores()
    orden = list(df[x])
    base = alt.Chart(df).encode(x=alt.X(f"{x}:N", sort=orden, title="Escenario", axis=alt.Axis(labelAngle=0, labelFontSize=12, titleFontSize=12)))
    puntos = base.mark_point(filled=True, size=120, color=col["principal"]).encode(
        y=alt.Y("dif_pp:Q", axis=_eje_pct("Diferencia 3-5 menos 1-2 (puntos porcentuales)")),
        tooltip=[alt.Tooltip(f"{x}:N", title="Escenario"), alt.Tooltip("dif_txt:N", title="Diferencia"), alt.Tooltip("ic_txt:N", title="Intervalo de Newcombe")])
    error = base.mark_errorbar(color=col["texto"], thickness=2, ticks=True).encode(y=alt.Y("inf_pp:Q", title=""), y2="sup_pp:Q")
    cero = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color=col["secundario"], strokeDash=[6, 4], size=2).encode(y="y:Q")
    chart = alt.layer(cero, error, puntos).properties(title=alt.TitleParams(partir_titulo(titulo), fontSize=14, anchor="start", color=col["texto"]), height=alto, padding=RELLENO_GRAFICO_CON_TITULO)
    st.altair_chart(_con_texto_oscuro(chart.properties(description=descripcion)), width="stretch")
    st.caption("Cada punto es la diferencia observada en ese escenario; la línea vertical que lo cruza va del límite inferior al superior del intervalo de Newcombe al 95 % y las rayas de sus extremos "
               "marcan esos límites. La línea discontinua marca la ausencia de diferencia.")


def dispersion(df, titulo, descripcion, orden_clases, alto=ALTO_GRAFICO):
    """Dispersión lon/lat por clase de daño. No es un mapa cartográfico: sin fondo, sin teselas y sin recursos externos.

    Las coordenadas se rotulan «grados decimales» y llevan cuatro decimales con coma (F-13, D87): con tres, «3,440» se leía como miles. La leyenda va abajo y en dos columnas para dejar ancho al gráfico y que no se corte «sin_datos» a 390 px.
    No dibuja límites de barrios ni distancias: solo ubica puntos.
    """
    col = tema.colores()
    colores = [col["neutro"], col["apoyo"], col["secundario"], col["principal"]][: len(orden_clases)]
    formas = ["circle", "square", "triangle-up", "diamond"][: len(orden_clases)]
    chart = alt.Chart(df).mark_point(filled=True, size=50, opacity=0.8).encode(
        x=alt.X("lon:Q", scale=alt.Scale(zero=False), axis=alt.Axis(title="Longitud (grados decimales)", labelExpr=EXPRESION_GRADOS, labelFontSize=12, titleFontSize=12)),
        y=alt.Y("lat:Q", scale=alt.Scale(zero=False), axis=alt.Axis(title="Latitud (grados decimales)", labelExpr=EXPRESION_GRADOS, labelFontSize=12, titleFontSize=12)),
        color=alt.Color("clase_dano:N", scale=alt.Scale(domain=list(orden_clases), range=colores), legend=alt.Legend(title="Clase de daño", orient="bottom", columns=2, labelFontSize=12, titleFontSize=12)),
        shape=alt.Shape("clase_dano:N", scale=alt.Scale(domain=list(orden_clases), range=formas), legend=None),
        tooltip=[alt.Tooltip("objectid:Q", title="Construcción"), alt.Tooltip("clase_dano:N", title="Clase"), alt.Tooltip("barrio:N", title="Barrio")],
    ).properties(title=alt.TitleParams(titulo, fontSize=14, anchor="start", color=col["texto"]), height=alto, description=descripcion)
    st.altair_chart(_con_texto_oscuro(chart), width="stretch")
    st.caption("Dispersión de las construcciones de la página mostrada: no es un mapa cartográfico (sin fondo ni escala de distancia).")
