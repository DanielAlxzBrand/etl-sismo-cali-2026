"""Las cifras de los documentos de estado coinciden con el informe de pruebas y con la matriz de casos (D81).

Por qué existe: después de agregar pruebas, `estado_checklist.md` y `guia_de_evidencias.md` seguían diciendo «316 pruebas», «118 casos» y «66,2 %»
cuando los generados ya decían 616, 179 y 72,9 %. Aquí cada cifra que esos documentos repiten se compara con la que dicen
`docs/validacion/informe_pruebas.md` y `docs/validacion/matriz_casos_prueba.csv`. Si un documento cambia la forma de escribirla
y la prueba ya no la encuentra, también falla: así una cifra no se escapa de la vigilancia.
"""
import csv
import re
from collections import Counter

import pytest

from src.common import ROOT

VALIDACION = ROOT / "docs" / "validacion"
DOCUMENTOS = {
    "estado": ROOT / "docs" / "checklist" / "estado_checklist.md",
    "guia": ROOT / "docs" / "checklist" / "guia_de_evidencias.md",
    "interesados": ROOT / "docs" / "estrategia" / "02_stakeholders.md",
    "objetivos": ROOT / "docs" / "estrategia" / "03_objetivo_alcance_okr_kpi.md",
}

# clave: (expresión que encuentra la cifra en el texto, qué verdad compara cada grupo; None = no se compara)
PATRONES = {
    "pruebas_en_verde": (r"\b(\d+) pruebas (?:sin red ni MySQL )?en verde", ["total"]),
    "n_de_n": (r"(?<![\d.])(\d{3,4}) de (\d{3,4})(?![\d.])", ["total", "total"]),
    "passed_de_5_1": (r"`(\d+) passed`\. Nombre: `captura_5\.1_", ["total"]),
    "casos_para_funciones": (r"(\d+) casos para (\d+) funciones críticas", ["casos", "funciones"]),
    "matriz_de_casos_de_prueba": (r"Matriz de (\d+) casos de prueba para (\d+) funciones críticas", ["casos", "funciones"]),
    "funciones_con_casos": (r"(\d+) funciones críticas con (\d+) casos \((\d+) correctos, (\d+) incorrectos y (\d+) límite\)",
                            ["funciones", "casos", "correcto", "incorrecto", "límite"]),
    "casos_por_tipo": (r"(\d+) casos correctos, (\d+) incorrectos y (\d+) límite", ["correcto", "incorrecto", "límite"]),
    "tipos_entre_parentesis": (r"\((\d+), (\d+) y (\d+) casos\)", ["correcto", "incorrecto", "límite"]),
    "cobertura": (r"(\d+,\d) % de (\d\.\d{3}) líneas", ["cobertura", "lineas"]),
    "pruebas_de_interesados": (r"Repositorio ejecutable, (\d+) pruebas", ["total"]),
    "p5": (r"\| P5 Pruebas en verde[^\n]*? (\d+) passed in [\d.]+s \(verificado el (\d{4}-\d{2}-\d{2})\)", ["total", "fecha"]),
}
# Cifras que cada documento DEBE repetir y cuántas veces como mínimo (si una desaparece o cambia de forma, la prueba falla).
OBLIGATORIAS = {
    "estado": {"pruebas_en_verde": 2, "n_de_n": 2, "casos_para_funciones": 1, "funciones_con_casos": 1, "casos_por_tipo": 1, "cobertura": 1},
    "guia": {"n_de_n": 1, "passed_de_5_1": 1, "matriz_de_casos_de_prueba": 1, "funciones_con_casos": 1, "tipos_entre_parentesis": 1, "cobertura": 1},
    "interesados": {"pruebas_de_interesados": 1},
    "objetivos": {"p5": 1},
}


def _con_miles(n):
    return f"{int(n):,}".replace(",", ".")


def verdad_de_los_informes(carpeta=VALIDACION):
    """Cifras vigentes según el informe de pruebas y la matriz de casos (con comprobaciones cruzadas entre ambos)."""
    informe = (carpeta / "informe_pruebas.md").read_text(encoding="utf-8")
    ejecutadas, pasan, fallan, omitidas = (int(x) for x in re.search(
        r"\*\*Pruebas ejecutadas:\*\* (\d+); \*\*pasan:\*\* (\d+); \*\*fallan:\*\* (\d+); \*\*omitidas:\*\* (\d+)", informe).groups())
    casos_informe, funciones_informe = (int(x) for x in re.search(r"\*\*Casos de la matriz:\*\* (\d+) \(funciones críticas: (\d+)\)", informe).groups())
    pct, lineas = re.search(r"Total: ([\d.]+) % de (\d+) líneas", informe).groups()
    fecha = re.search(r"Salida real registrada el (\d{4}-\d{2}-\d{2})", informe).group(1)
    with open(carpeta / "matriz_casos_prueba.csv", encoding="utf-8", newline="") as f:
        matriz = list(csv.DictReader(f))
    tipos = Counter(fila["tipo"] for fila in matriz)
    with open(carpeta / "cobertura_pruebas.csv", encoding="utf-8", newline="") as f:
        lineas_csv = sum(int(fila["lineas"]) for fila in csv.DictReader(f))
    # No se exige aquí que el informe esté en verde: al regenerarlo, pytest corre mientras el informe anterior sigue en disco y la prueba
    # no podría converger. Que todas pasen lo comprueba la propia ejecución de pytest y la verificación final.
    assert omitidas == 0 and pasan + fallan == ejecutadas, "el informe de pruebas está incompleto"
    assert (len(matriz), len({fila["funcion_critica"] for fila in matriz})) == (casos_informe, funciones_informe), "el informe y la matriz no coinciden"
    assert int(lineas) == lineas_csv, "el total de líneas del informe no coincide con cobertura_pruebas.csv"
    return {"total": str(ejecutadas), "casos": str(casos_informe), "funciones": str(funciones_informe), "correcto": str(tipos["correcto"]),
            "incorrecto": str(tipos["incorrecto"]), "límite": str(tipos["límite"]), "cobertura": pct.replace(".", ","), "lineas": _con_miles(lineas), "fecha": fecha}


