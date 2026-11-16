"""Guardián de DF-19: el `chown` de `airflow-init` no recorre el proyecto montado en solo lectura (`orquestacion/docker-compose.yaml`).

Por qué existe: el compose oficial hace `chown -R … /opt/airflow/`; nuestra adaptación monta el proyecto en `/opt/airflow/medallon:ro` y ese recorrido entraba a su `.venv` y dejaba una línea «Read-only file system»
por archivo (visto al probar el zip; el contenedor igual terminaba con código 0). Ahora un `find … -prune` salta ese montaje. Aquí se comprueba que el compose, el generador, el diff y el documento de
diferencias dicen lo mismo, que el compose del repositorio es exactamente lo que sale del oficial (sin red: se deshacen los reemplazos y se comprueba el sha256 del oficial) y que el comando salta el montaje de verdad.
Qué NO demuestra: lo que hace Docker (que el contenedor termine bien y que `logs`, `dags`, `plugins` y `config` queden con el dueño correcto se comprobó ejecutando el DAG desde un zip nuevo, EV aparte).
"""
import importlib.util
import re
import shutil
import subprocess

import pytest
import yaml

from src.common import ROOT

COMPOSE = ROOT / "orquestacion" / "docker-compose.yaml"
PRUNE = "find /opt/airflow -path /opt/airflow/medallon -prune -o -exec chown -h"


def _generador():
    espec = importlib.util.spec_from_file_location("generar_compose_chown", ROOT / "scripts" / "orquestacion" / "generar_compose.py")
    modulo = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(modulo)
    return modulo


def _orden_de_init():
    c = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))
    return c["services"]["airflow-init"]["command"][-1], c


def test_el_init_salta_el_montaje_del_proyecto_y_ya_no_hace_chown_recursivo_de_todo_opt_airflow():
    orden, _ = _orden_de_init()
    assert PRUNE in orden
    assert re.search(r'chown -R "\$\{AIRFLOW_UID:-50000\}:0" /opt/airflow/\s*$', orden, re.M) is None, "el chown recursivo de todo /opt/airflow volvió"


def test_lo_que_se_salta_es_exactamente_donde_se_monta_el_proyecto_y_las_carpetas_compartidas_siguen_con_su_chown():
    orden, c = _orden_de_init()
    montaje = [v for v in c["x-airflow-common"]["volumes"] if v.endswith(":ro")][0].rsplit(":", 2)[1]
    assert montaje == "/opt/airflow/medallon" and f"-path {montaje} -prune" in orden
    assert re.search(r'chown -v -R "\$\{AIRFLOW_UID:-50000\}:0" /opt/airflow/\{logs,dags,plugins,config\}', orden), "las cuatro carpetas compartidas deben conservar su chown"
    assert orden.count("-exec chown -h") == 1 and orden.index(PRUNE) < orden.index("chown -v -R")


def test_el_generador_lleva_el_reemplazo_y_el_aviso_y_el_diff_lo_muestran():
    g = _generador()
    assert (g.CHOWN_OFICIAL, g.CHOWN_NUEVO) in g.REEMPLAZOS and g.CHOWN_OFICIAL.count("chown -R") == 1 and PRUNE in g.CHOWN_NUEVO
    assert "DF-13 a DF-20" in g.AVISO and "find" in g.AVISO and "Read-only file system" in g.AVISO
    texto = COMPOSE.read_text(encoding="utf-8")
    assert "DF-13 a DF-20" in texto and "Read-only file system" in texto
    diff = (ROOT / "orquestacion" / "docker-compose.diff").read_text(encoding="utf-8")
    assert '-        chown -R "${AIRFLOW_UID:-50000}:0" /opt/airflow/' in diff and "+        " + PRUNE in diff


def test_el_compose_del_repositorio_es_exactamente_lo_que_sale_del_oficial_sin_necesitar_la_red():
    """Deshace cada reemplazo del generador sobre el compose adaptado: debe salir el texto oficial de Airflow 3.3.2 (su sha256 está en el generador) y volver a adaptarlo debe dar el mismo archivo."""
    g = _generador()
    adaptado = COMPOSE.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert adaptado.count("\n" + g.AVISO) == 1
    oficial = adaptado.replace("\n" + g.AVISO, "", 1)
    for ancla, nuevo in g.REEMPLAZOS:
        assert oficial.count(nuevo) == 1, nuevo[:60]
        oficial = oficial.replace(nuevo, ancla)
    assert g.sha256_texto(oficial) == g.SHA256_OFICIAL
    assert g.adaptar(oficial) == adaptado


def test_las_diferencias_con_la_guia_dicen_lo_mismo_que_el_compose():
    texto = (ROOT / "docs" / "orquestacion" / "diferencias_con_la_guia.md").read_text(encoding="utf-8")
    assert "(DF-13 a DF-20)" in texto and re.search(r"^\| DF-19 \|", texto, re.M)
    fila = [l for l in texto.splitlines() if l.startswith("| DF-19 |")][0]
    assert "Read-only file system" in fila and "-prune" in fila and "/opt/airflow/medallon" in fila and "logs" in fila


def test_el_comando_salta_de_verdad_el_montaje_y_cubre_el_resto(tmp_path):
    """Ejecuta el mismo `find … -prune -o -exec` (con `echo` en lugar de `chown`) sobre un árbol de mentira con el programa `bash` si el equipo lo tiene (Git para Windows lo trae); sin él no hay nada que ejecutar."""
    bash = shutil.which("bash")
    if bash is None:
        return
    raiz = tmp_path / "airflow"
    for rel in ("logs/a.log", "dags/d.py", "medallon/.venv/lib/x.py", "medallon/README.md"):
        (raiz / rel).parent.mkdir(parents=True, exist_ok=True)
        (raiz / rel).write_text("x", encoding="utf-8")
    base = raiz.as_posix()
    comando = f'find {base} -path {base}/medallon -prune -o -exec echo {{}} +'
    r = subprocess.run([bash, "-c", comando], capture_output=True, text=True, encoding="utf-8")
    rutas = set(r.stdout.split())
    assert r.returncode == 0 and f"{base}/logs/a.log" in rutas and f"{base}/dags/d.py" in rutas and base in rutas
    assert not any("/medallon" in p for p in rutas)
