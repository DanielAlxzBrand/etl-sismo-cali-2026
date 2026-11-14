"""Configuración de las pruebas: protege defectos ya corregidos del entorno de pruebas."""
import re

from src.common import ROOT


def test_pytest_ini_fija_la_ruta_de_importacion_y_la_carpeta_de_pruebas():
    """Sin `pythonpath = .` el ejecutable `pytest -q` fallaba con ModuleNotFoundError para `src` (solo `python -m pytest` funcionaba)."""
    ini = (ROOT / "pytest.ini").read_text(encoding="utf-8")
    assert re.search(r"(?m)^pythonpath\s*=\s*\.\s*$", ini) and re.search(r"(?m)^testpaths\s*=\s*tests\s*$", ini)


def test_todos_los_archivos_de_pruebas_terminan_en_py():
    """Un archivo `test_quality.p` (sin la y) no se recolectaba y sus pruebas no se ejecutaban."""
    sueltos = [p.name for p in (ROOT / "tests").glob("test_*") if p.is_file() and p.suffix != ".py"]
    assert sueltos == []


def test_coverage_esta_en_los_requisitos_del_proyecto():
    assert re.search(r"(?m)^coverage>=\d", (ROOT / "requirements.txt").read_text(encoding="utf-8"))


def test_requirements_fija_pandas_en_la_version_de_la_linea_base():
    """Con otra versión de pandas cambian celdas del decimal 12 de gold_final.csv y de la base SQLite (D56)."""
    assert re.search(r"(?m)^pandas==3\.0\.6$", (ROOT / "requirements.txt").read_text(encoding="utf-8"))
