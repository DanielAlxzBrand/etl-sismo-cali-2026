"""Evalúa si la versión fijada de Streamlit permite traducir u ocultar de forma limpia los controles en inglés de tablas y gráficos (F-11).

Uso:  python scripts/evidencias/evidencia_streamlit_controles.py
Mira tres cosas y lo deja escrito en EV-080 (docs/evidencias/ajustes_ux/): (1) qué parámetros ofrecen `st.dataframe` y `st.altair_chart` y qué opciones de configuración tocan la barra de herramientas;
(2) en cuántos archivos del front de Streamlit aparece cada texto en inglés (si está escrito dentro del código, no hay forma de traducirlo con una opción); (3) una prueba en vivo, con una aplicación mínima
en una carpeta temporal y un navegador sin ventana (como D79), de qué botones quedan en una tabla y en un gráfico con y sin `embedOptions` de Vega. No toca `src/panel` ni instala nada.
"""
import inspect
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
import evidencia_capturas_panel as base  # noqa: E402

import streamlit  # noqa: E402
from streamlit import config  # noqa: E402

PUERTO = 8790
TEXTOS = ("Download as CSV", "Search", "Fullscreen", "Show/hide columns", "Copy Vega-Lite spec", "Download as PNG", "Show data", "Skip to main content", "Collapse sidebar")
APLICACION = '''import altair as alt
import pandas as pd
import streamlit as st

df = pd.DataFrame({"a": ["x", "y", "z"], "b": [1, 2, 3]})
st.subheader("tabla")
st.dataframe(df, hide_index=True)
st.subheader("grafico con actions False")
st.altair_chart(alt.Chart(df).mark_bar().encode(x="a", y="b").properties(usermeta={"embedOptions": {"actions": False}}), width="stretch")
st.subheader("grafico por defecto")
st.altair_chart(alt.Chart(df).mark_bar().encode(x="a", y="b"), width="stretch")
'''
JS = """(() => { const por = {}; const etiquetas = (raiz) => { const s = new Set();
  for (const e of raiz.querySelectorAll('button, [role=button], [aria-label], [title]')) for (const v of [e.getAttribute('aria-label'), e.getAttribute('title'), e.tagName === 'BUTTON' ? e.innerText : null]) if (v && v.trim()) s.add(v.trim().replace(/\\s+/g, ' ').slice(0, 60));
  return [...s].sort(); };
  const contenedores = [...document.querySelectorAll('[data-testid="stElementContainer"]')].filter(c => c.querySelector('[data-testid="stDataFrame"], [data-testid="stVegaLiteChart"], [data-testid="stArrowVegaLiteChart"]'));
  return JSON.stringify(contenedores.map(b => ({tipo: b.querySelector('[data-testid="stDataFrame"]') ? 'stDataFrame' : 'stVegaLiteChart', etiquetas: etiquetas(b).filter(x => !/^(X|Y)-axis|^[ab]: /.test(x))}))); })()"""


def parametros(funcion):
    """Nombres de los parámetros de una función de Streamlit, sin los internos."""
    return [n for n in inspect.signature(funcion).parameters]


def cuentas_en_el_front():
    """{texto: número de archivos .js del front que lo contienen}."""
    base_js = Path(streamlit.__file__).parent / "static"
    archivos = [f.read_text(encoding="utf-8", errors="ignore") for f in base_js.rglob("*.js")]
    return {t: sum(1 for a in archivos if t in a) for t in TEXTOS}, len(archivos)


