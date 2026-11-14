"""Pruebas de los requisitos del proyecto: versiones exactas, paquetes declarados y versión de Python soportada.

Por qué existen: en una instalación desde cero, con versiones mínimas, un cambio de Python o de fecha ya hacía fallar
una prueba (numpy 2.4.6 en Python 3.11 frente a numpy 2.5.4). Aquí se exige que todo lo que el código importa esté en
`requirements.txt` con `==`, y que la versión de Python soportada esté escrita en los documentos y coincida con la que corre.
"""
import ast
import re
import sys

import pytest

from src.common import ROOT

PYTHON_SOPORTADO = "3.13"
"""Política aprobada: una sola versión soportada, la de la línea base."""

# Nombre con el que se importa -> nombre de la distribución que se instala con pip.
# Se escribe a mano porque no siempre coinciden (yaml es PyYAML, dotenv es python-dotenv).
IMPORT_A_DISTRIBUCION = {
    "altair": "altair",
    "cryptography": "cryptography",
    "dotenv": "python-dotenv",
    "fastapi": "fastapi",
    "httpx": "httpx",
    "matplotlib": "matplotlib",
    "numpy": "numpy",
    "openpyxl": "openpyxl",
    "pandas": "pandas",
    "pydantic": "pydantic",
    "pymysql": "pymysql",
    "pytest": "pytest",
    "requests": "requests",
    "shapely": "shapely",
    "starlette": "starlette",
    "streamlit": "streamlit",
    "websockets": "websockets",
    "yaml": "pyyaml",
}

CARPETAS_CODIGO = ("src", "scripts", "tests")
LINEA_FIJA = re.compile(r"^(?P<nombre>[A-Za-z0-9][A-Za-z0-9._-]*)(\[[^\]]+\])?==(?P<version>[0-9][^\s;#]*)\s*(;[^#]*)?(#.*)?$")


def _normalizar(nombre):
    """Nombre de distribución comparable (PEP 503): minúsculas y guiones."""
    return re.sub(r"[-_.]+", "-", nombre).lower()


def lineas_de_requisitos(texto):
    """Líneas con contenido de un requirements.txt: sin vacías ni comentarios."""
    return [l.strip() for l in texto.splitlines() if l.strip() and not l.strip().startswith("#")]


def lineas_sin_version_exacta(lineas):
    """Líneas que no tienen la forma `paquete==versión` (mínimos, rangos, sin versión u opciones)."""
    return [l for l in lineas if not LINEA_FIJA.match(l)]


def paquetes_declarados(lineas):
    """Nombres normalizados de las distribuciones declaradas."""
    return [_normalizar(LINEA_FIJA.match(l).group("nombre")) for l in lineas if LINEA_FIJA.match(l)]


def imports_de_terceros(fuentes, locales):
    """Nombres superiores importados que no son de la biblioteca estándar ni módulos propios.

    `fuentes` es una lista de textos de código Python; `locales` son los nombres de módulos y paquetes del proyecto.
    """
    importados = set()
    for texto in fuentes:
        for nodo in ast.walk(ast.parse(texto)):
            if isinstance(nodo, ast.Import):
                nombres = [a.name for a in nodo.names]
            elif isinstance(nodo, ast.ImportFrom) and nodo.module and nodo.level == 0:
                nombres = [nodo.module]
            else:
                continue
            importados.update(n.split(".")[0] for n in nombres)
    return {n for n in importados if n not in sys.stdlib_module_names and n not in locales}


def faltan_por_declarar(terceros, declarados, tabla):
    """Distribuciones que se importan y no están declaradas, y los imports que no están en la tabla import → distribución."""
    sin_tabla = sorted(n for n in terceros if n not in tabla)
    sin_declarar = sorted(tabla[n] for n in terceros if n in tabla and _normalizar(tabla[n]) not in declarados)
    return sin_declarar, sin_tabla


def _archivos_de_codigo():
    archivos = [ROOT / "main.py"]
    for carpeta in CARPETAS_CODIGO:
        archivos += sorted((ROOT / carpeta).rglob("*.py"))
    return archivos


def _nombres_locales():
    """Módulos y paquetes propios: carpetas de código y el nombre de cada archivo .py (los scripts se importan entre sí por nombre)."""
    nombres = {"main", *CARPETAS_CODIGO}
    for ruta in _archivos_de_codigo():
        nombres.add(ruta.stem)
    for carpeta in CARPETAS_CODIGO:
        nombres.update(p.name for p in (ROOT / carpeta).rglob("*") if p.is_dir())
    return nombres


@pytest.fixture(scope="module")
def requisitos():
    return (ROOT / "requirements.txt").read_text(encoding="utf-8")


# ---------------------------------------------------------------- (a) versiones exactas

def test_toda_linea_de_requirements_usa_version_exacta(requisitos):
    """Con `>=` una instalación nueva trae versiones distintas de las probadas; todo debe ir con `==`."""
    assert lineas_sin_version_exacta(lineas_de_requisitos(requisitos)) == []


