"""Criterio de texto de los archivos versionados (D97): lo que viaja en el zip no trata de forma personal al equipo docente, no remite a un archivo de declaración, no nombra herramientas de
elaboración ni usa la etiqueta del avance anterior.

Por qué existe: la auditoría intermedia retiró de documentos, notebooks, generadores y pruebas el vocativo al equipo docente, las remisiones a un archivo de declaración, los pies sobre el uso de
herramientas, los nombres de herramientas y la etiqueta del avance anterior. Esta prueba recorre exactamente lo que empaqueta `scripts/make_dist.py` y falla si alguno vuelve.
La única excepción es el documento original de la retroalimentación recibida, que no se edita, y está atada a su sha256 (con los saltos de línea normalizados): si alguien lo edita, la excepción deja
de valer. Los nombres de herramientas y las frases de elaboración no se escriben aquí: están como sha256 en `scripts/terminos_vigilados.py`; las demás cadenas buscadas se parten para que este archivo no se detecte a sí mismo.
Qué NO demuestra: que no existan otras formas de decir lo mismo; solo vigila las listadas. La sigla «IA» como concepto técnico está permitida (D17) y no se vigila aquí.
"""
import base64
import hashlib
import importlib.util
import re

from src.common import ROOT

_spec = importlib.util.spec_from_file_location("make_dist_criterio", ROOT / "scripts" / "make_dist.py")
make_dist = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(make_dist)
_spec_tv = importlib.util.spec_from_file_location("terminos_vigilados_criterio", ROOT / "scripts" / "terminos_vigilados.py")
tv = importlib.util.module_from_spec(_spec_tv)
_spec_tv.loader.exec_module(tv)

SUFIJOS = {".md", ".py", ".txt", ".yaml", ".yml", ".ini", ".ipynb", ".csv", ".json", ".jsonl", ".diff", ".sha256", ".xml", ".example"}
REGLAS = {
    "trato personal al equipo docente": re.compile(r"(?i)\bpro" + r"fe(?:sor(?:es)?)?\b"),
    "remisión a un archivo de declaración": re.compile("DECLARACION" + "_USO"),
    "pie de declaración de uso": tv.Vigilados(tv.FRASES_DE_ELABORACION),
    "etiqueta del avance anterior": re.compile(r"(?i)avance[\s_]?" + r"2(?!\d)"),
    "nombre de una herramienta de elaboración": tv.Vigilados(),
}
# Excepciones por ruta y sha256 del contenido con saltos de línea normalizados (LF): el original recibido no se edita.
EXCEPCIONES = {
    "docs/retroalimentacion/retroalimentacion_recibida.txt": ("a7fc50952cd84de2a36b5ecc1f6d46c0bf30f59092670f1f20e57d289b6f6839", {"etiqueta del avance anterior"},
                                                              "documento original recibido, no se edita"),
}
# Las salidas crudas registradas conservan lo que tenían al capturarse (igual que la prueba de rastros de elaboración).
CRUDAS = ("docs/evidencias/base/", "docs/evidencias/estrategia/", "docs/evidencias/api/")


def _b64(texto):
    """Una cadena guardada en base64 en este archivo (así no aparece escrita)."""
    return base64.b64decode(texto).decode("utf-8")