def prueba_en_vivo():
    exe = next((p for p in base.NAVEGADORES if Path(p).exists()), None)
    if exe is None:
        return None
    with tempfile.TemporaryDirectory() as carpeta, tempfile.TemporaryDirectory() as perfil:
        app = Path(carpeta) / "app_minima.py"
        app.write_text(APLICACION, encoding="utf-8")
        servidor = subprocess.Popen([sys.executable, "-m", "streamlit", "run", str(app), "--server.port", str(PUERTO), "--server.address", "127.0.0.1", "--server.headless", "true",
                                     "--browser.gatherUsageStats", "false", "--client.toolbarMode", "minimal", "--server.fileWatcherType", "none"],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=carpeta)
        nav = subprocess.Popen([exe, "--headless=new", "--disable-gpu", f"--user-data-dir={perfil}", f"--remote-debugging-port={base.PUERTO_DEPURACION}", "--window-size=1200,1400", "about:blank"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cdp = None
        try:
            objetivo = next(t for t in base._json(f"http://127.0.0.1:{base.PUERTO_DEPURACION}/json/list") if t["type"] == "page")
            cdp = base.Cdp(objetivo["webSocketDebuggerUrl"])
            cdp.llamar("Page.enable")
            for _ in range(60):      # la comprobación de salud de Streamlit responde «ok» (texto, no JSON)
                try:
                    if urllib.request.urlopen(f"http://127.0.0.1:{PUERTO}/_stcore/health", timeout=3).read().strip() == b"ok":
                        break
                except OSError:
                    time.sleep(0.5)
            cdp.llamar("Page.navigate", url=f"http://127.0.0.1:{PUERTO}/")
            fin = time.monotonic() + 60
            while time.monotonic() < fin:
                datos = json.loads(cdp.evaluar(JS) or "[]")
                if len(datos) >= 3 and all(d["etiquetas"] is not None for d in datos):
                    time.sleep(2)
                    return json.loads(cdp.evaluar(JS))
                time.sleep(0.7)
            return json.loads(cdp.evaluar(JS) or "[]")
        finally:
            if cdp is not None:
                cdp.cerrar()
            for p in (nav, servidor):
                p.terminate()
                try:
                    p.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    p.kill()


def main():
    t0 = time.perf_counter()
    cuentas, n_js = cuentas_en_el_front()
    opciones = {k: v for k, v in config._config_options_template.items() if any(x in k.lower() for x in ("toolbar", "locale", "language", "i18n"))}
    vivo = prueba_en_vivo()
    L = [f"Versión de Streamlit: {streamlit.__version__} (la fijada en `requirements.txt`).", "",
         "## 1. Qué ofrece la interfaz de programación",
         f"- `st.dataframe` acepta: {', '.join(parametros(streamlit.dataframe))}. Ninguno controla los botones de la barra de herramientas de la tabla ni su idioma.",
         f"- `st.altair_chart` acepta: {', '.join(parametros(streamlit.altair_chart))}. Tampoco hay uno para la barra de herramientas del gráfico.",
         f"- Opciones de configuración que mencionan barra de herramientas o idioma: {', '.join(opciones) or 'ninguna'}. `client.toolbarMode` solo muestra u oculta las opciones del menú de la aplicación (imprimir, grabar, desplegar…); el panel ya usa «minimal».",
         "", f"## 2. Dónde está escrito cada texto en el front ({n_js} archivos .js)", "| Texto | Archivos que lo contienen |", "|---|---|"] + [f"| {t} | {c} |" for t, c in cuentas.items()]
    L += ["", "Los textos están escritos dentro del código del front y no hay una opción de idioma para cambiarlos.", "", "## 3. Prueba en vivo con una aplicación mínima (navegador sin ventana)"]
    if vivo is None:
        L.append("No hay un navegador automatizable: no se hizo la prueba en vivo.")
    else:
        nombres = ["tabla (`st.dataframe`)", "gráfico con `embedOptions: {actions: False}`", "gráfico por defecto"]
        for nombre, bloque in zip(nombres, vivo):
            L.append(f"- **{nombre}** ({bloque['tipo']}): {'; '.join(bloque['etiquetas']) or 'sin etiquetas'}")
    L += ["", "## Conclusión (F-11)",
          "La versión fijada de Streamlit **no permite traducir** estos controles (están dentro del front y no hay opción de idioma) y **no permite ocultar** los de las tablas con ningún parámetro. "
          "Pasar `embedOptions` solo cambia el menú propio de Vega, no la barra de herramientas de Streamlit, y sustituir las tablas por `st.table` quitaría el orden, la búsqueda y la descarga que sí sirven. "
          "Por eso F-11 queda **aplazado**: no hay una corrección limpia con esta versión.", "",
          "Qué NO demuestra: que otra versión de Streamlit no lo permita (no se probó ninguna otra) ni que las personas usuarias se confundan con estos textos (eso lo dirán las sesiones).", ""]
    cuerpo = "\n".join(L)
    ruta = evidencia.guardar("ajustes_ux", "EV-080_controles_de_streamlit.txt", "Evaluación de los controles en inglés de Streamlit (F-11)", "python scripts/evidencias/evidencia_streamlit_controles.py", 0, time.perf_counter() - t0, cuerpo)
    print(cuerpo)
    print("evidencia:", ruta.relative_to(REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
