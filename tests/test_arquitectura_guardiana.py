"""Guardiana del documento de arquitectura y de sus registros de decisión, ADR (D106): forma, redacción, enlaces, diagramas en texto y coherencia con DECISIONES.md.

Comprueba, sobre el texto: las 18 secciones en orden, sin emojis, sin guiones largos ni términos prohibidos, enlaces e imágenes válidos (también las anclas de otros archivos), los diagramas
en ASCII dentro del documento y su coherencia con la tabla de cajas y con el DAG real, y la única excepción de texto (el crédito del artículo de Airflow, una vez, en la sección 18 y solo en ese archivo).
De cada ADR comprueba su estructura y que lo que presenta como «consideradas entonces» está de verdad en DECISIONES.md. Las cifras del documento se vigilan en `tests/test_arquitectura_cifras.py`.
Cada regla tiene su prueba negativa con un texto sintético.
"""
import ast
import re

from src.common import ROOT
from tests.test_readme_guardiana import (ARCHIVO_DECLARACION, CORREO, EMOJIS, GUIONES, LINEA_CITA_AIRFLOW, RUTA_LOCAL, TERMINOS, _ancla, _encabezados, _sin_codigo)

DOC = ROOT / "docs" / "arquitectura" / "arquitectura_del_sistema.md"
ADRS = ROOT / "docs" / "arquitectura" / "adr"
DECISIONES = (ROOT / "docs" / "DECISIONES.md").read_text(encoding="utf-8")

# El único crédito de una fuente externa de método: la misma línea del README, con la ruta relativa de su enlace ajustada a la carpeta del documento (el texto es idéntico).
LINEA_CITA_DOC = LINEA_CITA_AIRFLOW.replace("](docs/orquestacion/", "](../orquestacion/")
TERMINOS_DEL_DOCUMENTO = {k: v for k, v in TERMINOS.items() if k != "cita externa fuera de su línea"}
CITA_EXTERNA = TERMINOS["cita externa fuera de su línea"]


# ------------------------------------------------------------------------------------------------ reglas generales de redacción y de enlaces
def secciones_numeradas(texto):
    return [int(re.match(r"(\d+)\.", t).group(1)) for n, t in _encabezados(texto) if n == 2 and re.match(r"\d+\.", t)]


def _enlaces_rotos(texto, base):
    """Enlaces e imágenes relativos que no existen, sin alt o con un ancla inexistente (en el mismo archivo o en otro de Markdown)."""
    errores = []
    anclas = {_ancla(t) for _, t in _encabezados(texto)}
    for m in re.finditer(r"(!?)\[([^\]]*)\]\(([^)\s]+)\)", re.sub(r"(?s)```.*?```", "", texto)):
        imagen, alt, destino = m.group(1) == "!", m.group(2), m.group(3)
        if destino.startswith(("http://", "https://", "mailto:")):
            continue
        ruta, _, ancla = destino.partition("#")
        if imagen and not alt.strip():
            errores.append(f"imagen sin texto alternativo: {destino}")
        if ruta and not (base / ruta).exists():
            errores.append(f"el enlace o la imagen no existe: {destino}")
        elif ruta and ancla and (base / ruta).suffix == ".md":
            if ancla not in {_ancla(t) for _, t in _encabezados((base / ruta).read_text(encoding="utf-8"))}:
                errores.append(f"ancla inexistente en {ruta}: #{ancla}")
        if not ruta and ancla and ancla not in anclas:
            errores.append(f"ancla inexistente: #{ancla}")
    return errores


