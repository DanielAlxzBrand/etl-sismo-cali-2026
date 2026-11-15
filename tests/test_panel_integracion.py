"""Integración interfaz ↔ API ↔ almacenamiento: el panel, conectado en memoria a la API REAL sobre una copia temporal de la SQLite (solo lectura),
muestra valores que coinciden con las salidas del pipeline (kpis_gold.csv, kpis_sensibilidad.csv, gold_final.csv, quality_report.json) leídas y recalculadas aquí."""
import csv
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import pytest

from src.panel import formato
from tests import panel_apoyo as pa

RAIZ = Path(__file__).resolve().parents[1]
GOLD = RAIZ / "data" / "gold"


def _csv(ruta):
    with open(ruta, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _f(valor):
    return None if valor in ("", None) else float(valor)


def _b(valor):
    return str(valor).strip().lower() == "true"


@pytest.fixture(scope="module")
def datos():
    return {"kpis": _csv(GOLD / "kpis_gold.csv"), "sens": _csv(GOLD / "kpis_sensibilidad.csv"), "gold": _csv(GOLD / "gold_final.csv"),
            "calidad": json.loads((RAIZ / "data" / "silver" / "quality_report.json").read_text(encoding="utf-8"))}


@pytest.fixture(scope="module")
def paginas():
    carpeta, ruta = pa.copia_temporal_de_la_base()
    http, cliente = pa.api_en_memoria(ruta)
    api = pa.como_consulta(cliente)
    yield {p: pa.pagina(p, api) for p in ("respuesta", "estratos", "comunas", "sensibilidades", "concentracion", "calidad", "fuentes")}, api
    cliente.cerrar()
    http.close()
    shutil.rmtree(carpeta, ignore_errors=True)


def _k(datos, kpi, grupo=None):
    return next(r for r in datos["kpis"] if r["kpi_id"] == kpi and (grupo is None or r["grupo"] == grupo))


def _metricas(at):
    return {m.label: m for m in at.metric}


def _con_datos(gold):
    return [g for g in gold if not _b(g["sin_datos"])]


# ---------- Respuesta (K2 y K5) ----------
def test_respuesta_muestra_k2_igual_a_kpis_gold_y_a_lo_recalculado_de_gold_final(paginas, datos):
    m = _metricas(paginas[0]["respuesta"])
    t35, t12 = _k(datos, "K2", "estratos_3-5"), _k(datos, "K2", "estratos_1-2")
    dif, razon = _k(datos, "K2", "diferencia_3-5_menos_1-2"), _k(datos, "K2", "razon_3-5_vs_1-2")
    assert m["Tasa 3-5"].value == formato.porcentaje(_f(t35["valor"]))
    assert m["Tasa 1-2 (muestra baja)"].value == formato.porcentaje(_f(t12["valor"]))
    assert m["Diferencia (3-5 menos 1-2)"].value == formato.puntos_porcentuales(_f(dif["valor"]))
    assert m["Razón de tasas (3-5 / 1-2)"].value == formato.razon(_f(razon["valor"]))
    # recálculo independiente desde gold_final.csv
    cd = _con_datos(datos["gold"])
    n35 = [g for g in cd if g["estrato"] and 3 <= float(g["estrato"]) <= 5]
    n12 = [g for g in cd if g["estrato"] and 1 <= float(g["estrato"]) <= 2]
    k35, k12 = sum(_b(g["severo_estricto"]) for g in n35), sum(_b(g["severo_estricto"]) for g in n12)
    assert (k35, len(n35)) == (int(float(t35["numerador"])), int(float(t35["denominador"])))
    assert (k12, len(n12)) == (int(float(t12["numerador"])), int(float(t12["denominador"])))
    assert m["Tasa 3-5"].value == formato.porcentaje(k35 / len(n35))
    assert m["Tasa 1-2 (muestra baja)"].value == formato.porcentaje(k12 / len(n12))
    assert m["Diferencia (3-5 menos 1-2)"].value == formato.puntos_porcentuales(k35 / len(n35) - k12 / len(n12))


def test_respuesta_muestra_k5_con_el_formato_de_los_documentos(paginas, datos):
    m = _metricas(paginas[0]["respuesta"])
    assert m["Cobertura de la llave"].value == "99,883 %" and m["Estrato válido"].value == "99,845 %" and m["Nombre validado"].value == "93,52 %"
    q = datos["calidad"]
    assert m["Estrato válido"].value == formato.porcentaje(q["cobertura_estrato_valido"]["pct"], 3)
    assert m["Estrato válido"].help == f"{formato.numero(q['cobertura_estrato_valido']['num'])} de {formato.numero(q['cobertura_estrato_valido']['den'])}"


# ---------- Estratos (K1) ----------
def test_estratos_coincide_con_k1_y_con_los_conteos_de_gold_final(paginas, datos):
    tabla = paginas[0]["estratos"].dataframe[0].value
    filas = [r for r in datos["kpis"] if r["kpi_id"] == "K1"]
    assert len(tabla) == len(filas) == 6
    cd = _con_datos(datos["gold"])
    sin = Counter(int(float(g["estrato"])) for g in datos["gold"] if _b(g["sin_datos"]) and g["estrato"])
    for i, r in enumerate(filas):
        e = int(r["grupo"][-1])
        del_estrato = [g for g in cd if g["estrato"] and int(float(g["estrato"])) == e]
        k = sum(_b(g["severo_estricto"]) for g in del_estrato)
        fila = tabla.iloc[i]
        assert fila["Severos"] == formato.numero(k) and fila["Con datos"] == formato.numero(len(del_estrato))
        assert fila["Tasa"] == formato.porcentaje(k / len(del_estrato))
        assert fila["Intervalo de Wilson"] == formato.intervalo(_f(r["ic95_inf"]), _f(r["ic95_sup"]))
        assert fila["Sin datos"] == formato.numero(sin[e]) and fila["% sin datos"] == formato.porcentaje(_f(r["pct_sin_datos"]), 1)
        assert fila["Cotas por «sin datos»"] == formato.intervalo(_f(r["cota_inf"]), _f(r["cota_sup"]))
        assert ("muestra baja" in fila["Estrato"]) == _b(r["muestra_baja"])


# ---------- Comunas (K6 y composición) ----------
def test_comunas_coincide_con_k6_y_con_los_conteos_de_gold_final(paginas, datos):
    tabla = paginas[0]["comunas"].dataframe[0].value
    filas = [r for r in datos["kpis"] if r["kpi_id"] == "K6"]
    assert len(tabla) == len(filas) == 7
    cd = _con_datos(datos["gold"])
    for i, r in enumerate(filas):
        c = r["grupo"].replace("comuna_", "")
        mias = [g for g in cd if g["comuna"] == c]
        k = sum(_b(g["severo_estricto"]) for g in mias)
        fila = tabla.iloc[i]
        assert fila["Comuna"].startswith(c)
        assert fila["Severos"] == formato.numero(k) and fila["Con datos"] == formato.numero(len(mias)) and fila["Tasa"] == formato.porcentaje(k / len(mias))
        assert fila["Intervalo de Wilson"] == formato.intervalo(_f(r["ic95_inf"]), _f(r["ic95_sup"]))
        assert ("muestra baja" in fila["Comuna"]) == _b(r["muestra_baja"])


def test_la_composicion_por_comuna_y_grupo_coincide_con_gold_final(paginas, datos):
    tabla = paginas[0]["comunas"].dataframe[1].value
    grupo = lambda e: "1-2" if e <= 2 else ("3-5" if e <= 5 else "6")   # noqa: E731
    cuenta, severos = Counter(), Counter()
    for g in _con_datos(datos["gold"]):
        if g["comuna"] and g["estrato"]:
            clave = (g["comuna"], grupo(int(float(g["estrato"]))))
            cuenta[clave] += 1
            severos[clave] += _b(g["severo_estricto"])
    for _, fila in tabla.iterrows():
        for g in ("1-2", "3-5", "6"):
            col = f"Estratos {g}: con datos"
            if col in tabla.columns:
                assert fila[col] == formato.numero(cuenta[(fila["Comuna"], g)]), (fila["Comuna"], g)
                assert fila[f"Estratos {g}: severos"] == formato.numero(severos[(fila["Comuna"], g)])
    assert "Comuna 20" in "\n".join(m.value for m in paginas[0]["comunas"].info)


# ---------- Sensibilidades ----------
def test_sensibilidades_coincide_con_kpis_sensibilidad(paginas, datos):
    tabla = paginas[0]["sensibilidades"].dataframe[0].value
    por = defaultdict(dict)
    for r in datos["sens"]:
        if r["kpi_id"] == "K2":
            por[r["escenario"]][r["grupo"]] = r
    assert tabla["Escenario"].tolist() == ["S0", "S1", "S2", "S3", "S4", "S5"]
    for _, fila in tabla.iterrows():
        e = por[fila["Escenario"]]
        d = e["diferencia_3-5_menos_1-2"]
        assert fila["Diferencia"] == formato.puntos_porcentuales(_f(d["tasa"]))
        assert fila["Intervalo de Newcombe"] == formato.intervalo(_f(d["ic95_inf"]), _f(d["ic95_sup"]), como="pp")
        assert fila["Tasa 3-5"] == formato.porcentaje(_f(e["estratos_3-5"]["tasa"])) and fila["Tasa 1-2"] == formato.porcentaje(_f(e["estratos_1-2"]["tasa"]))
        assert fila["Razón ajustada (MH)"] == formato.razon(_f(e["razon_MH_ajustada_comuna"]["tasa"]))
        assert fila["Filtro o definición"] == e["razon_3-5_vs_1-2"]["nota"]


# ---------- Concentración, calidad y fuentes ----------
def test_concentracion_coincide_con_k3_y_k4(paginas, datos):
    at = paginas[0]["concentracion"]
    m = _metricas(at)
    k3, k4 = _k(datos, "K3"), _k(datos, "K4")
    assert m["Severos en barrios líderes"].value == formato.porcentaje(_f(k3["valor"]), 1)
    assert m["Correlación"].value == formato.numero(_f(k4["valor"]), 3)
    assert m["Barrios incluidos"].value == formato.numero(_f(k4["denominador"]))
    tabla = at.dataframe[0].value
    barrios = [p.split(":") for p in k3["nota"].split("severos ")[1].split("; esos")[0].split("; ")]
    assert tabla["Código de barrio"].tolist() == [b[0] for b in barrios]
    assert tabla["Severos"].tolist() == [formato.numero(int(b[1])) for b in barrios]
    # recálculo: los severos por código de barrio desde gold_final.csv
    cuenta = Counter(g["codigo_barrio"] for g in datos["gold"] if _b(g["severo_estricto"]) and g["codigo_barrio"])
    for codigo, n in barrios:
        assert cuenta[codigo] == int(n)


def test_calidad_coincide_con_quality_report(paginas, datos):
    at = paginas[0]["calidad"]
    q = datos["calidad"]
    m = _metricas(at)
    assert m["Cobertura de la llave"].value == formato.porcentaje(q["cobertura_llave"]["pct"], 3)
    assert m["Estrato válido"].value == formato.porcentaje(q["cobertura_estrato_valido"]["pct"], 3)
    assert m["Nombre validado"].value == formato.porcentaje(q["pct_nombre_validado"]["global"]["pct"], 2)
    assert f"**Confianza de la llave:** {q['llave_confianza']}" in [x.value for x in at.markdown]


def test_fuentes_coincide_con_la_poblacion_de_gold_final(paginas, datos):
    m = _metricas(paginas[0]["fuentes"])
    gold = datos["gold"]
    assert m["Construcciones"].value == formato.numero(len(gold))
    assert m["Construcciones"].help == f"{formato.numero(len(_con_datos(gold)))} con datos satelitales"
    assert m["Comunas"].value == formato.numero(len({g["comuna"] for g in gold if g["comuna"]}))
    assert m["Códigos de barrio"].value == formato.numero(len({g["codigo_barrio"] for g in gold if g["codigo_barrio"]}))


def test_construcciones_pagina_y_filtros_coinciden_con_gold_final(paginas, datos):
    _, api = paginas
    at = pa.pagina("construcciones", api)
    gold = sorted(datos["gold"], key=lambda g: int(g["objectid"]))
    assert at.dataframe[0].value["Construcción"].tolist() == [int(g["objectid"]) for g in gold[:50]]
    at.selectbox(key="filtro_comuna").select("20").run()
    texto = [c.value for c in at.caption if "construcciones con estos filtros" in c.value][0]
    assert texto.startswith(formato.numero(sum(g["comuna"] == "20" for g in gold)) + " construcciones")
    at.selectbox(key="filtro_severo").select("Solo con cambio satelital severo").run()
    texto = [c.value for c in at.caption if "construcciones con estos filtros" in c.value][0]
    assert texto.startswith(formato.numero(sum(g["comuna"] == "20" and _b(g["severo_estricto"]) for g in gold)) + " construcciones")


def test_el_panel_no_modifica_data_al_consultar(paginas):
    antes = {p: p.stat().st_mtime_ns for p in GOLD.rglob("*") if p.is_file()}
    pa.pagina("respuesta", paginas[1])
    assert {p: p.stat().st_mtime_ns for p in GOLD.rglob("*") if p.is_file()} == antes
