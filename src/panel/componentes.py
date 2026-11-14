"""Componentes comunes del panel: marco de página, recuadro de alcance, avisos de fallo, tarjetas, tablas y gráficos Altair.

Solo lectura: nada de aquí abre archivos ni bases; los datos llegan ya leídos por el cliente de la API. Sin HTML propio, sin JavaScript
y sin recursos externos. Ningún número se escribe en el código: todas las cifras vienen de los datos y se dan formato con `formato`.
"""
import altair as alt
import pandas as pd
import streamlit as st

from src.logger import get_logger
from src.panel import formato, registro, tema

log = get_logger(__name__)

ALTO_GRAFICO = 340
EXPRESION_COMA = "replace(format(datum.value, '.1f'), '.', ',')"
ETIQUETA_BAJA = "muestra baja"
ETIQUETA_SUFICIENTE = "muestra suficiente"
PIE_INTERVALO = "Las barras de error son el intervalo de confianza de Wilson al 95 %: indican la incertidumbre de la tasa en esta muestra."


def fallo(resultado):
    """Si la consulta falló, muestra un aviso claro en español (sin trazas ni rutas) y devuelve True."""
    if resultado.ok:
        return False
    estado = f" (código {resultado.error.estado})" if resultado.error.estado else ""
    st.warning(resultado.error.mensaje + estado, icon=":material/warning:")
    return True


def recuadro_alcance(metadata=None):
    """Recuadro permanente de alcance (DP-4): proxy de daño, tasas condicionales a la muestra y estrato de 2015."""
    alcance = " " + metadata["alcance_temporal"] if isinstance(metadata, dict) and "alcance_temporal" in metadata else " El estrato es anterior al evento y se asignó por lados de manzana al barrio."
    with st.container(border=True, key="alcance"):
        st.markdown(
            "**Alcance.** El cambio satelital severo (severo estricto) es un **proxy de daño**, no una evaluación estructural. "
            "Las tasas son **condicionales a esta muestra** y no son prevalencias de Cali." + alcance
        )


def encabezado(salud):
    """Estado de la API, almacenamiento y fecha de corte, en una línea."""
    if salud is None or not salud.ok or not isinstance(salud.datos, dict):
        st.caption("API: sin conexión")
        return
    s = salud.datos
    estado = "en línea" if s.get("estado") == "ok" else "degradada"
    st.caption(f"API: {estado} · almacenamiento: {s.get('almacenamiento')} · fecha de corte: {s.get('fecha_corte') or formato.SIN_DATO}")


def pie(metadata):
    """Pie con la fuente y las licencias que informa la API."""
    if not isinstance(metadata, dict) or not isinstance(metadata.get("licencias"), dict):
        st.caption("Fuente: datos publicados por la API del proyecto.")
        return
    licencias = "; ".join(f"{k}: {str(v).split(' (')[0]}" for k, v in metadata["licencias"].items())
    st.caption(f"Fuente: capa de edificaciones y estrato por barrio, procesados por este proyecto. Licencias: {licencias}.")


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
        pie(meta.datos if meta.ok else None)
    except (KeyError, TypeError, ValueError, AttributeError, IndexError):
        log.exception("la página %s recibió datos con un formato inesperado", id_pagina)
        st.warning("Los datos recibidos de la API no tienen el formato esperado; no se pueden mostrar.", icon=":material/warning:")


def tarjeta(etiqueta, valor, ayuda=None, clave=None):
    st.metric(etiqueta, valor, help=ayuda, border=True)


def tabla(df, clave=None):
    """Tabla con texto ya formateado; sin índice."""
    st.dataframe(df, hide_index=True, width="stretch", key=clave)


def _eje_pct(titulo):
    return alt.Axis(title=titulo, labelExpr=EXPRESION_COMA, labelFontSize=12, titleFontSize=12)


