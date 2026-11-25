"""Capa de interfaz propia del panel (D115): confinamiento del HTML, el CSS y el JavaScript, seguridad (texto escapado y JavaScript sin APIs peligrosas), y equivalencia de «Estratos (K1)»
con lo que entrega la API y con lo que mostraba el panel original.

Qué demuestran: que el código de presentación vive solo en `src/panel/frontend/`, que ninguna cifra, fecha ni regla de ejemplo pasó a la interfaz, que cada número de la página sale de la API con las
funciones de formato y redacción de siempre, y que los textos que vienen de los datos se escapan. Qué NO demuestran: cómo se ve en un navegador ni que el JavaScript funcione; eso lo comprueban las capturas
y el recorrido interactivo registrados como evidencia.
Los datos de las pruebas de seguridad son SINTÉTICOS (inventados), no datos del proyecto.
"""
import hashlib
import json
import re
import shutil
import socket
from html import escape, unescape

import pytest

from src.common import ROOT
from src.panel import componentes, formato, glosario, redaccion, registro, tema
from src.panel.frontend import activos, estilos, navegacion
from src.panel.frontend import estratos as vista
from src.panel.frontend import vista as vista_base
from src.panel.paginas import estratos as pagina
from tests import panel_apoyo as pa
from tests.test_panel_registro_y_aislamiento import ARCHIVOS, PANEL, PERMITIDO_CON_DIGITOS, PERMITIDO_FRONTEND, cifras_sobrantes

FRONTEND = PANEL / "frontend"
EXTENSIONES_DE_INTERFAZ = {".js", ".css", ".html", ".svg", ".webp", ".png", ".jpg", ".jpeg", ".gif"}
# Huella de cada JavaScript auditado: cambiar el archivo obliga a revisarlo y a actualizar esta cifra (y D115).
JS_FIJADOS = {"lectura.js": "51bf9b39cb5f6e630710376afdf6b5eae351743a84e7232c61d35b688f770404"}
ESPACIO_DE_NOMBRES_SVG = "http://www.w3.org/2000/svg"
PROHIBIDO_EN_JS = {
    "asignar HTML": r"\.(?:inner|outer)HTML\b|insertAdjacentHTML|document\.write|\bsrcdoc\b",
    "evaluar texto como código": r"\beval\s*\(|\bnew\s+Function\b|\bFunction\s*\(|setTimeout\(\s*[\"'`]|setInterval\(\s*[\"'`]",
    "salir a la red": r"\bfetch\s*\(|XMLHttpRequest|WebSocket|EventSource|sendBeacon|importScripts|\bimport\s*\(",
    "almacenamiento persistente o cookies": r"localStorage|indexedDB|document\.cookie",
    "mensajes entre ventanas": r"postMessage",
    "direcciones externas": r"https?://",
}
PROHIBIDO_EN_PLANTILLAS = {
    "scripts o marcos": r"(?i)<script|<iframe|<object|<embed|<link\b|<base\b|<form\b|<foreignObject",
    "manejadores de eventos": r"(?i)\son[a-z]+\s*=",
    "enlaces con código": r"(?i)javascript:",
}
PROHIBIDO_EN_CSS = {"importar hojas": r"@import", "código en estilos": r"(?i)javascript:|expression\s*\(|behavior\s*:", "recursos remotos": r"url\(\s*(?![\"']?\s*(?:data:|var\())"}
DATOS_DE_EJEMPLO = (r"ficticio", r"2099", r"Datos de ejemplo", r"Sin dato\b", r"prototipo", r"menor de 12", r"31/12", r"serie de ejemplo", r"Lectura del ejemplo")


def _archivos(sufijos):
    return sorted(p for p in FRONTEND.rglob("*") if p.is_file() and p.suffix in sufijos and "__pycache__" not in p.parts)


def _sin_comentarios_js(texto):
    return re.sub(r"/\*.*?\*/|(?<=\s)//[^\n]*|^//[^\n]*", "", texto, flags=re.S | re.M)


def hallazgos(texto, reglas):
    """Nombres de las reglas que el texto incumple."""
    return [nombre for nombre, patron in reglas.items() if re.search(patron, texto)]


