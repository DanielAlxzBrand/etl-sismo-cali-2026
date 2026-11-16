"""Guardianes de la guía de simulación (`docs/usuarios/guia_simulacion/`) y de su generador de PDF (`scripts/usuarios/generar_guia_simulacion.py`).

Por qué existe: la guía se sigue comando por comando en el equipo de cada persona, así que un comando que ya no existe, una cifra que cambió o una inclusión rota la dejan inservible justo cuando alguien
que nunca ejecutó el proyecto la necesita. Aquí se comprueba, sin abrir ningún navegador: (1) el conversor de Markdown a HTML (tablas, listas, bloques de código, imágenes con recorte y enlaces);
(2) las inclusiones que traen a la guía lo que ya está escrito en otros documentos; (3) que el PDF del participante no traiga las tareas ni sus criterios y el del facilitador sí; (4) que cada archivo y cada
script que cita la guía exista; (5) que las cifras y los avisos de sesgo que repite coincidan con su fuente; y (6) que los archivos con el formato de la guía (unidos como lo hace quien junta) los lea el análisis.
Todos los datos de la prueba del punto 6 son SINTÉTICOS; no representan a ninguna persona. El paso que imprime con Edge no se prueba aquí: se probó a mano, página por página, al generar los PDF.
Qué NO demuestra: que la guía se entienda (eso lo dice quien la sigue por primera vez) ni que los PDF salgan bien impresos.
"""
import csv
import importlib.util
import re
import sys

import pytest

from src.common import ROOT

CARPETA = ROOT / "scripts" / "usuarios"
FUENTES = ROOT / "docs" / "usuarios" / "guia_simulacion"
USUARIOS = ROOT / "docs" / "usuarios"


def _cargar(nombre):
    espec = importlib.util.spec_from_file_location(nombre, CARPETA / f"{nombre}.py")
    modulo = importlib.util.module_from_spec(espec)
    sys.path.insert(0, str(CARPETA))
    try:
        espec.loader.exec_module(modulo)
    finally:
        sys.path.remove(str(CARPETA))
    return modulo


gen = _cargar("generar_guia_simulacion")
an = _cargar("analizar_sesiones")


def _fuente(nombre):
    return (FUENTES / nombre).read_text(encoding="utf-8")


def _todo_el_texto(perfil):
    return "\n".join(texto for _, texto in gen.partes(perfil))


# ---------------------------------------------------------------- conversor de Markdown
def test_el_ancla_conserva_las_tildes_y_quita_los_signos():
    assert gen.ancla("Paso 1 · Introducción hablada") == "paso-1-introducción-hablada"
    assert gen.ancla("4. Cierre y cuestionarios (5 minutos)") == "4-cierre-y-cuestionarios-5-minutos"
    assert gen.ancla("`main.py` y la API") == "mainpy-y-la-api"


def test_la_seccion_termina_en_el_proximo_titulo_del_mismo_nivel_y_no_lee_titulos_dentro_de_codigo():
    texto = "# A\nuno\n## B\ndos\n```\n## no es título\n```\n### C\ntres\n## D\ncuatro\n"
    assert gen.seccion(texto, "b") == "dos\n```\n## no es título\n```\n### C\ntres"
    with pytest.raises(gen.ErrorDeGuia):
        gen.seccion(texto, "no-existe")


def test_los_titulos_repetidos_reciben_anclas_distintas():
    html = gen.md_a_html("## Igual\n\n## Igual\n")
    assert 'id="igual"' in html and 'id="igual-2"' in html


def test_una_tabla_se_convierte_en_filas_y_celdas_y_una_barra_dentro_de_codigo_no_separa():
    html = gen.md_a_html("| a | b |\n|---|---|\n| `x\\|y` | **dos** |\n| 3 | 4 |\n")
    assert html.count("<tr>") == 3 and html.count("<th>") == 2 and html.count("<td>") == 4
    assert "<code>x\\|y</code>" in html or "<code>x|y</code>" in html
    assert "<td><strong>dos</strong></td>" in html


def test_las_listas_anidadas_y_las_casillas_se_convierten():
    html = gen.md_a_html("- uno\n  - dos\n- tres\n\n1. primero\n2. segundo\n\n- [ ] pendiente\n- [x] hecha\n")
    assert html.count("<ul>") == 3 and html.count("<ol>") == 1
    assert html.count('<li class="casilla">') == 2 and "&#9744;" in html and "&#9745;" in html
    assert html.index("<li>uno") < html.index("<li>dos") < html.index("<li>tres")


