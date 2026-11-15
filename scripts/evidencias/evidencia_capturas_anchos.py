"""Capturas, desbordamiento, tiempos de dibujo y contraste del texto de cada página del panel en tres anchos (1400, 1024 y 390 px).

Uso:  python scripts/evidencias/evidencia_capturas_anchos.py [--repeticiones 5]
Arranca el lanzador real (API y panel en 127.0.0.1, SQLite) y un navegador sin ventana (Edge o Chrome) controlado por el protocolo DevTools, igual que
`evidencia_capturas_panel.py` (D79). Por cada página y ancho: una captura completa; si el contenido se desborda en horizontal (ancho del documento frente al de la ventana);
los elementos con texto recortado por el propio CSS; el tiempo hasta que la página termina de dibujarse, medido DENTRO del navegador (1 carga de calentamiento y N medidas;
«medición local de una máquina»); y la relación de contraste del texto secundario con la fórmula WCAG de `src/panel/tema.py` (valores calculados, sin declarar un nivel).
Escribe en docs/evidencias/usuarios/: EV-066 (capturas y resumen), EV-067 (tiempos) y EV-068 (contraste). Las imágenes se rotulan «captura automatizada del navegador».
No instala nada y cierra el navegador y el panel al terminar.
"""
import argparse
import base64
import csv
import io
import json
import re
import statistics
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

from src.panel import registro  # noqa: E402
from src.panel.tema import colores, contraste  # noqa: E402

ANCHOS = (1400, 1024, 390)
ALTO_MINIMO, ALTO_MAXIMO = 800, 12000
DESTINO = REPO / "docs" / "evidencias" / "usuarios"

OBSERVADOR = """(() => {
  window.__t = null; window.__grafico = %s;
  const listo = () => {
    const m = document.querySelector('[data-testid="stMain"]'); if (!m) return false;
    if (!(m.innerText || '').includes('Alcance.')) return false;
    if (document.querySelector('[data-testid="stStatusWidget"]')) return false;
    if (window.__grafico && !document.querySelectorAll('[data-testid="stVegaLiteChart"] canvas, [data-testid="stArrowVegaLiteChart"] canvas, [data-testid="stVegaLiteChart"] svg').length) return false;
    return true;
  };
  const tick = () => { if (window.__t === null && listo()) window.__t = performance.now(); };
  new MutationObserver(tick).observe(document, {subtree: true, childList: true, characterData: true});
  setInterval(tick, 40);
})();"""

MEDIDAS = """(() => {
  const w = window.innerWidth, de = document.documentElement;
  const main = document.querySelector('[data-testid="stMain"]') || document.body;
  const rec = [], des = [];
  for (const e of main.querySelectorAll('*')) {
    const cs = getComputedStyle(e);
    const txt = (e.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 50);
    if (e.scrollWidth > e.clientWidth + 1 && e.clientWidth > 0) {
      if (['hidden', 'clip'].includes(cs.overflowX) && txt) rec.push({tag: e.tagName.toLowerCase(), texto: txt, sw: e.scrollWidth, cw: e.clientWidth});
      else if (['auto', 'scroll'].includes(cs.overflowX)) des.push({tag: e.tagName.toLowerCase(), testid: e.getAttribute('data-testid') || '', texto: txt, sw: e.scrollWidth, cw: e.clientWidth});
    }
  }
  return JSON.stringify({iw: w, docSW: de.scrollWidth, mainSW: main.scrollWidth, mainCW: main.clientWidth, alto: main.scrollHeight,
    recortados: rec.slice(0, 8), n_recortados: rec.length, desplazables: des.slice(0, 8), n_desplazables: des.length});
})()"""

INVENTARIO = """(() => {
  const s = new Set();
  for (const e of document.querySelectorAll('button, [role=tab], [role=button], [aria-label], [title], input, textarea, a')) {
    for (const v of [e.getAttribute('aria-label'), e.getAttribute('title'), e.getAttribute('placeholder'), (e.tagName === 'BUTTON' || e.tagName === 'A') ? e.innerText : null]) {
      if (v && v.trim()) s.add(e.tagName.toLowerCase() + ': ' + v.trim().replace(/\\s+/g, ' ').slice(0, 80));
    }
  }
  const tablas = [...document.querySelectorAll('[data-testid="stDataFrame"]')].map(e => ({alto: e.offsetHeight, ancho: e.offsetWidth}));
  return JSON.stringify({controles: [...s].sort(), tablas});
})()"""

