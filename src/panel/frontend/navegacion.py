"""Barra lateral del panel: marca, enlaces a las ocho páginas agrupados y la imagen de la ciudad. La navegación nativa se oculta y esta la reemplaza con las mismas páginas y el mismo orden."""
from html import escape

import streamlit as st

from src.panel import registro
from src.panel.frontend import estilos

GRUPOS = (("Resultados", ("respuesta", "estratos", "comunas", "sensibilidades")), ("Territorio y evidencia", ("concentracion", "calidad", "construcciones")), ("Documentación", ("fuentes",)))
ICONOS = {"respuesta": "speed", "estratos": "layers", "comunas": "map", "sensibilidades": "tune", "concentracion": "scatter_plot", "calidad": "key", "construcciones": "apartment", "fuentes": "database"}


def grupo_de(id_pagina):
    return next(nombre for nombre, ids in GRUPOS if id_pagina in ids)


def barra_lateral(paginas):
    """Dibuja la barra en `st.sidebar`. `paginas` es un diccionario id → `st.Page`."""
    with st.sidebar, st.container(key="rail_final", gap="small"):
        st.html(estilos.hoja_global())
        st.html(f'<div class="marca-lateral"><span class="icono" aria-hidden="true" style="background-image:{estilos.marca()}"></span><div><strong>Sismo de Cali</strong><small>Panel de consulta</small></div></div>')
        with st.container(key="menu", gap=None):
            for grupo, ids in GRUPOS:
                st.html(f'<div class="grupo-lateral">{escape(grupo)}</div>')
                for id_pagina in ids:
                    st.page_link(paginas[id_pagina], label=registro.pagina(id_pagina).titulo, icon=f":material/{ICONOS[id_pagina]}:")
        with st.container(key="cali_pie"):
            st.html('<span class="cali" aria-hidden="true"></span>')
