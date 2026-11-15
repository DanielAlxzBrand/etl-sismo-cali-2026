"""Diagnóstico del entorno para ejecutar el proyecto en un equipo nuevo; con `--instalar` crea el entorno virtual de Python 3.13 e instala `requirements.txt` (D93).

Uso (PowerShell, raíz del proyecto):
  py -3.13 scripts\\preparar_entorno.py                      diagnóstico de solo lectura, modo mínimo (pipeline, API y panel con SQLite)
  py -3.13 scripts\\preparar_entorno.py --modo completo      además MySQL, Docker y los puertos de Airflow y phpMyAdmin
  py -3.13 scripts\\preparar_entorno.py --instalar           crea `.venv` con `py -3.13` e instala `requirements.txt`, pidiendo confirmación antes

Qué hace: por cada cosa que el proyecto necesita imprime ✓ o ✗ y, si falta, la acción exacta que sugerimos: Python 3.13 (se busca con `py -0p`, porque se instala en paralelo aunque el equipo tenga una versión
más nueva), el entorno virtual, los requisitos instalados con las versiones exactas (`pip check` y `requirements.txt`), el `.env` y los NOMBRES de sus variables, si MySQL responde, si Docker está encendido y si
los puertos 8000, 8501, 8080 y 8081 están libres. Por qué es así: en los equipos del grupo hay versiones de Python distintas y el proyecto solo se probó en la 3.13; saberlo antes evita horas de errores raros.
Qué NO hace: sin `--instalar` no escribe nada, no cambia el PATH, no instala ni desinstala Python, nunca lee ni imprime un valor del `.env` (solo nombres) y no se conecta a MySQL con credenciales (solo abre y cierra
un socket al puerto). No decide por el equipo: los pasos de MySQL y Docker los hace cada persona con sus propias contraseñas.
"""
import argparse
import json
import re
import socket
import subprocess
import sys
from collections import namedtuple
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "orquestacion"))
from dotenv import dotenv_values  # noqa: E402

import preparar_airflow  # noqa: E402  (aquí viven la comprobación de Docker y la de puertos libres; no se duplican)

VERSION = (3, 13)
PUERTOS = {8000: "API", 8501: "panel", 8080: "Airflow", 8081: "phpMyAdmin"}
PUERTOS_MINIMO = (8000, 8501)
NOMBRES_ENV_COMPLETO = ("MYSQL_HOST", "MYSQL_PORT", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE", "MYSQL_DATABASE_PRUEBA",
                        "MYSQL_DOCKER_USER", "MYSQL_DOCKER_PASSWORD", "MYSQL_DOCKER_ORIGEN", "MYSQL_LECTURA_USER", "MYSQL_LECTURA_PASSWORD")
Resultado = namedtuple("Resultado", "nombre ok detalle accion modos")   # modos: en qué modos cuenta (a = mínimo, b = completo)
MINIMO, COMPLETO = "minimo", "completo"
AMBOS = (MINIMO, COMPLETO)


def _correr(ejecutar, cmd, **kw):
    return ejecutar(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=kw.pop("timeout", 120), **kw)


def pythons_instalados(ejecutar=subprocess.run):
    """{'3.13': ruta, ...} según `py -0p` (el lanzador de Python para Windows); {} si el lanzador no existe."""
    try:
        r = _correr(ejecutar, ["py", "-0p"])
    except (OSError, subprocess.SubprocessError):
        return {}
    versiones = {}
    for linea in (r.stdout or "").splitlines():
        m = re.match(r"\s*-(?:V:)?(\d+\.\d+)(?:-\d+)?\s+\*?\s*(\S.*)$", linea)
        if m:
            versiones[m.group(1)] = m.group(2).strip()
    return versiones


def comprobar_python(ejecutar=subprocess.run, actual=None):
    """¿Hay un Python 3.13? Se busca con `py -0p`; si el lanzador no existe, vale el intérprete que ejecuta este script."""
    actual = actual or sys.version_info[:2]
    encontrados = pythons_instalados(ejecutar)
    objetivo = f"{VERSION[0]}.{VERSION[1]}"
    otros = ", ".join(v for v in sorted(encontrados) if v != objetivo)
    if objetivo in encontrados or tuple(actual) == VERSION:
        extra = f" (también hay {otros}: no se usa)" if otros else ""
        return Resultado("Python 3.13", True, f"encontrado{extra}", "", AMBOS)
    hay = f"Solo se encontró {otros}." if otros else ("No se encontró el lanzador `py`." if not encontrados else "")
    return Resultado("Python 3.13", False, hay, "Instale Python 3.13 desde python.org EN PARALELO (marque «py launcher»; no desinstale la versión que ya tiene) y vuelva a ejecutar este script con `py -3.13`.", AMBOS)


def python_del_entorno(raiz):
    """Intérprete del entorno virtual del proyecto (`.venv`)."""
    return Path(raiz) / ".venv" / "Scripts" / "python.exe"


