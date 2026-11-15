"""La herramienta que comprueba que un cambio de textos no tocó el código (`scripts/validacion/igualdad_de_codigo.py`) detecta lo que debe, y los notebooks son válidos.

Por qué existe: la limpieza de textos de la auditoría intermedia quitó el vocativo de diez celdas de notebooks y cambió docstrings de scripts. Que eso no alteró ningún cálculo se demuestra con esta
herramienta contra la etiqueta `auditoria-inicio` (EV-093), y estas pruebas comprueban que la herramienta funciona: ve un cambio de código, de salida, de metadatos o de celdas, y no se
confunde con un cambio de docstring o de comentario. Además cada notebook se valida con `nbformat` y su JSON debe estar íntegro.
Qué NO demuestra: que el código sea correcto ni que los notebooks se ejecuten; solo que su forma es válida y que la herramienta distingue textos de código.
"""
import importlib.util
import json

import nbformat
import pytest

from src.common import ROOT

_spec = importlib.util.spec_from_file_location("igualdad_de_codigo", ROOT / "scripts" / "validacion" / "igualdad_de_codigo.py")
igualdad = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(igualdad)

BASE_PY = '"""Módulo."""\nimport os\n\n\ndef f(x):\n    """Suma uno."""\n    # comentario\n    return x + 1\n'


def test_python_un_docstring_o_un_comentario_no_cambian_el_codigo():
    assert igualdad.comparar_python(BASE_PY, BASE_PY) == "igual"
    assert igualdad.comparar_python(BASE_PY, BASE_PY.replace("Suma uno.", "Suma uno al valor.")) == "solo cambian textos"
    assert igualdad.comparar_python(BASE_PY, BASE_PY.replace("# comentario", "# otro comentario")) == "solo cambian textos"
    assert igualdad.comparar_python(BASE_PY, BASE_PY.replace('"""Módulo."""\n', "")) == "solo cambian textos"


def test_python_un_cambio_de_codigo_se_detecta():
    assert igualdad.comparar_python(BASE_PY, BASE_PY.replace("x + 1", "x + 2")) == "cambia el código"
    assert igualdad.comparar_python(BASE_PY, BASE_PY.replace("import os", "import sys")) == "cambia el código"
    assert igualdad.comparar_python(BASE_PY, BASE_PY + "y = 1\n") == "cambia el código"
    assert igualdad.comparar_python(BASE_PY, BASE_PY.replace("return x + 1", "return 'x + 1'")) == "cambia el código"


def _notebook(codigo="x = 1\n", salida="1", texto="Hola", cuenta=1, meta=None):
    nb = nbformat.v4.new_notebook()
    nb.cells = [nbformat.v4.new_markdown_cell(texto), nbformat.v4.new_code_cell(codigo, execution_count=cuenta, outputs=[nbformat.v4.new_output("stream", name="stdout", text=salida)])]
    nb.cells[0]["id"], nb.cells[1]["id"] = "aaaaaaaa", "bbbbbbbb"
    nb.cells[1].metadata = meta or {}
    return nbformat.writes(nb)


def test_notebook_los_textos_no_cambian_el_codigo():
    base = _notebook()
    assert igualdad.comparar_notebooks(base, base) == "igual"
    assert igualdad.comparar_notebooks(base, _notebook(texto="Otro texto")) == "solo cambian textos"
    assert igualdad.comparar_notebooks(base, _notebook(codigo='"""Aquí lo primero."""\nx = 1\n')) == "solo cambian textos"


def test_notebook_un_cambio_de_codigo_de_salida_o_de_metadatos_se_detecta():
    base = _notebook()
    assert igualdad.comparar_notebooks(base, _notebook(codigo="x = 2\n")) == "cambia el código"
    assert igualdad.comparar_notebooks(base, _notebook(salida="2")) == "cambia el código"
    assert igualdad.comparar_notebooks(base, _notebook(cuenta=2)) == "cambia el código"
    assert igualdad.comparar_notebooks(base, _notebook(meta={"tags": ["x"]})) == "cambia el código"
    otro = nbformat.reads(base, as_version=4)
    otro.cells.append(nbformat.v4.new_code_cell("y = 1"))
    assert igualdad.comparar_notebooks(base, nbformat.writes(otro)) == "cambia el código"
    cambiado = nbformat.reads(base, as_version=4)
    cambiado.cells[0].cell_type = "raw"
    assert igualdad.comparar_notebooks(base, nbformat.writes(cambiado)) == "cambia el código"


def test_notebook_un_json_roto_o_invalido_se_rechaza():
    base = _notebook()
    with pytest.raises(Exception):
        igualdad.comparar_notebooks(base, base[:-20])
    roto = json.loads(base)
    roto["cells"][1].pop("outputs")
    with pytest.raises(Exception):
        igualdad.comparar_notebooks(base, json.dumps(roto))


def test_clasificacion_de_archivos_nuevos_y_eliminados():
    assert igualdad.comparar("a.py", None, BASE_PY) == "nuevo"
    assert igualdad.comparar("a.py", BASE_PY, None) == "eliminado"


def test_los_notebooks_del_proyecto_son_validos_y_su_json_esta_integro():
    cuadernos = sorted((ROOT / "notebooks").glob("*.ipynb"))
    assert len(cuadernos) == 5
    for ruta in cuadernos:
        texto = ruta.read_text(encoding="utf-8")
        assert json.loads(texto)["nbformat"] == 4, ruta.name
        nb = nbformat.reads(texto, as_version=4)
        nbformat.validate(nb)
        assert nb.cells and all("".join(c.source).strip() for c in nb.cells), ruta.name
