"""Informe de pruebas: lectura de JUnit, resultado por caso y métricas del análisis, con datos sintéticos (no se vuelve a ejecutar pytest dentro de pytest)."""
import importlib.util

from src.common import ROOT


def _cargar():
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("informe_pruebas_prueba", ROOT / "scripts" / "informe_pruebas.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


ip = _cargar()
XML = """<?xml version="1.0" encoding="utf-8"?><testsuites><testsuite name="pytest">
<testcase classname="tests.test_extract" name="test_manifiesto_existe_y_no_vacio" time="0.01"/>
<testcase classname="tests.test_dist" name="test_origen[a]" time="0.02"/>
<testcase classname="tests.test_dist" name="test_origen[b]" time="0.03"><failure message="assert 1 == 2">detalle</failure></testcase>
<testcase classname="tests.test_api" name="test_omitida" time="0.00"><skipped message="x"/></testcase>
</testsuite></testsuites>"""


def test_lee_el_junit_con_resultado_duracion_y_variantes(tmp_path):
    xml = tmp_path / "j.xml"
    xml.write_text(XML, encoding="utf-8")
    pruebas = ip.leer_junit(xml)
    assert [(p["archivo"], p["base"], p["resultado"]) for p in pruebas] == [("tests/test_extract.py", "test_manifiesto_existe_y_no_vacio", "passed"), ("tests/test_dist.py", "test_origen", "passed"),
                                                                           ("tests/test_dist.py", "test_origen", "failed"), ("tests/test_api.py", "test_omitida", "skipped")]
    assert pruebas[2]["mensaje"] == "assert 1 == 2" and abs(pruebas[1]["duracion"] - 0.02) < 1e-9


def test_una_prueba_parametrizada_pasa_solo_si_pasan_todas_sus_variantes(tmp_path):
    xml = tmp_path / "j.xml"
    xml.write_text(XML, encoding="utf-8")
    r = ip.resultado_por_caso(ip.leer_junit(xml))
    assert r["tests/test_dist.py::test_origen"][:2] == (2, 1) and r["tests/test_dist.py::test_origen"][3] == "failed"
    assert r["tests/test_extract.py::test_manifiesto_existe_y_no_vacio"][3] == "passed"


def test_el_recalculo_independiente_coincide_con_los_kpi_publicados():
    filas, maxdif, qr = ip.metricas_analisis()
    assert len(filas) == 6 and maxdif < 1e-9
    assert [int(f[2]) for f in filas] == [302, 92, 1173, 2095, 1031, 11]
    assert qr["llave_confianza"] in ("alta", "media", "baja")


def test_wilson_propio_coincide_con_los_vectores_conocidos():
    lo, hi = ip.wilson(5, 10)
    assert round(lo, 4) == 0.2366 and round(hi, 4) == 0.7634


def test_el_informe_se_genera_con_esperado_obtenido_y_sin_rutas_de_la_maquina(tmp_path, monkeypatch):
    casos = ip.matriz.casos()
    pruebas = [{"archivo": c[6].split("::")[0], "nombre": c[6].split("::")[1], "base": c[6].split("::")[1], "resultado": "passed", "duracion": 0.01, "mensaje": ""} for c in casos]
    pruebas[0]["resultado"] = "failed"
    pruebas[0]["mensaje"] = "assert falso"
    cobertura = [("src/common.py", 61, 22, 64.0), ("src/load/relacional.py", 164, 4, 97.6)]
    sin_resultado, fallan = ip.generar(pruebas, cobertura, 12.3, 1, True, tmp_path)
    md = (tmp_path / "informe_pruebas.md").read_text(encoding="utf-8")
    assert sin_resultado == 0 and len(fallan) == 1 and "FALLA" in md and "cumplió lo esperado" in md and "Resultado esperado" in md
    assert "Salida real registrada el" in md and "C:\\" not in md and "Users" not in md
    assert "descarga y escritura de Bronze" in md   # el motivo de la cobertura baja aparece junto al módulo
    assert len((tmp_path / "informe_pruebas.csv").read_text(encoding="utf-8").splitlines()) == len(casos) + 1
    assert (tmp_path / "cobertura_pruebas.csv").exists()


def test_todo_modulo_con_cobertura_baja_declarada_tiene_un_motivo():
    for modulo in ip.MOTIVOS:
        assert (ROOT / modulo).exists(), modulo
    assert all(len(m) > 20 for m in ip.MOTIVOS.values())
