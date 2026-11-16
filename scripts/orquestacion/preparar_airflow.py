"""Prepara la carpeta de Airflow a partir del proyecto (por ejemplo, el descomprimido del zip) para levantar el DAG `medallon_etl_sismo` con Docker (D91).

Uso (PowerShell, raíz del proyecto):
  .\\.venv\\Scripts\\python.exe scripts\\orquestacion\\preparar_airflow.py [--destino CARPETA] [--puerto 8080] [--regenerar | --completar] [--nombre-compose NOMBRE]
  .\\.venv\\Scripts\\python.exe scripts\\orquestacion\\preparar_airflow.py --verificar          solo mira, no escribe nada (idempotente)

Qué hace: crea `dags`, `logs`, `plugins` y `config` en la carpeta de destino (por defecto `airflow-medallon`, hermana del proyecto), copia el compose adaptado, el Dockerfile y
`requirements-airflow.txt`, copia el DAG comprobando su sha256 contra `orquestacion/dag.sha256` y escribe el `.env` de Airflow SOLO si no existe, con cuatro secretos aleatorios (contraseña de la interfaz, FERNET_KEY, contraseña de Postgres y secreto JWT)
(más AIRFLOW_UID, PROYECTO_NOMBRE y AIRFLOW_PUERTO). Después imprime los comandos que siguen. El nombre de la carpeta del proyecto se detecta solo, porque el compose monta `../<nombre>` y ese nombre ya no es fijo.
Además avisa (con «!», sin fallar nunca por Docker apagado) si ya existe el volumen de Postgres del proyecto de Compose y es de otra instalación, y con `--nombre-compose NOMBRE` guarda COMPOSE_PROJECT_NAME (opcional,
fuera de las siete variables obligatorias) para que otro nombre de proyecto use otro volumen sin borrar el viejo.
Por qué es así: quien reciba el zip no tiene la carpeta de Airflow, ni el compose original, ni su `.env`; este script deja todo listo sin pedir que parchee nada a mano y sin que ningún valor secreto pase por la pantalla.
Qué NO hace: no ejecuta `docker compose`, no toca el `.env` del proyecto (solo comprueba, por nombre, las variables MYSQL_DOCKER_* que necesita la tarea de carga), no sobrescribe un `.env` existente sin `--regenerar`
(con `--completar` solo agrega las variables que falten, sin cambiar las que ya tiene) y no imprime nunca un valor del `.env`.
"""
import argparse
import base64
import os
import re
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dotenv import dotenv_values  # noqa: E402

import sincronizar_dag  # noqa: E402  (la lógica de la copia del DAG con su sha256 vive allí; aquí no se duplica)
from src.logger import get_logger  # noqa: E402

log = get_logger(__name__)
PUERTO_POR_DEFECTO = 8080
NOMBRES_ENV_AIRFLOW = ("AIRFLOW_UID", "_AIRFLOW_WWW_USER_PASSWORD", "FERNET_KEY", "POSTGRES_PASSWORD", "AIRFLOW__API_AUTH__JWT_SECRET", "PROYECTO_NOMBRE", "AIRFLOW_PUERTO")
NOMBRES_ENV_MYSQL_DOCKER = ("MYSQL_DOCKER_USER", "MYSQL_DOCKER_PASSWORD", "MYSQL_PORT", "MYSQL_DATABASE")   # las que lee la tarea de carga
ARCHIVOS = ("docker-compose.yaml", "Dockerfile", "requirements-airflow.txt")
CARPETAS = ("dags", "logs", "plugins", "config")
COMANDO_MYSQL = r".\.venv\Scripts\python.exe scripts\mysql\configurar_mysql.py --usuario-docker --origen localhost"   # D65: el contenedor llega a MySQL como localhost
# Opcional: NO es una de las siete variables obligatorias (NOMBRES_ENV_AIRFLOW, orquestacion/airflow-env.nombres.txt). Solo existe en el `.env` de Airflow si se pidió `--nombre-compose`; sin ella Compose usa el
# nombre de la carpeta de Airflow como nombre de proyecto y, por tanto, el mismo volumen de Postgres para cualquier zip que se descomprima junto a una carpeta con ese nombre.
NOMBRE_COMPOSE = "COMPOSE_PROJECT_NAME"
VOLUMEN_POSTGRES = "postgres-db-volume"       # el volumen que declara el compose; Compose le antepone «<proyecto>_»


