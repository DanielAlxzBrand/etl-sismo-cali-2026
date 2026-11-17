"""Gold lee solo Silver y no usa `shapely` (ADR-014).

El paso espacial vive en Silver (regla R09, `src/transform/clean_api.py`). Aquí se comprueban dos cosas sobre Gold: que su código no importa `shapely` y que se regenera desde una copia
que tiene `src`, `config` y `data/silver` pero NO `data/bronze`, con los mismos sha256 que los tres archivos de Gold versionados. Si Gold leyera Bronze, la copia fallaría.
"""
import ast
import hashlib
import os
import shutil
import subprocess
import sys

from src.common import ROOT

GOLD = ["data/gold/gold_final.csv", "data/gold/kpis_gold.csv", "data/gold/kpis_sensibilidad.csv"]
CODIGO = "from src.transform.build_gold import run_gold; run_gold()"


def importa_shapely(fuente):
    """True si el código fuente importa `shapely` o alguno de sus submódulos."""
    for nodo in ast.walk(ast.parse(fuente)):
        if isinstance(nodo, ast.Import) and any(a.name.split(".")[0] == "shapely" for a in nodo.names):
            return True
        if isinstance(nodo, ast.ImportFrom) and (nodo.module or "").split(".")[0] == "shapely":
            return True
    return False


def _sha(ruta):
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def test_el_codigo_de_gold_no_importa_shapely():
    assert not importa_shapely((ROOT / "src" / "transform" / "build_gold.py").read_text(encoding="utf-8"))
    assert importa_shapely((ROOT / "src" / "transform" / "clean_api.py").read_text(encoding="utf-8")), "el paso espacial sí está en Silver (R09)"


def test_el_detector_de_shapely_reconoce_cada_forma_de_importarlo():
    assert importa_shapely("import shapely")
    assert importa_shapely("import shapely.geometry as g")
    assert importa_shapely("from shapely.geometry import Point")
    assert importa_shapely("def f():\n    from shapely.strtree import STRtree\n")
    assert not importa_shapely("import pandas as pd\nfrom src.common import ROOT\n")
    assert not importa_shapely("import shapelyish")


def test_gold_se_regenera_desde_silver_sin_data_bronze_con_los_mismos_sha256(tmp_path):
    for carpeta in ("src", "config"):
        shutil.copytree(ROOT / carpeta, tmp_path / carpeta, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copytree(ROOT / "data" / "silver", tmp_path / "data" / "silver")
    (tmp_path / "data" / "gold").mkdir()
    assert not (tmp_path / "data" / "bronze").exists() and not any((tmp_path / "data" / "gold").iterdir()), "la copia parte sin Bronze y sin salidas de Gold"
    r = subprocess.run([sys.executable, "-c", CODIGO], cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", errors="replace", env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    assert r.returncode == 0, r.stderr[-800:]
    assert not (tmp_path / "data" / "bronze").exists()
    assert {s: _sha(tmp_path / s) for s in GOLD} == {s: _sha(ROOT / s) for s in GOLD}, "Gold regenerado desde Silver debe coincidir con los tres archivos versionados"
