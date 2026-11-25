"""Página «Comunas (K6 y composición)»: tasa por comuna con intervalo y la composición por grupo de estrato.

Desde D115 se dibuja con la interfaz propia (figura de barras, puntos y tabla, glosario, guía, curiosidades, modo presentación y exportación). Los datos, el formato y los textos son los de siempre.
"""
import pandas as pd
import streamlit as st

from src.panel import claves, componentes, formato, redaccion
from src.panel.frontend import comunas as vista
from src.panel.frontend import lectura
from src.panel.frontend import vista as base
from src.panel.frontend.marco import dibujar, marco
from src.panel.paginas._comun import texto_ic

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


def tabla_k6(filas):
    """DataFrame de texto de «Detalle por comuna»: una fila por comuna, con las cifras ya formateadas."""
    return pd.DataFrame([{
        "Comuna": f["comuna"] + (f" ({componentes.ETIQUETA_BAJA})" if f["muestra_baja"] else ""),
        "Severos": formato.numero(f["severos"]), "Con datos": formato.numero(f["n_con_datos"]), "Tasa": formato.porcentaje(f["tasa"]),
        "Intervalo de Wilson": texto_ic(f["ic95_inf"], f["ic95_sup"]), "Sin datos": formato.numero(f["n_sin_datos"]),
        "% sin datos": formato.porcentaje(f["pct_sin_datos"], 1),
    } for f in filas])


def render(api):
    def cuerpo(contexto):
        r = api("/comunas")
        dibujar(base.cabecera(contexto.pagina, contexto.grupo, contexto.corte, contexto.metadata))
        if componentes.fallo(r):
            return
        filas = r.datos
        if not filas:
            st.warning("La API no devolvió filas de K6.")
            return
        etiquetas = ["Comuna " + f["comuna"] for f in filas]
        tabla = tabla_k6(filas)
        conclusion = redaccion.conclusion_comunas(filas)
        c = api("/composicion")
        composicion = comuna = None
        if c.ok and c.datos:
            composicion, comuna = _tabla_composicion(c.datos), redaccion.comuna_que_concentra(c.datos, claves.GRUPO_COMPOSICION_1_2)
        documento = vista.lamina(contexto.pagina, contexto.grupo, contexto.corte, contexto.metadata, filas, etiquetas, tabla, conclusion, composicion, comuna)
        lectura.herramientas(ID, contexto.pagina.titulo, vista.guia(), base.curiosidades(ID), documento, "comunas_tasa_por_comuna.html")
        dibujar(vista.cuerpo(filas, etiquetas, tabla, conclusion, composicion, comuna))
        if componentes.fallo(c):
            return
        if not c.datos:
            st.warning("La API no devolvió la composición por comuna.")

    marco(api, ID, cuerpo)
