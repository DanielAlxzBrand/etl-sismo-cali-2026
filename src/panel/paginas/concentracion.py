"""Página «Concentración (K3 y K4)»: los barrios con más construcciones con cambio satelital severo y la correlación de Spearman."""
import re

import pandas as pd
import streamlit as st

from src.panel import claves, componentes, formato, redaccion
from src.panel.paginas._comun import avisar_falta, por_grupo

ID = "concentracion"


def barrios_de_la_nota(nota):
    """[(código, severos)] leídos de la nota de K3 («códigos:severos 1914:30; 1913:25; …»); lista vacía si la nota no tiene ese formato."""
    m = re.search(r"severos ((?:\d+:\d+(?:; )?)+)", nota or "")
    if m is None:
        return []
    return [(par.split(":")[0], int(par.split(":")[1])) for par in m.group(1).split("; ") if ":" in par]


def construcciones_de_la_nota(nota):
    """(construcciones con datos de esos barrios, total con datos) leídos de «(2292 de 4709)»; None si no están."""
    m = re.search(r"\((\d+) de (\d+)\)", nota or "")
    return (int(m.group(1)), int(m.group(2))) if m else None


def p_permutacion(nota):
    m = re.search(r"p_permutacion=([0-9.]+)", nota or "")
    return float(m.group(1)) if m else None


def render(api):
    def cuerpo():
        r = api("/kpis")
        if componentes.fallo(r):
            return
        k3, k4 = por_grupo(r.datos, claves.K3, claves.K3_TOP10), por_grupo(r.datos, claves.K4)
        st.subheader("K3 · Concentración de los casos")
        if not k3:
            avisar_falta("el indicador K3")
        else:
            c1, c2 = st.columns(2)
            with c1:
                componentes.tarjeta("Participación de los barrios con más severos", formato.porcentaje(k3["valor"], 1),
                                    f"{k3['nombre']}: {formato.numero(k3['numerador'])} de {formato.numero(k3['denominador'])} construcciones con cambio satelital severo")
            share = construcciones_de_la_nota(k3["nota"])
            with c2:
                if share:
                    componentes.tarjeta("Esos barrios en las construcciones con datos", formato.porcentaje(share[0] / share[1], 1),
                                        f"{formato.numero(share[0])} de {formato.numero(share[1])} construcciones con datos")
            barrios = barrios_de_la_nota(k3["nota"])
            if barrios:
                total = k3["denominador"]
                componentes.tabla(pd.DataFrame([{"Código de barrio": c, "Severos": formato.numero(n), "Participación en los severos": formato.porcentaje(n / total, 1)} for c, n in barrios]))
            else:
                st.info(k3["nota"] or "La API no trae el detalle de los barrios.")
            st.caption("Los barrios con más casos también tienen más construcciones: concentración de casos no es mayor riesgo. Se excluyen los casos sin barrio asignado.")
        st.subheader("K4 · Estrato y tasa por barrio (Spearman)")
        if not k4:
            avisar_falta("el indicador K4")
        else:
            c1, c2, c3 = st.columns(3)
            p = p_permutacion(k4["nota"])
            with c1:
                componentes.tarjeta("Correlación de Spearman", formato.numero(k4["valor"], 3), "Entre el estrato moda del barrio y su tasa de severos.")
            with c2:
                componentes.tarjeta("Barrios incluidos", formato.numero(k4["denominador"]), "Solo barrios con suficientes construcciones con datos.")
            with c3:
                componentes.tarjeta("p de permutación", formato.numero(p, 4) if p is not None else formato.SIN_DATO, "Prueba de permutaciones con semilla fija.")
            st.caption("Es descriptivo y a nivel de barrio (falacia ecológica); no es una prueba de causalidad.")
        st.markdown("**Lectura generada.** " + redaccion.conclusion_concentracion(k3, k4))

    componentes.marco(api, ID, cuerpo)
