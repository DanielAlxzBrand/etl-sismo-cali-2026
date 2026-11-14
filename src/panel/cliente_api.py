"""Cliente HTTP de solo lectura de la API: único punto por el que el panel obtiene datos.

Solo usa GET. Traduce todo fallo (API apagada, 503, 404, 422, JSON inválido, tiempo agotado) a un `Resultado` tipado con un mensaje en español,
sin trazas ni rutas. Reintenta una vez únicamente los errores de conexión. La caché de Streamlit solo guarda respuestas correctas, de modo que
un fallo no se queda «pegado» cuando la API vuelve.
"""
import time
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx

from src.logger import get_logger
from src.panel.configuracion import cargar_panel

log = get_logger(__name__)

MENSAJES = {
    "api_apagada": "No se pudo conectar con la API. Verifique que esté en marcha y vuelva a intentarlo.",
    "tiempo_agotado": "La API tardó demasiado en responder. Vuelva a intentarlo en unos segundos.",
    "base_no_disponible": "La API está en marcha, pero el almacenamiento de datos no está disponible.",
    "no_encontrado": "La API no tiene el recurso solicitado.",
    "parametros_invalidos": "La API rechazó los parámetros de la consulta.",
    "respuesta_invalida": "La respuesta de la API no tiene el formato esperado.",
    "error_servidor": "La API informó un error interno.",
    "error_http": "La API respondió con un error inesperado.",
}


@dataclass(frozen=True)
class ErrorApi:
    tipo: str
    mensaje: str
    estado: Optional[int] = None


@dataclass(frozen=True)
class Resultado:
    """Resultado de una consulta: `datos` si salió bien; `error` si no. Nunca lleva excepciones ni trazas."""
    ok: bool
    datos: Any = None
    error: Optional[ErrorApi] = None
    ruta: str = field(default="")


def _error(tipo, ruta, estado=None):
    return Resultado(False, None, ErrorApi(tipo, MENSAJES[tipo], estado), ruta)


class ClienteApi:
    """GET a la API. `http` permite inyectar un cliente httpx (por ejemplo, uno conectado en memoria a la aplicación real)."""

    def __init__(self, url_base, tiempo_espera=10.0, reintentos_conexion=1, espera_reintento=0.3, http=None, dormir=time.sleep):
        self.url_base = url_base.rstrip("/")
        self.reintentos_conexion = max(0, int(reintentos_conexion))
        self.espera_reintento = espera_reintento
        self._dormir = dormir
        self._propio = http is None
        self._http = http if http is not None else httpx.Client(timeout=tiempo_espera)

    def cerrar(self):
        if self._propio:
            self._http.close()

    def obtener(self, ruta, params=None):
        """GET `ruta` con parámetros opcionales (los None se omiten). Devuelve un `Resultado`; nunca lanza."""
        parametros = {k: v for k, v in (params or {}).items() if v is not None}
        url = self.url_base + ruta
        respuesta = None
        for intento in range(self.reintentos_conexion + 1):
            try:
                respuesta = self._http.get(url, params=parametros)
                break
            except httpx.TimeoutException:
                log.warning("tiempo agotado en %s", ruta)
                return _error("tiempo_agotado", ruta)
            except httpx.ConnectError:
                if intento < self.reintentos_conexion:
                    self._dormir(self.espera_reintento)
                    continue
                log.warning("sin conexión con la API en %s", ruta)
                return _error("api_apagada", ruta)
            except httpx.HTTPError:
                log.warning("error de transporte en %s", ruta)
                return _error("error_http", ruta)
        return self._traducir(ruta, respuesta)

    def _traducir(self, ruta, respuesta):
        estado = respuesta.status_code
        if estado == 200:
            try:
                return Resultado(True, respuesta.json(), None, ruta)
            except ValueError:
                return _error("respuesta_invalida", ruta, estado)
        tipo = {404: "no_encontrado", 422: "parametros_invalidos", 503: "base_no_disponible"}.get(estado)
        if tipo is None:
            tipo = "error_servidor" if estado >= 500 else "error_http"
        return _error(tipo, ruta, estado)


def crear_cliente(config=None, http=None, dormir=time.sleep):
    """Cliente con los parámetros de la clave `panel` de config.yaml."""
    cfg = config or cargar_panel()
    return ClienteApi(cfg["api_url"], cfg["tiempo_espera_s"], cfg["reintentos_conexion"], cfg["espera_reintento_s"], http=http, dormir=dormir)


def consulta_con_cache(cliente, ttl_s):
    """Función `consultar(ruta, **params)` que usa `st.cache_data` con tiempo de vida `ttl_s` y solo guarda respuestas correctas.

    La clave de la caché es (URL base, ruta, parámetros); el cliente no entra en la clave. Un fallo no se guarda.
    """
    import streamlit as st

    class _Fallo(Exception):
        def __init__(self, resultado):
            super().__init__(resultado.error.tipo)
            self.resultado = resultado

    @st.cache_data(ttl=ttl_s, show_spinner=False)
    def _correcta(url_base, ruta, params_ordenados):
        r = cliente.obtener(ruta, dict(params_ordenados))
        if not r.ok:
            raise _Fallo(r)
        return r.datos

    def consultar(ruta, **params):
        limpios = tuple(sorted((k, v) for k, v in params.items() if v is not None))
        try:
            return Resultado(True, _correcta(cliente.url_base, ruta, limpios), None, ruta)
        except _Fallo as f:
            return f.resultado

    return consultar
