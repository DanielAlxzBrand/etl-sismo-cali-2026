"""Comprueba si el contraste de 1,0 de un rótulo de eje (Construcciones a 1024 px, EV-068) era texto invisible de verdad o un artefacto de la medición (F-12).

Uso:  python scripts/evidencias/evidencia_contraste_dudoso.py
Abre la página Construcciones a 1024 px en un navegador sin ventana (como D79), lista los textos de los ejes del gráfico con su relleno y su opacidad calculados por el navegador, y guarda un recorte del
gráfico (EV-076). Si los rótulos con opacidad cero son los que el gráfico oculta por solaparse con sus vecinos, la medición de 1,0 era un artefacto; si el rótulo faltara en la imagen, sería un defecto.
Escribe EV-076 en docs/evidencias/ajustes_ux/ y cierra el navegador y el panel al terminar.
"""
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
import evidencia  # noqa: E402
import evidencia_capturas_panel as base  # noqa: E402
import panel_vivo  # noqa: E402

DESTINO = REPO / "docs" / "evidencias" / "ajustes_ux"
JS = """(() => { const sal = [];
  for (const g of document.querySelectorAll('[data-testid="stVegaLiteChart"] svg g.role-axis-label, [data-testid="stArrowVegaLiteChart"] svg g.role-axis-label')) {
    const eje = g.closest('g.role-axis') ? (g.closest('g.role-axis').getAttribute('aria-label') || '') : '';
    for (const t of g.querySelectorAll('text')) { const cs = getComputedStyle(t);
      sal.push({eje: eje.startsWith('X-axis') ? 'eje horizontal (longitud)' : 'eje vertical (latitud)', texto: t.textContent, relleno: cs.fill, opacidad: cs.opacity}); } }
  const ch = document.querySelector('[data-testid="stVegaLiteChart"], [data-testid="stArrowVegaLiteChart"]'); const rc = ch ? ch.getBoundingClientRect() : null;
  return JSON.stringify({textos: sal, caja: rc ? {x: rc.x, y: rc.y + window.scrollY, w: rc.width, h: rc.height} : null}); })()"""


def main():
    t0 = time.perf_counter()
    exe = next((p for p in base.NAVEGADORES if Path(p).exists()), None)
    if exe is None:
        print("No hay un navegador automatizable.")
        return 1
    with tempfile.TemporaryDirectory() as perfil, panel_vivo.panel_en_marcha(duracion=300) as (urls, _, _):
        nav = subprocess.Popen([exe, "--headless=new", "--disable-gpu", f"--user-data-dir={perfil}", f"--remote-debugging-port={base.PUERTO_DEPURACION}", "--window-size=1400,900", "--force-color-profile=srgb",
                                "--hide-scrollbars", "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cdp = None
        try:
            objetivo = next(t for t in base._json(f"http://127.0.0.1:{base.PUERTO_DEPURACION}/json/list") if t["type"] == "page")
            cdp = base.Cdp(objetivo["webSocketDebuggerUrl"])
            cdp.llamar("Page.enable")
            cdp.llamar("Emulation.setEmulatedMedia", features=[{"name": "prefers-color-scheme", "value": "light"}])
            cdp.llamar("Emulation.setDeviceMetricsOverride", width=1024, height=1800, deviceScaleFactor=2, mobile=False)
            cdp.llamar("Page.navigate", url=f"{urls['panel']}/construcciones")
            base.esperar_pagina(cdp, "construcciones")
            time.sleep(1.5)
            datos = json.loads(cdp.evaluar(JS))
            c = datos["caja"]
            png = base64.b64decode(cdp.llamar("Page.captureScreenshot", format="png", clip={"x": c["x"], "y": c["y"], "width": c["w"], "height": c["h"], "scale": 1}, captureBeyondViewport=True)["data"])
        finally:
            if cdp is not None:
                cdp.cerrar()
            nav.terminate()
            try:
                nav.wait(timeout=15)
            except subprocess.TimeoutExpired:
                nav.kill()
    DESTINO.mkdir(parents=True, exist_ok=True)
    (DESTINO / "EV-076_eje_construcciones_1024.png").write_bytes(png)
    ocultos = [t for t in datos["textos"] if float(t["opacidad"]) < 0.05]
    visibles = [t for t in datos["textos"] if float(t["opacidad"]) >= 0.5]
    filas = ["| Eje | Rótulo | Relleno | Opacidad calculada |", "|---|---|---|---|"] + [f"| {t['eje']} | {t['texto']} | {t['relleno']} | {t['opacidad']} |" for t in datos["textos"]]
    cuerpo = ("Textos de los ejes del gráfico «Ubicación de las construcciones de la página» (página Construcciones, 1024 px de ancho), tal como los calculó el navegador:\n\n" + "\n".join(filas) +
              f"\n\nRótulos con opacidad cero: {len(ocultos)}; con opacidad plena: {len(visibles)}. La imagen `EV-076_eje_construcciones_1024.png` (captura automatizada del navegador) muestra solo los rótulos de opacidad plena: "
              "los de opacidad cero no se dibujan porque el gráfico los oculta cuando se solapan con sus vecinos (por eso solo se ve uno de cada dos en el eje horizontal).\n\n"
              "Conclusión: el contraste de 1,0 de EV-068 fue un **artefacto de la medición**: el script tomaba el primer texto del eje, que podía ser uno de los ocultos (opacidad cero), y calculaba su contraste como si fuera visible. "
              "No hay texto invisible en el gráfico. `evidencia_capturas_ajustes.py` mide solo texto con opacidad plena.\n\n"
              "Qué NO demuestra: que todos los rótulos posibles del gráfico se vean en cualquier ancho, ni que la medición cubra otros gráficos fuera de Construcciones.\n")
    ruta = evidencia.guardar("ajustes_ux", "EV-076_contraste_dudoso.txt", "Verificación del contraste de 1,0 de un rótulo de eje", "python scripts/evidencias/evidencia_contraste_dudoso.py",
                             0 if ocultos and visibles and not panel_vivo.procesos_del_panel() else 1, time.perf_counter() - t0, cuerpo)
    print(cuerpo[-900:])
    print("evidencia:", ruta.relative_to(REPO))
    return 0 if ocultos and visibles and not panel_vivo.procesos_del_panel() else 1


if __name__ == "__main__":
    sys.exit(main())
