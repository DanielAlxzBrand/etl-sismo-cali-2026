"""Aplicación Streamlit del panel (solo lectura): navegación explícita entre las páginas del registro.

Ejecución: python -m streamlit run src/panel/app.py   (o el lanzador `python scripts/panel/ejecutar_panel.py`, que también arranca la API).
"""
import streamlit as st

from src.panel import registro
from src.panel.cliente_api import consulta_con_cache, crear_cliente
from src.panel.configuracion import cargar_panel
from src.panel.paginas import calidad, comunas, concentracion, construcciones, estratos, fuentes, respuesta, sensibilidades

MODULOS = {m.ID: m for m in (respuesta, estratos, comunas, sensibilidades, concentracion, calidad, construcciones, fuentes)}


@st.cache_resource(show_spinner=False)
def _api():
    """Consulta con caché sobre el cliente HTTP de la API; se crea una vez por proceso."""
    cfg = cargar_panel()
    return consulta_con_cache(crear_cliente(cfg), cfg["ttl_cache_s"])


def _pagina(id_pagina, api, por_defecto):
    def ejecutar():
        MODULOS[id_pagina].render(api)

    p = registro.pagina(id_pagina)
    return st.Page(ejecutar, title=p.titulo, url_path=p.url_path, default=por_defecto)


def principal():
    st.set_page_config(page_title="Panel · cambio satelital y estrato", layout="wide", initial_sidebar_state="expanded", menu_items={})
    api = _api()
    paginas = [_pagina(p.id, api, i == 0) for i, p in enumerate(registro.PAGINAS)]
    st.navigation(paginas).run()


if __name__ == "__main__":
    principal()
