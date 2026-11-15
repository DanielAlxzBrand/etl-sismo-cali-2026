"""Ajustes del panel que salieron de la evaluación heurística interna (F-01 a F-13, D87 a D90): cada prueba falla si el defecto vuelve.

Son una iteración técnica, no una validación con personas usuarias. Los gráficos se comprueban leyendo la especificación que se le entrega a Streamlit (no se dibujan aquí); lo que se ve en
pantalla lo comprueban las capturas de EV-077 a EV-079. Los datos de las pruebas de gráficos son SINTÉTICOS (inventados), no datos del proyecto.
"""
import ast
import importlib.util
import re
import shutil
from unittest import mock

import pandas as pd
import pytest
import streamlit as st

from src.common import ROOT
from src.panel import componentes, glosario, registro, tema
from src.panel.paginas import calidad, comunas, concentracion, construcciones, estratos, fuentes, respuesta, sensibilidades
from tests import panel_apoyo as pa
from tests.test_panel_textos import prohibidas_en

PAGINAS = [p.id for p in registro.PAGINAS]
MODULOS = {m.ID: m for m in (respuesta, estratos, comunas, sensibilidades, concentracion, calidad, construcciones, fuentes)}


@pytest.fixture(scope="module")
def api():
    carpeta, ruta = pa.copia_temporal_de_la_base()
    http, cliente = pa.api_en_memoria(ruta)
    yield pa.como_consulta(cliente)
    cliente.cerrar()
    http.close()
    shutil.rmtree(carpeta, ignore_errors=True)


@pytest.fixture(scope="module")
def paginas(api):
    return {p: pa.pagina(p, api) for p in PAGINAS}


def _graficos_de(pagina, api):
    """Especificaciones (diccionarios) de los gráficos que la página entrega a `st.altair_chart`."""
    capturados = []
    with mock.patch.object(st, "altair_chart", side_effect=lambda chart, **kw: capturados.append(chart.to_dict())):
        pa.pagina(pagina, api)
    return capturados


# ---------------------------------------------------------------- F-02 · barra lateral
def _argumentos_de_set_page_config():
    arbol = ast.parse((ROOT / "src" / "panel" / "app.py").read_text(encoding="utf-8"))
    for n in ast.walk(arbol):
        if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "set_page_config":
            return {k.arg: k.value.value for k in n.keywords if isinstance(k.value, ast.Constant)}
    raise AssertionError("app.py no llama a set_page_config")


def test_la_barra_lateral_no_se_abre_sola_en_pantallas_estrechas():
    """«expanded» la dejaba abierta a 390 px y cubría casi todo el contenido (F-02); «auto» la cierra en pantallas estrechas y la deja abierta en las anchas."""
    assert _argumentos_de_set_page_config()["initial_sidebar_state"] == "auto"


# ---------------------------------------------------------------- F-01 · tarjetas
@pytest.mark.parametrize("pagina", PAGINAS)
def test_ninguna_etiqueta_de_tarjeta_pasa_del_largo_que_cabe(paginas, pagina):
    largas = [m.label for m in paginas[pagina].metric if len(m.label) > componentes.LARGO_MAXIMO_ETIQUETA]
    assert largas == [], f"Streamlit las recortaría con puntos suspensivos: {largas}"


def _columnas_pedidas(pagina, api):
    llamadas = []
    original = st.columns

    def registrar(spec, *a, **k):
        llamadas.append(spec if isinstance(spec, int) else len(spec))
        return original(spec, *a, **k)

    with mock.patch.object(st, "columns", side_effect=registrar):
        pa.pagina(pagina, api)
    return llamadas


@pytest.mark.parametrize("pagina,esperadas", [("respuesta", [2, 2, 3]), ("fuentes", [2, 2]), ("concentracion", [2, 3])])
def test_las_tarjetas_de_cifras_largas_van_de_dos_en_dos(api, pagina, esperadas):
    """Con cuatro por fila, a 1024 px la caja de la cifra medía unos 97 píxeles y «6,33 %» y «2026-09-02» salían recortadas (F-01)."""
    assert _columnas_pedidas(pagina, api) == esperadas


def test_ninguna_pagina_pide_mas_de_tres_columnas_de_tarjetas(api):
    assert max(max(_columnas_pedidas(p, api) or [0]) for p in PAGINAS) <= 3


