"""Evidencia de que las pruebas de regresión de los defectos nuevos fallan sin su corrección (DEF-015 y DEF-016).

Uso:  python scripts/evidencias/evidencia_regresiones_nuevas.py [--nombre EV-065_regresiones_def015_def016.txt]
Reutiliza `scripts/validacion/verificar_regresiones.py` con solo esos dos defectos: reintroduce cada uno en una copia temporal del código y comprueba que su prueba
pasa con la corrección y falla sin ella. No sobrescribe EV-036 (la evidencia de los defectos anteriores) y nunca modifica el repositorio.
"""
import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "validacion"))
sys.path.insert(0, str(ROOT / "scripts" / "evidencias"))
import evidencia  # noqa: E402
import verificar_regresiones as vr  # noqa: E402

NUEVOS = ("DEF-015", "DEF-016")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--nombre", default="EV-065_regresiones_def015_def016.txt")
    a = ap.parse_args(argv)
    t0 = time.perf_counter()
    vr.MUTACIONES = [m for m in vr.MUTACIONES if m[0] in NUEVOS]
    ok, filas = vr.verificar()
    lineas = ["En una copia temporal se reintrodujo cada defecto (un reemplazo de texto en `src/panel/paginas/concentracion.py`) y se ejecutó solo su prueba de regresión: debe pasar con la corrección y fallar sin ella.", "",
              "| Defecto | Archivo modificado | Prueba de regresión | Con la corrección | Sin la corrección | Resultado |", "|---|---|---|---|---|---|"]
    lineas += [f"| {i} | `{f}` | `{p}` | {c} | {s} | {'la prueba detecta el defecto' if b else 'NO LO DETECTA'} |" for i, f, p, c, s, b in filas]
    lineas += ["", f"Resultado: {'las dos pruebas de regresión fallan sin su corrección' if ok else 'HAY PRUEBAS QUE NO DETECTAN SU DEFECTO'}.", "",
               "Qué NO demuestra: que no existan otras formas de nota que la lectura acepte mal; solo cubre los dos defectos registrados."]
    cuerpo = "\n".join(lineas) + "\n"
    print(cuerpo)
    ruta = evidencia.guardar("usuarios", a.nombre, "Las pruebas de regresión de DEF-015 y DEF-016 fallan sin su corrección",
                             "python scripts/evidencias/evidencia_regresiones_nuevas.py", 0 if ok else 1, time.perf_counter() - t0, cuerpo)
    print("evidencia:", ruta.relative_to(ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