def problemas_de_redaccion(texto, base):
    """Reglas de redacción comunes al documento y a los ADR (lista vacía si cumple). La cita del artículo no se admite en este nivel: la trata `problemas_del_documento`."""
    errores = []
    prosa = _sin_codigo(texto)
    if EMOJIS.search(texto):
        errores.append("hay emojis o símbolos gráficos")
    if GUIONES.search(texto):
        errores.append("hay guiones largos o medios")
    if re.search(r"(?<=\S) - (?=\S)", prosa):
        errores.append("hay un guion usado como separador de ideas")
    for nombre, patron in TERMINOS_DEL_DOCUMENTO.items():
        if patron.search(prosa) or patron.search(texto):
            errores.append(f"término prohibido: {nombre}")
    if CITA_EXTERNA.search(texto):
        errores.append("término prohibido: cita externa fuera de su línea")
    if "DECLARACION" + "_USO" in texto or ARCHIVO_DECLARACION in texto:
        errores.append("remite a la declaración de la raíz: solo lo hace el README")
    if CORREO.search(texto):
        errores.append("hay una dirección de correo")
    if RUTA_LOCAL.search(texto):
        errores.append("hay una ruta absoluta local")
    return errores + _enlaces_rotos(texto, base)


def problemas_del_documento(texto, base):
    """Reglas del documento de arquitectura: redacción, 18 secciones, metadatos honestos y la única excepción de texto."""
    lineas = texto.split("\n")
    n_cita = sum(1 for l in lineas if l == LINEA_CITA_DOC)
    errores = []
    if n_cita != 1:
        errores.append(f"la línea de crédito del artículo de Airflow debe aparecer una vez y aparece {n_cita}")
    else:
        titulos = re.findall(r"(?m)^## (.+)$", texto.split(LINEA_CITA_DOC)[0])
        if not titulos or not re.match(r"18\.", titulos[-1]):
            errores.append("la línea de crédito no está en la sección 18")
    resto = "\n".join(l for l in lineas if l != LINEA_CITA_DOC)
    errores += problemas_de_redaccion(resto, base)
    if secciones_numeradas(texto) != list(range(1, 19)):
        errores.append("las secciones numeradas no son 1 a 18 en orden")
    # metadatos honestos: la tabla de la sección 1 dice Borrador, revisión y aprobadores pendientes y repositorio sin publicar (no basta con que la palabra aparezca en otro lugar)
    portada = re.search(r"(?ms)^## 1\. .*?(?=^## 2\. )", texto)
    portada = portada.group(0) if portada else ""
    for regla, descripcion in ((r"(?m)^\| Estado \| Borrador \|$", "estado Borrador"), (r"(?m)^\| Revisión de la documentación \| pendiente\b", "revisión pendiente"),
                               (r"(?m)^\| Aprobadores \| pendiente \|$", "aprobadores pendientes"), (r"(?m)^\| Repositorio \| aún no está publicado\b", "repositorio sin publicar")):
        if not re.search(regla, portada):
            errores.append(f"falta en los metadatos de la sección 1: {descripcion}")
    return errores


# ------------------------------------------------------------------------------------------------ diagramas en texto
TITULOS_DE_DIAGRAMAS = ("Diagrama de contexto", "Diagrama de contenedores", "Flujo de datos", "Secuencia del camino feliz del DAG", "Secuencia del camino de fallo y la recuperación")


def diagramas(texto):
    """{título: bloque} de cada encabezado de nivel 3 cuyo primer bloque de código, antes del siguiente encabezado, es un diagrama (bloque sin lenguaje)."""
    salida, titulo, dentro, bloque = {}, None, False, []
    for linea in texto.split("\n"):
        if not dentro and linea.startswith("#"):
            titulo = linea[4:].strip() if linea.startswith("### ") else None
        elif linea == "```" and not dentro and titulo and titulo not in salida:
            dentro, bloque = True, []
        elif linea.startswith("```") and dentro:
            salida[titulo] = "\n".join(bloque) + "\n"
            dentro = False
        elif dentro:
            bloque.append(linea)
    return salida


