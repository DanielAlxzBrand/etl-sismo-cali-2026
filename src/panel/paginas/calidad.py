"""Página «Calidad de la llave»: cobertura de la llave, estrato válido y nombre validado (K5), y los códigos que requieren revisión.

Desde D115 y D116 lleva la cabecera, el glosario, la guía, las curiosidades, el modo presentación y la exportación de la interfaz propia; las cifras se dibujan como tarjetas del diseño y las
tablas y avisos siguen siendo los componentes nativos de siempre. Los datos, el formato y los textos no cambiaron.
"""
import pandas as pd
import streamlit as st

from src.panel import componentes, formato
from src.panel.frontend import lectura
from src.panel.frontend import vista as base
from src.panel.frontend.marco import dibujar, marco

ID = "calidad"
NO_DEMUESTRA = ("Qué NO demuestra: que el estrato asignado al barrio refleje el de cada construcción hoy, ni que el nombre validado garantice que el código sea el correcto; "
                "la renumeración de códigos entre fuentes es una explicación documentada de estas diferencias, no una mala asignación comprobada.")


def clasificar(item):
    """Clasificación del código derivada de la coincidencia con el polígono (la API no entrega una categoría)."""
    pct = item.get("pct_coincide_poligono")
    if pct is None:
        return "sin dato de coincidencia"
    if pct >= 1:
        return "el código coincide con el polígono; el nombre se escribe distinto"
    if pct <= 0:
        return "el código no coincide con el polígono (renumeración de códigos)"
    return "coincidencia parcial con el polígono"


def _tarjeta(titulo, bloque, decimales):
    return (titulo, formato.porcentaje(bloque["pct"], decimales), f"{formato.numero(bloque['num'])} de {formato.numero(bloque['den'])} construcciones")


def tarjetas_k5(q):
    """Las tres tarjetas de cobertura: llave, estrato válido y nombre validado."""
    return [_tarjeta("Cobertura de la llave", q["cobertura_llave"], 3), _tarjeta("Estrato válido", q["cobertura_estrato_valido"], 3), _tarjeta("Nombre validado", q["pct_nombre_validado"]["global"], 2)]


def tabla_nombre_validado(q):
    """DataFrame de «Nombre validado según la coincidencia con el polígono»: todas, con código coincidente y con código no coincidente."""
    v = q["pct_nombre_validado"]
    filas = [("Todas las construcciones con llave", v["global"]), ("El código coincide con el polígono", v["coincide_poligono_true"]), ("El código no coincide con el polígono", v["coincide_poligono_false"])]
    return pd.DataFrame([{"Grupo": g, "Con nombre validado": formato.numero(b["num"]), "Total": formato.numero(b["den"]), "Porcentaje": formato.porcentaje(b["pct"], 2)} for g, b in filas])


def tabla_revision(items):
    """DataFrame de los códigos de barrio sin nombre validado, con su clasificación."""
    return pd.DataFrame([{
        "Código": i["codigo_barrio"], "Construcciones": formato.numero(i["n_construcciones"]), "Nombre en el CSV de estrato": i["nombre_csv_2015"],
        "Nombre del polígono": i["nombre_poligono_dominante"], "Coincidencia con el polígono": formato.porcentaje(i["pct_coincide_poligono"], 0),
        "Clasificación": clasificar(i),
    } for i in items])


def render(api):
    def cuerpo(contexto):
        r = api("/calidad")
        dibujar(base.cabecera(contexto.pagina, contexto.grupo, contexto.corte, contexto.metadata))
        if componentes.fallo(r):
            return
        q = r.datos
        tarjetas, nombre, confianza = tarjetas_k5(q), tabla_nombre_validado(q), f"**Confianza de la llave:** {q['llave_confianza']}"
        rev = api("/llave/revision")
        items = rev.datos["items"] if rev.ok else None
        revision = tabla_revision(items) if items is not None else None
        resumen = f"{formato.numero(rev.datos['total_codigos'])} códigos; detalle en {rev.datos['documento']}." if rev.ok else None
        informe = _informe(contexto, tarjetas, confianza, nombre, revision, resumen)
        lectura.herramientas(ID, contexto.pagina.titulo, base.guia(ID), base.curiosidades(ID), informe, "calidad_de_la_llave.html", "Exportar informe")
        with st.container(key="contenido_analitico"):
            dibujar(base.tarjetas(tarjetas))
            st.markdown(confianza)
            st.subheader("Nombre validado según la coincidencia con el polígono")
            componentes.tabla(nombre)
            st.subheader("Códigos de barrio sin nombre validado")
            if componentes.fallo(rev):
                return
            st.caption(resumen)
            componentes.tabla(revision, texto_largo=True)
            st.info(NO_DEMUESTRA)
        dibujar(base.pie_pagina())

    marco(api, ID, cuerpo)


def _informe(contexto, tarjetas, confianza, nombre, revision, resumen):
    """Informe HTML autónomo con las tarjetas, las dos tablas, el resumen de la revisión y el aviso de lo que no demuestra."""
    partes = base.fichas_html(tarjetas) + base.parrafos([confianza.replace("**", "")]) + base.tabla_simple(nombre, "Nombre validado según la coincidencia con el polígono", "Nombre validado")
    if revision is not None:
        partes += base.tabla_simple(revision, "Códigos de barrio sin nombre validado", "Códigos para revisión", resumen)
    return base.documento(contexto.pagina, contexto.grupo, contexto.corte, contexto.metadata, base.panel("detalle", "Cobertura y validación de la llave", partes), NO_DEMUESTRA)
