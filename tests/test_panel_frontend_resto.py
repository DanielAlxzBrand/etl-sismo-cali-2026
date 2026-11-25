"""Concentración, Calidad de la llave, Construcciones y Fuentes y sistema con la interfaz propia (D116): cada página muestra lo mismo que el panel original (tarjetas, tablas, notas y avisos con las
funciones de siempre), conserva sus funciones y exporta un documento autónomo. Construcciones, además, conserva la consulta paginada de la API, trata con cuidado la fila elegida y el CSV.

Qué NO demuestran: cómo se ven en un navegador ni que el JavaScript funcione (lo registran las capturas y el recorrido interactivo). Los datos hostiles son SINTÉTICOS.
"""
import csv
import io
import re
from html import escape, unescape

import pandas as pd
import pytest

from src.panel import claves, formato, glosario, redaccion, registro
from src.panel.configuracion import cargar_panel
from src.panel.frontend.marco import Contexto
from src.panel.paginas import calidad as p_calidad
from src.panel.paginas import concentracion as p_conc
from src.panel.paginas import construcciones as p_cons
from src.panel.paginas import fuentes as p_fuentes
from tests import panel_apoyo as pa
from tests.test_panel_frontend import HOSTIL, entorno, hallazgos_plantilla, metadata  # noqa: F401  (fixtures y ayudas compartidas)

PAGINAS4 = ("concentracion", "calidad", "construcciones", "fuentes")


def _normal(texto):
    return re.sub(r"\s+", " ", texto)


def _contexto(pagina_id, metadata_):
    return Contexto(registro.pagina(pagina_id), "Grupo", "2026-09-02", metadata_, None)


@pytest.fixture(scope="module")
def paginas4(entorno):
    return {p: pa.pagina(p, entorno) for p in PAGINAS4}


@pytest.fixture(scope="module")
def kpis(entorno):
    return entorno("/kpis").datos


@pytest.fixture(scope="module")
def calidad(entorno):
    return entorno("/calidad").datos


@pytest.fixture(scope="module")
def revision(entorno):
    return entorno("/llave/revision").datos


@pytest.fixture(scope="module")
def fuentes(entorno):
    return entorno("/fuentes").datos


@pytest.fixture(scope="module")
def salud(entorno):
    return entorno("/health").datos


@pytest.fixture(scope="module")
def construcciones(entorno):
    return entorno("/construcciones", limit=50, offset=0).datos


# ---------------------------------------------------------------- las cuatro páginas
@pytest.mark.parametrize("pagina_id,botones", [("concentracion", ["Exportar informe"]), ("calidad", ["Exportar informe"]),
                                               ("construcciones", ["Exportar informe", "Descargar CSV (filas mostradas)"]), ("fuentes", ["Exportar informe"])])
def test_cada_pagina_se_dibuja_con_cabecera_propia_glosario_y_exportaciones(paginas4, pagina_id, botones):
    at = paginas4[pagina_id]
    assert len(at.exception) == 0 and pa.titulo(at) == registro.pagina(pagina_id).titulo
    texto = pa.texto_html(at)
    assert registro.pagina(pagina_id).pregunta in texto and "Corte de datos: 2026-09-02" in texto
    assert sorted(b.proto.label for b in at.get("download_button")) == sorted(botones)
    pares, cerrado = pa.glosario_html(at)
    assert cerrado and pares == [tuple(x) for x in glosario.entradas(pagina_id)]


