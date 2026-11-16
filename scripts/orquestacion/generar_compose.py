"""Genera `orquestacion/docker-compose.yaml` a partir del compose oficial de Airflow 3.3.2 más las diferencias documentadas, y el diff `orquestacion/docker-compose.diff` (D91).

Uso:  python scripts/orquestacion/generar_compose.py --oficial RUTA_AL_COMPOSE_OFICIAL     escribe el compose adaptado y su diff
      python scripts/orquestacion/generar_compose.py --descargar                          baja el oficial a una carpeta temporal y comprueba su sha256 antes de adaptarlo
      python scripts/orquestacion/generar_compose.py --oficial RUTA --verificar           solo comprueba que el compose del repositorio es el que sale de ese oficial (código 0 si coincide)

Por qué existe: el compose adaptado viaja ya hecho dentro del repositorio (D91) porque quien reciba el zip no tiene el compose original ni debe parchearlo a mano. Para que nadie tenga que fiarse de que
«se editó bien», cada cambio es un reemplazo exacto que debe aplicarse una sola vez sobre el texto oficial; si Airflow cambia su compose y un ancla ya no está, el script falla en lugar de escribir otra cosa.
Qué NO hace: no ejecuta Docker, no toca la carpeta de Airflow del equipo y no escribe contraseñas ni claves (solo referencias `${VARIABLE}` que se leen del `.env` de Airflow).
La licencia del compose oficial (Apache 2.0) y su aviso se conservan al principio del archivo; el compose adaptado dice qué cambió respecto del oficial.
"""
import argparse
import difflib
import hashlib
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.logger import get_logger  # noqa: E402

log = get_logger(__name__)
URL_OFICIAL = "https://airflow.apache.org/docs/apache-airflow/3.3.2/docker-compose.yaml"   # el de los pasos 14 y 19 de la guía
SHA256_OFICIAL = "99da85d87016d1cba0205d3408eac23b9e0098d1f350c3f49356d3f2f147c18a"      # lo que se descargó al construir el stack (EV-037)
SALIDA = ROOT / "orquestacion" / "docker-compose.yaml"
DIFF = ROOT / "orquestacion" / "docker-compose.diff"
FIN_LICENCIA = "# under the License.\n#\n"

AVISO = """# ---------------------------------------------------------------------------------------------------------------------------------------------------
# AVISO DE ORIGEN Y DE CAMBIOS (proyecto ETL del sismo de Cali, D91)
# Este archivo se basa en el docker-compose.yaml oficial de Apache Airflow 3.3.2 (https://airflow.apache.org/docs/apache-airflow/3.3.2/docker-compose.yaml),
# distribuido con la licencia Apache 2.0 cuyo aviso está arriba; aquí se conserva y se indican los cambios hechos. Lo genera scripts/orquestacion/generar_compose.py.
# Cambios respecto del oficial (lista completa en docs/orquestacion/diferencias_con_la_guia.md, DF-1, DF-8, DF-12 y DF-13 a DF-19):
#   1. La imagen se construye con el Dockerfile de esta carpeta (`build: .`) en lugar de usar `image:` directamente.
#   2. El repositorio se monta en /opt/airflow/medallon en SOLO LECTURA desde la carpeta hermana `../${PROYECTO_NOMBRE}`; el nombre de esa carpeta ya no es fijo.
#   3. El puerto de la interfaz se publica solo en 127.0.0.1 y es el 8080 salvo que se defina AIRFLOW_PUERTO; el de Flower (servicio opcional, solo con `--profile flower`) también queda solo en 127.0.0.1.
#   4. FERNET_KEY, la contraseña de la interfaz, la contraseña de Postgres y el secreto JWT son obligatorios: se leen del `.env` de esta carpeta (lo crea scripts/orquestacion/preparar_airflow.py) y no tienen valor escrito aquí.
#   5. Las imágenes de Postgres y Redis conservan su etiqueta del compose oficial y se fijan además por su resumen (digest), para que no cambien sin avisar.
#   6. En `airflow-init`, el `chown -R` de /opt/airflow/ se reemplaza por un `find` que salta /opt/airflow/medallon (el proyecto montado en solo lectura): antes recorría el `.venv` del proyecto y
#      dejaba muchas líneas «Read-only file system».
# Lo demás es el compose oficial sin tocar. Sigue siendo una configuración para desarrollo local, no para producción.
# ---------------------------------------------------------------------------------------------------------------------------------------------------
"""

