"""Respaldo lógico, restauración con conciliación y reglas de la medición de lotes, sin servidor MySQL (SQLite con el mismo esquema)."""
import importlib.util
import json
import sys

import pytest

from src.common import ROOT
from src.load import conexion, relacional


def _cargar(ruta, nombre):
    sys.path.insert(0, str(ROOT / "scripts" / "mysql"))
    espec = importlib.util.spec_from_file_location(nombre, ROOT / ruta)
    modulo = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(modulo)
    return modulo


rr = _cargar("scripts/mysql/respaldar_restaurar.py", "respaldar_restaurar_prueba")
bench = _cargar("scripts/mysql/benchmark_lotes.py", "benchmark_lotes_prueba")
ver = _cargar("scripts/mysql/verificar_mysql.py", "verificar_mysql_prueba")


@pytest.fixture(scope="module")
def origen(tmp_path_factory):
    c = conexion.conectar_sqlite(tmp_path_factory.mktemp("rr") / "origen.db")
    relacional.cargar(c, "sqlite")
    yield c
    c.close()


@pytest.fixture()
def respaldo(origen, tmp_path_factory):
    carpeta = tmp_path_factory.mktemp("respaldo")
    return carpeta, rr.respaldar(origen, carpeta)


def test_el_respaldo_escribe_un_csv_por_tabla_con_manifiesto(respaldo):
    carpeta, man = respaldo
    assert set(man["tablas"]) == set(rr.ORDEN)
    assert {p.name for p in carpeta.iterdir()} == {f"{t}.csv" for t in rr.ORDEN} | {rr.MANIFIESTO}
    assert man["tablas"]["construccion"]["filas"] == 5146
    assert json.loads((carpeta / rr.MANIFIESTO).read_text(encoding="utf-8"))["tablas"] == man["tablas"]


def test_restaurar_reproduce_cada_tabla_con_la_misma_huella(origen, respaldo):
    carpeta, man = respaldo
    destino = conexion.conectar_sqlite()
    rr.restaurar(destino, "sqlite", carpeta)
    resultado = rr.conciliar(origen, destino, man)
    assert len(resultado) == 7 and all(n0 == n1 and igual for _, n0, n1, igual in resultado)
    destino.close()


def test_un_respaldo_alterado_se_rechaza_antes_de_restaurar(respaldo):
    carpeta, _ = respaldo
    ruta = carpeta / "kpi.csv"
    ruta.write_text(ruta.read_text(encoding="utf-8").replace("K1", "K9", 1), encoding="utf-8", newline="")
    destino = conexion.conectar_sqlite()
    with pytest.raises(rr.RespaldoError, match="manifiesto"):
        rr.restaurar(destino, "sqlite", carpeta)
    assert destino.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()[0] == 0
    destino.close()


def test_no_se_restaura_encima_de_datos(origen, respaldo):
    carpeta, _ = respaldo
    with pytest.raises(rr.RespaldoError, match="no está vacía"):
        rr.restaurar(origen, "sqlite", carpeta, reiniciar=False)


def test_el_respaldo_debe_ir_fuera_del_repositorio(origen):
    with pytest.raises(rr.RespaldoError, match="fuera del repositorio"):
        rr.respaldar(origen, ROOT / "respaldo_no_permitido")
    assert not (ROOT / "respaldo_no_permitido").exists()


def test_el_texto_estable_distingue_nulo_de_cadena_vacia_y_formatea_los_tipos():
    from datetime import date
    from decimal import Decimal
    assert rr._texto(None) == rr.NULO and rr._texto("") == "" and rr._texto(Decimal("1.50")) == "1.50" and rr._texto(0.1) == "0.1"
    assert rr._texto(date(2026, 8, 10)) == "2026-08-10" and rr._texto(True) == "1"
    with pytest.raises(rr.RespaldoError):
        rr._texto(rr.NULO)


def test_una_restauracion_que_falla_no_deja_datos_a_medias(origen, respaldo, monkeypatch):
    carpeta, _ = respaldo
    ruta = carpeta / "kpi.csv"
    lineas = ruta.read_text(encoding="utf-8").split("\n")
    lineas[1] = lineas[1].replace(lineas[1].split(",")[1], "texto", 1)   # un valor ilegible en una columna numérica
    ruta.write_text("\n".join(lineas), encoding="utf-8", newline="")
    man = json.loads((carpeta / rr.MANIFIESTO).read_text(encoding="utf-8"))
    man["tablas"]["kpi"]["sha256"] = relacional.sha256_file(ruta)   # el manifiesto coincide: el fallo es de conversión, no de huella
    (carpeta / rr.MANIFIESTO).write_text(json.dumps(man), encoding="utf-8")
    destino = conexion.conectar_sqlite()
    with pytest.raises(Exception):
        rr.restaurar(destino, "sqlite", carpeta)
    assert all(destino.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] == 0 for t in rr.ORDEN)
    destino.close()


# ---------------------------------------------------------------- medición de lotes
def test_percentil_interpola_y_con_pocas_repeticiones_se_acerca_al_maximo():
    assert bench.percentil([1, 2, 3, 4, 5], 50) == 3
    assert bench.percentil([1, 2, 3, 4, 5], 95) == pytest.approx(4.8)
    assert bench.percentil([7], 95) == 7


def test_el_lote_elegido_es_el_de_menor_mediana_y_con_empate_el_mas_pequeno():
    assert bench.elegir({1: ([], 9.0), 500: ([], 1.00), 1000: ([], 0.80), 2000: ([], 0.90)}) == 1000
    assert bench.elegir({1: ([], 9.0), 500: ([], 1.00), 1000: ([], 1.02), 2000: ([], 1.04)}) == 500
    assert bench.elegir({1: ([], 0.1), 500: ([], 1.0), 1000: ([], 1.0), 2000: ([], 1.0)}) == 500   # la carga fila a fila no compite como valor por defecto


def test_el_valor_de_lote_de_la_configuracion_es_una_de_las_opciones_medidas():
    from src.common import load_config
    assert load_config()["almacenamiento"]["lote"] in (500, 1000, 2000)


def test_los_scripts_en_vivo_solo_operan_sobre_la_base_de_prueba():
    for nombre in ("verificar_mysql.py", "benchmark_lotes.py", "respaldar_restaurar.py"):
        texto = (ROOT / "scripts" / "mysql" / nombre).read_text(encoding="utf-8")
        assert "prueba=True" in texto and "endswith(\"_prueba\")" in texto, nombre
    assert ver.TABLAS_HIJAS_A_PADRES[-1] == "comuna" and ver.TABLAS_HIJAS_A_PADRES[0] == "kpi_sensibilidad"


def test_los_scripts_en_vivo_fallan_con_claridad_si_no_hay_servidor(monkeypatch, capsys):
    def sin_servidor(*a, **k):
        raise conexion.ConexionError("no se pudo conectar a MySQL: no hay un servidor")
    monkeypatch.setattr(conexion, "conectar_mysql", sin_servidor)
    assert ver.main([]) == 1
    assert bench.main(["--repeticiones", "1"]) == 3
    assert rr.main([]) == 3