# ---------------------------------------------------------------- Concentración
def test_concentracion_muestra_las_tarjetas_la_tabla_y_la_lectura_del_panel_original(paginas4, kpis):
    at = paginas4["concentracion"]
    k3, k4 = next(f for f in kpis if f["kpi_id"] == "K3" and f["grupo"] == claves.K3_TOP10), next(f for f in kpis if f["kpi_id"] == "K4")
    esperadas = p_conc.tarjetas_k3(k3) + p_conc.tarjetas_k4(k4)
    assert [(f.label, f.value, f.help) for f in pa.fichas_html(at)] == esperadas and len(esperadas) == 5
    assert at.dataframe[0].value.equals(p_conc.tabla_k3(k3))
    texto = _normal(pa.textos(at))
    assert _normal(redaccion.conclusion_concentracion(k3, k4)) in texto and p_conc.NOTA_K3 in texto and p_conc.NOTA_K4 in texto
    valores = {f.label: f.value for f in pa.fichas_html(at)}
    assert valores["Correlación"] == formato.numero(k4["valor"], 3) and valores["p de permutación"] == formato.numero(p_conc.p_permutacion(k4["nota"]), 4)


def test_concentracion_muestra_la_nota_tal_cual_cuando_no_tiene_el_formato_y_el_informe_tambien(kpis, metadata):
    k3 = dict(next(f for f in kpis if f["kpi_id"] == "K3" and f["grupo"] == claves.K3_TOP10), nota="barrios raros sin pares")
    assert p_conc.tabla_k3(k3) is None
    informe = p_conc._informe(_contexto("concentracion", metadata), p_conc.tarjetas_k3(k3), None, k3, None, "lectura").decode("utf-8")
    assert "barrios raros sin pares" in informe and "<table" not in informe and "La API no devolvió el indicador K4." in informe


def test_el_informe_de_concentracion_trae_las_cifras_y_la_tabla_de_barrios(kpis, metadata):
    k3, k4 = next(f for f in kpis if f["kpi_id"] == "K3" and f["grupo"] == claves.K3_TOP10), next(f for f in kpis if f["kpi_id"] == "K4")
    tabla = p_conc.tabla_k3(k3)
    informe = p_conc._informe(_contexto("concentracion", metadata), p_conc.tarjetas_k3(k3), tabla, k3, p_conc.tarjetas_k4(k4), "lectura").decode("utf-8")
    assert hallazgos_plantilla(informe) == [] and "Content-Security-Policy" in informe
    analizador = pa._Tablas()
    analizador.feed(informe)
    assert analizador.tablas[0][1:] == [[str(v) for v in f] for f in tabla.to_numpy().tolist()]
    assert all(formato.numero(k4["valor"], 3) in informe for _ in [0])


# ---------------------------------------------------------------- Calidad de la llave
def test_calidad_muestra_las_tarjetas_las_tablas_y_el_aviso_del_panel_original(paginas4, calidad, revision):
    at = paginas4["calidad"]
    assert [(f.label, f.value, f.help) for f in pa.fichas_html(at)] == p_calidad.tarjetas_k5(calidad)
    assert at.dataframe[0].value.equals(p_calidad.tabla_nombre_validado(calidad)) and at.table[0].value.equals(p_calidad.tabla_revision(revision["items"]))
    assert [i.value for i in at.info] == [p_calidad.NO_DEMUESTRA] and f"**Confianza de la llave:** {calidad['llave_confianza']}" in [m.value for m in at.markdown]
    assert f"{formato.numero(revision['total_codigos'])} códigos; detalle en {revision['documento']}." in [c.value for c in at.caption]


def test_la_clasificacion_distingue_coincidentes_parciales_no_coincidentes_y_sin_dato():
    assert "el nombre se escribe distinto" in p_calidad.clasificar({"pct_coincide_poligono": 1})
    assert "parcial" in p_calidad.clasificar({"pct_coincide_poligono": 0.5}) and "renumeración" in p_calidad.clasificar({"pct_coincide_poligono": 0})
    assert p_calidad.clasificar({"pct_coincide_poligono": None}) == "sin dato de coincidencia"


def test_el_informe_de_calidad_trae_las_dos_tablas_y_lo_que_no_demuestra(calidad, revision, metadata):
    nombre, rev = p_calidad.tabla_nombre_validado(calidad), p_calidad.tabla_revision(revision["items"])
    informe = p_calidad._informe(_contexto("calidad", metadata), p_calidad.tarjetas_k5(calidad), "**Confianza de la llave:** x", nombre, rev, "resumen").decode("utf-8")
    assert hallazgos_plantilla(informe) == [] and escape(p_calidad.NO_DEMUESTRA) in informe
    analizador = pa._Tablas()
    analizador.feed(informe)
    assert analizador.tablas[0][1:] == [[str(v) for v in f] for f in nombre.to_numpy().tolist()] and analizador.tablas[1][1:] == [[str(v) for v in f] for f in rev.to_numpy().tolist()]


