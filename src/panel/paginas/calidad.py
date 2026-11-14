"""Página «Calidad de la llave»: cobertura de la llave, estrato válido y nombre validado (K5), y los códigos que requieren revisión."""
import pandas as pd
import streamlit as st

from src.panel import componentes, formato

ID = "calidad"


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


def _metrica(titulo, bloque, decimales):
    componentes.tarjeta(titulo, formato.porcentaje(bloque["pct"], decimales), f"{formato.numero(bloque['num'])} de {formato.numero(bloque['den'])} construcciones")


def render(api):
    def cuerpo():
        r = api("/calidad")
        if componentes.fallo(r):
            return
        q = r.datos
        c1, c2, c3 = st.columns(3)
        with c1:
            _metrica("Cobertura de la llave", q["cobertura_llave"], 3)
        with c2:
            _metrica("Estrato válido", q["cobertura_estrato_valido"], 3)
        with c3:
            _metrica("Nombre validado", q["pct_nombre_validado"]["global"], 2)
        st.markdown(f"**Confianza de la llave:** {q['llave_confianza']}")
        st.subheader("Nombre validado según la coincidencia con el polígono")
        componentes.tabla(pd.DataFrame([
            {"Grupo": "Todas las construcciones con llave", "Con nombre validado": formato.numero(q["pct_nombre_validado"]["global"]["num"]),
             "Total": formato.numero(q["pct_nombre_validado"]["global"]["den"]), "Porcentaje": formato.porcentaje(q["pct_nombre_validado"]["global"]["pct"], 2)},
            {"Grupo": "El código coincide con el polígono", "Con nombre validado": formato.numero(q["pct_nombre_validado"]["coincide_poligono_true"]["num"]),
             "Total": formato.numero(q["pct_nombre_validado"]["coincide_poligono_true"]["den"]), "Porcentaje": formato.porcentaje(q["pct_nombre_validado"]["coincide_poligono_true"]["pct"], 2)},
            {"Grupo": "El código no coincide con el polígono", "Con nombre validado": formato.numero(q["pct_nombre_validado"]["coincide_poligono_false"]["num"]),
             "Total": formato.numero(q["pct_nombre_validado"]["coincide_poligono_false"]["den"]), "Porcentaje": formato.porcentaje(q["pct_nombre_validado"]["coincide_poligono_false"]["pct"], 2)},
        ]))
        st.subheader("Códigos de barrio sin nombre validado")
        rev = api("/llave/revision")
        if componentes.fallo(rev):
            return
        items = rev.datos["items"]
        st.caption(f"{formato.numero(rev.datos['total_codigos'])} códigos; detalle en {rev.datos['documento']}.")
        componentes.tabla(pd.DataFrame([{
            "Código": i["codigo_barrio"], "Construcciones": formato.numero(i["n_construcciones"]), "Nombre en el CSV de estrato": i["nombre_csv_2015"],
            "Nombre del polígono": i["nombre_poligono_dominante"], "Coincidencia con el polígono": formato.porcentaje(i["pct_coincide_poligono"], 0),
            "Clasificación": clasificar(i),
        } for i in items]))
        st.info("Qué NO demuestra: que el estrato asignado al barrio refleje el de cada construcción hoy, ni que el nombre validado garantice que el código sea el correcto; "
                "la renumeración de códigos entre fuentes es una explicación documentada de estas diferencias, no una mala asignación comprobada.")

    componentes.marco(api, ID, cuerpo)
