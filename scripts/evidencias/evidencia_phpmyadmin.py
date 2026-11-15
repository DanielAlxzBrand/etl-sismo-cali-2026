"""phpMyAdmin en vivo con la cuenta de solo lectura: tablas, claves foráneas, conteos iguales a Gold y escrituras rechazadas por MySQL.

Uso, desde la raíz del repositorio (con Docker Desktop encendido, MySQL con la cuenta `sismo_lectura` creada y su `.env`):
    python scripts/evidencias/evidencia_phpmyadmin.py [--salida CARPETA] [--puerto 8791]

Qué hace: levanta phpMyAdmin con `servicios/phpmyadmin/docker-compose.yaml` en un proyecto de Docker propio (`servicios_prueba_pma`) y en un puerto aparte, abre un navegador sin ventana
por DevTools, entra con la cuenta de solo lectura, recorre las siete tablas de `sismo_cali`, su estructura y relaciones, cuenta las filas con SQL de lectura y las compara con los
CSV de Gold, intenta un `INSERT`, un `DROP`, un `UPDATE` y un `DELETE` (MySQL debe rechazarlos por privilegios) y vuelve a contar. Escribe `resumen_phpmyadmin.json` (sin secretos)
y las capturas PNG en `--salida` (por defecto, una carpeta dentro de la carpeta temporal del sistema); después baja solo lo que levantó.
Por qué es así: es la evidencia de que la cuenta de solo lectura no puede escribir y de que lo que se ve en el navegador coincide con Gold (EV-085).
Qué NO hace: no toca `data/`, no escribe en MySQL (las escrituras que intenta son las que debe rechazar), no usa ni baja ningún otro proyecto de Docker y no imprime ni guarda
credenciales: se leen de `.env` en memoria y se comprueba que no aparezcan en el texto de la página.
Última ejecución real: EV-085, con el script de la sesión del que sale este archivo; esta versión solo se validó de forma estática (Docker estaba apagado).
"""
import argparse
import base64
import csv
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT))
import evidencia_capturas_panel as base  # noqa: E402
from dotenv import dotenv_values  # noqa: E402

NOMBRE = "servicios_prueba_pma"
PUERTO_DEPURACION = 9335
RES = {}
CONFIG = {"puerto": 8791, "capturas": Path(tempfile.gettempdir()) / "capturas_pma"}


def url():
    """Dirección base de phpMyAdmin en el puerto elegido."""
    return f"http://127.0.0.1:{CONFIG['puerto']}/"


def sh(cmd, **kw):
    """Corre un comando con el puerto de phpMyAdmin en el entorno y devuelve el resultado."""
    entorno = {**os.environ, "PMA_PUERTO": str(CONFIG["puerto"]), "PYTHONIOENCODING": "utf-8"}
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=entorno, **kw)


def compose():
    """Prefijo del comando de Docker Compose con el proyecto propio y el compose versionado de phpMyAdmin."""
    return ["docker", "compose", "-p", NOMBRE, "-f", str(ROOT / "servicios" / "phpmyadmin" / "docker-compose.yaml")]


class CdpConDialogos(base.Cdp):
    """Igual que Cdp, pero guarda los avisos (alert, confirm) que abre la página y los acepta, para que no dejen colgado el navegador."""
    avisos = []

    def evaluar(self, expresion):
        """Si la página se está recargando en ese momento, la evaluación no devuelve valor: se trata como «todavía no»."""
        try:
            return super().evaluar(expresion)
        except (KeyError, RuntimeError):
            return None

    def llamar(self, metodo, **params):
        """Llama a un método de DevTools y acepta los diálogos de la página que aparezcan mientras espera la respuesta."""
        self.n += 1
        self.ws.send(json.dumps({"id": self.n, "method": metodo, "params": params}))
        while True:
            r = json.loads(self.ws.recv(timeout=60))
            if r.get("method") == "Page.javascriptDialogOpening":
                self.avisos.append(r["params"].get("message", "")[:200])
                self.n += 1
                self.ws.send(json.dumps({"id": self.n, "method": "Page.handleJavaScriptDialog", "params": {"accept": True}}))
                continue
            if r.get("id") == self.n:
                if "error" in r:
                    raise RuntimeError(f"{metodo}: {r['error'].get('message')}")
                return r.get("result", {})


