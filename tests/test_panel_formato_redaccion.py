"""Formato de cifras y regla de redacción del panel. Los valores de redacción son SINTÉTICOS (inventados para recorrer cada rama), no datos del proyecto."""
import re

import pytest

from src.panel import formato, redaccion

PROHIBIDAS = [r"el estrato no influye", r"prevalencia en Cali", r"\bcausa\b", r"\bcausó\b", r"\bprovoca\b"]


# ---------- formato ----------
@pytest.mark.parametrize("valor,decimales,esperado", [
    (1173, 0, "1.173"), (1234567.891, 1, "1.234.567,9"), (0, 0, "0"), (999, 0, "999"), (1000, 0, "1.000"), (0.125, 2, "0,13"),
    (-2.364, 2, "−2,36"), (-0.001, 2, "0,00"), (2.5, 0, "3"), (0.5, 0, "1"), (1.005, 2, "1,01"),
])
def test_numero_con_miles_coma_decimal_y_half_up(valor, decimales, esperado):
    assert formato.numero(valor, decimales) == esperado


@pytest.mark.parametrize("valor", [None, float("nan"), float("inf"), "no es un número", True])
def test_numero_sin_dato_devuelve_raya(valor):
    assert formato.numero(valor) == formato.SIN_DATO


def test_el_formateador_redondea_9984_45_hacia_arriba_y_no_hacia_abajo():
    # 99,8445 % exacto: el redondeo binario da 99,844; el formato de los documentos es 99,845
    assert formato.porcentaje(0.998445, 3) == "99,845 %"
    assert formato.porcentaje(0.998444, 3) == "99,844 %"


@pytest.mark.parametrize("fraccion,esperado", [(0.066225165563, "6,62 %"), (0, "0,00 %"), (1, "100,00 %"), (0.0583756345, "5,84 %"), (-0.0236, "−2,36 %")])
def test_porcentaje(fraccion, esperado):
    assert formato.porcentaje(fraccion) == esperado


def test_porcentaje_sin_dato():
    assert formato.porcentaje(None) == formato.SIN_DATO


@pytest.mark.parametrize("diferencia,esperado", [(0.004894, "+0,49 pp"), (-0.02364, "−2,36 pp"), (0, "0,00 pp"), (0.02553, "+2,55 pp")])
def test_puntos_porcentuales_con_signo(diferencia, esperado):
    assert formato.puntos_porcentuales(diferencia) == esperado


def test_intervalos_en_porcentaje_y_en_puntos_porcentuales():
    assert formato.intervalo(0.0392, 0.0861) == "[3,92 %; 8,61 %]"
    assert formato.intervalo(-0.0236, 0.02553, como="pp") == "[−2,36; +2,55] pp"
    assert formato.intervalo(None, 0.1) == formato.SIN_DATO
    assert formato.intervalo(0.1, None, como="pp") == formato.SIN_DATO


def test_razon_con_tres_decimales():
    assert formato.razon(1.083851) == "1,084"
    assert formato.razon(None) == formato.SIN_DATO


# ---------- redacción ----------
def test_intervalo_que_incluye_cero_usa_la_frase_de_no_deteccion():
    t = redaccion.conclusion_diferencia(0.0049, -0.0236, 0.0255)
    assert redaccion.FRASE_SIN_DIFERENCIA in t and "incluye 0" in t


def test_intervalo_que_no_incluye_cero_describe_la_muestra_sin_causalidad():
    t = redaccion.conclusion_diferencia(0.03, 0.01, 0.05)
    assert "no incluye 0" in t and "mayor" in t and redaccion.AVISO_NO_CAUSAL in t
    assert redaccion.FRASE_SIN_DIFERENCIA not in t


def test_diferencia_negativa_dice_menor():
    assert "menor" in redaccion.conclusion_diferencia(-0.03, -0.05, -0.01)


def test_intervalos_que_se_solapan_sin_cero_en_la_diferencia_usan_la_frase():
    t = redaccion.conclusion_diferencia(0.03, 0.01, 0.05, solapan_intervalos=True)
    assert "se solapan" in t and redaccion.FRASE_SIN_DIFERENCIA in t


def test_muestra_baja_agrega_la_advertencia():
    assert redaccion.AVISO_MUESTRA_BAJA in redaccion.conclusion_diferencia(0.0, -0.01, 0.01, muestra_baja=True)


def test_sin_intervalo_no_se_redacta_una_conclusion():
    assert "no se redacta" in redaccion.conclusion_diferencia(None, None, None)


def test_incluye_cero_y_solapamiento_en_los_bordes():
    assert redaccion.incluye_cero(0, 1) and redaccion.incluye_cero(-1, 0) and not redaccion.incluye_cero(0.1, 1)
    assert redaccion.se_solapan(0, 1, 1, 2) is True and redaccion.se_solapan(0, 1, 1.01, 2) is False
    assert redaccion.se_solapan(0, None, 1, 2) is None and redaccion.incluye_cero(None, 1) is False