# ---------------------------------------------------------------- Fuentes y sistema
def test_fuentes_muestra_tarjetas_tablas_y_los_ocho_limites_del_panel_original(paginas4, metadata, fuentes, salud):
    at = paginas4["fuentes"]
    assert [(f.label, f.value, f.help) for f in pa.fichas_html(at)] == [(e, v, d or "") for e, v, d in p_fuentes.tarjetas_poblacion(metadata)]
    assert at.dataframe[0].value.equals(p_fuentes.tabla_filas(salud)) and at.table[0].value.equals(p_fuentes.tabla_fuentes(fuentes))
    puntos = [m.value for m in at.markdown if m.value.startswith("- ")]
    assert puntos == ["- " + p for p in p_fuentes.limites(metadata)] + ["- " + p for p in p_fuentes.LIMITACIONES] and len(p_fuentes.limites(metadata)) == 8
    assert fuentes["aviso"] in [c.value for c in at.caption]


def test_el_informe_de_fuentes_trae_los_ocho_limites_el_catalogo_y_las_filas_por_tabla(metadata, fuentes, salud):
    informe = p_fuentes._informe(_contexto("fuentes", metadata), p_fuentes.tarjetas_poblacion(metadata), "imágenes", p_fuentes.tabla_fuentes(fuentes), fuentes["aviso"], p_fuentes.tabla_filas(salud), salud,
                                 p_fuentes.limites(metadata)).decode("utf-8")
    assert hallazgos_plantilla(informe) == [] and informe.count("<li>") == 12
    texto = unescape(re.sub(r"<[^>]+>", "", informe))      # las negritas de Markdown pasan a <b>: se compara el texto visible
    assert all(re.sub(r"\*\*", "", p) in texto for p in p_fuentes.limites(metadata)) and all(f["licencia"] in texto for f in fuentes["fuentes"])


# ---------------------------------------------------------------- Construcciones: consulta, selección y CSV
def test_construcciones_pide_a_la_api_solo_la_pagina_con_el_limite_configurado(entorno):
    llamadas = []

    def espia(ruta, **parametros):
        if ruta == "/construcciones":
            llamadas.append(parametros)
        return entorno(ruta, **parametros)

    at = pa.pagina("construcciones", espia)
    tamano = int(cargar_panel()["tamano_pagina_tabla"])
    assert len(at.exception) == 0 and len(llamadas) == 1
    assert llamadas[0]["limit"] == tamano and llamadas[0]["offset"] == 0 and len(at.dataframe[0].value) <= tamano


@pytest.mark.parametrize("ajuste,offset_esperado,total_texto", [("pagina2", 50, "5.146 construcciones con estos filtros; página 2 de 103")])
def test_cambiar_de_pagina_cambia_el_desplazamiento_y_no_pide_mas_filas(entorno, ajuste, offset_esperado, total_texto):
    from streamlit.testing.v1 import AppTest

    llamadas = []

    def espia(ruta, **parametros):
        if ruta == "/construcciones":
            llamadas.append(parametros)
        return entorno(ruta, **parametros)

    pa.fijar_api(espia)
    at = AppTest.from_string(pa.CAMPO_SCRIPT.format(modulo="construcciones"), default_timeout=60).run()
    at.number_input(key="pagina").set_value(2).run()
    assert [c["offset"] for c in llamadas][-1] == offset_esperado and all(c["limit"] == 50 for c in llamadas)
    assert any(total_texto in c.value for c in at.caption)