def captura(cdp, nombre, ancho=1280, alto=None):
    """Guarda una captura de la página actual con el ancho y alto indicados."""
    h = alto or int(cdp.evaluar("Math.min(Math.max(document.documentElement.scrollHeight, 600), 2600)"))
    cdp.llamar("Emulation.setDeviceMetricsOverride", width=ancho, height=h, deviceScaleFactor=1, mobile=False)
    time.sleep(0.8)
    try:
        png = base64.b64decode(cdp.llamar("Page.captureScreenshot", format="png")["data"])
    except TimeoutError:
        RES.setdefault("capturas_omitidas", []).append(nombre)
        return
    (CONFIG["capturas"] / nombre).write_bytes(png)


def ir(cdp, destino, espera="document.readyState === 'complete'"):
    """Navega a una dirección y espera hasta 30 s a que se cumpla la condición de JavaScript."""
    cdp.llamar("Page.navigate", url=destino)
    fin = time.monotonic() + 30
    time.sleep(1.2)
    while time.monotonic() < fin:
        if cdp.evaluar(espera):
            return
        time.sleep(0.4)


def texto(cdp):
    """Texto visible de la página."""
    return cdp.evaluar("document.body.innerText") or ""


def consulta(cdp, tk, sql):
    """Abre la pestaña SQL de sismo_cali, escribe la consulta en el editor y pulsa «Continuar»; espera la tabla de resultados o un mensaje de error."""
    ir(cdp, f"{url()}index.php?route=/database/sql&db=sismo_cali&server=1&token={tk}", "!!document.querySelector('.CodeMirror') || !!document.querySelector('#sqlquery')")
    time.sleep(1.0)
    # se teclea en el editor como lo haría una persona: se enfoca el cuadro de texto de CodeMirror y se inserta el texto
    cdp.evaluar("(() => { const e = document.querySelector('.CodeMirror textarea') || document.querySelector('#sqlquery'); e.focus(); })()")
    cdp.llamar("Input.insertText", text=sql)
    time.sleep(0.5)
    RES.setdefault("largo_consulta_en_el_editor", []).append(cdp.evaluar("(document.querySelector('.CodeMirror-code') || document.querySelector('#sqlquery')).textContent.length"))
    cdp.evaluar("setTimeout(() => (document.querySelector('#button_submit_query') || document.querySelector('input[type=submit][name=SQL]')).click(), 50); 1")
    fin = time.monotonic() + 25
    while time.monotonic() < fin:
        time.sleep(0.7)
        if cdp.evaluar("!!document.querySelector('table.table_results') || !!document.querySelector('.alert-danger, .error, div.alert')"):
            break
    time.sleep(0.8)


def conteos_de_la_tabla(cdp):
    """{tabla: filas} leído de la última tabla de resultados."""
    filas = cdp.evaluar("[...document.querySelectorAll('table.table_results tbody tr')].map(tr => [...tr.querySelectorAll('td')].map(td => td.innerText.trim()).filter(Boolean))")
    return {f[-2]: int(f[-1].replace('.', '').replace(',', '')) for f in filas if len(f) >= 2 and f[-1].replace('.', '').replace(',', '').isdigit()}


def filas_de_csv(ruta):
    """Filas de datos (sin la cabecera) de un CSV del repositorio."""
    with open(ROOT / ruta, encoding="utf-8", newline="") as f:
        return sum(1 for _ in csv.reader(f)) - 1