def problemas_de_diagramas(texto, tareas_del_dag):
    errores = []
    d = diagramas(texto)
    for titulo in TITULOS_DE_DIAGRAMAS:
        if titulo not in d:
            errores.append(f"falta el diagrama: {titulo}")
    for titulo, bloque in d.items():
        if titulo not in TITULOS_DE_DIAGRAMAS:
            continue
        if any(ord(c) > 127 for c in bloque):
            errores.append(f"el diagrama «{titulo}» tiene caracteres que no son ASCII")
        if max(len(l) for l in bloque.splitlines()) > 100:
            errores.append(f"el diagrama «{titulo}» pasa de 100 columnas")
        if len(bloque.splitlines()) < 5:
            errores.append(f"el diagrama «{titulo}» tiene menos de 5 líneas")
    # las cajas del diagrama de contenedores son las de su tabla
    if "Diagrama de contenedores" in d:
        etiquetas = set(re.findall(r"\[([^\]]+)\]", d["Diagrama de contenedores"]))
        tabla = re.search(r"(?s)### Cajas del diagrama de contenedores\n\| Caja \| Qué es \|\n\|---\|---\|\n(.*?)\n\n", texto)
        cajas = set(re.findall(r"(?m)^\| ([^|]+?) \|", tabla.group(1))) if tabla else set()
        if etiquetas != cajas:
            errores.append(f"las cajas del diagrama y de su tabla no coinciden: {sorted(etiquetas ^ cajas)}")
    # las cuatro tareas del DAG real, en su orden, en las dos secuencias
    for titulo in ("Secuencia del camino feliz del DAG", "Secuencia del camino de fallo y la recuperación"):
        if titulo in d:
            posiciones = [d[titulo].find(t) for t in tareas_del_dag]
            if -1 in posiciones or posiciones != sorted(posiciones):
                errores.append(f"«{titulo}» no nombra las tareas del DAG en su orden")
    if "Secuencia del camino de fallo y la recuperación" in d:
        for pieza in ("fallo_inducido", "upstream_failed", "RuntimeError", "ANTES de producir", "ya_cargada"):
            if pieza not in d["Secuencia del camino de fallo y la recuperación"]:
                errores.append(f"el camino de fallo no menciona {pieza}")
    if "Secuencia del camino feliz del DAG" in d and "ya_cargada" not in d["Secuencia del camino feliz del DAG"]:
        errores.append("el camino feliz no menciona ya_cargada")
    if "Flujo de datos" in d:
        for pieza in ("BRONZE", "SILVER", "GOLD", "SQLite", "MySQL"):
            if pieza not in d["Flujo de datos"]:
                errores.append(f"el flujo de datos no menciona {pieza}")
    return errores


def tareas_del_dag_real():
    """Funciones decoradas con @task en el DAG versionado, en el orden en que se definen."""
    arbol = ast.parse((ROOT / "dags" / "medallon_etl_dag.py").read_text(encoding="utf-8"))
    return [n.name for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef) and any(isinstance(d, ast.Name) and d.id == "task" for d in n.decorator_list)]


# ------------------------------------------------------------------------------------------------ ADR
def texto_de_origen(decisiones, token):
    """Texto de DECISIONES.md que respalda un origen: «D40», «D-FUENTES» o «sección «Título»»; None si no existe."""
    token = token.strip()
    m = re.fullmatch(r"D(\d+)", token)
    if m:
        n = int(m.group(1))
        patron = rf"(?m)^\| D{n} \|.*$" if n <= 10 else rf"(?m)^\*\*D{n} · .*$"
        r = re.search(patron, decisiones)
        return r.group(0) if r else None
    if token == "D-FUENTES":
        r = re.search(r"(?s)## D-FUENTES.*?(?=\n## |\Z)", decisiones)
        return r.group(0) if r else None
    m = re.fullmatch(r"sección «(.+)»", token)
    if m:
        r = re.search(rf"(?s)#+ {re.escape(m.group(1))}\n.*?(?=\n#|\Z)", decisiones)
        return r.group(0) if r else None
    return None


def origenes_de(texto_adr):
    m = re.search(r"\*\*D de origen:\*\* (.+?)\. \*\*Propietario", texto_adr)
    return [t.strip() for t in re.split(r",(?![^«]*»)", m.group(1))] if m else []


