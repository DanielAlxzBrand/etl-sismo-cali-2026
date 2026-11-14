"""Textos del panel que no vienen de la API: los límites de la página «Fuentes», las notas de K3 y K4 y las frases de redacción.

Qué vigilan (D81):
- que «qué no se puede concluir» del panel siga diciendo lo mismo que `docs/gold/KPIs.md` (mismo número de puntos y las mismas ideas);
- que las funciones que leen las notas de K3 y K4 lean la nota real y, ante una nota alterada, caigan a mostrarla tal cual;
- que NINGUNA función de redacción afirme causalidad ni que el estrato no influye, y que una función de texto nueva no quede sin cubrir.

Los valores de redacción de este archivo son SINTÉTICOS (inventados para recorrer cada rama); no son datos del proyecto.
"""
import csv
import dataclasses
import inspect
import re
import shutil

import pytest

from src.common import ROOT
from src.panel import claves, formato, redaccion
from src.panel.paginas import concentracion, fuentes
from tests import panel_apoyo as pa


def _plano(texto):
    """Texto comparable: minúsculas, sin negritas ni comillas de código y con espacios simples."""
    return re.sub(r"\s+", " ", re.sub(r"[*`]", "", texto)).strip().lower()


# ---------------------------------------------------------------- 5.1 · límites del panel frente a KPIs.md

# Frases ancla que ambos textos deben contener (una por idea del punto). Se eligieron leyendo los ocho puntos.
ANCLAS_COMUNES = (
    ("cambio visible desde satélite", "no sustituye"),                     # 1 · el proxy no es daño interno ni inspección
    ("no se extrapolan", "describen esta muestra"),                         # 2 · pocas comunas; no se extrapola a Cali
    ("no es aleatoria", "cotas"),                                           # 3 · sin datos en E2 no es aleatoria
    ("muestra baja",),                                                      # 4 · estratos con muestra baja
    ("falacia ecológica", "lados de manzana"),                              # 5 · estrato por barrio
    ("baja confianza", "grupo de control"),                                 # 6 · daño visible
    ("asociación no", "diferencia entre estratos"),                         # 7 · asociación no es causa
    ("grupo de estratos 1-2", "en la práctica"),                            # 8 · estrato confundido con comuna
)
# Frase del panel que fija el SENTIDO de cada punto: si alguien la cambia («muy pocas» por «muchas»), debe fallar.
SENTIDO_DEL_PANEL = (
    "no daño interno",
    "las comunas ausentes no se pueden evaluar",
    "no se ordenan frente a los demás",
    "se muestran, pero no se ordenan",
    "es anterior al evento",
    "imágenes separadas por meses y sin grupo de control",
    "no demuestra que el estrato carezca de efecto",
    "muy pocas comunas",
)


def puntos_de_kpis(texto):
    """Puntos numerados de la sección «Qué NO se puede concluir» de KPIs.md (sin el número)."""
    seccion = texto.split("## Qué NO se puede concluir", 1)[1].split("\n## ", 1)[0]
    return [re.sub(r"^\d+\.\s*", "", l) for l in seccion.splitlines() if re.match(r"^\d+\. ", l)]


def revisar_limites(puntos_kpis, puntos_panel, anclas=ANCLAS_COMUNES, sentido=SENTIDO_DEL_PANEL):
    """Errores de la correspondencia entre los puntos de KPIs.md y los del panel (lista vacía si coinciden)."""
    errores = []
    if not (len(puntos_kpis) == len(puntos_panel) == len(anclas) == len(sentido)):
        return [f"distinto número de puntos: KPIs.md {len(puntos_kpis)}, panel {len(puntos_panel)}, anclas {len(anclas)}, sentido {len(sentido)}"]
    for i, (k, p, a, s) in enumerate(zip(puntos_kpis, puntos_panel, anclas, sentido), 1):
        k, p = _plano(k), _plano(p)
        errores += [f"punto {i}: KPIs.md no contiene «{x}»" for x in a if x not in k]
        errores += [f"punto {i}: el panel no contiene «{x}»" for x in a if x not in p]
        if s not in p:
            errores.append(f"punto {i}: el panel cambió la frase que fija su sentido («{s}»)")
    return errores


def _kpis_md():
    return (ROOT / "docs" / "gold" / "KPIs.md").read_text(encoding="utf-8")