def entrar(cdp, usuario, clave):
    """Teclea las credenciales (valores solo en memoria), entra y devuelve el token de la sesión de phpMyAdmin."""
    ir(cdp, url(), "!!document.querySelector('#input_username')")
    captura(cdp, "01_acceso.png", alto=620)
    cdp.evaluar("(() => { document.querySelector('#input_username').value = " + json.dumps(usuario) + "; document.querySelector('#input_password').value = " + json.dumps(clave) + "; })()")
    cdp.evaluar("document.querySelector('#input_go').click()")
    fin = time.monotonic() + 30
    while time.monotonic() < fin and not cdp.evaluar("!!document.querySelector('a[href*=\"token=\"]')"):
        time.sleep(0.5)
    token = None
    for expresion in ("(document.querySelector('a[href*=\"token=\"]') ? (document.querySelector('a[href*=\"token=\"]').href.match(/token=([^&]+)/) || [])[1] : null)",
                      "(document.querySelector('input[name=token]') || {}).value", "(window.CommonParams && window.CommonParams.get('token'))",
                      "new URLSearchParams(location.search).get('token')", "(document.documentElement.innerHTML.match(/token[\"']?\\s*[:=]\\s*[\"']([0-9a-f]{32})/) || [])[1]"):
        token = cdp.evaluar(expresion)
        if token:
            break
    RES["entro"] = bool(token)
    RES["titulo_tras_entrar"] = cdp.evaluar("document.title")
    return urllib.parse.quote(token or "")


def recorrido(cdp, tk, secretos):
    """Tablas, estructura, relaciones, conteos, la tabla corrida y las cuatro escrituras que MySQL debe rechazar."""
    ir(cdp, f"{url()}index.php?route=/database/structure&db=sismo_cali&server=1&token={tk}", "!!document.querySelector('table')")
    RES["tablas_vistas"] = sorted(set(re.findall(r"\b(barrio_estrato|comuna|construccion|corrida_archivo|corrida|kpi_sensibilidad|kpi)\b", texto(cdp))))
    captura(cdp, "02_tablas_de_sismo_cali.png")
    ir(cdp, f"{url()}index.php?route=/table/structure&db=sismo_cali&table=construccion&server=1&token={tk}", "!!document.querySelector('table')")
    captura(cdp, "03_estructura_construccion.png")
    ir(cdp, f"{url()}index.php?route=/table/relation&db=sismo_cali&table=construccion&server=1&token={tk}", "document.readyState==='complete'")
    t = texto(cdp)
    RES["relaciones_texto_clave"] = "FOREIGN KEY" in t.upper() or "restricciones" in t.lower() or "foreign" in t.lower()
    captura(cdp, "04_relaciones_construccion.png")
    sql = ("SELECT 'barrio_estrato' AS tabla, COUNT(*) AS filas FROM barrio_estrato UNION ALL SELECT 'comuna', COUNT(*) FROM comuna UNION ALL SELECT 'construccion', COUNT(*) FROM construccion "
           "UNION ALL SELECT 'corrida', COUNT(*) FROM corrida UNION ALL SELECT 'corrida_archivo', COUNT(*) FROM corrida_archivo UNION ALL SELECT 'kpi', COUNT(*) FROM kpi UNION ALL SELECT 'kpi_sensibilidad', COUNT(*) FROM kpi_sensibilidad")
    consulta(cdp, tk, sql)
    conteos = conteos_de_la_tabla(cdp)
    RES["conteos_mysql"] = conteos
    captura(cdp, "05_conteos_por_tabla.png", alto=700)
    RES["conteos_csv"] = {"gold_final.csv": filas_de_csv("data/gold/gold_final.csv"), "kpis_gold.csv": filas_de_csv("data/gold/kpis_gold.csv"),
                          "kpis_sensibilidad.csv": filas_de_csv("data/gold/kpis_sensibilidad.csv")}
    RES["iguales_a_gold"] = (conteos.get("construccion") == RES["conteos_csv"]["gold_final.csv"] and conteos.get("kpi") == RES["conteos_csv"]["kpis_gold.csv"]
                             and conteos.get("kpi_sensibilidad") == RES["conteos_csv"]["kpis_sensibilidad.csv"])
    consulta(cdp, tk, "SELECT * FROM corrida")      # se comprueba antes que no muestre rutas ni usuario
    t = texto(cdp)
    RES["corrida_filas"] = len(cdp.evaluar("[...document.querySelectorAll('table.table_results tbody tr')]") or [])
    RES["corrida_sin_rutas"] = not re.search(r"\b[A-Z]:\\[A-Za-z]|\bUsers\b", t)
    if RES["corrida_sin_rutas"]:
        captura(cdp, "06_tabla_corrida.png", alto=520)
    rechazos = {}
    for nombre, q in (("insert", "INSERT INTO corrida (id) VALUES (999999)"), ("drop", "DROP TABLE comuna"), ("update", "UPDATE comuna SET nombre = 'x'"), ("delete", "DELETE FROM kpi")):
        consulta(cdp, tk, q)
        t = texto(cdp)
        mensaje = re.search(r"#\d{4}[^\n]{0,120}", t)
        rechazos[nombre] = {"denegado": bool(re.search(r"denied|denegad|#1142|#1044|#1227", t, re.I)), "mensaje": mensaje.group(0) if mensaje else ""}
        if nombre in ("insert", "drop"):
            captura(cdp, f"07_{nombre}_rechazado.png", alto=640)
    RES["escrituras"] = rechazos
    consulta(cdp, tk, sql)
    RES["conteos_iguales_despues_de_las_escrituras"] = conteos_de_la_tabla(cdp) == conteos
    RES["avisos_de_la_pagina"] = CdpConDialogos.avisos
    RES["ningun_secreto_en_el_texto"] = not any(s in texto(cdp) for s in secretos)


