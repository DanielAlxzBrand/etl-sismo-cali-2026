"""El pipeline (transformar y gold) se ejecuta en una copia temporal y reproduce byte a byte los CSV y JSON versionados: es la misma comparación que hace el DAG.

Se ejecuta en un subproceso con el intérprete actual, sobre una copia mínima (src, config, data y la entrada de docs/silver); el repositorio no se escribe.
"""
import hashlib
import os
import shutil
import subprocess
import sys

import pytest

from src.common import ROOT

CODIGO = "from src.transform.integrate import run_transform; from src.transform.build_gold import run_gold; run_transform(); run_gold()"
SALIDAS = ["data/silver/silver_construcciones.csv", "data/silver/silver_estrato_barrio.csv", "data/silver/silver_integrated.csv", "data/silver/silver_orphans_left.csv",
           "data/silver/silver_orphans_right.csv", "data/silver/quality_report.json", "data/gold/gold_final.csv", "data/gold/kpis_gold.csv", "data/gold/kpis_sensibilidad.csv"]


def _sha(ruta):
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


HUELLAS_REPO = {s: _sha(ROOT / s) for s in SALIDAS}   # antes de ejecutar nada


def _copia(destino):
    for carpeta in ("src", "config", "data"):
        shutil.copytree(ROOT / carpeta, destino / carpeta, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (destino / "docs" / "silver").mkdir(parents=True)
    shutil.copy2(ROOT / "docs/silver/hallazgos_eda.md", destino / "docs/silver/hallazgos_eda.md")


@pytest.fixture(scope="module")
def corrida(tmp_path_factory):
    destino = tmp_path_factory.mktemp("pipeline")
    _copia(destino)
    antes = {r: _sha(destino / r) for r in SALIDAS}
    r = subprocess.run([sys.executable, "-c", CODIGO], cwd=destino, capture_output=True, text=True, encoding="utf-8", errors="replace", env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    return destino, antes, r


def test_las_etapas_terminan_sin_error(corrida):
    _, _, r = corrida
    assert r.returncode == 0, r.stderr[-800:]


def test_los_nueve_archivos_de_la_linea_base_se_reproducen_byte_a_byte(corrida):
    destino, _, r = corrida
    assert r.returncode == 0
    distintos = [s for s in SALIDAS if _sha(destino / s) != _sha(ROOT / s)]
    assert distintos == [], "salidas distintas de las versionadas (¿cambió la versión de pandas u otra dependencia?): " + ", ".join(distintos)


def test_regenerar_no_cambia_lo_que_ya_estaba_versionado_en_la_copia(corrida):
    destino, antes, r = corrida
    assert r.returncode == 0 and {s: _sha(destino / s) for s in SALIDAS} == antes


def test_el_repositorio_no_se_toco(corrida):
    _, _, r = corrida
    assert r.returncode == 0
    assert {s: _sha(ROOT / s) for s in SALIDAS} == HUELLAS_REPO   # trabajó sobre la copia: las salidas versionadas conservan su sha256