def test_no_hay_paquetes_repetidos_en_requirements(requisitos):
    nombres = paquetes_declarados(lineas_de_requisitos(requisitos))
    assert len(nombres) == len(set(nombres))


# ---------------------------------------------------------------- (b) todo lo que se importa está declarado

def test_todo_paquete_de_terceros_importado_esta_declarado(requisitos):
    fuentes = [r.read_text(encoding="utf-8") for r in _archivos_de_codigo()]
    terceros = imports_de_terceros(fuentes, _nombres_locales())
    sin_declarar, sin_tabla = faltan_por_declarar(terceros, set(paquetes_declarados(lineas_de_requisitos(requisitos))), IMPORT_A_DISTRIBUCION)
    assert sin_tabla == [], f"imports sin entrada en la tabla import → distribución: {sin_tabla}"
    assert sin_declarar == [], f"distribuciones importadas y no declaradas en requirements.txt: {sin_declarar}"


def test_la_tabla_import_distribucion_solo_tiene_distribuciones_declaradas(requisitos):
    """Una entrada de la tabla que ya no está en requirements.txt es una tabla vieja."""
    declarados = set(paquetes_declarados(lineas_de_requisitos(requisitos)))
    assert {_normalizar(d) for d in IMPORT_A_DISTRIBUCION.values()} <= declarados


def test_la_tabla_import_distribucion_solo_tiene_imports_que_existen():
    fuentes = [r.read_text(encoding="utf-8") for r in _archivos_de_codigo()]
    terceros = imports_de_terceros(fuentes, _nombres_locales())
    assert set(IMPORT_A_DISTRIBUCION) == terceros


# ---------------------------------------------------------------- (c) versión de Python soportada

def test_requirements_declara_la_version_de_python_soportada(requisitos):
    assert re.search(rf"(?m)^# Python soportado: {re.escape(PYTHON_SOPORTADO)}\b", requisitos)


def test_el_readme_declara_la_misma_version_de_python():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"Python {PYTHON_SOPORTADO}" in readme


def test_el_interprete_es_la_version_soportada():
    """Anuncia el problema con un mensaje claro: con Python 3.11 pip no encuentra numpy 2.5.4 (exige 3.12 o más)."""
    actual = f"{sys.version_info.major}.{sys.version_info.minor}"
    assert actual == PYTHON_SOPORTADO, (
        f"Python {actual} no es la versión soportada ({PYTHON_SOPORTADO}); con otra versión pip puede no encontrar numpy 2.5.4 "
        "y los resultados de la línea base no están verificados"
    )


# ---------------------------------------------------------------- (d) pruebas negativas con listas sintéticas

def test_negativa_una_linea_sin_igual_igual_se_detecta():
    sintetico = ["pandas==3.0.6", "requests>=2.31", "pytest", "numpy~=2.5", "fastapi<1"]
    assert lineas_sin_version_exacta(sintetico) == ["requests>=2.31", "pytest", "numpy~=2.5", "fastapi<1"]


def test_negativa_formas_validas_de_fijar_no_se_marcan_como_error():
    validas = ["pandas==3.0.6", "uvicorn[standard]==0.54.0", "pywin32==311; sys_platform == 'win32'", "pytest==9.2.0  # pruebas"]
    assert lineas_sin_version_exacta(validas) == []
    assert paquetes_declarados(validas) == ["pandas", "uvicorn", "pywin32", "pytest"]


def test_negativa_un_import_no_declarado_se_detecta():
    terceros = imports_de_terceros(["import pandas\nimport numpy as np\nfrom pydantic import BaseModel\nimport os\nimport modulo_propio"], {"modulo_propio"})
    assert terceros == {"pandas", "numpy", "pydantic"}
    sin_declarar, sin_tabla = faltan_por_declarar(terceros, {"pandas"}, IMPORT_A_DISTRIBUCION)
    assert sin_declarar == ["numpy", "pydantic"] and sin_tabla == []


def test_negativa_un_import_que_no_esta_en_la_tabla_se_detecta():
    terceros = imports_de_terceros(["import paquete_nuevo_sin_tabla"], set())
    sin_declarar, sin_tabla = faltan_por_declarar(terceros, set(), IMPORT_A_DISTRIBUCION)
    assert sin_tabla == ["paquete_nuevo_sin_tabla"] and sin_declarar == []


def test_negativa_un_import_dentro_de_una_funcion_tambien_cuenta():
    terceros = imports_de_terceros(["def f():\n    import websockets\n    from yaml import safe_load\n"], set())
    assert terceros == {"websockets", "yaml"}


def test_negativa_la_version_de_python_distinta_se_detecta():
    assert not re.search(rf"(?m)^# Python soportado: {re.escape(PYTHON_SOPORTADO)}\b", "# Python soportado: 3.11\npandas==3.0.6\n")