def main(argv=None):
    """Levanta phpMyAdmin, hace el recorrido y baja lo levantado; escribe el resumen sin secretos."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--salida", type=Path, default=Path(tempfile.gettempdir()) / "evidencia_phpmyadmin", help="carpeta del resumen y de las capturas")
    ap.add_argument("--puerto", type=int, default=8791, help="puerto local de phpMyAdmin")
    args = ap.parse_args(argv)
    CONFIG["puerto"] = args.puerto
    CONFIG["capturas"] = args.salida / "capturas"
    e = dotenv_values(ROOT / ".env")
    usuario, clave = e.get("MYSQL_LECTURA_USER"), e.get("MYSQL_LECTURA_PASSWORD")
    if not usuario or not clave:
        raise SystemExit("faltan MYSQL_LECTURA_USER y MYSQL_LECTURA_PASSWORD en .env")
    secretos = [v for k, v in e.items() if v and len(v) >= 6 and re.search("PASSWORD|TOKEN|SECRET|KEY", k, re.I)]
    CONFIG["capturas"].mkdir(parents=True, exist_ok=True)
    for p in CONFIG["capturas"].glob("*"):
        p.unlink()
    exe = next(p for p in base.NAVEGADORES if Path(p).exists())
    nav = cdp = None
    try:
        t0 = time.perf_counter()
        r = sh(compose() + ["up", "-d"])
        RES["up_codigo"], RES["up_segundos"] = r.returncode, round(time.perf_counter() - t0, 1)
        t0 = time.perf_counter()
        for _ in range(60):
            try:
                RES["login_http"] = urllib.request.urlopen(url(), timeout=5).status
                break
            except OSError:
                time.sleep(1)
        RES["pagina_de_acceso_segundos"] = round(time.perf_counter() - t0, 1)
        time.sleep(30)     # en reposo antes de medir la memoria
        m = sh(["docker", "stats", "--no-stream", "--format", "{{.Name}}|{{.MemUsage}}"])
        RES["memoria"] = [linea for linea in m.stdout.splitlines() if "phpmyadmin" in linea]
        perfil = tempfile.mkdtemp()
        nav = subprocess.Popen([exe, "--headless=new", "--disable-gpu", f"--user-data-dir={perfil}", f"--remote-debugging-port={PUERTO_DEPURACION}", "--window-size=1280,900", "about:blank"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        destino = next(t for t in base._json(f"http://127.0.0.1:{PUERTO_DEPURACION}/json/list") if t["type"] == "page")
        cdp = CdpConDialogos(destino["webSocketDebuggerUrl"])
        cdp.llamar("Page.enable")
        tk = entrar(cdp, usuario, clave)
        recorrido(cdp, tk, secretos)
    finally:
        if cdp is not None:
            cdp.cerrar()
        if nav is not None:
            nav.terminate()
            try:
                nav.wait(timeout=15)
            except subprocess.TimeoutExpired:
                nav.kill()
        d = sh(compose() + ["down", "--remove-orphans"])
        RES["down_codigo"] = d.returncode
        (args.salida / "resumen_phpmyadmin.json").write_text(json.dumps(RES, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(RES, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