def test_tarjetas_reparte_en_filas_del_tamano_pedido():
    pedidas = []
    with mock.patch.object(st, "columns", side_effect=lambda n, *a, **k: pedidas.append(n) or [mock.MagicMock() for _ in range(n)]), mock.patch.object(st, "metric") as metrica:
        componentes.tarjetas([("a", "1", None)] * 5, por_fila=2)
    assert pedidas == [2, 2, 2] and metrica.call_count == 5


# ---------------------------------------------------------------- F-03 · aviso de tabla ancha
COLUMNAS_DE_UNA_TABLA_ANCHA = 4      # fijo a propósito: a 390 px se cortaron las tablas de cuatro columnas o más; si el umbral del código sube, esta prueba falla


def test_el_umbral_de_tabla_ancha_no_sube_de_cuatro_columnas():
    assert componentes.UMBRAL_COLUMNAS_ANCHAS <= COLUMNAS_DE_UNA_TABLA_ANCHA
@pytest.mark.parametrize("pagina", PAGINAS)
def test_cada_tabla_ancha_lleva_su_aviso_de_desplazamiento(paginas, pagina):
    at = paginas[pagina]
    anchas = sum(1 for t in list(at.dataframe) + list(at.table) if t.value.shape[1] >= COLUMNAS_DE_UNA_TABLA_ANCHA)
    avisos = sum(1 for c in at.caption if c.value == componentes.AVISO_TABLA_ANCHA)
    assert avisos == anchas


def test_el_aviso_aparece_solo_con_el_umbral_de_columnas():
    with mock.patch.object(st, "caption") as pie, mock.patch.object(st, "dataframe"):
        componentes.tabla(pd.DataFrame([[1] * componentes.UMBRAL_COLUMNAS_ANCHAS]))
        angostas = pie.call_count
        componentes.tabla(pd.DataFrame([[1] * (componentes.UMBRAL_COLUMNAS_ANCHAS - 1)]))
    assert angostas == 1 and pie.call_count == 1


# ---------------------------------------------------------------- F-04 y F-05 · gráficos de barras
GRUPOS_SINTETICOS = pd.DataFrame({"grupo": [f"Grupo {i}" + (" · muestra baja" if i % 2 else "") for i in range(7)], "tasa_pct": [5.0] * 7, "inf_pct": [3.0] * 7, "sup_pct": [8.0] * 7,
                                  "muestra": ["muestra suficiente", "muestra baja"] * 3 + ["muestra suficiente"], "tasa_txt": ["5,0 %"] * 7, "ic_txt": ["[3,0 %; 8,0 %]"] * 7})


def _especificacion_de_tasas(df=GRUPOS_SINTETICOS):
    capturado, pies = [], []
    with mock.patch.object(st, "altair_chart", side_effect=lambda chart, **kw: capturado.append(chart.to_dict())), mock.patch.object(st, "caption", side_effect=pies.append):
        componentes.grafico_tasas(df, "grupo", "Titulo", "Descripcion", titulo_x="Grupo")
    return capturado[0], pies


def test_las_barras_de_tasa_son_horizontales_y_cada_etiqueta_tiene_su_fila():
    espec, _ = _especificacion_de_tasas()
    barras, error = espec["layer"]
    assert barras["mark"]["type"] == "bar" and barras["encoding"]["y"]["type"] == "nominal" and barras["encoding"]["x"]["type"] == "quantitative"
    assert "x2" in error["encoding"] and error["encoding"]["y"]["field"] == "grupo"
    assert barras["encoding"]["y"]["axis"]["labelLimit"] == 0 and barras["encoding"]["y"]["axis"]["labelOverlap"] is False
    assert espec["height"] == {"step": componentes.ALTO_POR_BARRA}      # un alto fijo achicaba el área y Vega borraba las etiquetas de en medio


def test_la_muestra_baja_sigue_marcada_por_texto_y_por_color():
    espec, _ = _especificacion_de_tasas()
    color = espec["layer"][0]["encoding"]["color"]
    assert color["scale"]["domain"] == [componentes.ETIQUETA_SUFICIENTE, componentes.ETIQUETA_BAJA] and len(set(color["scale"]["range"])) == 2
    assert color["legend"]["orient"] == "bottom"
    assert any("muestra baja" in g for g in GRUPOS_SINTETICOS["grupo"])


