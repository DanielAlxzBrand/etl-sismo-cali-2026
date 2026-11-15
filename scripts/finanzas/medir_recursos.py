"""Mide el consumo de recursos del pipeline y reúne las mediciones que ya existen en `docs/finanzas/recursos_medidos.csv` (magnitud, valor, unidad, origen, fecha).

Uso:  python scripts/finanzas/medir_recursos.py [--repeticiones 3] [--docker]
Mide EN UN CLON temporal (el repositorio no se toca): tiempo y pico de memoria de `python main.py --stage all` (mediana de N repeticiones), tamaño en disco de `data/`, de la base SQLite y del
zip de prueba armado con `scripts/make_dist.py`. Reutiliza, leyéndolas de sus archivos, las mediciones de la suite de pruebas, de la API (EV-055), de la carga a MySQL (EV-030) y del DAG en vivo
(EV-064). Con --docker y Docker encendido mide la memoria en reposo de los contenedores de Airflow con `docker stats --no-stream`; si estaban apagados los levanta y los vuelve a apagar.
Todo son mediciones locales de una máquina: no valen como garantía para otro equipo. No contiene ni calcula ninguna cifra monetaria.
"""
import argparse
import csv
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SALIDA = ROOT / "docs" / "finanzas" / "recursos_medidos.csv"
ENVOLTURA = r"""
import runpy, sys
sys.argv = ["main.py", "--stage", "all"]
codigo = 0
try:
    runpy.run_path("main.py", run_name="__main__")
except SystemExit as e:
    codigo = e.code or 0
try:
    import ctypes
    from ctypes import wintypes
    class Contadores(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD), ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t), ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t), ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
    c = Contadores(); c.cb = ctypes.sizeof(c)
    ctypes.windll.kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    ctypes.windll.psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Contadores), wintypes.DWORD]
    ctypes.windll.psapi.GetProcessMemoryInfo(ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(c), c.cb)
    print("PICO_MB=%.1f" % (c.PeakWorkingSetSize / 1048576), file=sys.stderr)
except Exception:
    import resource
    print("PICO_MB=%.1f" % (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024), file=sys.stderr)
sys.exit(codigo)
"""


def tamano_mb(ruta):
    ruta = Path(ruta)
    total = ruta.stat().st_size if ruta.is_file() else sum(p.stat().st_size for p in ruta.rglob("*") if p.is_file())
    return total / 1048576


def medir_pipeline(repeticiones):
    """(tiempos en s, picos de memoria en MB, tamaño de data/ en MB, de la base en MB, del zip en MB) medidos en un clon temporal."""
    with tempfile.TemporaryDirectory() as tmp:
        clon = Path(tmp) / "clon"
        subprocess.run(["git", "clone", "--quiet", "--no-hardlinks", str(ROOT), str(clon)], check=True, capture_output=True)
        entorno = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}
        tiempos, picos = [], []
        for _ in range(repeticiones):
            t0 = time.perf_counter()
            r = subprocess.run([sys.executable, "-c", ENVOLTURA], cwd=clon, capture_output=True, text=True, encoding="utf-8", errors="replace", env=entorno)
            tiempos.append(time.perf_counter() - t0)
            if r.returncode != 0:
                raise RuntimeError(f"main.py --stage all falló en el clon: {r.stderr[-300:]}")
            m = re.search(r"PICO_MB=([\d.]+)", r.stderr)
            picos.append(float(m.group(1)) if m else float("nan"))
        data, base = tamano_mb(clon / "data"), tamano_mb(clon / "data" / "gold" / "etl_sismo.db")
        subprocess.run([sys.executable, "scripts/make_dist.py"], cwd=clon, capture_output=True, check=True, env=entorno)
        zips = sorted((clon / "dist").glob("*.zip"), key=lambda p: p.stat().st_mtime)
        return tiempos, picos, data, base, tamano_mb(zips[-1])


