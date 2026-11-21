"""Guardianes del PDF del documento de arquitectura y de los ADR (`scripts/arquitectura/generar_pdf_arquitectura.py`).

Por qué existe: el PDF sale del mismo texto que vigilan las pruebas del documento, pero un enlace que no apunta a ningún lado, un título sin marcador, una fecha distinta en cada ejecución o un carácter que
la fuente no dibuja solo se notan al abrirlo. Aquí se comprueba, sin abrir ningún navegador: (1) que el HTML traiga la portada, el índice, el documento y los 15 ADR seguidos, con el salto de página solo antes del anexo, y las dos figuras grises en las secciones 6 y 9 con su leyenda; (2) que cada
enlace interno tenga su destino, que un enlace a un ADR o a una sección sea interno y que el resto quede como ruta en código; (3) que todo carácter quepa en las fuentes estándar y no haya emojis ni guiones largos;
(4) que el pie y los parámetros de impresión pidan marcadores, pie en todas las páginas y A4; (5) que las fechas del PDF se fijen sin cambiar su longitud; y (6) las reglas con las que se juzga un PDF real
(marcadores uno por título, enlaces, fechas, páginas). El paso que imprime con Edge se comprueba con `python scripts/arquitectura/generar_pdf_arquitectura.py --verificar` (EV-117), no aquí.
Qué NO demuestra: que el PDF se vea bien (eso se revisa mirando páginas) ni que otro equipo obtenga el mismo sha256.
"""
import importlib.util
import re
import subprocess
import sys

import pytest

from src.common import ROOT

CARPETA = ROOT / "scripts" / "arquitectura"
DOC = ROOT / "docs" / "arquitectura" / "arquitectura_del_sistema.md"
ADRS = sorted((ROOT / "docs" / "arquitectura" / "adr").glob("adr-*.md"))


def _cargar():
    espec = importlib.util.spec_from_file_location("generar_pdf_arquitectura", CARPETA / "generar_pdf_arquitectura.py")
    modulo = importlib.util.module_from_spec(espec)
    sys.path.insert(0, str(CARPETA))
    try:
        espec.loader.exec_module(modulo)
    finally:
        sys.path.remove(str(CARPETA))
    return modulo


gen = _cargar()
HTML = gen.construir_html()
DATOS = gen.metadatos(DOC.read_text(encoding="utf-8"))


def test_el_html_trae_la_portada_el_indice_el_documento_y_los_adr_seguidos():
    assert 'class="portada"' in HTML and 'id="titulo-de-la-guia"' in HTML and 'class="indice"' in HTML
    assert len(ADRS) == 15
    adrs_en_html = re.findall(r'<h2 id="(adr-\d{3}-[^"]*)" class="adr"', HTML)
    assert len(adrs_en_html) == len(ADRS) == len(set(adrs_en_html))
    assert [a[:7] for a in adrs_en_html] == [f"adr-{n:03d}" for n in range(1, 16)], "los ADR salen en orden"
    secciones = re.findall(r'<h2 id="(\d+)-', HTML)
    assert secciones == [str(n) for n in range(1, 19)], "las 18 secciones del documento salen en orden"
    assert "Anexo. Registros de decisión (ADR)" in HTML
    indice = re.search(r'(?s)<nav class="indice">.*?</nav>', HTML).group(0)
    assert all(f'href="#{a}"' in indice for a in adrs_en_html), "el índice lista los 15 ADR"
    assert all(re.search(rf'href="#{n}-', indice) for n in range(1, 19)), "y las 18 secciones"
    regla_adr = re.search(r"h2\.adr \{[^}]*\}", gen.ESTILO_EXTRA).group(0)
    assert "page-break-before" not in regla_adr, "los ADR van seguidos: ninguno empieza en página nueva"
    assert re.search(r"h1 \{[^}]*page-break-before: always", gen.gen.ESTILO), "el título del anexo sí empieza en página nueva"
    assert re.search(r'<h1 id="anexo-registros-de-decisión-adr"(?! class="continuo")', HTML), "el anexo no es una parte continua"


