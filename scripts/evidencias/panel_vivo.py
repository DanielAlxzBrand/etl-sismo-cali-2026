"""Apoyo de las evidencias del panel: arranca el lanzador real como subproceso, lee las URL que imprime y garantiza el cierre de todo el árbol de procesos.

No imprime ni lee credenciales: con `--almacenamiento mysql` la API lee `.env` por su cuenta, dentro de su proceso.
"""
import os
import re
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LANZADOR = REPO / "scripts" / "panel" / "ejecutar_panel.py"
PUERTO_API, PUERTO_PANEL = 8765, 8766


def procesos_del_panel():
    """Líneas de comando de los procesos uvicorn o streamlit del panel que sigan vivos (vacío si no queda ninguno)."""
    if os.name != "nt":
        r = subprocess.run(["pgrep", "-af", "streamlit run src/panel|uvicorn src.api"], capture_output=True, text=True)
        return [l for l in r.stdout.splitlines() if l.strip()]
    consulta = ("Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'python*' -and $_.CommandLine -match 'streamlit run src/panel|uvicorn src.api.app|crear_app' } | "
                "ForEach-Object { $_.ProcessId }")
    r = subprocess.run(["powershell", "-NoProfile", "-Command", consulta], capture_output=True, text=True)
    return [l for l in r.stdout.split() if l.isdigit()]


def _matar_arbol(proc):
    if proc.poll() is None:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
        else:
            proc.kill()
        proc.wait(timeout=15)


@contextmanager
def panel_en_marcha(almacenamiento="sqlite", duracion=600, puerto_api=PUERTO_API, puerto_panel=PUERTO_PANEL, espera=90):
    """Cede (urls, proceso_del_lanzador, líneas_de_salida); al salir, cierra el árbol si el lanzador sigue vivo."""
    cmd = [sys.executable, str(LANZADOR), "--almacenamiento", almacenamiento, "--duracion", str(duracion), "--puerto-api", str(puerto_api), "--puerto-panel", str(puerto_panel)]
    proc = subprocess.Popen(cmd, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, encoding="utf-8", errors="replace",
                            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"})
    lineas = []
    hilo = threading.Thread(target=lambda: [lineas.append(l.rstrip("\n")) for l in proc.stdout], daemon=True)
    hilo.start()
    try:
        fin = time.monotonic() + espera
        while time.monotonic() < fin and not any(l.startswith("Se cerrarán solos") or l.startswith("Ctrl+C") for l in lineas):
            if proc.poll() is not None:
                break
            time.sleep(0.3)
        texto = "\n".join(lineas)
        api = re.search(r"API:\s+(http://127\.0\.0\.1:\d+)", texto)
        panel = re.search(r"Panel:\s+(http://127\.0\.0\.1:\d+)", texto)
        if not (api and panel):
            raise RuntimeError("el lanzador no informó las URL a tiempo")
        yield {"api": api.group(1), "panel": panel.group(1)}, proc, lineas
    finally:
        _matar_arbol(proc)
        hilo.join(timeout=5)


# ---------- páginas con AppTest dentro del proceso (para equivalencias y mediciones) ----------
_ACTUAL = {}
GUION = "from panel_vivo import api_actual\nfrom src.panel.paginas import {modulo}\n{modulo}.render(api_actual())\n"


def api_actual():
    return _ACTUAL["api"]


def renderizar(modulo, api, tiempo=90):
    """(AppTest ya ejecutado, segundos que tardó) de la página `modulo` con la consulta `api(ruta, **params)`."""
    from streamlit.testing.v1 import AppTest
    _ACTUAL["api"] = api
    t0 = time.perf_counter()
    at = AppTest.from_string(GUION.format(modulo=modulo), default_timeout=tiempo).run()
    return at, time.perf_counter() - t0


def textos(at):
    """Todo el texto visible de la página, más el contenido de sus tablas."""
    partes = []
    for grupo in (at.markdown, at.caption, at.subheader, at.title, at.warning, at.info, at.error):
        partes += [e.value for e in grupo]
    for m in at.metric:
        partes += [m.label, m.value, m.help or ""]
    for t in list(at.dataframe) + list(at.table):
        partes.append(t.value.to_csv(index=False))
    return "\n".join(str(p) for p in partes)
