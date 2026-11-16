"""Guardián de DF-20: `airflow-init` comprueba la conexión con la base de metadatos y termina con código 1 si falla (`orquestacion/docker-compose.yaml`).

Por qué existe: al probar el zip con un volumen de Postgres de otra instalación, `airflow-init` terminó con código 0 aunque la migración falló por «password authentication failed»; el servidor de Airflow quedó «unhealthy» minutos después.
El script del compose oficial no usa `set -e`, termina en un `ls` y hasta `/entrypoint airflow version` sale con 0 (medido), así que `set -e` no habría bastado: se añade `airflow db check`, que sale con 1 si no se conecta.
Aquí se comprueba, sin Docker, que el compose, el generador, el diff y el documento de diferencias dicen lo mismo; que la comprobación va después de `airflow version` y antes del `ls` final; que falla con `exit 1` y deja ver solo dos líneas de error; que
no imprime la traza (que lleva la dirección de conexión); y, ejecutando el mismo `if … else … exit 1` con `bash` si el equipo lo tiene, que el código de salida es 1 cuando la comprobación falla y 0 cuando no.
Qué NO demuestra: lo que hace Docker. Que con el volumen viejo `airflow-init` termine con 1 y los demás servicios no arranquen, y que con el volumen nuevo todo siga sano, se midió ejecutando el compose (evidencia aparte).
"""
import importlib.util
import re
import subprocess

import pytest
import yaml

from bash_para_pruebas import bash_que_lee_rutas
from src.common import ROOT

COMPOSE = ROOT / "orquestacion" / "docker-compose.yaml"


def _generador():
    espec = importlib.util.spec_from_file_location("generar_compose_db_check", ROOT / "scripts" / "orquestacion" / "generar_compose.py")
    modulo = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(modulo)
    return modulo


def _orden():
    c = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))
    return c["services"]["airflow-init"]["command"][-1], c


def _bloque(orden):
    """El `if … fi` de la comprobación tal como lo ve bash (YAML ya le quitó la sangría del bloque)."""
    ini = orden.index("if /entrypoint airflow db check")
    return orden[ini:orden.index("\nfi\n", ini) + len("\nfi\n")]


def test_la_comprobacion_va_despues_de_airflow_version_y_antes_del_ls_final_y_falla_con_exit_1():
    orden, _ = _orden()
    assert orden.count("/entrypoint airflow db check") == 1 and orden.count("/entrypoint airflow version") == 1
    assert orden.index("/entrypoint airflow version") < orden.index("/entrypoint airflow db check") < orden.rindex("ls -la")
    bloque = _bloque(orden)
    assert "else" in bloque and "exit 1" in bloque and bloque.index("else") < bloque.index("exit 1")
    assert re.search(r"if /entrypoint airflow db check > /tmp/db_check\.log 2>&1; then", bloque), "la salida de la comprobación va a un archivo y no a la pantalla"


def test_solo_se_muestran_dos_lineas_de_error_y_nunca_la_traza_ni_el_archivo_completo():
    orden, _ = _orden()
    assert "grep -E 'FATAL|OperationalError' /tmp/db_check.log | head -n 2 | cut -c1-200" in orden
    assert "cat /tmp/db_check.log" not in orden and "tail" not in orden.split("db check")[1].split("fi\n")[0]


def test_el_script_sigue_sin_set_e_y_terminando_en_ls_como_dice_la_guia():
    orden, _ = _orden()
    assert "set -e" not in orden
    ultimo = [l.strip() for l in orden.splitlines() if l.strip() and not l.strip().startswith("#")][-1]
    assert ultimo.startswith("ls ")


def test_el_generador_lleva_el_reemplazo_y_el_aviso_y_el_diff_lo_muestran():
    g = _generador()
    assert (g.DB_OFICIAL, g.DB_NUEVO) in g.REEMPLAZOS and g.DB_OFICIAL == "        /entrypoint airflow version\n" and g.DB_NUEVO.startswith(g.DB_OFICIAL)
    assert "DF-13 a DF-20" in g.AVISO and "airflow db check" in g.AVISO
    texto = COMPOSE.read_text(encoding="utf-8")
    assert "DF-13 a DF-20" in texto and "7. En `airflow-init`" in texto
    diff = (ROOT / "orquestacion" / "docker-compose.diff").read_text(encoding="utf-8")
    assert "+        if /entrypoint airflow db check" in diff and "+          exit 1" in diff


def test_las_diferencias_con_la_guia_dicen_lo_mismo_que_el_compose():
    texto = (ROOT / "docs" / "orquestacion" / "diferencias_con_la_guia.md").read_text(encoding="utf-8")
    assert "(DF-13 a DF-20)" in texto and re.search(r"^\| DF-20 \|", texto, re.M)
    fila = [l for l in texto.splitlines() if l.startswith("| DF-20 |")][0]
    for pieza in ("airflow db check", "exit 1", "set -e", "ls", "service_completed_successfully", "código 1"):
        assert pieza in fila, pieza


def test_el_mismo_if_else_exit_1_da_1_si_la_comprobacion_falla_y_0_si_no(tmp_path):
    """Ejecuta el bloque del compose con `bash` y un `/entrypoint` de mentira que falla o no; sin `bash` no hay nada que ejecutar."""
    bash = bash_que_lee_rutas(tmp_path)
    if bash is None:
        pytest.skip("no hay un bash que lea rutas de Windows (Git para Windows lo trae; el de WSL no sirve)")
    orden, _ = _orden()
    bloque = _bloque(orden)
    for sale, esperado in ((1, 1), (0, 0)):
        entrada = tmp_path / f"entrypoint{sale}"
        entrada.write_text(f"#!/bin/sh\necho 'FATAL:  password authentication failed for user \"airflow\"' >&2\necho 'Traceback (most recent call last): url=muy-larga'\nexit {sale}\n", encoding="utf-8", newline="\n")
        guion = tmp_path / f"init{sale}.sh"
        guion.write_text(bloque.replace("/entrypoint", entrada.as_posix()).replace("/tmp/db_check.log", (tmp_path / f"c{sale}.log").as_posix()) + "\necho FIN\n", encoding="utf-8", newline="\n")
        r = subprocess.run([bash, guion.as_posix()], capture_output=True, text=True, encoding="utf-8", errors="replace")
        assert r.returncode == esperado, r.stdout + r.stderr
        if esperado == 1:
            assert "ERROR: could not connect" in r.stdout and "FATAL:  password authentication failed" in r.stdout and "Traceback" not in r.stdout and "FIN" not in r.stdout
        else:
            assert "Connection successful." in r.stdout and "FIN" in r.stdout