def test_las_dos_figuras_grises_van_en_las_secciones_6_y_9_con_su_leyenda_y_las_de_color_no_se_incrustan():
    import base64

    figuras = re.findall(r"(?s)<figure>(.*?)</figure>", HTML)
    assert len(figuras) == 2 == len(gen.FIGURAS)
    assert [re.search(r"Figura (\d+)\.", f).group(1) for f in figuras] == ["1", "2"]
    pos = {n: HTML.index(f'<h2 id="{n}-') for n in (6, 7, 9, 10)}
    assert pos[6] < HTML.index("Figura 1.") < pos[7] and pos[9] < HTML.index("Figura 2.") < pos[10], "cada figura está en su sección"
    for _, ruta, _, leyenda in gen.FIGURAS:
        assert (ROOT / ruta).is_file() and f"data:image/png;base64,{base64.b64encode((ROOT / ruta).read_bytes()).decode()}" in HTML, ruta
        yaml_citado = re.search(r"`(docs/diagramas/[a-z_]+\.yaml)`", leyenda).group(1)
        assert (ROOT / yaml_citado).is_file() and (ROOT / yaml_citado).with_suffix(".png") == ROOT / ruta, "la leyenda cita la fuente de la imagen"
    for color in ("arquitectura_nueva.png", "flujo_dag_nueva.png"):
        assert base64.b64encode((ROOT / "docs" / "diagramas" / color).read_bytes()).decode()[:200] not in HTML, f"{color} no se incrusta"
    assert "Figura 1." not in DOC.read_text(encoding="utf-8"), "las figuras se agregan al PDF sin tocar el Markdown"
    with pytest.raises(ValueError):
        gen.insertar_figuras("<h2 id=\"otra-cosa\">x</h2>")
    assert gen.insertar_figuras('<h2 id="6-vista-de-alto-nivel">6</h2>', gen.FIGURAS[:1]).count("<figure>") == 1


def test_cada_enlace_interno_tiene_su_destino_y_ningun_enlace_apunta_a_un_archivo():
    ids = set(re.findall(r'\bid="([^"]+)"', HTML))
    hrefs = re.findall(r'href="([^"]+)"', HTML)
    internos = [h for h in hrefs if h.startswith("#")]
    assert len(internos) >= 36, "al menos los 36 enlaces del documento a los ADR"
    assert sorted({h for h in internos if h[1:] not in ids}) == []
    assert [h for h in hrefs if not h.startswith("#")] == [], "ningún enlace sale del PDF"
    assert not re.search(r'href="[^"#][^"]*\.md', HTML)
    assert "#titulo-del-documento" in HTML or 'id="titulo-del-documento"' in HTML


def test_un_enlace_a_un_adr_o_a_una_seccion_es_interno_y_a_otro_archivo_queda_como_ruta():
    anclas = {"adr-003_almacenamiento_dual_sin_orm.md": "adr-003-almacenamiento"}
    base = DOC.parent
    assert gen.convertir_enlaces("[ADR-003](adr/adr-003_almacenamiento_dual_sin_orm.md)", base, anclas) == "[ADR-003](#adr-003-almacenamiento)"
    assert gen.convertir_enlaces("[glosario](arquitectura_del_sistema.md#18-glosario-y-referencias)", base, anclas) == "[glosario](#18-glosario-y-referencias)"
    assert gen.convertir_enlaces("[docs/DECISIONES.md](../DECISIONES.md)", base, anclas) == "`docs/DECISIONES.md`"
    assert gen.convertir_enlaces("[DECISIONES.md](../DECISIONES.md)", base, anclas) == "`docs/DECISIONES.md`"
    assert gen.convertir_enlaces("[las decisiones](../DECISIONES.md)", base, anclas) == "las decisiones (`docs/DECISIONES.md`)"
    assert gen.convertir_enlaces("[adr/](adr/)", base, anclas) == "`docs/arquitectura/adr/`"
    assert gen.convertir_enlaces("[README](../../README.md#19-contacto-y-responsables)", base, anclas) == "README (`README.md#19-contacto-y-responsables`)"
    assert gen.convertir_enlaces("[web](https://example.org/x) y [aquí](#algo)", base, anclas) == "[web](https://example.org/x) y [aquí](#algo)"
    with pytest.raises(ValueError):
        gen.convertir_enlaces("[roto](../no_existe.md)", base, anclas)


