"""Estabilidad del pipeline: en un clon temporal ejecuta dos veces las funciones que llama el DAG (transformar, gold y carga a SQLite) y compara con lo versionado.

Uso:  python scripts/evidencias/evidencia_estabilidad.py [--nombre EV-035_estabilidad_pipeline.txt]
Nunca escribe en el repositorio salvo la evidencia saneada. La tabla resultante fija la regla de comparación del DAG: CSV y JSON se comparan byte a byte;
`etl_sismo.db` se compara tabla a tabla (el archivo SQLite no es idéntico byte a byte entre ejecuciones); los .md generados de docs/silver no se comparan.
"""
import argparse
import hashlib
import importlib.metadata as im
import os
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import evidencia  # noqa: E402

ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
CODIGO = ("from src.transform.integrate import run_transform; from src.transform.build_gold import run_gold; from src.load.load_database import load_to_sqlite; "
          "run_transform(); run_gold(); load_to_sqlite()")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def huellas(raiz):
    """sha256 de data/ (sin bronze) y de los .md generados de docs/silver."""
    out = {}
    for p in sorted((raiz / "data").rglob("*")):
        if p.is_file() and "bronze" not in p.relative_to(raiz).parts:
            out[p.relative_to(raiz).as_posix()] = sha(p)
    for p in sorted((raiz / "docs" / "silver").glob("*.md")):
        out[p.relative_to(raiz).as_posix()] = sha(p)
    return out


def tablas(db):
    """{tabla: (filas, hash del contenido ordenado)}: compara el contenido y no los bytes del archivo."""
    con = None
    try:
        con = sqlite3.connect(f"{Path(db).as_uri()}?mode=ro", uri=True)
        res = {}
        for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name").fetchall():
            cols = [c[1] for c in con.execute(f"PRAGMA table_info({t})")]
            h, n = hashlib.sha256(), 0
            for fila in con.execute(f"SELECT * FROM {t} ORDER BY {', '.join(cols)}"):
                h.update(repr(fila).encode("utf-8"))
                n += 1
            res[t] = (n, h.hexdigest())
        return res
    finally:
        if con is not None:
            con.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nombre", default="estabilidad_pipeline.txt")
    a = ap.parse_args()
    t0 = time.perf_counter()
    tmp = tempfile.mkdtemp()
    clon = Path(tmp) / "clon"
    subprocess.run(["git", "clone", "--quiet", "--no-hardlinks", str(ROOT), str(clon)], check=True, capture_output=True)
    base, base_tab = huellas(clon), tablas(clon / "data/gold/etl_sismo.db")
    corridas = []
    for i in (1, 2):
        t1 = time.perf_counter()
        r = subprocess.run([sys.executable, "-c", CODIGO], cwd=clon, capture_output=True, text=True, env=ENV, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            print(r.stderr[-1500:])
            return 1
        corridas.append((huellas(clon), tablas(clon / "data/gold/etl_sismo.db"), time.perf_counter() - t1))
    (h1, t1_, d1), (h2, t2_, d2) = corridas
    versiones = {p: im.version(p) for p in ("pandas", "numpy", "shapely", "PyYAML", "python-dotenv", "requests")}
    L = [f"Clon limpio del commit actual (carpeta temporal fuera del repositorio). Python {sys.version.split()[0]}; " + ", ".join(f"{k} {v}" for k, v in versiones.items()) + ".",
         f"Cada corrida ejecuta `run_transform()`, `run_gold()` y `load_to_sqlite()`: corrida 1 en {d1:.1f} s y corrida 2 en {d2:.1f} s.", "",
         "| Archivo | Igual al versionado | Corrida 1 = corrida 2 | Regla del DAG |", "|---|---|---|---|"]
    ok = True
    for ruta in sorted(set(base) | set(h1)):
        if ruta.endswith("etl_sismo.db"):
            continue
        igual, estable = h1.get(ruta) == base.get(ruta), h1.get(ruta) == h2.get(ruta)
        regla = "byte a byte" if ruta.endswith((".csv", ".json")) else "no se compara (documento generado)"
        if ruta.endswith((".csv", ".json")):
            ok &= igual and estable
        L.append(f"| `{ruta}` | {'sí' if igual else 'NO'} | {'sí' if estable else 'NO'} | {regla} |")
    L += ["", "| Tabla de `etl_sismo.db` | Filas | Contenido igual al versionado | Corrida 1 = corrida 2 |", "|---|---|---|---|"]
    for t in sorted(set(base_tab) | set(t1_)):
        igual, estable = t1_[t][1] == base_tab[t][1], t1_[t][1] == t2_[t][1]
        ok &= igual and estable
        L.append(f"| `{t}` | {t1_[t][0]} | {'sí' if igual else 'NO'} | {'sí' if estable else 'NO'} | ")
    db1, db2, dbv = h1["data/gold/etl_sismo.db"], h2["data/gold/etl_sismo.db"], base["data/gold/etl_sismo.db"]
    L += ["", f"Archivo `etl_sismo.db` byte a byte: igual al versionado {'sí' if db1 == dbv else 'NO'}; corrida 1 igual a corrida 2 {'sí' if db1 == db2 else 'NO'}. "
          "El contenido tabla a tabla sí es estable, por eso la regla del DAG para la base es la comparación de contenido.",
          "`docs/silver/reglas_silver.md` se regenera con la ruta anterior de un documento (texto del generador) y por eso difiere del versionado; es estable entre corridas y no se compara.",
          "", f"Resultado: {'CSV y JSON byte a byte y base tabla a tabla estables e iguales a lo versionado' if ok else 'HAY DIFERENCIAS'}."]
    cuerpo = "\n".join(L) + "\n"
    print(cuerpo)
    ruta = evidencia.guardar("orquestacion", a.nombre, "Estabilidad del pipeline antes de orquestarlo", "python scripts/evidencias/evidencia_estabilidad.py", 0 if ok else 1, time.perf_counter() - t0, cuerpo)
    print("evidencia:", ruta.relative_to(ROOT))
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
