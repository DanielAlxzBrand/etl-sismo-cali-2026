"""Capturas automatizadas del navegador sin ventana (Edge o Chrome por el protocolo DevTools) de cada página del panel en marcha.

Uso:  python scripts/evidencias/evidencia_capturas_panel.py [--nombre EV-054_capturas_panel.txt]
Arranca el lanzador real (API y panel en 127.0.0.1, almacenamiento SQLite), abre cada página en el navegador, espera a que Streamlit termine de dibujarla y guarda una captura
por página (`EV-054_captura_<página>.png`) más un registro con el texto de cada una. Las imágenes se rotulan «captura automatizada del navegador»; no las toma una persona.
Se usa el protocolo DevTools porque Streamlit dibuja por websocket y la captura directa con `--screenshot` solo alcanza a guardar la pantalla de carga.
No instala nada: el cliente websocket ya viene con Streamlit.
"""
import argparse
import base64
import json
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import evidencia  # noqa: E402
import panel_vivo  # noqa: E402
from websockets.sync.client import connect  # noqa: E402

from src.panel import registro  # noqa: E402

NAVEGADORES = (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Google\Chrome\Application\chrome.exe")
PUERTO_DEPURACION = 9333
ANCHO, ALTO_MINIMO, ALTO_MAXIMO = 1400, 900, 7000
CON_GRAFICO = {"estratos", "comunas", "sensibilidades", "construcciones"}
SONDA = """(() => { const m = document.querySelector('[data-testid="stMain"]') || document.body;
  return JSON.stringify({texto: m.innerText || '', alto: m.scrollHeight, corriendo: !!document.querySelector('[data-testid="stStatusWidget"]'),
    graficos: document.querySelectorAll('[data-testid="stVegaLiteChart"], [data-testid="stArrowVegaLiteChart"]').length,
    lienzos: document.querySelectorAll('[data-testid="stVegaLiteChart"] canvas, [data-testid="stArrowVegaLiteChart"] canvas, [data-testid="stVegaLiteChart"] svg').length}); })()"""


class Cdp:
    def __init__(self, url):
        self._contexto = connect(url, max_size=None, open_timeout=20)
        self.ws, self.n = self._contexto.__enter__(), 0

    def llamar(self, metodo, **params):
        self.n += 1
        self.ws.send(json.dumps({"id": self.n, "method": metodo, "params": params}))
        while True:
            r = json.loads(self.ws.recv(timeout=60))
            if r.get("id") == self.n:
                if "error" in r:
                    raise RuntimeError(f"{metodo}: {r['error'].get('message')}")
                return r.get("result", {})

    def evaluar(self, expresion):
        return self.llamar("Runtime.evaluate", expression=expresion, returnByValue=True)["result"].get("value")

    def cerrar(self):
        self._contexto.__exit__(None, None, None)


def _json(url, intentos=60):
    for _ in range(intentos):
        try:
            return json.loads(urllib.request.urlopen(url, timeout=3).read())
        except OSError:
            time.sleep(0.5)
    raise RuntimeError(f"sin respuesta de {url}")


def esperar_pagina(cdp, pagina, limite=75):
    """Espera a que Streamlit termine de dibujar (alcance visible, sin «Running» y, si aplica, con el gráfico dibujado). Devuelve la sonda final."""
    fin, estable, ultima = time.monotonic() + limite, 0, None
    while time.monotonic() < fin:
        s = json.loads(cdp.evaluar(SONDA))
        listo = "Alcance." in s["texto"] and not s["corriendo"] and (pagina not in CON_GRAFICO or (s["graficos"] >= 1 and s["lienzos"] >= 1))
        estable = estable + 1 if listo and ultima and abs(s["alto"] - ultima["alto"]) < 2 else 0
        ultima = s
        if estable >= 3:
            return s
        time.sleep(0.7)
    raise RuntimeError(f"la página {pagina} no terminó de dibujarse a tiempo")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nombre", default="EV-054_capturas_panel.txt")
    a = ap.parse_args()
    t0 = time.perf_counter()
    exe = next((p for p in NAVEGADORES if Path(p).exists()), None)
    if exe is None:
        print("No hay un navegador automatizable (Edge o Chrome): no se generan capturas; queda la captura manual opcional (política D35).")
        return 1
    destino = REPO / "docs" / "evidencias" / "panel"
    destino.mkdir(parents=True, exist_ok=True)
    lineas, ok = [], True
    with tempfile.TemporaryDirectory() as perfil, panel_vivo.panel_en_marcha(duracion=900) as (urls, _, _):
        navegador = subprocess.Popen([exe, "--headless=new", "--disable-gpu", f"--user-data-dir={perfil}", f"--remote-debugging-port={PUERTO_DEPURACION}",
                                      f"--window-size={ANCHO},{ALTO_MINIMO}", "--force-color-profile=srgb", "--hide-scrollbars", "about:blank"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cdp = None
        try:
            version = _json(f"http://127.0.0.1:{PUERTO_DEPURACION}/json/version")
            objetivo = next(t for t in _json(f"http://127.0.0.1:{PUERTO_DEPURACION}/json/list") if t["type"] == "page")
            cdp = Cdp(objetivo["webSocketDebuggerUrl"])
            cdp.llamar("Page.enable")
            cdp.llamar("Emulation.setEmulatedMedia", features=[{"name": "prefers-color-scheme", "value": "light"}])
            lineas += [f"Navegador: {Path(exe).name} {version['Browser']} sin ventana, por el protocolo DevTools; ventana de {ANCHO} px de ancho.",
                       f"Panel: {urls['panel']} (lanzado con scripts/panel/ejecutar_panel.py; API en {urls['api']}, almacenamiento SQLite).",
                       "Cada imagen es una «captura automatizada del navegador» (no la toma una persona) de la página ya dibujada; no muestra datos sensibles.", "",
                       "| Página | Archivo | Alto (px) | Gráficos | Texto visible | Errores en pantalla |", "|---|---|---|---|---|---|"]
            for i, p in enumerate(registro.PAGINAS):
                cdp.llamar("Emulation.setDeviceMetricsOverride", width=ANCHO, height=ALTO_MINIMO, deviceScaleFactor=1, mobile=False)
                cdp.llamar("Page.navigate", url=f"{urls['panel']}/" + ("" if i == 0 else p.url_path))   # la primera página es la de inicio: vive en la raíz
                s = esperar_pagina(cdp, p.id)
                alto = max(ALTO_MINIMO, min(ALTO_MAXIMO, int(s["alto"]) + 40))
                cdp.llamar("Emulation.setDeviceMetricsOverride", width=ANCHO, height=alto, deviceScaleFactor=1, mobile=False)
                time.sleep(1.5)
                s = json.loads(cdp.evaluar(SONDA))
                png = base64.b64decode(cdp.llamar("Page.captureScreenshot", format="png")["data"])
                nombre = f"EV-054_captura_{p.id}.png"
                (destino / nombre).write_bytes(png)
                errores = [x for x in ("Traceback", "Exception", "Error", "No se pudo conectar", "Page not found") if x in s["texto"]]
                ok &= not errores and "Alcance." in s["texto"] and p.titulo in s["texto"]
                lineas.append(f"| {p.titulo} | `{nombre}` | {alto} | {s['graficos']} | {len(s['texto'])} caracteres; recuadro de alcance: {'sí' if 'Alcance.' in s['texto'] else 'NO'} | {', '.join(errores) or 'ninguno'} |")
        finally:
            if cdp is not None:
                cdp.cerrar()
            navegador.terminate()
            try:
                navegador.wait(timeout=15)
            except subprocess.TimeoutExpired:
                navegador.kill()
    ok &= not panel_vivo.procesos_del_panel()
    lineas += ["", f"Procesos del panel o de la API que quedan vivos al terminar: {len(panel_vivo.procesos_del_panel())}.", f"Resultado: {'todas las páginas se capturaron con su alcance visible y sin avisos de error' if ok else 'HAY PÁGINAS CON PROBLEMAS'}."]
    cuerpo = "\n".join(lineas) + "\n"
    print(cuerpo)
    evidencia.guardar("panel", a.nombre, "Capturas automatizadas del navegador de las ocho páginas del panel", "python scripts/evidencias/evidencia_capturas_panel.py (navegador sin ventana por DevTools)",
                      0 if ok else 1, time.perf_counter() - t0, cuerpo)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