def revisar_cifras(textos, verdad, obligatorias=OBLIGATORIAS):
    """Errores de las cifras de `textos` ({documento: texto}) frente a `verdad` (lista vacía si todo coincide)."""
    errores = []
    for doc, texto in textos.items():
        encontradas = Counter()
        for clave, (patron, grupos) in PATRONES.items():
            for m in re.finditer(patron, texto):
                encontradas[clave] += 1
                for valor, verdad_de in zip(m.groups(), grupos):
                    if valor != verdad[verdad_de]:
                        errores.append(f"{doc}: «{m.group(0)[:80]}» dice {valor} y {verdad_de} vale {verdad[verdad_de]}")
        faltan = sorted(c for c, minimo in obligatorias.get(doc, {}).items() if encontradas[c] < minimo)
        if faltan:
            errores.append(f"{doc}: no se encontró la cifra «{', '.join(faltan)}» con la forma esperada y las veces esperadas")
    return errores


def _textos():
    return {doc: ruta.read_text(encoding="utf-8") for doc, ruta in DOCUMENTOS.items()}


def test_las_cifras_de_los_documentos_de_estado_coinciden_con_el_informe_y_la_matriz():
    assert revisar_cifras(_textos(), verdad_de_los_informes()) == []


def test_la_fecha_de_p5_es_la_de_la_ultima_salida_del_informe():
    assert re.search(rf"verificado el {verdad_de_los_informes()['fecha']}\)", _textos()["objetivos"])


# ---------------------------------------------------------------- pruebas negativas con textos y verdades sintéticos
VERDAD_SINTETICA = {"total": "700", "casos": "200", "funciones": "30", "correcto": "90", "incorrecto": "60", "límite": "50",
                    "cobertura": "80,5", "lineas": "5.000", "fecha": "2027-01-01"}
TEXTO_SINTETICO = {
    "estado": ("700 pruebas en verde; 700 de 700 pasan; Matriz de 200 casos para 30 funciones críticas; "
               "30 funciones críticas con 200 casos (90 correctos, 60 incorrectos y 50 límite); 90 casos correctos, 60 incorrectos y 50 límite; 80,5 % de 5.000 líneas"),
}


OBLIGATORIAS_SINTETICAS = {"estado": {clave: 1 for clave in OBLIGATORIAS["estado"]}}


def test_negativa_un_texto_con_las_cifras_vigentes_no_da_errores():
    assert revisar_cifras(TEXTO_SINTETICO, VERDAD_SINTETICA, OBLIGATORIAS_SINTETICAS) == []


@pytest.mark.parametrize("viejo,nuevo", [
    ("700 pruebas en verde", "316 pruebas en verde"), ("700 de 700 pasan", "316 de 316 pasan"), ("para 30 funciones", "para 19 funciones"),
    ("200 casos para", "118 casos para"), ("(90 correctos", "(55 correctos"), ("50 límite;", "27 límite;"), ("80,5 % de 5.000 líneas", "66,2 % de 3.383 líneas"),
])
def test_negativa_una_cifra_vieja_se_detecta(viejo, nuevo):
    alterado = {"estado": TEXTO_SINTETICO["estado"].replace(viejo, nuevo, 1)}
    assert alterado["estado"] != TEXTO_SINTETICO["estado"]
    assert revisar_cifras(alterado, VERDAD_SINTETICA, OBLIGATORIAS_SINTETICAS)


def test_negativa_una_cifra_que_cambia_de_forma_y_ya_no_se_encuentra_se_detecta():
    alterado = {"estado": TEXTO_SINTETICO["estado"].replace("700 pruebas en verde", "setecientas pruebas en verde")}
    assert any("no se encontró" in e for e in revisar_cifras(alterado, VERDAD_SINTETICA, OBLIGATORIAS_SINTETICAS))


def test_negativa_la_fecha_de_p5_vieja_se_detecta():
    texto = {"objetivos": "| P5 Pruebas en verde | x | `tests/` | Todas | 700 passed in 190.00s (verificado el 2026-11-12) | s | l |"}
    errores = revisar_cifras(texto, VERDAD_SINTETICA, {"objetivos": {"p5": 1}})
    assert errores and "fecha" in errores[0]
