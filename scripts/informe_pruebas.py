"""Informe de pruebas con resultado esperado, obtenido y evidencia por prueba y por caso, más la cobertura y las métricas de validación del análisis. Un solo comando.

Uso:  python scripts/informe_pruebas.py [--sin-cobertura] [--salida CARPETA]
Ejecuta `pytest` (con `coverage` salvo --sin-cobertura) con salida JUnit y escribe docs/validacion/informe_pruebas.md, informe_pruebas.csv y cobertura_pruebas.csv.
Lo esperado de cada caso lo tomamos de la matriz (scripts/make_matriz_casos.py) y lo obtenido, de la ejecución real. Las métricas del análisis se recalculan desde los archivos de salida.
Solo escribe en la carpeta de salida (docs/validacion por defecto) y cambia las rutas de la máquina por marcadores.
"""
import argparse
import csv
import io
import json
import math
import os
import sqlite3
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import make_matriz_casos as matriz  # noqa: E402

# Motivo por el que un módulo queda con cobertura baja (menos de 70 %): la cobertura mide líneas ejecutadas dentro del proceso de pytest
UMBRAL_EXPLICACION = 70
MOTIVOS = {
    "scripts/make_modelo_datos.py": "genera el diccionario y el diagrama; el diccionario se comprueba contra el esquema y el dibujo con matplotlib no se prueba",
    "scripts/mysql/benchmark_lotes.py": "necesita MySQL en vivo; su evidencia es EV-030 y se prueban las reglas de elección y el percentil",
    "scripts/mysql/verificar_mysql.py": "batería contra MySQL en vivo; su evidencia es EV-028 y se prueban su operación solo sobre la base de prueba y el fallo sin servidor",
    "src/common.py": "descarga y escritura de Bronze (save_bronze): Bronze es inmutable y las pruebas no tocan la red ni data/bronze",
    "src/extract/extract_api.py": "descarga de la capa ArcGIS y de los polígonos: requiere red y crearía snapshots; las pruebas verifican lo ya descargado con el manifiesto",
    "src/extract/extract_excel.py": "descarga del CSV de estrato: requiere red; se prueba la lectura y limpieza con el archivo ya descargado",
    "src/load/conexion.py": "la rama de conexión real a MySQL se ejercita en vivo (EV-028); las pruebas cubren SQLite y los mensajes de error",
    "src/transform/build_gold.py": "cálculo de Gold y de sensibilidades: se ejecuta en un subproceso (test_pipeline_reproducible) que pytest-coverage no contabiliza; sus funciones estadísticas sí se prueban en proceso",
    "src/transform/clean_api.py": "limpieza de construcciones: se ejecuta en un subproceso (test_pipeline_reproducible) y se comprueba su salida byte a byte",
    "src/transform/integrate.py": "JOIN y reporte de calidad: se ejecuta en un subproceso (test_pipeline_reproducible) y se comprueba su salida byte a byte",
}
TZ = ZoneInfo("America/Bogota")


def ejecutar(sin_cobertura, tmp):
    """Corre pytest (con coverage) y devuelve (ruta del xml, ruta del json de cobertura o None, duración, código)."""
    xml = Path(tmp) / "junit.xml"
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "COVERAGE_FILE": str(Path(tmp) / ".coverage")}
    base = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--junitxml={xml}"]
    cmd = base if sin_cobertura else [sys.executable, "-m", "coverage", "run", "--source=src,scripts", "-m", *base[2:]]
    t0 = time.perf_counter()
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    dur = time.perf_counter() - t0
    js = None
    if not sin_cobertura:
        js = Path(tmp) / "cobertura.json"
        subprocess.run([sys.executable, "-m", "coverage", "json", "-o", str(js), "--quiet"], cwd=ROOT, capture_output=True, env=env)
    return xml, js, dur, r.returncode


def leer_junit(xml):
    """[{archivo, nombre, base, resultado, duracion, mensaje}] por prueba (las parametrizadas llevan su variante en `nombre`)."""
    pruebas = []
    for tc in ET.parse(xml).getroot().iter("testcase"):
        hijo = next((c for c in tc if c.tag in ("failure", "error", "skipped")), None)
        res = "passed" if hijo is None else {"failure": "failed", "error": "error", "skipped": "skipped"}[hijo.tag]
        archivo = tc.get("classname", "").replace(".", "/") + ".py"
        nombre = tc.get("name", "")
        pruebas.append({"archivo": archivo, "nombre": nombre, "base": nombre.split("[")[0], "resultado": res, "duracion": float(tc.get("time", 0)),
                        "mensaje": ((hijo.get("message") or "")[:160] if hijo is not None else "")})
    return pruebas


