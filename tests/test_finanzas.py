"""Costos (6.4): la fórmula de costo por ejecución, los parámetros vacíos y la regla de fuente y fecha.

Los valores numéricos de este archivo son «valores de prueba, no son precios»: se inventaron para comprobar la aritmética y no representan ningún costo real.
"""
import importlib.util
import sys

import pytest
import yaml

from src.common import ROOT

CARPETA = ROOT / "scripts" / "finanzas"
_espec = importlib.util.spec_from_file_location("costos", CARPETA / "costos.py")
costos = importlib.util.module_from_spec(_espec)
_espec.loader.exec_module(costos)

NECESARIOS = ["precio_hora_computo", "precio_gb_mes_almacenamiento", "ejecuciones_por_mes", "tarifa_hora_equipo", "horas_equipo_por_ejecucion"]


def _parametros(valores):
    """Parámetros con la forma del YAML; los de `valores` tienen valor, fuente y fecha de prueba."""
    p = {n: {"valor": None, "unidad": "unidad", "descripcion": "d", "fuente": None, "fecha": None} for n in costos.cargar_parametros()}
    for n, v in valores.items():
        p[n].update(valor=v, fuente="valor de prueba, no es un precio", fecha="2000-01-01")
    return p


COMPLETOS = {"precio_hora_computo": 2, "precio_gb_mes_almacenamiento": 3, "ejecuciones_por_mes": 4, "tarifa_hora_equipo": 10, "horas_equipo_por_ejecucion": 0.5}


def test_con_los_parametros_reales_vacios_faltan_los_cinco_que_necesita_el_costo_por_ejecucion():
    assert costos.faltantes(costos.cargar_parametros()) == NECESARIOS


def test_el_costo_por_ejecucion_coincide_con_la_formula_calculada_a_mano():
    """t = 3600 s (1 h), A = 1024 MB (1 GB): cómputo 1 × 2 = 2; almacenamiento 1 × 3 ÷ 4 = 0,75; equipo 0,5 × 10 = 5; total 7,75."""
    r = costos.costo_por_ejecucion(_parametros(COMPLETOS), 3600, 1024)
    assert r["computo"] == pytest.approx(2.0) and r["almacenamiento"] == pytest.approx(0.75) and r["equipo"] == pytest.approx(5.0) and r["total"] == pytest.approx(7.75)


def test_el_costo_escala_con_el_tiempo_y_con_el_almacenamiento():
    p = _parametros(COMPLETOS)
    base, doble_t, doble_a = (costos.costo_por_ejecucion(p, t, a)["total"] for t, a in ((3600, 1024), (7200, 1024), (3600, 2048)))
    assert doble_t - base == pytest.approx(2.0) and doble_a - base == pytest.approx(0.75)


@pytest.mark.parametrize("falta", NECESARIOS)
def test_si_falta_un_solo_parametro_no_calcula_nada_y_lo_nombra(falta):
    valores = {k: v for k, v in COMPLETOS.items() if k != falta}
    with pytest.raises(costos.ParametroNoValido, match=falta):
        costos.costo_por_ejecucion(_parametros(valores), 3600, 1024)


def test_ejecuciones_por_mes_en_cero_se_rechaza():
    with pytest.raises(costos.ParametroNoValido):
        costos.costo_por_ejecucion(_parametros({**COMPLETOS, "ejecuciones_por_mes": 0}), 3600, 1024)


# ---------------------------------------------------------------- regla de fuente y fecha
def test_un_valor_sin_fuente_o_sin_fecha_se_rechaza():
    p = _parametros({})
    p["precio_hora_computo"].update(valor=5)
    assert any("precio_hora_computo" in e for e in costos.revisar_parametros(p))
    p["precio_hora_computo"].update(fuente="valor de prueba, no es un precio")
    assert any("precio_hora_computo" in e for e in costos.revisar_parametros(p))      # falta la fecha
    p["precio_hora_computo"].update(fecha="2000-01-01")
    assert costos.revisar_parametros(p) == []


def test_un_valor_que_no_es_un_numero_se_rechaza():
    p = _parametros({})
    p["tarifa_hora_equipo"].update(valor="mucho", fuente="x", fecha="2000-01-01")
    assert any("número" in e for e in costos.revisar_parametros(p))


def test_el_yaml_real_tiene_todos_los_parametros_vacios_y_con_su_estructura():
    datos = yaml.safe_load((ROOT / "config" / "parametros_costos.yaml").read_text(encoding="utf-8"))
    assert datos and all(set(p) == {"valor", "unidad", "descripcion", "fuente", "fecha"} for p in datos.values())
    assert all(p["valor"] is None and p["unidad"] and p["descripcion"] for p in datos.values())
    assert set(NECESARIOS) <= set(datos)


# ---------------------------------------------------------------- línea de comandos
def _escribir_yaml(ruta, parametros):
    ruta.write_text(yaml.safe_dump(parametros, allow_unicode=True), encoding="utf-8")
    return ruta


def test_con_parametros_vacios_muestra_el_consumo_y_dice_que_no_calcula(capsys):
    assert costos.main([]) == 0
    salida = capsys.readouterr().out
    assert "Consumo medido" in salida and "tiempo_main_todas_las_etapas" in salida
    assert "costo no calculado: faltan parámetros: precio_hora_computo" in salida and "Costo por ejecución" not in salida


def test_con_parametros_completos_calcula(tmp_path, capsys):
    recursos = tmp_path / "recursos.csv"
    recursos.write_text("magnitud,valor,unidad,origen,fecha\ntiempo_main_todas_las_etapas,3600,s,prueba,2000-01-01\ntamano_data_mb,1024,MB,prueba,2000-01-01\n", encoding="utf-8")
    yaml_ruta = _escribir_yaml(tmp_path / "p.yaml", _parametros(COMPLETOS))
    assert costos.main(["--parametros", str(yaml_ruta), "--recursos", str(recursos)]) == 0
    assert "total 7.7500" in capsys.readouterr().out


def test_un_parametro_con_valor_y_sin_fuente_detiene_la_linea_de_comandos(tmp_path, capsys):
    p = _parametros({})
    p["precio_hora_computo"].update(valor=1)
    assert costos.main(["--parametros", str(_escribir_yaml(tmp_path / "p.yaml", p))]) == 2
    assert "precio_hora_computo" in capsys.readouterr().err


def test_los_recursos_medidos_del_repositorio_se_pueden_leer():
    r = costos.leer_recursos()
    assert {"tiempo_main_todas_las_etapas", "pico_memoria_main_todas_las_etapas", "tamano_data_mb", "tamano_base_sqlite_mb", "tamano_zip_de_prueba_mb"} <= set(r)
    assert all(float(r[k]) > 0 for k in ("tiempo_main_todas_las_etapas", "pico_memoria_main_todas_las_etapas", "tamano_data_mb"))
