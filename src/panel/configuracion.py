"""Lee solo la clave `panel` de config/config.yaml (sin secretos y sin tocar el archivo de credenciales).

La única variable de entorno que acepta es `PANEL_API_URL`, que el lanzador usa cuando la API queda en un puerto distinto del configurado;
solo se admite una dirección local (127.0.0.1, localhost o ::1): el panel no habla con servidores remotos.
"""
import os
from pathlib import Path
from urllib.parse import urlparse

import yaml

RAIZ = Path(__file__).resolve().parents[2]
RUTA_CONFIG = RAIZ / "config" / "config.yaml"
VARIABLE_URL = "PANEL_API_URL"
HOSTS_LOCALES = ("127.0.0.1", "localhost", "::1")


def validar_url_local(url):
    """Devuelve la URL si es http y apunta a esta máquina; si no, lanza ValueError."""
    partes = urlparse(url)
    if partes.scheme != "http" or partes.hostname not in HOSTS_LOCALES:
        raise ValueError("el panel solo se conecta a una API local (http en 127.0.0.1)")
    return url.rstrip("/")


def cargar_panel(ruta=None, entorno=None):
    """Diccionario de la clave `panel`; falla con un mensaje claro si falta. `PANEL_API_URL` sustituye a `api_url`."""
    with open(ruta or RUTA_CONFIG, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if not isinstance(cfg, dict) or "panel" not in cfg:
        raise KeyError("config.yaml no tiene la clave `panel`")
    panel = dict(cfg["panel"])
    url = (os.environ if entorno is None else entorno).get(VARIABLE_URL)
    panel["api_url"] = validar_url_local(url or panel["api_url"])
    return panel