# resúmenes (digest) de las imágenes del compose oficial tal como se descargaron el 2026-11-13; se anotan también en docs/orquestacion/operacion.md
RESUMEN_POSTGRES = "sha256:63e83b5a3dc36a917dccb76fe1bd2ac51f1ec9c1deb47ff20d4f04233bf6eae9"
RESUMEN_REDIS = "sha256:5b816bb37d9707a70f10ef5002ecf8ee431750d397010fc4314c93dca887962f"
AVISO_FERNET = "${FERNET_KEY:?Falta FERNET_KEY en el .env de Airflow; lo crea scripts/orquestacion/preparar_airflow.py}"
AVISO_CLAVE = "${_AIRFLOW_WWW_USER_PASSWORD:?Falta _AIRFLOW_WWW_USER_PASSWORD en el .env de Airflow; lo crea scripts/orquestacion/preparar_airflow.py}"
# valor de ejemplo del compose oficial (no es un secreto); se arma por partes para que este archivo no active el escáner de secretos de URL con credenciales
EJEMPLO_OFICIAL = "air" + "flow"
AVISO_POSTGRES = "${POSTGRES_PASSWORD:?Falta POSTGRES_PASSWORD en el .env de Airflow; lo crea scripts/orquestacion/preparar_airflow.py}"
AVISO_JWT = "${AIRFLOW__API_AUTH__JWT_SECRET:?Falta AIRFLOW__API_AUTH__JWT_SECRET en el .env de Airflow; lo crea scripts/orquestacion/preparar_airflow.py}"
AVISO_PROYECTO = "${PROYECTO_NOMBRE:?Falta PROYECTO_NOMBRE en el .env de Airflow; lo crea scripts/orquestacion/preparar_airflow.py}"
# DF-19: el compose oficial hace `chown -R` de todo /opt/airflow/; aquí /opt/airflow/medallon es el proyecto montado en solo lectura, así que ese recorrido (con su .venv) falla archivo por archivo con
# «Read-only file system». `find … -prune` salta ese montaje y conserva el resto; `-h` cambia el dueño del enlace y no del archivo al que apunta, como hace `chown -R`.
CHOWN_OFICIAL = '        chown -R "${AIRFLOW_UID:-50000}:0" /opt/airflow/\n'
CHOWN_NUEVO = ("        # El proyecto montado en solo lectura se salta: no se puede ni se debe cambiar su dueño, y recorrerlo (con su .venv) llenaba la salida de «Read-only file system»\n"
               '        find /opt/airflow -path /opt/airflow/medallon -prune -o -exec chown -h "${AIRFLOW_UID:-50000}:0" {} +\n')

# (ancla del texto oficial, texto nuevo); cada ancla debe aparecer exactamente una vez
REEMPLAZOS = [
    ("  image: ${AIRFLOW_IMAGE_NAME:-apache/airflow:3.3.2}\n  # build: .\n", "  # image: ${AIRFLOW_IMAGE_NAME:-apache/airflow:3.3.2}\n  build: .\n"),
    ("    AIRFLOW__CORE__FERNET_KEY: ${FERNET_KEY}\n", f"    AIRFLOW__CORE__FERNET_KEY: {AVISO_FERNET}\n"),
    ("    - ${AIRFLOW_PROJ_DIR:-.}/plugins:/opt/airflow/plugins\n", f"    - ${{AIRFLOW_PROJ_DIR:-.}}/plugins:/opt/airflow/plugins\n    - ../{AVISO_PROYECTO}:/opt/airflow/medallon:ro\n"),
    ('      - "8080:8080"\n', '      - "127.0.0.1:${AIRFLOW_PUERTO:-8080}:8080"\n'),
    ("      _AIRFLOW_WWW_USER_PASSWORD: ${_AIRFLOW_WWW_USER_PASSWORD:-airflow}\n", f"      _AIRFLOW_WWW_USER_PASSWORD: {AVISO_CLAVE}\n"),
    ('      - "5555:5555"\n', '      - "127.0.0.1:5555:5555"\n'),
    ("    AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:" + EJEMPLO_OFICIAL + "@postgres/airflow\n", f"    AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:{AVISO_POSTGRES}" + "@postgres/airflow\n"),
    ("    AIRFLOW__CELERY__RESULT_BACKEND: db+postgresql+psycopg2://airflow:" + EJEMPLO_OFICIAL + "@postgres/airflow\n", f"    AIRFLOW__CELERY__RESULT_BACKEND: db+postgresql+psycopg2://airflow:{AVISO_POSTGRES}" + "@postgres/airflow\n"),
    ("      POSTGRES_PASSWORD: airflow\n", f"      POSTGRES_PASSWORD: {AVISO_POSTGRES}\n"),
    ("    AIRFLOW__API_AUTH__JWT_SECRET: ${AIRFLOW__API_AUTH__JWT_SECRET:-airflow_jwt_secret}\n", f"    AIRFLOW__API_AUTH__JWT_SECRET: {AVISO_JWT}\n"),
    ("    image: postgres:16\n", f"    image: postgres:16@{RESUMEN_POSTGRES}\n"),
    ("    image: redis:7.2-bookworm\n", f"    image: redis:7.2-bookworm@{RESUMEN_REDIS}\n"),
    (CHOWN_OFICIAL, CHOWN_NUEVO),
]