def test_un_bloque_de_codigo_se_escapa_y_las_filas_csv_se_pueden_cortar_despues_de_una_coma():
    html = gen.md_a_html("```powershell\nGet-Content <ruta> & más\n```\n\n```csv\na,b,c\n```\n")
    assert "Get-Content &lt;ruta&gt; &amp; más" in html
    assert '<code class="csv">a,<wbr>b,<wbr>c</code>' in html


def test_el_texto_con_signos_de_html_se_escapa_y_el_codigo_en_linea_no_se_interpreta():
    html = gen.md_a_html("Use `<b>` y a < b & c\n")
    assert "<code>&lt;b&gt;</code>" in html and "a &lt; b &amp; c" in html and "<b>" not in html.replace("<code>&lt;b&gt;</code>", "")


def test_una_cita_se_convierte_en_bloque_y_conserva_su_formato():
    html = gen.md_a_html("> **Ojo**: algo\n> - uno\n")
    assert html.startswith("<blockquote>") and "<strong>Ojo</strong>" in html and "<li>uno" in html


def test_las_directivas_de_pagina_cambian_el_salto_y_no_quedan_como_texto():
    html = gen.md_a_html("{{sin-salto}}\n# Parte corta\n\ntexto\n\n{{salto}}\n\n# Otra\n")
    assert 'id="parte-corta" class="continuo"' in html and 'class="salto"' in html and "{{" not in html and 'id="otra">' in html


def test_una_imagen_se_incrusta_y_con_recorte_solo_muestra_esa_parte():
    html = gen.md_a_html("![Menú](../../evidencias/ajustes_ux/EV-077_captura_respuesta_1400.png){recorte=0,60,300,200}\n\n![Completa](../../evidencias/ajustes_ux/EV-077_captura_respuesta_1400.png)\n")
    assert html.count("data:image/png;base64,") == 2
    assert 'class="recorte" style="width:300px;height:200px"' in html and "left:-0px;top:-60px" in html


def test_una_imagen_que_no_existe_o_sale_de_la_raiz_falla():
    with pytest.raises(gen.ErrorDeGuia):
        gen.md_a_html("![x](../no_existe.png)\n")
    with pytest.raises(gen.ErrorDeGuia):
        gen.md_a_html("![x](../../../../fuera.png)\n")


def test_un_enlace_a_un_archivo_del_repositorio_queda_como_texto_con_su_ruta_y_los_demas_se_respetan():
    html = gen.md_a_html("Vea [el protocolo](../protocolo_sesiones.md), [la web](https://example.org/a) y [más abajo](#paso-1).\n")
    assert "el protocolo (<code>docs/usuarios/protocolo_sesiones.md</code>)" in html
    assert '<a href="https://example.org/a">la web</a>' in html and '<a href="#paso-1">más abajo</a>' in html
    assert "<a href=\"../protocolo" not in html


def test_un_enlace_a_algo_que_no_existe_o_que_sale_de_la_raiz_falla():
    with pytest.raises(gen.ErrorDeGuia):
        gen.md_a_html("[x](../no_existe.md)\n")
    with pytest.raises(gen.ErrorDeGuia):
        gen.md_a_html("[x](../../../../fuera.md)\n")


# ---------------------------------------------------------------- inclusiones
def test_incluir_una_seccion_trae_su_cuerpo_sin_el_titulo_ni_la_seccion_siguiente():
    cuerpo = gen.resolver_inclusiones("{{incluir: docs/instalacion/modo_minimo.md#2-comprobar-el-equipo}}")
    origen = (ROOT / "docs" / "instalacion" / "modo_minimo.md").read_text(encoding="utf-8")
    primera = next(l for l in cuerpo.splitlines() if l.strip())
    assert primera in origen.replace("\r\n", "\n") and not primera.startswith("#")
    assert "Crear el entorno e instalar" not in cuerpo


