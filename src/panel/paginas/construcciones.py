"""Página «Construcciones»: tabla paginada con filtros que la API aplica, dispersión lon/lat y descarga CSV de lo mostrado.

Desde D115 y D116 lleva la cabecera, el glosario, la guía, las curiosidades, el modo presentación y la exportación de la interfaz propia, y permite elegir una fila para leerla en palabras.
Los filtros, la consulta paginada de la API, la tabla, la descarga y la dispersión son los de siempre: la página nunca pide todas las construcciones, solo la página que se ve.
"""
import math

import pandas as pd
import streamlit as st

from src.panel import claves, componentes, formato
from src.panel.configuracion import cargar_panel
from src.panel.frontend import lectura
from src.panel.frontend import vista as base
from src.panel.frontend.marco import dibujar, marco

ID = "construcciones"
TODAS = "Todas"
OPCIONES_SEVERO = {TODAS: None, "Solo con cambio satelital severo": True, "Sin cambio satelital severo": False}
AVISO_SIN_FILA = "Seleccione una fila de la tabla para leerla en palabras. Al cambiar de página o de filtros la selección se limpia."
INICIO_PELIGROSO =("=", "+", "-", "@", "\t", "\r")   # una celda que empieza así se interpreta como fórmula en una hoja de cálculo


def _si_no(valor):
    return formato.SIN_DATO if valor is None else ("Sí" if valor else "No")


def tabla_de_items(items):
    """DataFrame de texto de la página mostrada (también es el contenido del CSV descargable)."""
    return pd.DataFrame([{
        "Construcción": i["objectid"], "Comuna": i["comuna"] or formato.SIN_DATO, "Barrio": i["barrio"] or formato.SIN_DATO,
        "Código de barrio": i["codigo_barrio"] or formato.SIN_DATO, "Estrato": formato.numero(i["estrato"]) if i["estrato"] is not None else formato.SIN_DATO,
        "Clase de daño": i["clase_dano"] or formato.SIN_DATO, "Cambio severo": _si_no(i["severo_estricto"]), "Nombre validado": _si_no(i["nombre_validado"]),
    } for i in items])


def csv_seguro(df):
    """Bytes del CSV de la tabla mostrada. Las celdas de texto que empiezan con «=», «+», «-», «@», tabulación o retorno de carro llevan una comilla simple delante para que una hoja de cálculo
    no las ejecute como fórmula; el resto del contenido es el de siempre (UTF-8, mismos encabezados, sin índice)."""
    def neutralizar(valor):
        return "'" + valor if isinstance(valor, str) and valor.startswith(INICIO_PELIGROSO) else valor

    return df.map(neutralizar).to_csv(index=False).encode("utf-8")


def clave_de_seleccion(comuna, estrato, severo, pagina):
    """Clave de la tabla seleccionable: cambia con cualquier filtro y con la página, así una fila elegida en una consulta no queda marcada en otra (selección obsoleta)."""
    return f"registros_{comuna}_{estrato}_{severo}_{pagina}"


def descripcion_de_fila(item):
    """La fila en palabras: qué construcción es, dónde está y qué dice su clase satelital; solo usa los valores de la fila."""
    barrio = item["barrio"] or formato.SIN_DATO
    severo = {True: "cuenta como cambio satelital severo", False: "no cuenta como cambio satelital severo", None: "no tiene clasificación satelital, así que no entra en las tasas"}[item["severo_estricto"]]
    return (f"La construcción {item['objectid']} está en el barrio {barrio} de la comuna {item['comuna'] or formato.SIN_DATO}. Su clase satelital es «{item['clase_dano'] or formato.SIN_DATO}» y {severo}. "
            f"El estrato {formato.numero(item['estrato']) if item['estrato'] is not None else formato.SIN_DATO} es el de su barrio, no el de la construcción. Nombre del barrio validado: {_si_no(item['nombre_validado'])}.")


def fila_elegida(evento, items):
    """Índice de la fila elegida en la tabla, o None si no hay selección o ya no existe en esta página (selección obsoleta)."""
    filas = getattr(getattr(evento, "selection", None), "rows", None) or []
    return filas[0] if filas and 0 <= filas[0] < len(items) else None


def _opciones_comuna(api):
    r = api("/comunas")
    return [TODAS] + sorted({f["comuna"] for f in r.datos}) if r.ok else [TODAS]


def _opciones_estrato(api):
    r = api("/kpis/K1")
    if not r.ok:
        return [TODAS]
    return [TODAS] + sorted({f["grupo"].replace("estrato_", "") for f in r.datos if str(f.get("grupo", "")).startswith("estrato_")})