def test_los_limites_del_panel_dicen_lo_mismo_que_kpis_md():
    assert revisar_limites(puntos_de_kpis(_kpis_md()), list(fuentes.LIMITES)) == []


def test_kpis_md_lista_ocho_puntos_de_que_no_se_puede_concluir():
    assert len(puntos_de_kpis(_kpis_md())) == len(fuentes.LIMITES) == len(ANCLAS_COMUNES)


def test_negativa_un_punto_de_menos_o_de_mas_se_detecta():
    k, p = puntos_de_kpis(_kpis_md()), list(fuentes.LIMITES)
    assert "distinto número" in revisar_limites(k, p[:-1])[0]
    assert "distinto número" in revisar_limites(k + ["Un punto nuevo."], p)[0]


def test_negativa_cambiar_el_sentido_sin_tocar_digitos_se_detecta():
    k, p = puntos_de_kpis(_kpis_md()), list(fuentes.LIMITES)
    p[7] = p[7].replace("muy pocas comunas", "muchas comunas")
    assert any("punto 8" in e and "sentido" in e for e in revisar_limites(k, p))


def test_negativa_si_kpis_md_cambia_una_idea_el_panel_ya_no_coincide():
    k, p = puntos_de_kpis(_kpis_md()), list(fuentes.LIMITES)
    k[1] = k[1].replace("no se extrapolan", "se pueden extrapolar")
    assert any("punto 2" in e and "KPIs.md" in e for e in revisar_limites(k, p))


def test_negativa_un_punto_del_panel_sin_la_idea_ancla_se_detecta():
    k, p = puntos_de_kpis(_kpis_md()), list(fuentes.LIMITES)
    p[6] = "Un punto distinto que no habla de asociación."
    assert any("punto 7" in e for e in revisar_limites(k, p))


# ---------------------------------------------------------------- 5.2 · notas de K3 y K4

def _fila_kpi(kpi_id):
    with open(ROOT / "data" / "gold" / "kpis_gold.csv", encoding="utf-8", newline="") as f:
        return next(r for r in csv.DictReader(f) if r["kpi_id"] == kpi_id)


def _pares_leidos_aparte(nota):
    """Los pares «código:severos» de la nota de K3 leídos con otro método (cortes de texto, sin expresión regular)."""
    cuerpo = nota.split("severos ", 1)[1].split("; esos", 1)[0]
    return [(a, int(b)) for a, b in (p.split(":") for p in cuerpo.split("; "))]


def test_la_nota_real_de_k3_se_lee_completa():
    fila = _fila_kpi("K3")
    esperados = _pares_leidos_aparte(fila["nota"])
    assert concentracion.barrios_de_la_nota(fila["nota"]) == esperados
    assert len(esperados) == int(re.search(r"top(\d+)_barrios", fila["grupo"])[1])
    assert sum(n for _, n in esperados) == int(float(fila["numerador"]))      # los severos de la tabla suman el numerador de K3
    assert all(isinstance(c, str) and isinstance(n, int) for c, n in esperados)


def test_la_nota_real_de_k3_trae_las_construcciones_y_su_porcentaje_coincide():
    nota = _fila_kpi("K3")["nota"]
    a, b = (int(x) for x in re.findall(r"\((\d+) de (\d+)\)", nota)[0])
    assert concentracion.construcciones_de_la_nota(nota) == (a, b)
    assert formato.porcentaje(a / b, 1) in nota                                # «48,7 %» de la nota = el que calcula el panel


def test_la_nota_real_de_k4_trae_p_de_permutacion_y_n_de_barrios():
    fila = _fila_kpi("K4")
    p = float(fila["nota"].split("p_permutacion=", 1)[1].split(" ", 1)[0])
    assert concentracion.p_permutacion(fila["nota"]) == p and 0 < p <= 1
    assert int(re.search(r"n_barrios=(\d+)", fila["nota"])[1]) == int(float(fila["denominador"]))


@pytest.mark.parametrize("rotulo,cambio", [
    ("sin barrios (solo la parte de las construcciones)", lambda n: "esos barrios reúnen " + n.split("esos barrios reúnen ", 1)[1]),
    ("dos puntos cambiados por guion", lambda n: n.replace(":", "-")),
    ("sin la palabra «severos»", lambda n: n.replace("severos ", "")),
    ("nota vacía", lambda n: ""),
    ("nota ausente", lambda n: None),
    ("texto libre", lambda n: "sin detalle disponible por ahora"),
])
def test_si_la_nota_de_k3_no_tiene_el_formato_no_se_inventan_barrios(rotulo, cambio):
    assert concentracion.barrios_de_la_nota(cambio(_fila_kpi("K3")["nota"])) == [], rotulo


