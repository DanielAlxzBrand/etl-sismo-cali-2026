"""Página «Estratos (K1)»: tasa por estrato con intervalo de Wilson, muestra baja visible y cotas por «sin datos».

Desde D115 la página se dibuja con la interfaz propia de `src/panel/frontend/` (figura de barras, puntos y tabla, glosario, guía, curiosidades, modo presentación y exportación).
Los datos, el formato de las cifras y la redacción son los de siempre: `tabla_k1`, `avisos_k1` y `redaccion.conclusion_estratos` no cambiaron.
"""
import pandas as pd
import streamlit as st

from src.panel import componentes, formato, redaccion
from src.panel.frontend import estratos as vista
from src.panel.frontend import lectura
from src.panel.frontend.marco import dibujar, marco

ID = "estratos"
NOTA_COTAS = ("Las cotas por «sin datos» son extremas (todo lo que falta sin daño, o todo con daño): no son estimaciones; "
              "si las cotas de dos estratos se solapan, su orden no es identificable.")


def _etiqueta(grupo):
    return str(grupo).replace("estrato_", "Estrato ")


def etiquetas_k1(filas):
    return [_etiqueta(f["grupo"]) for f in filas]


def tabla_k1(filas):
    """DataFrame de texto de «Detalle por estrato»: una fila por estrato, con las cifras ya formateadas."""
    etiquetas = etiquetas_k1(filas)
    return pd.DataFrame([{
        "Estrato": etiquetas[i] + (f" ({componentes.ETIQUETA_BAJA})" if f["muestra_baja"] else ""),
        "Severos": formato.numero(f["numerador"]), "Con datos": formato.numero(f["denominador"]), "Tasa": formato.porcentaje(f["valor"]),
        "Intervalo de Wilson": formato.intervalo(f["ic95_inf"], f["ic95_sup"]), "Sin datos": formato.numero(f["n_sin_datos"]),
        "% sin datos": formato.porcentaje(f["pct_sin_datos"], 1), "Cotas por «sin datos»": formato.intervalo(f["cota_inf"], f["cota_sup"]),
    } for i, f in enumerate(filas)])


def avisos_k1(filas):
    """Avisos sobre los estratos con más faltantes y con menos construcciones con datos."""
    mas_falta = max(filas, key=lambda f: f["pct_sin_datos"] or 0)
    menos = min(filas, key=lambda f: f["denominador"] or 0)
    notas = [f"El estrato con más construcciones sin datos satelitales es {_etiqueta(mas_falta['grupo'])} ({formato.porcentaje(mas_falta['pct_sin_datos'], 1)}): "
             f"su tasa podría estar entre {formato.porcentaje(mas_falta['cota_inf'], 1)} y {formato.porcentaje(mas_falta['cota_sup'], 1)}, y la falta de datos no es aleatoria."]
    if menos["muestra_baja"]:
        notas.append(f"El estrato con menos construcciones con datos es {_etiqueta(menos['grupo'])} ({formato.numero(menos['denominador'])}): "
                     "su intervalo es muy amplio y no permite compararlo con los demás.")
    return notas


def render(api):
    def cuerpo(contexto):
        r = api("/kpis/K1")
        filas = r.datos if r.ok else None
        dibujar(vista.cabecera(contexto.pagina, contexto.grupo, contexto.corte, contexto.metadata, filas if filas else None))
        if componentes.fallo(r):
            return
        if not filas:
            st.warning("La API no devolvió filas de K1.")
            return
        etiquetas = etiquetas_k1(filas)
        tabla = tabla_k1(filas)
        conclusion = redaccion.conclusion_estratos(filas)
        avisos = avisos_k1(filas)
        descarga = vista.lamina(contexto.pagina, contexto.grupo, contexto.corte, contexto.metadata, filas, etiquetas, tabla, conclusion, NOTA_COTAS)
        lectura.herramientas(ID, contexto.pagina.titulo, vista.guia(filas, etiquetas), vista.fichas(), descarga, "estratos_tasa_por_estrato.html")
        dibujar(vista.cuerpo(filas, etiquetas, tabla, conclusion, avisos, NOTA_COTAS))

    marco(api, ID, cuerpo)
