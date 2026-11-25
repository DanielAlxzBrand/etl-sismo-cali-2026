"""Comprobación en el navegador del título del gráfico de diferencias de Sensibilidades (D119): capturas a 1440 x 900, 768 x 1024 y 375 x 812 píxeles y medidas del título.

Uso:  python scripts/evidencias/capturas_titulo_sensibilidades.py [--nombre EV-129_titulo_del_grafico_de_sensibilidades.txt]
Qué hace: arranca el lanzador oficial (API y panel en 127.0.0.1, SQLite), abre Sensibilidades en cada tamaño, lleva la tarjeta del gráfico al borde superior de la ventana, guarda una captura
`docs/img/panel/sensibilidades_titulo_<ancho>x<alto>.png` (PNG de 256 colores) y mide en el SVG del gráfico la posición del título frente al borde del gráfico y frente al primer rótulo del eje.
A 1440 px además pasa el cursor por un punto (el tooltip debe traer el intervalo de Newcombe) y abre la guía de lectura (debe decir «1 de 6»). Escribe el registro en `docs/evidencias/frontend/`.
Qué NO hace: no cambia ningún dato ni ninguna cifra, no sustituye a las capturas de EV-128 (que quedan como se registraron) y no toma datos de otra fuente que la API del proyecto.
Última ejecución real: la del registro EV-129 (2026-11-24), sobre Edge sin ventana.
"""
import argparse
import base64
import hashlib
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import capturas_panel_definitivo as cap  # noqa: E402
import evidencia  # noqa: E402
import evidencia_capturas_panel as base  # noqa: E402
import panel_vivo  # noqa: E402
from PIL import Image  # noqa: E402

TAMANOS = ((1440, 900, False), (768, 1024, False), (375, 812, True))
MEDIDA = """(() => { const s = document.querySelector('[data-testid=stVegaLiteChart] svg'); const sr = s.getBoundingClientRect();
  const t = s.querySelector('.role-title text'); const tb = t.getBoundingClientRect();
  const ejes = [...s.querySelectorAll('.role-axis text')].map(e => e.getBoundingClientRect().top).filter(v => v > sr.top);
  const chart = s.closest('[data-testid=stVegaLiteChart]').getBoundingClientRect(); const tarjeta = chart.width;
  return JSON.stringify({lineas: t.querySelectorAll('tspan').length || 1, texto: t.textContent, arriba: Math.round((tb.top - sr.top) * 10) / 10, abajo: Math.round((tb.bottom - sr.top) * 10) / 10,
    primer_rotulo: Math.round((Math.min(...ejes) - sr.top) * 10) / 10, ancho: Math.round(sr.width), alto: Math.round(sr.height), ancho_ventana: innerWidth, desborda: document.documentElement.scrollWidth > innerWidth}); })()"""
