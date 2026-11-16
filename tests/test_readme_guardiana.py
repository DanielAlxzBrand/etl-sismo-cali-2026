"""Guardiana mínima del README (D106): forma y reglas de redacción que no dependen de ninguna cifra.

Comprueba, sobre el texto del README: sin emojis, sin guiones largos ni medios, sin términos prohibidos, una sola mención de la inteligencia artificial (la línea autorizada de la
sección 20, que apunta a un archivo que existe), enlaces relativos e imágenes que existen, anclas válidas y una tabla de contenidos que enlaza cada sección.
Las cifras se vigilan en `tests/test_readme_cifras.py`. Cada regla tiene su prueba negativa con un texto sintético.
Las cadenas buscadas se parten para que este archivo no se detecte a sí mismo en el criterio de texto del zip.
"""
import re

from src.common import ROOT

# La única mención permitida de la inteligencia artificial: exactamente esta línea, dentro de la sección «Licencia y créditos».
ARCHIVO_DECLARACION = "DECLARACION" + "_USO_IA.md"
LINEA_AUTORIZADA = f"Todo el contenido generado con ayuda " + f"de IA en este proyecto está declarado en [{ARCHIVO_DECLARACION}]({ARCHIVO_DECLARACION})."

EMOJIS = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u2300-\u23FF\uFE0F\u200D]")
GUIONES = re.compile("[\u2012\u2013\u2014\u2015]")
CORREO = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
RUTA_LOCAL = re.compile(r"[A-Za-z]:\\Us" + r"ers|/Us" + r"ers/|/ho" + "me/")
TERMINOS = {
    "inteligencia artificial": re.compile(r"(?i)inteligencia artificial|aprendizaje autom"),
    "sigla de IA": re.compile(r"\bIA\b"),
    "asistente": re.compile(r"(?i)\basistentes?\b"),
    "instrucción de entrada": re.compile(r"(?i)\bpro" + r"mpts?\b"),
    "fases del trabajo": re.compile(r"(?i)\bfases?\b"),
    "docentes": re.compile(r"(?i)\bpro" + r"fe(?:sor(?:es|a|as)?)?\b|\bdocentes?\b"),
    "asignatura": re.compile(r"(?i)\basignaturas?\b"),
    "carpeta del equipo": re.compile(r"(?i)gu[ií]a[_ ]equipo"),
    "generador retirado": re.compile("make" + "_readme"),
    "marca pendiente": re.compile(r"\bTODO\b|\[COMPLETAR"),
    "nombre de una herramienta": re.compile("Cla" + "ude|Anthro" + "pic|Chat" + "GPT|Co" + "pilot|Gem" + "ini|Open" + "AI"),
}


def _sin_codigo(texto):
    """El texto sin bloques de código ni fragmentos en línea (en ellos van comandos y rutas literales)."""
    texto = re.sub(r"(?s)```.*?```", "", texto)
    return re.sub(r"`[^`\n]*`", "", texto)


def _ancla(titulo):
    """Ancla de un encabezado como la calcula GitHub: minúsculas, sin signos y con guiones en lugar de espacios."""
    t = re.sub(r"[^\w\- ]", "", titulo.strip().lower())
    return t.replace(" ", "-")


def _encabezados(texto):
    """Encabezados de nivel 2 y 3 fuera de los bloques de código, en orden: lista de (nivel, título)."""
    sin_bloques = re.sub(r"(?s)```.*?```", "", texto)
    return [(len(m.group(1)), m.group(2).strip()) for m in re.finditer(r"(?m)^(#{2,3}) (.+)$", sin_bloques)]