def test_las_opciones_filas_solo_tablas_y_nivel_filtran_y_desplazan():
    fuente = "docs/instalacion/README.md#2-requisitos"
    entera = gen.resolver_inclusiones("{{incluir: " + fuente + "}}")
    filtrada = gen.resolver_inclusiones("{{incluir: " + fuente + " | filas: Windows 11; Python 3.13}}")
    assert sum(l.startswith("|") for l in filtrada.splitlines()) < sum(l.startswith("|") for l in entera.splitlines())
    assert filtrada.count("Windows 11") >= 1 and "Python 3.13" in filtrada
    solo = gen.resolver_inclusiones("{{incluir: docs/usuarios/instrumentos.md#1-sus-escala-de-usabilidad-del-sistema | solo: tablas}}")
    assert solo.strip() and all(l.startswith("|") for l in solo.splitlines())
    abajo = gen.resolver_inclusiones("{{incluir: docs/usuarios/guion_sesion.md#3-tareas | nivel: 2}}")
    assert not re.search(r"^#{1,2} ", abajo, re.M)


def test_incluir_codigo_trae_solo_las_lineas_pedidas_dentro_de_un_bloque():
    plantilla = (USUARIOS / "sesiones_reales" / "plantilla_registro.csv").read_text(encoding="utf-8").splitlines()[0]
    assert gen.resolver_inclusiones("{{codigo: docs/usuarios/sesiones_reales/plantilla_registro.csv | csv | lineas: 1-1}}") == f"```csv\n{plantilla}\n```"


@pytest.mark.parametrize("directiva", [
    "{{incluir: docs/no_existe.md}}",
    "{{incluir: docs/instalacion/modo_minimo.md#no-existe}}",
    "{{incluir: docs/instalacion/README.md#2-requisitos | filas: texto que ninguna fila contiene}}",
    "{{codigo: docs/no_existe.csv | csv}}",
])
def test_una_inclusion_que_no_se_puede_resolver_falla_en_vez_de_dejar_un_hueco(directiva):
    with pytest.raises(gen.ErrorDeGuia):
        gen.resolver_inclusiones(directiva)


# ---------------------------------------------------------------- perfiles y documento
def _perfil_de(nombre):
    primera = _fuente(nombre).splitlines()[0]
    return primera.removeprefix("{{para: ").removesuffix("}}")


def test_cada_perfil_trae_solo_las_partes_que_le_corresponden():
    todas = sorted(p.name for p in FUENTES.glob("0*.md"))
    assert len(todas) == 9
    assert [n for n, _ in gen.partes("completa")] == todas
    assert [n for n, _ in gen.partes("participante")] == [n for n in todas if _perfil_de(n) == "todos"]
    assert {_perfil_de(n) for n in todas} == {"todos", "facilitador"}


def test_el_pdf_del_participante_no_trae_las_tareas_ni_sus_criterios_y_el_del_facilitador_si():
    guion = (USUARIOS / "guion_sesion.md").read_text(encoding="utf-8")
    filas = [l for l in guion.split("## 3. Tareas")[1].split("## 4.")[0].splitlines() if re.match(r"^\| T[1-6] \|", l)]
    assert len(filas) == len(an.TAREAS)
    participante, completa = _todo_el_texto("participante"), _todo_el_texto("completa")
    for fila in filas:
        enunciado = fila.split("|")[2].strip().strip("«»")
        criterio = fila.split("|")[4].strip()
        assert enunciado[:60] in completa and criterio[:60] in completa
        assert enunciado[:60] not in participante and criterio[:60] not in participante
    assert "Criterio de éxito" not in participante and "Criterio de éxito" in completa
    assert not re.search(r"\{\{(incluir|codigo|para)", participante + completa)      # ninguna inclusión quedó sin resolver


def test_el_documento_trae_portada_indice_con_enlaces_a_cada_parte_y_es_siempre_el_mismo():
    for perfil in ("completa", "participante"):
        html = gen.construir_html(perfil)
        assert html == gen.construir_html(perfil)
        assert "<title>" + gen.TITULO + "</title>" in html and gen.version() in html
        titulos = re.findall(r'<h1 id="([^"]+)"[^>]*>(?!Índice)', html)
        enlaces = re.search(r'<nav class="indice">(.*?)</nav>', html, re.S).group(1)
        for ancla in titulos:
            if ancla != "titulo-de-la-guia":
                assert f'href="#{ancla}"' in enlaces, f"el índice no enlaza a {ancla}"
        assert not re.search(r'src="(?!data:)', html)       # ninguna imagen se pide fuera del documento


