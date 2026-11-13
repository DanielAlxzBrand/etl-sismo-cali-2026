"""Configura MySQL para el proyecto (lo ejecuta el equipo en su PC): crea las bases y el usuario `sismo_etl` y guarda sus credenciales en `.env`.

Uso (PowerShell, raíz del proyecto):  .\\.venv\\Scripts\\python.exe scripts\\mysql\\configurar_mysql.py [--rotar | --solo-verificar] [--usuario-admin root]
La contraseña del administrador se pide con getpass (sin eco): nunca por argumento, variable de entorno ni archivo; no se guarda ni se registra.
La contraseña de `sismo_etl` se genera con `secrets` y solo se escribe en `.env` (de forma atómica); el script imprime NOMBRES de variables, nunca valores.
Es idempotente: si el usuario ya existe y `.env` tiene credenciales válidas no cambia nada (ni pide la contraseña del administrador).
"""
import argparse
import getpass
import os
import re
import secrets
import string
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from dotenv import dotenv_values  # noqa: E402

from src.common import load_config  # noqa: E402
from src.logger import get_logger  # noqa: E402

log = get_logger(__name__)
USUARIO, HOST_USUARIO = "sismo_etl", "localhost"   # nunca '%': solo conexiones desde este equipo
PRIVILEGIOS = "SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, INDEX, REFERENCES"   # sin privilegios globales ni GRANT OPTION
LONGITUD_CLAVE = 32
NOMBRES_ENV = ("MYSQL_HOST", "MYSQL_PORT", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE", "MYSQL_DATABASE_PRUEBA")
ERRORES = {2003: "el servicio MySQL no responde en el puerto indicado (¿está activo el servicio MySQL80?)", 1045: "autenticación fallida (usuario o contraseña incorrectos)",
           1044: "permisos insuficientes para esta operación", 1227: "permisos insuficientes para esta operación", 1142: "permisos insuficientes para esta operación"}


class ConfiguracionError(Exception):
    """Error esperado con un mensaje claro para el equipo (nunca incluye contraseñas)."""


def generar_clave(n=LONGITUD_CLAVE):
    """Contraseña aleatoria fuerte (secrets): al menos una mayúscula, una minúscula, un dígito y un símbolo seguro para `.env` y SQL."""
    alfabeto = {"may": string.ascii_uppercase, "min": string.ascii_lowercase, "dig": string.digits, "sim": "_-.+="}
    while True:
        clave = "".join(secrets.choice("".join(alfabeto.values())) for _ in range(n))
        if all(any(c in grupo for c in clave) for grupo in alfabeto.values()):
            return clave


def clave_fuerte(clave):
    """True si la contraseña cumple la fortaleza exigida (longitud y las cuatro clases de caracteres)."""
    return len(clave) >= LONGITUD_CLAVE and all(any(f(c) for c in clave) for f in (str.isupper, str.islower, str.isdigit, lambda c: c in "_-.+="))


def actualizar_env(ruta, valores):
    """Actualiza o agrega variables en `.env` conservando las demás líneas; escribe un archivo temporal y lo reemplaza (atómico). No imprime valores."""
    ruta = Path(ruta)
    lineas = ruta.read_text(encoding="utf-8").splitlines() if ruta.exists() else []
    pendientes = dict(valores)
    salida = []
    for linea in lineas:
        m = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=", linea)
        if m and m.group(1) in pendientes:
            salida.append(f"{m.group(1)}={pendientes.pop(m.group(1))}")
        else:
            salida.append(linea)
    salida += [f"{k}={v}" for k, v in pendientes.items()]
    fd, tmp = tempfile.mkstemp(dir=ruta.parent, prefix=".env.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(salida) + "\n")
        os.replace(tmp, ruta)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def env_ignorado_y_no_versionado(raiz=ROOT):
    """True si git ignora `.env` y no lo versiona."""
    ign = subprocess.run(["git", "check-ignore", "-q", ".env"], cwd=raiz, capture_output=True).returncode == 0
    ver = subprocess.run(["git", "ls-files", "--error-unmatch", ".env"], cwd=raiz, capture_output=True).returncode != 0
    return ign and ver


def _consultar(conn, sql, params=()):
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        cur.close()


def _ejecutar(conn, sql, params=()):
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
    finally:
        cur.close()


def comprobar_servidor(admin):
    """Versión 8.0 o superior y juego de caracteres; informa lower_case_table_names (nombres en minúsculas: no depende de él)."""
    version = _consultar(admin, "SELECT VERSION()")[0][0]
    mayor, menor = (int(x) for x in re.match(r"(\d+)\.(\d+)", version).groups())
    if (mayor, menor) < (8, 0):
        raise ConfiguracionError(f"se necesita MySQL 8.0 o superior (hay {version})")
    lower = _consultar(admin, "SELECT @@lower_case_table_names")[0][0]
    charset = _consultar(admin, "SELECT @@character_set_server")[0][0]
    log.info("servidor MySQL %s; lower_case_table_names=%s; character_set_server=%s", version, lower, charset)
    return {"version": version, "lower_case_table_names": lower, "character_set_server": charset}


def aplicar(admin, bases, usuario_existe, clave):
    """Crea las bases y el usuario (o cambia su contraseña) y concede privilegios SOLO sobre las bases del proyecto. La contraseña va como parámetro."""
    for b in bases:   # los nombres de las bases son constantes del proyecto (config.yaml), no entrada del usuario
        _ejecutar(admin, f"CREATE DATABASE IF NOT EXISTS `{b}` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci")
    if usuario_existe:
        _ejecutar(admin, f"ALTER USER '{USUARIO}'@'{HOST_USUARIO}' IDENTIFIED BY %s", (clave,))
    else:
        _ejecutar(admin, f"CREATE USER '{USUARIO}'@'{HOST_USUARIO}' IDENTIFIED BY %s", (clave,))
    for b in bases:
        _ejecutar(admin, f"GRANT {PRIVILEGIOS} ON `{b}`.* TO '{USUARIO}'@'{HOST_USUARIO}'")


def verificar_privilegios(conn_usuario, bases):
    """SHOW GRANTS del usuario del proyecto: solo las dos bases, sin privilegios globales ni GRANT OPTION. Devuelve los permisos por base."""
    concesiones = [f[0] for f in _consultar(conn_usuario, "SHOW GRANTS FOR CURRENT_USER()")]
    if any("WITH GRANT OPTION" in g.upper() for g in concesiones):
        raise ConfiguracionError("el usuario del proyecto tiene GRANT OPTION")
    por_base = {}
    for g in concesiones:
        m = re.match(r"GRANT (.+?) ON (.+?) TO ", g, re.I)
        if not m:
            continue
        privilegios, objeto = m.group(1).strip(), m.group(2).replace("`", "").strip()
        if objeto == "*.*":
            if privilegios.upper() != "USAGE":
                raise ConfiguracionError("el usuario del proyecto tiene privilegios globales")
            continue
        por_base[objeto.split(".")[0]] = privilegios
    faltan = [b for b in bases if b not in por_base]
    sobran = [b for b in por_base if b not in bases]
    if faltan or sobran:
        raise ConfiguracionError(f"los privilegios no coinciden con las bases del proyecto (faltan {faltan}, sobran {sobran})")
    return por_base


def credenciales_validas(conectar_usuario, env, bases):
    """True si las credenciales de .env abren conexión y sus privilegios son los esperados (sin tocar nada)."""
    if not all(env.get(n) for n in ("MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE")) or env.get("MYSQL_USER") != USUARIO:
        return False
    conn = None
    try:
        conn = conectar_usuario(env["MYSQL_PASSWORD"], env["MYSQL_DATABASE"])
        verificar_privilegios(conn, bases)
        return True
    except Exception:  # noqa: BLE001 - cualquier fallo significa «no válidas»; el motivo no importa y puede traer datos de conexión
        return False
    finally:
        if conn is not None:
            conn.close()


def configurar(cfg, args, conectar_admin, conectar_usuario, pedir_clave=getpass.getpass, ruta_env=ROOT / ".env"):
    """Flujo completo; las funciones de conexión se inyectan para poder probarlo sin MySQL. Devuelve los NOMBRES de variables escritas."""
    al = cfg["almacenamiento"]
    bases = (al["base"], al["base_prueba"])
    env = dict(dotenv_values(ruta_env)) if Path(ruta_env).exists() else {}
    if not env_ignorado_y_no_versionado(Path(ruta_env).parent):
        raise ConfiguracionError(".env no está ignorado por git o está versionado; corrige .gitignore antes de guardar credenciales")
    validas = credenciales_validas(conectar_usuario, env, bases)
    if args.solo_verificar:
        if not validas:
            raise ConfiguracionError("las credenciales de .env no son válidas (ejecuta el script sin --solo-verificar)")
        log.info("verificación correcta: las credenciales de .env funcionan y los privilegios son los esperados")
        return []
    if validas and not args.rotar:
        log.info("sin cambios: el usuario ya existe y las credenciales de .env son válidas")
        return []
    clave_admin = pedir_clave(f"Contraseña del administrador de MySQL ({args.usuario_admin}); no se muestra al escribir: ")
    admin = None
    nueva = None
    try:
        admin = conectar_admin(args.usuario_admin, clave_admin)
        clave_admin = None   # fuera de memoria en cuanto se abre la conexión (mejor esfuerzo: las cadenas de Python son inmutables)
        comprobar_servidor(admin)
        existe = _consultar(admin, f"SELECT COUNT(*) FROM mysql.user WHERE user = %s AND host = '{HOST_USUARIO}'", (USUARIO,))[0][0] > 0
        nueva = generar_clave()
        aplicar(admin, bases, existe, nueva)
        conn = None
        try:
            conn = conectar_usuario(nueva, al["base"])
            verificar_privilegios(conn, bases)
        finally:
            if conn is not None:
                conn.close()
        valores = {"MYSQL_HOST": al["host"], "MYSQL_PORT": str(al["puerto"]), "MYSQL_USER": USUARIO, "MYSQL_PASSWORD": nueva, "MYSQL_DATABASE": al["base"], "MYSQL_DATABASE_PRUEBA": al["base_prueba"]}
        actualizar_env(ruta_env, valores)   # .env se escribe solo después de verificar la conexión del usuario
        return list(valores)
    finally:
        nueva = None
        clave_admin = None
        if admin is not None:
            admin.close()


def _conexiones(cfg):
    import pymysql
    al = cfg["almacenamiento"]
    base = {"host": al["host"], "port": int(al["puerto"]), "charset": "utf8mb4", "connect_timeout": int(al["tiempo_espera_s"]), "local_infile": False}

    def admin(usuario, clave):
        return pymysql.connect(user=usuario, password=clave, autocommit=True, **base)

    def usuario(clave, bd):
        return pymysql.connect(user=USUARIO, password=clave, database=bd, **base)
    return admin, usuario


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--usuario-admin", default="root")
    grupo = ap.add_mutually_exclusive_group()
    grupo.add_argument("--rotar", action="store_true", help="genera una contraseña nueva para sismo_etl y actualiza .env")
    grupo.add_argument("--solo-verificar", action="store_true", help="solo comprueba las credenciales de .env")
    args = ap.parse_args(argv)
    cfg = load_config()
    import pymysql
    admin, usuario = _conexiones(cfg)
    try:
        escritas = configurar(cfg, args, admin, usuario)
    except ConfiguracionError as e:
        log.error("%s", e)
        return 1
    except pymysql.err.Error as e:
        codigo = e.args[0] if e.args else 0
        log.error("MySQL: %s", ERRORES.get(codigo, f"error {codigo}"))
        return 1
    if escritas:
        log.info("variables escritas en .env: %s", ", ".join(escritas))
    log.info("Listo")
    return 0


if __name__ == "__main__":
    sys.exit(main())