class PrepararError(Exception):
    """Error esperado con un mensaje claro para el equipo (nunca incluye valores del `.env`)."""


def nombre_del_proyecto(raiz=ROOT):
    """Nombre de la carpeta del proyecto; el compose lo monta como `../<nombre>`, por eso ya no puede ser fijo."""
    return Path(raiz).resolve().name


def validar_nombre_compose(nombre):
    """Nombre de proyecto de Compose válido (minúsculas, dígitos, guion y guion bajo, y empieza con letra o dígito); si no, PrepararError antes de escribir nada."""
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", nombre or ""):
        raise PrepararError("el nombre de proyecto de Compose solo admite minúsculas, dígitos, guion y guion bajo, y debe empezar con una letra o un dígito (por ejemplo: airflow-zip)")
    return nombre


def nombre_compose_efectivo(destino, env=None):
    """Nombre de proyecto que usará Compose: el de COMPOSE_PROJECT_NAME en el `.env` de Airflow si existe; si no, el de la carpeta de Airflow en minúsculas y sin caracteres no admitidos."""
    fijado = dotenv_values(env).get(NOMBRE_COMPOSE) if env and Path(env).exists() else None
    return fijado or re.sub(r"[^a-z0-9_-]", "", Path(destino).resolve().name.lower())