def test_todo_caracter_del_texto_cabe_en_las_fuentes_estandar_y_no_hay_emojis_ni_guiones_largos():
    texto = DOC.read_text(encoding="utf-8") + "".join(a.read_text(encoding="utf-8") for a in ADRS)
    fuera = sorted({c for c in texto if ord(c) > 127 and not _en_winansi(c)})
    assert fuera == [], f"caracteres que una fuente estándar no dibuja: {fuera}"
    assert not re.search("[‒–—―\U0001F000-\U0001FAFF☀-➿⬀-⯿️‍]", texto)
    assert _en_winansi("á") and _en_winansi("«") and not _en_winansi("≈") and not _en_winansi("→")


def _en_winansi(c):
    try:
        c.encode("cp1252")
        return True
    except UnicodeEncodeError:
        return False


def test_el_pie_y_los_parametros_de_impresion_piden_marcadores_pie_en_todas_las_paginas_y_a4():
    p = gen.parametros_del_pdf(gen.pie_del_pdf(DATOS))
    assert p["generateDocumentOutline"] is True and p["displayHeaderFooter"] is True and p["preferCSSPageSize"] is True and p["printBackground"] is True
    assert "Página" in p["footerTemplate"] and "pageNumber" in p["footerTemplate"] and "totalPages" in p["footerTemplate"]
    version, fecha, estado = gen.version_y_estado(DATOS)
    assert (version, estado) == ("1.0", "Aprobado") and re.fullmatch(r"\d{4}-\d{2}-\d{2}", fecha)
    assert f"versión {version} · {estado}" in p["footerTemplate"], "el pie lleva la versión y el estado de la portada"
    assert "@page portada" in gen.ESTILO_EXTRA and "size: A4" in gen.gen.ESTILO


def test_los_metadatos_de_la_portada_se_exigen_y_se_leen_bien():
    assert set(gen.CAMPOS_DE_PORTADA) <= set(DATOS)
    sin_estado = DOC.read_text(encoding="utf-8").replace("| Estado | Aprobado |\n", "")
    with pytest.raises(ValueError):
        gen.metadatos(sin_estado)
    with pytest.raises(ValueError):
        gen.version_y_estado({**DATOS, "Versión y fecha": "0.2"})
    assert gen.version_y_estado({**DATOS, "Versión y fecha": "1.0, 2027-01-02", "Estado": "Aprobado"}) == ("1.0", "2027-01-02", "Aprobado")
    assert gen.pie_del_pdf({**DATOS, "Estado": "Revisado"}) != gen.pie_del_pdf(DATOS)


def test_las_fechas_del_pdf_se_fijan_sin_cambiar_la_longitud_y_exigen_las_dos():
    pdf = b"%PDF-1.4 /Producer (Skia) /CreationDate (D:20261118152100+00'00') /ModDate (D:20261118152106+00'00') fin"
    fijo = gen.fijar_fechas(pdf, "2026-11-18")
    assert len(fijo) == len(pdf) and fijo.count(b"D:20261118000000+00'00'") == 2
    otro = pdf.replace(b"152100", b"090000").replace(b"152106", b"090007")
    assert gen.fijar_fechas(otro, "2026-11-18") == fijo, "dos ejecuciones con segundos distintos dan los mismos bytes"
    assert gen.fijar_fechas(pdf, "2027-01-02") != fijo
    with pytest.raises(ValueError):
        gen.fijar_fechas(b"%PDF-1.4 /CreationDate (D:20261118152100+00'00') fin", "2026-11-18")