def resultado_por_caso(pruebas):
    """{nodeid base: (variantes, pasan, segundos, resultado)}: una prueba parametrizada pasa solo si pasan todas sus variantes."""
    d = {}
    for p in pruebas:
        k = f"{p['archivo']}::{p['base']}"
        v = d.setdefault(k, [0, 0, 0.0, []])
        v[0] += 1
        v[1] += p["resultado"] == "passed"
        v[2] += p["duracion"]
        if p["resultado"] != "passed":
            v[3].append(p["resultado"])
    return {k: (v[0], v[1], v[2], "passed" if v[0] == v[1] else ",".join(sorted(set(v[3])))) for k, v in d.items()}


def wilson(k, n, z=1.96):
    """Implementación propia del intervalo de Wilson al 95 % con z = 1,96, la convención del proyecto (independiente de src/), para el recálculo."""
    if n == 0:
        return float("nan"), float("nan")
    p, d = k / n, 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def metricas_analisis():
    """Recalcula K1 por estrato con SQL sobre una copia en memoria de gold_final.csv y con la fórmula de Wilson propia, y compara con kpis_gold.csv."""
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("CREATE TABLE g (estrato REAL, sin_datos TEXT, severo TEXT)")
        with open(ROOT / "data/gold/gold_final.csv", encoding="utf-8", newline="") as f:
            conn.executemany("INSERT INTO g VALUES (?, ?, ?)", [(float(r["estrato"]) if r["estrato"] else None, r["sin_datos"], r["severo_estricto"]) for r in csv.DictReader(f)])
        sql = {int(e): (int(k), int(n)) for e, k, n in conn.execute(
            "SELECT estrato, SUM(severo = 'True'), COUNT(*) FROM g WHERE estrato IS NOT NULL AND sin_datos = 'False' GROUP BY estrato")}
    finally:
        conn.close()
    kp = {r["grupo"]: r for r in csv.DictReader(open(ROOT / "data/gold/kpis_gold.csv", encoding="utf-8", newline="")) if r["kpi_id"] == "K1"}
    filas, maxdif = [], 0.0
    for e in range(1, 7):
        k, n = sql.get(e, (0, 0))
        r = kp[f"estrato_{e}"]
        lo, hi = wilson(k, n)
        d = max(abs(k / n - float(r["valor"])) if n else 0.0, abs(lo - float(r["ic95_inf"])) if n else 0.0, abs(hi - float(r["ic95_sup"])) if n else 0.0)
        maxdif = max(maxdif, d)
        filas.append((e, k, n, f"{k / n:.6f}" if n else "", r["numerador"], r["denominador"], f"{d:.2e}"))
    qr = json.loads((ROOT / "data/silver/quality_report.json").read_text(encoding="utf-8"))
    return filas, maxdif, qr


def tabla_cobertura(js):
    datos = json.loads(Path(js).read_text(encoding="utf-8"))["files"]
    filas = []
    for ruta, d in sorted(datos.items()):
        rel = Path(ruta).as_posix()
        if d["summary"]["num_statements"] == 0:
            continue
        s = d["summary"]
        filas.append((rel, s["num_statements"], s["missing_lines"], s["percent_covered"]))
    return filas