def hallazgos_css(texto):
    quitado = texto.replace(ESPACIO_DE_NOMBRES_SVG, "")
    return hallazgos(quitado, PROHIBIDO_EN_CSS) + (["direcciones externas"] if re.search(r"https?://", quitado) else [])


def hallazgos_plantilla(texto):
    quitado = texto.replace(ESPACIO_DE_NOMBRES_SVG, "")
    return hallazgos(quitado, PROHIBIDO_EN_PLANTILLAS) + (["direcciones externas"] if re.search(r"https?://", quitado) else [])


@pytest.fixture(scope="module")
def entorno():
    carpeta, ruta = pa.copia_temporal_de_la_base()
    http, cliente = pa.api_en_memoria(ruta)
    yield pa.como_consulta(cliente)
    cliente.cerrar()
    http.close()
    shutil.rmtree(carpeta, ignore_errors=True)


@pytest.fixture(scope="module")
def k1(entorno):
    return entorno("/kpis/K1").datos


@pytest.fixture(scope="module")
def metadata(entorno):
    return entorno("/metadata").datos


@pytest.fixture(scope="module")
def at(entorno):
    return pa.pagina("estratos", entorno)


# ---------------------------------------------------------------- confinamiento
def test_los_recursos_de_interfaz_viven_solo_en_la_carpeta_frontend():
    fuera = [p.relative_to(ROOT).as_posix() for p in PANEL.rglob("*") if p.is_file() and p.suffix in EXTENSIONES_DE_INTERFAZ and FRONTEND not in p.parents]
    assert fuera == []
    assert _archivos({".js"}) and _archivos({".css"}) and _archivos({".svg"})


def test_html_y_componentes_solo_se_llaman_desde_la_carpeta_frontend():
    for ruta in ARCHIVOS:
        if FRONTEND in ruta.parents:
            continue
        texto = ruta.read_text(encoding="utf-8")
        assert "st.html(" not in texto and "components.v2" not in texto and ".component(" not in texto, ruta.relative_to(PANEL).as_posix()


def test_negativa_un_modulo_fuera_de_frontend_que_dibuja_html_se_detecta():
    texto = "import streamlit as st\nst.html('<b>x</b>')\nst.components.v2.component('x')\n"
    assert "st.html(" in texto and "components.v2" in texto


def test_solo_activos_lee_archivos_de_la_interfaz_y_nunca_fuera_de_su_carpeta():
    for ruta in sorted(FRONTEND.glob("*.py")):
        if ruta.name == "activos.py":
            continue
        assert re.search(r"\bopen\(|read_text|read_bytes|read_csv|\.db\b", ruta.read_text(encoding="utf-8")) is None, ruta.name
    for salida in (("..", "config", "config.yaml"), ("..", "..", "..", ".env"), (str(ROOT / "config" / "config.yaml"),)):
        with pytest.raises(ValueError):
            activos.ruta(*salida)
    assert activos.ruta("estilos", "marco.css").is_file()


# ---------------------------------------------------------------- JavaScript
def test_hay_solo_los_javascript_auditados_y_su_huella_no_cambio():
    encontrados = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in _archivos({".js"})}
    assert encontrados == JS_FIJADOS, "un JavaScript nuevo o editado exige revisarlo, actualizar JS_FIJADOS y registrarlo en D115"


def test_el_javascript_no_usa_apis_peligrosas():
    for ruta in _archivos({".js"}):
        assert hallazgos(_sin_comentarios_js(ruta.read_text(encoding="utf-8")), PROHIBIDO_EN_JS) == [], ruta.name


