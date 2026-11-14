"""Relación de contraste WCAG de la paleta del panel: cálculo y valores mínimos de cada par usado (texto y objetos gráficos)."""
import pytest

from src.panel import tema


def test_blanco_sobre_negro_es_21_a_1_y_un_color_consigo_mismo_es_1():
    assert tema.contraste("#000000", "#FFFFFF") == pytest.approx(21.0)
    assert tema.contraste("#336699", "#336699") == pytest.approx(1.0)


def test_el_contraste_es_simetrico():
    assert tema.contraste("#0072B2", "#FFFFFF") == pytest.approx(tema.contraste("#FFFFFF", "#0072B2"))


def test_valor_conocido_del_azul_principal_sobre_blanco():
    assert tema.contraste("#0072B2", "#FFFFFF") == pytest.approx(5.19, abs=0.01)


def test_la_luminancia_de_los_extremos():
    assert tema.luminancia("#000000") == 0 and tema.luminancia("#FFFFFF") == pytest.approx(1.0)


def test_el_texto_sobre_el_fondo_tiene_al_menos_7_a_1_y_sobre_el_fondo_secundario_tambien():
    c = tema.colores()
    assert tema.contraste(c["texto"], c["fondo"]) >= 7
    assert tema.contraste(c["texto"], c["fondo_secundario"]) >= 7


@pytest.mark.parametrize("color", ["principal", "secundario", "apoyo", "neutro"])
def test_los_colores_de_los_graficos_tienen_al_menos_3_a_1_sobre_el_fondo(color):
    c = tema.colores()
    assert tema.contraste(c[color], c["fondo"]) >= 3


def test_un_par_de_bajo_contraste_se_detecta():
    assert tema.contraste("#F0E442", "#FFFFFF") < 3      # amarillo de Okabe-Ito sobre blanco: no se usa por eso