def grafico_tasas(df, x, titulo, descripcion, alto=ALTO_GRAFICO, titulo_x=None):
    """Barras de tasa con barras de error (intervalo de Wilson). `df` debe traer: x, tasa_pct, inf_pct, sup_pct, muestra, tasa_txt, ic_txt.

    La muestra baja se distingue por texto (en la leyenda y en la etiqueta del eje), no solo por color.
    """
    col = tema.colores()
    orden = list(df[x])
    base = alt.Chart(df).encode(x=alt.X(f"{x}:N", sort=orden, title=titulo_x or "", axis=alt.Axis(labelAngle=0, labelFontSize=12, titleFontSize=12)))
    barras = base.mark_bar().encode(
        y=alt.Y("tasa_pct:Q", axis=_eje_pct("Tasa de cambio satelital severo (%)")),
        color=alt.Color("muestra:N", scale=alt.Scale(domain=[ETIQUETA_SUFICIENTE, ETIQUETA_BAJA], range=[col["principal"], col["secundario"]]),
                        legend=alt.Legend(title="Tamaño de la muestra", labelFontSize=12, titleFontSize=12)),
        tooltip=[alt.Tooltip(f"{x}:N", title="Grupo"), alt.Tooltip("tasa_txt:N", title="Tasa"), alt.Tooltip("ic_txt:N", title="Intervalo de Wilson"), alt.Tooltip("muestra:N", title="Muestra")],
    )
    error = base.mark_errorbar(color=col["texto"], thickness=2, ticks=True).encode(y=alt.Y("inf_pct:Q", title=""), y2="sup_pct:Q")
    chart = alt.layer(barras, error).properties(title=alt.TitleParams(titulo, fontSize=14, anchor="start", color=col["texto"]), height=alto, usermeta={"descripcion": descripcion})
    chart = chart.properties(description=descripcion)
    st.altair_chart(chart, width="stretch")
    st.caption(PIE_INTERVALO)


def grafico_diferencias(df, x, titulo, descripcion, alto=ALTO_GRAFICO):
    """Puntos con intervalo para la diferencia en puntos porcentuales por escenario. `df`: x, dif_pp, inf_pp, sup_pp, dif_txt, ic_txt."""
    col = tema.colores()
    orden = list(df[x])
    base = alt.Chart(df).encode(x=alt.X(f"{x}:N", sort=orden, title="Escenario", axis=alt.Axis(labelAngle=0, labelFontSize=12, titleFontSize=12)))
    puntos = base.mark_point(filled=True, size=120, color=col["principal"]).encode(
        y=alt.Y("dif_pp:Q", axis=_eje_pct("Diferencia 3-5 menos 1-2 (puntos porcentuales)")),
        tooltip=[alt.Tooltip(f"{x}:N", title="Escenario"), alt.Tooltip("dif_txt:N", title="Diferencia"), alt.Tooltip("ic_txt:N", title="Intervalo de Newcombe")])
    error = base.mark_errorbar(color=col["texto"], thickness=2, ticks=True).encode(y=alt.Y("inf_pp:Q", title=""), y2="sup_pp:Q")
    cero = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color=col["secundario"], strokeDash=[6, 4], size=2).encode(y="y:Q")
    chart = alt.layer(cero, error, puntos).properties(title=alt.TitleParams(titulo, fontSize=14, anchor="start", color=col["texto"]), height=alto)
    st.altair_chart(chart.properties(description=descripcion), width="stretch")
    st.caption("La línea discontinua marca la ausencia de diferencia. Las barras de error son el intervalo de Newcombe al 95 % de la diferencia de tasas.")


def dispersion(df, titulo, descripcion, orden_clases, alto=ALTO_GRAFICO):
    """Dispersión lon/lat por clase de daño. No es un mapa cartográfico: sin fondo, sin teselas y sin recursos externos."""
    col = tema.colores()
    colores = [col["neutro"], col["apoyo"], col["secundario"], col["principal"]][: len(orden_clases)]
    formas = ["circle", "square", "triangle-up", "diamond"][: len(orden_clases)]
    chart = alt.Chart(df).mark_point(filled=True, size=50, opacity=0.8).encode(
        x=alt.X("lon:Q", scale=alt.Scale(zero=False), axis=alt.Axis(title="Longitud (grados)", labelExpr="replace(format(datum.value, '.3f'), '.', ',')")),
        y=alt.Y("lat:Q", scale=alt.Scale(zero=False), axis=alt.Axis(title="Latitud (grados)", labelExpr="replace(format(datum.value, '.3f'), '.', ',')")),
        color=alt.Color("clase_dano:N", scale=alt.Scale(domain=list(orden_clases), range=colores), legend=alt.Legend(title="Clase de daño")),
        shape=alt.Shape("clase_dano:N", scale=alt.Scale(domain=list(orden_clases), range=formas), legend=None),
        tooltip=[alt.Tooltip("objectid:Q", title="Construcción"), alt.Tooltip("clase_dano:N", title="Clase"), alt.Tooltip("barrio:N", title="Barrio")],
    ).properties(title=alt.TitleParams(titulo, fontSize=14, anchor="start", color=col["texto"]), height=alto, description=descripcion)
    st.altair_chart(chart, width="stretch")
    st.caption("Dispersión de las construcciones de la página mostrada: no es un mapa cartográfico (sin fondo ni escala de distancia).")
