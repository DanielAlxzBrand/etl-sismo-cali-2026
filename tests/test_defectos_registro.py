"""El registro de defectos, el verificador de regresiones y los documentos de estado dicen lo mismo (D82).

Por qué existe: el registro llegó a tener 14 defectos mientras los documentos de estado seguían diciendo 13, y dos defectos corregidos
(DEF-015 y DEF-016) no estaban registrados. Aquí se comprueba que los identificadores sean consecutivos, que cada defecto marcado «Sí» en
«¿falla sin la corrección?» tenga su reintroducción en `scripts/validacion/verificar_regresiones.py` (y al revés), que cada prueba de
regresión citada exista y que el número de defectos de los documentos de estado sea el del registro.
"""
import ast
import importlib.util
import re

import pytest

from src.common import ROOT

REGISTRO = ROOT / "docs" / "validacion" / "registro_defectos.md"
DOCUMENTOS = [ROOT / "docs" / "checklist" / "estado_checklist.md", ROOT / "docs" / "checklist" / "guia_de_evidencias.md"]


def filas_del_registro(texto):
    """[(id, celdas)] de cada fila de defecto de la tabla del registro."""
    filas = []
    for linea in texto.splitlines():
        m = re.match(r"^\| (DEF-\d+[a-z]?) \|", linea)
        if m:
            filas.append((m.group(1), [c.strip() for c in linea.strip().strip("|").split(" | ")]))
    return filas


def errores_de_numeracion(ids):
    """Errores si los identificadores no son DEF-001 a DEF-nnn sin saltos ni repetidos."""
    numeros = [int(re.search(r"\d+", i).group()) for i in ids]
    esperado = list(range(1, len(numeros) + 1))
    return [] if numeros == esperado else [f"los identificadores no son consecutivos: {ids}"]


def pruebas_citadas(celda):
    """[(archivo, prueba)] citadas entre comillas de código: «`tests/a.py::test_x` y `test_y`» da dos pruebas del mismo archivo."""
    citadas, archivo = [], None
    for ficha in re.findall(r"`([^`]+)`", celda):
        if "::" in ficha and ficha.startswith("tests/"):
            archivo, nombre = ficha.split("::")
            citadas.append((archivo, nombre))
        elif ficha.startswith("test_") and archivo:
            citadas.append((archivo, ficha))
    return citadas


def existe_la_prueba(archivo, nombre):
    arbol = ast.parse((ROOT / archivo).read_text(encoding="utf-8"))
    return any(isinstance(n, ast.FunctionDef) and n.name == nombre for n in ast.walk(arbol))


def cargar_verificador():
    espec = importlib.util.spec_from_file_location("verificar_regresiones", ROOT / "scripts" / "validacion" / "verificar_regresiones.py")
    modulo = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(modulo)
    return modulo


@pytest.fixture(scope="module")
def filas():
    return filas_del_registro(REGISTRO.read_text(encoding="utf-8"))


def test_los_identificadores_del_registro_son_consecutivos(filas):
    ids = [i for i, _ in filas if not i[-1].isalpha()]
    assert errores_de_numeracion(ids) == []


def test_toda_fila_del_registro_tiene_siete_celdas(filas):
    assert all(len(c) == 7 for _, c in filas)


def test_cada_defecto_marcado_si_tiene_su_reintroduccion_y_al_reves(filas):
    con_si = {i for i, c in filas if c[6].startswith("Sí")}
    del_verificador = {m[0] for m in cargar_verificador().MUTACIONES}
    assert {i.rstrip("b") for i in del_verificador} == con_si


def test_cada_prueba_de_regresion_citada_existe(filas):
    for ident, celdas in filas:
        for archivo, nombre in pruebas_citadas(celdas[5]):
            assert existe_la_prueba(archivo, nombre), f"{ident}: no existe {archivo}::{nombre}"


def test_el_verificador_apunta_a_pruebas_que_existen():
    for ident, archivo, _, _, prueba in cargar_verificador().MUTACIONES:
        ruta, nombre = prueba.split("::")
        assert existe_la_prueba(ruta, nombre), f"{ident}: no existe {prueba}"
        assert (ROOT / archivo).is_file(), f"{ident}: no existe {archivo}"


@pytest.mark.parametrize("documento", DOCUMENTOS, ids=lambda p: p.name)
def test_los_documentos_de_estado_citan_el_numero_de_defectos_del_registro(documento, filas):
    total = len([i for i, _ in filas if not i[-1].isalpha()])
    texto = documento.read_text(encoding="utf-8")
    cifras = re.findall(r"\b(\d+) defectos\b", texto)
    assert cifras, "el documento no cita el número de defectos con la forma «N defectos»"
    assert set(cifras) == {str(total)}, f"dicen {sorted(set(cifras))} y el registro tiene {total}"
    assert set(re.findall(r"DEF-001 a DEF-(\d+)", texto)) <= {f"{total:03d}"}


# ---------------------------------------------------------------- negativas con registros sintéticos
def test_negativa_un_salto_de_numeracion_se_detecta():
    assert errores_de_numeracion(["DEF-001", "DEF-002", "DEF-004"])
    assert errores_de_numeracion(["DEF-001", "DEF-001"])
    assert errores_de_numeracion(["DEF-001", "DEF-002"]) == []


def test_negativa_una_prueba_que_no_existe_se_detecta():
    assert existe_la_prueba("tests/test_defectos_registro.py", "test_los_identificadores_del_registro_son_consecutivos")
    assert not existe_la_prueba("tests/test_defectos_registro.py", "test_que_no_existe")


def test_negativa_el_lector_de_filas_ignora_lo_que_no_es_un_defecto():
    texto = "| ID | x |\n|---|---|\n| DEF-001 | a | b | c | d | e | f |\n| otra | fila |\n"
    assert [i for i, _ in filas_del_registro(texto)] == ["DEF-001"]
