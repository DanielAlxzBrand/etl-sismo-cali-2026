"""Páginas del panel con AppTest (interfaz ↔ lógica) sobre la API REAL en memoria, y su resiliencia ante cada tipo de fallo de la API."""
import shutil

import httpx
import pytest

from src.panel import registro
from src.panel.cliente_api import ClienteApi
from tests import panel_apoyo as pa

PAGINAS = [p.id for p in registro.PAGINAS]
PROHIBIDAS = ["el estrato no influye", "prevalencia en Cali", "la prevalencia de Cali", "Traceback", 'File "']
ALCANCE = ("proxy de daño", "condicionales a esta muestra", "no son prevalencias de Cali")


@pytest.fixture(scope="module")
def entorno():
    carpeta, ruta = pa.copia_temporal_de_la_base()
    http, cliente = pa.api_en_memoria(ruta)
    yield http, cliente
    cliente.cerrar()
    http.close()
    shutil.rmtree(carpeta, ignore_errors=True)


@pytest.fixture(scope="module")
def renderizadas(entorno):
    api = pa.como_consulta(entorno[1])
    return {p: pa.pagina(p, api) for p in PAGINAS}


def _con_fallo(entorno, ruta_objetivo, accion):
    """API cuyo único cambio es que `ruta_objetivo` falla de la forma indicada (el resto lo responde la aplicación real)."""
    http, _ = entorno

    def manejador(req):
        if req.url.path == ruta_objetivo:
            return accion(req)
        real = http.get(req.url.path, params=dict(req.url.params))
        return httpx.Response(real.status_code, content=real.content)
    cliente = ClienteApi("http://api.local", http=httpx.Client(transport=httpx.MockTransport(manejador)), reintentos_conexion=0)
    return pa.como_consulta(cliente)


def _todo_cae(accion):
    cliente = ClienteApi("http://api.local", http=httpx.Client(transport=httpx.MockTransport(lambda req: accion(req))), reintentos_conexion=0, dormir=lambda s: None)
    return pa.como_consulta(cliente)


def _sin_traza(at):
    assert len(at.exception) == 0
    texto = pa.textos(at)
    for p in ("Traceback", 'File "', "Error:", "Exception"):
        assert p not in texto


# ---------- cada página ----------
@pytest.mark.parametrize("pagina", PAGINAS)
def test_cada_pagina_se_renderiza_sin_excepciones_y_con_titulo_y_pregunta(renderizadas, pagina):
    at = renderizadas[pagina]
    assert len(at.exception) == 0
    p = registro.pagina(pagina)
    assert at.title[0].value == p.titulo
    assert p.pregunta in [c.value for c in at.caption]


@pytest.mark.parametrize("pagina", PAGINAS)
def test_cada_pagina_muestra_el_recuadro_de_alcance(renderizadas, pagina):
    texto = pa.textos(renderizadas[pagina])
    for frase in ALCANCE:
        assert frase in texto
    assert "Estrato 2015 asignado por lados de manzana" in texto


@pytest.mark.parametrize("pagina", PAGINAS)
def test_ninguna_pagina_contiene_cadenas_prohibidas(renderizadas, pagina):
    texto = pa.textos(renderizadas[pagina])
    for cadena in PROHIBIDAS:
        assert cadena not in texto


@pytest.mark.parametrize("pagina", PAGINAS)
def test_cada_pagina_muestra_la_fecha_de_corte_el_estado_de_la_api_y_la_fuente(renderizadas, pagina):
    captions = [c.value for c in renderizadas[pagina].caption]
    assert any(c.startswith("API: en línea") and "fecha de corte: 2026-09-02" in c for c in captions)
    assert any(c.startswith("Fuente:") and "Licencias" in c for c in captions)