def comprobar_entorno(raiz, ejecutar=subprocess.run):
    """¿Existe `.venv` y es de Python 3.13?"""
    py = python_del_entorno(raiz)
    accion = r"Créelo con: py -3.13 -m venv .venv   (o ejecute este script con --instalar)"
    if not py.exists():
        return Resultado("Entorno virtual .venv", False, "no existe", accion, AMBOS)
    try:
        r = _correr(ejecutar, [str(py), "-c", "import sys; print('%d.%d' % sys.version_info[:2])"])
    except (OSError, subprocess.SubprocessError):
        return Resultado("Entorno virtual .venv", False, "no se pudo ejecutar su Python", accion, AMBOS)
    version = (r.stdout or "").strip()
    if version != f"{VERSION[0]}.{VERSION[1]}":
        return Resultado("Entorno virtual .venv", False, f"es de Python {version or 'desconocido'}, no de 3.13", "Bórrelo y créelo de nuevo con: py -3.13 -m venv .venv", AMBOS)
    return Resultado("Entorno virtual .venv", True, "Python 3.13", "", AMBOS)


def requisitos_fijados(raiz):
    """{nombre normalizado: versión} de las líneas `paquete==versión` de requirements.txt."""
    fijados = {}
    for linea in (Path(raiz) / "requirements.txt").read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*([A-Za-z0-9_.\[\]-]+?)\s*==\s*([^\s;#]+)", linea)
        if m:
            fijados[re.sub(r"[-_.]+", "-", m.group(1).split("[")[0]).lower()] = m.group(2)
    return fijados


def comprobar_requisitos(raiz, ejecutar=subprocess.run):
    """¿Están instalados los requisitos con las versiones exactas y `pip check` no ve conflictos?"""
    py = python_del_entorno(raiz)
    accion = r"Instálelos con: .\.venv\Scripts\python.exe -m pip install -r requirements.txt   (tarda de 5 a 7 minutos)"
    if not py.exists():
        return Resultado("Requisitos instalados", False, "falta el entorno virtual", accion, AMBOS)
    try:
        lista = json.loads(_correr(ejecutar, [str(py), "-m", "pip", "list", "--format=json"]).stdout or "[]")
        chequeo = _correr(ejecutar, [str(py), "-m", "pip", "check"])
    except (OSError, subprocess.SubprocessError, ValueError):
        return Resultado("Requisitos instalados", False, "no se pudo consultar pip", accion, AMBOS)
    instalados = {re.sub(r"[-_.]+", "-", p["name"]).lower(): p["version"] for p in lista}
    fijados = requisitos_fijados(raiz)
    distintos = sorted(n for n, v in fijados.items() if instalados.get(n) != v)
    if distintos:
        return Resultado("Requisitos instalados", False, f"{len(distintos)} de {len(fijados)} paquetes no están o tienen otra versión (por ejemplo {distintos[0]})", accion, AMBOS)
    if chequeo.returncode != 0:
        return Resultado("Requisitos instalados", False, "`pip check` encontró conflictos", "Reinstale con: .\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt", AMBOS)
    return Resultado("Requisitos instalados", True, f"{len(fijados)} paquetes con versión exacta y `pip check` sin conflictos", "", AMBOS)


def comprobar_env(raiz):
    """`.env` presente y qué NOMBRES de variables le faltan (nunca se lee ni se muestra un valor). El modo mínimo no lo necesita."""
    ruta = Path(raiz) / ".env"
    accion = r"Copie .env.example a .env y cree las cuentas con scripts\mysql\configurar_mysql.py (ver docs/instalacion/)."
    if not ruta.exists():
        return Resultado(".env del proyecto", False, "no existe (solo lo necesita el modo completo)", accion, (COMPLETO,))
    valores = dotenv_values(ruta)
    faltan = [n for n in NOMBRES_ENV_COMPLETO if not valores.get(n)]
    if faltan:
        return Resultado(".env del proyecto", False, "le faltan: " + ", ".join(faltan), accion, (COMPLETO,))
    return Resultado(".env del proyecto", True, f"con las {len(NOMBRES_ENV_COMPLETO)} variables de MySQL", "", (COMPLETO,))


def mysql_alcanzable(host, puerto, tiempo=3):
    """True si algo escucha en host:puerto (abre y cierra un socket; no se identifica ni consulta nada)."""
    try:
        with socket.create_connection((host, int(puerto)), timeout=tiempo):
            return True
    except OSError:
        return False


def comprobar_mysql(raiz, alcanzable=mysql_alcanzable):
    """¿Responde algo en el puerto de MySQL? Se toma de `.env` (MYSQL_HOST y MYSQL_PORT) y, si no están, 127.0.0.1:3306. Como ningún valor del `.env` se imprime, el mensaje nombra las variables, no su valor."""
    valores = dotenv_values(Path(raiz) / ".env") if (Path(raiz) / ".env").exists() else {}
    host, puerto = valores.get("MYSQL_HOST") or "127.0.0.1", valores.get("MYSQL_PORT") or "3306"
    donde = "el servidor de MYSQL_HOST y MYSQL_PORT" if valores.get("MYSQL_HOST") or valores.get("MYSQL_PORT") else "127.0.0.1:3306"
    if alcanzable(host, puerto):
        return Resultado("MySQL", True, f"responde en {donde}", "", (COMPLETO,))
    return Resultado("MySQL", False, f"no responde en {donde}", "Inicie el servicio MySQL80 (Servicios de Windows, o en PowerShell de administrador: Start-Service MySQL80).", (COMPLETO,))


def comprobar_docker(ejecutar=subprocess.run):
    """¿Docker Desktop está encendido y trae Compose? Reutiliza la comprobación de preparar_airflow.py."""
    ok, mensaje = preparar_airflow.comprobar_docker(ejecutar)
    return Resultado("Docker", ok, mensaje if ok else "", "" if ok else mensaje[0].upper() + mensaje[1:] + ".", (COMPLETO,))


def comprobar_puertos(comprobar_puerto=None):
    """Un resultado por puerto (8000 y 8501 cuentan en el modo mínimo; 8080 y 8081, solo en el completo)."""
    comprobar_puerto = comprobar_puerto or preparar_airflow.puerto_libre
    resultados = []
    for puerto, servicio in PUERTOS.items():
        libre = comprobar_puerto(puerto)
        modos = AMBOS if puerto in PUERTOS_MINIMO else (COMPLETO,)
        resultados.append(Resultado(f"Puerto {puerto} ({servicio})", libre, "libre" if libre else "ocupado",
                                    "" if libre else f"Cierre lo que usa el puerto {puerto} o elija otro al lanzar {servicio}.", modos))
    return resultados


def diagnosticar(raiz=ROOT, ejecutar=subprocess.run, comprobar_puerto=None, alcanzable=mysql_alcanzable, actual=None):
    """Todas las comprobaciones, en el orden en que conviene arreglarlas. Solo lee."""
    return ([comprobar_python(ejecutar, actual), comprobar_entorno(raiz, ejecutar), comprobar_requisitos(raiz, ejecutar), comprobar_env(raiz),
             comprobar_mysql(raiz, alcanzable), comprobar_docker(ejecutar)] + comprobar_puertos(comprobar_puerto))


def formatear(resultados, modo):
    """Texto del informe con ✓/✗; lo que no cuenta en el modo elegido se marca con «·» y no hace fallar el diagnóstico. Devuelve (texto, todo_bien)."""
    lineas, bien = [], True
    for r in resultados:
        cuenta = modo in r.modos
        marca = ("✓" if r.ok else "✗") if cuenta else ("✓" if r.ok else "·")
        lineas.append(f"{marca} {r.nombre}" + (f": {r.detalle}" if r.detalle else "") + ("" if cuenta else f"  (solo cuenta en el modo {COMPLETO})"))
        if not r.ok and cuenta:
            bien = False
            lineas.append(f"    → {r.accion}")
    lineas.append(f"\nModo {modo}: " + ("todo lo necesario está listo." if bien else "falta lo marcado con ✗; siga las acciones sugeridas y vuelva a ejecutar."))
    return "\n".join(lineas), bien


def instalar(raiz, preguntar=input, ejecutar=subprocess.run, salida=print):
    """Crea `.venv` con `py -3.13` (si no existe) e instala `requirements.txt` DESPUÉS de pedir confirmación. Devuelve el código de salida (0 bien, 1 no se hizo o falló)."""
    raiz = Path(raiz)
    py = python_del_entorno(raiz)
    salida("Se va a " + ("" if py.exists() else "crear el entorno virtual .venv con `py -3.13` y a ") + "instalar requirements.txt en él (descarga unos 200 MB y tarda de 5 a 7 minutos).")
    if preguntar("¿Continuar? [s/N] ").strip().lower() not in ("s", "si", "sí", "y", "yes"):
        salida("No se hizo nada.")
        return 1
    if not py.exists():
        r = ejecutar(["py", "-3.13", "-m", "venv", str(raiz / ".venv")], cwd=raiz)
        if r.returncode != 0:
            salida("✗ No se pudo crear el entorno con `py -3.13` (¿está instalado Python 3.13 en paralelo?).")
            return 1
    r = ejecutar([str(py), "-m", "pip", "install", "-r", "requirements.txt"], cwd=raiz)
    if r.returncode != 0:
        salida("✗ La instalación de requirements.txt falló; revise el mensaje de pip de arriba.")
        return 1
    salida("✓ Entorno listo. Vuelva a ejecutar este script sin --instalar para comprobarlo.")
    return 0


def main(argv=None):
    for flujo in (sys.stdout, sys.stderr):           # las marcas ✓ y ✗ no existen en cp1252: con la salida redirigida se reemplazan por «?» en lugar de caer
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--modo", choices=AMBOS, default=MINIMO, help="minimo: pipeline, API y panel con SQLite; completo: además MySQL, Docker, Airflow y phpMyAdmin")
    ap.add_argument("--instalar", action="store_true", help="crea .venv con py -3.13 e instala requirements.txt, pidiendo confirmación")
    a = ap.parse_args(argv)
    if a.instalar:
        return instalar(ROOT)
    texto, bien = formatear(diagnosticar(ROOT), a.modo)
    print(texto)
    return 0 if bien else 1


if __name__ == "__main__":
    sys.exit(main())