@pytest.mark.parametrize("rotulo,cambio", [
    ("separador «, »", lambda n: n.replace("; ", ", ")),
    ("separador «,» sin espacio", lambda n: n.replace("; ", ",")),
    ("separador «;» sin espacio", lambda n: n.replace("; ", ";")),
    ("separador « / »", lambda n: n.replace("; ", " / ")),
    ("separador « & »", lambda n: n.replace("; ", " & ")),
    ("un par incompleto al final", lambda n: n.replace("1903:10", "1903:")),
    ("punto en lugar de «;» antes del texto final", lambda n: n.replace("1903:10; esos", "1903:10. esos")),
])
def test_si_la_nota_de_k3_cambia_de_separador_no_se_muestra_una_tabla_a_medias(rotulo, cambio):
    """Antes de corregirlo, un separador distinto dejaba pasar solo el primer barrio (1 de 10); ahora la lectura es completa o vacía (D78, D81)."""
    nota = cambio(_fila_kpi("K3")["nota"])
    assert nota != _fila_kpi("K3")["nota"], rotulo
    assert concentracion.barrios_de_la_nota(nota) == [], rotulo


def test_la_lectura_de_la_nota_de_k3_acepta_el_formato_con_o_sin_cierre():
    pares = "1914:30; 1913:25; 306:21"
    esperado = [("1914", 30), ("1913", 25), ("306", 21)]
    assert concentracion.barrios_de_la_nota(f"códigos:severos {pares}; esos barrios reúnen 1 %") == esperado
    assert concentracion.barrios_de_la_nota(f"códigos:severos {pares}") == esperado
    assert concentracion.barrios_de_la_nota(f"códigos:severos {pares};") == esperado


@pytest.mark.parametrize("nota,esperado", [
    ("p_permutacion=0.8218 (5000 permutaciones)", 0.8218),
    ("n_barrios=45; p_permutacion=0.8218.", 0.8218),      # el punto final es el de la frase
    ("p_permutacion=1", 1.0),
    ("p_permutacion=0.8218.5", None),
    ("p_permutacion=.", None),
    ("p_permutacion=abc", None),
])
def test_p_permutacion_nunca_falla_con_un_texto_mal_formado(nota, esperado):
    """Antes de corregirlo, «p_permutacion=0.8218.» lanzaba ValueError y hacía caer la página de Concentración."""
    assert concentracion.p_permutacion(nota) == esperado


def test_la_pagina_con_otro_separador_en_la_nota_de_k3_muestra_la_nota_tal_cual(api_real):
    nota = _fila_kpi("K3")["nota"].replace("; ", ", ")
    at = pa.pagina("concentracion", _api_con_nota_de_k3(api_real, nota))
    assert not at.exception
    assert len(at.dataframe) == 0 and nota in [i.value for i in at.info]


@pytest.mark.parametrize("nota", ["", None, "texto libre", "(2292/4709)", "(dos de tres)"])
def test_si_la_nota_no_trae_las_construcciones_devuelve_none(nota):
    assert concentracion.construcciones_de_la_nota(nota) is None


@pytest.mark.parametrize("nota", ["", None, "texto libre", "p_permutacion=", "sin p"])
def test_si_la_nota_no_trae_la_p_de_permutacion_devuelve_none(nota):
    assert concentracion.p_permutacion(nota) is None


@pytest.fixture(scope="module")
def api_real():
    carpeta, ruta = pa.copia_temporal_de_la_base()
    http, cliente = pa.api_en_memoria(ruta)
    yield pa.como_consulta(cliente)
    cliente.cerrar()
    http.close()
    shutil.rmtree(carpeta, ignore_errors=True)


def _api_con_nota_de_k3(api, nota):
    """La API real, con la nota de K3 reemplazada por `nota` (el resto sin cambios)."""
    def envuelta(ruta, **params):
        r = api(ruta, **params)
        if ruta != "/kpis":
            return r
        filas = [dict(f, nota=nota) if (f["kpi_id"], f["grupo"]) == (claves.K3, claves.K3_TOP10) else f for f in r.datos]
        return dataclasses.replace(r, datos=filas)
    return envuelta


