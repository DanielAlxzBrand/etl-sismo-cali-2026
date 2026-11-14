"""La matriz de casos de prueba se genera desde una definición única y cada caso apunta a una prueba que existe."""
import importlib.util

import pytest

from src.common import ROOT


def _cargar():
    spec = importlib.util.spec_from_file_location("make_matriz_casos_prueba", ROOT / "scripts" / "make_matriz_casos.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


mc = _cargar()


def test_cada_caso_apunta_a_una_prueba_existente_y_cada_funcion_tiene_correcto_e_incorrecto_o_limite():
    assert mc.verificar_definicion() == []


def test_los_documentos_generados_coinciden_con_la_definicion():
    assert mc.main(["--verificar"]) == 0


def test_los_identificadores_son_consecutivos_y_unicos():
    ids = [c[0] for c in mc.casos()]
    assert ids == [f"CP-{n:03d}" for n in range(1, len(ids) + 1)]


def test_los_modulos_citados_por_cada_funcion_existen():
    for fc, _, modulos, _ in mc.FUNCIONES:
        for ruta in [m.strip() for m in modulos.split(",")]:
            assert (ROOT / ruta).exists(), f"{fc}: no existe {ruta}"


def test_una_definicion_con_una_prueba_inexistente_se_detecta(monkeypatch):
    rota = [("FC-99", "Prueba", "src/", [("caso", mc.C, "ok", "test_extract.py::test_que_no_existe"), ("otro", mc.I, "falla", "test_extract.py::test_manifiesto_existe_y_no_vacio")])]
    monkeypatch.setattr(mc, "FUNCIONES", rota)
    errores = mc.verificar_definicion()
    assert any("no existe" in e for e in errores)


@pytest.mark.parametrize("tipos,esperado", [([("a", "correcto")], "sin caso incorrecto ni límite"), ([("a", "límite")], "sin caso correcto")])
def test_una_funcion_sin_variedad_de_casos_se_detecta(monkeypatch, tipos, esperado):
    lista = [(c, t, "ok", "test_extract.py::test_manifiesto_existe_y_no_vacio") for c, t in tipos]
    monkeypatch.setattr(mc, "FUNCIONES", [("FC-98", "Prueba", "src/", lista)])
    assert any(esperado in e for e in mc.verificar_definicion())