def test_una_pagina_fuera_de_rango_tras_filtrar_muestra_el_aviso_y_conserva_las_herramientas(entorno):
    from streamlit.testing.v1 import AppTest

    pa.fijar_api(entorno)
    at = AppTest.from_string(pa.CAMPO_SCRIPT.format(modulo="construcciones"), default_timeout=60).run()
    at.selectbox(key="filtro_comuna").select("20").run()
    at.number_input(key="pagina").set_value(50).run()
    assert len(at.exception) == 0 and "No hay construcciones en esta página con estos filtros." in pa.textos(at)
    assert not at.dataframe and [b.proto.label for b in at.get("download_button")] == ["Exportar informe"]
    assert any("construcciones con estos filtros" in c.value for c in at.caption)


def test_la_tabla_de_construcciones_es_la_del_panel_original_y_el_csv_normal_es_identico(construcciones):
    df = p_cons.tabla_de_items(construcciones["items"])
    assert p_cons.csv_seguro(df) == df.to_csv(index=False).encode("utf-8")
    filas = list(csv.reader(io.StringIO(p_cons.csv_seguro(df).decode("utf-8"))))
    assert filas[0] == list(df.columns) and len(filas) == len(df) + 1


@pytest.mark.parametrize("valor", ["=HYPERLINK(\"http://x\",\"a\")", "+1+1", "-2+3", "@SUM(A1)", "\tcmd", "\rcmd"])
def test_el_csv_neutraliza_las_celdas_que_una_hoja_de_calculo_ejecutaria_como_formula(valor):
    df = pd.DataFrame([{"Construcción": 1, "Barrio": valor, "Comuna": "20"}])
    celda = list(csv.reader(io.StringIO(p_cons.csv_seguro(df).decode("utf-8"))))[1][1]
    assert celda == "'" + valor.replace("\r", "\r") and not celda.startswith(p_cons.INICIO_PELIGROSO)


def test_el_csv_no_altera_las_celdas_de_texto_normales_ni_los_numeros():
    df = pd.DataFrame([{"Construcción": 7, "Barrio": "Siloé", "Estrato": "−1", "Clase": "—"}])
    celdas = list(csv.reader(io.StringIO(p_cons.csv_seguro(df).decode("utf-8"))))[1]
    assert celdas == ["7", "Siloé", "−1", "—"]


def test_la_clave_de_seleccion_cambia_con_cada_filtro_y_con_la_pagina():
    base_ = p_cons.clave_de_seleccion("Todas", "Todas", "Todas", 1)
    otras = [p_cons.clave_de_seleccion("20", "Todas", "Todas", 1), p_cons.clave_de_seleccion("Todas", "3", "Todas", 1),
             p_cons.clave_de_seleccion("Todas", "Todas", "Solo con cambio satelital severo", 1), p_cons.clave_de_seleccion("Todas", "Todas", "Todas", 2)]
    assert len({base_, *otras}) == 5


class _Evento:
    def __init__(self, filas):
        self.selection = type("S", (), {"rows": filas})()


def test_una_seleccion_obsoleta_o_vacia_no_elige_ninguna_fila():
    items = [{}] * 3
    assert p_cons.fila_elegida(_Evento([1]), items) == 1 and p_cons.fila_elegida(_Evento([]), items) is None
    assert p_cons.fila_elegida(_Evento([7]), items) is None and p_cons.fila_elegida(_Evento([-1]), items) is None and p_cons.fila_elegida(None, items) is None


@pytest.mark.parametrize("severo,fragmento", [(True, "cuenta como cambio satelital severo"), (False, "no cuenta como cambio satelital severo"), (None, "no tiene clasificación satelital")])
def test_la_fila_elegida_se_lee_en_palabras_con_sus_valores_y_sin_inventar_ninguno(severo, fragmento):
    item = {"objectid": 42, "comuna": "20", "barrio": "Siloé", "codigo_barrio": "2001", "estrato": 2, "clase_dano": "escombros", "severo_estricto": severo, "nombre_validado": True, "lon": None, "lat": None}
    texto = p_cons.descripcion_de_fila(item)
    assert fragmento in texto and "42" in texto and "Siloé" in texto and "comuna 20" in texto and "«escombros»" in texto and "estrato 2 es el de su barrio" in texto
    sin = p_cons.descripcion_de_fila(dict(item, barrio=None, comuna=None, estrato=None, clase_dano=None, nombre_validado=None))
    assert sin.count(formato.SIN_DATO) >= 5


