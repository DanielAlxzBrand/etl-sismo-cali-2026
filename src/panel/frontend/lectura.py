"""Herramientas de lectura de una página: guía, curiosidades, aviso, modo presentación y exportación.

El componente (`lectura.js`) recibe solo texto y lo escribe con `textContent`. La exportación es un botón de descarga nativo de Streamlit: el archivo lo arma Python con los datos de la API.
"""
import streamlit as st

from src.panel.frontend import activos

_componente = st.components.v2.component("lectura_panel", html=activos.texto("plantillas", "herramientas.html"), js=activos.texto("lectura.js"), isolate_styles=False)


def herramientas(id_pagina, titulo, guia, fichas, descarga, nombre_archivo, etiqueta="Exportar figura"):
    """Barra de herramientas de lectura con su botón de exportación (`etiqueta`). `descarga` son los bytes del documento ya armado."""
    with st.container(key="barra_herramientas"):
        izquierda, derecha = st.columns([4, 1], vertical_alignment="top")
        with izquierda:
            _componente(data=dict(slug=id_pagina, titulo=titulo, guia=guia, fichas=fichas), key="lectura_" + id_pagina)
        with derecha, st.container(key="exportar"):
            st.download_button(etiqueta, data=descarga, file_name=nombre_archivo, mime="text/html", key="descarga_" + id_pagina, help="Descarga el contenido de la página y su alcance en un archivo HTML")