def _bloque(texto, titulo, nivel="##"):
    m = re.search(rf"(?ms)^{nivel} {re.escape(titulo)}\n(.*?)(?=^#{{1,{len(nivel)}}} |\Z)", texto)
    return m.group(1) if m else None


def problemas_de_adr(texto, nombre, decisiones):
    """Reglas de un ADR (lista vacía si cumple): estructura, origen en DECISIONES.md y alternativas «entonces» realmente registradas."""
    errores = []
    m = re.fullmatch(r"adr-(\d{3})_[a-z0-9_]+\.md", nombre)
    if not m:
        return [f"nombre de archivo inválido: {nombre}"]
    if not texto.startswith(f"# ADR-{m.group(1)}: "):
        errores.append("el título no lleva el número del archivo")
    for campo in ("**Estado:**", "**Fecha de la decisión:**", "**D de origen:**", "**Propietario técnico:** Daniel Alexander Brand García", "**Revisión:** pendiente"):
        if campo not in texto:
            errores.append(f"falta el campo {campo}")
    titulos = [t for n, t in _encabezados(texto)]
    esperados = ["Contexto", "Decisión", "Consecuencias", "Positivas", "Negativas", "Alternativas consideradas entonces", "Alternativas que hoy descartamos y por qué"]
    if titulos != esperados:
        errores.append(f"las secciones no son las esperadas: {titulos}")
        return errores
    origenes = origenes_de(texto)
    textos = {o: texto_de_origen(decisiones, o) for o in origenes}
    if not origenes or any(v is None for v in textos.values()):
        errores.append(f"un origen no existe en DECISIONES.md: {[o for o, v in textos.items() if v is None]}")
    for seccion, nivel in (("Positivas", "###"), ("Negativas", "###")):
        if not re.search(r"(?m)^- ", _bloque(texto, seccion, nivel) or ""):
            errores.append(f"«{seccion}» no tiene ningún punto")
    entonces = _bloque(texto, "Alternativas consideradas entonces") or ""
    if "No se registraron alternativas." not in entonces:
        if "Registradas en `docs/DECISIONES.md`:" not in entonces:
            errores.append("«entonces» no dice que las alternativas están registradas")
        puntos = re.findall(r"(?m)^- (.+)$", entonces)
        if not puntos:
            errores.append("«entonces» no tiene alternativas")
        for p in puntos:
            r = re.fullmatch(r"(.+) \((D\d+|D-FUENTES|sección «.+?»)\)", p)
            if not r:
                errores.append(f"una alternativa «entonces» no cita su D: {p}")
                continue
            alternativa, origen = r.group(1).lower(), r.group(2)
            if origen not in origenes:
                errores.append(f"la alternativa cita {origen}, que no es un origen del ADR: {p}")
            elif alternativa not in (textos.get(origen) or "").lower():
                errores.append(f"alternativa que DECISIONES.md no registra en {origen}: {p}")
    hoy = _bloque(texto, "Alternativas que hoy descartamos y por qué") or ""
    if not hoy.lstrip().startswith("Razonamiento actual del equipo, no registrado en su momento."):
        errores.append("«hoy» no está rotulado como razonamiento actual")
    puntos_hoy = re.findall(r"(?m)^- \*\*.+", hoy)
    if len(puntos_hoy) < 2:
        errores.append("«hoy» tiene menos de dos alternativas")
    if not any(re.search(r"\d", p) for p in puntos_hoy):
        errores.append("«hoy» no apoya ninguna alternativa en un hecho medible")
    citadas = set(re.findall(r"\bD(\d+)\b", texto))
    for n in citadas:
        if texto_de_origen(decisiones, f"D{n}") is None:
            errores.append(f"cita D{n}, que no existe")
    return errores


def archivos_adr():
    return sorted(ADRS.glob("adr-*.md"))


