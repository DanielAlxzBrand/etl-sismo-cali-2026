"""Página «Comunas (K6 y composición)»: tasa por comuna con intervalo y la composición por grupo de estrato."""
import pandas as pd
import streamlit as st

from src.panel import claves, componentes, formato, redaccion
from src.panel.paginas._comun import filas_tasa, texto_ic

ID = "comunas"
GRUPOS = (claves.GRUPO_COMPOSICION_1_2, claves.GRUPO_COMPOSICION_3_5)


def _tabla_composicion(composicion):
    """Una fila por comuna con, para cada grupo de estrato, las construcciones con datos y los severos."""
    comunas = sorted({f["comuna"] for f in composicion})
    grupos = sorted({f["grupo_estrato"] for f in composicion})
    registros = []
    for c in comunas:
        fila = {"Comuna": c}
        for g in grupos:
            celda = next((f for f in composicion if f["comuna"] == c and f["grupo_estrato"] == g), None)
            fila[f"Estratos {g}: con datos"] = formato.numero(celda["n_con_datos"]) if celda else formato.numero(0)
            fila[f"Estratos {g}: severos"] = formato.numero(celda["severos"]) if celda else formato.numero(0)
        registros.append(fila)
    return pd.DataFrame(registros)


def render(api):
    def cuerpo():
        r = api("/comunas")
        if componentes.fallo(r):
            return
        filas = r.datos
        if not filas:
            st.warning("La API no devolvió filas de K6.")
            return
        etiquetas = ["Comuna " + f["comuna"] for f in filas]
        componentes.grafico_tasas(filas_tasa(filas, etiquetas, clave_tasa="tasa"), "grupo", "Tasa de cambio satelital severo por comuna",
                                  "Barras de la tasa por comuna con su intervalo de Wilson; las comunas con muestra baja llevan esa etiqueta.", titulo_x="Comuna")
        st.subheader("Detalle por comuna")
        tabla = pd.DataFrame([{
            "Comuna": f["comuna"] + (f" ({componentes.ETIQUETA_BAJA})" if f["muestra_baja"] else ""),
            "Severos": formato.numero(f["severos"]), "Con datos": formato.numero(f["n_con_datos"]), "Tasa": formato.porcentaje(f["tasa"]),
            "Intervalo de Wilson": texto_ic(f["ic95_inf"], f["ic95_sup"]), "Sin datos": formato.numero(f["n_sin_datos"]),
            "% sin datos": formato.porcentaje(f["pct_sin_datos"], 1),
        } for f in filas])
        componentes.tabla(tabla)
        st.markdown("**Lectura generada.** " + redaccion.conclusion_comunas(filas))
        st.subheader("Composición por comuna y grupo de estrato")
        c = api("/composicion")
        if componentes.fallo(c):
            return
        if not c.datos:
            st.warning("La API no devolvió la composición por comuna.")
            return
        componentes.tabla(_tabla_composicion(c.datos))
        st.caption("Construcciones con datos satelitales y severas por comuna y grupo de estrato (los grupos de estrato son los que define la API).")
        st.info(redaccion.comuna_que_concentra(c.datos, claves.GRUPO_COMPOSICION_1_2))

    componentes.marco(api, ID, cuerpo)
