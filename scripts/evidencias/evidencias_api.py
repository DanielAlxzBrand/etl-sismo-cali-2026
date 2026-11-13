"""Evidencias de la capa de servicio (EV-013 a EV-024) en un clon temporal fuera del repositorio.

Uso (PowerShell, raíz del repositorio): .\\.venv\\Scripts\\python.exe scripts\\evidencias\\evidencias_api.py [--sin-venv-nuevo] [--minutos-venv 25]
Clona el commit actual a una carpeta temporal, ejecuta ahí todo lo que escribe o arranca y guarda las salidas SANEADAS (sin rutas de usuario,
usuario ni equipo) solo en docs/evidencias/api/. No escribe en data/ ni en ningún otro lugar del repositorio y borra la carpeta temporal.
"""
import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import signal
import socket
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO), str(Path(__file__).parent)]
from saneamiento import Saneador, quitar_hostname_junit  # noqa: E402
from src.logger import get_logger  # noqa: E402

log = get_logger(__name__)
TZ = ZoneInfo("America/Bogota")
PY = sys.executable
SALIDA = REPO / "docs" / "evidencias" / "api"
ENDPOINTS = [("health", "/health"), ("metadata", "/metadata"), ("fuentes", "/fuentes"), ("kpis", "/kpis"), ("kpis_K1", "/kpis/K1"), ("kpis_sensibilidad", "/kpis/sensibilidad"),
             ("comunas", "/comunas"), ("composicion", "/composicion"), ("construcciones", "/construcciones?limit=5"), ("calidad", "/calidad"), ("llave_revision", "/llave/revision")]
LIMITE_RESPUESTA = 50 * 1024
CALENTAMIENTO, REPETICIONES = 5, 50


def ahora():
    return datetime.now(TZ).isoformat(timespec="seconds")


def sh(cmd, cwd, timeout=None):
    t0 = time.perf_counter()
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    return r.returncode, r.stdout + r.stderr, time.perf_counter() - t0


def huellas(carpeta):
    return {p.relative_to(carpeta).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(carpeta.rglob("*")) if p.is_file()}


def resumen_pip(salida):
    """Resumen de la instalación: cuántos paquetes quedaron instalados (la lista completa son dependencias de Jupyter, pandas y similares)."""
    linea = next((l for l in salida.splitlines() if l.startswith("Successfully installed")), "")
    return f"{len(linea.split()) - 2} paquetes instalados (lista completa omitida)" if linea else "no se encontró el resumen de instalación"


