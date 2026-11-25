"""Apoyo de las pruebas del panel: la API real en memoria sobre una copia temporal de la SQLite, y el armado de páginas con AppTest.

Nada de esto toca `data/`: la copia vive en una carpeta temporal y la API la abre en solo lectura.
"""
import re
import shutil
from collections import namedtuple
import tempfile
from html import unescape
from html.parser import HTMLParser
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


def texto_html(at, sin_glosario=False):
    """Texto visible de los bloques `st.html` de la página (D115): sin etiquetas, sin hojas de estilo y con las entidades ya resueltas; `sin_glosario` quita el glosario de la cabecera."""
    partes = []
    for h in at.html:
        limpio = re.sub(r"(?is)<style.*?</style>", " ", h.value)
        if sin_glosario:
            limpio = re.sub(r'(?is)<details class="glos".*?</details>', " ", limpio)
        limpio = re.sub(r"(?i)</?(?:b|i|em|strong|span|small|a|summary)\b[^>]*>", "", limpio)       # las etiquetas en línea no separan palabras
        partes.append(unescape(re.sub(r"<[^>]+>", " ", limpio)))
    return re.sub(r"[ \t]+", " ", "\n".join(partes))


def textos(at):
    """Todo el texto visible de la página (markdown, subtítulos, avisos, métricas, pies y bloques HTML de la interfaz propia), para comprobar contenido."""
    partes = []
    for grupo in (at.markdown, at.caption, at.subheader, at.title, at.warning, at.info, at.error, at.success):
        partes += [e.value for e in grupo]
    for m in at.metric:
        partes += [m.label, m.value, m.help or ""]
    partes.append(texto_html(at))
    return "\n".join(str(p) for p in partes)


PAGINAS_CON_INTERFAZ_PROPIA = ("respuesta", "estratos", "comunas", "sensibilidades", "concentracion", "calidad", "construcciones", "fuentes")   # D115: se dibujan con `src/panel/frontend/`; las demás siguen con los componentes nativos hasta que se integren


def titulo(at):
    """Título de la página: el `st.title` nativo o, en las páginas con interfaz propia (D115), el `h1` de su cabecera."""
    if at.title:
        return at.title[0].value
    for h in at.html:
        m = re.search(r"(?s)<h1>(.*?)</h1>", h.value)
        if m:
            return unescape(m.group(1))
    return None


def pregunta_visible(at, pregunta):
    """True si la pregunta de la página aparece como pie nativo o como párrafo de la cabecera propia."""
    return pregunta in [c.value for c in at.caption] or pregunta in texto_html(at)


class _Tablas(HTMLParser):
    """Extrae las tablas de un HTML como listas de filas de texto. En la primera celda de cada fila solo cuenta el rótulo (`summary`), no su explicación."""

    def __init__(self):
        super().__init__()
        self.tablas, self._fila, self._celda, self._ignorar = [], None, None, 0

    def handle_starttag(self, etiqueta, atributos):
        if etiqueta == "table":
            self.tablas.append([])
        elif etiqueta == "tr":
            self._fila = []
        elif etiqueta in ("td", "th"):
            self._celda = []
        elif etiqueta == "p" and self._celda is not None:
            self._ignorar += 1

    def handle_endtag(self, etiqueta):
        if etiqueta == "p" and self._ignorar:
            self._ignorar -= 1
        elif etiqueta in ("td", "th") and self._celda is not None:
            self._fila.append(re.sub(r"\s+", " ", "".join(self._celda)).strip())
            self._celda = None
        elif etiqueta == "tr" and self._fila is not None:
            self.tablas[-1].append(self._fila)
            self._fila = None

    def handle_data(self, datos):
        if self._celda is not None and not self._ignorar:
            self._celda.append(datos)


def tablas_html(at):
    """Tablas de los bloques `st.html` de la página: lista de tablas, cada una lista de filas (la primera es el encabezado)."""
    analizador = _Tablas()
    for h in at.html:
        analizador.feed(h.value)
    return analizador.tablas


Ficha = namedtuple("Ficha", "label value help")


def fichas_html(at):
    """Tarjetas de cifras `(etiqueta, valor, detalle)` de los bloques `st.html` de la página (D115)."""
    out = []
    for h in at.html:
        for m in re.finditer(r'<div class="ficha">(.*?)<b>(.*?)</b>(?:<small>(.*?)</small>)?</div>', h.value, re.S):
            etiqueta = re.sub(r"<[^>]+>", "", m.group(1))
            out.append(Ficha(unescape(etiqueta).replace(" · ", " · ").strip(), unescape(m.group(2)), unescape(m.group(3) or "")))
    return out


def tabla_html_df(at, indice=0):
    """La tabla número `indice` de los bloques `st.html` como DataFrame de texto (la primera fila es el encabezado)."""
    import pandas as pd
    tabla = tablas_html(at)[indice]
    return pd.DataFrame(tabla[1:], columns=tabla[0])


def glosario_html(at):
    """[(término, definición)] del glosario de la cabecera propia (`details.glos`) y si va cerrado, o (None, None) si la página no lo trae."""
    for h in at.html:
        m = re.search(r'(?s)<details class="glos"(?P<abierto>[^>]*)>(?P<cuerpo>.*?)</details>', h.value)
        if m:
            pares = re.findall(r"<b>(.*?)</b><p>(.*?)</p>", m.group("cuerpo"))
            return [(unescape(n), unescape(d)) for n, d in pares], "open" not in m.group("abierto")
    return None, None