def generar(pruebas, cobertura, dur_total, codigo, con_cobertura, salida):
    ahora = datetime.now(TZ)
    por_caso = resultado_por_caso(pruebas)
    casos = matriz.casos()
    total = len(pruebas)
    pasan = sum(p["resultado"] == "passed" for p in pruebas)
    fallan = [p for p in pruebas if p["resultado"] in ("failed", "error")]
    L = ["# Informe de pruebas: resultado esperado, obtenido y evidencia", "",
         f"Salida real registrada el {ahora.strftime('%Y-%m-%d')} ({ahora.isoformat(timespec='seconds')}, America/Bogota). Generado con `python scripts/informe_pruebas.py`; no se edita a mano.", "",
         "## Resumen", "",
         f"- **Pruebas ejecutadas:** {total}; **pasan:** {pasan}; **fallan:** {len(fallan)}; **omitidas:** {sum(p['resultado'] == 'skipped' for p in pruebas)}. Duración: {dur_total:.1f} s. Código de salida de pytest: {codigo}.",
         f"- **Casos de la matriz:** {len(casos)} (funciones críticas: {len(matriz.FUNCIONES)}); el resultado esperado de cada uno está en [matriz_casos_prueba.md](matriz_casos_prueba.md).", ""]
    if fallan:
        L += ["### Pruebas que fallan", ""] + [f"- `{p['archivo']}::{p['nombre']}`: {p['mensaje']}" for p in fallan] + [""]
    L += ["## Por archivo de pruebas", "", "| Archivo | Pruebas | Pasan | Duración (s) |", "|---|---|---|---|"]
    archivos = {}
    for p in pruebas:
        a = archivos.setdefault(p["archivo"], [0, 0, 0.0])
        a[0] += 1
        a[1] += p["resultado"] == "passed"
        a[2] += p["duracion"]
    L += [f"| `{k}` | {v[0]} | {v[1]} | {v[2]:.2f} |" for k, v in sorted(archivos.items())]
    L += ["", "## Por caso (resultado esperado y obtenido)", "", "| CP | Caso | Tipo | Resultado esperado | Resultado obtenido | Estado | Duración (s) | Evidencia |", "|---|---|---|---|---|---|---|---|"]
    csv_filas = [["cp", "funcion_critica", "caso", "tipo", "resultado_esperado", "resultado_obtenido", "estado", "duracion_s", "prueba", "variantes"]]
    sin_resultado = 0
    for cp, fc, _, caso, tipo, esperado, nodeid in casos:
        r = por_caso.get(nodeid)
        if r is None:
            sin_resultado += 1
            obtenido, estado, dur, var = "no ejecutada", "SIN RESULTADO", 0.0, 0
        else:
            var, _, dur, res = r
            obtenido, estado = ("cumplió lo esperado", "pasa") if res == "passed" else (f"no cumplió ({res})", "FALLA")
        L.append(f"| {cp} | {caso} | {tipo} | {esperado} | {obtenido} | {estado} | {dur:.2f} | `{nodeid}` |")
        csv_filas.append([cp, fc, caso, tipo, esperado, obtenido, estado, f"{dur:.3f}", nodeid, var])
    L += ["", f"Casos sin resultado: {sin_resultado}.", ""]
    filas, maxdif, qr = metricas_analisis()
    L += ["## Métricas de validación del análisis (recálculo independiente)", "",
          "K1 por estrato recalculado con SQL sobre `gold_final.csv` y con una fórmula de Wilson propia (no la de `src/`), frente a `kpis_gold.csv`.", "",
          "| Estrato | Severas | Con datos | Tasa recalculada | Numerador en kpis_gold | Denominador en kpis_gold | Mayor diferencia (tasa e intervalo) |", "|---|---|---|---|---|---|---|"]
    L += [f"| {e} | {k} | {n} | {t} | {a} | {b} | {d} |" for e, k, n, t, a, b, d in filas]
    L += ["", f"- Mayor diferencia absoluta entre lo recalculado y lo publicado: {maxdif:.2e}.",
          f"- Cobertura de la llave en el reporte de calidad: {qr['cobertura_llave']['pct']:.4f}; confianza de la llave: {qr['llave_confianza']}.", ""]
    if con_cobertura and cobertura:
        tot_s = sum(f[1] for f in cobertura)
        tot_m = sum(f[2] for f in cobertura)
        L += ["## Cobertura de líneas por módulo", "",
              f"Medida con `coverage` sobre `src/` y `scripts/` durante la misma ejecución, sin umbrales impuestos. Total: {100 * (tot_s - tot_m) / tot_s:.1f} % de {tot_s} líneas.", "",
              "| Módulo | Líneas | Sin ejecutar | Cobertura | Motivo si es menor de 70 % |", "|---|---|---|---|---|"]
        for rel, s, m, pc in cobertura:
            motivo = MOTIVOS.get(rel, "") if pc < UMBRAL_EXPLICACION else ""
            L.append(f"| `{rel}` | {s} | {m} | {pc:.0f} % | {motivo} |")
        L.append("")
    L += ["Salida real registrada por `scripts/informe_pruebas.py`; las rutas de la máquina no aparecen en este documento."]
    (salida / "informe_pruebas.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    b = io.StringIO()
    csv.writer(b, lineterminator="\n").writerows(csv_filas)
    (salida / "informe_pruebas.csv").write_text(b.getvalue(), encoding="utf-8", newline="\n")
    if con_cobertura and cobertura:
        b = io.StringIO()
        w = csv.writer(b, lineterminator="\n")
        w.writerow(["modulo", "lineas", "sin_ejecutar", "cobertura_pct", "motivo_si_menor_de_70"])
        w.writerows([(r, s, m, f"{p:.1f}", MOTIVOS.get(r, "") if p < UMBRAL_EXPLICACION else "") for r, s, m, p in cobertura])
        (salida / "cobertura_pruebas.csv").write_text(b.getvalue(), encoding="utf-8", newline="\n")
    return sin_resultado, fallan


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sin-cobertura", action="store_true")
    ap.add_argument("--salida", default=str(ROOT / "docs" / "validacion"))
    a = ap.parse_args(argv)
    salida = Path(a.salida)
    salida.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        xml, js, dur, codigo = ejecutar(a.sin_cobertura, tmp)
        pruebas = leer_junit(xml)
        cobertura = tabla_cobertura(js) if js and js.exists() else []
    sin_resultado, fallan = generar(pruebas, cobertura, dur, codigo, not a.sin_cobertura, salida)
    print(f"informe escrito: {len(pruebas)} pruebas, {len(fallan)} fallan, {sin_resultado} casos sin resultado")
    return 0 if codigo == 0 and not sin_resultado else 1


if __name__ == "__main__":
    sys.exit(main())