def puerto_libre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sin-venv-nuevo", action="store_true")
    ap.add_argument("--minutos-venv", type=int, default=25)
    a = ap.parse_args()
    SALIDA.mkdir(parents=True, exist_ok=True)
    (SALIDA / "respuestas_api").mkdir(exist_ok=True)
    raiz_tmp = Path(tempfile.mkdtemp(prefix="evidencias_api_"))
    clon = raiz_tmp / "clon"
    san = Saneador(REPO, clon, raiz_tmp)
    resumen = {}

    def guardar(nombre, titulo, comando, codigo, dur, commit, cuerpo):
        cab = (f"# {titulo}\n- comando: `{comando}`\n- fecha: {ahora()} (America/Bogota)\n- código de salida: {codigo}\n- duración: {dur:.1f} s\n"
               f"- Python: {sys.version.split()[0]}\n- commit del clon: {commit}\n\n")
        san.escribir(SALIDA / nombre, cab + cuerpo)

    try:
        c, t, _ = sh(["git", "clone", "--quiet", "--no-hardlinks", str(REPO), str(clon)], raiz_tmp)
        assert c == 0, san(t)
        commit = sh(["git", "rev-parse", "--short", "HEAD"], clon)[1].strip()
        resumen["commit"] = commit
        inicial = huellas(clon / "data")

        # EV-013: paquetes instalados en el .venv del proyecto (solo lectura)
        t0 = time.perf_counter()
        c1, t1, _ = sh([PY, "-c", "import fastapi, uvicorn, httpx, pydantic, pydantic_core, starlette, sys;print('Python', sys.version.split()[0]);"
                        "[print(m.__name__, m.__version__) for m in (fastapi, uvicorn, httpx, pydantic, pydantic_core, starlette)]"], raiz_tmp)
        c2, t2, _ = sh([PY, "-m", "pip", "check"], raiz_tmp)
        import importlib.metadata as im
        etiquetas = " ".join(l for l in (im.distribution("pydantic-core").read_text("WHEEL") or "").splitlines() if l.startswith("Tag:"))
        guardar("EV-013_instalacion_paquetes.txt", "EV-013 · Paquetes instalados en el .venv del proyecto (fastapi, uvicorn, httpx)",
                "<VENV>\\Scripts\\python.exe -c \"import fastapi, uvicorn, httpx, ...\"; <VENV>\\Scripts\\python.exe -m pip check; lectura del WHEEL de pydantic-core",
                0 if (c1 == 0 and c2 == 0) else 1, time.perf_counter() - t0, commit,
                "importación y versiones:\n" + t1 + "\npip check:\n" + t2 + f"\netiqueta de la rueda de pydantic-core (dependencia de fastapi): {etiquetas}\n"
                "(cp313 = Python 3.13: la dependencia binaria tiene rueda para esta versión)\n\nLa instalación se hizo con `<VENV>\\Scripts\\python.exe -m pip install fastapi uvicorn httpx` "
                "(nunca en el Python global); httpx 0.28.1 ya estaba como dependencia de Jupyter.\n")

        # EV-014: pytest con junit (en el clon)
        xml = SALIDA / "junit_api.xml"
        c, t, d = sh([PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--junitxml={xml}"], clon)
        xml.write_text(san(quitar_hostname_junit(xml.read_text(encoding="utf-8"))), encoding="utf-8", newline="\n")
        guardar("EV-014_pytest.txt", "EV-014 · Pruebas en un clon temporal", "<VENV>\\Scripts\\python.exe -m pytest -q -p no:cacheprovider --junitxml=junit_api.xml (cwd: <CLON>)", c, d, commit, t)
        resumen["pytest"] = (c, [l for l in t.splitlines() if " passed" in l or " failed" in l][-1].strip("= "))
        tras_pytest = huellas(clon / "data")

        # EV-016/018/017: servicio real en 127.0.0.1
        puerto = puerto_libre()
        base = f"http://127.0.0.1:{puerto}"
        log_srv = open(raiz_tmp / "servicio.log", "w", encoding="utf-8")
        t0 = time.perf_counter()
        srv = subprocess.Popen([PY, "-m", "uvicorn", "src.api.app:app", "--host", "127.0.0.1", "--port", str(puerto)], cwd=clon, stdout=log_srv, stderr=subprocess.STDOUT,
                               text=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        indice, filas_lat = [], []
        try:
            with httpx.Client(base_url=base, timeout=15) as cli:
                for _ in range(100):
                    try:
                        if cli.get("/health").status_code == 200:
                            break
                    except httpx.HTTPError:
                        time.sleep(0.2)
                else:
                    raise RuntimeError("el servicio no arrancó")
                indice = [f"servicio: uvicorn src.api.app:app --host 127.0.0.1 --port <puerto libre>", ""]
                for nombre, ruta in ENDPOINTS:
                    r = cli.get(ruta)
                    cuerpo, corte = r.text, ""
                    if len(r.content) > LIMITE_RESPUESTA:
                        cuerpo = r.content[:LIMITE_RESPUESTA].decode("utf-8", errors="ignore")
                        corte = f" (respuesta recortada a los primeros {LIMITE_RESPUESTA} bytes de {len(r.content)})"
                    san.escribir(SALIDA / "respuestas_api" / f"{nombre}.json", cuerpo)
                    indice.append(f"GET {ruta} -> {r.status_code}, {len(r.content)} bytes{corte}; archivo respuestas_api/{nombre}.json")
                for etiqueta, ruta in [("error 404", "/kpis/K99"), ("error 422", "/construcciones?limit=999"), ("método no permitido", None)]:
                    r = cli.get(ruta) if ruta else cli.post("/kpis")
                    indice.append(f"{etiqueta}: {'GET ' + ruta if ruta else 'POST /kpis'} -> {r.status_code} {r.text}")
                oa = cli.get("/openapi.json")
                san.escribir(SALIDA / "openapi.json", json.dumps(oa.json(), ensure_ascii=False, indent=2) + "\n")
                metodos = sorted({m.upper() for p in oa.json()["paths"].values() for m in p})
                indice.append(f"GET /openapi.json -> {oa.status_code}; {len(oa.json()['paths'])} rutas; métodos: {', '.join(metodos)}")
                # latencia: calentamiento y repeticiones contra el servidor real (mediciones locales de una máquina)
                for nombre, ruta in ENDPOINTS:
                    for _ in range(CALENTAMIENTO):
                        cli.get(ruta)
                    ms = []
                    for _ in range(REPETICIONES):
                        t1 = time.perf_counter()
                        cli.get(ruta)
                        ms.append((time.perf_counter() - t1) * 1000)
                    ms.sort()
                    filas_lat.append([ruta, REPETICIONES, CALENTAMIENTO, round(statistics.median(ms), 2), round(ms[math.ceil(0.95 * len(ms)) - 1], 2), round(ms[-1], 2),
                                      "medición local en una máquina, servidor real en 127.0.0.1"])
                with open(SALIDA / "EV-018_latencia_api.csv", "w", encoding="utf-8", newline="") as f:
                    w = csv.writer(f, lineterminator="\n")
                    w.writerow(["endpoint", "repeticiones", "calentamiento", "mediana_ms", "p95_ms", "maximo_ms", "alcance"])
                    w.writerows(filas_lat)
                resumen["latencia"] = filas_lat
                navegador = next((p for p in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Google\Chrome\Application\chrome.exe") if Path(p).exists()), None)
                png = SALIDA / "EV-017_docs_navegador.png"
                if navegador:
                    perfil = raiz_tmp / "perfil"
                    cn, tn, dn = sh([navegador, "--headless=new", "--disable-gpu", f"--user-data-dir={perfil}", f"--screenshot={png}", "--window-size=1280,1600",
                                     "--virtual-time-budget=15000", f"{base}/docs"], raiz_tmp, timeout=120)
                    guardar("EV-017_docs_navegador.txt", "EV-017 · Captura automatizada del navegador (no es una captura manual)",
                            f"{Path(navegador).name} --headless=new --disable-gpu --user-data-dir=<TEMP>\\perfil --screenshot=EV-017_docs_navegador.png --window-size=1280,1600 --virtual-time-budget=15000 http://127.0.0.1:<puerto>/docs",
                            cn, dn, commit, f"navegador: {Path(navegador).name}; la imagen muestra la interfaz Swagger de /docs del servicio local.\nsalida del navegador (recortada):\n{tn[-300:]}\n")
                    resumen["captura"] = (cn, png.exists() and png.stat().st_size)
                else:
                    resumen["captura"] = "no hay Edge ni Chrome"
        finally:
            srv.send_signal(signal.CTRL_BREAK_EVENT)
            try:
                srv.wait(timeout=15)
            except subprocess.TimeoutExpired:
                srv.kill()
                srv.wait()
            log_srv.close()
        registro = (raiz_tmp / "servicio.log").read_text(encoding="utf-8", errors="replace").splitlines()
        indice.append(f"cierre ordenado con CTRL+BREAK: código de salida {srv.returncode} (en Windows uvicorn vuelve a emitir la señal tras cerrar; 3 es el código esperado)")
        indice += ["", "registro del servicio (inicio y cierre):"] + [l for l in registro if l.startswith("INFO:     ") and "HTTP/1.1" not in l] + ["...", "últimas solicitudes registradas:"] + [l for l in registro if " etl.app " in l][-3:]
        guardar("EV-016_respuestas_api.txt", "EV-016 · Servicio en 127.0.0.1 y una llamada a cada endpoint", "<VENV>\\Scripts\\python.exe -m uvicorn src.api.app:app --host 127.0.0.1 --port <libre>; GET a cada ruta",
                0, time.perf_counter() - t0, commit, "\n".join(indice) + "\n")

        # EV-015: sha256 de data/ y de la base: tras clonar, tras las pruebas y tras consultar con el servidor real
        final = huellas(clon / "data")
        iguales = inicial == tras_pytest == final
        db = {k: v for k, v in final.items() if k.endswith(".db")}
        cuerpo = [f"archivos de data/: tras clonar {len(inicial)}; tras las pruebas {len(tras_pytest)}; tras consultar con el servidor real {len(final)}", f"idénticos en los tres momentos: {iguales}",
                  f"base de datos (sha256 en los tres momentos): {[h.get(k) for h in (inicial, tras_pytest, final) for k in db]}", "", "sha256 de cada archivo (idéntico antes y después):"] + [f"{k} | {inicial[k]}" for k in sorted(inicial)]
        guardar("EV-015_sin_escritura_hashes.txt", "EV-015 · Sin escritura: sha256 de data/ antes y después de las pruebas y de consultar el servidor real", "sha256 de cada archivo de data/ y de etl_sismo.db en <CLON>",
                0 if iguales else 1, 0, commit, "\n".join(cuerpo) + "\n")
        resumen["hashes"] = (len(inicial), iguales)

        # EV-019: escáner sobre el clon, su historial y un zip armado con make_dist en carpeta temporal
        zdir = raiz_tmp / "zip_prueba"
        zdir.mkdir()
        c1, t1, _ = sh([PY, "-c", "import importlib.util as u;s=u.spec_from_file_location('md','scripts/make_dist.py');m=u.module_from_spec(s);s.loader.exec_module(m);"
                        "from pathlib import Path;m.empaquetar(Path('.'),Path(r'%s'))" % zdir], clon)
        zpath = sorted(zdir.glob("*.zip"))[-1]
        c2, t2, d2 = sh([PY, "scripts/escanear_secretos.py", "--zip", str(zpath)], clon)
        import zipfile
        with zipfile.ZipFile(zpath) as z:
            nombres = z.namelist()
        con_env = [n for n in nombres if Path(n).name == ".env"]
        guardar("EV-019_escaner_secretos.txt", "EV-019 · Escáner de secretos sobre el clon, su historial y un zip de prueba", "<VENV>\\Scripts\\python.exe scripts/escanear_secretos.py --zip <zip armado con scripts/make_dist.py en <TEMP>> (cwd: <CLON>)",
                c2, d2, commit, f"zip de prueba: {len(nombres)} archivos; archivos .env dentro del zip: {len(con_env)} (nunca se genera dist/)\n\nsalida del escáner (archivo:línea: patrón; nunca valores):\n{t2}")
        resumen["escaner"] = (c2, t2.strip().splitlines()[-1], len(nombres), len(con_env))

        # EV-020: entorno virtual nuevo con requirements.txt
        if a.sin_venv_nuevo:
            resumen["venv_nuevo"] = "omitido por parámetro"
        else:
            venv = raiz_tmp / "venv_nuevo"
            t0 = time.perf_counter()
            try:
                c3, _, _ = sh([PY, "-m", "venv", str(venv)], raiz_tmp)
                py2 = str(venv / "Scripts" / "python.exe")
                c4, t4, _ = sh([py2, "-m", "pip", "install", "--disable-pip-version-check", "-r", "requirements.txt"], clon, timeout=a.minutos_venv * 60)
                c5, t5, _ = sh([py2, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"], clon, timeout=600)
                n_col = sum(1 for l in t5.splitlines() if "::" in l)
                _, t6, _ = sh([py2, "-m", "pip", "freeze"], clon)
                claves = [l for l in t6.splitlines() if l.split("==")[0].lower() in ("fastapi", "uvicorn", "httpx", "pydantic", "starlette", "pydantic_core")]
                cuerpo = (f"crear entorno: código {c3}\ninstalar requirements.txt: código {c4}\nrecolección de pruebas con el entorno nuevo: código {c5}; pruebas recolectadas: {n_col}\n\n"
                          "paquetes de la capa de servicio instalados:\n" + "\n".join(claves) + "\n\nresumen de la instalación:\n" + resumen_pip(t4)
                          + "\n\nfin de la recolección (últimas líneas):\n" + "\n".join(t5.splitlines()[-3:]) + "\n")
                guardar("EV-020_requirements_entorno_nuevo.txt", "EV-020 · Entorno virtual nuevo con requirements.txt y recolección de pruebas",
                        "python -m venv <TEMP>\\venv_nuevo; <TEMP>\\venv_nuevo\\Scripts\\python.exe -m pip install -r requirements.txt; ... -m pytest --collect-only -q (cwd: <CLON>)",
                        0 if (c3 == 0 and c4 == 0 and c5 == 0) else 1, time.perf_counter() - t0, commit, cuerpo)
                resumen["venv_nuevo"] = (c3, c4, c5, n_col)
            except subprocess.TimeoutExpired:
                guardar("EV-020_requirements_entorno_nuevo.txt", "EV-020 · Entorno virtual nuevo con requirements.txt (NO completado)", "pip install -r requirements.txt en un entorno nuevo", 1, time.perf_counter() - t0, commit,
                        f"La instalación superó el tiempo máximo de {a.minutos_venv} minutos y se interrumpió; no se afirma que requirements.txt esté completo.\n")
                resumen["venv_nuevo"] = "tiempo agotado"
    finally:
        shutil.rmtree(raiz_tmp, ignore_errors=True)

    # imágenes renderizadas con matplotlib desde las salidas registradas
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fecha = ahora()
    pie = "Imagen generada a partir de la salida registrada; no es una captura de pantalla."

    def img(fig, nombre, titulo):
        fig.suptitle(f"{titulo}\nSalida real registrada el {fecha}", fontsize=11, fontweight="bold")
        fig.text(0.01, 0.0, pie, fontsize=7.5, style="italic")
        fig.savefig(SALIDA / nombre, dpi=200, bbox_inches="tight")
        plt.close(fig)

    filas = list(csv.DictReader(open(SALIDA / "EV-018_latencia_api.csv", encoding="utf-8")))
    fig, ax = plt.subplots(figsize=(9, 5))
    y = list(range(len(filas)))
    ax.barh([i + 0.2 for i in y], [float(f["mediana_ms"]) for f in filas], height=0.38, label="mediana", color="#4C78A8")
    ax.barh([i - 0.2 for i in y], [float(f["p95_ms"]) for f in filas], height=0.38, label="percentil 95", color="#F58518")
    ax.set_yticks(y)
    ax.set_yticklabels([f["endpoint"] for f in filas], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel(f"milisegundos ({REPETICIONES} repeticiones locales por endpoint; medición local de una máquina)")
    ax.set_ylabel("endpoint")
    ax.legend()
    ax.grid(axis="x", alpha=0.3)
    img(fig, "EV-021_latencias.png", "Latencia de la API por endpoint (servidor real en 127.0.0.1)")
    lineas = (SALIDA / "EV-015_sin_escritura_hashes.txt").read_text(encoding="utf-8").split("\n\n")[-1].strip().splitlines()[1:]

    def corto(r):
        p = r.split("/")
        return "/".join(p[:1] + ["..."] + p[-1:]) if r.startswith("bronze/") and len(p) > 3 else r
    fig, ax = plt.subplots(figsize=(10, 0.26 * len(lineas) + 1.3))
    ax.axis("off")
    tabla = ax.table(cellText=[[corto(l.split(" | ")[0]), l.split(" | ")[1][:16] + "...", "igual", "igual"] for l in lineas], colLabels=["archivo de data/", "sha256 (inicio)", "antes", "después"],
                     loc="center", cellLoc="left", colWidths=[0.5, 0.25, 0.12, 0.12])
    tabla.auto_set_font_size(False)
    tabla.set_fontsize(7.5)
    img(fig, "EV-022_hashes_antes_despues.png", "sha256 de data/ antes y después de consultar la API")
    res = resumen["pytest"][1]
    fig, ax = plt.subplots(figsize=(8, 2.6))
    ax.axis("off")
    ax.text(0.02, 0.6, res, fontsize=20, fontweight="bold", color="#2E7D32" if "failed" not in res else "#C62828", transform=ax.transAxes)
    ax.text(0.02, 0.25, "pytest -q -p no:cacheprovider en un clon temporal (sin red)", fontsize=10, transform=ax.transAxes)
    img(fig, "EV-023_pytest.png", "Resultado de las pruebas")
    ultima = resumen["escaner"][1]
    fig, ax = plt.subplots(figsize=(8, 2.6))
    ax.axis("off")
    ax.text(0.02, 0.6, ultima, fontsize=20, fontweight="bold", color="#2E7D32" if ultima == "hallazgos: 0" else "#C62828", transform=ax.transAxes)
    ax.text(0.02, 0.25, "escáner de secretos: clon, historial de git y zip de prueba; nunca se imprime un valor", fontsize=10, transform=ax.transAxes)
    img(fig, "EV-024_escaner.png", "Hallazgos del escáner de secretos")
    log.info("evidencias de la capa de servicio escritas en %s; resumen: %s", SALIDA.relative_to(REPO), json.dumps(resumen, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
