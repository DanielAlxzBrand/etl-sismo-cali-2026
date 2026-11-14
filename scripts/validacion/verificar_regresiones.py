"""Comprueba que cada prueba de regresión FALLA sin la corrección que protege: en una copia temporal reintroduce el defecto y ejecuta solo esa prueba.

Uso:  python scripts/validacion/verificar_regresiones.py [--evidencia]
Para cada defecto: (1) la prueba pasa con el código real de la copia (control); (2) se reintroduce el defecto con un reemplazo de texto; (3) la misma prueba debe fallar.
Nunca modifica el repositorio: trabaja en una copia con `src`, `scripts`, `tests`, `data`, `dags`, `orquestacion`, `config` y los archivos de primer nivel que las pruebas leen.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "evidencias"))

# id del defecto, archivo, texto correcto, texto del defecto, prueba de regresión
MUTACIONES = [
    ("DEF-001", "src/transform/build_gold.py", "d[d.comuna.notna() & ~d.sin_datos].groupby(", "d[d.comuna.notna()].groupby(",
     "tests/test_kpis.py::test_regresion_defecto_mh_sin_datos_no_entra_en_mh"),
    ("DEF-002", "src/logger.py", '(authorization)(\\s*[:=]\\s*)(.+)")', '(authorization)(\\s*[:=]\\s*)(\\S+)")',
     "tests/test_logger.py::test_enmascara_cabeceras_y_tokens"),
    ("DEF-004", "pytest.ini", "pythonpath = .", "pythonpath = src",
     "tests/test_entorno_de_pruebas.py::test_pytest_ini_fija_la_ruta_de_importacion_y_la_carpeta_de_pruebas"),
    ("DEF-005", "scripts/make_dist.py", 'd.name in EXCLUIR_DIRS or d.name.startswith(".") or parece_entorno_virtual(d)', "d.name in EXCLUIR_DIRS or parece_entorno_virtual(d)",
     "tests/test_dist.py::test_ninguna_carpeta_oculta_dentro_de_las_carpetas_permitidas_entra"),
    ("DEF-007", "src/load/relacional.py", "except (InvalidOperation, ValueError):", "except InvalidOperation:",
     "tests/test_carga_relacional.py::test_conversion_que_perderia_informacion_falla"),
    ("DEF-008", "src/load/sql/esquema_mysql.sql", "COMMENT 'identificador de la corrida'", "COMMENT 'identificador; de la corrida'",
     "tests/test_carga_relacional.py::test_las_sentencias_no_dependen_de_separadores_dentro_de_los_textos"),
    ("DEF-008b", "src/load/sql/esquema_mysql.sql", "COMMENT 'identificador de la corrida'", "COMMENT 'identificador; de la corrida'",
     "tests/test_carga_relacional.py::test_los_dos_esquemas_declaran_las_mismas_tablas_y_columnas_en_el_mismo_orden"),
    ("DEF-012", "dags/medallon_etl_dag.py", '"docs" / "silver" / "hallazgos_eda.md", destino / "docs" / "silver" / "hallazgos_eda.md"', '"docs" / "silver" / "otro.md", destino / "docs" / "silver" / "otro.md"',
     "tests/test_dag_estatico.py::test_la_copia_incluye_la_entrada_de_docs_silver_que_lee_la_transformacion"),
]
COPIAR = ("src", "scripts", "tests", "data", "dags", "orquestacion", "config")
ARCHIVOS = ("pytest.ini", ".env.example", ".gitignore", "requirements.txt")


def copiar(destino):
    for c in COPIAR:
        shutil.copytree(ROOT / c, destino / c, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for f in ARCHIVOS:
        shutil.copy2(ROOT / f, destino / f)


def correr(copia, prueba):
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", prueba], cwd=copia, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    resumen = next((l for l in reversed(r.stdout.splitlines()) if " passed" in l or " failed" in l or "error" in l), "")
    return r.returncode, resumen.strip()


def verificar():
    filas, ok = [], True
    with tempfile.TemporaryDirectory() as tmp:
        copia = Path(tmp) / "copia"
        copiar(copia)
        for ident, archivo, bien, mal, prueba in MUTACIONES:
            ruta = copia / archivo
            original = ruta.read_bytes().decode("utf-8")
            if bien not in original:
                filas.append((ident, archivo, prueba, "no se encontró el texto a modificar", "", False))
                ok = False
                continue
            c0, r0 = correr(copia, prueba)
            ruta.write_bytes(original.replace(bien, mal, 1).encode("utf-8"))
            c1, r1 = correr(copia, prueba)
            ruta.write_bytes(original.encode("utf-8"))
            bueno = c0 == 0 and c1 != 0
            ok &= bueno
            filas.append((ident, archivo, prueba, f"con la corrección: {r0}", f"sin la corrección: {r1}", bueno))
    return ok, filas


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--evidencia", action="store_true")
    a = ap.parse_args(argv)
    t0 = time.perf_counter()
    ok, filas = verificar()
    L = ["En una copia temporal se reintrodujo cada defecto (un reemplazo de texto en el código) y se ejecutó solo su prueba de regresión: debe pasar con la corrección y fallar sin ella.", "",
         "| Defecto | Archivo modificado | Prueba de regresión | Con la corrección | Sin la corrección | Resultado |", "|---|---|---|---|---|---|"]
    L += [f"| {i} | `{f}` | `{p}` | {c} | {s} | {'la prueba detecta el defecto' if b else 'NO LO DETECTA'} |" for i, f, p, c, s, b in filas]
    L += ["", f"Resultado: {'todas las pruebas de regresión fallan sin su corrección' if ok else 'HAY PRUEBAS QUE NO DETECTAN SU DEFECTO'}."]
    cuerpo = "\n".join(L) + "\n"
    print(cuerpo)
    if a.evidencia:
        import evidencia
        ruta = evidencia.guardar("orquestacion", "EV-036_regresiones_sin_correccion.txt", "Las pruebas de regresión fallan sin su corrección", "python scripts/validacion/verificar_regresiones.py --evidencia",
                                 0 if ok else 1, time.perf_counter() - t0, cuerpo)
        print("evidencia:", ruta.relative_to(ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