def test_la_pagina_con_la_nota_de_k3_sin_barrios_muestra_la_nota_tal_cual(api_real):
    """D78: si la nota de K3 cambia de formato, la tabla de barrios cae a mostrar la nota."""
    nota = "detalle de los barrios no disponible en este momento"
    at = pa.pagina("concentracion", _api_con_nota_de_k3(api_real, nota))
    assert not at.exception
    assert len(at.dataframe) == 0 and nota in [i.value for i in at.info]


def test_la_pagina_con_la_nota_real_de_k3_muestra_la_tabla_de_barrios(api_real):
    at = pa.pagina("concentracion", api_real)
    assert not at.exception and len(at.dataframe[0].value) == len(_pares_leidos_aparte(_fila_kpi("K3")["nota"]))


# ---------------------------------------------------------------- 5.3 · ninguna frase generada afirma causalidad

PROHIBIDAS = [r"el estrato no influye", r"el estrato no tiene efecto", r"el estrato no importa", r"no hay efecto del estrato",
              r"prevalencia en cali", r"\bcausa\b", r"\bcausó\b", r"\bprovoca\b", r"\bprovocó\b", r"debido al estrato", r"a causa del estrato",
              r"demuestra que el estrato", r"prueba que el estrato", r"\bnan\b", r"\bnone\b"]
NEGACIONES_PERMITIDAS = ["no una causa", "no establece causalidad"]       # frases que niegan la causa: no son una afirmación

# VALORES SINTÉTICOS: filas inventadas con la forma de las respuestas de la API.
K1_SINTETICO = [
    {"grupo": "estrato_1", "ic95_inf": 0.01, "ic95_sup": 0.20, "muestra_baja": True},
    {"grupo": "estrato_3", "ic95_inf": 0.10, "ic95_sup": 0.20, "muestra_baja": False},
    {"grupo": "estrato_4", "ic95_inf": 0.12, "ic95_sup": 0.22, "muestra_baja": False},
    {"grupo": "estrato_5", "ic95_inf": 0.40, "ic95_sup": 0.50, "muestra_baja": False},
]
COMPOSICION_SINTETICA = [{"grupo_estrato": "1-2", "comuna": "20", "n_con_datos": 300}, {"grupo_estrato": "1-2", "comuna": "18", "n_con_datos": 50},
                         {"grupo_estrato": "3-5", "comuna": "19", "n_con_datos": 900}]
ESCENARIO_CON_CERO = {"ic95_inf": -0.05, "ic95_sup": 0.05, "tasa": 0.01}
ESCENARIO_SIN_CERO = {"ic95_inf": 0.02, "ic95_sup": 0.09, "tasa": 0.05}