def test_el_pie_del_pdf_numera_las_paginas_y_pide_papel_a4():
    p = gen.parametros_pdf("Pie <de prueba>")
    assert p["displayHeaderFooter"] and p["preferCSSPageSize"] and p["printBackground"]
    assert "Pie &lt;de prueba&gt;" in p["footerTemplate"] and 'class="pageNumber"' in p["footerTemplate"] and 'class="totalPages"' in p["footerTemplate"]
    assert "size: A4" in gen.ESTILO


def test_generar_solo_el_html_escribe_los_archivos_pedidos_sin_abrir_ningun_navegador(tmp_path):
    assert gen.main(["--solo-html", "--perfil", "participante", "--salida", str(tmp_path / "salida")]) == 0
    assert [p.name for p in (tmp_path / "salida").iterdir()] == ["guia_simulacion_participante.html"]
    assert (tmp_path / "salida" / "guia_simulacion_participante.html").read_text(encoding="utf-8") == gen.construir_html("participante")


# ---------------------------------------------------------------- lo que cita la guía existe
CREADOS_POR_EL_PROCEDIMIENTO = {
    "docs/usuarios/sesiones_reales/registro.csv", "docs/usuarios/sesiones_reales/cuestionarios.csv",   # los crea quien junta (parte E)
}
RUTA = re.compile(r"^(?:docs|scripts|src|tests|config|data|orquestacion|servicios)[/\\][\w./\\-]+$")


def _citas_de_rutas():
    citas = []
    for fuente in sorted(FUENTES.glob("*.md")):
        for m in re.finditer(r"`([^`\n]+)`", fuente.read_text(encoding="utf-8")):
            dentro = m.group(1).strip()
            if RUTA.match(dentro):
                citas.append((fuente.name, dentro.replace("\\", "/")))
    return citas


def test_la_guia_cita_rutas_y_todas_existen():
    citas = _citas_de_rutas()
    assert len(citas) >= 10, "no se encontraron las rutas que la guía debería citar"
    inexistentes = [(f, r) for f, r in citas if r not in CREADOS_POR_EL_PROCEDIMIENTO and not (ROOT / r.rstrip("/")).exists()]
    assert inexistentes == []


def test_cada_script_que_la_guia_manda_ejecutar_existe():
    scripts = set()
    for bloque in re.findall(r"```powershell\n(.*?)```", _todo_el_texto("completa"), re.S):      # con las inclusiones ya resueltas: algunos comandos vienen de la guía de instalación
        scripts |= {s.replace("\\", "/") for s in re.findall(r"scripts[/\\][\w/\\]+\.py", bloque)}
    assert {"scripts/preparar_entorno.py", "scripts/panel/ejecutar_panel.py", "scripts/usuarios/analizar_sesiones.py"} <= scripts
    assert [s for s in sorted(scripts) if not (ROOT / s).is_file()] == []


def test_cada_enlace_de_las_fuentes_de_la_guia_se_resuelve_dentro_del_repositorio():
    for fuente in sorted(FUENTES.glob("*.md")):
        for destino in re.findall(r"\]\(([^)\s]+)\)", fuente.read_text(encoding="utf-8")):
            if destino.startswith(("http", "#")):
                continue
            assert (fuente.parent / destino.partition("#")[0]).resolve().is_relative_to(ROOT), f"{fuente.name}: {destino}"
            assert (fuente.parent / destino.partition("#")[0]).exists(), f"{fuente.name}: {destino}"