def test_el_pie_de_los_graficos_de_barras_explica_la_linea_y_las_rayas():
    _, pies = _especificacion_de_tasas()
    assert pies and "límite inferior" in pies[0] and "superior" in pies[0] and "rayas" in pies[0] and "Wilson" in pies[0]


def test_el_grafico_de_diferencias_explica_el_punto_la_linea_y_la_linea_discontinua():
    df = pd.DataFrame({"escenario": ["S0", "S1"], "dif_pp": [0.5, 0.2], "inf_pp": [-2.0, -2.5], "sup_pp": [2.5, 2.0], "dif_txt": ["+0,5 pp", "+0,2 pp"], "ic_txt": ["x", "y"]})
    pies = []
    with mock.patch.object(st, "altair_chart"), mock.patch.object(st, "caption", side_effect=pies.append):
        componentes.grafico_diferencias(df, "escenario", "T", "D")
    assert "Cada punto" in pies[0] and "límite inferior" in pies[0] and "discontinua" in pies[0] and "Newcombe" in pies[0]


@pytest.mark.parametrize("pagina", ["estratos", "comunas"])
def test_las_paginas_de_barras_entregan_el_grafico_horizontal(api, pagina):
    espec = _graficos_de(pagina, api)[0]
    assert espec["layer"][0]["encoding"]["y"]["type"] == "nominal"


# ---------------------------------------------------------------- F-13 · coordenadas
def test_la_latitud_y_la_longitud_llevan_cuatro_decimales_con_coma_y_se_rotulan_grados_decimales(api):
    espec = _graficos_de("construcciones", api)[0]
    for eje in ("x", "y"):
        e = espec["encoding"][eje]["axis"]
        assert ".4f" in e["labelExpr"] and ".3f" not in e["labelExpr"] and "replace(" in e["labelExpr"]
        assert "grados decimales" in e["title"]
    assert componentes.EXPRESION_GRADOS.count(".4f") == 1


def test_la_leyenda_de_la_ubicacion_va_abajo_en_dos_columnas_para_no_cortarse(api):
    leyenda = _graficos_de("construcciones", api)[0]["encoding"]["color"]["legend"]
    assert leyenda["orient"] == "bottom" and leyenda["columns"] == 2


def test_el_titulo_del_grafico_de_ubicacion_cabe_en_una_pantalla_estrecha(api):
    titulo = _graficos_de("construcciones", api)[0]["title"]["text"]
    assert len(titulo) <= 60


# ---------------------------------------------------------------- F-12 · contraste
def _mezcla(texto, fondo, alfa):
    a, b = (tuple(int(c.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)) for c in (texto, fondo))
    return "#%02x%02x%02x" % tuple(round(alfa * x + (1 - alfa) * y) for x, y in zip(a, b))


def _script_de_contraste():
    espec = importlib.util.spec_from_file_location("contraste_script", ROOT / "scripts" / "panel" / "contraste.py")
    modulo = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(modulo)
    return modulo


def test_los_textos_de_la_paleta_alcanzan_cuatro_y_medio_a_uno_segun_el_script_de_contraste():
    lista, c = _script_de_contraste().pares()
    for nombre, x, y, tipo in lista:
        if tipo == "texto":
            assert tema.contraste(c[x], c[y]) >= 4.5, nombre


def test_los_elementos_graficos_de_la_paleta_alcanzan_tres_a_uno_segun_el_script_de_contraste():
    lista, c = _script_de_contraste().pares()
    for nombre, x, y, tipo in lista:
        if tipo == "gráfico" and "frente al secundario" not in nombre:      # el par «dos categorías vecinas» se distingue además por texto y por forma (D74)
            assert tema.contraste(c[x], c[y]) >= 3, nombre


def test_los_pies_que_streamlit_dibuja_al_sesenta_por_ciento_del_texto_alcanzan_cuatro_y_medio_a_uno():
    """Streamlit pinta pies y subtítulos con el 60 % del color del texto; con el texto anterior daba 4,05 a 1 (F-12)."""
    c = tema.colores()
    for fondo in ("fondo", "fondo_secundario"):
        assert tema.contraste(_mezcla(c["texto"], c[fondo], 0.6), c[fondo]) >= 4.5, fondo


