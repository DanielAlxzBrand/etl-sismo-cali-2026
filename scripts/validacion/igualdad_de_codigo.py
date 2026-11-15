"""Comprueba que un cambio de textos no tocó el código: compara el árbol de trabajo con una referencia de git ignorando los docstrings.

Uso, desde la raíz del repositorio:
    python scripts/validacion/igualdad_de_codigo.py --base REF [--rutas src scripts dags notebooks main.py]

Qué hace: para cada archivo `.py` y `.ipynb` de las rutas indicadas, compara la versión de `REF` (una etiqueta, un commit o una rama) con la del árbol de trabajo.
  * `.py`: compara el árbol sintáctico (`ast.dump`) después de quitar los docstrings de módulos, clases y funciones; los comentarios no forman parte del árbol.
  * `.ipynb`: valida cada versión con `nbformat`, compara la lista de celdas y sus tipos, y en cada celda de código el árbol sintáctico sin docstrings, y exige idénticos `outputs`,
    `execution_count` y `metadata` de las celdas y del cuaderno.
Clasifica cada archivo en: igual, «solo cambian textos» (docstrings, comentarios o celdas de texto), «cambia el código», nuevo o eliminado. Termina con código 1 si alguno cambia el código
y no está en `--permitir`.
Por qué es así: una limpieza de textos (por ejemplo, quitar un vocativo de un docstring) no debe poder alterar un cálculo; esta comprobación lo demuestra sin ejecutar nada.
Qué NO hace: no ejecuta el código, no compara datos ni salidas nuevas y no modifica ningún archivo.
"""
import argparse
import ast
import json
import subprocess
import sys
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[2]


def sin_docstrings(arbol):
    """El árbol sintáctico sin los docstrings de módulo, clases y funciones."""
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and nodo.body:
            primero = nodo.body[0]
            if isinstance(primero, ast.Expr) and isinstance(primero.value, ast.Constant) and isinstance(primero.value.value, str):
                nodo.body = nodo.body[1:] or [ast.Pass()]
    return arbol


def volcado(fuente):
    """`ast.dump` del código sin docstrings (cadena vacía si la fuente está vacía)."""
    return ast.dump(sin_docstrings(ast.parse(fuente)))


def comparar_python(antes, despues):
    """«igual», «solo cambian textos» o «cambia el código» para dos versiones de un `.py`."""
    if antes == despues:
        return "igual"
    return "solo cambian textos" if volcado(antes) == volcado(despues) else "cambia el código"


def _celdas(texto):
    nb = nbformat.reads(texto, as_version=4)
    nbformat.validate(nb)
    return nb


def comparar_notebooks(antes, despues):
    """Clasificación de dos versiones de un `.ipynb`; ambas deben ser notebooks válidos de `nbformat`."""
    if antes == despues:
        return "igual"
    a, b = _celdas(antes), _celdas(despues)
    if len(a.cells) != len(b.cells) or a.metadata != b.metadata:
        return "cambia el código"
    for ca, cb in zip(a.cells, b.cells):
        if ca.cell_type != cb.cell_type or ca.get("id") != cb.get("id") or ca.metadata != cb.metadata:
            return "cambia el código"
        if ca.cell_type == "code":
            if ca.get("outputs") != cb.get("outputs") or ca.get("execution_count") != cb.get("execution_count"):
                return "cambia el código"
            if volcado("".join(ca.source)) != volcado("".join(cb.source)):
                return "cambia el código"
    return "solo cambian textos"


def comparar(ruta, antes, despues):
    """Clasifica un archivo según su extensión (`.py` o `.ipynb`)."""
    if antes is None:
        return "nuevo"
    if despues is None:
        return "eliminado"
    return comparar_notebooks(antes, despues) if str(ruta).endswith(".ipynb") else comparar_python(antes, despues)


def leer_de_git(ref, ruta):
    """Contenido del archivo en `ref` o None si no existía."""
    r = subprocess.run(["git", "show", f"{ref}:{ruta}"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout if r.returncode == 0 else None


def archivos(ref, rutas):
    """Rutas (relativas, con `/`) de los `.py` y `.ipynb` que existen en `ref` o en el árbol de trabajo, dentro de `rutas`."""
    en_ref = subprocess.run(["git", "ls-tree", "-r", "--name-only", ref, *rutas], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.split()
    en_arbol = []
    for r in rutas:
        p = ROOT / r
        en_arbol += [x.relative_to(ROOT).as_posix() for x in ([p] if p.is_file() else p.rglob("*") if p.is_dir() else [])]
    return sorted({f for f in en_ref + en_arbol if f.endswith((".py", ".ipynb")) and "__pycache__" not in f and ".ipynb_checkpoints" not in f})


def main(argv=None):
    """Compara el árbol de trabajo con `--base` e imprime un resumen por categoría."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", required=True, help="etiqueta, commit o rama de referencia")
    ap.add_argument("--rutas", nargs="+", default=["src", "scripts", "dags", "notebooks", "main.py"])
    ap.add_argument("--permitir", nargs="*", default=[], help="archivos cuyo cambio de código ya está justificado")
    ap.add_argument("--json", type=Path, help="escribe el detalle en este archivo")
    args = ap.parse_args(argv)
    detalle = {}
    for f in archivos(args.base, args.rutas):
        p = ROOT / f
        detalle[f] = comparar(f, leer_de_git(args.base, f), p.read_text(encoding="utf-8") if p.is_file() else None)
    cuenta = {}
    for estado in detalle.values():
        cuenta[estado] = cuenta.get(estado, 0) + 1
    print("resumen:", json.dumps(cuenta, ensure_ascii=False))
    cambian = [f for f, e in detalle.items() if e == "cambia el código" and f not in args.permitir]
    for f in sorted(f for f, e in detalle.items() if e in ("solo cambian textos", "cambia el código", "nuevo", "eliminado")):
        print(f"  {detalle[f]:<22} {f}{'  (permitido)' if f in args.permitir else ''}")
    if args.json:
        args.json.write_text(json.dumps(detalle, ensure_ascii=False, indent=1), encoding="utf-8")
    return 1 if cambian else 0


if __name__ == "__main__":
    sys.exit(main())
