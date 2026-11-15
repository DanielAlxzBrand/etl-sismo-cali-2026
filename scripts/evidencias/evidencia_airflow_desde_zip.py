"""Airflow levantado como lo haría una persona que recibe el zip: carpetas temporales, proyecto de Docker propio y un puerto aparte.

Uso, desde la raíz del repositorio (con Docker Desktop encendido, las imágenes base ya descargadas y el `.env` del proyecto con las variables `MYSQL_DOCKER_*`):
    python scripts/evidencias/evidencia_airflow_desde_zip.py [--salida CARPETA] [--puerto 8082]

Qué hace: clona el commit actual, arma el zip con `make_dist.empaquetar` (nunca en `dist/`), lo descomprime en una carpeta temporal con un nombre distinto del real,
copia allí el `.env` del proyecto, corre `preparar_airflow.py` hacia otra carpeta temporal y construye y levanta Airflow con el proyecto de Docker `servicios_prueba`; espera la interfaz,
comprueba que el DAG `medallon_etl_sismo` aparezca sin errores de importación, lo dispara y espera sus cuatro tareas; comprueba que la carga diga «ya cargada», que MySQL siga con
las mismas corridas y que `data/` no haya cambiado. Escribe `resumen_airflow.json` (sin secretos) y `registro_airflow.txt` en `--salida` y, al terminar, baja y borra solo lo que creó.
Por qué es así: la persona que reciba el zip no tendrá la carpeta de Airflow ni su `.env`; esto prueba que `preparar_airflow.py` deja todo listo (D91 y D92, EV-087).
Qué NO hace: no toca el proyecto original ni su `data/`, no baja ningún otro proyecto de Docker (`down -v` solo del suyo) y no imprime valores del `.env`: los secretos se leen en
memoria y se reemplazan por «<oculto>» en todo lo que se escribe. Las carpetas temporales se borran, junto con los `.env` que se copiaron o generaron.
Última ejecución real: EV-087, con el script de la sesión del que sale este archivo; esta versión solo se validó de forma estática (Docker estaba apagado).
"""
import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[2]
PROYECTO_NOMBRE = "proyecto sismo de prueba"
NOMBRE_DOCKER = "servicios_prueba"
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"}
LOG = []
RES = {}
SECRETOS = []


def sh(cmd, cwd=None, timeout=1800):
    """Corre un comando y devuelve su resultado con la salida como texto."""
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV, timeout=timeout)


def limpiar(t):
    """Reemplaza cualquier secreto conocido por «<oculto>»."""
    for s in SECRETOS:
        t = t.replace(s, "<oculto>")
    return t


def paso(nombre, cmd, cwd=None, timeout=1800, ok=(0,)):
    """Corre un paso, anota su código y duración y su salida limpia en el registro; falla si el código no es el esperado."""
    t0 = time.perf_counter()
    r = sh(cmd, cwd=cwd, timeout=timeout)
    dt = time.perf_counter() - t0
    salida = limpiar((r.stdout or "") + (r.stderr or ""))
    LOG.append(f"## {nombre} (código {r.returncode}, {dt:.1f} s)\n$ {' '.join(map(str, cmd))[:200]}\n{salida[-3000:]}\n")
    RES[nombre] = {"codigo": r.returncode, "segundos": round(dt, 1)}
    if r.returncode not in ok:
        raise RuntimeError(f"falló {nombre}")
    return r, salida


def espera(nombre, fn, limite, cada=5):
    """Repite `fn` hasta que devuelva un valor verdadero o se acabe el tiempo."""
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < limite:
        try:
            v = fn()
            if v:
                RES[nombre] = {"segundos": round(time.perf_counter() - t0, 1)}
                LOG.append(f"## {nombre}: listo en {time.perf_counter() - t0:.1f} s\n")
                return v
        except Exception:  # noqa: BLE001
            pass
        time.sleep(cada)
    raise RuntimeError(f"tiempo agotado: {nombre}")


def huellas(carpeta):
    """{ruta relativa: sha256} de todos los archivos de una carpeta."""
    return {p.relative_to(carpeta).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(carpeta).rglob("*")) if p.is_file()}


