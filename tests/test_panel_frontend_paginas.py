"""Respuesta, Comunas y Sensibilidades con la interfaz propia (D115): cada página muestra lo mismo que el panel original (mismas celdas, mismas cifras, mismos textos de `redaccion`),
conserva sus funciones (tablas, avisos, notas) y exporta un documento autónomo; los textos que vienen de los datos se escapan.

Qué NO demuestran: cómo se ven en un navegador ni que el JavaScript funcione (lo registran las capturas y el recorrido interactivo). Los datos hostiles de las pruebas de seguridad son SINTÉTICOS.
"""
import re
from html import escape, unescape

import pytest

from src.panel import formato, glosario, redaccion, registro
from src.panel.frontend import comunas as vista_comunas
from src.panel.frontend import respuesta as vista_respuesta
from src.panel.frontend import sensibilidades as vista_sens
from src.panel.frontend import vista as base
from src.panel.paginas import comunas as pagina_comunas
from src.panel.paginas import respuesta as pagina_respuesta
from src.panel.paginas import sensibilidades as pagina_sens
from tests import panel_apoyo as pa
from tests.test_panel_frontend import HOSTIL, entorno, hallazgos_plantilla, metadata  # noqa: F401  (fixtures y ayudas compartidas)

ESCENARIOS = ["S0", "S1", "S2", "S3", "S4", "S5"]
DIFERENCIA = "diferencia_3-5_menos_1-2"


def _normal(texto):
    return re.sub(r"\s+", " ", texto)


@pytest.fixture(scope="module")
def paginas3(entorno):
    return {p: pa.pagina(p, entorno) for p in ("respuesta", "comunas", "sensibilidades")}


@pytest.fixture(scope="module")
def kpis(entorno):
    return entorno("/kpis").datos


@pytest.fixture(scope="module")
def k6(entorno):
    return entorno("/comunas").datos


@pytest.fixture(scope="module")
def composicion(entorno):
    return entorno("/composicion").datos


@pytest.fixture(scope="module")
def sensibilidad(entorno):
    return entorno("/kpis/sensibilidad").datos


def _k2(kpis, grupo):
    return next(f for f in kpis if f["kpi_id"] == "K2" and f["grupo"] == grupo)


# ---------------------------------------------------------------- las tres páginas
@pytest.mark.parametrize("pagina_id,etiqueta", [("respuesta", "Exportar informe"), ("comunas", "Exportar figura"), ("sensibilidades", "Exportar informe")])
def test_cada_pagina_se_dibuja_con_cabecera_propia_glosario_y_exportacion(paginas3, pagina_id, etiqueta):
    at = paginas3[pagina_id]
    assert len(at.exception) == 0 and pa.titulo(at) == registro.pagina(pagina_id).titulo
    texto = pa.texto_html(at)
    assert registro.pagina(pagina_id).pregunta in texto and "Corte de datos: 2026-09-02" in texto
    assert [b.proto.label for b in at.get("download_button")] == [etiqueta]
    pares, cerrado = pa.glosario_html(at)
    assert cerrado and pares == [tuple(x) for x in glosario.entradas(pagina_id)]


# ---------------------------------------------------------------- Respuesta
def test_respuesta_muestra_las_cifras_la_lectura_y_el_aviso_de_cotas_del_panel_original(paginas3, kpis):
    at = paginas3["respuesta"]
    t35, t12, dif, razon = _k2(kpis, "estratos_3-5"), _k2(kpis, "estratos_1-2"), _k2(kpis, DIFERENCIA), _k2(kpis, "razon_3-5_vs_1-2")
    tasas, comparacion = pagina_respuesta.tarjetas_k2(t35, t12, dif, razon)
    mostradas = [(f.label, f.value, f.help) for f in pa.fichas_html(at)]
    assert mostradas[:2] == comparacion and mostradas[2:4] == tasas and len(mostradas) == 7
    texto = _normal(pa.texto_html(at))
    solapan = redaccion.se_solapan(t35["ic95_inf"], t35["ic95_sup"], t12["ic95_inf"], t12["ic95_sup"])
    assert _normal(redaccion.conclusion_diferencia(dif["valor"], dif["ic95_inf"], dif["ic95_sup"], solapan, bool(t12["muestra_baja"]))) in texto
    assert _normal(redaccion.conclusion_cotas([t35, t12])) in texto
    assert f"Intervalo de la diferencia (Newcombe): {formato.intervalo(dif['ic95_inf'], dif['ic95_sup'], como='pp')}" in texto and "Calidad de la unión (K5)" in texto