@pytest.mark.parametrize("ejemplo,regla", [
    ("caja.innerHTML = datos.html;", "asignar HTML"), ("x.insertAdjacentHTML('beforeend', t)", "asignar HTML"), ("document.write(t)", "asignar HTML"),
    ("eval(texto)", "evaluar texto como código"), ("new Function('return 1')", "evaluar texto como código"), ("setTimeout('f()', 5)", "evaluar texto como código"),
    ("fetch('/x')", "salir a la red"), ("new WebSocket(u)", "salir a la red"), ("await import('x')", "salir a la red"),
    ("localStorage.setItem('a','b')", "almacenamiento persistente o cookies"), ("window.postMessage(1, '*')", "mensajes entre ventanas"),
    ("const u = 'https://externo.org/x.js'", "direcciones externas"),
])
def test_negativa_el_detector_de_javascript_reconoce_lo_prohibido(ejemplo, regla):
    assert regla in hallazgos(ejemplo, PROHIBIDO_EN_JS)


def test_el_javascript_escribe_los_textos_con_textcontent_y_usa_solo_almacenamiento_de_sesion():
    js = _sin_comentarios_js((FRONTEND / "lectura.js").read_text(encoding="utf-8"))
    assert js.count("textContent") >= 5 and "sessionStorage" in js
    assert ".st-key-lienzo" in js and 'key="lienzo"' in (FRONTEND / "marco.py").read_text(encoding="utf-8")


PAGINAS_INTEGRADAS = ("respuesta", "estratos", "comunas", "sensibilidades")


def _textos_de_apoyo(pagina_id):
    contenido = activos.contenido(pagina_id)
    textos = [contenido[k] for k in ("interpretacion", "precauciones", "como_leer", "como_leer_columnas", "ayuda_intervalo") if k in contenido]
    textos += [f["titulo"] + f["explicacion"] for f in contenido["fichas"]] + [(p["titulo"] or "") + (p["texto"] or "") + p["region"] for p in contenido["pasos"]]
    return textos


@pytest.mark.parametrize("pagina_id", PAGINAS_INTEGRADAS)
def test_los_textos_que_recibe_el_javascript_no_llevan_etiquetas(pagina_id):
    assert all("<" not in t and ">" not in t for t in _textos_de_apoyo(pagina_id))


@pytest.mark.parametrize("pagina_id", PAGINAS_INTEGRADAS)
def test_cada_pagina_integrada_trae_seis_pasos_tres_curiosidades_y_terminos_de_su_glosario(pagina_id):
    contenido = activos.contenido(pagina_id)
    assert len(contenido["pasos"]) == 6 and len(contenido["fichas"]) == 3
    assert all(f["termino"] in glosario.TERMINOS_POR_PAGINA[pagina_id] for f in contenido["fichas"])
    assert [f["fundamento"] for f in vista_base.curiosidades(pagina_id)] == ["Glosario del panel · " + glosario.TERMINOS[f["termino"]][0] for f in contenido["fichas"]]
    sin_texto = [p for p in contenido["pasos"] if p["texto"] is None]
    assert len(sin_texto) <= 1 and (pagina_id in ("respuesta", "estratos") or not sin_texto)


# ---------------------------------------------------------------- CSS, plantillas y textos de apoyo
def test_los_estilos_no_cargan_nada_de_fuera():
    for ruta in _archivos({".css"}):
        assert hallazgos_css(ruta.read_text(encoding="utf-8")) == [], ruta.name


@pytest.mark.parametrize("ejemplo,regla", [
    ("@import url(https://x.org/a.css);", "importar hojas"), ("a{background:url(https://x.org/a.png)}", "recursos remotos"), ("a{background:url(imagen.png)}", "recursos remotos"),
    ("a{width:expression(alert(1))}", "código en estilos"), ("a{background:url(javascript:alert(1))}", "código en estilos"),
])
def test_negativa_el_detector_de_estilos_reconoce_lo_prohibido(ejemplo, regla):
    assert regla in hallazgos_css(ejemplo)


def test_las_plantillas_y_las_texturas_no_llevan_scripts_ni_direcciones_externas():
    for ruta in _archivos({".html", ".svg"}):
        assert hallazgos_plantilla(ruta.read_text(encoding="utf-8")) == [], ruta.name