@pytest.mark.parametrize("pagina,fragmentos", [
    ("respuesta", ["Tasa de los estratos 3-5", "Tasa de los estratos 1-2 (muestra baja)", "Diferencia (3-5 menos 1-2)", "Razón de tasas (3-5 / 1-2)", "Cobertura de la llave", "Estrato válido", "Nombre validado"]),
    ("concentracion", ["Correlación de Spearman", "Barrios incluidos", "p de permutación", "Participación de los barrios con más severos"]),
    ("calidad", ["Cobertura de la llave", "Estrato válido", "Nombre validado"]),
    ("fuentes", ["Fecha de corte", "Construcciones", "Comunas", "Códigos de barrio"]),
])
def test_las_paginas_con_metricas_muestran_las_esperadas(renderizadas, pagina, fragmentos):
    etiquetas = [m.label for m in renderizadas[pagina].metric]
    for f in fragmentos:
        assert f in etiquetas


def test_la_respuesta_redacta_la_conclusion_con_la_regla(renderizadas):
    texto = pa.textos(renderizadas["respuesta"])
    assert "con este proxy y esta muestra no se detecta diferencia" in texto
    assert "una asociación no establece causalidad" in texto
    assert "El orden entre los grupos no es identificable".lower() in texto.lower()


def test_estratos_marca_la_muestra_baja_con_texto_y_no_ordena(renderizadas):
    at = renderizadas["estratos"]
    tabla = at.dataframe[0].value
    bajos = tabla[tabla["Estrato"].str.contains("muestra baja")]["Estrato"].tolist()
    assert bajos == ["Estrato 1 (muestra baja)", "Estrato 2 (muestra baja)", "Estrato 6 (muestra baja)"]
    assert "no se ordenan" in pa.textos(at)
    assert tabla["Estrato"].tolist()[0].startswith("Estrato 1")   # orden natural de los estratos, no un ranking


def test_sensibilidades_muestra_seis_escenarios_y_advierte_de_mantel_haenszel(renderizadas):
    at = renderizadas["sensibilidades"]
    assert at.dataframe[0].value["Escenario"].tolist() == ["S0", "S1", "S2", "S3", "S4", "S5"]
    avisos = [w.value for w in at.warning]
    assert len(avisos) == 6 and sum("no es interpretable" in a for a in avisos) == 5 and any("no está definida" in a for a in avisos)
    assert "incluye 0" in pa.textos(at)


def test_concentracion_lista_los_barrios_y_aclara_que_concentracion_no_es_riesgo(renderizadas):
    at = renderizadas["concentracion"]
    assert len(at.dataframe[0].value) == 10
    assert "concentración de casos no es mayor riesgo" in pa.textos(at)


def test_calidad_lista_los_codigos_con_su_clasificacion(renderizadas):
    tabla = renderizadas["calidad"].table[0].value
    assert len(tabla) == 7 and set(tabla["Clasificación"]) >= {"el código no coincide con el polígono (renumeración de códigos)"}
    assert "Qué NO demuestra" in pa.textos(renderizadas["calidad"])


def test_comunas_calcula_la_comuna_que_concentra_los_estratos_1_2(renderizadas):
    assert "Comuna 20" in pa.textos(renderizadas["comunas"]) and "comparar estratos es, en la práctica, comparar comunas" in pa.textos(renderizadas["comunas"])


def test_fuentes_lista_los_ocho_puntos_de_que_no_se_puede_concluir(renderizadas):
    texto = pa.textos(renderizadas["fuentes"])
    assert "Qué no se puede concluir" in texto
    puntos = [m.value for m in renderizadas["fuentes"].markdown if m.value.startswith("- ")]
    assert len(puntos) == 12   # 8 puntos de conclusión + 4 limitaciones del panel


def test_construcciones_pagina_filtra_en_la_api_y_ofrece_la_descarga(entorno):
    api = pa.como_consulta(entorno[1])
    at = pa.pagina("construcciones", api)
    assert len(at.exception) == 0 and "5.146 construcciones con estos filtros" in pa.textos(at)
    assert len(at.dataframe[0].value) == 50
    at.selectbox(key="filtro_comuna").select("20").run()
    filtrado = [c.value for c in at.caption if "construcciones con estos filtros" in c.value][0]
    assert not filtrado.startswith("5.146")
    at.selectbox(key="filtro_severo").select("Solo con cambio satelital severo").run()
    assert (at.dataframe[0].value["Cambio severo"] == "Sí").all()
    at.number_input(key="pagina").set_value(999).run()
    assert "No hay construcciones en esta página" in pa.textos(at)