def test_el_texto_de_los_graficos_usa_un_color_de_al_menos_cuatro_y_medio_a_uno(api):
    c = tema.colores()
    assert tema.contraste(c["texto_secundario"], c["fondo"]) >= 4.5
    for pagina in ("estratos", "comunas", "sensibilidades", "construcciones"):
        for espec in _graficos_de(pagina, api):
            assert espec["config"]["axis"]["labelColor"] == c["texto_secundario"] and espec["config"]["axis"]["titleColor"] == c["texto_secundario"]
            assert espec["config"]["legend"]["labelColor"] == c["texto_secundario"]


def test_la_paleta_sigue_siendo_la_apta_para_daltonismo():
    c = tema.colores()
    assert (c["principal"], c["secundario"], c["apoyo"], c["neutro"]) == ("#0072B2", "#D55E00", "#009E73", "#595959")


# ---------------------------------------------------------------- F-07 · glosario
def _texto_sin_glosario(at):
    glos = {m.value for e in at.expander for m in e.markdown}
    partes = [m.value for m in at.markdown if m.value not in glos] + [e.value for g in (at.caption, at.subheader, at.title, at.warning, at.info) for e in g]
    for m in at.metric:
        partes += [m.label, m.value, m.help or ""]
    for t in list(at.dataframe) + list(at.table):
        partes += [str(c) for c in t.value.columns]
    return "\n".join(partes).lower()


def test_el_glosario_tiene_entrada_para_cada_termino_declarado_y_cada_pagina_del_panel():
    assert set(glosario.TERMINOS_POR_PAGINA) == set(PAGINAS)
    declarados = {k for ks in glosario.TERMINOS_POR_PAGINA.values() for k in ks}
    assert declarados <= set(glosario.TERMINOS) and set(glosario.TECNICOS.values()) <= set(glosario.TERMINOS)
    assert all(nombre.strip() and definicion.strip() for nombre, definicion in glosario.TERMINOS.values())


@pytest.mark.parametrize("pagina", PAGINAS)
def test_cada_pagina_muestra_su_glosario_completo_y_cerrado(paginas, pagina):
    at = paginas[pagina]
    desplegables = [e for e in at.expander if e.label.startswith("Glosario")]
    assert len(desplegables) == 1
    mostrados = [m.value for m in desplegables[0].markdown]
    esperados = [f"- **{n}.** {d}" for n, d in glosario.entradas(pagina)]
    assert mostrados == esperados and esperados


@pytest.mark.parametrize("pagina", PAGINAS)
def test_todo_termino_tecnico_que_usa_la_pagina_esta_en_su_glosario(paginas, pagina):
    texto = _texto_sin_glosario(paginas[pagina])
    faltan = [forma for forma, clave in glosario.TECNICOS.items() if forma in texto and clave not in glosario.TERMINOS_POR_PAGINA[pagina]]
    assert faltan == [], f"{pagina}: usa términos técnicos sin entrada en su glosario: {faltan}"


def test_el_glosario_no_afirma_causalidad_ni_lleva_cifras_propias():
    for nombre, definicion in glosario.TERMINOS.values():
        assert prohibidas_en(nombre + " " + definicion) == [], nombre
        resto = re.sub(r"95 %|\b0\b|\b[1-6]-[1-6]\b|\bS[0-5]\b|\bK[1-6]\b", "", definicion)
        assert not re.search(r"\d", resto), (nombre, definicion)


def test_negativa_una_pagina_sin_glosario_o_sin_un_termino_se_detecta(api):
    with mock.patch.object(glosario, "desplegable"):
        sin = pa.pagina("estratos", api)
    assert not [e for e in sin.expander if e.label.startswith("Glosario")]
    recortado = dict(glosario.TERMINOS_POR_PAGINA, estratos=tuple(k for k in glosario.TERMINOS_POR_PAGINA["estratos"] if k != "intervalo de Wilson"))
    with mock.patch.object(glosario, "TERMINOS_POR_PAGINA", recortado):
        at = pa.pagina("estratos", api)
    assert "intervalo de wilson" not in "".join(m.value.lower() for e in at.expander for m in e.markdown)
    assert "wilson" in _texto_sin_glosario(at)