def _pdf_sintetico(titulos, enlaces, fecha="2026-11-18", paginas=3, esquema=True):
    f = f"(D:{fecha.replace('-', '')}000000+00'00')".encode()
    partes = [b"%PDF-1.4", b"/CreationDate " + f, b"/ModDate " + f, b"/Title (doc)"]
    partes += [b"/Title (t)"] * titulos + [b"/Subtype /Link"] * enlaces + [b"/Type /Page"] * paginas
    if esquema:
        partes.append(b"/Outlines 1 0 R")
    return b"\n".join(partes)


def test_las_reglas_con_las_que_se_juzga_un_pdf_detectan_cada_defecto():
    html = '<h1 id="a">A</h1><h2 id="b">B</h2><h3 id="c">C</h3><a href="#a">x</a><a href="#b">y</a>'
    assert gen.problemas_del_pdf(_pdf_sintetico(3, 2), html, "2026-11-18") == []
    assert gen.problemas_del_pdf(_pdf_sintetico(3, 2, esquema=False), html, "2026-11-18"), "sin marcadores"
    assert gen.problemas_del_pdf(_pdf_sintetico(2, 2), html, "2026-11-18"), "falta el marcador de un título"
    assert gen.problemas_del_pdf(_pdf_sintetico(4, 2), html, "2026-11-18"), "sobra un marcador"
    assert gen.problemas_del_pdf(_pdf_sintetico(3, 1), html, "2026-11-18"), "falta un enlace interno"
    assert gen.problemas_del_pdf(_pdf_sintetico(3, 2, fecha="2026-11-17"), html, "2026-11-18"), "fecha distinta a la de la versión"
    assert gen.problemas_del_pdf(_pdf_sintetico(3, 2, paginas=1), html, "2026-11-18"), "una sola página"
    assert gen.problemas_del_pdf(b"no es un pdf", html, "2026-11-18"), "no es un PDF"
    assert gen.problemas_del_pdf(_pdf_sintetico(3, 2).replace(b"%PDF-1.4", b"XXXX"), html, "2026-11-18") == ["no empieza como un PDF"], "lo único que falla es la cabecera"
    info = gen.inspeccionar_pdf(_pdf_sintetico(3, 2, paginas=5))
    assert info["paginas"] == 5 and info["titulos"] == 4 and info["enlaces"] == 2 and info["esquema"] is True and len(info["fechas"]) == 2


def test_el_pdf_se_escribe_por_omision_en_dist_que_git_ignora_y_el_zip_no_lleva_pdf_de_docs():
    ap_salida = gen.ROOT / "dist"
    assert "dist/" in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert gen.NOMBRE_PDF == "arquitectura_del_sistema_y_adr.pdf"
    espec = importlib.util.spec_from_file_location("make_dist", ROOT / "scripts" / "make_dist.py")
    make_dist = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(make_dist)
    assert make_dist.PDF_PERMITIDOS == ("docs/proyecto/referencias/", "docs/retroalimentacion/"), "un PDF en docs/arquitectura/ no viajaría en el zip"
    assert ap_salida.name == "dist" and 'default=ROOT / "dist"' in (CARPETA / "generar_pdf_arquitectura.py").read_text(encoding="utf-8"), "la carpeta de salida por omisión es dist/"


def test_el_script_solo_importa_lo_que_ya_esta_declarado_y_no_tiene_marcas_de_proceso():
    fuente = (CARPETA / "generar_pdf_arquitectura.py").read_text(encoding="utf-8")
    terceros = {m for m in re.findall(r"(?m)^\s*(?:from|import) (\w+)", fuente)} - set(sys.stdlib_module_names) - {"generar_guia_simulacion"}
    assert terceros == {"websockets"}, "websockets ya está en requirements.txt y no se agrega ningún paquete"
    assert re.search(r"(?m)^websockets==", (ROOT / "requirements.txt").read_text(encoding="utf-8"))
    r = subprocess.run([sys.executable, str(CARPETA / "generar_pdf_arquitectura.py"), "--help"], capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT)
    assert r.returncode == 0 and "--verificar" in r.stdout and "--solo-html" in r.stdout and "--nombre" in r.stdout