def test_el_informe_de_construcciones_trae_solo_las_filas_mostradas_y_escapa_los_valores(construcciones, metadata):
    df = p_cons.tabla_de_items(construcciones["items"])
    informe = p_cons._informe(_contexto("construcciones", metadata), "resumen de la consulta", df).decode("utf-8")
    analizador = pa._Tablas()
    analizador.feed(informe)
    assert analizador.tablas[0][1:] == [[str(v) for v in f] for f in df.to_numpy().tolist()] and len(analizador.tablas[0]) - 1 <= 50
    hostil = df.assign(Barrio=HOSTIL)
    salida = p_cons._informe(_contexto("construcciones", metadata), HOSTIL, hostil).decode("utf-8")
    assert "<img" not in salida and "<script" not in salida      # el texto hostil queda escapado: «onerror=» como texto no es un manejador de eventos
    vacio = p_cons._informe(_contexto("construcciones", metadata), "sin filas", None).decode("utf-8")
    assert "No hay construcciones en esta página con estos filtros." in vacio and "<table" not in vacio


def test_la_guia_de_construcciones_cita_la_consulta_real(paginas4):
    from src.panel.frontend import vista as base

    pasos = base.guia("construcciones", "5.146 construcciones con estos filtros; esta página muestra 50 filas.")
    assert len(pasos) == 6 and "5.146" in pasos[3]["texto"]


# ---------------------------------------------------------------- seguridad y degradación en las cuatro páginas
def test_un_texto_hostil_se_escapa_en_los_informes_de_concentracion_calidad_y_fuentes(kpis, calidad, revision, fuentes, salud, metadata):
    k3 = dict(next(f for f in kpis if f["kpi_id"] == "K3" and f["grupo"] == claves.K3_TOP10), nota=HOSTIL)
    c = _contexto("concentracion", metadata)
    a = p_conc._informe(c, p_conc.tarjetas_k3(k3), None, k3, [(HOSTIL, HOSTIL, HOSTIL)], HOSTIL).decode("utf-8")
    rev = p_calidad.tabla_revision([dict(i, nombre_csv_2015=HOSTIL, nombre_poligono_dominante=HOSTIL) for i in revision["items"]])
    b = p_calidad._informe(_contexto("calidad", metadata), [(HOSTIL, HOSTIL, HOSTIL)], HOSTIL, p_calidad.tabla_nombre_validado(calidad), rev, HOSTIL).decode("utf-8")
    ft = p_fuentes.tabla_fuentes({"fuentes": [dict(f, nombre=HOSTIL, licencia=HOSTIL) for f in fuentes["fuentes"]]})
    d = p_fuentes._informe(_contexto("fuentes", metadata), [(HOSTIL, HOSTIL, None)], HOSTIL, ft, HOSTIL, p_fuentes.tabla_filas(salud), salud, [HOSTIL]).decode("utf-8")
    for salida in (a, b, d):
        assert "<img" not in salida and "<script" not in salida and escape(HOSTIL) in salida


@pytest.mark.parametrize("pagina_id", PAGINAS4)
def test_con_la_api_caida_cada_pagina_conserva_cabecera_y_aviso_sin_trazas(pagina_id):
    import httpx

    from src.panel.cliente_api import ClienteApi

    cliente = ClienteApi("http://api.local", http=httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(503, json={"error": {"codigo": "base_no_disponible", "mensaje": "x"}}))), reintentos_conexion=0)
    at = pa.pagina(pagina_id, pa.como_consulta(cliente))
    assert len(at.exception) == 0 and len(at.warning) >= 1 and pa.titulo(at) == registro.pagina(pagina_id).titulo and "Traceback" not in pa.textos(at)