def problemas_del_readme(texto, base):
    """Reglas que incumple un README (lista vacía si cumple). `base` es la carpeta contra la que se resuelven los enlaces relativos."""
    errores = []
    # la línea autorizada se retira una sola vez: una segunda aparición o una versión editada se detecta con las reglas siguientes
    lineas = texto.split("\n")
    n_autorizada = sum(1 for l in lineas if l == LINEA_AUTORIZADA)
    if n_autorizada != 1:
        errores.append(f"la línea autorizada sobre la declaración de IA debe aparecer una vez y aparece {n_autorizada}")
    resto = "\n".join(l for i, l in enumerate(lineas) if not (l == LINEA_AUTORIZADA and i == lineas.index(LINEA_AUTORIZADA)))
    if EMOJIS.search(resto):
        errores.append("hay emojis o símbolos gráficos")
    if GUIONES.search(resto):
        errores.append("hay guiones largos o medios")
    prosa = _sin_codigo(resto)
    if re.search(r"(?<=\S) - (?=\S)", prosa):
        errores.append("hay un guion usado como separador de ideas")
    for nombre, patron in TERMINOS.items():
        if patron.search(prosa) or patron.search(resto):
            errores.append(f"término prohibido: {nombre}")
    if CORREO.search(resto):
        errores.append("hay una dirección de correo")
    if RUTA_LOCAL.search(resto):
        errores.append("hay una ruta absoluta local")
    # la línea autorizada vive en la sección de licencia y créditos y su enlace existe
    if n_autorizada == 1:
        antes = texto.split(LINEA_AUTORIZADA)[0]
        titulos = re.findall(r"(?m)^## (.+)$", antes)
        if not titulos or not re.match(r"(?i)(\d+\.\s*)?licencia", titulos[-1]):
            errores.append("la línea autorizada no está en la sección de licencia y créditos")
        if not (base / ARCHIVO_DECLARACION).is_file():
            errores.append("la línea autorizada apunta a un archivo que no existe")
    # enlaces e imágenes relativos
    encabezados = _encabezados(texto)
    anclas = {_ancla(t) for _, t in encabezados}
    sin_bloques = re.sub(r"(?s)```.*?```", "", texto)
    for m in re.finditer(r"(!?)\[([^\]]*)\]\(([^)\s]+)\)", sin_bloques):
        imagen, alt, destino = m.group(1) == "!", m.group(2), m.group(3)
        if destino.startswith(("http://", "https://", "mailto:")):
            continue
        ruta, _, ancla = destino.partition("#")
        if imagen and not alt.strip():
            errores.append(f"imagen sin texto alternativo: {destino}")
        if ruta and not (base / ruta).exists():
            errores.append(f"el enlace o la imagen no existe: {destino}")
        if not ruta and ancla and ancla not in anclas:
            errores.append(f"ancla inexistente: #{ancla}")
    # tabla de contenidos: enlaza cada sección numerada
    numerados = [t for n, t in encabezados if n == 2 and re.match(r"\d+\.", t)]
    toc = re.search(r"(?ms)^## (?:\d+\.\s*)?Tabla de contenidos\n(.*?)(?=^## )", texto)
    if toc is None:
        errores.append("falta la tabla de contenidos")
    else:
        enlazadas = set(re.findall(r"\]\(#([^)]+)\)", toc.group(1)))
        for t in numerados:
            if _ancla(t) not in enlazadas and not re.match(r"3\.", t):
                errores.append(f"la tabla de contenidos no enlaza: {t}")
    return errores


# ------------------------------------------------------------------------------------------------ casos sintéticos
BASE_FALSA = ROOT   # los destinos de los casos sintéticos son archivos que existen en el repositorio


def _bueno():
    return (
        "# Proyecto\n\nUna frase de propósito.\n\n## 1. Descripción\nTexto, con comas.\n\n## 2. Insignias\n![Pruebas](README.md)\n\n"
        "## 3. Tabla de contenidos\n- [1. Descripción](#1-descripción)\n- [2. Insignias](#2-insignias)\n- [4. Arquitectura](#4-arquitectura)\n- [20. Licencia y créditos](#20-licencia-y-créditos)\n\n"
        "## 4. Arquitectura\nVer [requisitos](requirements.txt) y [la sección](#4-arquitectura).\n\n"
        f"## 20. Licencia y créditos\nMIT.\n\n{LINEA_AUTORIZADA}\n"
    )


def test_un_readme_correcto_no_tiene_problemas():
    assert problemas_del_readme(_bueno(), BASE_FALSA) == []


def _con(reemplazo_de, por):
    assert reemplazo_de in _bueno()
    return _bueno().replace(reemplazo_de, por, 1)


