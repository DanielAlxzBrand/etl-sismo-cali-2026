"""Guardiana mínima del README (D106): forma y reglas de redacción que no dependen de ninguna cifra.

Comprueba, sobre el texto del README: sin emojis, sin guiones largos ni medios, sin términos prohibidos (los de herramientas y de IA están como sha256 en `scripts/terminos_vigilados.py`),
enlaces relativos e imágenes que existen, anclas válidas y una tabla de contenidos que enlaza cada sección.
Las cifras se vigilan en `tests/test_readme_cifras.py`. Cada regla tiene su prueba negativa con un texto sintético.
Las demás cadenas buscadas se parten para que este archivo no se detecte a sí mismo en el criterio de texto del zip.
"""
import base64
import importlib.util
import re

from src.common import ROOT

_spec_tv = importlib.util.spec_from_file_location("terminos_vigilados_readme", ROOT / "scripts" / "terminos_vigilados.py")
tv = importlib.util.module_from_spec(_spec_tv)
_spec_tv.loader.exec_module(tv)

# El único crédito de una fuente externa de método: el artículo en que se basa la orquestación (título y autor; sin enlace porque no está verificado).
LINEA_CITA_AIRFLOW = ("Orquestación: el DAG y el compose de Airflow siguen el artículo de Juan Manuel Núñez Velasco, «Apache Airflow en Windows con WSL2 y Docker: "
                      "tutorial paso a paso para orquestar un pipeline ETL 2026», con las diferencias documentadas en "
                      "[docs/orquestacion/diferencias_con_la_guia.md](docs/orquestacion/diferencias_con_la_guia.md).")
NOMBRES_LICENCIA = ("Daniel Alexander Brand García", "Diego Fernando Gordillo Londoño", "Jhoan Sebastián Castellanos Mayor")

