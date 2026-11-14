"""Ayudas compartidas por las páginas: selección de filas de la API y armado de tablas con texto ya formateado."""
import pandas as pd
import streamlit as st

from src.panel import formato
from src.panel.componentes import ETIQUETA_BAJA, ETIQUETA_SUFICIENTE


def por_grupo(filas, kpi_id, grupo=None):
    """Primera fila del KPI (y grupo) pedido; None si no está."""
    return next((f for f in filas if f.get("kpi_id") == kpi_id and (grupo is None or f.get("grupo") == grupo)), None)


def avisar_falta(nombre):
    st.warning(f"La API no devolvió {nombre}; no se puede mostrar este componente.", icon=":material/warning:")


def texto_ic(inferior, superior):
    return formato.intervalo(inferior, superior)


def filas_tasa(filas, etiquetas, clave_tasa="valor"):
    """DataFrame para `grafico_tasas`: una fila por elemento de `filas` con tasa y límites en porcentaje y los textos de la ayuda."""
    registros = []
    for fila, etiqueta in zip(filas, etiquetas):
        tasa, inf, sup = fila.get(clave_tasa), fila.get("ic95_inf"), fila.get("ic95_sup")
        baja = bool(fila.get("muestra_baja"))
        registros.append({
            "grupo": etiqueta + (f" ({ETIQUETA_BAJA})" if baja else ""),
            "tasa_pct": None if tasa is None else tasa * 100,
            "inf_pct": None if inf is None else inf * 100,
            "sup_pct": None if sup is None else sup * 100,
            "muestra": ETIQUETA_BAJA if baja else ETIQUETA_SUFICIENTE,
            "tasa_txt": formato.porcentaje(tasa),
            "ic_txt": texto_ic(inf, sup),
        })
    return pd.DataFrame(registros)