def test_la_guia_de_respuesta_traduce_los_conteos_con_los_datos_reales(kpis):
    t35, t12 = _k2(kpis, "estratos_3-5"), _k2(kpis, "estratos_1-2")
    pasos = base.guia("respuesta", vista_respuesta.ejemplo(t35, t12))
    assert len(pasos) == 6 and formato.numero(t35["denominador"]) in pasos[3]["texto"] and formato.numero(t12["numerador"]) in pasos[3]["texto"]


# ---------------------------------------------------------------- Comunas
def test_comunas_dibuja_la_tabla_y_la_composicion_del_panel_original(paginas3, k6, composicion):
    at = paginas3["comunas"]
    tablas = pa.tablas_html(at)
    detalle = pagina_comunas.tabla_k6(k6)
    assert tablas[0] == [list(detalle.columns)] + [[str(v) for v in f] for f in detalle.to_numpy().tolist()]
    comp = pagina_comunas._tabla_composicion(composicion)
    assert tablas[1] == [list(comp.columns)] + [[str(v) for v in f] for f in comp.to_numpy().tolist()]
    texto = _normal(pa.texto_html(at))
    assert _normal(redaccion.conclusion_comunas(k6)) in texto and _normal(redaccion.comuna_que_concentra(composicion, "1-2")) in texto
    assert vista_comunas.INTRO_COMPOSICION in texto


def test_la_figura_de_comunas_muestra_tasa_intervalo_y_conteos_y_la_muestra_baja_viene_de_la_api(paginas3, k6):
    html = next(h.value for h in paginas3["comunas"].html if 'class="analisis"' in h.value)
    filas = re.findall(r'<label class="dato r(\d+)( baja)?">(.*?)</label>', html, re.S)
    assert len(filas) == len(k6) == 7
    for (_, clase, interior), f in zip(filas, k6):
        texto = _normal(unescape(re.sub(r"<[^>]+>", " ", re.sub(r'<span class="ayuda".*?</span>', "", interior, flags=re.S))))
        assert formato.porcentaje(f["tasa"]) in texto and formato.intervalo(f["ic95_inf"], f["ic95_sup"]) in texto
        assert f"{formato.numero(f['severos'])} de {formato.numero(f['n_con_datos'])}" in texto and f["comuna"] in texto
        assert bool(clase) == bool(f["muestra_baja"]) and ("Muestra baja" in texto) == bool(f["muestra_baja"])
    assert any(f["muestra_baja"] for f in k6) and any(not f["muestra_baja"] for f in k6)


def test_la_normalizacion_de_k6_no_cambia_ningun_valor(k6):
    for f in k6:
        n = vista_comunas.normalizar(f)
        assert (n["valor"], n["numerador"], n["denominador"]) == (f["tasa"], f["severos"], f["n_con_datos"]) and all(n[k] == v for k, v in f.items())


# ---------------------------------------------------------------- Sensibilidades
def test_sensibilidades_conserva_grafico_tabla_avisos_y_notas_del_panel_original(paginas3, sensibilidad):
    at = paginas3["sensibilidades"]
    assert [e for e in ESCENARIOS if pagina_sens._fila(sensibilidad, e, DIFERENCIA)] == ESCENARIOS
    tabla = pagina_sens.tabla_escenarios(sensibilidad, ESCENARIOS)
    assert at.dataframe[0].value.equals(tabla) and "Razón ajustada (MH)" in tabla.columns
    assert [w.value for w in at.warning] == pagina_sens.avisos_mh(sensibilidad, ESCENARIOS)
    notas = [m.value for e in at.expander for m in e.markdown]
    assert len(notas) == 6 and all(n.startswith(f"**{e}.** ") for n, e in zip(notas, ESCENARIOS))
    assert _normal(redaccion.conclusion_sensibilidades([{"escenario": e, **pagina_sens._fila(sensibilidad, e, DIFERENCIA)} for e in ESCENARIOS])) in _normal(pa.textos(at))


