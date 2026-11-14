"""Página «Construcciones»: tabla paginada con filtros que la API aplica, dispersión lon/lat y descarga CSV de lo mostrado."""
import math

import pandas as pd
import streamlit as st

from src.panel import claves, componentes, formato
from src.panel.configuracion import cargar_panel

ID = "construcciones"
TODAS = "Todas"
OPCIONES_SEVERO = {TODAS: None, "Solo con cambio satelital severo": True, "Sin cambio satelital severo": False}


def _si_no(valor):
    return formato.SIN_DATO if valor is None else ("Sí" if valor else "No")


def tabla_de_items(items):
    """DataFrame de texto de la página mostrada (también es el contenido del CSV descargable)."""
    return pd.DataFrame([{
        "Construcción": i["objectid"], "Comuna": i["comuna"] or formato.SIN_DATO, "Barrio": i["barrio"] or formato.SIN_DATO,
        "Código de barrio": i["codigo_barrio"] or formato.SIN_DATO, "Estrato": formato.numero(i["estrato"]) if i["estrato"] is not None else formato.SIN_DATO,
        "Clase de daño": i["clase_dano"] or formato.SIN_DATO, "Cambio severo": _si_no(i["severo_estricto"]), "Nombre validado": _si_no(i["nombre_validado"]),
    } for i in items])


def _opciones_comuna(api):
    r = api("/comunas")
    return [TODAS] + sorted({f["comuna"] for f in r.datos}) if r.ok else [TODAS]


def _opciones_estrato(api):
    r = api("/kpis/K1")
    if not r.ok:
        return [TODAS]
    return [TODAS] + sorted({f["grupo"].replace("estrato_", "") for f in r.datos if str(f.get("grupo", "")).startswith("estrato_")})


def render(api):
    def cuerpo():
        tamano = int(cargar_panel()["tamano_pagina_tabla"])
        f1, f2, f3 = st.columns(3)
        with f1:
            comuna = st.selectbox("Comuna", _opciones_comuna(api), key="filtro_comuna")
        with f2:
            estrato = st.selectbox("Estrato", _opciones_estrato(api), key="filtro_estrato")
        with f3:
            severo = st.selectbox("Cambio satelital severo", list(OPCIONES_SEVERO), key="filtro_severo")
        pagina = st.number_input("Página", min_value=1, value=1, step=1, key="pagina")
        r = api("/construcciones", limit=tamano, offset=(int(pagina) - 1) * tamano, comuna=None if comuna == TODAS else comuna,
                estrato=None if estrato == TODAS else int(estrato), severo_estricto=OPCIONES_SEVERO[severo])
        if componentes.fallo(r):
            return
        datos = r.datos
        paginas = max(1, math.ceil(datos["total"] / tamano))
        st.caption(f"{formato.numero(datos['total'])} construcciones con estos filtros; página {formato.numero(pagina)} de {formato.numero(paginas)}. "
                   "Los filtros los aplica la API sobre toda la muestra, no solo sobre la página mostrada.")
        if not datos["items"]:
            st.info("No hay construcciones en esta página con estos filtros.")
            return
        df = tabla_de_items(datos["items"])
        componentes.tabla(df)
        st.download_button("Descargar CSV (filas mostradas)", df.to_csv(index=False).encode("utf-8"), file_name="construcciones_pagina.csv", mime="text/csv", key="descarga_csv")
        con_coord = pd.DataFrame([i for i in datos["items"] if i["lon"] is not None and i["lat"] is not None])
        if con_coord.empty:
            st.info("Ninguna construcción de esta página trae coordenadas.")
            return
        con_coord["barrio"] = con_coord["barrio"].fillna(formato.SIN_DATO)
        con_coord["clase_dano"] = con_coord["clase_dano"].fillna(formato.SIN_DATO)
        componentes.dispersion(con_coord, "Ubicación de las construcciones de la página, por clase de daño",
                               "Dispersión de longitud y latitud de las construcciones mostradas, con clase de daño distinguida por color y forma.", claves.CLASES_DANO)

    componentes.marco(api, ID, cuerpo)