def fecha_del_volumen(proyecto, ejecutar=subprocess.run):
    """Fecha de creación (con zona horaria) del volumen de Postgres del proyecto de Compose, o None si no existe, si Docker no responde o si la respuesta no es una fecha. Nunca lanza: apagado o no, Docker no
    debe romper una revisión de solo lectura."""
    try:
        r = ejecutar(["docker", "volume", "inspect", f"{proyecto}_{VOLUMEN_POSTGRES}", "--format", "{{.CreatedAt}}"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    try:
        fecha = datetime.fromisoformat((r.stdout or "").strip())
    except ValueError:
        return None
    return fecha if fecha.tzinfo else fecha.replace(tzinfo=timezone.utc)


def creacion_del_env(env):
    """Momento en que se creó el `.env` (en Windows, su fecha de creación; la de modificación de un archivo reemplazado es la misma)."""
    st = Path(env).stat()
    return datetime.fromtimestamp(getattr(st, "st_birthtime", st.st_ctime), tz=timezone.utc)


def aviso_de_volumen(proyecto, destino, ejecutar=subprocess.run, creacion_env=None):
    """Texto de aviso (o None) si ya existe el volumen de Postgres de ese proyecto de Compose y probablemente tiene la contraseña de OTRA instalación: o no hay `.env` de Airflow todavía (se creará uno con
    contraseña nueva) o el volumen es anterior al `.env` actual. Es lo que deja al apiserver «unhealthy» con «password authentication failed for user airflow». Solo informa: no borra nada."""
    fecha = fecha_del_volumen(proyecto, ejecutar)
    if fecha is None:
        return None
    env = Path(destino) / ".env"
    if env.exists():
        creado = creacion_env or creacion_del_env(env)
        if fecha >= creado:
            return None
        motivo = "es anterior al `.env` de Airflow actual"
    else:
        motivo = "se va a crear un `.env` nuevo con una contraseña de Postgres nueva"
    return (f"ya existe el volumen {proyecto}_{VOLUMEN_POSTGRES} (creado {fecha.astimezone().strftime('%Y-%m-%d %H:%M')}) y {motivo}: si es de otra instalación, el apiserver quedará «unhealthy» con "
            f"«password authentication failed for user airflow». Para empezar con una base nueva sin tocar ese volumen, repita con --nombre-compose <otro nombre>; borrarlo (docker compose down -v) elimina esa instalación de Airflow")


def puerto_libre(puerto, host="127.0.0.1"):
    """True si se puede escuchar en `host:puerto` (se prueba abriendo y cerrando un socket; no queda nada abierto)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, int(puerto)))
        except OSError:
            return False
    return True


def siguiente_puerto_libre(desde, comprobar=puerto_libre, intentos=50):
    """Primer puerto libre a partir de `desde` (para sugerirlo cuando el pedido está ocupado); None si no hay en `intentos` intentos."""
    return next((p for p in range(int(desde), int(desde) + intentos) if comprobar(p)), None)


def comprobar_docker(ejecutar=subprocess.run):
    """(ok, mensaje): Docker responde y tiene Compose. `ejecutar` se inyecta para poder probar los casos sin Docker."""
    try:
        servidor = ejecutar(["docker", "version", "--format", "{{.Server.Version}}"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    except (OSError, subprocess.SubprocessError):
        return False, "no se encontró Docker (instale Docker Desktop y vuelva a ejecutar)"
    if servidor.returncode != 0 or not (servidor.stdout or "").strip():
        return False, "Docker está instalado pero no responde (encienda Docker Desktop y espere a que diga que está en ejecución)"
    try:
        compose = ejecutar(["docker", "compose", "version", "--short"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    except (OSError, subprocess.SubprocessError):
        return False, "no se encontró «docker compose» (actualice Docker Desktop)"
    if compose.returncode != 0:
        return False, "no se encontró «docker compose» (actualice Docker Desktop)"
    return True, f"Docker {servidor.stdout.strip()} y Compose {compose.stdout.strip()}"


def _valor_seguro(valor):
    """Valor listo para `.env`: tal cual si solo trae caracteres que Compose no interpreta; entre comillas dobles (y con `$` duplicado) si trae espacios, comillas u otros."""
    if re.fullmatch(r"[A-Za-z0-9_.:/=+@-]*", valor):
        return valor
    return '"' + valor.replace("\\", "\\\\").replace('"', '\\"').replace("$", "$$") + '"'


def clave_fernet():
    """Clave Fernet válida (32 bytes aleatorios en base64 seguro para URL), sin depender de que `cryptography` esté instalada."""
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii")


def valores_nuevos(proyecto, puerto):
    """Variables del `.env` de Airflow con sus valores; las cuatro secretas (interfaz, Fernet, Postgres y JWT) son aleatorias y distintas. AIRFLOW_UID=50000 es el de la imagen oficial."""
    return {"AIRFLOW_UID": "50000", "_AIRFLOW_WWW_USER_PASSWORD": secrets.token_urlsafe(24), "FERNET_KEY": clave_fernet(), "POSTGRES_PASSWORD": secrets.token_urlsafe(24),
            "AIRFLOW__API_AUTH__JWT_SECRET": secrets.token_urlsafe(32), "PROYECTO_NOMBRE": proyecto, "AIRFLOW_PUERTO": str(puerto)}


def escribir_env(ruta, valores):
    """Escribe el `.env` de forma atómica (archivo temporal y reemplazo). No imprime nada."""
    ruta = Path(ruta)
    cuerpo = "".join(f"{k}={_valor_seguro(v)}\n" for k, v in valores.items())
    fd, tmp = tempfile.mkstemp(dir=ruta.parent, prefix=".env.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(cuerpo)
        os.replace(tmp, ruta)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def agregar_faltantes(ruta, valores):
    """Agrega al `.env` existente SOLO las variables de `valores` que no tiene (o tiene vacías); no cambia ninguna que ya tenga valor. Devuelve los NOMBRES agregados."""
    actuales = dotenv_values(ruta)
    faltan = {k: v for k, v in valores.items() if not actuales.get(k)}
    if faltan:
        texto = Path(ruta).read_text(encoding="utf-8")
        lineas = [l for l in texto.splitlines() if not re.match(r"\s*(" + "|".join(re.escape(k) for k in faltan) + r")\s*=\s*$", l)]
        lineas += [f"{k}={_valor_seguro(v)}" for k, v in faltan.items()]
        fd, tmp = tempfile.mkstemp(dir=Path(ruta).parent, prefix=".env.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
                f.write("\n".join(lineas) + "\n")
            os.replace(tmp, ruta)
        except BaseException:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise
    return list(faltan)


def fijar_variable(ruta, nombre, valor):
    """Pone `nombre=valor` en el `.env` existente (reemplaza esa línea o la agrega al final) sin tocar ninguna otra variable; escritura atómica y sin imprimir nada."""
    texto = Path(ruta).read_text(encoding="utf-8")
    lineas = [l for l in texto.splitlines() if not re.match(r"\s*" + re.escape(nombre) + r"\s*=", l)]
    lineas.append(f"{nombre}={_valor_seguro(valor)}")
    fd, tmp = tempfile.mkstemp(dir=Path(ruta).parent, prefix=".env.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lineas) + "\n")
        os.replace(tmp, ruta)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def variables_que_faltan(ruta, nombres):
    """NOMBRES de `nombres` que no están o están vacías en el archivo `.env` (vacío si el archivo no existe: faltan todas)."""
    valores = dotenv_values(ruta) if Path(ruta).exists() else {}
    return [n for n in nombres if not valores.get(n)]


def comprobar_destino(destino, raiz):
    """El compose monta `../<proyecto>`: la carpeta de Airflow debe estar junto al proyecto, o el montaje apuntaría a otro lado."""
    if Path(destino).resolve().parent != Path(raiz).resolve().parent:
        raise PrepararError("la carpeta de Airflow debe ser hermana de la del proyecto (el compose monta ../<proyecto>); elija un --destino junto a ella")
    if Path(destino).resolve() == Path(raiz).resolve():
        raise PrepararError("la carpeta de Airflow no puede ser la del proyecto")


def preparar(raiz, destino, puerto, regenerar=False, completar=False, ejecutar=subprocess.run, comprobar_puerto=None, nombre_compose=None, creacion_env=None):
    """Crea o actualiza la carpeta de Airflow. Devuelve un diccionario con lo hecho (solo nombres y textos, nunca valores del `.env`). Falla con PrepararError antes de escribir nada si Docker no responde,
    el puerto está ocupado, el destino no es una carpeta hermana o el nombre de Compose no es válido. El `.env` de Airflow se escribe solo si no existe (o con `regenerar`); con `completar` agrega las variables que falten.
    Con `nombre_compose` se guarda además COMPOSE_PROJECT_NAME (opcional, fuera de las siete obligatorias) y `regenerar` conserva el que ya tenía. Si ya existe un volumen de Postgres de otra instalación, lo avisa en `avisos`."""
    raiz, destino = Path(raiz).resolve(), Path(destino).resolve()
    if nombre_compose is not None:
        validar_nombre_compose(nombre_compose)
    comprobar_puerto = comprobar_puerto or puerto_libre        # se resuelve al llamar (no al definir) para que una prueba pueda sustituirlo
    comprobar_destino(destino, raiz)
    ok, mensaje_docker = comprobar_docker(ejecutar)
    if not ok:
        raise PrepararError(mensaje_docker)
    if not comprobar_puerto(puerto):
        sugerido = siguiente_puerto_libre(int(puerto) + 1, comprobar_puerto)
        raise PrepararError(f"el puerto {puerto} está ocupado" + (f"; pruebe con --puerto {sugerido}" if sugerido else "; indique otro con --puerto"))
    dag_repo, dag_vivo = raiz / "dags" / sincronizar_dag.NOMBRE, destino / "dags" / sincronizar_dag.NOMBRE
    registro = raiz / "orquestacion" / "dag.sha256"
    if not dag_repo.exists() or not registro.exists():
        raise PrepararError("faltan dags/medallon_etl_dag.py o orquestacion/dag.sha256 en el proyecto")
    if sincronizar_dag.sha256(dag_repo) != registro.read_text(encoding="utf-8").split()[0]:
        raise PrepararError("el DAG del proyecto no coincide con el sha256 registrado en orquestacion/dag.sha256")
    for nombre in ARCHIVOS:
        if not (raiz / "orquestacion" / nombre).exists():
            raise PrepararError(f"falta orquestacion/{nombre} en el proyecto")
    hecho = {"creadas": [], "copiados": [], "env": "sin cambios", "agregadas": [], "avisos": []}
    destino.mkdir(exist_ok=True)
    for carpeta in CARPETAS:
        if not (destino / carpeta).is_dir():
            (destino / carpeta).mkdir()
            hecho["creadas"].append(carpeta)
    for nombre in ARCHIVOS:
        shutil.copy2(raiz / "orquestacion" / nombre, destino / nombre)
        hecho["copiados"].append(nombre)
    sincronizar_dag.sincronizar(dag_repo, dag_vivo)          # la misma copia que usa sincronizar_dag.py
    if sincronizar_dag.sha256(dag_vivo) != sincronizar_dag.sha256(dag_repo):
        raise PrepararError("el DAG copiado no coincide con el del proyecto")
    hecho["copiados"].append("dags/" + sincronizar_dag.NOMBRE)
    env = destino / ".env"
    nuevos = valores_nuevos(nombre_del_proyecto(raiz), puerto)
    existia = env.exists()
    previo = dotenv_values(env).get(NOMBRE_COMPOSE) if existia else None     # con --regenerar no se pierde: cambiaría el nombre del volumen sin que nadie lo pida
    if not existia or regenerar:
        a_escribir = dict(nuevos)
        if nombre_compose or previo:
            a_escribir[NOMBRE_COMPOSE] = nombre_compose or previo
        escribir_env(env, a_escribir)
        hecho["env"] = "regenerado con valores nuevos" if existia else "creado"
    else:
        if completar:
            hecho["agregadas"] = agregar_faltantes(env, nuevos)
            hecho["env"] = "completado" if hecho["agregadas"] else "sin cambios"
        if nombre_compose and nombre_compose != previo:
            fijar_variable(env, NOMBRE_COMPOSE, nombre_compose)
            hecho["env"] = hecho["env"] + (" y " if hecho["env"] != "sin cambios" else " salvo ") + NOMBRE_COMPOSE
    hecho["nombre_compose"] = nombre_compose_efectivo(destino, env)
    hecho["compose_fijado"] = bool(dotenv_values(env).get(NOMBRE_COMPOSE))
    if existia and not regenerar:
        # el `.env` existente manda: se avisa (con valores que no son secretos) si ya no coincide con lo pedido
        actuales = dotenv_values(env)
        for nombre, pedido in (("PROYECTO_NOMBRE", nuevos["PROYECTO_NOMBRE"]), ("AIRFLOW_PUERTO", nuevos["AIRFLOW_PUERTO"])):
            if actuales.get(nombre) and actuales[nombre] != pedido:
                hecho["avisos"].append(f"el `.env` existente tiene {nombre}={actuales[nombre]}, distinto de lo pedido ({pedido}); no se cambió (use --regenerar o edite esa variable)")
    aviso = aviso_de_volumen(hecho["nombre_compose"], destino, ejecutar, creacion_env)
    if aviso:
        hecho["avisos"].append(aviso)
    hecho["faltan_en_env"] = variables_que_faltan(env, NOMBRES_ENV_AIRFLOW)
    hecho["faltan_mysql"] = variables_que_faltan(raiz / ".env", NOMBRES_ENV_MYSQL_DOCKER)
    hecho["docker"] = mensaje_docker
    return hecho


def verificar(raiz, destino, ejecutar=subprocess.run, comprobar_puerto=None):
    """Revisión de solo lectura: lista de (ok, texto) con el estado de cada pieza. No escribe nada y se puede repetir."""
    raiz, destino = Path(raiz).resolve(), Path(destino).resolve()
    comprobar_puerto = comprobar_puerto or puerto_libre
    filas = []
    try:
        comprobar_destino(destino, raiz)
        filas.append((True, "la carpeta de Airflow es hermana del proyecto"))
    except PrepararError as e:
        filas.append((False, str(e)))
    faltan = [c for c in CARPETAS if not (destino / c).is_dir()]
    filas.append((not faltan, "carpetas dags, logs, plugins y config presentes" if not faltan else "faltan las carpetas " + ", ".join(faltan)))
    distintos = [n for n in ARCHIVOS if not (destino / n).exists() or not (raiz / "orquestacion" / n).exists()
                 or (destino / n).read_bytes().replace(b"\r\n", b"\n") != (raiz / "orquestacion" / n).read_bytes().replace(b"\r\n", b"\n")]
    filas.append((not distintos, "compose, Dockerfile y requisitos iguales a los del proyecto" if not distintos else "distintos o ausentes: " + ", ".join(distintos)))
    dag_repo, dag_vivo = raiz / "dags" / sincronizar_dag.NOMBRE, destino / "dags" / sincronizar_dag.NOMBRE
    igual = dag_repo.exists() and dag_vivo.exists() and sincronizar_dag.sha256(dag_repo) == sincronizar_dag.sha256(dag_vivo)
    filas.append((igual, "DAG igual al del proyecto (sha256)" if igual else "el DAG de la carpeta de Airflow falta o es distinto del del proyecto"))
    env = destino / ".env"
    falta = variables_que_faltan(env, NOMBRES_ENV_AIRFLOW)
    filas.append((not falta, f"`.env` de Airflow con sus {len(NOMBRES_ENV_AIRFLOW)} variables" if not falta else "al `.env` de Airflow le faltan: " + ", ".join(falta) + " (use --completar)"))
    if env.exists():
        proyecto = dotenv_values(env).get("PROYECTO_NOMBRE")
        coincide = proyecto == nombre_del_proyecto(raiz)
        filas.append((coincide, "PROYECTO_NOMBRE coincide con la carpeta del proyecto" if coincide else "PROYECTO_NOMBRE no coincide con la carpeta del proyecto (¿la renombró? use --regenerar o edite esa variable)"))
    fijado = bool(dotenv_values(env).get(NOMBRE_COMPOSE)) if env.exists() else False
    compose = nombre_compose_efectivo(destino, env)
    filas.append((True, f"nombre de proyecto de Compose: {compose} ({'guardado en el `.env` de Airflow' if fijado else 'el de la carpeta de Airflow, por defecto'})"))
    falta_mysql = variables_que_faltan(raiz / ".env", NOMBRES_ENV_MYSQL_DOCKER)
    filas.append((not falta_mysql, "`.env` del proyecto con las variables MYSQL_DOCKER_* de la carga" if not falta_mysql
                  else "al `.env` del proyecto le faltan: " + ", ".join(falta_mysql) + f"; las crea: {COMANDO_MYSQL}"))
    ok, mensaje = comprobar_docker(ejecutar)
    filas.append((ok, mensaje))
    if ok:      # con Docker apagado no hay nada que preguntar (y no se convierte en un error): la fila de arriba ya lo dice
        aviso = aviso_de_volumen(compose, destino, ejecutar)
        if aviso:
            filas.append((None, aviso))      # None = «aviso»: no es un error y no cambia el código de salida
    puerto = (dotenv_values(env).get("AIRFLOW_PUERTO") if env.exists() else None) or str(PUERTO_POR_DEFECTO)
    libre = comprobar_puerto(int(puerto)) if puerto.isdigit() else False
    filas.append((True, f"puerto {puerto} libre" if libre else f"puerto {puerto} ocupado (si Airflow ya está encendido es lo esperado)"))
    return filas


def comandos_siguientes(destino, puerto):
    """Texto con los comandos que siguen, en PowerShell; sin ningún valor del `.env`."""
    return "\n".join([
        "Siguientes pasos (PowerShell):",
        f'  cd "{destino}"',
        "  docker compose build",
        "  docker compose up airflow-init",
        "  docker compose up -d",
        f"Interfaz: http://127.0.0.1:{puerto} · usuario: airflow · contraseña: la variable _AIRFLOW_WWW_USER_PASSWORD de {Path(destino).name}\\.env (no se imprime aquí)",
        "Activar y disparar el DAG:  docker compose exec airflow-scheduler airflow dags unpause medallon_etl_sismo",
        "Para apagar:  docker compose down",
    ])


def _salida_tolerante():
    """Las marcas ✓ y ✗ no existen en la codificación predeterminada de una consola de Windows (cp1252) cuando la salida se redirige: se reemplazan por «?» en lugar de caer con UnicodeEncodeError."""
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(errors="replace")


def main(argv=None):
    _salida_tolerante()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--destino", default=None, help="carpeta de Airflow (por defecto, airflow-medallon junto al proyecto)")
    ap.add_argument("--puerto", type=int, default=PUERTO_POR_DEFECTO, help="puerto de la interfaz en 127.0.0.1 (por defecto 8080)")
    grupo = ap.add_mutually_exclusive_group()
    grupo.add_argument("--regenerar", action="store_true", help="vuelve a escribir el `.env` de Airflow con valores nuevos (sobrescribe el existente)")
    grupo.add_argument("--completar", action="store_true", help="agrega al `.env` existente solo las variables que le falten")
    grupo.add_argument("--verificar", action="store_true", help="solo comprueba el estado, sin escribir nada")
    ap.add_argument("--nombre-compose", default=None, metavar="NOMBRE",
                    help="guarda COMPOSE_PROJECT_NAME en el `.env` de Airflow (opcional): con otro nombre Compose usa otro volumen de Postgres y no choca con el de otra instalación; sin esta opción nada cambia")
    a = ap.parse_args(argv)
    if a.verificar and a.nombre_compose:
        ap.error("--nombre-compose escribe en el `.env` de Airflow y no se usa con --verificar")
    destino = Path(a.destino) if a.destino else ROOT.parent / "airflow-medallon"
    if a.verificar:
        filas = verificar(ROOT, destino, ejecutar=subprocess.run)      # se resuelve al llamar: una prueba puede sustituir `subprocess.run`
        for ok, texto in filas:
            print(("✓ " if ok else "! " if ok is None else "✗ ") + texto)
        return 0 if all(ok is not False for ok, _ in filas) else 1
    try:
        hecho = preparar(ROOT, destino, a.puerto, regenerar=a.regenerar, completar=a.completar, nombre_compose=a.nombre_compose, ejecutar=subprocess.run)
    except PrepararError as e:
        log.error("%s", e)
        return 2
    print(f"✓ {hecho['docker']}")
    print(f"✓ carpetas creadas: {', '.join(hecho['creadas']) or 'ninguna (ya existían)'}; copiados: {', '.join(hecho['copiados'])}")
    print(f"✓ `.env` de Airflow: {hecho['env']}" + (f" (agregadas: {', '.join(hecho['agregadas'])})" if hecho["agregadas"] else ""))
    print(f"✓ nombre de proyecto de Compose: {hecho['nombre_compose']} ({'guardado en el `.env` de Airflow' if hecho['compose_fijado'] else 'el de la carpeta de Airflow, por defecto'})")
    for aviso in hecho["avisos"]:
        print("! " + aviso)
    if hecho["faltan_en_env"]:
        print("✗ al `.env` de Airflow le faltan: " + ", ".join(hecho["faltan_en_env"]) + " (ejecute de nuevo con --completar)")
    if hecho["faltan_mysql"]:
        print("✗ al `.env` del proyecto le faltan: " + ", ".join(hecho["faltan_mysql"]) + f"; las crea (con su contraseña de administrador, tecleada por usted):\n  {COMANDO_MYSQL}")
    print(comandos_siguientes(destino, a.puerto))
    return 0 if not hecho["faltan_en_env"] else 1


if __name__ == "__main__":
    sys.exit(main())