def sha_lf(texto):
    """sha256 del texto con los saltos de línea normalizados a LF."""
    return hashlib.sha256(texto.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def problemas_de_texto(rel, texto):
    """Reglas que incumple un archivo del zip (lista vacía si cumple); aplica las excepciones atadas a sha256."""
    permitidas = set()
    if rel in EXCEPCIONES and sha_lf(texto) == EXCEPCIONES[rel][0]:
        permitidas = EXCEPCIONES[rel][1]
    errores = []
    for nombre, patron in REGLAS.items():
        if nombre in permitidas:
            continue
        if nombre == "nombre de una herramienta de elaboración" and rel.startswith(CRUDAS):
            continue
        if patron.search(texto):
            errores.append(f"{rel}: {nombre}")
    return errores


def _archivos():
    for p in make_dist.listar(ROOT):
        rel = p.relative_to(ROOT).as_posix()
        if p.suffix in SUFIJOS and rel.split("/")[0] != "data":
            yield rel, p.read_text(encoding="utf-8", errors="ignore")


def test_ningun_archivo_del_zip_incumple_el_criterio_de_texto():
    hallazgos = []
    n = 0
    for rel, texto in _archivos():
        n += 1
        hallazgos += problemas_de_texto(rel, texto)
    assert n > 300
    assert hallazgos == []


def test_la_excepcion_del_original_esta_atada_a_su_ruta_y_a_su_sha256():
    rel = "docs/retroalimentacion/retroalimentacion_recibida.txt"
    texto = (ROOT / rel).read_text(encoding="utf-8")
    assert sha_lf(texto) == EXCEPCIONES[rel][0]
    assert problemas_de_texto(rel, texto) == []
    assert problemas_de_texto(rel, texto + "\nuna línea editada") != [], "si se edita el original, la excepción deja de valer"
    assert problemas_de_texto("docs/otro.txt", texto) != [], "otra ruta no hereda la excepción"


def _real(rel):
    return (ROOT / rel).read_text(encoding="utf-8", errors="ignore")


def test_negativas_cada_regla_se_dispara_con_una_reintroduccion():
    pro, dec = "Pro" + "fesor", "DECLARACION" + "_USO_IA.md"
    casos = {
        "trato personal al equipo docente": ("docs/estrategia/02_stakeholders.md", _real("docs/estrategia/02_stakeholders.md").replace("Equipo docente (evaluación del curso)", pro + " del curso")),
        "remisión a un archivo de declaración": ("scripts/make_dist.py", _real("scripts/make_dist.py").replace('".gitattributes")', '".gitattributes", "' + dec + '")', 1)),
        "pie de declaración de uso": ("docs/usuarios/evaluacion_heuristica.md", _real("docs/usuarios/evaluacion_heuristica.md") + "\n" + _b64("VXNvIGRlIElB") + ": ver el archivo de la raíz\n"),
        "etiqueta del avance anterior": ("docs/estrategia/05_mvp_criterios_aceptacion.md", _real("docs/estrategia/05_mvp_criterios_aceptacion.md").replace("el zip anterior de `dist/`", "`dist/avance" + "2_etl.zip`", 1)),
        "nombre de una herramienta de elaboración": ("README.md", _real("README.md") + "\nHecho con " + tv.canario().capitalize() + ".\n"),
    }
    for nombre, (rel, texto) in casos.items():
        assert any(nombre in e for e in problemas_de_texto(rel, texto)), nombre
        assert problemas_de_texto(rel, _real(rel)) == [], f"el archivo real debe cumplir: {rel}"
    cuaderno = _real("notebooks/02_eda_bronze.ipynb")
    assert problemas_de_texto("notebooks/02_eda_bronze.ipynb", cuaderno) == []
    assert problemas_de_texto("notebooks/02_eda_bronze.ipynb", cuaderno.replace('"Aquí cargamos', '"Pro' + 'fe, aquí cargamos', 1)), "una celda de notebook con el vocativo"
    assert problemas_de_texto("docs/x.md", "una palabra como profesional no cuenta") == []
    assert problemas_de_texto("docs/x.md", "Avance 1 sí se conserva") == []


def test_ningun_archivo_del_zip_remite_a_un_archivo_de_declaracion_ni_siquiera_el_readme():
    dec = "DECLARACION" + "_USO_IA.md"
    assert problemas_de_texto("README.md", "# Título\n\nVer " + dec + ".\n"), "una remisión en el README"
    assert problemas_de_texto("docs/DECISIONES.md", "Ver [" + dec + "](" + dec + ")."), "una remisión en un documento"
    assert [rel for rel, texto in _archivos() if "DECLARACION" + "_USO" in texto] == []


def test_la_raiz_del_zip_no_trae_ningun_documento_suelto_aparte_del_readme():
    nombres = [p.relative_to(ROOT).as_posix() for p in make_dist.listar(ROOT)]
    sueltos = [n for n in nombres if "/" not in n and n.endswith(".md") and n != "README.md"]
    assert sueltos == []


def test_ningun_archivo_trae_la_autorizacion_de_una_excepcion():
    rol = r"(?:do" + r"cente|pro" + r"fe\w*)"
    corto = r"[^\n.]{0,100}"
    patron = re.compile(r"(?i)" + rol + corto + r"autoriz|autoriz\w*" + corto + rol + r"|autorizaci[oó]n\s+(?:verbal|" + "do" + "cente)")
    hallazgos = [rel for rel, texto in _archivos() if patron.search(texto)]
    assert hallazgos == []
    assert patron.search("el do" + "cente autorizó terminar con evidencia simulada") and patron.search("una autorización " + "verbal"), "la regla se dispara con lo que vigila"
    assert not patron.search("Equipo do" + "cente (evaluación del curso)"), "el equipo de los interesados no se confunde"
