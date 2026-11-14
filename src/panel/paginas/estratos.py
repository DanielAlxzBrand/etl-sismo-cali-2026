"""Página «Estratos (K1)»: tasa por estrato con intervalo de Wilson, muestra baja visible y cotas por «sin datos»."""
import pandas as pd
import streamlit as st

from src.panel import componentes, formato, redaccion
from src.panel.paginas._comun import filas_tasa, texto_ic

ID = "estratos"


def _etiqueta(grupo):
    return str(grupo).replace("estrato_", "Estrato ")


def render(api):
    def cuerpo():
        r = api("/kpis/K1")
        if componentes.fallo(r):
            return
        filas = r.datos
        if not filas:
            st.warning("La API no devolvió filas de K1.")
            return
        etiquetas = [_etiqueta(f["grupo"]) for f in filas]
        componentes.grafico_tasas(filas_tasa(filas, etiquetas), "grupo", "Tasa de cambio satelital severo por estrato",
                                  "Barras de la tasa por estrato con su intervalo de Wilson; los estratos con muestra baja llevan esa etiqueta.",
                                  titulo_x="Estrato (por lados de manzana)")
        st.subheader("Detalle por estrato")
        tabla = pd.DataFrame([{
            "Estrato": etiquetas[i] + (f" ({componentes.ETIQUETA_BAJA})" if f["muestra_baja"] else ""),
            "Severos": formato.numero(f["numerador"]), "Con datos": formato.numero(f["denominador"]), "Tasa": formato.porcentaje(f["valor"]),
            "Intervalo de Wilson": texto_ic(f["ic95_inf"], f["ic95_sup"]), "Sin datos": formato.numero(f["n_sin_datos"]),
            "% sin datos": formato.porcentaje(f["pct_sin_datos"], 1), "Cotas por «sin datos»": texto_ic(f["cota_inf"], f["cota_sup"]),
        } for i, f in enumerate(filas)])
        componentes.tabla(tabla)
        st.caption("Las cotas por «sin datos» son extremas (todo lo que falta sin daño, o todo con daño): no son estimaciones; "
                   "si las cotas de dos estratos se solapan, su orden no es identificable.")
        st.markdown("**Lectura generada.** " + redaccion.conclusion_estratos(filas))
        mas_falta = max(filas, key=lambda f: f["pct_sin_datos"] or 0)
        menos = min(filas, key=lambda f: f["denominador"] or 0)
        notas = [f"El estrato con más construcciones sin datos satelitales es {_etiqueta(mas_falta['grupo'])} ({formato.porcentaje(mas_falta['pct_sin_datos'], 1)}): "
                 f"su tasa podría estar entre {formato.porcentaje(mas_falta['cota_inf'], 1)} y {formato.porcentaje(mas_falta['cota_sup'], 1)}, y la falta de datos no es aleatoria."]
        if menos["muestra_baja"]:
            notas.append(f"El estrato con menos construcciones con datos es {_etiqueta(menos['grupo'])} ({formato.numero(menos['denominador'])}): "
                         "su intervalo es muy amplio y no permite compararlo con los demás.")
        for n in notas:
            st.info(n)

    componentes.marco(api, ID, cuerpo)