# ---------------------------------------------------------------- cifras y avisos que repite la guía
def test_las_nueve_huellas_de_la_comprobacion_son_las_del_archivo_de_referencia():
    lineas = [l for l in (ROOT / "docs" / "validacion" / "sha256_despues_logging.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lineas) == 9 and all(re.match(r"^[0-9a-f]{64} \*\S+$", l) for l in lineas)
    parte_a = _fuente("02_parte_a_antes_de_empezar.md")
    assert "nueve líneas que dicen «igual»" in parte_a and "docs\\validacion\\sha256_despues_logging.txt" in parte_a
    assert "-split ' \\*'" in parte_a and ".Hash.ToLower()" in parte_a      # el archivo trae las huellas en minúsculas y Get-FileHash las escribe en mayúsculas
    assert "sin distinguir mayúsculas de minúsculas" in parte_a


def test_las_pruebas_omitidas_que_dice_la_guia_son_las_de_la_guia_de_instalacion():
    instalacion = (ROOT / "docs" / "instalacion" / "README.md").read_text(encoding="utf-8")
    parte_a = _fuente("02_parte_a_antes_de_empezar.md")
    assert "se omiten 10" in instalacion and "sin Git se omiten 10" in parte_a
    assert re.search(r"\|\s*zip descomprimido, con Git instalado\s*\|\s*\*\*1\*\*", instalacion) and "una se omite" in parte_a


def test_el_conteo_de_lineas_que_espera_quien_junta_sale_del_numero_de_tareas_y_de_sesiones():
    parte_e = _fuente("06_parte_e_devolver_los_resultados.md")
    sesiones, tareas = 3, len(an.TAREAS)
    assert f"**{1 + sesiones * tareas}** (el encabezado y {sesiones * tareas} filas)" in parte_e
    assert f"**{1 + sesiones}** (el encabezado y {sesiones} filas)" in parte_e


def test_el_plan_b_para_cerrar_el_panel_busca_solo_el_proceso_que_escucha():
    parte_b = _fuente("03_parte_b_primera_vez_con_el_panel.md")
    assert "Get-NetTCPConnection -LocalPort 8501 -State Listen | Select-Object OwningProcess" in parte_b      # sin `-State Listen` la lista trae también conexiones cerradas y varios números
    assert "Stop-Process -Id" in parte_b and "Ctrl+C" in parte_b


def test_la_guia_declara_el_sesgo_de_quien_conoce_las_tareas_y_de_quien_abre_la_carpeta_de_usuarios():
    como_usar, no_demuestra, parte_d = _fuente("01_como_usar.md"), _fuente("09_que_no_demuestra.md"), _fuente("05_parte_d_que_anotar.md")
    assert "no abre la carpeta `docs/usuarios/` antes de su sesión" in como_usar
    assert "El zip trae `docs/usuarios/` con las tareas y sus criterios" in no_demuestra and "no hay manera de comprobarlo" in no_demuestra
    assert "Por defecto, una sola persona facilita las dos primeras sesiones y participa en la tercera" in como_usar and "**Alternativa**" in como_usar
    assert "Exposición previa a las tareas" in parte_d and "exposición previa" in no_demuestra
    assert "S01" in no_demuestra and "no son personas" in no_demuestra
    assert not re.search(r"\bP0[4-9]\b", "\n".join(f.read_text(encoding="utf-8") for f in FUENTES.glob("*.md"))), "la guía solo usa los códigos P01 a P03"


def test_la_guia_y_su_generador_viajan_en_el_zip_y_los_pdf_no():
    spec = importlib.util.spec_from_file_location("make_dist", ROOT / "scripts" / "make_dist.py")
    md = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(md)
    viajan = {p.relative_to(ROOT).as_posix() for p in md.listar(ROOT)}
    assert {f"docs/usuarios/guia_simulacion/{p.name}" for p in FUENTES.glob("*.md")} <= viajan
    assert "scripts/usuarios/generar_guia_simulacion.py" in viajan
    assert not [r for r in viajan if r.endswith(".pdf") and r.startswith("dist/")]


# ---------------------------------------------------------------- archivos con el formato de la guía
def _plantilla(nombre):
    return (USUARIOS / "sesiones_reales" / nombre).read_text(encoding="utf-8").splitlines()[0].split(",")


def _sesion_sintetica(carpeta, codigo, resultados):
    """Archivos de UNA sesión sintética con la cabecera exacta de las plantillas que da la guía; devuelve los dos archivos y las filas escritas."""
    carpeta.mkdir(parents=True, exist_ok=True)
    cab_registro, cab_cuestionarios = _plantilla("plantilla_registro.csv"), _plantilla("plantilla_cuestionarios.csv")
    with open(carpeta / f"registro_{codigo}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\r\n")
        w.writerow(cab_registro)
        for t, r in zip(an.TAREAS, resultados):
            w.writerow([codigo, "otro", "2000-01-01", t, r, 100 + 10 * int(t[1]), 1 if r == "exito_con_ayuda" else 0, 0, "comentario de prueba, con coma" if t == "T3" else "", "real"])
    with open(carpeta / f"cuestionarios_{codigo}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\r\n")
        w.writerow(cab_cuestionarios)
        w.writerow([codigo, "otro", "2000-01-01"] + [4, 2, 4, 2, 4, 2, 4, 2, 4, 2] + [4, "real"])


def _juntar(recibidos, destino):
    """Lo mismo que hace el bloque de la parte E: copia la plantilla y agrega las filas de cada envío sin repetir su encabezado (con los saltos de línea de Windows)."""
    destino.mkdir(parents=True, exist_ok=True)
    for prefijo, nombre in (("registro_P", "registro.csv"), ("cuestionarios_P", "cuestionarios.csv")):
        base = USUARIOS / "sesiones_reales" / f"plantilla_{nombre}"
        salida = destino / nombre
        salida.write_bytes(base.read_bytes())
        if not salida.read_bytes().endswith(b"\n"):
            salida.write_bytes(salida.read_bytes() + b"\r\n")
        for archivo in sorted(recibidos.glob(f"{prefijo}*.csv")):
            filas = archivo.read_text(encoding="utf-8").splitlines()[1:]
            with open(salida, "a", encoding="utf-8", newline="") as f:
                f.write("".join(l + "\r\n" for l in filas))


CASOS = {"P01": ("exito", "exito", "exito_con_ayuda", "exito", "exito", "exito"), "P02": ("exito", "fracaso", "exito", "exito_con_ayuda", "exito", "exito"), "P03": ("exito",) * 6}


def _tres_sesiones(tmp_path):
    recibidos = tmp_path / "recibidos con espacios"
    for codigo, resultados in CASOS.items():
        _sesion_sintetica(recibidos, codigo, resultados)
    _juntar(recibidos, tmp_path / "docs_usuarios" / "sesiones_reales")
    return tmp_path / "docs_usuarios"


def test_tres_sesiones_en_el_formato_de_la_guia_se_unen_con_el_conteo_esperado_y_se_analizan(tmp_path, capsys):
    base = _tres_sesiones(tmp_path)
    reales = base / "sesiones_reales"
    assert len((reales / "registro.csv").read_text(encoding="utf-8").splitlines()) == 19
    assert len((reales / "cuestionarios.csv").read_text(encoding="utf-8").splitlines()) == 4
    assert an.main(["--base", str(base)]) == 0
    assert "3 personas" in capsys.readouterr().out
    texto = (base / "resultados.md").read_text(encoding="utf-8")
    assert " de 3 |" in texto and "no se informa (n < 5)" in texto
    assert re.search(r"\d+,\d %", texto) is None            # con tres personas no hay porcentajes


def test_una_fila_con_un_resultado_que_no_existe_se_rechaza_con_su_numero_de_fila(tmp_path, capsys):
    base = _tres_sesiones(tmp_path)
    ruta = base / "sesiones_reales" / "registro.csv"
    ruta.write_text(ruta.read_text(encoding="utf-8").replace(",exito_con_ayuda,", ",bien,", 1), encoding="utf-8", newline="")
    assert an.main(["--base", str(base)]) == 2
    mensaje = capsys.readouterr().err
    assert "registro.csv, fila 4" in mensaje and "'bien'" in mensaje
    assert not (base / "resultados.md").exists()


def test_un_envio_sin_el_encabezado_de_la_plantilla_se_rechaza(tmp_path):
    base = _tres_sesiones(tmp_path)
    ruta = base / "sesiones_reales" / "cuestionarios.csv"
    lineas = ruta.read_text(encoding="utf-8").splitlines()
    lineas[0] = lineas[0].replace("csat", "satisfaccion")
    ruta.write_text("\r\n".join(lineas) + "\r\n", encoding="utf-8", newline="")
    assert an.main(["--base", str(base)]) == 2


def test_un_envio_marcado_como_sintetico_no_entra_a_las_sesiones_reales(tmp_path):
    base = _tres_sesiones(tmp_path)
    ruta = base / "sesiones_reales" / "registro.csv"
    ruta.write_bytes(ruta.read_bytes().replace(b",real\r\n", b",sintetico\r\n", 1))
    assert an.main(["--base", str(base)]) == 2