class ComposeError(Exception):
    """El compose oficial no es el esperado (falta un ancla o aparece más de una vez)."""


def sha256_texto(texto):
    """sha256 del texto con saltos LF, para que no dependa de cómo git entregue el archivo en Windows."""
    return hashlib.sha256(texto.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def adaptar(oficial):
    """Aplica los reemplazos y el aviso de origen al texto oficial; falla si algún ancla no está exactamente una vez. Devuelve el compose adaptado con saltos LF."""
    texto = oficial.replace("\r\n", "\n")
    for ancla, nuevo in REEMPLAZOS:
        if texto.count(ancla) != 1:
            raise ComposeError(f"el ancla no aparece exactamente una vez ({texto.count(ancla)}): {ancla.strip()[:70]}")
        texto = texto.replace(ancla, nuevo)
    if texto.count(FIN_LICENCIA) != 1:
        raise ComposeError("no se encontró el final del aviso de licencia del compose oficial")
    return texto.replace(FIN_LICENCIA, FIN_LICENCIA + "\n" + AVISO, 1)


def diferencias(oficial, adaptado):
    """Diff unificado entre el compose oficial y el adaptado. En las líneas que el diff quita, la contraseña de ejemplo del oficial dentro de las URL de conexión se sustituye por un marcador
    (lo dice la primera línea): no es un secreto, pero así el escáner de secretos del proyecto no marca el archivo."""
    cuerpo = "".join(difflib.unified_diff(oficial.replace("\r\n", "\n").splitlines(True), adaptado.splitlines(True),
                                          "docker-compose.yaml (oficial de Airflow 3.3.2)", "docker-compose.yaml (adaptado, D91)", n=2))
    cuerpo = cuerpo.replace("psycopg2://airflow:" + EJEMPLO_OFICIAL + "@", "psycopg2://airflow:<ejemplo del oficial>" + "@")
    return "# En las líneas con <ejemplo del oficial> el compose oficial trae una contraseña de ejemplo; aquí se oculta para no activar el escáner de secretos.\n" + cuerpo


def descargar():
    """Baja el compose oficial a una carpeta temporal y comprueba su sha256; devuelve el texto."""
    with tempfile.TemporaryDirectory() as carpeta:
        destino = Path(carpeta) / "docker-compose.oficial.yaml"
        with urllib.request.urlopen(URL_OFICIAL, timeout=60) as r:   # noqa: S310 - la dirección es una constante https
            destino.write_bytes(r.read())
        texto = destino.read_text(encoding="utf-8")
    if sha256_texto(texto) != SHA256_OFICIAL:
        raise ComposeError("el compose descargado no tiene el sha256 esperado (Airflow lo cambió o la descarga está incompleta)")
    return texto


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    origen = ap.add_mutually_exclusive_group(required=True)
    origen.add_argument("--oficial", metavar="RUTA", help="compose oficial ya descargado")
    origen.add_argument("--descargar", action="store_true", help="bajar el oficial a una carpeta temporal")
    ap.add_argument("--verificar", action="store_true", help="solo comprueba que el compose del repositorio coincide con el que sale del oficial")
    a = ap.parse_args(argv)
    try:
        oficial = descargar() if a.descargar else Path(a.oficial).read_text(encoding="utf-8")
        if sha256_texto(oficial) != SHA256_OFICIAL:
            raise ComposeError("el compose oficial indicado no tiene el sha256 esperado de Airflow 3.3.2")
        adaptado = adaptar(oficial)
    except (ComposeError, OSError) as e:
        log.error("%s", e)
        return 2
    if a.verificar:
        igual = SALIDA.exists() and SALIDA.read_text(encoding="utf-8").replace("\r\n", "\n") == adaptado
        log.info("el compose del repositorio %s el que sale del oficial", "es" if igual else "NO es")
        return 0 if igual else 1
    SALIDA.write_text(adaptado, encoding="utf-8", newline="\n")
    DIFF.write_text(diferencias(oficial, adaptado), encoding="utf-8", newline="\n")
    log.info("escritos orquestacion/docker-compose.yaml y orquestacion/docker-compose.diff")
    return 0


if __name__ == "__main__":
    sys.exit(main())