CONTRASTE = """(() => {
  const CATS = [['pie (caption)', '[data-testid="stCaptionContainer"]'], ['subtítulo', '[data-testid="stHeading"] h2, [data-testid="stHeading"] h3, h2, h3'],
    ['rótulo de tarjeta', '[data-testid="stMetricLabel"]'], ['valor de tarjeta', '[data-testid="stMetricValue"]'], ['texto de apoyo de tarjeta', '[data-testid="stMetricDelta"]'],
    ['texto del cuerpo', '[data-testid="stMarkdownContainer"] p'], ['encabezado de tabla', 'th'], ['celda de tabla', 'td'], ['aviso', '[data-testid="stAlert"] p, [data-testid="stAlert"]'],
    ['rótulo de control', '[data-testid="stWidgetLabel"]']];
  const parse = c => { const m = c.match(/rgba?\\(([^)]+)\\)/); if (!m) return null; const p = m[1].split(',').map(x => parseFloat(x)); return {r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1}; };
  const mezcla = (f, b) => ({r: f.r * f.a + b.r * (1 - f.a), g: f.g * f.a + b.g * (1 - f.a), b: f.b * f.a + b.b * (1 - f.a), a: 1});
  const fondo = e => { let capas = []; for (let n = e; n; n = n.parentElement) { const c = parse(getComputedStyle(n).backgroundColor); if (c && c.a > 0) { capas.push(c); if (c.a === 1) break; } }
    let b = {r: 255, g: 255, b: 255, a: 1}; for (const c of capas.reverse()) b = mezcla(c, b); return b; };
  const opac = e => { let o = 1; for (let n = e; n; n = n.parentElement) o *= parseFloat(getComputedStyle(n).opacity); return o; };
  const sal = [];
  for (const [cat, sel] of CATS) {
    const e = [...document.querySelectorAll(sel)].find(x => (x.innerText || '').trim().length > 2 && x.offsetParent !== null);
    if (!e) continue;
    const cs = getComputedStyle(e), f = fondo(e), c0 = parse(cs.color); c0.a = c0.a * opac(e); const t = mezcla(c0, f);
    sal.push({categoria: cat, texto: e.innerText.trim().replace(/\\s+/g, ' ').slice(0, 40), texto_rgb: [t.r, t.g, t.b].map(Math.round), fondo_rgb: [f.r, f.g, f.b].map(Math.round),
      px: parseFloat(cs.fontSize), peso: cs.fontWeight, opacidad: getComputedStyle(e).opacity});
  }
  const ejes = [];
  const SVG = [['rótulo de eje (gráfico)', 'g.role-axis-label text'], ['título de eje (gráfico)', 'g.role-axis-title text'], ['rótulo de leyenda (gráfico)', 'g.role-legend-label text']];
  for (const [cat, sel] of SVG) {
    const e = document.querySelector('[data-testid="stVegaLiteChart"] svg ' + sel) || document.querySelector('[data-testid="stArrowVegaLiteChart"] svg ' + sel);
    if (!e) continue;
    const cs = getComputedStyle(e), f = fondo(e.closest('[data-testid]') || document.body), c0 = parse(cs.fill); if (!c0) continue; c0.a = c0.a * opac(e) * parseFloat(cs.fillOpacity || 1);
    const t = mezcla(c0, f);
    sal.push({categoria: cat, texto: (e.textContent || '').slice(0, 40), texto_rgb: [t.r, t.g, t.b].map(Math.round), fondo_rgb: [f.r, f.g, f.b].map(Math.round), px: parseFloat(cs.fontSize), peso: cs.fontWeight, opacidad: opac(e)});
  }
  return JSON.stringify({texto: sal, ejes});
})()"""


