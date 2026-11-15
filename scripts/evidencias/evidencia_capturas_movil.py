"""Capturas de las ocho páginas del panel a 390 px con la barra lateral cerrada (complemento de `evidencia_capturas_anchos.py`).

Uso:  python scripts/evidencias/evidencia_capturas_movil.py
A 390 px el panel abre con la barra lateral desplegada y cubre el contenido (EV-066). Aquí se repite la captura después de cerrar esa barra con su botón, para ver cómo se acomoda
el contenido en un ancho de teléfono y medir el desbordamiento y el texto recortado. Mismo procedimiento que D79 (navegador sin ventana por DevTools); escribe EV-069 en docs/evidencias/usuarios/.
Las imágenes son «capturas automatizadas del navegador» con un dispositivo móvil emulado (densidad 1).
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
import evidencia_capturas_anchos as anchos  # noqa: E402
import evidencia_capturas_panel as base  # noqa: E402
import panel_vivo  # noqa: E402

from src.panel import registro  # noqa: E402

ANCHO = 390
CERRAR = """(() => { const b = document.querySelector('[data-testid="stSidebarCollapseButton"] button') || document.querySelector('[data-testid="stSidebarCollapseButton"]');
  if (!b) return 'sin botón'; b.click(); return 'cerrada'; })()"""


def main():
    t0 = time.perf_counter()
    exe = next((p for p in base.NAVEGADORES if Path(p).exists()), None)
    if exe is None:
        print("No hay un navegador automatizable.")
        return 1
    filas, ok = [], True
    with tempfile.TemporaryDirectory() as perfil, panel_vivo.panel_en_marcha(duracion=900) as (urls, _, _):
        nav = subprocess.Popen([exe, "--headless=new", "--disable-gpu", f"--user-data-dir={perfil}", f"--remote-debugging-port={base.PUERTO_DEPURACION}", "--window-size=1400,900",
                                "--force-color-profile=srgb", "--hide-scrollbars", "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cdp = None
        try:
            objetivo = next(t for t in base._json(f"http://127.0.0.1:{base.PUERTO_DEPURACION}/json/list") if t["type"] == "page")
            cdp = base.Cdp(objetivo["webSocketDebuggerUrl"])
            cdp.llamar("Page.enable")
            cdp.llamar("Emulation.setEmulatedMedia", features=[{"name": "prefers-color-scheme", "value": "light"}])
            for i, p in enumerate(registro.PAGINAS):
                cdp.llamar("Emulation.setDeviceMetricsOverride", width=ANCHO, height=anchos.ALTO_MINIMO, deviceScaleFactor=1, mobile=True)
                cdp.llamar("Page.navigate", url=f"{urls['panel']}/" + ("" if i == 0 else p.url_path))
                base.esperar_pagina(cdp, p.id)
                estado = cdp.evaluar(CERRAR)
                time.sleep(1.0)
                s = base.esperar_pagina(cdp, p.id)
                m = json.loads(cdp.evaluar(anchos.MEDIDAS))
                alto = max(anchos.ALTO_MINIMO, min(anchos.ALTO_MAXIMO, int(s["alto"]) + 40))
                cdp.llamar("Emulation.setDeviceMetricsOverride", width=ANCHO, height=alto, deviceScaleFactor=1, mobile=True)
                time.sleep(1.2)
                png = base64.b64decode(cdp.llamar("Page.captureScreenshot", format="png")["data"])
                nombre = f"EV-069_captura_{p.id}_390_barra_cerrada.png"
                (anchos.DESTINO / nombre).write_bytes(png)
                ok &= estado == "cerrada"
                filas.append((p.titulo, nombre, alto, estado, m))
        finally:
            if cdp is not None:
                cdp.cerrar()
            nav.terminate()
            try:
                nav.wait(timeout=15)
            except subprocess.TimeoutExpired:
                nav.kill()
    vivos = len(panel_vivo.procesos_del_panel())
    L = ["Cada imagen es una «captura automatizada del navegador» a 390 px de ancho (dispositivo móvil emulado, densidad 1) después de cerrar la barra lateral con su botón.", "",
         "| Página | Archivo | Alto (px) | Barra lateral | Ancho del documento / de la ventana | Desborda | Elementos con texto recortado | Contenedores con desplazamiento horizontal |", "|---|---|---|---|---|---|---|---|"]
    for titulo, nombre, alto, estado, m in filas:
        L.append(f"| {titulo} | `{nombre}` | {alto} | {estado} | {m['docSW']} / {m['iw']} | {'sí' if m['docSW'] > m['iw'] + 1 else 'no'} | {m['n_recortados']} | {m['n_desplazables']} |")
    L += ["", "## Texto recortado y tablas con desplazamiento", ""]
    for titulo, nombre, alto, estado, m in filas:
        L += [f"- {titulo}: recortado `<{r['tag']}>` «{r['texto']}» ({r['sw']} px en {r['cw']} px)" for r in m["recortados"]]
        L += [f"- {titulo}: desplazable `<{r['tag']}>` {r['testid']} ({r['sw']} px en {r['cw']} px)" for r in m["desplazables"]]
    L += ["", f"Procesos del panel o de la API que quedan vivos al terminar: {vivos}."]
    evidencia.guardar("usuarios", "EV-069_capturas_390_barra_cerrada.txt", "Capturas a 390 px con la barra lateral cerrada", "python scripts/evidencias/evidencia_capturas_movil.py (navegador sin ventana por DevTools)",
                      0 if ok and vivos == 0 else 1, time.perf_counter() - t0, "\n".join(L) + "\n")
    print("\n".join(L)[:2500])
    return 0 if ok and vivos == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
