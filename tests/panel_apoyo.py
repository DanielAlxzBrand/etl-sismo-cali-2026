"""Apoyo de las pruebas del panel: la API real en memoria sobre una copia temporal de la SQLite, y el armado de páginas con AppTest.

Nada de esto toca `data/`: la copia vive en una carpeta temporal y la API la abre en solo lectura.
"""
import shutil
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest

from src.api.app import crear_app
from src.panel.cliente_api import ClienteApi, Resultado

RAIZ = Path(__file__).resolve().parents[1]
BASE = RAIZ / "data" / "gold" / "etl_sismo.db"
CAMPO_SCRIPT = "from tests.panel_apoyo import api_actual\nfrom src.panel.paginas import {modulo}\n{modulo}.render(api_actual())\n"
_ACTUAL = {}


def copia_temporal_de_la_base():
    """Copia de etl_sismo.db en una carpeta temporal (la API la abre en solo lectura); devuelve (carpeta, ruta)."""
    carpeta = Path(tempfile.mkdtemp(prefix="panel_base_"))
    destino = carpeta / "etl_sismo.db"
    shutil.copyfile(BASE, destino)
    return carpeta, destino


def api_en_memoria(ruta_db):
    """(TestClient, ClienteApi) conectados en memoria a la aplicación real de la API sobre `ruta_db`."""
    http = TestClient(crear_app(ruta_db=ruta_db), base_url="http://api.local")
    return http, ClienteApi("http://api.local", http=http, dormir=lambda s: None)


def como_consulta(cliente):
    """Función `api(ruta, **params)` sin caché, como la que reciben las páginas."""
    def api(ruta, **params):
        return cliente.obtener(ruta, params)
    return api


def fijar_api(api):
    _ACTUAL["api"] = api


def api_actual():
    return _ACTUAL["api"]


def pagina(modulo, api, tiempo=30):
    """AppTest de la página `modulo` (por ejemplo, 'respuesta') con la consulta `api`; ya ejecutada."""
    fijar_api(api)
    at = AppTest.from_string(CAMPO_SCRIPT.format(modulo=modulo), default_timeout=tiempo)
    return at.run()


def resultado_error(tipo, mensaje="error de prueba", estado=None):
    from src.panel.cliente_api import ErrorApi
    return Resultado(False, None, ErrorApi(tipo, mensaje, estado), "")


def textos(at):
    """Todo el texto visible de la página (markdown, subtítulos, avisos, métricas y pies), para comprobar contenido."""
    partes = []
    for grupo in (at.markdown, at.caption, at.subheader, at.title, at.warning, at.info, at.error, at.success):
        partes += [e.value for e in grupo]
    for m in at.metric:
        partes += [m.label, m.value, m.help or ""]
    return "\n".join(str(p) for p in partes)