@pytest.mark.parametrize("ejemplo,regla", [
    ("<script>alert(1)</script>", "scripts o marcos"), ("<iframe src=x></iframe>", "scripts o marcos"), ("<svg onload=alert(1)>", "manejadores de eventos"),
    ("<a href=\"javascript:alert(1)\">x</a>", "enlaces con código"), ("<img src=\"http://externo.org/p.png\">", "direcciones externas"),
])
def test_negativa_el_detector_de_plantillas_reconoce_lo_prohibido(ejemplo, regla):
    assert regla in hallazgos_plantilla(ejemplo)


def test_la_lamina_exportable_declara_una_politica_de_contenido_que_no_permite_scripts_ni_red():
    texto = (FRONTEND / "plantillas" / "lamina.html").read_text(encoding="utf-8")
    politica = re.search(r'http-equiv="Content-Security-Policy" content="([^"]+)"', texto).group(1)
    assert "default-src 'none'" in politica and "script-src" not in politica and "style-src 'unsafe-inline'" in politica


@pytest.mark.parametrize("pagina_id", PAGINAS_INTEGRADAS)
def test_los_textos_de_apoyo_no_llevan_cifras_propias(pagina_id):
    contenido = activos.contenido(pagina_id)
    cadenas = [v for v in contenido.values() if isinstance(v, str)] + [x for f in contenido["fichas"] for x in f.values()] + [x for p in contenido["pasos"] for x in p.values() if x]
    for cadena in cadenas:
        assert not cifras_sobrantes(cadena, PERMITIDO_CON_DIGITOS), cadena
    assert cifras_sobrantes("De 12 construcciones con clasificación", PERMITIDO_CON_DIGITOS)       # negativa: una cifra escrita a mano se detecta


def test_negativa_los_modulos_de_la_interfaz_no_pueden_escribir_otras_cifras():
    assert not cifras_sobrantes("<h1>Titulo</h1> 95 % base64 K1", PERMITIDO_FRONTEND)
    assert cifras_sobrantes("hay 253 construcciones", PERMITIDO_FRONTEND) and cifras_sobrantes("<td>12,5</td>", PERMITIDO_FRONTEND)
    assert cifras_sobrantes("<h1>Titulo</h1> corte 2099", PERMITIDO_FRONTEND)


def test_ni_datos_ni_fechas_ni_reglas_de_ejemplo_pasaron_a_la_interfaz():
    for ruta in sorted(FRONTEND.rglob("*")):
        if not ruta.is_file() or ruta.suffix in (".webp", ".pyc"):
            continue
        texto = ruta.read_text(encoding="utf-8")
        for patron in DATOS_DE_EJEMPLO:
            assert re.search(patron, texto, re.I) is None, (ruta.name, patron)
    assert re.search(r"Datos de ejemplo", "Datos de ejemplo · Corte ficticio 31/12/2099")    # negativa: el detector ve el texto del prototipo


# ---------------------------------------------------------------- paleta
def test_las_categorias_de_los_graficos_usan_okabe_ito_y_la_interfaz_usa_el_verde():
    c, hoja = tema.colores(), estilos.hoja_global()
    assert f"--cat-suficiente:{c['principal']}" in hoja and f"--cat-baja:{c['secundario']}" in hoja
    assert (c["principal"], c["secundario"]) == ("#0072B2", "#D55E00")
    css = (FRONTEND / "estilos" / "integracion.css").read_text(encoding="utf-8")
    assert "background:var(--cat-suficiente)" in css and "border:2px dashed var(--cat-baja)" in css
    assert tema.interfaz()["principal"] == "#087A6B"


def test_la_paleta_de_la_interfaz_alcanza_los_contrastes_minimos():
    i = tema.interfaz()
    assert tema.contraste(i["texto"], i["fondo"]) >= 7 and tema.contraste(i["texto"], i["fondo_secundario"]) >= 7
    assert tema.contraste(i["principal"], i["fondo_secundario"]) >= 4.5 and tema.contraste(i["principal"], i["fondo"]) >= 4.5
    assert tema.contraste(i["lateral_texto"], i["lateral_fondo"]) >= 7 and tema.contraste(i["lateral_principal"], i["lateral_fondo"]) >= 4.5


