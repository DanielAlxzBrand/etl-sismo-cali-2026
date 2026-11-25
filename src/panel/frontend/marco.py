"""Marco de las páginas con interfaz propia: estado de la API, lienzo con la estructura del diseño, cuerpo y pie.

Conserva el comportamiento de `componentes.marco`: si la API no responde, el cuerpo no se ejecuta y se muestra el aviso; si responde con una forma inesperada, se informa sin trazas ni rutas.
La cabecera con título, pregunta, alcance y glosario la dibuja el cuerpo (`frontend.estratos.cabecera`), porque necesita los datos de la página.
"""
from dataclasses import dataclass

import streamlit as st

from src.logger import get_logger
from src.panel import componentes, formato, registro
from src.panel.frontend import estilos, navegacion

log = get_logger(__name__)


def dibujar(html):
    """Dibuja un bloque de HTML de la interfaz propia. Los bloques los arma `frontend/estratos.py` con todo texto de los datos ya escapado; Streamlit los sanea además al mostrarlos."""
    st.html(html)


@dataclass(frozen=True)
class Contexto:
    pagina: object
    grupo: str
    corte: str
    metadata: object
    salud: object


def marco(api, id_pagina, cuerpo):
    """Dibuja la página dentro del contenedor `lienzo`; `cuerpo(contexto)` hace el resto."""
    pagina = registro.pagina(id_pagina)
    try:
        salud = api("/health")
        meta = api("/metadata")
        metadata = meta.datos if meta.ok else None
        datos_salud = salud.datos if salud.ok and isinstance(salud.datos, dict) else {}
        contexto = Contexto(pagina, navegacion.grupo_de(id_pagina), datos_salud.get("fecha_corte") or formato.SIN_DATO, metadata, salud)
        with st.container(key="lienzo"):
            st.html(estilos.hoja_pagina(id_pagina))
            componentes.encabezado(salud)
            if not salud.ok:
                st.title(pagina.titulo)
                st.caption(pagina.pregunta)
                componentes.recuadro_alcance(metadata)
                componentes.fallo(salud)
            else:
                cuerpo(contexto)
            componentes.pie(metadata)
    except (KeyError, TypeError, ValueError, AttributeError, IndexError):
        log.exception("la página %s recibió datos con un formato inesperado", id_pagina)
        st.warning("Los datos recibidos de la API no tienen el formato esperado; no se pueden mostrar.", icon=":material/warning:")