def a_hex(rgb):
    return "#%02x%02x%02x" % tuple(int(v) for v in rgb)


def esperar_t(cdp, limite=75):
    fin = time.monotonic() + limite
    while time.monotonic() < fin:
        v = cdp.evaluar("window.__t")
        if v is not None:
            return float(v)
        time.sleep(0.08)
    raise RuntimeError("la página no terminó de dibujarse a tiempo")


def cargar(cdp, url, grafico):
    """Navega a `url` y devuelve los milisegundos, medidos en el navegador, hasta que la página terminó de dibujarse."""
    ident = cdp.llamar("Page.addScriptToEvaluateOnNewDocument", source=OBSERVADOR % ("true" if grafico else "false"))["identifier"]
    try:
        cdp.llamar("Page.navigate", url=url)
        return esperar_t(cdp)
    finally:
        cdp.llamar("Page.removeScriptToEvaluateOnNewDocument", identifier=ident)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repeticiones", type=int, default=5)
    a = ap.parse_args()
    t0 = time.perf_counter()
    exe = next((p for p in base.NAVEGADORES if Path(p).exists()), None)
    if exe is None:
        print("No hay un navegador automatizable (Edge o Chrome): no se generan capturas.")
        return 1
    DESTINO.mkdir(parents=True, exist_ok=True)
    tiempos, resumen_cap, contrastes, controles, tablas_vistas = [], [], [], {}, {}
    paleta = colores()
    with tempfile.TemporaryDirectory() as perfil, panel_vivo.panel_en_marcha(duracion=2400) as (urls, _, _):
        navegador = subprocess.Popen([exe, "--headless=new", "--disable-gpu", f"--user-data-dir={perfil}", f"--remote-debugging-port={base.PUERTO_DEPURACION}", "--window-size=1400,900",
                                      "--force-color-profile=srgb", "--hide-scrollbars", "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cdp = None
        try:
            version = base._json(f"http://127.0.0.1:{base.PUERTO_DEPURACION}/json/version")
            objetivo = next(t for t in base._json(f"http://127.0.0.1:{base.PUERTO_DEPURACION}/json/list") if t["type"] == "page")
            cdp = base.Cdp(objetivo["webSocketDebuggerUrl"])
            cdp.llamar("Page.enable")
            cdp.llamar("Emulation.setEmulatedMedia", features=[{"name": "prefers-color-scheme", "value": "light"}])
            for ancho in ANCHOS:
                for i, p in enumerate(registro.PAGINAS):
                    url = f"{urls['panel']}/" + ("" if i == 0 else p.url_path)
                    cdp.llamar("Emulation.setDeviceMetricsOverride", width=ancho, height=ALTO_MINIMO, deviceScaleFactor=1, mobile=ancho < 500)
                    cargar(cdp, url, p.id in base.CON_GRAFICO)                          # calentamiento
                    medidas = [cargar(cdp, url, p.id in base.CON_GRAFICO) for _ in range(a.repeticiones)]
                    tiempos += [(p.id, ancho, k + 1, round(m, 1)) for k, m in enumerate(medidas)]
                    s = base.esperar_pagina(cdp, p.id)
                    m = json.loads(cdp.evaluar(MEDIDAS))
                    inv = json.loads(cdp.evaluar(INVENTARIO))
                    controles.setdefault(p.id, set()).update(inv["controles"])
                    tablas_vistas[(p.id, ancho)] = inv["tablas"]
                    cont = json.loads(cdp.evaluar(CONTRASTE))
                    for t in cont["texto"]:
                        contrastes.append((p.id, ancho, t["categoria"], t["texto"], a_hex(t["texto_rgb"]), a_hex(t["fondo_rgb"]), t["px"], t["peso"],
                                           round(contraste(a_hex(t["texto_rgb"]), a_hex(t["fondo_rgb"])), 2)))
                    alto = max(ALTO_MINIMO, min(ALTO_MAXIMO, int(s["alto"]) + 40))
                    cdp.llamar("Emulation.setDeviceMetricsOverride", width=ancho, height=alto, deviceScaleFactor=1, mobile=ancho < 500)
                    time.sleep(1.2)
                    png = base64.b64decode(cdp.llamar("Page.captureScreenshot", format="png")["data"])
                    nombre = f"EV-066_captura_{p.id}_{ancho}.png"
                    (DESTINO / nombre).write_bytes(png)
                    resumen_cap.append((p.titulo, ancho, nombre, alto, m))
        finally:
            if cdp is not None:
                cdp.cerrar()
            navegador.terminate()
            try:
                navegador.wait(timeout=15)
            except subprocess.TimeoutExpired:
                navegador.kill()
    vivos = len(panel_vivo.procesos_del_panel())

    # ---- EV-067: tiempos
    with io.StringIO() as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["pagina", "ancho_px", "repeticion", "ms_hasta_dibujada"])
        w.writerows(tiempos)
        evidencia_csv = f.getvalue()
    (DESTINO / "EV-067_mediciones_anchos.csv").write_text(evidencia_csv, encoding="utf-8", newline="\n")
    filas = ["| Página | Ancho (px) | Mediana (ms) | Mínimo (ms) | Máximo (ms) |", "|---|---|---|---|---|"]
    for p in registro.PAGINAS:
        for ancho in ANCHOS:
            v = [t for pid, an, _, t in tiempos if pid == p.id and an == ancho]
            filas.append(f"| {p.titulo} | {ancho} | {statistics.median(v):.0f} | {min(v):.0f} | {max(v):.0f} |")
    cuerpo_t = ("Tiempo desde que se pide la página hasta que Streamlit la dibujó (recuadro de alcance visible, sin indicador de ejecución y, si hay gráfico, ya dibujado), medido dentro del navegador con "
                f"`performance.now()`. 1 carga de calentamiento y {a.repeticiones} medidas por página y ancho. **Medición local de una máquina**: no es una garantía para otro equipo ni para otra red; "
                "el panel y la API corren en el mismo equipo y la API usa SQLite.\n\n" + "\n".join(filas) + "\n\nQué NO demuestra: ni la experiencia de una persona real con otra conexión ni el comportamiento con más de una persona a la vez; "
                "el tiempo percibido también depende de lo que la persona espera ver primero.\n")
    evidencia.guardar("usuarios", "EV-067_mediciones_anchos.txt", "Tiempos de dibujo de las ocho páginas en tres anchos", "python scripts/evidencias/evidencia_capturas_anchos.py (tiempo medido en el navegador)",
                      0, time.perf_counter() - t0, cuerpo_t)

    # ---- EV-068: contraste
    (DESTINO / "EV-068_contraste_texto.csv").write_text(
        "pagina,ancho_px,categoria,texto,color_texto,color_fondo,tamano_px,peso,relacion_de_contraste\n" + "\n".join(
            ",".join(f'"{x}"' if isinstance(x, str) and ("," in x or '"' in x) else str(x) for x in fila) for fila in contrastes) + "\n", encoding="utf-8", newline="\n")
    por_cat = {}
    for fila in contrastes:
        por_cat.setdefault(fila[2], []).append(fila[8])
    filas_c = ["| Categoría | Muestras | Mínimo | Mediana | Máximo | Supera 3 | Supera 4,5 | Supera 7 |", "|---|---|---|---|---|---|---|---|"]
    for cat, vs in sorted(por_cat.items(), key=lambda kv: min(kv[1])):
        sup = lambda u: "sí" if min(vs) >= u else ("en parte" if max(vs) >= u else "no")   # noqa: E731
        filas_c.append(f"| {cat} | {len(vs)} | {str(min(vs)).replace('.', ',')} | {str(round(statistics.median(vs), 2)).replace('.', ',')} | {str(max(vs)).replace('.', ',')} | {sup(3)} | {sup(4.5)} | {sup(7)} |")
    cuerpo_c = ("Relación de contraste del texto que dibuja Streamlit (pies, subtítulos, rótulos y valores de tarjetas, texto de tablas, avisos y rótulos de controles), calculada con la fórmula de luminancia relativa de WCAG 2.x "
                "(`src/panel/tema.py`) sobre los colores que el navegador calculó para el primer elemento visible de cada categoría en cada página y ancho. Valores calculados: **no se declara un nivel de conformidad**. "
                "El texto de los gráficos (rótulos y títulos de ejes, rótulos de leyenda) se midió en los elementos de texto del SVG; el texto de las tablas interactivas se dibuja en un lienzo y no se mide. La opacidad de los elementos y de sus contenedores se aplicó al color.\n\n"
                + "\n".join(filas_c) + "\n\nDetalle por página y ancho en `EV-068_contraste_texto.csv`. Qué NO demuestra: el contraste de cada elemento de la interfaz (solo una muestra por categoría), la legibilidad para personas con baja visión ni la conformidad con ninguna norma.\n")
    evidencia.guardar("usuarios", "EV-068_contraste_texto.txt", "Contraste calculado del texto secundario y de los rótulos del panel", "python scripts/evidencias/evidencia_capturas_anchos.py (colores calculados por el navegador)",
                      0, time.perf_counter() - t0, cuerpo_c)

    # ---- EV-066: capturas y desbordamiento
    L = [f"Navegador: {Path(exe).name} {version['Browser']} sin ventana, por el protocolo DevTools. Panel lanzado con scripts/ejecutar_panel.py (SQLite; API y panel en 127.0.0.1).".replace("scripts/ejecutar_panel.py", "scripts/panel/ejecutar_panel.py"),
         "Cada imagen es una «captura automatizada del navegador» (no la toma una persona) de la página ya dibujada. A 390 px se emula un dispositivo móvil con densidad 1; a 1024 y 1400 px, una ventana de escritorio.", "",
         "| Página | Ancho (px) | Archivo | Alto (px) | Ancho del documento / de la ventana | Desborda en horizontal | Elementos con texto recortado | Contenedores con desplazamiento horizontal |", "|---|---|---|---|---|---|---|---|"]
    for titulo, ancho, nombre, alto, m in resumen_cap:
        L.append(f"| {titulo} | {ancho} | `{nombre}` | {alto} | {m['docSW']} / {m['iw']} | {'sí' if m['docSW'] > m['iw'] + 1 else 'no'} | {m['n_recortados']} | {m['n_desplazables']} |")
    L += ["", "## Elementos con texto recortado por el CSS (hasta 8 por página y ancho)", ""]
    for titulo, ancho, nombre, alto, m in resumen_cap:
        for r in m["recortados"]:
            L.append(f"- {titulo}, {ancho} px: `<{r['tag']}>` «{r['texto']}» (contenido {r['sw']} px en una caja de {r['cw']} px)")
    L += ["", "## Contenedores con desplazamiento horizontal (tablas anchas)", ""]
    for titulo, ancho, nombre, alto, m in resumen_cap:
        for r in m["desplazables"]:
            L.append(f"- {titulo}, {ancho} px: `<{r['tag']}>` {r['testid']} (contenido {r['sw']} px en {r['cw']} px)")
    L += ["", "## Tablas interactivas (alto y ancho de la caja)", ""]
    for (pid, ancho), tabs in sorted(tablas_vistas.items()):
        if tabs:
            L.append(f"- {pid}, {ancho} px: {', '.join(f'{t['ancho']}×{t['alto']} px' for t in tabs)}")
    L += ["", "## Textos de controles y etiquetas accesibles que dibuja el navegador (por página; sin los de datos)", ""]
    for pid, textos in sorted(controles.items()):
        L.append(f"- **{pid}**: " + "; ".join(sorted(textos)[:40]))
    L += ["", f"Procesos del panel o de la API que quedan vivos al terminar: {vivos}."]
    cuerpo = "\n".join(L) + "\n"
    print(cuerpo[:3000])
    evidencia.guardar("usuarios", "EV-066_capturas_anchos.txt", "Capturas, desbordamiento y texto recortado de las ocho páginas en tres anchos", "python scripts/evidencias/evidencia_capturas_anchos.py (navegador sin ventana por DevTools)",
                      0 if vivos == 0 else 1, time.perf_counter() - t0, cuerpo)
    return 0 if vivos == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