def render(api):
    """Dibuja la página «Construcciones»: filtros, tabla paginada que filtra la API, descarga del CSV y ubicación de las construcciones de la página.

    El título del gráfico de ubicación es corto (F-04, D87): a 390 px Vega cortaba el anterior («…, por c…»).
    """
    def cuerpo(contexto):
        tamano = int(cargar_panel()["tamano_pagina_tabla"])
        dibujar(base.cabecera(contexto.pagina, contexto.grupo, contexto.corte, contexto.metadata))
        herramientas = st.container()      # se llena al final: la guía y el informe dependen de la consulta
        consulta = None
        with st.container(key="contenido_analitico"):
            f1, f2, f3 = st.columns(3)
            with f1:
                comuna = st.selectbox("Comuna", _opciones_comuna(api), key="filtro_comuna")
            with f2:
                estrato = st.selectbox("Estrato", _opciones_estrato(api), key="filtro_estrato")
            with f3:
                severo = st.selectbox("Cambio satelital severo", list(OPCIONES_SEVERO), key="filtro_severo")
            pagina = st.number_input("Página", min_value=1, value=1, step=1, key="pagina")
            r = api("/construcciones", limit=tamano, offset=(int(pagina) - 1) * tamano, comuna=None if comuna == TODAS else comuna,
                    estrato=None if estrato == TODAS else int(estrato), severo_estricto=OPCIONES_SEVERO[severo])
            if componentes.fallo(r):
                return
            datos = r.datos
            paginas = max(1, math.ceil(datos["total"] / tamano))
            resumen = (f"{formato.numero(datos['total'])} construcciones con estos filtros; página {formato.numero(pagina)} de {formato.numero(paginas)}. "
                       "Los filtros los aplica la API sobre toda la muestra, no solo sobre la página mostrada.")
            st.caption(resumen)
            if not datos["items"]:
                st.info("No hay construcciones en esta página con estos filtros.")
                consulta = (resumen, None, None)
            else:
                df = tabla_de_items(datos["items"])
                evento = componentes.tabla(df, clave=clave_de_seleccion(comuna, estrato, severo, pagina), seleccion=True)
                elegida = fila_elegida(evento, datos["items"])
                with st.expander("Qué significa esta fila", expanded=elegida is not None):
                    st.markdown(descripcion_de_fila(datos["items"][elegida]) if elegida is not None else AVISO_SIN_FILA)
                st.download_button("Descargar CSV (filas mostradas)", csv_seguro(df), file_name="construcciones_pagina.csv", mime="text/csv", key="descarga_csv")
                con_coord = pd.DataFrame([i for i in datos["items"] if i["lon"] is not None and i["lat"] is not None])
                if con_coord.empty:
                    st.info("Ninguna construcción de esta página trae coordenadas.")
                else:
                    con_coord["barrio"] = con_coord["barrio"].fillna(formato.SIN_DATO)
                    con_coord["clase_dano"] = con_coord["clase_dano"].fillna(formato.SIN_DATO)
                    componentes.dispersion(con_coord, "Ubicación por clase de daño",
                                           "Dispersión de longitud y latitud de las construcciones mostradas, con clase de daño distinguida por color y forma.", claves.CLASES_DANO)
                consulta = (resumen, df, datos["items"])
        if consulta is not None:
            resumen, df, items = consulta
            ejemplo = f"{resumen.split('; página')[0]}; esta página muestra {formato.numero(len(items or []))} filas."
            informe = _informe(contexto, resumen, df)
            with herramientas:
                lectura.herramientas(ID, contexto.pagina.titulo, base.guia(ID, ejemplo), base.curiosidades(ID), informe, "construcciones_pagina.html", "Exportar informe")
        dibujar(base.pie_pagina())

    marco(api, ID, cuerpo)


def _informe(contexto, resumen, df):
    """Informe HTML autónomo con la consulta, las filas mostradas (con todo valor escapado) y los avisos de alcance."""
    cuerpo = base.parrafos([resumen])
    cuerpo += base.tabla_simple(df, "Registros de la consulta", "Registros de la consulta", nota="Longitud y latitud se expresan en grados decimales. La ubicación es una dispersión, no un mapa.") if df is not None \
        else base.parrafos(["No hay construcciones en esta página con estos filtros."])
    return base.documento(contexto.pagina, contexto.grupo, contexto.corte, contexto.metadata, base.panel("detalle", "Construcciones de la consulta", cuerpo))
