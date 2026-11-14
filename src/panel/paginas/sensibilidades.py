"""Página «Sensibilidades (S0 a S5)»: diferencia 3-5 menos 1-2 con su intervalo por escenario y razón ajustada por comuna."""
import re

import pandas as pd
import streamlit as st

from src.panel import claves, componentes, formato, redaccion

ID = "sensibilidades"


def _fila(filas, escenario, grupo):
    return next((f for f in filas if f["kpi_id"] == claves.K2 and f["escenario"] == escenario and f["grupo"] == grupo), None)


def comunas_usadas(nota):
    """Cantidad de comunas que la nota de la razón ajustada dice haber usado; None si la nota no trae ese dato."""
    m = re.search(r"comunas usadas:([^;]*)", nota or "")
    if m is None:
        return None
    return len([c for c in m.group(1).split(",") if c.strip()])


def render(api):
    def cuerpo():
        r = api("/kpis/sensibilidad")
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
        componentes.grafico_diferencias(df, "escenario", "Diferencia de tasas (3-5 menos 1-2) por escenario",
                                        "Diferencia de tasas entre los estratos 3-5 y 1-2 en cada escenario, con su intervalo de Newcombe y una línea en 0.")
        st.subheader("Escenarios y resultados")
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
        componentes.tabla(pd.DataFrame(tabla))
        st.markdown("**Lectura generada.** " + redaccion.conclusion_sensibilidades([{"escenario": e, **d} for e, d in zip(escenarios, difs)]))
        for e, d in zip(escenarios, difs):
            st.markdown("- " + redaccion.conclusion_escenario(e, d))
        st.subheader("Razón ajustada por comuna (Mantel-Haenszel)")
        for e in escenarios:
            mh = _fila(filas, e, claves.K2_MANTEL_HAENSZEL)
            st.warning(f"{e}: " + redaccion.aviso_mantel_haenszel(mh, comunas_usadas((mh or {}).get("nota"))), icon=":material/info:")
        with st.expander("Notas completas de la razón ajustada por escenario"):
            for e in escenarios:
                mh = _fila(filas, e, claves.K2_MANTEL_HAENSZEL)
                st.markdown(f"**{e}.** " + ((mh or {}).get("nota") or formato.SIN_DATO))

    componentes.marco(api, ID, cuerpo)