CASOS_DE_TEXTO = {
    "conclusion_diferencia": [
        lambda: redaccion.conclusion_diferencia(0.0, -0.1, 0.1, False, False), lambda: redaccion.conclusion_diferencia(0.1, 0.05, 0.2, False, True),
        lambda: redaccion.conclusion_diferencia(-0.1, -0.2, -0.05, True, True), lambda: redaccion.conclusion_diferencia(0.1, 0.02, 0.2, True, False),
        lambda: redaccion.conclusion_diferencia(None, None, None)],
    "conclusion_cotas": [
        lambda: redaccion.conclusion_cotas([{"cota_inf": 0.0, "cota_sup": 0.3}, {"cota_inf": 0.1, "cota_sup": 0.4}]),
        lambda: redaccion.conclusion_cotas([{"cota_inf": 0.0, "cota_sup": 0.1}, {"cota_inf": 0.2, "cota_sup": 0.4}]),
        lambda: redaccion.conclusion_cotas([{"cota_inf": None, "cota_sup": None}])],
    "conclusion_estratos": [lambda: redaccion.conclusion_estratos(K1_SINTETICO), lambda: redaccion.conclusion_estratos([]),
                            lambda: redaccion.conclusion_estratos([{"grupo": "estrato_2", "muestra_baja": True}])],
    "comuna_que_concentra": [lambda: redaccion.comuna_que_concentra(COMPOSICION_SINTETICA), lambda: redaccion.comuna_que_concentra([]),
                             lambda: redaccion.comuna_que_concentra(COMPOSICION_SINTETICA, grupo="3-5")],
    "conclusion_comunas": [lambda: redaccion.conclusion_comunas([{"comuna": "09", "muestra_baja": True}, {"comuna": "19", "muestra_baja": False}]),
                           lambda: redaccion.conclusion_comunas([])],
    "conclusion_escenario": [lambda: redaccion.conclusion_escenario("S1", ESCENARIO_CON_CERO), lambda: redaccion.conclusion_escenario("S2", ESCENARIO_SIN_CERO),
                             lambda: redaccion.conclusion_escenario("S3", None), lambda: redaccion.conclusion_escenario("S4", {"ic95_inf": None})],
    "conclusion_sensibilidades": [
        lambda: redaccion.conclusion_sensibilidades([dict(ESCENARIO_CON_CERO, escenario="S0"), dict(ESCENARIO_CON_CERO, escenario="S1")]),
        lambda: redaccion.conclusion_sensibilidades([dict(ESCENARIO_CON_CERO, escenario="S0"), dict(ESCENARIO_SIN_CERO, escenario="S4")]),
        lambda: redaccion.conclusion_sensibilidades([])],
    "aviso_mantel_haenszel": [lambda: redaccion.aviso_mantel_haenszel(None, None), lambda: redaccion.aviso_mantel_haenszel({"tasa": None}, 0),
                              lambda: redaccion.aviso_mantel_haenszel({"tasa": 1.2}, 1), lambda: redaccion.aviso_mantel_haenszel({"tasa": 1.2}, 3)],
    "conclusion_concentracion": [
        lambda: redaccion.conclusion_concentracion({"valor": 0.5, "numerador": 50, "denominador": 100}, {"valor": 0.03, "denominador": 45}),
        lambda: redaccion.conclusion_concentracion(None, None), lambda: redaccion.conclusion_concentracion({"valor": 0.5, "numerador": 5, "denominador": 10}, None)],
}
FUNCIONES_QUE_NO_ESCRIBEN_TEXTO = {"incluye_cero", "se_solapan"}


def funciones_publicas(modulo):
    """Nombres de las funciones públicas definidas en el módulo (no importadas y sin guion bajo inicial)."""
    return {n for n, f in inspect.getmembers(modulo, inspect.isfunction) if not n.startswith("_") and f.__module__ == modulo.__name__}


def prohibidas_en(texto):
    """Patrones prohibidos presentes en `texto`, tras quitar las frases que niegan la causa."""
    limpio = texto.lower()
    for permitida in NEGACIONES_PERMITIDAS:
        limpio = limpio.replace(permitida, "")
    return [p for p in PROHIBIDAS if re.search(p, limpio)]


def test_toda_funcion_publica_de_redaccion_esta_cubierta():
    """Si se agrega una función de texto a redaccion.py sin sus casos aquí (o sin declararla sin texto), esta prueba falla."""
    assert funciones_publicas(redaccion) == set(CASOS_DE_TEXTO) | FUNCIONES_QUE_NO_ESCRIBEN_TEXTO


@pytest.mark.parametrize("nombre", sorted(CASOS_DE_TEXTO))
def test_ninguna_rama_de_cada_funcion_de_texto_afirma_causalidad(nombre):
    textos = [caso() for caso in CASOS_DE_TEXTO[nombre]]
    assert textos and all(isinstance(t, str) for t in textos)
    for t in textos:
        assert prohibidas_en(t) == [], f"{nombre}: {t!r}"


def test_negativa_el_detector_reconoce_las_afirmaciones_prohibidas():
    assert prohibidas_en("En esta muestra el estrato no influye en el daño.") == [r"el estrato no influye"]
    assert prohibidas_en("El estrato provoca el daño por una causa clara.") == [r"\bcausa\b", r"\bprovoca\b"]
    assert prohibidas_en("La diferencia es nan puntos.") == [r"\bnan\b"]
    assert prohibidas_en("Describe la muestra y no una causa; una asociación no establece causalidad.") == []


def test_negativa_una_funcion_de_texto_nueva_sin_casos_se_detecta():
    declaradas = set(CASOS_DE_TEXTO) | FUNCIONES_QUE_NO_ESCRIBEN_TEXTO
    assert funciones_publicas(redaccion) | {"conclusion_nueva"} != declaradas
