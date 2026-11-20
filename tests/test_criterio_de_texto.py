"""Criterio de texto de los archivos versionados (D97): lo que viaja en el zip no trata de forma personal al equipo docente, no remite a la declaración de uso, no nombra herramientas de elaboración ni
usa la etiqueta del avance anterior.

Por qué existe: la auditoría intermedia retiró de documentos, notebooks, generadores y pruebas el vocativo al equipo docente, las remisiones al archivo de declaración (que ahora es un documento aislado de la
raíz, sin nombrarlo), los pies sobre el uso de herramientas, los nombres de herramientas y la etiqueta del avance anterior. Esta prueba recorre exactamente lo que empaqueta `scripts/make_dist.py` y falla si alguno vuelve.
La única excepción es el documento original de la retroalimentación recibida, que no se edita, y está atada a su sha256 (con los saltos de línea normalizados): si alguien lo edita, la excepción deja
de valer. Las cadenas buscadas se parten para que este archivo no se detecte a sí mismo.
Qué NO demuestra: que no existan otras formas de decir lo mismo; solo vigila las listadas. La sigla «IA» como concepto técnico está permitida (D17) y no se vigila aquí.
"""
import hashlib
import importlib.util
import re

from src.common import ROOT

_spec = importlib.util.spec_from_file_location("make_dist_criterio", ROOT / "scripts" / "make_dist.py")
make_dist = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(make_dist)

SUFIJOS = {".md", ".py", ".txt", ".yaml", ".yml", ".ini", ".ipynb", ".csv", ".json", ".jsonl", ".diff", ".sha256", ".xml", ".example"}
# Las cadenas se parten para que este archivo no se detecte a sí mismo.
REGLAS = {
    "trato personal al equipo docente": re.compile(r"(?i)\bpro" + r"fe(?:sor(?:es)?)?\b"),
    "remisión a la declaración de uso": re.compile("DECLARACION" + "_USO"),
    "pie de declaración de uso": re.compile("(?i)uso de " + r"IA\b"),
    "etiqueta del avance anterior": re.compile(r"(?i)avance[\s_]?" + r"2(?!\d)"),
    "nombre de una herramienta de elaboración": re.compile("Cla" + "ude|Anthro" + "pic|Chat" + "GPT|Co" + "pilot|Gem" + "ini|Open" + "AI|(?i:" + r"\bpro" + r"mpt\b)"),
}
# Excepciones por ruta y sha256 del contenido con saltos de línea normalizados (LF): el original recibido no se edita.
EXCEPCIONES = {
    "docs/retroalimentacion/retroalimentacion_recibida.txt": ("a7fc50952cd84de2a36b5ecc1f6d46c0bf30f59092670f1f20e57d289b6f6839", {"etiqueta del avance anterior"},
                                                              "documento original recibido, no se edita"),
}
# Las salidas crudas registradas conservan lo que tenían al capturarse (igual que la prueba de rastros de elaboración).
CRUDAS = ("docs/evidencias/base/", "docs/evidencias/estrategia/", "docs/evidencias/api/")


def sha_lf(texto):
    """sha256 del texto con los saltos de línea normalizados a LF."""
    return hashlib.sha256(texto.replace("\r\n", "\n").encode("utf-8")).hexdigest()


# D106: el README remite a la declaración de uso con una única línea; la excepción es de ese archivo y de esa línea exacta, una sola vez (D97 sigue valiendo para todo lo demás).
RUTA_CON_LINEA_AUTORIZADA = "README.md"


def sin_la_linea_autorizada(rel, texto):
    """El texto sin la línea autorizada si es el README (una sola aparición); cualquier otro archivo o cualquier variante de la línea conserva todo su texto."""
    from tests.test_readme_guardiana import LINEA_AUTORIZADA

    if rel != RUTA_CON_LINEA_AUTORIZADA:
        return texto
    lineas = texto.split("\n")
    if LINEA_AUTORIZADA in lineas:
        lineas.remove(LINEA_AUTORIZADA)
    return "\n".join(lineas)


# D111: la frase de la excepción de 6.1, 6.2, 6.3, 6.5 y 7.4 puede aparecer, tal cual, solo en estos archivos; cualquier variante o cualquier otro archivo conserva todo su texto.
FRASE_DE_LA_EXCEPCION = "excepción declarada en " + "DECLARACION" + "_USO_IA.md, sección 7"
ARCHIVOS_CON_LA_EXCEPCION = {"docs/DECISIONES.md", "docs/checklist/estado_checklist.md", "docs/checklist/trazabilidad.csv", "docs/checklist/trazabilidad.md"}


def sin_la_frase_de_la_excepcion(rel, texto):
    """El texto sin la frase exacta de la excepción si es uno de los archivos autorizados; en cualquier otro archivo no se quita nada."""
    return texto.replace(FRASE_DE_LA_EXCEPCION, "") if rel in ARCHIVOS_CON_LA_EXCEPCION else texto


