"""Lectura de los recursos de la capa de interfaz (CSS, JavaScript, plantillas, imágenes, texturas y textos de apoyo).

Es el único módulo del panel que lee archivos distintos del YAML de configuración (D115) y solo lee dentro de esta carpeta: `ruta` rechaza cualquier camino que salga de ella.
Qué NO hace: no lee datos ni resultados; los datos llegan siempre por el cliente de la API.
"""
import json
from base64 import b64encode
from functools import lru_cache
from pathlib import Path
from string import Template

BASE = Path(__file__).resolve().parent
TIPOS = {".svg": "image/svg+xml", ".webp": "image/webp"}


def ruta(*partes):
    """Ruta absoluta de un recurso de esta carpeta; lanza ValueError si sale de ella."""
    destino = BASE.joinpath(*partes).resolve()
    if not destino.is_relative_to(BASE):
        raise ValueError("el recurso pedido está fuera de la carpeta de la interfaz")
    return destino


@lru_cache(maxsize=None)
def texto(*partes):
    return ruta(*partes).read_text(encoding="utf-8")


@lru_cache(maxsize=None)
def contenido(nombre):
    """Texto de apoyo de una página (guía, curiosidades, glosario de lectura), de `contenido/<nombre>.json`."""
    return json.loads(texto("contenido", nombre + ".json"))


def plantilla(*partes):
    return Template(texto(*partes))


@lru_cache(maxsize=None)
def uri_datos(*partes):
    """URI `data:` con el archivo en base64, para usarlo como fondo CSS sin servir archivos estáticos."""
    destino = ruta(*partes)
    return "data:" + TIPOS[destino.suffix] + ";base64," + b64encode(destino.read_bytes()).decode("ascii")