# ------------------------------------------------------------------------------------------------ pruebas sobre los archivos reales
def test_el_documento_real_cumple_la_guardiana():
    assert problemas_del_documento(DOC.read_text(encoding="utf-8"), DOC.parent) == []


def test_los_diagramas_reales_son_texto_ascii_coherente_con_el_dag_y_con_sus_cajas():
    assert tareas_del_dag_real() == ["validar_bronze", "transformar_a_silver", "integrar_a_gold", "cargar_datawarehouse"]
    assert problemas_de_diagramas(DOC.read_text(encoding="utf-8"), tareas_del_dag_real()) == []


def test_los_adr_reales_cumplen_su_estructura_y_su_origen():
    assert archivos_adr(), "no hay ADR"
    for ruta in archivos_adr():
        assert problemas_de_adr(ruta.read_text(encoding="utf-8"), ruta.name, DECISIONES) == [], ruta.name
        assert problemas_de_redaccion(ruta.read_text(encoding="utf-8"), ruta.parent) == [], ruta.name


def test_la_numeracion_de_los_adr_es_consecutiva_y_el_indice_del_documento_los_lista_todos():
    numeros = [int(re.match(r"adr-(\d{3})", r.name).group(1)) for r in archivos_adr()]
    assert numeros == list(range(1, len(numeros) + 1)) and 10 <= len(numeros) <= 14
    seccion = _bloque(DOC.read_text(encoding="utf-8"), "10. Decisiones y ADR") or ""
    filas = re.findall(r"(?m)^\| \[(ADR-\d{3})\]\((adr/[^)]+)\) \| (.+?) \| (.+?) \|$", seccion)
    assert [f[1].split("/")[-1] for f in filas] == [r.name for r in archivos_adr()]
    for (_, ruta, titulo, origen), adr in zip(filas, archivos_adr()):
        texto = adr.read_text(encoding="utf-8")
        assert texto.splitlines()[0].split(": ", 1)[1] == titulo, adr.name
        assert origen.split(", ") == origenes_de(texto), adr.name


def test_d106_registra_la_estructura_y_marca_d21_y_d5_sin_reescribirlas():
    d106 = texto_de_origen(DECISIONES, "D106")
    assert d106 and "docs/arquitectura/adr/" in d106 and "Alternativas que hoy descartamos y por qué" in d106
    d21, d5 = texto_de_origen(DECISIONES, "D21"), texto_de_origen(DECISIONES, "D5")
    assert "**Modificada por D57 y D92:**" in d21 and "variante ligera (ejecutor local, sin Redis ni Celery)" in d21 and "**Fecha:** 2026-11-12." in d21, "D21 conserva su texto original"
    assert "**Modificada por D106**" in d5 and "shapely queda instalado como contingencia" in d5, "D5 conserva su texto original"


# ------------------------------------------------------------------------------------------------ casos sintéticos
def _doc_bueno():
    cuerpo = "\n".join(f"## {n}. Sección {n}\nTexto." for n in range(2, 18))
    return ("# Título\n\n## 1. Portada\n| Campo | Valor |\n|---|---|\n| Estado | Borrador |\n| Revisión de la documentación | pendiente (alguien) |\n| Aprobadores | pendiente |\n"
            f"| Repositorio | aún no está publicado |\n\n{cuerpo}\n## 18. Glosario y referencias\nTexto. Un Borrador más.\n\n{LINEA_CITA_DOC}\n")


def test_un_documento_correcto_no_tiene_problemas():
    assert problemas_del_documento(_doc_bueno(), ROOT / "docs" / "arquitectura") == []


def test_la_linea_de_la_cita_es_la_del_readme_con_la_ruta_ajustada():
    assert LINEA_CITA_DOC != LINEA_CITA_AIRFLOW
    assert LINEA_CITA_DOC.replace("](../orquestacion/", "](docs/orquestacion/") == LINEA_CITA_AIRFLOW
    assert (ROOT / "docs" / "arquitectura" / "../orquestacion/diferencias_con_la_guia.md").is_file()


