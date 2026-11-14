"""Carga a SQLite (load_to_sqlite): se ejecuta en una carpeta temporal y su contenido se compara tabla a tabla con la base versionada, sin escribir en el repositorio."""
import hashlib
import shutil
import sqlite3

import pytest

from src.common import ROOT
from src.load import load_database

ENTRADAS = ["data/silver/silver_integrated.csv", "data/gold/gold_final.csv", "data/gold/kpis_gold.csv", "data/gold/kpis_sensibilidad.csv"]
TABLAS = ["silver_integrated", "gold_final", "kpis_gold", "kpis_sensibilidad"]


def _huellas(ruta):
    """Contenido de cada tabla ordenado: el archivo SQLite no es idéntico byte a byte entre ejecuciones, su contenido sí."""
    conn = sqlite3.connect(f"{ruta.as_uri()}?mode=ro", uri=True)
    try:
        salida = {}
        for t in TABLAS:
            cols = [c[1] for c in conn.execute(f"PRAGMA table_info({t})")]
            h, n = hashlib.sha256(), 0
            for fila in conn.execute(f"SELECT * FROM {t} ORDER BY {', '.join(cols)}"):
                h.update(repr(fila).encode("utf-8"))
                n += 1
            salida[t] = (n, h.hexdigest(), cols)
        return salida
    finally:
        conn.close()


@pytest.fixture()
def carpeta(tmp_path, monkeypatch):
    for r in ENTRADAS:
        (tmp_path / r).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / r, tmp_path / r)
    (tmp_path / "data/gold").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(load_database, "ROOT", tmp_path)
    return tmp_path


def test_el_contenido_cargado_es_igual_al_de_la_base_versionada(carpeta):
    load_database.load_to_sqlite()
    nueva, versionada = _huellas(carpeta / "data/gold/etl_sismo.db"), _huellas(ROOT / "data/gold/etl_sismo.db")
    assert nueva == versionada and [nueva[t][0] for t in TABLAS] == [5146, 5146, 23, 107]


def test_cargar_dos_veces_reemplaza_las_tablas_sin_duplicar_filas(carpeta):
    load_database.load_to_sqlite()
    primera = _huellas(carpeta / "data/gold/etl_sismo.db")
    load_database.load_to_sqlite()
    assert _huellas(carpeta / "data/gold/etl_sismo.db") == primera


def test_con_una_sola_fila_por_tabla_se_cargan_cuatro_filas(carpeta):
    for r in ENTRADAS:
        lineas = (carpeta / r).read_text(encoding="utf-8").splitlines()
        (carpeta / r).write_text("\n".join(lineas[:2]) + "\n", encoding="utf-8", newline="")
    load_database.load_to_sqlite()
    assert [v[0] for v in _huellas(carpeta / "data/gold/etl_sismo.db").values()] == [1, 1, 1, 1]


def test_un_csv_ausente_falla_y_no_deja_la_conexion_abierta(carpeta):
    (carpeta / "data/gold/kpis_gold.csv").unlink()
    with pytest.raises(FileNotFoundError):
        load_database.load_to_sqlite()
    (carpeta / "data/gold/etl_sismo.db").unlink()   # en Windows falla si el archivo quedó abierto por la conexión


def test_la_carga_no_modifica_el_repositorio(carpeta):
    antes = hashlib.sha256((ROOT / "data/gold/etl_sismo.db").read_bytes()).hexdigest()
    load_database.load_to_sqlite()
    assert hashlib.sha256((ROOT / "data/gold/etl_sismo.db").read_bytes()).hexdigest() == antes