def test_cotas_que_se_solapan_dicen_que_el_orden_no_es_identificable():
    sinteticas = [{"cota_inf": 0.05, "cota_sup": 0.14}, {"cota_inf": 0.04, "cota_sup": 0.20}]
    assert "no es identificable" in redaccion.conclusion_cotas(sinteticas)
    assert "no se solapan" in redaccion.conclusion_cotas([{"cota_inf": 0.0, "cota_sup": 0.1}, {"cota_inf": 0.2, "cota_sup": 0.3}])
    assert redaccion.conclusion_cotas([{"cota_inf": None, "cota_sup": 0.1}, {"cota_inf": 0.2, "cota_sup": 0.3}]) == ""


def test_estratos_con_muestra_baja_no_se_ordenan_y_se_informa_el_solapamiento():
    filas = [  # sintéticas
        {"grupo": "estrato_1", "muestra_baja": True, "ic95_inf": 0.01, "ic95_sup": 0.20},
        {"grupo": "estrato_3", "muestra_baja": False, "ic95_inf": 0.05, "ic95_sup": 0.08},
        {"grupo": "estrato_4", "muestra_baja": False, "ic95_inf": 0.06, "ic95_sup": 0.09},
        {"grupo": "estrato_5", "muestra_baja": False, "ic95_inf": 0.10, "ic95_sup": 0.12},
    ]
    t = redaccion.conclusion_estratos(filas)
    assert "E1" in t and "no se ordenan" in t
    assert "E3 y E4" in t and redaccion.FRASE_SIN_DIFERENCIA in t
    assert "no se solapan entre E3 y E5" in t


def test_la_comuna_que_concentra_un_grupo_se_calcula_de_la_composicion():
    comp = [{"comuna": "20", "grupo_estrato": "1-2", "n_con_datos": 90, "severos": 5}, {"comuna": "18", "grupo_estrato": "1-2", "n_con_datos": 10, "severos": 1},
            {"comuna": "03", "grupo_estrato": "3-5", "n_con_datos": 500, "severos": 20}]   # sintética
    t = redaccion.comuna_que_concentra(comp, "1-2")
    assert "Comuna 20" in t and "90" in t and "90,0 %" in t and "Comuna 18" in t
    assert "No hay construcciones" in redaccion.comuna_que_concentra([], "1-2")


def test_comunas_con_muestra_baja_no_se_ordenan():
    t = redaccion.conclusion_comunas([{"comuna": "09", "muestra_baja": True}, {"comuna": "19", "muestra_baja": False}])
    assert "09" in t and "no se ordenan" in t and "ordenamiento" in t


def test_escenario_y_resumen_de_sensibilidades():
    con_cero = {"escenario": "S1", "tasa": 0.0017, "ic95_inf": -0.028, "ic95_sup": 0.023}
    sin_cero = {"escenario": "S9", "tasa": 0.04, "ic95_inf": 0.01, "ic95_sup": 0.07}   # sintético
    assert redaccion.FRASE_SIN_DIFERENCIA in redaccion.conclusion_escenario("S1", con_cero)
    assert "no incluye 0" in redaccion.conclusion_escenario("S9", sin_cero)
    assert "En los 1 escenarios" in redaccion.conclusion_sensibilidades([con_cero])
    mixto = redaccion.conclusion_sensibilidades([con_cero, sin_cero])
    assert "1 de 2" in mixto and "S9" in mixto
    assert "sin intervalo" in redaccion.conclusion_escenario("S2", {"ic95_inf": None})
    assert "No hay intervalos" in redaccion.conclusion_sensibilidades([])


def test_mantel_haenszel_advierte_cuando_descansa_en_una_comuna():
    assert "no es interpretable" in redaccion.aviso_mantel_haenszel({"tasa": 1.97}, 1)
    assert "con cautela" in redaccion.aviso_mantel_haenszel({"tasa": 1.5}, 3)
    assert "no está definida" in redaccion.aviso_mantel_haenszel({"tasa": None}, 0)
    assert "no está definida" in redaccion.aviso_mantel_haenszel(None, None)


def test_concentracion_aclara_que_no_es_mayor_riesgo():
    t = redaccion.conclusion_concentracion({"valor": 0.5, "numerador": 50, "denominador": 100}, {"valor": 0.03, "denominador": 45})
    assert "no es mayor riesgo" in t and "falacia ecológica" in t
    assert "No hay datos" in redaccion.conclusion_concentracion(None, None)


@pytest.mark.parametrize("diferencia,inf,sup,solapan,baja", [(0.0, -0.1, 0.1, False, False), (0.1, 0.05, 0.2, False, True), (-0.1, -0.2, -0.05, True, True), (0.1, 0.0, 0.2, True, False)])
def test_ninguna_rama_afirma_causalidad_ni_que_el_estrato_no_influye(diferencia, inf, sup, solapan, baja):
    texto = redaccion.conclusion_diferencia(diferencia, inf, sup, solapan, baja) + redaccion.conclusion_estratos([]) + redaccion.conclusion_comunas([])
    for patron in PROHIBIDAS:
        assert re.search(patron, texto, re.I) is None, patron
