"""Capturas nuevas para el README: dos páginas del panel y la documentación automática de la API, con el navegador sin ventana (Edge o Chrome por DevTools).

Uso:  python scripts/evidencias/evidencia_capturas_readme.py [--destino docs/evidencias/readme]
Arranca el lanzador real del panel (API y panel en 127.0.0.1, almacenamiento SQLite, sin Docker), espera a que cada página termine de dibujarse y guarda la imagen original
(`EV-110_captura_<nombre>.png`) más un registro con lo que se vio. No toca el panel, la API ni los datos. Las imágenes son capturas automatizadas del navegador; no las toma una persona.
La documentación de la API (`/docs`) la dibuja Swagger UI con archivos que el navegador pide a un CDN, así que esa captura necesita red; si no la hay, se informa y se omite.
"""
import argparse
import base64
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import evidencia_capturas_panel as cp  # noqa: E402
import panel_vivo  # noqa: E402

PANEL = (("respuesta", ""), ("estratos", "estratos"))
SONDA_API = "(() => JSON.stringify({ruta: location.pathname, ops: document.querySelectorAll('.opblock').length, alto: document.documentElement.scrollHeight, cargando: document.querySelector('.loading-container') !== null}))()"


def capturar(cdp, ancho, alto):
    cdp.llamar("Emulation.setDeviceMetricsOverride", width=ancho, height=alto, deviceScaleFactor=1, mobile=False)
    time.sleep(1.5)
    return base64.b64decode(cdp.llamar("Page.captureScreenshot", format="png")["data"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--destino", default="docs/evidencias/readme")
    a = ap.parse_args()
    exe = next((p for p in cp.NAVEGADORES if Path(p).exists()), None)
    if exe is None:
        print("No hay un navegador automatizable (Edge o Chrome): no se generan capturas.")
        return 1
    destino = REPO / a.destino
    destino.mkdir(parents=True, exist_ok=True)
    lineas, ok = [], True
    with tempfile.TemporaryDirectory() as perfil, panel_vivo.panel_en_marcha(duracion=600) as (urls, _, _):
        navegador = subprocess.Popen([exe, "--headless=new", "--disable-gpu", f"--user-data-dir={perfil}", f"--remote-debugging-port={cp.PUERTO_DEPURACION}",
                                      f"--window-size={cp.ANCHO},{cp.ALTO_MINIMO}", "--force-color-profile=srgb", "--hide-scrollbars", "about:blank"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cdp = None
        try:
            version = cp._json(f"http://127.0.0.1:{cp.PUERTO_DEPURACION}/json/version")
            objetivo = next(t for t in cp._json(f"http://127.0.0.1:{cp.PUERTO_DEPURACION}/json/list") if t["type"] == "page")
            cdp = cp.Cdp(objetivo["webSocketDebuggerUrl"])
            cdp.llamar("Page.enable")
            cdp.llamar("Emulation.setEmulatedMedia", features=[{"name": "prefers-color-scheme", "value": "light"}])
            lineas += [f"Navegador: {Path(exe).name} {version['Browser']} sin ventana, por el protocolo DevTools; ventana de {cp.ANCHO} px de ancho.",
                       f"Panel: {urls['panel']} y API: {urls['api']} (lanzador scripts/panel/ejecutar_panel.py, almacenamiento SQLite, sin Docker).",
                       "Cada imagen es una captura automatizada del navegador; no muestra rutas del equipo, usuarios ni credenciales.", "",
                       "| Imagen | Archivo | Alto (px) | Qué se verificó |", "|---|---|---|---|"]
            for pid, url_path in PANEL:
                cdp.llamar("Emulation.setDeviceMetricsOverride", width=cp.ANCHO, height=cp.ALTO_MINIMO, deviceScaleFactor=1, mobile=False)
                cdp.llamar("Page.navigate", url=f"{urls['panel']}/{url_path}")
                for _ in range(60):   # tras navegar, el documento nuevo tarda un instante en poder evaluarse
                    if cdp.evaluar(cp.SONDA) is not None:
                        break
                    time.sleep(0.5)
                s = cp.esperar_pagina(cdp, pid)
                alto = max(cp.ALTO_MINIMO, min(cp.ALTO_MAXIMO, int(s["alto"]) + 40))
                png = capturar(cdp, cp.ANCHO, alto)
                nombre = f"EV-110_captura_panel_{pid}.png"
                (destino / nombre).write_bytes(png)
                errores = [x for x in ("Traceback", "Exception", "Error", "No se pudo conectar", "Page not found") if x in s["texto"]]
                ok &= not errores and "Alcance." in s["texto"]
                lineas.append(f"| Panel, página {pid} | `{nombre}` | {alto} | recuadro de alcance visible; errores en pantalla: {', '.join(errores) or 'ninguno'} |")
            cdp.llamar("Page.navigate", url=f"{urls['api']}/docs")
            fin, listo = time.monotonic() + 40, None
            while time.monotonic() < fin:
                s = json.loads(cdp.evaluar(SONDA_API))
                if s["ops"] >= 11 and not s["cargando"]:
                    listo = s
                    break
                time.sleep(1)
            if listo is None:
                lineas.append("| API, /docs | (no generada) | | Swagger UI no terminó de dibujarse en 40 s (necesita red para su CDN) |")
                ok = False
            else:
                alto = max(cp.ALTO_MINIMO, min(cp.ALTO_MAXIMO, int(listo["alto"]) + 40))
                png = capturar(cdp, cp.ANCHO, alto)
                nombre = "EV-110_captura_api_docs.png"
                (destino / nombre).write_bytes(png)
                lineas.append(f"| API, documentación automática | `{nombre}` | {alto} | {listo['ops']} operaciones dibujadas |")
        finally:
            if cdp is not None:
                cdp.cerrar()
            navegador.terminate()
            try:
                navegador.wait(timeout=15)
            except subprocess.TimeoutExpired:
                navegador.kill()
    vivos = panel_vivo.procesos_del_panel()
    ok &= not vivos
    lineas += ["", f"Procesos del panel o de la API que quedan vivos al terminar: {len(vivos)}.", f"Resultado: {'todas las capturas se generaron' if ok else 'HAY CAPTURAS CON PROBLEMAS'}."]
    cuerpo = "\n".join(lineas) + "\n"
    print(cuerpo)
    (destino / "EV-110_capturas_para_el_readme.txt").write_text(cuerpo, encoding="utf-8", newline="\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