# ---------------------------------------------------------------- navegación
def test_la_barra_lateral_lista_las_ocho_paginas_en_el_orden_del_registro():
    ordenadas = [i for _, ids in navegacion.GRUPOS for i in ids]
    assert ordenadas == [p.id for p in registro.PAGINAS] and set(navegacion.ICONOS) == set(ordenadas)
    assert all(navegacion.grupo_de(i) for i in ordenadas)


def test_la_aplicacion_completa_muestra_los_ocho_enlaces_de_la_barra_lateral(monkeypatch):
    from streamlit.testing.v1 import AppTest

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        libre = s.getsockname()[1]
    monkeypatch.setenv("PANEL_API_URL", f"http://127.0.0.1:{libre}")
    import streamlit as st
    st.cache_resource.clear()
    st.cache_data.clear()
    app = AppTest.from_file(str(pa.RAIZ / "src" / "panel" / "app.py"), default_timeout=60).run()
    assert len(app.exception) == 0
    enlaces = [e.proto.label for e in app.get("page_link")]
    assert enlaces == [p.titulo for p in registro.PAGINAS] or sorted(enlaces) == sorted(p.titulo for p in registro.PAGINAS)
    st.cache_resource.clear()
    st.cache_data.clear()


# ---------------------------------------------------------------- equivalencia de Estratos con la API y con el panel original
def test_la_pagina_se_dibuja_sin_excepciones_y_con_su_barra_de_herramientas(at):
    assert len(at.exception) == 0
    assert pa.titulo(at) == registro.pagina("estratos").titulo
    botones = at.get("download_button")
    assert len(botones) == 1 and botones[0].proto.label == "Exportar figura"


def test_la_tabla_de_la_interfaz_es_la_tabla_del_panel_original(at, k1):
    original = pagina.tabla_k1(k1)
    tabla = pa.tablas_html(at)[0]
    assert tabla[0] == list(original.columns)
    assert tabla[1:] == [[str(v) for v in fila] for fila in original.to_numpy().tolist()]


def _filas_de_la_figura(at):
    html = next(h.value for h in at.html if 'class="analisis"' in h.value)
    return [(m.group(1), m.group(2), unescape(re.sub(r"<[^>]+>", " ", re.sub(r'<span class="ayuda".*?</span>', "", m.group(3)))), m.group(3))
            for m in re.finditer(r'<label class="dato r(\d+)( baja)?">(.*?)</label>', html, re.S)]


def test_la_figura_muestra_la_tasa_el_intervalo_y_los_conteos_de_cada_estrato(at, k1):
    filas = _filas_de_la_figura(at)
    assert len(filas) == len(k1) == 6
    for (_, _, texto, _), f in zip(filas, k1):
        texto = re.sub(r"\s+", " ", texto)
        assert formato.porcentaje(f["valor"]) in texto and formato.intervalo(f["ic95_inf"], f["ic95_sup"]) in texto
        assert f"{formato.numero(f['numerador'])} de {formato.numero(f['denominador'])}" in texto
        assert pagina._etiqueta(f["grupo"]) in texto


def test_la_marca_de_muestra_baja_la_entrega_la_api_y_se_lee_en_texto(at, k1):
    filas = _filas_de_la_figura(at)
    for (_, clase, texto, _), f in zip(filas, k1):
        assert bool(clase) == bool(f["muestra_baja"])
        assert ("Muestra baja" in texto) == bool(f["muestra_baja"])
    assert any(f["muestra_baja"] for f in k1) and any(not f["muestra_baja"] for f in k1)


def test_las_barras_se_ubican_con_la_escala_calculada_a_partir_de_los_datos(at, k1):
    tope, marcas = vista.escala(k1)
    assert tope >= max(f["ic95_sup"] * 100 for f in k1) and marcas[0] == 0 and marcas[-1] == tope and len(marcas) <= 7
    for (indice, _, _, crudo), f in zip(_filas_de_la_figura(at), k1):
        tasa, inf, rango = (float(x) for x in re.search(r"--tasa:([\d.]+)%;--inf:([\d.]+)%;--rango:([\d.]+)%", crudo).groups())
        assert tasa == pytest.approx(100 * f["valor"] * 100 / tope, abs=1e-3) and inf == pytest.approx(100 * f["ic95_inf"] * 100 / tope, abs=1e-3)
        assert rango == pytest.approx(100 * (f["ic95_sup"] - f["ic95_inf"]) * 100 / tope, abs=1e-3)