def test_emojis_se_detectan():
    assert problemas_del_readme(_con("Texto, con comas.", "Texto \U0001F680 con comas."), BASE_FALSA)
    assert problemas_del_readme(_con("Texto, con comas.", "Texto \u2705 con comas."), BASE_FALSA)


def test_guiones_largos_y_medios_se_detectan():
    assert problemas_del_readme(_con("Texto, con comas.", "Texto \u2014 con comas."), BASE_FALSA)
    assert problemas_del_readme(_con("Texto, con comas.", "De 1 a 2: 1\u20132."), BASE_FALSA)
    assert problemas_del_readme(_con("Texto, con comas.", "Texto - con guion."), BASE_FALSA), "un guion entre espacios separa ideas"


def test_un_guion_dentro_de_codigo_o_de_una_lista_no_se_detecta():
    assert problemas_del_readme(_con("Texto, con comas.", "Use `pip - x` y\n- una viñeta\n```\na - b\n```"), BASE_FALSA) == []


def test_terminos_prohibidos_se_detectan():
    for malo in ("Lo hizo un asistente.", "Con un pro" + "mpt.", "Hecho con Cla" + "ude.", "Las fases del trabajo.", "El pro" + "fesor lo pidió.", "La asignatura de ETL.",
                 "Ver guia" + "_equipo/", "Usa IA aquí.", "Con inteligencia artificial.", "Un TODO pendiente.", "make" + "_readme.py", "Mail a alguien@correo.com."):
        assert problemas_del_readme(_con("Texto, con comas.", malo), BASE_FALSA), malo


def test_rutas_locales_se_detectan():
    assert problemas_del_readme(_con("Texto, con comas.", "En C:\\Us" + "ers\\alguien\\x."), BASE_FALSA)


def test_la_linea_de_ia_debe_existir_una_sola_vez():
    sin = _bueno().replace(LINEA_AUTORIZADA, "")
    assert problemas_del_readme(sin, BASE_FALSA), "sin la línea"
    doble = _bueno() + "\n" + LINEA_AUTORIZADA + "\n"
    assert problemas_del_readme(doble, BASE_FALSA), "dos veces"


def test_la_linea_de_ia_editada_no_vale():
    editada = _bueno().replace("Todo el contenido", "Parte del contenido")
    assert problemas_del_readme(editada, BASE_FALSA)
    otra = _bueno().replace(LINEA_AUTORIZADA, LINEA_AUTORIZADA + " Usamos IA para todo.")
    assert problemas_del_readme(otra, BASE_FALSA)


def test_la_linea_de_ia_debe_estar_en_la_seccion_de_licencia():
    fuera = _bueno().replace(LINEA_AUTORIZADA, "").replace("## 4. Arquitectura\n", "## 4. Arquitectura\n" + LINEA_AUTORIZADA + "\n")
    assert any("sección de licencia" in e for e in problemas_del_readme(fuera, BASE_FALSA))


def test_la_linea_de_ia_debe_apuntar_a_un_archivo_que_existe(tmp_path):
    assert any("apunta a un archivo que no existe" in e for e in problemas_del_readme(_bueno(), tmp_path))


def test_enlaces_e_imagenes_inexistentes_se_detectan():
    assert problemas_del_readme(_con("[requisitos](requirements.txt)", "[requisitos](no_existe.txt)"), BASE_FALSA)
    assert problemas_del_readme(_con("![Pruebas](README.md)", "![Pruebas](docs/img/no_existe.png)"), BASE_FALSA)
    assert problemas_del_readme(_con("![Pruebas](README.md)", "![](README.md)"), BASE_FALSA), "imagen sin texto alternativo"


def test_anclas_inexistentes_se_detectan():
    assert problemas_del_readme(_con("[la sección](#4-arquitectura)", "[la sección](#9-no-existe)"), BASE_FALSA)


def test_la_tabla_de_contenidos_debe_enlazar_cada_seccion():
    assert problemas_del_readme(_con("- [4. Arquitectura](#4-arquitectura)\n", ""), BASE_FALSA)
    assert problemas_del_readme(_bueno().replace("## 3. Tabla de contenidos", "## 3. Índice"), BASE_FALSA), "sin tabla de contenidos"