def dc(*args):
    """Comando de Docker Compose con el proyecto de Docker propio de la prueba."""
    return ["docker", "compose", "-p", NOMBRE_DOCKER, *args]


def secretos_de(valores):
    """Valores del `.env` que parecen secretos (por el nombre de la variable); solo se guardan en memoria."""
    return [v for k, v in valores.items() if v and len(v) >= 6 and re.search("PASSWORD|TOKEN|SECRET|KEY", k, re.I)]


def json_de(salida):
    """Lista JSON que imprime la CLI de Airflow con `-o json`, o una lista vacía."""
    m = re.search(r"\[.*\]", salida, re.S)
    return json.loads(m.group(0)) if m else []


def armar(base, proyecto):
    """Clon del commit actual, zip con make_dist.empaquetar y proyecto descomprimido con el `.env` copiado."""
    paso("clonar", ["git", "clone", "--quiet", "--no-hardlinks", str(ROOT), str(base / "clon")])
    espec = importlib.util.spec_from_file_location("make_dist_del_clon", base / "clon" / "scripts" / "make_dist.py")
    md = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(md)
    t0 = time.perf_counter()
    ruta_zip, nombres = md.empaquetar(base / "clon", base / "zip")
    RES["zip"] = {"archivos": len(nombres), "mb": round(Path(ruta_zip).stat().st_size / 1048576, 1), "segundos": round(time.perf_counter() - t0, 1)}
    RES["zip_trae_servicios_y_compose"] = all(n in nombres for n in ("orquestacion/docker-compose.yaml", "servicios/phpmyadmin/docker-compose.yaml", "scripts/orquestacion/preparar_airflow.py"))
    RES["zip_sin_env"] = not any(n.split("/")[-1] == ".env" for n in nombres)
    with zipfile.ZipFile(ruta_zip) as z:
        z.extractall(proyecto)
    shutil.copy2(ROOT / ".env", proyecto / ".env")      # solo dentro de la carpeta temporal; se borra al final


def comprobar_el_dag(destino, puerto):
    """Dispara el DAG y espera su estado final; anota las tareas y lo que dice la carga."""
    def sano():
        return urllib.request.urlopen(f"http://127.0.0.1:{puerto}/api/v2/monitor/health", timeout=5).status == 200
    espera("interfaz_responde_salud", sano, 420)
    RES["interfaz_http"] = urllib.request.urlopen(f"http://127.0.0.1:{puerto}/", timeout=10).status

    def hay_dag():
        return "medallon_etl_sismo" in sh(dc("exec", "-T", "airflow-scheduler", "airflow", "dags", "list"), cwd=destino).stdout
    espera("dag_visible", hay_dag, 420)
    paso("dags_list", dc("exec", "-T", "airflow-scheduler", "airflow", "dags", "list"), cwd=destino)
    _, salida = paso("list_import_errors", dc("exec", "-T", "airflow-scheduler", "airflow", "dags", "list-import-errors"), cwd=destino)
    RES["sin_errores_de_importacion"] = "No data found" in salida
    paso("unpause", dc("exec", "-T", "airflow-scheduler", "airflow", "dags", "unpause", "medallon_etl_sismo"), cwd=destino)
    t0 = time.perf_counter()
    paso("trigger", dc("exec", "-T", "airflow-scheduler", "airflow", "dags", "trigger", "medallon_etl_sismo"), cwd=destino)

    def estado():
        corridas = json_de(sh(dc("exec", "-T", "airflow-scheduler", "airflow", "dags", "list-runs", "medallon_etl_sismo", "-o", "json"), cwd=destino).stdout)
        return next((c for c in corridas if c.get("state") in ("success", "failed")), None)
    corrida = espera("dag_termina", estado, 600, cada=6)
    RES["dag_estado"] = corrida["state"]
    RES["dag_segundos_desde_trigger"] = round(time.perf_counter() - t0, 1)
    r4 = sh(dc("exec", "-T", "airflow-scheduler", "airflow", "tasks", "states-for-dag-run", "medallon_etl_sismo", corrida["run_id"], "-o", "json"), cwd=destino)
    tareas = {t["task_id"]: t["state"] for t in json_de(r4.stdout)}
    RES["tareas"] = tareas
    LOG.append(f"## tareas\n{json.dumps(tareas, ensure_ascii=False)}\n")
    logs = "\n".join(limpiar(p.read_text(encoding="utf-8", errors="replace")) for p in (destino / "logs").rglob("*.log") if "cargar_datawarehouse" in p.as_posix())
    RES["carga_dice_ya_cargada"] = bool(re.search(r"ya cargada|ya_cargada", logs, re.I))