@pytest.mark.parametrize("filas,mayor_limite", [
    ([{"valor": 0.0, "ic95_sup": 0.0}], 0), ([{"valor": 0.04, "ic95_sup": 0.07}], 7), ([{"valor": 0.5, "ic95_sup": 0.97}], 97), ([{"valor": None, "ic95_sup": None}], 0),
])
def test_la_escala_cubre_el_mayor_limite_y_tiene_pocas_marcas(filas, mayor_limite):
    t, marcas = vista.escala(filas)
    assert t >= mayor_limite and t >= 1 and marcas[0] == 0 and marcas[-1] == t and 2 <= len(marcas) <= 7


def test_la_cabecera_y_el_resumen_son_los_de_la_api(at, k1):
    texto = pa.texto_html(at)
    assert registro.pagina("estratos").pregunta in texto and "Corte de datos: 2026-09-02" in texto
    resumen = next(h.value for h in at.html if 'class="kpis"' in h.value)
    assert f"<b>{formato.numero(len(k1))}</b>estratos" in resumen
    assert f'<b class="ambar">{formato.numero(sum(1 for f in k1 if f["muestra_baja"]))}</b>' in resumen


def test_el_alcance_la_lectura_y_el_pie_son_los_del_panel_original(at, k1, metadata):
    texto = re.sub(r"\s+", " ", pa.texto_html(at))
    assert re.sub(r"\s+", " ", componentes.alcance_markdown(metadata).replace("**", "")) in texto
    assert re.sub(r"\s+", " ", redaccion.conclusion_estratos(k1)) in texto
    assert all(re.sub(r"\s+", " ", a) in texto for a in pagina.avisos_k1(k1)) and pagina.NOTA_COTAS in texto
    assert [c.value for c in at.caption if c.value.startswith("Fuente:")] == [componentes.texto_pie(metadata)]


def test_la_tabla_ancha_trae_el_mismo_aviso_de_desplazamiento_que_antes(at):
    assert componentes.AVISO_TABLA_ANCHA in pa.texto_html(at)


def test_la_guia_traduce_la_tasa_con_una_fila_real_y_las_curiosidades_citan_el_glosario(k1):
    etiquetas = pagina.etiquetas_k1(k1)
    pasos = vista.guia(k1, etiquetas)
    assert len(pasos) == 6 and all(p["titulo"] and p["texto"] and p["region"] for p in pasos)
    primera = next(f for f in k1 if not f["muestra_baja"])
    assert vista.frase_fila(primera) in pasos[3]["texto"] and formato.porcentaje(primera["valor"]) in pasos[3]["texto"]
    fichas = vista.fichas()
    assert len(fichas) == 3 and all(f["fundamento"].startswith("Glosario del panel · ") for f in fichas)
    assert {f["termino"] for f in activos.contenido("estratos")["fichas"]} <= set(glosario.TERMINOS_POR_PAGINA["estratos"])


def test_negativa_un_glosario_recortado_se_detecta_en_la_cabecera(monkeypatch):
    completo = glosario.TERMINOS_POR_PAGINA
    nombres = re.findall(r"<b>(.*?)</b><p>", vista.glosario_html("estratos", activos.contenido("estratos")))
    assert nombres == [glosario.TERMINOS[k][0] for k in completo["estratos"]]
    monkeypatch.setattr(glosario, "TERMINOS_POR_PAGINA", dict(completo, estratos=tuple(k for k in completo["estratos"] if k != "intervalo de Wilson")))
    recortados = re.findall(r"<b>(.*?)</b><p>", vista.glosario_html("estratos", activos.contenido("estratos")))
    assert "Intervalo de Wilson" not in recortados and len(recortados) == len(nombres) - 1