def test_la_cita_del_articulo_solo_vale_una_vez_en_la_ultima_seccion_y_sin_variantes():
    base = ROOT / "docs" / "arquitectura"
    assert problemas_del_documento(_doc_bueno().replace(LINEA_CITA_DOC, ""), base), "sin la cita"
    assert problemas_del_documento(_doc_bueno() + "\n" + LINEA_CITA_DOC + "\n", base), "dos veces"
    fuera = _doc_bueno().replace(LINEA_CITA_DOC, "").replace("## 2. Sección 2\n", "## 2. Sección 2\n" + LINEA_CITA_DOC + "\n")
    assert any("sección 18" in e for e in problemas_del_documento(fuera, base))
    assert problemas_del_documento(_doc_bueno().replace("Juan Manuel", "J. M."), base), "cita editada"
    assert problemas_del_documento(_doc_bueno().replace("Texto.", "Basado en Núñez Velasco.", 1), base), "otra mención del autor"
    assert problemas_del_documento(_doc_bueno().replace("Texto.", "Ver el tutorial paso a paso.", 1), base), "otra mención del tutorial"


def test_la_excepcion_de_la_cita_no_vale_para_los_adr():
    adr = (ADRS / archivos_adr()[0].name).read_text(encoding="utf-8")
    assert problemas_de_redaccion(adr + "\n" + LINEA_CITA_DOC + "\n", ADRS), "la cita en un ADR"
    assert problemas_de_redaccion(adr + "\nVer el artículo de Núñez Velasco.\n", ADRS)


def test_las_reglas_de_redaccion_detectan_lo_prohibido():
    base = ROOT / "docs" / "arquitectura"
    for malo in ("un emoji \U0001F680", "un guion \u2014 largo", "un rango 1\u20132", "un guion - suelto", "Lo hizo un asistente.", "Con un pro" + "mpt.", "Las fases del trabajo.", "El pro" + "fesor lo pidió.",
                 "La asignatura de ETL.", "Ver guia" + "_equipo/", "Usa IA aquí.", "Un TODO pendiente.", "Escriba a alguien@correo.com.", "En C:\\Us" + "ers\\alguien\\x.", "Ver " + ARCHIVO_DECLARACION + "."):
        assert problemas_del_documento(_doc_bueno().replace("Texto.", malo, 1), base), malo


def test_un_guion_dentro_de_codigo_o_de_una_lista_no_se_detecta():
    assert problemas_del_documento(_doc_bueno().replace("Texto.", "Use `pip - x` y\n- una viñeta\n```\na - b\n```", 1), ROOT / "docs" / "arquitectura") == []


def test_enlaces_imagenes_y_anclas_rotos_se_detectan():
    base = ROOT / "docs" / "arquitectura"
    assert problemas_del_documento(_doc_bueno().replace("Texto.", "[x](no_existe.md)", 1), base)
    assert problemas_del_documento(_doc_bueno().replace("Texto.", "![](../../README.md)", 1), base), "imagen sin alt"
    assert problemas_del_documento(_doc_bueno().replace("Texto.", "[x](#9-no-existe)", 1), base), "ancla propia"
    assert problemas_del_documento(_doc_bueno().replace("Texto.", "[x](../../README.md#9-no-existe)", 1), base), "ancla en otro archivo"


