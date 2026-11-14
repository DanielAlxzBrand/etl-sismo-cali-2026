"""Lanzador del panel: arranca la API de solo lectura y el panel (Streamlit) en 127.0.0.1 y los cierra a los dos al terminar.

Uso:  python scripts/panel/ejecutar_panel.py [--almacenamiento sqlite|mysql] [--puerto-api N] [--puerto-panel N] [--verificar]
Sin opciones espera hasta Ctrl+C. Con --verificar arranca, comprueba que ambos responden, imprime las URL y cierra (útil para pruebas y evidencias).
Si un puerto está ocupado elige uno libre. La configuración de Streamlit viaja por variables de entorno: no crea `.streamlit/` ni archivos en el repo ni en el HOME.
`--almacenamiento mysql` solo cambia la fuente de la API (la lee de `.env` por su cuenta; el lanzador no la ve ni la imprime).
Códigos de salida: 0 correcto; 1 la API no arrancó; 2 el panel no arrancó; 3 un proceso terminó antes de tiempo.
"""
import argparse
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
import httpx  # noqa: E402

from src.logger import get_logger  # noqa: E402
from src.panel.configuracion import cargar_panel  # noqa: E402

log = get_logger("panel.lanzador")
HOST = "127.0.0.1"
LANZADOR_API_MYSQL = "import sys,uvicorn; from src.api.app import crear_app; uvicorn.run(crear_app(almacenamiento='mysql'), host=sys.argv[1], port=int(sys.argv[2]), log_level='warning')"


def puerto_libre(preferido):
    """El puerto preferido si está libre en 127.0.0.1; si no, uno libre que asigne el sistema."""
    for candidato in (preferido, 0):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((HOST, candidato))
            except OSError:
                continue
            return s.getsockname()[1]
    raise OSError("no hay puertos libres en 127.0.0.1")


def comando_api(puerto, almacenamiento="sqlite", python=None):
    """Comando de la API: el de docs/api/arquitectura.md para SQLite; para MySQL, la misma aplicación con ese almacenamiento."""
    py = python or sys.executable
    if almacenamiento == "mysql":
        return [py, "-c", LANZADOR_API_MYSQL, HOST, str(puerto)]
    return [py, "-m", "uvicorn", "src.api.app:app", "--host", HOST, "--port", str(puerto)]


def comando_panel(puerto, python=None):
    return [python or sys.executable, "-m", "streamlit", "run", "src/panel/app.py", "--server.port", str(puerto)]


def entorno_panel(puerto_panel, url_api, base=None, colores=None):
    """Entorno del proceso de Streamlit: sin cabeza, solo local, sin estadísticas de uso ni avisos, tema y URL de la API."""
    entorno = dict(os.environ if base is None else base)
    for nombre in [k for k in entorno if k.startswith("MYSQL_")]:
        del entorno[nombre]          # el panel no necesita ni recibe credenciales
    c = colores or cargar_panel()["colores"]
    entorno.update({
        "STREAMLIT_SERVER_HEADLESS": "true", "STREAMLIT_SERVER_ADDRESS": HOST, "STREAMLIT_SERVER_PORT": str(puerto_panel),
        "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false", "STREAMLIT_SERVER_SHOW_EMAIL_PROMPT": "false", "STREAMLIT_SERVER_FILE_WATCHER_TYPE": "none",
        "STREAMLIT_CLIENT_TOOLBAR_MODE": "minimal", "STREAMLIT_GLOBAL_DEVELOPMENT_MODE": "false",
        "STREAMLIT_THEME_BASE": "light", "STREAMLIT_THEME_PRIMARY_COLOR": c["principal"], "STREAMLIT_THEME_TEXT_COLOR": c["texto"],
        "STREAMLIT_THEME_BACKGROUND_COLOR": c["fondo"], "STREAMLIT_THEME_SECONDARY_BACKGROUND_COLOR": c["fondo_secundario"],
        "PANEL_API_URL": url_api, "PYTHONDONTWRITEBYTECODE": "1",
    })
    return entorno


def esperar(url, valido, proceso, limite_s, pausa=0.5, http=httpx):
    """True cuando GET `url` cumple `valido(respuesta)`; False si se agota el tiempo o el proceso termina."""
    fin = time.monotonic() + limite_s
    while time.monotonic() < fin:
        if proceso.poll() is not None:
            return False
        try:
            if valido(http.get(url, timeout=2)):
                return True
        except httpx.HTTPError:
            pass
        time.sleep(pausa)
    return False


def cerrar(proceso, espera_s=10):
    """Cierra el proceso y sus hijos (en Windows con taskkill /T); idempotente."""
    if proceso is None or proceso.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(proceso.pid), "/T", "/F"], capture_output=True)
    else:
        proceso.terminate()
    try:
        proceso.wait(timeout=espera_s)
    except subprocess.TimeoutExpired:
        proceso.kill()
        proceso.wait(timeout=espera_s)


def main(argv=None, abrir=subprocess.Popen):
    ap = argparse.ArgumentParser(description="Arranca la API y el panel en 127.0.0.1")
    ap.add_argument("--almacenamiento", choices=["sqlite", "mysql"], default="sqlite")
    ap.add_argument("--puerto-api", type=int)
    ap.add_argument("--puerto-panel", type=int)
    ap.add_argument("--verificar", action="store_true", help="arranca, comprueba la salud de ambos, imprime las URL y cierra")
    a = ap.parse_args(argv)
    cfg = cargar_panel()
    p_api = puerto_libre(a.puerto_api or cfg["puerto_api"])
    p_panel = puerto_libre(a.puerto_panel or cfg["puerto_panel"])
    url_api, url_panel = f"http://{HOST}:{p_api}", f"http://{HOST}:{p_panel}"
    api = panel = None
    try:
        api = abrir(comando_api(p_api, a.almacenamiento), cwd=RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log.info("API arrancada (pid %s) en %s", api.pid, url_api)
        if not esperar(url_api + "/health", lambda r: r.status_code == 200, api, cfg["espera_arranque_s"]):
            print("La API no arrancó o no respondió a tiempo.")
            return 1
        panel = abrir(comando_panel(p_panel), cwd=RAIZ, env=entorno_panel(p_panel, url_api), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log.info("panel arrancado (pid %s) en %s", panel.pid, url_panel)
        if not esperar(url_panel + "/_stcore/health", lambda r: r.status_code == 200 and r.text.strip() == "ok", panel, cfg["espera_arranque_s"]):
            print("El panel no arrancó o no respondió a tiempo.")
            return 2
        print(f"API:   {url_api}  (documentación en {url_api}/docs)")
        print(f"Panel: {url_panel}")
        print(f"Almacenamiento de la API: {a.almacenamiento}")
        if a.verificar:
            return 0
        print("Ctrl+C para cerrar los dos procesos.")
        while True:
            if api.poll() is not None or panel.poll() is not None:
                print("Un proceso terminó antes de tiempo; se cierra el otro.")
                return 3
            time.sleep(1)
    except KeyboardInterrupt:
        print("Cerrando…")
        return 0
    finally:
        cerrar(panel)
        cerrar(api)
        log.info("procesos cerrados")


if __name__ == "__main__":
    sys.exit(main())