EMOJIS = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u2300-\u23FF\uFE0F\u200D]")
GUIONES = re.compile("[\u2012\u2013\u2014\u2015]")
CORREO = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
RUTA_LOCAL = re.compile(r"[A-Za-z]:\\Us" + r"ers|/Us" + r"ers/|/ho" + "me/")
TERMINOS = {
    "inteligencia artificial o su sigla": tv.Vigilados(tv.DE_IA, partes=False),
    "aprendizaje automático": re.compile(r"(?i)aprendizaje autom"),
    "asistente": re.compile(r"(?i)\basistentes?\b"),
    "fases del trabajo": re.compile(r"(?i)\bfases?\b"),
    "docentes": re.compile(r"(?i)\bpro" + r"fe(?:sor(?:es|a|as)?)?\b|\bdocentes?\b"),
    "asignatura": re.compile(r"(?i)\basignaturas?\b"),
    "carpeta del equipo": re.compile(r"(?i)gu[ií]a[_ ]equipo"),
    "generador retirado": re.compile("make" + "_readme"),
    "cita externa fuera de su línea": re.compile(r"Núñez|tutorial paso a paso|Apache Airflow en Windows"),
    "marca pendiente": re.compile(r"\bTODO\b|\[COMPLETAR"),
    "afirmación de no manejar datos personales": re.compile(r"(?i)\bno (?:maneja|trata)(?:mos)? datos personales"),
    "nombre de una herramienta o instrucción de entrada": tv.Vigilados(),
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
    lineas = texto.split("\n")
    n_cita = sum(1 for l in lineas if l == LINEA_CITA_AIRFLOW)
    if n_cita != 1:
        errores.append(f"la línea de crédito del artículo de Airflow debe aparecer una vez y aparece {n_cita}")
    primera_cita = lineas.index(LINEA_CITA_AIRFLOW) if LINEA_CITA_AIRFLOW in lineas else -1
    resto = "\n".join(l for i, l in enumerate(lineas) if i != primera_cita)
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
    if n_cita == 1:
        titulos_cita = re.findall(r"(?m)^## (.+)$", texto.split(LINEA_CITA_AIRFLOW)[0])
        if not titulos_cita or not re.match(r"(?i)(\d+\.\s*)?licencia", titulos_cita[-1]):
            errores.append("la línea de crédito no está en la sección de licencia y créditos")
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
        f"## 20. Licencia y créditos\nMIT.\n\n{LINEA_CITA_AIRFLOW}\n"
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
    for malo in ("Lo hizo un asistente.", "Con un " + _b64("cHJvbXB0") + ".", "Hecho con " + tv.canario().capitalize() + ".", "Las fases del trabajo.", "El pro" + "fesor lo pidió.", "La asignatura de ETL.",
                 "Ver guia" + "_equipo/", "Usa IA aquí.", "Con inteligencia artificial.", "Un TODO pendiente.", "make" + "_readme.py", "Mail a alguien@correo.com.",
                 "El proyecto no maneja datos personales.", "No tratamos datos personales.", "Hoy no manejamos datos personales."):
        assert problemas_del_readme(_con("Texto, con comas.", malo), BASE_FALSA), malo


def _b64(texto):
    """Una palabra guardada en base64 en este archivo (así no aparece escrita)."""
    return base64.b64decode(texto).decode("utf-8")


def test_rutas_locales_se_detectan():
    assert problemas_del_readme(_con("Texto, con comas.", "En C:\\Us" + "ers\\alguien\\x."), BASE_FALSA)


def test_enlaces_e_imagenes_inexistentes_se_detectan():
    assert problemas_del_readme(_con("[requisitos](requirements.txt)", "[requisitos](no_existe.txt)"), BASE_FALSA)
    assert problemas_del_readme(_con("![Pruebas](README.md)", "![Pruebas](docs/img/no_existe.png)"), BASE_FALSA)
    assert problemas_del_readme(_con("![Pruebas](README.md)", "![](README.md)"), BASE_FALSA), "imagen sin texto alternativo"


def test_anclas_inexistentes_se_detectan():
    assert problemas_del_readme(_con("[la sección](#4-arquitectura)", "[la sección](#9-no-existe)"), BASE_FALSA)


def test_la_tabla_de_contenidos_debe_enlazar_cada_seccion():
    assert problemas_del_readme(_con("- [4. Arquitectura](#4-arquitectura)\n", ""), BASE_FALSA)
    assert problemas_del_readme(_bueno().replace("## 3. Tabla de contenidos", "## 3. Índice"), BASE_FALSA), "sin tabla de contenidos"


def test_la_cita_del_articulo_debe_existir_una_vez_y_en_la_seccion_de_licencia():
    assert problemas_del_readme(_bueno().replace(LINEA_CITA_AIRFLOW, ""), BASE_FALSA), "sin la cita"
    assert problemas_del_readme(_bueno() + "\n" + LINEA_CITA_AIRFLOW + "\n", BASE_FALSA), "dos veces"
    fuera = _bueno().replace(LINEA_CITA_AIRFLOW, "").replace("## 4. Arquitectura\n", "## 4. Arquitectura\n" + LINEA_CITA_AIRFLOW + "\n")
    assert any("crédito no está" in e for e in problemas_del_readme(fuera, BASE_FALSA))


def test_la_cita_del_articulo_no_admite_variantes_ni_otras_menciones():
    assert problemas_del_readme(_bueno().replace("Juan Manuel", "J. M."), BASE_FALSA), "cita editada"
    assert problemas_del_readme(_con("Texto, con comas.", "Basado en Núñez Velasco."), BASE_FALSA), "otra mención del autor"
    assert problemas_del_readme(_con("Texto, con comas.", "Ver el tutorial paso a paso."), BASE_FALSA), "otra mención del tutorial"


def aviso_de_licencia_correcto(texto):
    """True si la licencia es MIT y su aviso de derechos dice el año 2026 y los tres nombres completos, en ese orden."""
    lineas = texto.split("\n")
    return (lineas[0] == "MIT License" and len(lineas) > 2 and lineas[2] == "Copyright (c) 2026 " + ", ".join(NOMBRES_LICENCIA)
            and 'THE SOFTWARE IS PROVIDED "AS IS"' in texto and "Permission is hereby granted, free of charge" in texto)


def test_el_aviso_de_licencia_nombra_a_las_tres_personas_y_el_anio():
    assert aviso_de_licencia_correcto((ROOT / "LICENSE").read_text(encoding="utf-8"))


def test_un_aviso_de_licencia_alterado_se_detecta():
    real = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert aviso_de_licencia_correcto(real)
    assert not aviso_de_licencia_correcto(real.replace("2026", "2025", 1)), "otro año"
    assert not aviso_de_licencia_correcto(real.replace(", Jhoan Sebastián Castellanos Mayor", "", 1)), "falta un nombre"
    assert not aviso_de_licencia_correcto(real.replace("Diego Fernando Gordillo Londoño", "el equipo", 1)), "un nombre cambiado"
    assert not aviso_de_licencia_correcto(real.replace("MIT License", "Otra licencia", 1)), "otra licencia"


# ------------------------------------------------------------------------------------------------ el README real
README_TEXTO = (ROOT / "README.md").read_text(encoding="utf-8")
ORIGINALES = ("docs/diagramas/arquitectura_nueva.png", "docs/diagramas/flujo_dag_nueva.png")   # los dos diagramas en color aportados por Daniel (EV-112); no se tocan
DIAGRAMAS = ("docs/img/readme/arquitectura_gris.png", "docs/img/readme/flujo_dag_gris.png")   # sus copias en escala de grises, las que usa el README


def secciones_numeradas(texto):
    """Números de los encabezados de nivel 2 que empiezan por «N.», en orden."""
    return [int(re.match(r"(\d+)\.", t).group(1)) for n, t in _encabezados(texto) if n == 2 and re.match(r"\d+\.", t)]


def test_el_readme_real_cumple_la_guardiana():
    assert problemas_del_readme(README_TEXTO, ROOT) == []


def test_el_readme_tiene_las_veinte_secciones_numeradas_en_orden():
    assert secciones_numeradas(README_TEXTO) == list(range(1, 21))
    assert secciones_numeradas("## 1. A\n## 3. C\n") != list(range(1, 21)), "una sección que falta se detecta"
    assert secciones_numeradas("## 2. B\n## 1. A\n") != [1, 2], "el orden importa"


def test_el_readme_tiene_el_diagrama_de_arquitectura_y_la_seccion_de_primera_vez():
    assert re.search(r"!\[[^\]]*Arquitectura[^\]]*\]\([^)]+\)", README_TEXTO)
    assert any(re.search(r"(?i)primera vez", t) for _, t in _encabezados(README_TEXTO))


def test_el_readme_usa_las_copias_en_gris_de_los_diagramas_aportados_y_las_capturas_aprobadas():
    for ruta, original in zip(DIAGRAMAS, ORIGINALES):
        assert f"]({ruta})" in README_TEXTO, ruta
        assert (ROOT / ruta).is_file() and (ROOT / original).is_file(), ruta
        assert original not in README_TEXTO and "docs/diagramas/" not in README_TEXTO, "el README no apunta a los originales en color"
    for captura in ("airflow_dag", "phpmyadmin_tablas", "phpmyadmin_insert_rechazado", "panel_respuesta", "api_docs"):
        assert f"](docs/img/readme/{captura}.png)" in README_TEXTO, captura
    for insignia in ("python", "airflow", "mysql", "pruebas", "cobertura", "licencia", "madurez"):
        assert f"](docs/img/insignias/{insignia}.svg)" in README_TEXTO, insignia


def test_cada_figura_del_readme_tiene_un_pie_que_la_describe():
    figuras = re.findall(r"(?m)^\*Figura (\d+)\. (.+)\*$", README_TEXTO)
    assert [int(n) for n, _ in figuras] == list(range(1, len(figuras) + 1))
    assert len(figuras) == len(re.findall(r"(?m)^!\[[^\]]+\]\(docs/(?:diagramas|img/readme)/", README_TEXTO)), "una imagen sin pie o un pie sin imagen"
    assert all(t.startswith("Muestra ") for _, t in figuras), "el pie dice lo que la imagen muestra"


def copia_en_gris_corresponde_al_original(copia, original):
    """True si la copia es el original convertido a escala de grises, píxel por píxel (si alguien reemplaza el original, hay que volver a ejecutar `scripts/make_imagenes_readme.py`)."""
    from PIL import Image

    c, o = Image.open(copia), Image.open(original)
    return c.mode == "L" and c.size == o.size and c.tobytes() == o.convert("L").tobytes()


def test_las_copias_en_gris_son_los_originales_convertidos_y_estan_en_el_registro():
    registro = (ROOT / "docs" / "evidencias" / "readme" / "EV-111_imagenes_para_el_readme.txt").read_text(encoding="utf-8")
    for copia, original in zip(DIAGRAMAS, ORIGINALES):
        assert copia_en_gris_corresponde_al_original(ROOT / copia, ROOT / original), copia
        assert copia.split("/")[-1] in registro and original in registro, copia


def test_una_copia_que_no_corresponde_a_su_original_se_detecta(tmp_path):
    from PIL import Image

    color = tmp_path / "color.png"
    Image.new("RGB", (4, 4), (200, 30, 30)).save(color)
    buena, mala, otra_forma = tmp_path / "buena.png", tmp_path / "mala.png", tmp_path / "otra.png"
    Image.open(color).convert("L").save(buena)
    Image.new("L", (4, 4), 255).save(mala)
    Image.new("L", (5, 5), 0).save(otra_forma)
    assert copia_en_gris_corresponde_al_original(buena, color)
    assert not copia_en_gris_corresponde_al_original(mala, color), "otro contenido"
    assert not copia_en_gris_corresponde_al_original(otra_forma, color), "otro tamaño"
    assert not copia_en_gris_corresponde_al_original(color, color), "el original en color no es una copia en gris"


def test_el_readme_que_apunta_a_los_originales_en_color_se_detecta():
    malo = README_TEXTO.replace(DIAGRAMAS[0], ORIGINALES[0])
    assert malo != README_TEXTO and "docs/diagramas/" in malo
    assert f"]({DIAGRAMAS[0]})" not in malo