def test_las_secciones_y_los_metadatos_se_exigen():
    base = ROOT / "docs" / "arquitectura"
    assert problemas_del_documento(_doc_bueno().replace("## 7. Sección 7\nTexto.\n", ""), base), "falta una sección"
    assert problemas_del_documento(_doc_bueno().replace("## 3. Sección 3", "## 4. Sección 3"), base), "numeración"
    assert problemas_del_documento(_doc_bueno().replace("| Estado | Borrador |", "| Estado | Aprobado |"), base), "estado inventado aunque la palabra aparezca en otro lugar"
    assert problemas_del_documento(_doc_bueno().replace("| Aprobadores | pendiente |", "| Aprobadores | Alguien |"), base), "aprobadores inventados"
    assert problemas_del_documento(_doc_bueno().replace("| Revisión de la documentación | pendiente (alguien) |", "| Revisión de la documentación | aprobada (alguien) |"), base), "revisión inventada"
    assert problemas_del_documento(_doc_bueno().replace("aún no está publicado", "https://ejemplo.invalido/repo"), base), "repositorio inventado"
    assert problemas_del_documento(_doc_bueno().replace("## 1. Portada\n", "## 1. Portada\nTexto.\n").replace("| Estado | Borrador |\n", ""), base), "falta el estado"


def _diagramas_buenos():
    tareas = tareas_del_dag_real()
    ordenadas = "\n".join(f"      | {t}" for t in tareas)
    return ("### Diagrama de contexto\n```\n+---+\n| a |\n+---+\n| b |\n+---+\n```\n"
            "### Diagrama de contenedores\n```\n [Pipeline] --> [SQLite]\n a\n b\n c\n d\n```\n"
            "### Cajas del diagrama de contenedores\n| Caja | Qué es |\n|---|---|\n| Pipeline | x |\n| SQLite | y |\n\n"
            "### Flujo de datos\n```\nBRONZE SILVER GOLD SQLite MySQL\n a\n b\n c\n d\n```\n"
            f"### Secuencia del camino feliz del DAG\n```\n{ordenadas}\n ya_cargada\n a\n```\n"
            f"### Secuencia del camino de fallo y la recuperación\n```\n{ordenadas}\n fallo_inducido upstream_failed RuntimeError ANTES de producir ya_cargada\n```\n")


def test_unos_diagramas_correctos_no_tienen_problemas():
    assert problemas_de_diagramas(_diagramas_buenos(), tareas_del_dag_real()) == []


def test_los_diagramas_incorrectos_se_detectan():
    t = tareas_del_dag_real()
    assert problemas_de_diagramas(_diagramas_buenos().replace("### Flujo de datos", "### Otro"), t), "falta un diagrama"
    assert problemas_de_diagramas(_diagramas_buenos().replace("+---+", "\u250c\u2500\u2500\u2500\u2510", 1), t), "caracteres que no son ASCII"
    assert problemas_de_diagramas(_diagramas_buenos().replace(" a\n b\n c\n d\n```\n### Cajas", " " + "x" * 120 + "\n b\n c\n d\n```\n### Cajas"), t), "más de 100 columnas"
    assert problemas_de_diagramas(_diagramas_buenos().replace("| SQLite | y |", "| MySQL | y |"), t), "una caja de la tabla que no está en el diagrama"
    assert problemas_de_diagramas(_diagramas_buenos().replace("[SQLite]", "[SQLite] [Panel]"), t), "una caja del diagrama que no está en la tabla"
    assert problemas_de_diagramas(_diagramas_buenos().replace(t[1], "otra_tarea"), t), "una tarea del DAG que falta"
    assert problemas_de_diagramas(_diagramas_buenos().replace("upstream_failed", ""), t), "el camino de fallo sin su estado"
    assert problemas_de_diagramas(_diagramas_buenos().replace("RuntimeError", "").replace("ANTES de producir", ""), t), "el fallo sin su causa"


def _adr_bueno():
    return ("# ADR-001: Algo\n\n**Estado:** Vigente. **Fecha de la decisión:** 2026-10-15. **D de origen:** D6. **Propietario técnico:** Daniel Alexander Brand García. **Revisión:** pendiente.\n\n"
            "## Contexto\nTexto.\n\n## Decisión\nTexto.\n\n## Consecuencias\n### Positivas\n- Algo bueno.\n\n### Negativas\n- Algo malo.\n\n"
            "## Alternativas consideradas entonces\nRegistradas en `docs/DECISIONES.md`:\n- CSV consolidado (D6)\n\n"
            "## Alternativas que hoy descartamos y por qué\nRazonamiento actual del equipo, no registrado en su momento.\n- **Una.** Con 11 MB basta.\n- **Otra.** Texto.\n")


