"""Capturas del panel definitivo (D115 a D117) obtenidas ejecutando el panel real con su API, en el navegador sin ventana (Edge o Chrome por el protocolo DevTools).

Uso:  python scripts/evidencias/capturas_panel_definitivo.py [--nombre EV-128_capturas_definitivas_del_panel.txt]
Qué hace: arranca el lanzador oficial (API y panel en 127.0.0.1, almacenamiento SQLite), recorre las ocho páginas con una ventana de 1440 por 900 píxeles, guarda una captura de cada una,
más capturas de las herramientas de lectura y de estados elegidos (guía, curiosidad, modo presentación, vista de puntos, fila destacada, fila elegida) y cuatro capturas en pantalla de móvil.
Las imágenes se guardan optimizadas (paleta de 256 colores, sin retoques de contenido) en `docs/img/panel/`; cuatro de ellas se copian a `docs/img/readme/` para el README. Escribe un registro
en `docs/evidencias/frontend/` con el origen, el tamaño y el sha256 de cada imagen y una comprobación del texto de cada página (alcance visible, fecha de corte, sin errores en pantalla).
Qué NO hace: no toma datos de ninguna otra fuente que la API del proyecto, no instala nada, no muestra credenciales y no sustituye las capturas históricas de `docs/evidencias/`.
Para reemplazar las capturas cuando cambie la interfaz basta volver a ejecutarlo y registrar de nuevo el resultado en el manifiesto de evidencias.
"""
import argparse
import base64
import hashlib
import io
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
from PIL import Image  # noqa: E402

from src.panel import registro  # noqa: E402

DESTINO = REPO / "docs" / "img" / "panel"
DESTINO_README = REPO / "docs" / "img" / "readme"
ANCHO, ALTO = 1440, 900
MOVIL = (390, 844)
CORTE = "2026-09-02"
PARA_EL_README = {"escritorio_02_estratos": "panel_principal", "herramienta_01_respuesta_guia": "panel_guia_de_lectura", "estado_06_construcciones_fila_elegida": "panel_construcciones",
                  "movil_00_estratos_y_construcciones": "panel_movil"}
LIMPIAR = "sessionStorage.clear();"
CLIC_RADIO = "const r = document.querySelectorAll('.st-key-lienzo [name=categoria]')[%d]; if (r) r.click();"
DESPLAZAR = """(() => { const m = document.querySelector('[data-testid="stMain"]'); const e = %s; if (e) { e.scrollIntoView({block: 'start'}); m.scrollTop -= %d; } return !!e; })()"""
BOTON = "document.querySelector('.st-key-lienzo [data-accion=\"%s\"]').click();"
ENCABEZADO = "[...document.querySelectorAll('h2,h3')].find(x => x.textContent.includes(%s))"


def optimizar(png_bytes, ancho_maximo=None):
    """Imagen en paleta de 256 colores y PNG optimizado; reduce el tamaño sin cambiar lo que se lee."""
    im = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    if ancho_maximo and im.width > ancho_maximo:
        im = im.resize((ancho_maximo, round(im.height * ancho_maximo / im.width)), Image.LANCZOS)
    paleta = im.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    salida = io.BytesIO()
    paleta.save(salida, format="PNG", optimize=True)
    return salida.getvalue(), im.size


def ejecutar(cdp, js):
    return cdp.evaluar(js)


def pagina(cdp, urls, p, indice, ancho=ANCHO, alto=ALTO, movil=False):
    cdp.llamar("Emulation.setDeviceMetricsOverride", width=ancho, height=alto, deviceScaleFactor=2 if movil else 1, mobile=movil)
    cdp.llamar("Page.navigate", url=f"{urls['panel']}/" + ("" if indice == 0 else p.url_path))
    esperar(cdp, p.id)
    time.sleep(1.5)
    ejecutar(cdp, LIMPIAR)


def esperar(cdp, pagina_id, limite=75):
    """Espera a que Streamlit termine de dibujar la página: recuadro de alcance, sin «Running», altura estable y, donde el gráfico es nativo, el gráfico dibujado."""
    fin, estable, ultima = time.monotonic() + limite, 0, None
    while time.monotonic() < fin:
        s = json.loads(cdp.evaluar(base.SONDA))
        listo = "Alcance." in s["texto"] and not s["corriendo"] and (pagina_id not in {"sensibilidades", "construcciones"} or s["lienzos"] >= 1)
        estable = estable + 1 if listo and ultima and abs(s["alto"] - ultima["alto"]) < 2 else 0
        ultima = s
        if estable >= 3:
            return s
        time.sleep(0.7)
    raise RuntimeError(f"la página {pagina_id} no terminó de dibujarse a tiempo")


