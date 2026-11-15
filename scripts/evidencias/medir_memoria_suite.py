"""Mide el pico de memoria (conjunto de trabajo) del proceso de `pytest` al correr la suite completa.

Uso, desde la raíz del repositorio (solo Windows: usa la API `GetProcessMemoryInfo`):
    python scripts/evidencias/medir_memoria_suite.py [--salida CARPETA]

Qué hace: lanza `python -m pytest -q -p no:cacheprovider` con el mismo intérprete, muestrea el proceso real cada 0,2 s y escribe en `--salida`
(por defecto, la carpeta temporal del sistema) `memoria_suite.txt` con el pico en MiB, la duración y la última línea de `pytest`, y el registro completo de `pytest`
en `suite_memoria_registro.txt`.
Por qué es así: el `python.exe` del entorno virtual es un lanzador que arranca el intérprete real como hijo, así que se mide al hijo y no al lanzador.
Qué NO hace: no modifica el proyecto ni `data/`, no mide otros procesos y no sirve para otro sistema operativo. El pico depende de la máquina.
Última ejecución real: la de la fila `memoria_pico_suite_de_pruebas` de `docs/finanzas/recursos_medidos.csv` (286 MiB, 959 pruebas), hecha con el script de la sesión del que sale este archivo; esta versión solo se validó de forma estática.
"""
import argparse
import ctypes
import ctypes.wintypes as w
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class PMC(ctypes.Structure):
    """Estructura `PROCESS_MEMORY_COUNTERS` de la API de Windows."""
    _fields_ = [("cb", w.DWORD), ("PageFaultCount", w.DWORD), ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t), ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t), ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]


def pico(handle):
    """(pico, actual) del conjunto de trabajo del proceso, en bytes."""
    pmc = PMC()
    pmc.cb = ctypes.sizeof(pmc)
    ctypes.windll.psapi.GetProcessMemoryInfo(w.HANDLE(handle), ctypes.byref(pmc), pmc.cb)
    return pmc.PeakWorkingSetSize, pmc.WorkingSetSize


def hijo_de(pid):
    """PID del proceso hijo (el `python.exe` del entorno virtual es un lanzador que arranca el intérprete real como hijo)."""
    consulta = f"(Get-CimInstance Win32_Process -Filter 'ParentProcessId={pid}' | Select-Object -First 1).ProcessId"
    r = subprocess.run(["powershell", "-NoProfile", "-Command", consulta], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return int(r.stdout.strip()) if r.stdout.strip().isdigit() else None


def main(argv=None):
    """Corre la suite, mide el pico y escribe el resumen."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--salida", type=Path, default=Path(tempfile.gettempdir()), help="carpeta donde se escriben memoria_suite.txt y el registro de pytest")
    args = ap.parse_args(argv)
    args.salida.mkdir(parents=True, exist_ok=True)
    resumen_txt, registro_txt = args.salida / "memoria_suite.txt", args.salida / "suite_memoria_registro.txt"
    entorno = dict(os.environ)
    entorno["PYTHONDONTWRITEBYTECODE"] = "1"
    t0 = time.perf_counter()
    maximo = 0
    with open(registro_txt, "wb") as registro:
        p = subprocess.Popen([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--no-header", "--color=no"], cwd=ROOT, env=entorno, stdout=registro, stderr=subprocess.STDOUT)
        real = None
        while p.poll() is None and real is None:
            real = hijo_de(p.pid)
            time.sleep(0.5)
        h = ctypes.windll.kernel32.OpenProcess(0x1000 | 0x0400, False, real or p.pid)     # PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_QUERY_INFORMATION
        while p.poll() is None:
            pk, _ = pico(h)
            maximo = max(maximo, pk)
            time.sleep(0.2)
    lineas = registro_txt.read_text(encoding="utf-8", errors="replace").strip().splitlines()
    resumen_txt.write_text(f"pico_conjunto_de_trabajo_MiB={maximo / 1048576:.0f}\nduracion_s={time.perf_counter() - t0:.0f}\nresumen={lineas[-1] if lineas else ''}\n", encoding="utf-8")
    print(resumen_txt.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