def test_un_adr_correcto_no_tiene_problemas():
    assert problemas_de_adr(_adr_bueno(), "adr-001_algo.md", DECISIONES) == []


def test_los_adr_incorrectos_se_detectan():
    d = DECISIONES
    assert problemas_de_adr(_adr_bueno(), "adr1.md", d), "nombre de archivo"
    assert problemas_de_adr(_adr_bueno().replace("# ADR-001:", "# ADR-002:"), "adr-001_algo.md", d), "número del título"
    assert problemas_de_adr(_adr_bueno().replace("**Revisión:** pendiente", "**Revisión:** aprobada"), "adr-001_algo.md", d), "revisión inventada"
    assert problemas_de_adr(_adr_bueno().replace("## Contexto\nTexto.\n\n", ""), "adr-001_algo.md", d), "falta una sección"
    assert problemas_de_adr(_adr_bueno().replace("**D de origen:** D6.", "**D de origen:** D999."), "adr-001_algo.md", d), "origen inexistente"
    assert problemas_de_adr(_adr_bueno().replace("- Algo malo.", ""), "adr-001_algo.md", d), "consecuencias negativas vacías"


def test_una_alternativa_que_decisiones_no_registra_no_puede_presentarse_como_consideradas_entonces():
    d = DECISIONES
    inventada = _adr_bueno().replace("- CSV consolidado (D6)", "- Spark en un clúster (D6)")
    assert any("no registra" in e for e in problemas_de_adr(inventada, "adr-001_algo.md", d))
    sin_d = _adr_bueno().replace("- CSV consolidado (D6)", "- CSV consolidado")
    assert problemas_de_adr(sin_d, "adr-001_algo.md", d)
    otra_d = _adr_bueno().replace("- CSV consolidado (D6)", "- CSV consolidado (D10)")
    assert problemas_de_adr(otra_d, "adr-001_algo.md", d), "una D que no es de origen"
    de_otra_decision = _adr_bueno().replace("- CSV consolidado (D6)", "- Solo CSV (D6)")
    assert problemas_de_adr(de_otra_decision, "adr-001_algo.md", d), "una alternativa de otra decisión"
    sin_registro = _adr_bueno().replace("Registradas en `docs/DECISIONES.md`:\n- CSV consolidado (D6)", "No se registraron alternativas.")
    assert problemas_de_adr(sin_registro, "adr-001_algo.md", d) == [], "declarar que no hubo es válido"


def test_el_bloque_de_hoy_debe_estar_rotulado_y_apoyarse_en_un_hecho():
    d = DECISIONES
    assert problemas_de_adr(_adr_bueno().replace("Razonamiento actual del equipo, no registrado en su momento.\n", ""), "adr-001_algo.md", d), "sin rótulo"
    assert problemas_de_adr(_adr_bueno().replace("Con 11 MB basta.", "Basta."), "adr-001_algo.md", d), "sin ningún hecho medible"
    assert problemas_de_adr(_adr_bueno().replace("- **Otra.** Texto.\n", ""), "adr-001_algo.md", d), "una sola alternativa"


def test_los_origenes_se_leen_de_decisiones_por_numero_por_d_fuentes_y_por_seccion():
    assert "CSV consolidado" in texto_de_origen(DECISIONES, "D6")
    assert "G1" in texto_de_origen(DECISIONES, "D-FUENTES")
    assert "nombre normalizado" in texto_de_origen(DECISIONES, "sección «Llave del JOIN»")
    assert texto_de_origen(DECISIONES, "D999") is None and texto_de_origen(DECISIONES, "D-INVENTADA") is None
    assert origenes_de("**D de origen:** D4, D-FUENTES, sección «Llave del JOIN». **Propietario") == ["D4", "D-FUENTES", "sección «Llave del JOIN»"]