def captura(cdp):
    return base64.b64decode(cdp.llamar("Page.captureScreenshot", format="png")["data"])


def revisar(cdp, p):
    """Texto visible de la página ya dibujada y sus comprobaciones: alcance, fecha de corte real y ningún error en pantalla."""
    texto = json.loads(cdp.evaluar(base.SONDA))["texto"]
    errores = [x for x in ("Traceback", "Exception", "No se pudo conectar", "Page not found") if x in texto]
    return {"alcance": "Alcance." in texto, "corte": CORTE in texto, "titulo": p.titulo in texto, "errores": errores}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nombre", default="EV-128_capturas_definitivas_del_panel.txt")
    a = ap.parse_args()
    t0 = time.perf_counter()
    exe = next((x for x in base.NAVEGADORES if Path(x).exists()), None)
    if exe is None:
        print("No hay un navegador automatizable (Edge o Chrome): no se generan capturas.")
        return 1
    DESTINO.mkdir(parents=True, exist_ok=True)
    registro_filas, revision, ok, hechas = [], [], True, {}

    def guardar(nombre, png, que, ancho_maximo=None):
        datos, tam = optimizar(png, ancho_maximo)
        ruta = DESTINO / f"{nombre}.png"
        ruta.write_bytes(datos)
        hechas[nombre] = datos
        registro_filas.append(f"| `docs/img/panel/{nombre}.png` | {tam[0]} x {tam[1]} | {len(datos) // 1024} KB | {hashlib.sha256(datos).hexdigest()} | {que} |")

    with tempfile.TemporaryDirectory() as perfil, panel_vivo.panel_en_marcha(duracion=1500) as (urls, _, _):
        navegador = subprocess.Popen([exe, "--headless=new", "--disable-gpu", f"--user-data-dir={perfil}", f"--remote-debugging-port={base.PUERTO_DEPURACION}", f"--window-size={ANCHO},{ALTO}",
                                      "--force-color-profile=srgb", "--hide-scrollbars", "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cdp = None
        try:
            version = base._json(f"http://127.0.0.1:{base.PUERTO_DEPURACION}/json/version")
            objetivo = next(t for t in base._json(f"http://127.0.0.1:{base.PUERTO_DEPURACION}/json/list") if t["type"] == "page")
            cdp = base.Cdp(objetivo["webSocketDebuggerUrl"])
            cdp.llamar("Page.enable")
            cdp.llamar("Emulation.setFocusEmulationEnabled", enabled=True)      # sin ventana, el navegador marca la página como oculta y Streamlit deja de dibujar las tablas
            cdp.llamar("Page.bringToFront")
            cdp.llamar("Emulation.setEmulatedMedia", features=[{"name": "prefers-color-scheme", "value": "light"}])
            salud = json.loads(__import__("urllib.request", fromlist=["urlopen"]).urlopen(urls["api"] + "/health", timeout=10).read())
            ok &= salud.get("estado") == "ok" and salud.get("fecha_corte") == CORTE
            paginas = list(registro.PAGINAS)
            por_id = {p.id: (i, p) for i, p in enumerate(paginas)}

            # 1. las ocho páginas, vista superior a 1440 x 900
            for n, (i, p) in enumerate(por_id.values(), 1):
                pagina(cdp, urls, p, i)
                r = revisar(cdp, p)
                ok &= r["alcance"] and r["corte"] and r["titulo"] and not r["errores"]
                revision.append(f"| {p.titulo} | {'sí' if r['alcance'] else 'NO'} | {'sí' if r['corte'] else 'NO'} | {', '.join(r['errores']) or 'ninguno'} |")
                guardar(f"escritorio_{n:02d}_{p.id}", captura(cdp), f"{p.titulo}, vista superior de escritorio")

            # 2. herramientas de lectura y estados elegidos
            def estado(nombre, id_pagina, js, que, desplazar=None):
                nonlocal ok
                i, p = por_id[id_pagina]
                pagina(cdp, urls, p, i)
                ejecutar(cdp, f"(() => {{ {js} }})()")
                time.sleep(1.2)
                if desplazar:
                    ejecutar(cdp, desplazar)
                    time.sleep(0.8)
                guardar(nombre, captura(cdp), que)

            estado("herramienta_01_respuesta_guia", "respuesta", BOTON % "guia" + "".join(BOTON % "siguiente" for _ in range(3)), "Respuesta con la guía de lectura en el paso cuatro (conteos reales de K2)")
            estado("herramienta_02_estratos_curiosidad", "estratos", BOTON % "fichas", "Estratos con la primera curiosidad abierta")
            estado("herramienta_03_estratos_presentacion", "estratos", BOTON % "presentar", "Estratos en modo presentación (a pantalla completa, sin la barra lateral)")
            estado("estado_04_estratos_puntos_y_seleccion", "estratos", "document.querySelector('.st-key-lienzo input[name=vista][value=puntos]').click();" + CLIC_RADIO % 3,
                   "Estratos en la vista de puntos e intervalos con el Estrato 4 destacado", DESPLAZAR % (ENCABEZADO % "'Tasa por estrato'", 60))
            estado("estado_05_comunas_detalle", "comunas", CLIC_RADIO % 4 + "document.querySelector('.st-key-lienzo .lectura-fila summary').click();",
                   "Comunas con una comuna destacada y su lectura en palabras en el detalle", DESPLAZAR % (ENCABEZADO % "'Detalle por comuna'", 60))
            estado("estado_07_sensibilidades_mantel_haenszel", "sensibilidades", "", "Sensibilidades con la razón ajustada de Mantel-Haenszel y sus seis avisos",
                   DESPLAZAR % (ENCABEZADO % "'Razón ajustada'", 20))
            estado("estado_08_concentracion_k4", "concentracion", "", "Concentración con K4: Spearman, barrios incluidos y valor p de permutación", DESPLAZAR % (ENCABEZADO % "'K4'", 20))
            estado("estado_09_calidad_revision", "calidad", "", "Calidad de la llave con los códigos de barrio por revisar", DESPLAZAR % (ENCABEZADO % "'Códigos de barrio sin nombre'", 20))
            estado("estado_10_fuentes_limites", "fuentes", "", "Fuentes y sistema con los ocho puntos de lo que no se puede concluir", DESPLAZAR % (ENCABEZADO % "'Qué no se puede concluir'", 20))

            # fila elegida de Construcciones: se hace clic con el ratón en la casilla de la fila 2 de la tabla
            i, p = por_id["construcciones"]
            pagina(cdp, urls, p, i)
            for intento in range(3):      # la tabla de Streamlit se dibuja un poco después que el resto; si no aparece, se recarga la página
                for _ in range(40):
                    if cdp.evaluar("!!document.querySelector('[data-testid=stDataFrame] canvas')"):
                        break
                    time.sleep(0.5)
                else:
                    cdp.llamar("Page.reload")
                    esperar(cdp, "construcciones")
                    continue
                break
            ejecutar(cdp, "(() => { const e = document.querySelector('[data-testid=\"stDataFrame\"]'); e.scrollIntoView({block: 'start'}); document.querySelector('[data-testid=\"stMain\"]').scrollTop -= 160; })()")
            time.sleep(1.0)
            caja = json.loads(cdp.evaluar("(() => { const c = document.querySelector('[data-testid=\"stDataFrame\"] canvas'); const r = c.getBoundingClientRect(); return JSON.stringify({x: r.left, y: r.top}); })()"))
            x, y = caja["x"] + 17, caja["y"] + 35 + 35 * 1 + 17
            for tipo in ("mousePressed", "mouseReleased"):
                cdp.llamar("Input.dispatchMouseEvent", type=tipo, x=x, y=y, button="left", clickCount=1)
            time.sleep(2.5)
            texto = json.loads(cdp.evaluar(base.SONDA))["texto"]
            ok &= "La construcción " in texto and " está en el barrio " in texto
            ejecutar(cdp, DESPLAZAR % ("[...document.querySelectorAll('[data-testid=\"stExpander\"]')].find(e => e.textContent.includes('Qué significa esta fila'))", 480))
            time.sleep(1.0)
            guardar("estado_06_construcciones_fila_elegida", captura(cdp), "Construcciones con la fila 2 de la página elegida: «Qué significa esta fila», la descarga del CSV y la dispersión")

            # 3. pantalla de móvil
            movil = {}
            tabla_movil = ("document.querySelector('.st-key-contenido_analitico')", 40)
            for nombre, id_pagina, desplazar, que in (
                    ("movil_01_estratos_inicio", "estratos", "", "Estratos en pantalla de móvil: cabecera con su ícono, tarjetas de cifras y recuadro de alcance"),
                    ("movil_02_estratos_figura", "estratos", DESPLAZAR % (ENCABEZADO % "'Tasa por estrato'", 70), "Estratos en pantalla de móvil: figura de tasas con sus intervalos"),
                    ("movil_03_construcciones_tabla", "construcciones", DESPLAZAR % tabla_movil, "Construcciones en pantalla de móvil: filtros, página y tabla con selección"),
                    ("movil_04_sensibilidades_grafico", "sensibilidades", DESPLAZAR % tabla_movil, "Sensibilidades en pantalla de móvil: gráfico de diferencias (el título llega en dos líneas y la primera queda recortada por arriba)")):
                i, p = por_id[id_pagina]
                pagina(cdp, urls, p, i, *MOVIL, movil=True)
                if desplazar:
                    ejecutar(cdp, desplazar)
                time.sleep(1.2)
                guardar(nombre, captura(cdp), que)
                movil[nombre] = hechas[nombre]
            cdp.llamar("Emulation.clearDeviceMetricsOverride")
            lineas_cabecera = [f"Navegador: {Path(exe).name} {version['Browser']} sin ventana, por el protocolo DevTools; escritorio de {ANCHO} x {ALTO} px y móvil de {MOVIL[0]} x {MOVIL[1]} px con el doble de densidad.",
                               f"Panel: {urls['panel']} (lanzado con scripts/panel/ejecutar_panel.py; API en {urls['api']}, almacenamiento SQLite; /health: estado {salud.get('estado')}, corte {salud.get('fecha_corte')}).",
                               "Cada imagen es una «captura automatizada del navegador» del panel real con los datos de la API del proyecto; ninguna proviene del diseño de ejemplo ni muestra datos sensibles."]
        finally:
            if cdp is not None:
                cdp.cerrar()
            navegador.terminate()
            try:
                navegador.wait(timeout=15)
            except subprocess.TimeoutExpired:
                navegador.kill()

    # hoja de móvil para el README: las tres primeras capturas lado a lado
    ims = [Image.open(DESTINO / f"{n}.png").convert("RGB") for n in list(movil)[:3]]
    alto = max(i.height for i in ims)
    hoja = Image.new("RGB", (sum(i.width for i in ims) + 16 * (len(ims) + 1), alto + 32), "white")
    x = 16
    for im in ims:
        hoja.paste(im, (x, 16))
        x += im.width + 16
    buf = io.BytesIO()
    hoja.save(buf, format="PNG")
    guardar("movil_00_estratos_y_construcciones", buf.getvalue(), "Las tres primeras capturas de móvil lado a lado (para el README)", ancho_maximo=1400)
    DESTINO_README.mkdir(parents=True, exist_ok=True)
    for origen, destino in PARA_EL_README.items():
        (DESTINO_README / f"{destino}.png").write_bytes(hechas[origen])
    ok &= not panel_vivo.procesos_del_panel()
    cuerpo = "\n".join(lineas_cabecera + ["", "Comprobación del texto de cada página en el momento de la captura:", "", "| Página | Recuadro de alcance | Fecha de corte 2026-09-02 | Errores en pantalla |", "|---|---|---|---|"] + revision
                       + ["", "Imágenes (optimizadas a 256 colores; el sha256 es el del archivo guardado):", "", "| Archivo | Tamaño en píxeles | Peso | sha256 | Qué muestra |", "|---|---|---|---|---|"] + registro_filas
                       + ["", "Copias para el README (mismos bytes): " + ", ".join(f"`docs/img/readme/{d}.png` (de `{o}.png`)" for o, d in PARA_EL_README.items()) + ".",
                          f"Procesos del panel o de la API que quedan vivos al terminar: {len(panel_vivo.procesos_del_panel())}.",
                          f"Resultado: {'las ocho páginas se capturaron con su alcance visible, la fecha de corte real y sin avisos de error' if ok else 'HAY PÁGINAS CON PROBLEMAS: no usar estas capturas'}."]) + "\n"
    print(cuerpo)
    evidencia.guardar("frontend", a.nombre, "Capturas del panel definitivo (ocho páginas, herramientas de lectura, estados elegidos y móvil)",
                      "python scripts/evidencias/capturas_panel_definitivo.py (navegador sin ventana por DevTools)", 0 if ok else 1, time.perf_counter() - t0, cuerpo)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
