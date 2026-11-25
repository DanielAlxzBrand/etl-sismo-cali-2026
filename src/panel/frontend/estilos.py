"""Hojas de estilo de la interfaz: una global (marco, barra lateral, componentes de lectura) y una pequeña por página.

Los colores de las categorías de los gráficos salen de la paleta Okabe-Ito de `config.yaml` (`tema.colores`); el resto de la interfaz usa la paleta verde de los archivos CSS.
"""
import json
from base64 import b64encode
from functools import lru_cache

from src.panel import tema
from src.panel.frontend import activos

ORDEN = ("marco", "lectura", "acabado", "rail", "integracion")   # el orden del diseño aprobado: marco, lectura, acabado y, al final, el patrón de iconos y la barra lateral
PORTADAS = {"estratos": "capas"}
TEXTURAS = {"respuesta": "respuesta.svg", "estratos": "estratos.svg", "comunas": "comunas.svg", "sensibilidades": "sensibilidades.svg", "concentracion": "concentracion.svg",
            "calidad": "calidad.svg", "construcciones": "construcciones.svg", "fuentes": "fuentes.svg"}


def _uri_trazo(trazo):
    svg = activos.plantilla("iconos", "trazo.svg").substitute(trazo=trazo)
    return "data:image/svg+xml;base64," + b64encode(svg.encode("utf-8")).decode("ascii")


@lru_cache(maxsize=None)
def hoja_global():
    """`<style>` con los pictogramas, las variables de categoría, la imagen lateral y todos los CSS de la interfaz."""
    trazos = json.loads(activos.texto("iconos", "trazos.json"))
    colores = tema.colores()
    variables = [f'--ico-{nombre}:url("{_uri_trazo(trazo)}")' for nombre, trazo in trazos.items()]
    variables += [f"--cat-suficiente:{colores['principal']}", f"--cat-baja:{colores['secundario']}", f'--cali:url("{activos.uri_datos("imagenes", "cali_lateral.webp")}")']
    css = "\n".join(activos.texto("estilos", nombre + ".css") for nombre in ORDEN)
    return "<style>:root{" + ";".join(variables) + "}\n" + css + "</style>"


@lru_cache(maxsize=None)
def hoja_pagina(id_pagina):
    """`<style>` de una página: pictograma de portada y, si la tiene, la textura del territorio de fondo."""
    portada = PORTADAS.get(id_pagina, id_pagina)
    textura = TEXTURAS.get(id_pagina)
    fondo = f'--territorio:url("{activos.uri_datos("texturas", textura)}");' if textura else ""
    return f"<style>.st-key-lienzo{{--portada:var(--ico-{portada});{fondo}}}</style>"


def marca():
    """Imagen de la marca de la barra lateral como valor de `background-image`."""
    return "url(" + activos.uri_datos("iconos", "marca.svg") + ")"
