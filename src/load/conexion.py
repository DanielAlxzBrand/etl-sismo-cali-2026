"""Conexiones a la base relacional: MySQL desde variables de entorno (la contraseña solo viene de `.env`) y SQLite para pruebas."""
import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

from src.common import ROOT, load_config
from src.logger import get_logger

log = get_logger(__name__)
VARIABLES = ("MYSQL_HOST", "MYSQL_PORT", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE")


class ConexionError(Exception):
    """No se pudo abrir la conexión; el mensaje nunca incluye credenciales."""


def parametros(prueba=False):
    """Parámetros de conexión: valores no secretos de config.yaml, sobrescritos por MYSQL_* del entorno o de `.env`. Lanza ConexionError si falta la contraseña."""
    load_dotenv(ROOT / ".env")
    cfg = load_config()["almacenamiento"]
    base = os.getenv("MYSQL_DATABASE_PRUEBA") or cfg["base_prueba"] if prueba else os.getenv("MYSQL_DATABASE") or cfg["base"]
    p = {"host": os.getenv("MYSQL_HOST") or cfg["host"], "port": int(os.getenv("MYSQL_PORT") or cfg["puerto"]), "user": os.getenv("MYSQL_USER") or cfg["usuario"],
         "password": os.getenv("MYSQL_PASSWORD"), "database": base, "connect_timeout": int(cfg["tiempo_espera_s"])}
    if not p["password"]:
        raise ConexionError("falta la variable MYSQL_PASSWORD (se crea con scripts/mysql/configurar_mysql.py y vive solo en .env)")
    return p


def conectar_mysql(prueba=False, solo_lectura=False):
    """Conexión MySQL con utf8mb4, sin local_infile y sin confirmación automática. Con solo_lectura la sesión rechaza cualquier escritura."""
    import pymysql
    p = parametros(prueba)
    conn = None
    try:
        conn = pymysql.connect(host=p["host"], port=p["port"], user=p["user"], password=p["password"], database=p["database"], charset="utf8mb4",
                               connect_timeout=p["connect_timeout"], local_infile=False, autocommit=False)
        if solo_lectura:
            with conn.cursor() as cur:
                cur.execute("SET SESSION TRANSACTION READ ONLY")
        return conn
    except pymysql.err.OperationalError as e:
        if conn is not None:
            conn.close()
        codigo = e.args[0] if e.args else 0
        causas = {1045: "autenticación fallida (revisa MYSQL_USER y MYSQL_PASSWORD en .env)", 1049: f"la base {p['database']} no existe (ejecuta configurar_mysql.py)",
                  1044: f"el usuario {p['user']} no tiene permisos sobre {p['database']}", 2003: f"no hay un servidor MySQL en {p['host']}:{p['port']} (¿está activo el servicio MySQL80?)",
                  2013: "se perdió la conexión con el servidor", 2006: "el servidor cerró la conexión"}
        raise ConexionError(f"no se pudo conectar a MySQL: {causas.get(codigo, f'error {codigo}')}") from None
    except pymysql.err.Error as e:
        if conn is not None:
            conn.close()
        raise ConexionError(f"no se pudo conectar a MySQL (error {e.args[0] if e.args else '?'})") from None


def conectar_sqlite(ruta=":memory:", solo_lectura=False):
    """Conexión SQLite con claves foráneas activadas (lo hace cada conexión); con solo_lectura abre el archivo con `mode=ro`."""
    if solo_lectura and str(ruta) != ":memory:":
        conn = sqlite3.connect(f"{Path(ruta).resolve().as_uri()}?mode=ro", uri=True, check_same_thread=False)
    else:
        conn = sqlite3.connect(str(ruta), check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