PUNTO = """(() => { const p = document.querySelector('[data-testid=stVegaLiteChart] svg .role-mark.mark-symbol path') || document.querySelector('[data-testid=stVegaLiteChart] svg .mark-symbol path');
  const b = p.getBoundingClientRect(); return JSON.stringify({x: b.left + b.width / 2, y: b.top + b.height / 2}); })()"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nombre", default="EV-129_titulo_del_grafico_de_sensibilidades.txt")
    a = ap.parse_args()
    t0 = time.perf_counter()
    exe = next((x for x in base.NAVEGADORES if Path(x).exists()), None)
    if exe is None:
        print("No hay un navegador automatizable (Edge o Chrome).")
        return 1
    ok, filas, notas, hechas = True, [], [], []
    with tempfile.TemporaryDirectory() as perfil, panel_vivo.panel_en_marcha(duracion=900) as (urls, _, _):
        navegador = subprocess.Popen([exe, "--headless=new", "--disable-gpu", f"--user-data-dir={perfil}", f"--remote-debugging-port={base.PUERTO_DEPURACION}", "--window-size=1440,900",
                                      "--force-color-profile=srgb", "--hide-scrollbars", "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cdp = None
        try:
            version = base._json(f"http://127.0.0.1:{base.PUERTO_DEPURACION}/json/version")
            objetivo = next(t for t in base._json(f"http://127.0.0.1:{base.PUERTO_DEPURACION}/json/list") if t["type"] == "page")
            cdp = base.Cdp(objetivo["webSocketDebuggerUrl"])
            cdp.llamar("Page.enable")
            cdp.llamar("Emulation.setFocusEmulationEnabled", enabled=True)
            cdp.llamar("Page.bringToFront")
            cdp.llamar("Emulation.setEmulatedMedia", features=[{"name": "prefers-color-scheme", "value": "light"}])
            for ancho, alto, movil in TAMANOS:
                cdp.llamar("Emulation.setDeviceMetricsOverride", width=ancho, height=alto, deviceScaleFactor=2 if movil else 1, mobile=movil)
                cdp.llamar("Page.navigate", url=f"{urls['panel']}/sensibilidades")
                cap.esperar(cdp, "sensibilidades")
                time.sleep(2)
                cdp.evaluar("sessionStorage.clear();")
                cdp.evaluar("(() => { const m = document.querySelector('[data-testid=\"stMain\"]'); const e = document.querySelector('[data-testid=stVegaLiteChart]'); e.scrollIntoView({block: 'start'}); m.scrollTop -= 90; })()")
                time.sleep(1.5)
                m = json.loads(cdp.evaluar(MEDIDA))
                texto = json.loads(cdp.evaluar(base.SONDA))["texto"]
                bien = (m["arriba"] >= 4 and m["abajo"] <= m["primer_rotulo"] - 8 and m["lineas"] == 2 and not m["desborda"]
                        and "Alcance." in texto and "Razón ajustada" in texto and "Mantel-Haenszel" in texto)
                ok &= bien
                png, _ = cap.optimizar(base64.b64decode(cdp.llamar("Page.captureScreenshot", format="png")["data"]))
                nombre = f"sensibilidades_titulo_{ancho}x{alto}.png"
                (REPO / "docs" / "img" / "panel" / nombre).write_bytes(png)
                hechas.append(nombre)
                filas.append(f"| {ancho} x {alto} | `docs/img/panel/{nombre}` | {m['lineas']} | {m['arriba']} px | {m['abajo']} px | {m['primer_rotulo']} px | {'no' if not m['desborda'] else 'SÍ'} | {len(png) // 1024} KB | "
                             f"{hashlib.sha256(png).hexdigest()} | {'sí' if bien else 'NO'} |")
                if ancho == 1440:
                    p = json.loads(cdp.evaluar(PUNTO))
                    cdp.llamar("Input.dispatchMouseEvent", type="mouseMoved", x=p["x"], y=p["y"])
                    time.sleep(1.0)
                    tip = cdp.evaluar("(document.querySelector('#vg-tooltip-element') || {}).innerText || ''")
                    tip_ok = "Newcombe" in tip and "Escenario" in tip
                    cdp.evaluar("document.querySelector('.st-key-lienzo [data-accion=\"guia\"]').click()")
                    time.sleep(1.0)
                    guia = cdp.evaluar("document.querySelector('.st-key-lienzo [data-parte=\"serie\"]').textContent")
                    guia_ok = "1 de 6" in guia
                    ok &= tip_ok and guia_ok
                    notas += [f"Tooltip de un punto a 1440 px: «{' / '.join(tip.split())}» ({'trae el escenario y el intervalo de Newcombe' if tip_ok else 'NO trae lo esperado'}).",
                              f"Guía de lectura a 1440 px: «{guia}» ({'abre' if guia_ok else 'NO abre'})."]
            cdp.llamar("Emulation.clearDeviceMetricsOverride")
            cabecera = [f"Navegador: {Path(exe).name} {version['Browser']} sin ventana, por el protocolo DevTools. Panel lanzado con scripts/panel/ejecutar_panel.py (API y panel en 127.0.0.1, SQLite).",
                        "Texto del título medido: «" + m["texto"].replace("\n", " ") + "». El texto científico no cambió: se compara con el literal de la página en las pruebas (tests/test_panel_ajustes.py)."]
        finally:
            if cdp is not None:
                cdp.cerrar()
            navegador.terminate()
            try:
                navegador.wait(timeout=15)
            except subprocess.TimeoutExpired:
                navegador.kill()
    ok &= not panel_vivo.procesos_del_panel()
    cuerpo = "\n".join(cabecera + ["", "Medidas del título dentro del SVG del gráfico (distancias desde su borde superior; antes de la corrección, medido con el mismo método a 1440 px, el título empezaba a -8,5 px, es decir, la primera línea quedaba recortada):", "",
                                    "| Ventana | Captura | Líneas del título | Borde superior del título | Borde inferior del título | Primer rótulo del eje | Desborda en horizontal | Peso | sha256 | Correcto |",
                                    "|---|---|---|---|---|---|---|---|---|---|"] + filas
                       + ["", "Criterio de «correcto»: el borde superior del título está dentro del gráfico (4 px o más), su borde inferior queda al menos 8 px por encima del primer rótulo del eje, el título tiene dos líneas, la página no desborda y el texto de la página trae el alcance y la razón ajustada de Mantel-Haenszel."] + [""] + notas
                       + ["", f"Procesos del panel o de la API que quedan vivos al terminar: {len(panel_vivo.procesos_del_panel())}.",
                          f"Resultado: {'el título se muestra completo en los tres tamaños, sin superponerse, y el tooltip y la guía siguen funcionando' if ok else 'HAY PROBLEMAS: no usar estas capturas'}."]) + "\n"
    print(cuerpo)
    evidencia.guardar("frontend", a.nombre, "Título del gráfico de diferencias de Sensibilidades corregido (D119), a 1440, 768 y 375 píxeles",
                      "python scripts/evidencias/capturas_titulo_sensibilidades.py (navegador sin ventana por DevTools)", 0 if ok else 1, time.perf_counter() - t0, cuerpo)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