def test_el_informe_de_sensibilidades_trae_cada_escenario_con_su_aviso_de_mantel_haenszel(sensibilidad):
    difs = [pagina_sens._fila(sensibilidad, e, DIFERENCIA) for e in ESCENARIOS]
    tabla = pagina_sens.tabla_escenarios(sensibilidad, ESCENARIOS)
    avisos, notas = pagina_sens.avisos_mh(sensibilidad, ESCENARIOS), pagina_sens.notas_mh(sensibilidad, ESCENARIOS)
    documento = vista_sens.documento(registro.pagina("sensibilidades"), "Resultados", "2026-09-02", {}, ESCENARIOS, difs, tabla, "lectura", avisos, notas).decode("utf-8")
    assert hallazgos_plantilla(documento) == [] and "Content-Security-Policy" in documento
    assert all(formato.puntos_porcentuales(d["tasa"]) in documento for d in difs) and all(escape(a) in documento for a in avisos)
    analizador = pa._Tablas()
    analizador.feed(documento)
    assert analizador.tablas[0][1:] == [[str(v) for v in f] for f in tabla.to_numpy().tolist()]


@pytest.mark.parametrize("minimo,maximo", [(-4.88, 6.37), (-0.5, 0.4), (0.3, 2.0), (-30, 25)])
def test_la_escala_con_signo_incluye_el_cero_y_cubre_los_limites(minimo, maximo):
    inferior, superior, marcas = base.escala_con_signo(minimo, maximo)
    assert inferior <= min(minimo, 0) and superior >= max(maximo, 0) and inferior <= 0 <= superior
    assert marcas[0] == inferior and marcas[-1] == superior and len(marcas) <= 7


# ---------------------------------------------------------------- seguridad
def test_un_texto_hostil_se_escapa_en_los_informes_y_en_el_cuerpo_de_respuesta_y_comunas(k6, composicion, metadata):
    tarjetas = [(HOSTIL, HOSTIL, HOSTIL)]
    html = vista_respuesta.cuerpo(tarjetas, HOSTIL, HOSTIL, HOSTIL, tarjetas, tarjetas)
    documento = vista_respuesta.documento(registro.pagina("respuesta"), "Resultados", HOSTIL, metadata, html, HOSTIL).decode("utf-8")
    filas = [dict(f, comuna=HOSTIL) for f in k6]
    tabla, comp = pagina_comunas.tabla_k6(filas), pagina_comunas._tabla_composicion(composicion)
    cuerpo = vista_comunas.cuerpo(filas, [HOSTIL] * len(filas), tabla, HOSTIL, comp, HOSTIL)
    informe = vista_comunas.lamina(registro.pagina("comunas"), "Resultados", HOSTIL, metadata, filas, [HOSTIL] * len(filas), tabla, HOSTIL, comp, HOSTIL).decode("utf-8")
    for salida in (html, documento, cuerpo, informe):
        assert "<img" not in salida and "<script" not in salida and "onerror=alert" not in re.sub(r"&lt;img[^&]*&gt;", "", salida)


def test_un_aviso_o_una_nota_hostil_se_escapa_en_el_informe_de_sensibilidades(sensibilidad, metadata):
    difs = [pagina_sens._fila(sensibilidad, e, DIFERENCIA) for e in ESCENARIOS]
    tabla = pagina_sens.tabla_escenarios(sensibilidad, ESCENARIOS)
    documento = vista_sens.documento(registro.pagina("sensibilidades"), "Resultados", HOSTIL, metadata, ESCENARIOS, difs, tabla, HOSTIL, [HOSTIL], [HOSTIL]).decode("utf-8")
    assert "<img" not in documento and "<script" not in documento and escape(HOSTIL) in documento