# ---------------------------------------------------------------- exportación
def test_la_lamina_exportable_es_autonoma_y_trae_las_cifras_de_la_api(k1, metadata, at):
    pg = registro.pagina("estratos")
    etiquetas = pagina.etiquetas_k1(k1)
    documento = vista.lamina(pg, "Resultados", "2026-09-02", metadata, k1, etiquetas, pagina.tabla_k1(k1), redaccion.conclusion_estratos(k1), pagina.NOTA_COTAS).decode("utf-8")
    assert documento.startswith("<!doctype html>") and 'http-equiv="Content-Security-Policy"' in documento
    assert hallazgos_plantilla(documento) == []
    for f in k1:
        assert formato.porcentaje(f["valor"]) in documento and formato.intervalo(f["ic95_inf"], f["ic95_sup"]) in documento
    assert "Corte de datos:</strong> 2026-09-02" in documento and componentes.texto_pie(metadata) in documento
    original = pagina.tabla_k1(k1)
    asistente = pa._Tablas()
    asistente.feed(documento)
    assert asistente.tablas[0][1:] == [[str(v) for v in fila] for fila in original.to_numpy().tolist()]


# ---------------------------------------------------------------- seguridad: todo texto de los datos se escapa
HOSTIL = '<img src=x onerror=alert(1)>"\'<script>alert(2)</script>'


def _filas_hostiles(k1):
    return [dict(f, grupo="estrato_" + HOSTIL if i == 0 else f["grupo"]) for i, f in enumerate(k1)]


def test_un_nombre_de_grupo_con_etiquetas_se_escapa_en_la_figura_el_detalle_y_la_lamina(k1, metadata):
    filas = _filas_hostiles(k1)
    etiquetas = pagina.etiquetas_k1(filas)
    tabla = pagina.tabla_k1(filas)
    cuerpo = vista.cuerpo(filas, etiquetas, tabla, "texto", pagina.avisos_k1(filas), pagina.NOTA_COTAS)
    documento = vista.lamina(registro.pagina("estratos"), "Resultados", "2026-09-02", metadata, filas, etiquetas, tabla, "texto", pagina.NOTA_COTAS).decode("utf-8")
    for salida in (cuerpo, documento):
        assert "<img" not in salida and "<script" not in salida and "onerror=alert" not in salida.replace("&lt;img src=x onerror=alert(1)&gt;", "")
        assert escape(HOSTIL) in salida or "&lt;img" in salida


def test_un_alcance_o_un_corte_con_etiquetas_se_escapa_en_la_cabecera_y_en_la_lamina(k1):
    meta = {"alcance_temporal": HOSTIL, "licencias": {"a": HOSTIL}}
    cabecera = vista.cabecera(registro.pagina("estratos"), "Resultados", HOSTIL, meta, k1)
    documento = vista.lamina(registro.pagina("estratos"), "Resultados", HOSTIL, meta, k1, pagina.etiquetas_k1(k1), pagina.tabla_k1(k1), "texto", pagina.NOTA_COTAS).decode("utf-8")
    for salida in (cabecera, documento):
        assert "<img" not in salida and "<script" not in salida


def test_negativa_el_detector_de_etiquetas_sin_escapar_reconoce_un_html_inseguro():
    assert "<img" in f"<td>{HOSTIL}</td>" and "<img" not in f"<td>{escape(HOSTIL)}</td>"


# ---------------------------------------------------------------- degradación
def test_con_la_api_caida_la_cabecera_y_el_aviso_siguen_visibles_sin_figura(entorno):
    import httpx

    from src.panel.cliente_api import ClienteApi

    cliente = ClienteApi("http://api.local", http=httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(503, json={"error": {"codigo": "base_no_disponible", "mensaje": "x"}}))), reintentos_conexion=0)
    sin_api = pa.pagina("estratos", pa.como_consulta(cliente))
    assert len(sin_api.exception) == 0 and len(sin_api.warning) >= 1
    assert not any('class="analisis"' in h.value for h in sin_api.html) and pa.titulo(sin_api) == registro.pagina("estratos").titulo
    assert "Traceback" not in pa.textos(sin_api)
