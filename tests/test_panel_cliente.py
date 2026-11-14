"""Cliente HTTP del panel: solo GET, traducción de cada fallo a un resultado tipado y caché que no guarda errores. Transporte simulado con httpx."""
import httpx
import pytest

from src.panel import cliente_api
from src.panel.cliente_api import ClienteApi, crear_cliente
from src.panel.configuracion import cargar_panel, validar_url_local


def _cliente(manejador, reintentos=1, dormidos=None):
    http = httpx.Client(transport=httpx.MockTransport(manejador))
    return ClienteApi("http://api.local", reintentos_conexion=reintentos, http=http, dormir=(dormidos.append if dormidos is not None else (lambda s: None)))


def test_una_respuesta_correcta_devuelve_los_datos():
    c = _cliente(lambda req: httpx.Response(200, json={"estado": "ok"}))
    r = c.obtener("/health")
    assert r.ok and r.datos == {"estado": "ok"} and r.error is None


def test_solo_usa_get_y_omite_los_parametros_nulos():
    vistos = []

    def manejador(req):
        vistos.append((req.method, str(req.url)))
        return httpx.Response(200, json=[])
    _cliente(manejador).obtener("/construcciones", {"limit": 5, "comuna": None, "estrato": 3})
    assert vistos == [("GET", "http://api.local/construcciones?limit=5&estrato=3")]


@pytest.mark.parametrize("estado,tipo", [(404, "no_encontrado"), (422, "parametros_invalidos"), (503, "base_no_disponible"), (500, "error_servidor"), (502, "error_servidor"), (418, "error_http")])
def test_cada_estado_http_se_traduce_a_un_error_tipado_en_espanol(estado, tipo):
    r = _cliente(lambda req: httpx.Response(estado, json={"error": {"codigo": "x", "mensaje": "m"}})).obtener("/x")
    assert not r.ok and r.error.tipo == tipo and r.error.estado == estado
    assert r.error.mensaje == cliente_api.MENSAJES[tipo] and "Traceback" not in r.error.mensaje


def test_json_mal_formado_es_respuesta_invalida():
    r = _cliente(lambda req: httpx.Response(200, content=b"{no es json")).obtener("/x")
    assert not r.ok and r.error.tipo == "respuesta_invalida"


def test_cuerpo_vacio_con_200_es_respuesta_invalida():
    assert _cliente(lambda req: httpx.Response(200, content=b"")).obtener("/x").error.tipo == "respuesta_invalida"


def test_tiempo_agotado_no_se_reintenta():
    llamadas = []

    def manejador(req):
        llamadas.append(1)
        raise httpx.ReadTimeout("lento", request=req)
    r = _cliente(manejador, reintentos=3).obtener("/x")
    assert r.error.tipo == "tiempo_agotado" and len(llamadas) == 1


def test_error_de_conexion_se_reintenta_una_vez_y_luego_dice_api_apagada():
    llamadas, dormidos = [], []

    def manejador(req):
        llamadas.append(1)
        raise httpx.ConnectError("sin conexión", request=req)
    r = _cliente(manejador, reintentos=1, dormidos=dormidos).obtener("/x")
    assert r.error.tipo == "api_apagada" and len(llamadas) == 2 and len(dormidos) == 1


def test_la_conexion_que_se_recupera_en_el_reintento_devuelve_datos():
    estado = {"n": 0}

    def manejador(req):
        estado["n"] += 1
        if estado["n"] == 1:
            raise httpx.ConnectError("caída breve", request=req)
        return httpx.Response(200, json=[1])
    assert _cliente(manejador).obtener("/x").datos == [1]


def test_sin_reintentos_configurados_falla_a_la_primera():
    llamadas = []

    def manejador(req):
        llamadas.append(1)
        raise httpx.ConnectError("x", request=req)
    _cliente(manejador, reintentos=0).obtener("/x")
    assert len(llamadas) == 1


def test_otro_error_de_transporte_es_error_http():
    def manejador(req):
        raise httpx.ReadError("cortado", request=req)
    assert _cliente(manejador).obtener("/x").error.tipo == "error_http"


def test_obtener_nunca_lanza_excepciones():
    for excepcion in (httpx.ConnectError("a"), httpx.ReadTimeout("b"), httpx.ReadError("c"), httpx.RemoteProtocolError("d")):
        def manejador(req, e=excepcion):
            raise e
        assert _cliente(manejador).obtener("/x").ok is False


def test_los_mensajes_no_llevan_rutas_ni_trazas():
    for mensaje in cliente_api.MENSAJES.values():
        assert "\\" not in mensaje and "Traceback" not in mensaje and "/" not in mensaje


def test_la_configuracion_crea_el_cliente_con_la_url_local():
    c = crear_cliente(cargar_panel(entorno={}))
    try:
        assert c.url_base.startswith("http://127.0.0.1")
    finally:
        c.cerrar()


@pytest.mark.parametrize("url", ["http://127.0.0.1:9000", "http://localhost:8000", "http://[::1]:8000"])
def test_se_aceptan_las_direcciones_locales(url):
    assert validar_url_local(url) == url


@pytest.mark.parametrize("url", ["https://127.0.0.1:8000", "http://example.org:8000", "http://192.168.1.5:8000", "ftp://127.0.0.1", "http://0.0.0.0:8000"])
def test_se_rechazan_las_direcciones_no_locales_o_sin_http(url):
    with pytest.raises(ValueError):
        validar_url_local(url)


def test_la_variable_del_lanzador_sustituye_la_url_de_la_configuracion():
    assert cargar_panel(entorno={"PANEL_API_URL": "http://127.0.0.1:9123"})["api_url"] == "http://127.0.0.1:9123"
    with pytest.raises(ValueError):
        cargar_panel(entorno={"PANEL_API_URL": "http://example.org"})


def test_la_cache_no_guarda_los_fallos_y_si_guarda_los_aciertos():
    import streamlit as st

    st.cache_data.clear()
    estado = {"api_arriba": False, "llamadas": 0}

    def manejador(req):
        estado["llamadas"] += 1
        if not estado["api_arriba"]:
            return httpx.Response(503, json={})
        return httpx.Response(200, json={"v": estado["llamadas"]})
    consultar = cliente_api.consulta_con_cache(_cliente(manejador, reintentos=0), ttl_s=60)
    assert consultar("/x").error.tipo == "base_no_disponible"
    estado["api_arriba"] = True
    primero = consultar("/x")
    assert primero.ok
    llamadas = estado["llamadas"]
    assert consultar("/x").datos == primero.datos and estado["llamadas"] == llamadas   # segunda vez: desde la caché
    st.cache_data.clear()


def test_la_clave_de_la_cache_distingue_los_parametros():
    import streamlit as st

    st.cache_data.clear()
    consultar = cliente_api.consulta_con_cache(_cliente(lambda req: httpx.Response(200, json={"u": str(req.url)})), ttl_s=60)
    a, b = consultar("/construcciones", limit=1), consultar("/construcciones", limit=2)
    assert a.datos != b.datos
    st.cache_data.clear()