def _csv(ruta):
    with open(ruta, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def mediciones_previas():
    """[(magnitud, valor, unidad, origen)] leídas de las evidencias y del informe de pruebas ya registrados."""
    filas = []
    informe = (ROOT / "docs/validacion/informe_pruebas.md").read_text(encoding="utf-8")
    m = re.search(r"\*\*Pruebas ejecutadas:\*\* (\d+).*?Duración: ([\d.]+) s", informe)
    filas += [("duracion_suite_de_pruebas", m.group(2), "s", "docs/validacion/informe_pruebas.md (suite completa con cobertura)"), ("pruebas_ejecutadas", m.group(1), "pruebas", "docs/validacion/informe_pruebas.md")]
    api = _csv(ROOT / "docs/evidencias/panel/EV-055_mediciones_panel.csv")
    for almacen in ("sqlite", "mysql"):
        v = [float(f["mediana_ms"]) for f in api if f["tipo"] == "ruta" and f["almacen"] == almacen]
        filas.append((f"latencia_api_{almacen}_mediana_por_ruta", f"{min(v):.1f} a {max(v):.1f}", "ms", f"EV-055 (medición local, {len(v)} rutas)"))
    lotes = _csv(ROOT / "docs/evidencias/almacenamiento/EV-030_benchmark_lotes.csv")
    for f in lotes:
        filas.append((f"carga_a_mysql_{f['estrategia'].replace(' ', '_')}_mediana", f["mediana_s"], "s", f"EV-030 ({f['filas_cargadas']} filas)"))
    dag = (ROOT / "docs/evidencias/endurecimiento/EV-064_airflow_en_vivo.txt").read_text(encoding="utf-8")
    horas = re.findall(r"\| (?:validar_bronze|transformar_a_silver|integrar_a_gold|cargar_datawarehouse) \| success \| \S+T(\d\d):(\d\d):(\d\d) \| \S+T(\d\d):(\d\d):(\d\d) \|", dag)
    if horas:
        ini = min(int(h) * 3600 + int(mi) * 60 + int(s) for h, mi, s, *_ in horas)
        fin = max(int(h) * 3600 + int(mi) * 60 + int(s) for *_, h, mi, s in horas)
        filas.append(("duracion_dag_cuatro_tareas", str(fin - ini), "s", "EV-064 (ejecución manual en Airflow con Docker)"))
    return filas


def memoria_docker():
    """[(magnitud, valor, unidad, origen)] de la memoria en reposo de los contenedores de Airflow, o [] si Docker no responde."""
    if subprocess.run(["docker", "info"], capture_output=True).returncode != 0:
        return []
    carpeta = ROOT.parent / "airflow-medallon"
    corriendo = subprocess.run(["docker", "ps", "-q"], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.split()
    levantados = False
    if not corriendo:
        subprocess.run(["docker", "compose", "up", "-d"], cwd=carpeta, capture_output=True)
        levantados = True
        fin = time.monotonic() + 240
        while time.monotonic() < fin:
            estado = subprocess.run(["docker", "ps", "--format", "{{.Status}}"], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
            if estado and "starting" not in estado and "unhealthy" not in estado:
                break
            time.sleep(5)
        time.sleep(60)   # reposo: un minuto sin ejecutar el DAG
    salida = subprocess.run(["docker", "stats", "--no-stream", "--format", "{{.Name}}|{{.MemUsage}}"], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    if levantados:
        subprocess.run(["docker", "compose", "down"], cwd=carpeta, capture_output=True)
    filas, total = [], 0.0
    for linea in salida.splitlines():
        nombre, uso = linea.split("|")
        valor, unidad = re.match(r"([\d.]+)\s*(\w+)", uso).groups()
        mb = float(valor) * {"KiB": 1 / 1024, "MiB": 1, "GiB": 1024}.get(unidad, 1)
        total += mb
        filas.append((f"memoria_en_reposo_{re.sub(r'^airflow-medallon-|-1$', '', nombre)}", f"{mb:.0f}", "MiB", "docker stats --no-stream tras un minuto en reposo"))
    if filas:
        filas.append(("memoria_en_reposo_total_contenedores_de_airflow", f"{total:.0f}", "MiB", "suma de las filas anteriores"))
    return filas


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repeticiones", type=int, default=3)
    ap.add_argument("--docker", action="store_true")
    a = ap.parse_args(argv)
    hoy = date.today().isoformat()
    tiempos, picos, data, base, zip_mb = medir_pipeline(a.repeticiones)
    origen = f"medido en un clon temporal con scripts/finanzas/medir_recursos.py (mediana de {a.repeticiones} repeticiones; medición local de una máquina)"
    filas = [("tiempo_main_todas_las_etapas", f"{statistics.median(tiempos):.1f}", "s", origen), ("pico_memoria_main_todas_las_etapas", f"{statistics.median(picos):.0f}", "MB", origen + "; conjunto de trabajo máximo del proceso"),
             ("tamano_data_mb", f"{data:.1f}", "MB", "clon temporal"), ("tamano_base_sqlite_mb", f"{base:.1f}", "MB", "clon temporal"), ("tamano_zip_de_prueba_mb", f"{zip_mb:.1f}", "MB", "clon temporal, scripts/make_dist.py")]
    filas += mediciones_previas()
    docker = memoria_docker() if a.docker else []
    filas += docker if docker else [("memoria_en_reposo_contenedores_de_airflow", "no medido", "MiB", "Docker apagado o no se pidió --docker")]
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["magnitud", "valor", "unidad", "origen", "fecha"])
        w.writerows([(m, v, u, o, hoy) for m, v, u, o in filas])
    print(f"escrito {SALIDA.name}: {len(filas)} magnitudes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
