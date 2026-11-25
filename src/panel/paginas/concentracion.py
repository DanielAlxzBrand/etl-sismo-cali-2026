"""Página «Concentración (K3 y K4)»: los barrios con más construcciones con cambio satelital severo y la correlación de Spearman.

Desde D115 y D116 lleva la cabecera, el glosario, la guía, las curiosidades, el modo presentación y la exportación de la interfaz propia; las cifras se dibujan como tarjetas del diseño y la tabla,
los avisos y la lectura siguen siendo los componentes nativos de siempre. Los datos, el formato y los textos no cambiaron.
"""
import re

import pandas as pd
import streamlit as st

from src.panel import claves, componentes, formato, redaccion
from src.panel.frontend import lectura
from src.panel.frontend import vista as base
from src.panel.frontend.marco import dibujar, marco
from src.panel.paginas._comun import avisar_falta, por_grupo

ID = "concentracion"
NOTA_K3 = "Los barrios con más casos también tienen más construcciones: concentración de casos no es mayor riesgo. Se excluyen los casos sin barrio asignado."
NOTA_K4 = "Es descriptivo y a nivel de barrio (falacia ecológica); no es una prueba de causalidad."


def barrios_de_la_nota(nota):
    """[(código, severos)] leídos de la nota de K3 («códigos:severos 1914:30; 1913:25; …»).

    Se lee todo lo que hay después de «severos » hasta la primera letra y debe ser exactamente una lista de pares «código:severos» separados por «; ».
    Si algo no encaja (otro separador, un par incompleto), devuelve una lista vacía y la página muestra la nota tal cual (D78): una lectura a medias
    mostraría una tabla con menos barrios de los que hay.
    """
    m = re.search(r"severos ((?:(?![^\W\d_]).)*)", nota or "")
    if m is None:
        return []
    cuerpo = m.group(1).rstrip("; ")
    if re.fullmatch(r"\d+:\d+(?:; \d+:\d+)*", cuerpo) is None:
        return []
    return [(par.split(":")[0], int(par.split(":")[1])) for par in cuerpo.split("; ")]


def construcciones_de_la_nota(nota):
    """(construcciones con datos de esos barrios, total con datos) leídos de «(2292 de 4709)»; None si no están."""
    m = re.search(r"\((\d+) de (\d+)\)", nota or "")
    return (int(m.group(1)), int(m.group(2))) if m else None


def p_permutacion(nota):
    """p de la prueba de permutación leído de «p_permutacion=0.8218»; None si no está o no es un número bien formado.

    Un punto al final (el de la frase) no forma parte del número; «0.8218.5» o «.» no son números y devuelven None en lugar de fallar.
    """
    m = re.search(r"p_permutacion=(\d+(?:\.\d+)?)(?!\.?\d)", nota or "")
    return float(m.group(1)) if m else None


def tarjetas_k3(k3):
    """Las tarjetas de K3 como `(etiqueta, valor, detalle)`; la segunda solo si la nota trae las construcciones de esos barrios."""
    items = [("Severos en barrios líderes", formato.porcentaje(k3["valor"], 1),
              f"Participación de los barrios con más severos en el total de severos. {k3['nombre']}: {formato.numero(k3['numerador'])} de {formato.numero(k3['denominador'])} construcciones con cambio satelital severo")]
    share = construcciones_de_la_nota(k3["nota"])
    if share:
        items.append(("Peso de esos barrios", formato.porcentaje(share[0] / share[1], 1), f"Esos barrios en el total de construcciones con datos: {formato.numero(share[0])} de {formato.numero(share[1])}"))
    return items


def tabla_k3(k3):
    """DataFrame de los barrios líderes de K3, o None si la nota no tiene el formato esperado (se muestra la nota tal cual)."""
    barrios = barrios_de_la_nota(k3["nota"])
    if not barrios:
        return None
    total = k3["denominador"]
    return pd.DataFrame([{"Código de barrio": c, "Severos": formato.numero(n), "Participación en los severos": formato.porcentaje(n / total, 1)} for c, n in barrios])


def tarjetas_k4(k4):
    """Las tres tarjetas de K4: correlación de Spearman, barrios incluidos y valor p de permutación."""
    p = p_permutacion(k4["nota"])
    return [("Correlación", formato.numero(k4["valor"], 3), "Correlación de Spearman entre el estrato moda del barrio y su tasa de severos."),
            ("Barrios incluidos", formato.numero(k4["denominador"]), "Solo barrios con suficientes construcciones con datos."),
            ("p de permutación", formato.numero(p, 4) if p is not None else formato.SIN_DATO, "Prueba de permutaciones con semilla fija.")]


def render(api):
    """Dibuja la página «Concentración (K3 y K4)»: los barrios con más severos y la correlación de Spearman entre estrato y tasa por barrio.

    Si la nota de K3 no tiene el formato esperado, muestra la nota tal cual en lugar de una tabla a medias (DEF-015).
    """
    def cuerpo(contexto):
        r = api("/kpis")
        dibujar(base.cabecera(contexto.pagina, contexto.grupo, contexto.corte, contexto.metadata))
        if componentes.fallo(r):
            return
        k3, k4 = por_grupo(r.datos, claves.K3, claves.K3_TOP10), por_grupo(r.datos, claves.K4)
        conclusion = redaccion.conclusion_concentracion(k3, k4)
        items3 = tarjetas_k3(k3) if k3 else None
        tabla3 = tabla_k3(k3) if k3 else None
        items4 = tarjetas_k4(k4) if k4 else None
        informe = _informe(contexto, items3, tabla3, k3, items4, conclusion)
        lectura.herramientas(ID, contexto.pagina.titulo, base.guia(ID), base.curiosidades(ID), informe, "concentracion_barrios_y_spearman.html", "Exportar informe")
        with st.container(key="contenido_analitico"):
            st.subheader("K3 · Concentración de los casos")
            if not k3:
                avisar_falta("el indicador K3")
            else:
                dibujar(base.tarjetas(items3))
                if tabla3 is not None:
                    componentes.tabla(tabla3)
                else:
                    st.info(k3["nota"] or "La API no trae el detalle de los barrios.")
                st.caption(NOTA_K3)
            st.subheader("K4 · Estrato y tasa por barrio (Spearman)")
            if not k4:
                avisar_falta("el indicador K4")
            else:
                dibujar(base.tarjetas(items4))
                st.caption(NOTA_K4)
            st.markdown("**Lectura generada.** " + conclusion)
        dibujar(base.pie_pagina())

    marco(api, ID, cuerpo)


def _informe(contexto, items3, tabla3, k3, items4, conclusion):
    """Informe HTML autónomo con las mismas tarjetas, la tabla de barrios (o la nota tal cual), las notas y la lectura generada."""
    k3_html = base.fichas_html(items3) if items3 else base.parrafos(["La API no devolvió el indicador K3."])
    if items3:
        k3_html += base.tabla_simple(tabla3, "Barrios con más severos", "Barrios líderes") if tabla3 is not None else base.parrafos([k3["nota"] or "La API no trae el detalle de los barrios."])
        k3_html += base.parrafos([NOTA_K3])
    k4_html = (base.fichas_html(items4) + base.parrafos([NOTA_K4])) if items4 else base.parrafos(["La API no devolvió el indicador K4."])
    cuerpo = base.panel("detalle", "K3 · Concentración de los casos", k3_html) + base.panel("detalle", "K4 · Estrato y tasa por barrio (Spearman)", k4_html)
    return base.documento(contexto.pagina, contexto.grupo, contexto.corte, contexto.metadata, cuerpo, conclusion)
