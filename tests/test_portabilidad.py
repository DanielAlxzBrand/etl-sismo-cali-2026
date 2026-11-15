"""Portabilidad de las pruebas y los scripts a una consola predeterminada de Windows (cp1252) y a rutas con espacios y tildes (D92).

Por qué existe: en el equipo de desarrollo la consola y las variables de entorno ya fuerzan UTF-8, así que un archivo abierto sin `encoding` o una salida de subproceso leída con otra codificación funciona
«de casualidad». En otro Windows no: al ejecutar la suite en un clon con el nombre `Prueba con espacios y tildes ñ` y sin ninguna variable de UTF-8 falló una prueba (`streamlit config show` escribía en cp1252 y la
prueba leía UTF-8). Aquí se vigila con un análisis del código (nadie abre texto ni lee un subproceso sin decir la codificación) y con una ejecución real sin variables de UTF-8.
Qué NO demuestra: que todo el proyecto funcione en cualquier consola; solo cubre `scripts/` y `tests/` (`src/` no se toca en este componente) y lo que estas pruebas ejecutan.
"""
import ast
import os
import subprocess
import sys

import pytest

from src.common import ROOT

CARPETAS = ("scripts", "tests")
SUBPROCESOS = {"run", "Popen", "check_output", "check_call", "call"}


def _archivos():
    return sorted(p for c in CARPETAS for p in (ROOT / c).rglob("*.py") if "__pycache__" not in p.parts)


def _kw(llamada, nombre):
    return next((k.value for k in llamada.keywords if k.arg == nombre), None)


def _es_verdadero(nodo):
    return isinstance(nodo, ast.Constant) and nodo.value is True


def _modo(llamada, posicion):
    modo = _kw(llamada, "mode")
    if modo is None and len(llamada.args) > posicion:
        modo = llamada.args[posicion]
    return modo.value if isinstance(modo, ast.Constant) and isinstance(modo.value, str) else None


def _defectos(ruta):
    arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
    rel = ruta.relative_to(ROOT).as_posix()
    malos = []
    for n in ast.walk(arbol):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        es_open = (isinstance(f, ast.Name) and f.id == "open") or (isinstance(f, ast.Attribute) and (f.attr == "fdopen" or (f.attr == "open" and isinstance(f.value, ast.Name) and f.value.id == "io")))
        if isinstance(f, ast.Attribute) and f.attr in ("read_text", "write_text"):
            # el primer argumento posicional de `read_text` (y el segundo de `write_text`) es la codificación; en `Distribution.read_text("WHEEL")` es el nombre del archivo y tampoco la lleva
            if _kw(n, "encoding") is None and len(n.args) <= (0 if f.attr == "read_text" else 1):
                malos.append(f"{rel}:{n.lineno} {f.attr} sin encoding")
        elif es_open:
            modo = _modo(n, 1)
            if (modo is None or "b" not in modo) and _kw(n, "encoding") is None:
                malos.append(f"{rel}:{n.lineno} open en modo texto sin encoding")
        elif isinstance(f, ast.Attribute) and f.attr in SUBPROCESOS and isinstance(f.value, ast.Name) and f.value.id == "subprocess":
            if (_es_verdadero(_kw(n, "text")) or _es_verdadero(_kw(n, "universal_newlines"))) and _kw(n, "encoding") is None:
                malos.append(f"{rel}:{n.lineno} subprocess con text=True sin encoding")
    return malos


def test_ningun_script_ni_prueba_abre_texto_ni_lee_un_subproceso_sin_decir_la_codificacion():
    malos = [m for ruta in _archivos() for m in _defectos(ruta)]
    assert not malos, "\n".join(malos)


def test_el_analisis_detecta_los_tres_defectos(tmp_path, monkeypatch):
    """El análisis de arriba sirve si de verdad ve cada defecto: se prueba con un archivo que los trae."""
    malo = tmp_path / "malo.py"
    malo.write_text("import subprocess\nfrom pathlib import Path\nopen('a.txt')\nPath('a').read_text()\nPath('a').write_text('x')\nsubprocess.run(['x'], capture_output=True, text=True)\n"
                    "open('a.bin', 'rb')\nPath('a').read_text(encoding='utf-8')\nsubprocess.run(['x'], text=True, encoding='utf-8')\n", encoding="utf-8")
    monkeypatch.setattr(sys.modules[__name__], "ROOT", tmp_path)
    assert len(_defectos(malo)) == 4


def _entorno_sin_utf8():
    """Entorno de una consola predeterminada de Windows: sin ninguna variable que fuerce UTF-8."""
    return {k: v for k, v in os.environ.items() if not k.upper().startswith(("PYTHONUTF8", "PYTHONIOENCODING"))} | {"PYTHONDONTWRITEBYTECODE": "1"}


def test_las_pruebas_de_subprocesos_pasan_con_la_consola_predeterminada_sin_variables_de_utf8():
    """Es la prueba que falló en el clon con espacios y tildes: `streamlit config show` en cp1252 leído como UTF-8. Se repite sin las variables de UTF-8."""
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--no-header", "--color=no",
                        "tests/test_panel_lanzador.py"],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", env=_entorno_sin_utf8())
    assert r.returncode == 0, r.stdout[-1500:] + r.stderr[-500:]


@pytest.mark.parametrize("script,argumentos", [("scripts/orquestacion/preparar_airflow.py", ["--verificar", "--destino", "carpeta-de-airflow-inexistente"]),
                                                ("scripts/preparar_entorno.py", ["--modo", "completo"])])
def test_los_scripts_de_servicios_imprimen_sus_marcas_con_la_consola_predeterminada_sin_errores_de_codificacion(script, argumentos):
    """Las marcas ✓ y ✗ no existen en cp1252: con la salida redirigida el script no debe caer con UnicodeEncodeError."""
    argumentos = [str(ROOT.parent / a) if a.startswith("carpeta-") else a for a in argumentos]
    r = subprocess.run([sys.executable, str(ROOT / script), *argumentos], cwd=ROOT, capture_output=True, env=_entorno_sin_utf8())
    assert b"UnicodeEncodeError" not in r.stderr and b"Traceback" not in r.stderr, r.stderr[-800:].decode("utf-8", "replace")
    assert r.returncode in (0, 1) and (b"?" in r.stdout or "✓".encode("utf-8") in r.stdout or "✗".encode("utf-8") in r.stdout)
