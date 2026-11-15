"""Mide el pico de memoria (conjunto de trabajo) del proceso de `pytest` al correr la suite completa.

Uso, desde la raíz del repositorio (solo Windows: usa la API de procesos de Windows):
    python scripts/evidencias/medir_memoria_suite.py [--salida CARPETA]

Qué hace: lanza `python -m pytest -q -p no:cacheprovider` con el mismo intérprete, sigue a todos los procesos descendientes (el `python.exe` del entorno virtual es un lanzador que arranca el
intérprete real como hijo), guarda abierto un manejador de cada uno y, al terminar, toma el mayor `PeakWorkingSetSize`. Escribe en `--salida` (por defecto, la carpeta temporal del sistema)
`memoria_suite.txt` con el pico en MiB, la duración y la última línea de `pytest`, y el registro completo de `pytest` en `suite_memoria_registro.txt`.
Por qué es así: sondear solo al hijo con una consulta externa fallaba sin avisar y dejaba el pico en 0; ahora el pico sale del propio contador del sistema y, si no se puede medir, el script falla
con un mensaje en lugar de escribir 0.
Qué NO hace: no modifica el proyecto ni `data/`, no mide otros procesos y no sirve para otro sistema operativo. El pico depende de la máquina.
Última ejecución real: pendiente de registrar (la medición anterior, de la fila `memoria_pico_suite_de_pruebas` de `docs/finanzas/recursos_medidos.csv`, se hizo con el script de la sesión de trabajo).
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


class PROCESSENTRY32(ctypes.Structure):
    """Entrada de la lista de procesos de `CreateToolhelp32Snapshot` (solo se usan el PID y el PID del padre)."""
    _fields_ = [("dwSize", w.DWORD), ("cntUsage", w.DWORD), ("th32ProcessID", w.DWORD), ("th32DefaultHeapID", ctypes.c_size_t), ("th32ModuleID", w.DWORD), ("cntThreads", w.DWORD),
                ("th32ParentProcessID", w.DWORD), ("pcPriClassBase", ctypes.c_long), ("dwFlags", w.DWORD), ("szExeFile", ctypes.c_wchar * 260)]


def _api():
    """Funciones de Windows con sus tipos declarados (sin esto, los manejadores de 64 bits se truncan)."""
    k32, ps = ctypes.WinDLL("kernel32", use_last_error=True), ctypes.WinDLL("psapi", use_last_error=True)
    k32.OpenProcess.restype, k32.OpenProcess.argtypes = w.HANDLE, (w.DWORD, w.BOOL, w.DWORD)
    k32.CloseHandle.argtypes = (w.HANDLE,)
    k32.CreateToolhelp32Snapshot.restype, k32.CreateToolhelp32Snapshot.argtypes = w.HANDLE, (w.DWORD, w.DWORD)
    k32.Process32FirstW.argtypes = k32.Process32NextW.argtypes = (w.HANDLE, ctypes.POINTER(PROCESSENTRY32))
    ps.GetProcessMemoryInfo.argtypes, ps.GetProcessMemoryInfo.restype = (w.HANDLE, ctypes.POINTER(PMC), w.DWORD), w.BOOL
    return k32, ps


def descendientes(k32, pid):
    """Conjunto con `pid` y todos los procesos que cuelgan de él en este momento."""
    foto = k32.CreateToolhelp32Snapshot(0x2, 0)       # TH32CS_SNAPPROCESS
    pares = []
    e = PROCESSENTRY32()
    e.dwSize = ctypes.sizeof(e)
    ok = k32.Process32FirstW(foto, ctypes.byref(e))
    while ok:
        pares.append((e.th32ProcessID, e.th32ParentProcessID))
        ok = k32.Process32NextW(foto, ctypes.byref(e))
    k32.CloseHandle(foto)
    vivos, crece = {pid}, True
    while crece:
        nuevos = {hijo for hijo, padre in pares if padre in vivos and hijo not in vivos}
        crece = bool(nuevos)
        vivos |= nuevos
    return vivos


def pico(ps, handle):
    """Pico del conjunto de trabajo del proceso, en bytes (0 si la API no responde)."""
    pmc = PMC()
    pmc.cb = ctypes.sizeof(pmc)
    return pmc.PeakWorkingSetSize if ps.GetProcessMemoryInfo(handle, ctypes.byref(pmc), pmc.cb) else 0


def main(argv=None):
    """Corre la suite, mide el pico y escribe el resumen."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--salida", type=Path, default=Path(tempfile.gettempdir()), help="carpeta donde se escriben memoria_suite.txt y el registro de pytest")
    args = ap.parse_args(argv)
    args.salida.mkdir(parents=True, exist_ok=True)
    resumen_txt, registro_txt = args.salida / "memoria_suite.txt", args.salida / "suite_memoria_registro.txt"
    k32, ps = _api()
    entorno = dict(os.environ)
    entorno["PYTHONDONTWRITEBYTECODE"] = "1"
    t0 = time.perf_counter()
    manejadores = {}
    with open(registro_txt, "wb") as registro:
        p = subprocess.Popen([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--no-header", "--color=no"], cwd=ROOT, env=entorno, stdout=registro, stderr=subprocess.STDOUT)
        while p.poll() is None:
            for pid in descendientes(k32, p.pid):
                if pid not in manejadores:
                    h = k32.OpenProcess(0x1000 | 0x0400, False, pid)       # PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_QUERY_INFORMATION
                    if h:
                        manejadores[pid] = h
            time.sleep(0.2)
    maximo = max((pico(ps, h) for h in manejadores.values()), default=0)
    for h in manejadores.values():
        k32.CloseHandle(h)
    lineas = registro_txt.read_text(encoding="utf-8", errors="replace").strip().splitlines()
    if maximo == 0:
        raise SystemExit("no se pudo medir el pico de memoria (ningún proceso respondió); no se escribe un 0")
    resumen_txt.write_text(f"pico_conjunto_de_trabajo_MiB={maximo / 1048576:.0f}\nprocesos_medidos={len(manejadores)}\nduracion_s={time.perf_counter() - t0:.0f}\nresumen={lineas[-1] if lineas else ''}\n", encoding="utf-8")
    print(resumen_txt.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