# ---------- resiliencia (6.4) ----------
FALLOS = {
    "api_apagada": lambda req: (_ for _ in ()).throw(httpx.ConnectError("sin conexión", request=req)),
    "base_no_disponible": lambda req: httpx.Response(503, json={"error": {"codigo": "base_no_disponible", "mensaje": "x"}}),
    "no_encontrado": lambda req: httpx.Response(404, json={"error": {"codigo": "no_encontrado", "mensaje": "no existe el indicador K9"}}),
    "json_mal_formado": lambda req: httpx.Response(200, content=b"{roto"),
    "tiempo_agotado": lambda req: (_ for _ in ()).throw(httpx.ReadTimeout("lento", request=req)),
}


@pytest.mark.parametrize("pagina", PAGINAS)
@pytest.mark.parametrize("fallo", list(FALLOS))
def test_si_toda_la_api_falla_cada_pagina_muestra_un_aviso_claro_y_nunca_una_traza(pagina, fallo):
    at = pa.pagina(pagina, _todo_cae(FALLOS[fallo]))
    _sin_traza(at)
    assert len(at.warning) >= 1
    for frase in ALCANCE:
        assert frase in pa.textos(at)     # el alcance se mantiene visible aunque no haya datos


@pytest.mark.parametrize("pagina", PAGINAS)
def test_con_respuestas_vacias_cada_pagina_no_se_rompe(pagina):
    at = pa.pagina(pagina, _todo_cae(lambda req: httpx.Response(200, json=[])))
    _sin_traza(at)
    assert len(at.warning) + len(at.info) >= 1


@pytest.mark.parametrize("pagina", PAGINAS)
def test_con_objetos_vacios_cada_pagina_no_se_rompe(pagina):
    at = pa.pagina(pagina, _todo_cae(lambda req: httpx.Response(200, json={})))
    _sin_traza(at)


@pytest.mark.parametrize("pagina,ruta", [("respuesta", "/kpis"), ("estratos", "/kpis/K1"), ("comunas", "/comunas"), ("sensibilidades", "/kpis/sensibilidad"),
                                        ("concentracion", "/kpis"), ("calidad", "/calidad"), ("construcciones", "/construcciones"), ("fuentes", "/fuentes")])
@pytest.mark.parametrize("fallo", ["base_no_disponible", "no_encontrado", "json_mal_formado", "tiempo_agotado"])
def test_si_falla_solo_la_ruta_de_la_pagina_el_resto_sigue_visible(entorno, pagina, ruta, fallo):
    at = pa.pagina(pagina, _con_fallo(entorno, ruta, FALLOS[fallo]))
    _sin_traza(at)
    assert len(at.warning) >= 1
    assert at.title[0].value == registro.pagina(pagina).titulo
    assert any(c.value.startswith("API: en línea") for c in at.caption)


def test_un_kpi_inexistente_devuelve_404_y_la_pagina_lo_dice(entorno):
    at = pa.pagina("estratos", _con_fallo(entorno, "/kpis/K1", FALLOS["no_encontrado"]))
    assert "no tiene el recurso solicitado" in pa.textos(at) and "404" in pa.textos(at)


# ---------- la aplicación completa ----------
def test_la_aplicacion_arranca_con_la_navegacion_explicita_y_degrada_sin_api(monkeypatch):
    import socket

    import streamlit as st
    from streamlit.testing.v1 import AppTest

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        libre = s.getsockname()[1]
    monkeypatch.setenv("PANEL_API_URL", f"http://127.0.0.1:{libre}")
    st.cache_resource.clear()
    st.cache_data.clear()
    at = AppTest.from_file(str(pa.RAIZ / "src" / "panel" / "app.py"), default_timeout=60).run()
    assert len(at.exception) == 0
    assert at.title[0].value == "Respuesta" and "No se pudo conectar con la API" in pa.textos(at)
    for frase in ALCANCE:
        assert frase in pa.textos(at)
    st.cache_resource.clear()
    st.cache_data.clear()
