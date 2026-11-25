"""Página «Sensibilidades (S0 a S5)»: diferencia 3-5 menos 1-2 con su intervalo por escenario y razón ajustada por comuna.

Desde D115 lleva la cabecera, el glosario, la guía, las curiosidades, el modo presentación y la exportación de la interfaz propia; el gráfico (Okabe-Ito), la tabla y los avisos siguen siendo
los componentes nativos de siempre, dentro del contenedor de análisis del diseño aprobado. Los datos, el formato y los textos no cambiaron.
"""
import re

import pandas as pd
import streamlit as st

from src.panel import claves, componentes, formato, redaccion
from src.panel.frontend import lectura
from src.panel.frontend import sensibilidades as vista
from src.panel.frontend import vista as base
from src.panel.frontend.marco import dibujar, marco

ID = "sensibilidades"


def _fila(filas, escenario, grupo):
    return next((f for f in filas if f["kpi_id"] == claves.K2 and f["escenario"] == escenario and f["grupo"] == grupo), None)


def comunas_usadas(nota):
    """Cantidad de comunas que la nota de la razón ajustada dice haber usado; None si la nota no trae ese dato."""
    m = re.search(r"comunas usadas:([^;]*)", nota or "")
    if m is None:
        return None
    return len([c for c in m.group(1).split(",") if c.strip()])


def tabla_escenarios(filas, escenarios):
    """DataFrame de texto de «Escenarios y resultados»: una fila por escenario, con las cifras ya formateadas."""
    tabla = []
    for e in escenarios:
        t35, t12 = _fila(filas, e, claves.K2_TASA_3_5), _fila(filas, e, claves.K2_TASA_1_2)
        dif, razon = _fila(filas, e, claves.K2_DIFERENCIA), _fila(filas, e, claves.K2_RAZON)
        mh = _fila(filas, e, claves.K2_MANTEL_HAENSZEL)
        tabla.append({
            "Escenario": e, "Filtro o definición": (razon or {}).get("nota") or formato.SIN_DATO,
            "Tasa 3-5": formato.porcentaje((t35 or {}).get("tasa")), "Tasa 1-2": formato.porcentaje((t12 or {}).get("tasa")),
            "Diferencia": formato.puntos_porcentuales(dif["tasa"]), "Intervalo de Newcombe": formato.intervalo(dif["ic95_inf"], dif["ic95_sup"], como="pp"),
            "Razón ajustada (MH)": formato.razon((mh or {}).get("tasa")),
        })
    return pd.DataFrame(tabla)


def avisos_mh(filas, escenarios):
    """Aviso de Mantel-Haenszel de cada escenario, con el texto de `redaccion`."""
    out = []
    for e in escenarios:
        mh = _fila(filas, e, claves.K2_MANTEL_HAENSZEL)
        out.append(f"{e}: " + redaccion.aviso_mantel_haenszel(mh, comunas_usadas((mh or {}).get("nota"))))
    return out


def notas_mh(filas, escenarios):
    """Nota completa de la razón ajustada de cada escenario."""
    return [f"{e}. " + ((_fila(filas, e, claves.K2_MANTEL_HAENSZEL) or {}).get("nota") or formato.SIN_DATO) for e in escenarios]


def render(api):
    def cuerpo(contexto):
        r = api("/kpis/sensibilidad")
        dibujar(base.cabecera(contexto.pagina, contexto.grupo, contexto.corte, contexto.metadata))
        if componentes.fallo(r):
            return
        filas = r.datos
        escenarios = [e for e in claves.ESCENARIOS if _fila(filas, e, claves.K2_DIFERENCIA)]
        if not escenarios:
            st.warning("La API no devolvió escenarios de sensibilidad.")
            return
        difs = [_fila(filas, e, claves.K2_DIFERENCIA) for e in escenarios]
        df = pd.DataFrame([{
            "escenario": e, "dif_pp": d["tasa"] * 100, "inf_pp": d["ic95_inf"] * 100, "sup_pp": d["ic95_sup"] * 100,
            "dif_txt": formato.puntos_porcentuales(d["tasa"]), "ic_txt": formato.intervalo(d["ic95_inf"], d["ic95_sup"], como="pp"),
        } for e, d in zip(escenarios, difs)])
        tabla = tabla_escenarios(filas, escenarios)
        conclusion = redaccion.conclusion_sensibilidades([{"escenario": e, **d} for e, d in zip(escenarios, difs)])
        avisos, notas = avisos_mh(filas, escenarios), notas_mh(filas, escenarios)
        documento = vista.documento(contexto.pagina, contexto.grupo, contexto.corte, contexto.metadata, escenarios, difs, tabla, conclusion, avisos, notas)
        lectura.herramientas(ID, contexto.pagina.titulo, base.guia(ID), base.curiosidades(ID), documento, "sensibilidades_escenarios.html", "Exportar informe")
        with st.container(key="contenido_analitico"):
            componentes.grafico_diferencias(df, "escenario", "Diferencia de tasas (3-5 menos 1-2) por escenario",
                                            "Diferencia de tasas entre los estratos 3-5 y 1-2 en cada escenario, con su intervalo de Newcombe y una línea en 0.")
            st.subheader("Escenarios y resultados")
            componentes.tabla(tabla)
            st.markdown("**Lectura generada.** " + conclusion)
            for e, d in zip(escenarios, difs):
                st.markdown("- " + redaccion.conclusion_escenario(e, d))
            st.subheader("Razón ajustada por comuna (Mantel-Haenszel)")
            for aviso in avisos:
                st.warning(aviso, icon=":material/info:")
            with st.expander("Notas completas de la razón ajustada por escenario"):
                for e, nota in zip(escenarios, notas_mh(filas, escenarios)):
                    st.markdown(f"**{e}.** " + nota[len(e) + 2:])
        dibujar(vista.pie_de_pagina())

    marco(api, ID, cuerpo)