def problemas_de_texto(rel, texto):
    """Reglas que incumple un archivo del zip (lista vacía si cumple); aplica las excepciones atadas a sha256 y la línea autorizada del README."""
    permitidas = set()
    if rel in EXCEPCIONES and sha_lf(texto) == EXCEPCIONES[rel][0]:
        permitidas = EXCEPCIONES[rel][1]
    texto = sin_la_frase_de_la_excepcion(rel, sin_la_linea_autorizada(rel, texto))
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
        if p.suffix in SUFIJOS and rel.split("/")[0] != "data" and not make_dist.es_documento_aislado(rel):
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
        "remisión a la declaración de uso": ("scripts/make_dist.py", _real("scripts/make_dist.py").replace('".gitattributes")', '".gitattributes", "' + dec + '")', 1)),
        "pie de declaración de uso": ("docs/usuarios/evaluacion_heuristica.md", _real("docs/usuarios/evaluacion_heuristica.md") + "\nUso de " + "IA: ver " + dec + "\n"),
        "etiqueta del avance anterior": ("docs/estrategia/05_mvp_criterios_aceptacion.md", _real("docs/estrategia/05_mvp_criterios_aceptacion.md").replace("el zip anterior de `dist/`", "`dist/avance" + "2_etl.zip`", 1)),
        "nombre de una herramienta de elaboración": ("README.md", _real("README.md") + "\nHecho con Cla" + "ude.\n"),
    }
    for nombre, (rel, texto) in casos.items():
        assert any(nombre in e for e in problemas_de_texto(rel, texto)), nombre
        assert problemas_de_texto(rel, _real(rel)) == [], f"el archivo real debe cumplir: {rel}"
    cuaderno = _real("notebooks/02_eda_bronze.ipynb")
    assert problemas_de_texto("notebooks/02_eda_bronze.ipynb", cuaderno) == []
    assert problemas_de_texto("notebooks/02_eda_bronze.ipynb", cuaderno.replace('"Aquí cargamos', '"Pro' + 'fe, aquí cargamos', 1)), "una celda de notebook con el vocativo"
    assert problemas_de_texto("docs/x.md", "una palabra como profesional no cuenta") == []
    assert problemas_de_texto("docs/x.md", "Avance 1 sí se conserva") == []


def test_la_linea_autorizada_del_readme_es_la_unica_excepcion_a_la_remision_a_la_declaracion():
    from tests.test_readme_guardiana import LINEA_AUTORIZADA

    base = "# Título\n\n## 20. Licencia y créditos\nMIT.\n\n"
    assert problemas_de_texto("README.md", base + LINEA_AUTORIZADA + "\n") == [], "la línea exacta, una vez, en el README"
    assert problemas_de_texto("README.md", base + LINEA_AUTORIZADA + "\n" + LINEA_AUTORIZADA + "\n"), "la misma línea dos veces"
    assert problemas_de_texto("README.md", base + LINEA_AUTORIZADA.replace("Todo", "Casi todo") + "\n"), "la línea editada"
    assert problemas_de_texto("README.md", base + LINEA_AUTORIZADA + "\nVer " + "DECLARACION" + "_USO_IA.md.\n"), "otra remisión en el README"
    assert problemas_de_texto("docs/otro.md", base + LINEA_AUTORIZADA + "\n"), "la línea en otro archivo"
    assert problemas_de_texto("scripts/make_dist.py", LINEA_AUTORIZADA), "la línea en un script"


def test_el_zip_arma_el_documento_aislado_pero_la_prueba_no_lo_recorre_ni_lo_nombra():
    nombres = [p.relative_to(ROOT).as_posix() for p in make_dist.listar(ROOT)]
    aislados = [n for n in nombres if make_dist.es_documento_aislado(n)]
    assert len(aislados) == 1
    assert aislados[0] not in {rel for rel, _ in _archivos()}


def test_la_frase_de_la_excepcion_solo_vale_tal_cual_y_en_los_archivos_autorizados():
    base = "Cumple con matiz: evidencia simulada, sin personas reales (" + FRASE_DE_LA_EXCEPCION + ")."
    for rel in sorted(ARCHIVOS_CON_LA_EXCEPCION):
        assert problemas_de_texto(rel, base) == [], rel
        assert problemas_de_texto(rel, base.replace("sección 7", "sección 6")), "una variante de la frase"
        assert problemas_de_texto(rel, base + " Ver " + "DECLARACION" + "_USO_IA.md."), "otra remisión en el mismo archivo"
    assert problemas_de_texto("docs/usuarios/README.md", base), "la frase en un archivo no autorizado"
    assert problemas_de_texto("README.md", base), "ni siquiera el README la hereda"
    for rel in sorted(ARCHIVOS_CON_LA_EXCEPCION):
        assert FRASE_DE_LA_EXCEPCION in _real(rel), f"{rel} debe citar la excepción"


def test_ningun_archivo_fuera_de_la_declaracion_trae_la_autorizacion_de_la_excepcion():
    rol = r"(?:do" + r"cente|pro" + r"fe\w*)"
    corto = r"[^\n.]{0,100}"
    patron = re.compile(r"(?i)" + rol + corto + r"autoriz|autoriz\w*" + corto + rol + r"|autorizaci[oó]n\s+(?:verbal|" + "do" + "cente)")
    hallazgos = [rel for rel, texto in _archivos() if patron.search(texto)]
    assert hallazgos == []
    assert patron.search("el do" + "cente autorizó terminar con evidencia simulada") and patron.search("una autorización " + "verbal"), "la regla se dispara con lo que vigila"
    assert not patron.search("Equipo do" + "cente (evaluación del curso)"), "el equipo de los interesados no se confunde"
