"""El ayudante que elige un `bash` capaz de leer rutas de Windows (`tests/bash_para_pruebas.py`) devuelve uno que sirve y no uno que solo se llama «bash».

Por qué existe: en un PowerShell normal el primer `bash` del PATH puede ser el de WSL, que no lee rutas como `C:/Users/...`; dos pruebas del compose de Airflow fallaban con ese `bash` (DEF-022).
Aquí se comprueba, sin Docker, que un candidato que no ejecuta el guion de sonda se descarta, que los candidatos vacíos o inexistentes se ignoran y que, si hay un `bash` bueno detrás de uno malo, se devuelve el bueno.
Qué NO demuestra: que el equipo tenga un `bash` (si no lo tiene, las pruebas que lo usan se omiten con un motivo visible).
"""
import sys

import pytest

import bash_para_pruebas as bp


def test_un_candidato_que_no_ejecuta_el_guion_se_descarta(tmp_path, monkeypatch):
    # el intérprete de Python no puede ejecutar «exit 0» como guion de shell: sale con error y no sirve de bash
    monkeypatch.setattr(bp, "_candidatos", lambda: [sys.executable])
    assert bp.bash_que_lee_rutas(tmp_path) is None


def test_los_candidatos_vacios_o_inexistentes_se_ignoran(tmp_path, monkeypatch):
    monkeypatch.setattr(bp, "_candidatos", lambda: [None, "", str(tmp_path / "no_existe" / "bash")])
    assert bp.bash_que_lee_rutas(tmp_path) is None


def test_si_hay_un_bash_bueno_detras_de_uno_malo_se_devuelve_el_bueno(tmp_path, monkeypatch):
    bueno = bp.bash_que_lee_rutas(tmp_path)
    if bueno is None:
        pytest.skip("el equipo no tiene un bash que lea rutas de Windows")
    monkeypatch.setattr(bp, "_candidatos", lambda: [sys.executable, bueno])
    assert bp.bash_que_lee_rutas(tmp_path) == bueno
