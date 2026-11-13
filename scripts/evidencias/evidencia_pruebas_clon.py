"""Pruebas completas en un clon limpio del commit actual, con el desglose por archivo, la comparación de `data/` y el escáner de secretos.

Uso:  python scripts/evidencias/evidencia_pruebas_clon.py [--nombre EV-034_pruebas_clon.txt]
Clona el repositorio a una carpeta temporal fuera de él (sin tocar el árbol de trabajo), ejecuta `pytest` con el intérprete del proyecto, compara el sha256 de los archivos de `data/`
del clon con los del árbol de trabajo y ejecuta el escáner de secretos sobre el clon. Guarda la evidencia saneada.
"""
import argparse
import hashlib
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import evidencia  # noqa: E402


def huellas(carpeta):
    return {p.relative_to(carpeta).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(carpeta.rglob("*")) if p.is_file()}


def ejecutar(cmd, cwd):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout + r.stderr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nombre", default="pruebas_clon.txt")
    a = ap.parse_args()
    t0 = time.perf_counter()
    with tempfile.TemporaryDirectory() as tmp:
        clon = Path(tmp) / "clon"
        subprocess.run(["git", "clone", "--quiet", "--no-hardlinks", str(ROOT), str(clon)], check=True, capture_output=True)
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=clon, capture_output=True, text=True).stdout.strip()
        ok_data = huellas(clon / "data") == huellas(ROOT / "data")
        n_data = len(huellas(clon / "data"))
        cod_col, salida_col = ejecutar([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"], clon)
        por_archivo = Counter(l.split("::")[0].split("/")[-1] for l in salida_col.splitlines() if "::" in l)
        cod, salida = ejecutar([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], clon)
        resumen = [l for l in salida.splitlines() if " passed" in l or " failed" in l or " error" in l][-1:]
        cod_esc, salida_esc = ejecutar([sys.executable, "scripts/escanear_secretos.py"], clon)
        hall = [l for l in salida_esc.splitlines() if l.startswith("hallazgos:")]
        ok = cod == 0 and ok_data and cod_esc == 0
        lineas = [f"Clon limpio del commit {commit} (carpeta temporal fuera del repositorio).", "",
                  f"- pytest: código de salida {cod}; {resumen[0].strip() if resumen else 'sin resumen'}",
                  f"- pruebas recolectadas: {sum(por_archivo.values())}", f"- sha256 de los {n_data} archivos de `data/` del clon iguales a los del árbol de trabajo: {'sí' if ok_data else 'NO'}",
                  f"- escáner de secretos sobre el clon (árbol e historial): código {cod_esc}; {hall[0] if hall else 'sin resumen'}", "", "Pruebas por archivo:", "| Archivo | Pruebas |", "|---|---|"]
        lineas += [f"| `tests/{n}` | {k} |" for n, k in sorted(por_archivo.items())]
        lineas += ["", f"Resultado: {'todo correcto' if ok else 'HAY FALLOS'}."]
        if cod != 0:
            lineas += ["", "Salida de pytest (final):"] + salida.splitlines()[-30:]
        cuerpo = "\n".join(lineas) + "\n"
    ruta = evidencia.guardar("almacenamiento", a.nombre, "Pruebas completas en un clon limpio", "python -m pytest -q -p no:cacheprovider (cwd: <CLON>)", 0 if ok else 1, time.perf_counter() - t0, cuerpo)
    print(cuerpo)
    print("evidencia:", ruta.relative_to(ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