def comprobar_mysql_y_data(base, proyecto, antes_data):
    """MySQL sigue con las mismas corridas y `data/` no cambió (frente al del proyecto descomprimido y al del clon)."""
    import pymysql
    e = dotenv_values(ROOT / ".env")
    con = pymysql.connect(host=e["MYSQL_HOST"], port=int(e["MYSQL_PORT"]), user=e["MYSQL_USER"], password=e["MYSQL_PASSWORD"], database=e["MYSQL_DATABASE"])
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM corrida")
    RES["mysql_corridas"] = cur.fetchone()[0]
    con.close()
    despues_data = huellas(proyecto / "data")
    RES["data_archivos"] = len(despues_data)
    RES["data_sin_cambios"] = antes_data == despues_data
    RES["data_igual_al_clon"] = despues_data == huellas(base / "clon" / "data")


def main(argv=None):
    """Arma el zip, levanta Airflow, corre el DAG, comprueba y baja solo lo que creó."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--salida", type=Path, default=Path(tempfile.gettempdir()), help="carpeta del resumen y del registro")
    ap.add_argument("--puerto", type=int, default=8082, help="puerto local de la interfaz de Airflow")
    args = ap.parse_args(argv)
    args.salida.mkdir(parents=True, exist_ok=True)
    SECRETOS.extend(secretos_de(dotenv_values(ROOT / ".env")))
    base = Path(tempfile.mkdtemp(prefix="sismo_airflow_zip_"))
    destino, proyecto = base / "airflow-prueba", base / PROYECTO_NOMBRE
    creado = False
    try:
        armar(base, proyecto)
        antes_data = huellas(proyecto / "data")
        preparar = str(proyecto / "scripts" / "orquestacion" / "preparar_airflow.py")
        r, _ = paso("preparar_airflow", [sys.executable, preparar, "--destino", str(destino), "--puerto", str(args.puerto)], cwd=proyecto)
        envair = dotenv_values(destino / ".env")
        SECRETOS.extend(secretos_de(envair))
        RES["env_airflow_variables"] = sorted(envair)
        RES["proyecto_nombre_detectado"] = envair.get("PROYECTO_NOMBRE")
        RES["preparar_no_imprime_secretos"] = not any(s in (r.stdout + r.stderr) for s in SECRETOS)
        paso("verificar_preparacion", [sys.executable, preparar, "--destino", str(destino), "--verificar"], cwd=proyecto, ok=(0, 1))
        creado = True
        paso("compose_build", dc("build"), cwd=destino, timeout=2400)
        paso("compose_init", dc("up", "airflow-init"), cwd=destino, timeout=1200)
        paso("compose_up", dc("up", "-d"), cwd=destino, timeout=900)
        comprobar_el_dag(destino, args.puerto)
        comprobar_mysql_y_data(base, proyecto, antes_data)
    finally:
        if creado:
            try:
                paso("down", dc("down", "-v", "--rmi", "local", "--remove-orphans"), cwd=destino, timeout=600)
            except Exception as ex:  # noqa: BLE001
                LOG.append(f"## down falló: {ex}\n")
        for env in (proyecto / ".env", destino / ".env"):
            if env.exists():
                env.unlink()
        (args.salida / "registro_airflow.txt").write_text(limpiar("\n".join(LOG)), encoding="utf-8")
        RES["env_en_temporales"] = [p.as_posix() for p in base.rglob(".env")]
        shutil.rmtree(base, ignore_errors=True)
        (args.salida / "resumen_airflow.json").write_text(json.dumps({**RES, "carpeta_temporal_eliminada": not base.exists()}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(RES, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
