"""DAG medallon_etl_sismo: Bronze -> Silver -> Gold -> Carga (SQLite y MySQL) del ETL del sismo de Cali.

Procedimiento basado en la guía de Airflow de la asignatura (artículo de Juan Manuel Núñez Velasco); las diferencias con la guía están en docs/orquestacion/diferencias_con_la_guia.md.
El repositorio se monta en solo lectura en /opt/airflow/medallon y NUNCA se escribe: validar_bronze crea una copia de trabajo mínima en el contenedor, las demás tareas
producen sus salidas allí y las comparan con los archivos versionados del repositorio. `src` se importa solo dentro de las tareas y desde la copia.
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from airflow.sdk import DAG, get_current_context, task

PROJECT_DIR = Path("/opt/airflow/medallon")
BASE_TRABAJO = Path(tempfile.gettempdir())   # fuera del volumen del repositorio
SILVER = ["data/silver/silver_construcciones.csv", "data/silver/silver_estrato_barrio.csv", "data/silver/silver_integrated.csv",
          "data/silver/silver_orphans_left.csv", "data/silver/silver_orphans_right.csv", "data/silver/quality_report.json"]
GOLD = ["data/gold/gold_final.csv", "data/gold/kpis_gold.csv", "data/gold/kpis_sensibilidad.csv"]
TABLAS_SQLITE = ["silver_integrated", "gold_final", "kpis_gold", "kpis_sensibilidad"]
HOST_DOCKER = "host.docker.internal"   # origen de la conexión a MySQL desde el contenedor


def _sha256(ruta):
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def _trabajo(run_id):
    """Carpeta única por ejecución dentro del contenedor (no es el volumen del repositorio)."""
    return BASE_TRABAJO / ("medallon_" + re.sub(r"[^A-Za-z0-9]+", "_", run_id))


def _contexto():
    c = get_current_context()
    return c["run_id"], (c["dag_run"].conf or {})


def _fallo_inducido(nombre, conf):
    """Único complemento funcional: con {"fallo_inducido": "<tarea>"} esa tarea falla ANTES de producir salidas."""
    if conf.get("fallo_inducido") == nombre:
        raise RuntimeError(f"Fallo inducido en la tarea {nombre} (parámetro fallo_inducido)")


def _copiar_trabajo(destino):
    """Copia de trabajo mínima: src, config, data y docs/silver/hallazgos_eda.md (entrada de transformar). Sin .env, .venv, .git, dist, logs ni cachés."""
    ignorar = shutil.ignore_patterns("__pycache__", "*.pyc")
    for carpeta in ("src", "config", "data"):
        shutil.copytree(PROJECT_DIR / carpeta, destino / carpeta, ignore=ignorar)
    (destino / "docs" / "silver").mkdir(parents=True)
    shutil.copy2(PROJECT_DIR / "docs" / "silver" / "hallazgos_eda.md", destino / "docs" / "silver" / "hallazgos_eda.md")


def _comparar_con_repo(trabajo, rutas):
    """Compara byte a byte (sha256) lo producido en la copia con el archivo versionado del repositorio; falla si difiere."""
    distintos = [r for r in rutas if _sha256(trabajo / r) != _sha256(PROJECT_DIR / r)]
    if distintos:
        raise RuntimeError("Salida distinta de la versionada: " + ", ".join(distintos))
    print(f"Coinciden con el repositorio {len(rutas)} archivos (sha256)")


def _huella_tablas(ruta_db):
    """Contenido de cada tabla ordenado y resumido: la base SQLite no es idéntica byte a byte entre ejecuciones, su contenido sí."""
    conn = None
    try:
        conn = sqlite3.connect(f"{Path(ruta_db).as_uri()}?mode=ro", uri=True)
        huellas = {}
        for tabla in TABLAS_SQLITE:
            columnas = [c[1] for c in conn.execute(f"PRAGMA table_info({tabla})")]
            h = hashlib.sha256()
            for fila in conn.execute(f"SELECT * FROM {tabla} ORDER BY {', '.join(columnas)}"):
                h.update(repr(fila).encode("utf-8"))
            huellas[tabla] = h.hexdigest()
        return huellas
    finally:
        if conn is not None:
            conn.close()


def _credenciales_docker():
    """Credenciales del usuario de MySQL para Docker: se leen EN MEMORIA del .env del proyecto montado y solo viajan por os.environ de la tarea."""
    from dotenv import dotenv_values
    v = dotenv_values(PROJECT_DIR / ".env")
    nombres = ("MYSQL_DOCKER_USER", "MYSQL_DOCKER_PASSWORD", "MYSQL_PORT", "MYSQL_DATABASE")
    faltan = [n for n in nombres if not v.get(n)]
    if faltan:
        raise RuntimeError("Faltan variables en el .env del proyecto: " + ", ".join(faltan))
    return {"MYSQL_HOST": HOST_DOCKER, "MYSQL_PORT": v["MYSQL_PORT"], "MYSQL_USER": v["MYSQL_DOCKER_USER"], "MYSQL_PASSWORD": v["MYSQL_DOCKER_PASSWORD"], "MYSQL_DATABASE": v["MYSQL_DATABASE"]}


with DAG(
    dag_id="medallon_etl_sismo",
    description="Pipeline ETL Medallion: Bronze -> Silver -> Gold -> Load",
    start_date=datetime(2026, 1, 1, tzinfo=ZoneInfo("America/Bogota")),
    schedule=None,
    catchup=False,
    tags=["etl", "medallion", "sismo"],
) as dag:

    @task
    def validar_bronze():
        print("Validando capa Bronze...")
        run_id, conf = _contexto()
        _fallo_inducido("validar_bronze", conf)
        trabajo = _trabajo(run_id)
        try:
            if trabajo.exists():
                shutil.rmtree(trabajo)
            _copiar_trabajo(trabajo)
            # src se importa desde la copia (ROOT del pipeline = copia) y la validación usa el manifiesto con sha256: no descarga nada
            if _sha256(trabajo / "data/bronze/manifest.jsonl") != _sha256(PROJECT_DIR / "data/bronze/manifest.jsonl"):
                raise RuntimeError("El manifiesto de la copia difiere del del repositorio")
            sys.path.insert(0, str(trabajo))
            from src.common import read_manifest, verify_files
            manifiesto = read_manifest()
            if len(manifiesto) != 8 or not verify_files(manifiesto):
                raise RuntimeError("Bronze no coincide con el manifiesto (8 líneas con sha256)")
        except Exception:
            shutil.rmtree(trabajo, ignore_errors=True)
            raise
        print(f"Bronze validado correctamente: {len(manifiesto)} archivos con sha256 que coincide")
        print(f"Copia de trabajo creada: {trabajo.name}")

    @task
    def transformar_a_silver():
        print("Transformando Bronze hacia Silver...")
        run_id, conf = _contexto()
        trabajo = _trabajo(run_id)
        try:
            _fallo_inducido("transformar_a_silver", conf)   # dentro del try: si falla, la copia de trabajo también se elimina
            sys.path.insert(0, str(trabajo))
            from src.transform.integrate import run_transform
            run_transform()
            _comparar_con_repo(trabajo, SILVER)
        except Exception:
            shutil.rmtree(trabajo, ignore_errors=True)
            raise
        print("Silver generado correctamente")

    @task
    def integrar_a_gold():
        print("Construyendo capa Gold...")
        run_id, conf = _contexto()
        trabajo = _trabajo(run_id)
        try:
            _fallo_inducido("integrar_a_gold", conf)   # dentro del try: si falla, la copia de trabajo también se elimina
            sys.path.insert(0, str(trabajo))
            from src.transform.build_gold import run_gold
            run_gold()
            _comparar_con_repo(trabajo, GOLD)
        except Exception:
            shutil.rmtree(trabajo, ignore_errors=True)
            raise
        print("Gold generado correctamente")

    @task
    def cargar_datawarehouse():
        print("Iniciando carga...")
        run_id, conf = _contexto()
        trabajo = _trabajo(run_id)
        try:
            _fallo_inducido("cargar_datawarehouse", conf)
            sys.path.insert(0, str(trabajo))
            from src.load.load_database import load_to_sqlite
            load_to_sqlite()
            if _huella_tablas(trabajo / "data/gold/etl_sismo.db") != _huella_tablas(PROJECT_DIR / "data/gold/etl_sismo.db"):
                raise RuntimeError("El contenido de etl_sismo.db difiere del versionado")
            print(f"SQLite cargada: {len(TABLAS_SQLITE)} tablas con el mismo contenido que el repositorio")
            from src.load import conexion, relacional
            os.environ.update(_credenciales_docker())
            conn = None
            try:
                conn = conexion.conectar_mysql()
                resultado = relacional.cargar(conn, "mysql")   # idempotente: la misma entrada responde ya_cargada y no escribe
            finally:
                if conn is not None:
                    conn.close()
            print(f"Carga relacional: {resultado['estado']} (corrida {resultado['corrida_id']}), filas {resultado['filas']}")
        finally:
            shutil.rmtree(trabajo, ignore_errors=True)
        print("Carga terminada")

    bronze = validar_bronze()
    silver = transformar_a_silver()
    gold = integrar_a_gold()
    load = cargar_datawarehouse()

    bronze >> silver >> gold >> load
