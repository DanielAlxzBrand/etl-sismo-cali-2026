"""API de solo lectura: estructura, validación, coincidencia con las salidas y ausencia de escritura (sin red)."""
import hashlib
import json
import shutil
import sqlite3
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.api.app import crear_app
from src.api.repositorio import RepositorioSqlite
from src.common import ROOT

DB = ROOT / "data" / "gold" / "etl_sismo.db"
ENDPOINTS = ["/health", "/metadata", "/fuentes", "/kpis", "/kpis/K1", "/kpis/sensibilidad", "/comunas", "/composicion", "/construcciones", "/calidad", "/llave/revision"]
ST = {"comuna": str, "barrio": str, "codigo_barrio": str}


@pytest.fixture(scope="module")
def cliente():
    return TestClient(crear_app(), raise_server_exceptions=False)


def _nulo(v):
    return None if v is None or (isinstance(v, float) and v != v) else v


def _igual(esperado, real):
    """Compara filas de un CSV con la respuesta de la API: números con tolerancia 1e-9 y NaN como nulo."""
    for col, e in esperado.items():
        e, r = _nulo(e), _nulo(real[col])
        if isinstance(e, (int, float)) and not isinstance(e, bool) and r is not None:
            assert abs(float(e) - float(r)) < 1e-9, col
        elif isinstance(e, str) and r is not None and e in ("True", "False"):
            assert (e == "True") == bool(r), col
        else:
            assert e == r or (e in ("", None) and r in ("", None)), (col, e, r)


def _huellas():
    arch = [p for p in (ROOT / "data").rglob("*") if p.is_file()]
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(arch)}


def test_cada_endpoint_responde_200_con_la_estructura_esperada(cliente):
    for ruta in ENDPOINTS:
        r = cliente.get(ruta)
        assert r.status_code == 200, ruta
    h = cliente.get("/health").json()
    assert h["estado"] == "ok" and h["base_disponible"] is True and h["filas_por_tabla"]["gold_final"] == 5146
    m = cliente.get("/metadata").json()
    assert m["poblacion"]["construcciones"] == 5146 and m["poblacion"]["comunas"] == 7 and "no evaluación estructural" in m["aviso"]
    assert {"fecha_imagen_pre", "fecha_imagen_post", "fecha_edicion_capa", "alcance_temporal", "licencias", "fuentes"} <= m.keys()
    assert set(cliente.get("/construcciones").json()) == {"total", "limit", "offset", "items"}


def test_parametros_invalidos_dan_422_con_el_json_uniforme(cliente):
    for ruta in ["/construcciones?limit=0", "/construcciones?limit=abc", "/construcciones?estrato=9", "/construcciones?comuna=ab", "/kpis?kpi_id=XX", "/kpis/sensibilidad?escenario=S9",
                 "/construcciones?severo_estricto=quizas"]:
        r = cliente.get(ruta)
        assert r.status_code == 422, ruta
        e = r.json()["error"]
        assert set(e) == {"codigo", "mensaje", "detalle"} and e["codigo"] == "parametros_invalidos"


def test_ids_inexistentes_dan_404_y_rutas_desconocidas_tambien(cliente):
    for ruta in ["/kpis/K99", "/no_existe"]:
        r = cliente.get(ruta)
        assert r.status_code == 404 and r.json()["error"]["codigo"] == "no_encontrado"


def test_limites_de_paginacion_y_offset(cliente):
    assert cliente.get("/construcciones").json()["limit"] == 50
    assert cliente.get("/construcciones?limit=200").status_code == 200
    assert cliente.get("/construcciones?limit=201").status_code == 422
    assert cliente.get("/construcciones?offset=-1").status_code == 422
    lejos = cliente.get("/construcciones?offset=100000").json()
    assert lejos["items"] == [] and lejos["total"] == 5146


def test_paginas_ordenadas_y_sin_solaparse(cliente):
    a = cliente.get("/construcciones?limit=100&offset=0").json()["items"]
    b = cliente.get("/construcciones?limit=100&offset=100").json()["items"]
    ids = [x["objectid"] for x in a + b]
    assert ids == sorted(ids) and len(set(ids)) == 200


def test_la_inyeccion_en_comuna_y_estrato_se_rechaza(cliente):
    base = cliente.get("/construcciones").json()["total"]
    for valor in ["19' OR '1'='1", "19; DROP TABLE gold_final;--", "1 OR 1=1"]:
        assert cliente.get("/construcciones", params={"comuna": valor}).status_code == 422
        assert cliente.get("/construcciones", params={"estrato": valor}).status_code == 422
    assert cliente.get("/kpis", params={"grupo": "x' OR '1'='1"}).json() == []  # el filtro libre es un parámetro, no texto SQL
    assert cliente.get("/construcciones").json()["total"] == base
    assert cliente.get("/health").json()["filas_por_tabla"]["gold_final"] == 5146


def test_kpis_y_sensibilidad_son_iguales_a_los_csv(cliente):
    for ruta, archivo in [("/kpis", "kpis_gold.csv"), ("/kpis/sensibilidad", "kpis_sensibilidad.csv")]:
        df = pd.read_csv(ROOT / "data" / "gold" / archivo)
        r = cliente.get(ruta).json()
        assert len(r) == len(df)
        for esperado, real in zip(df.to_dict("records"), r):
            _igual(esperado, real)
    assert len(cliente.get("/kpis/K6").json()) == 7
    assert {x["escenario"] for x in cliente.get("/kpis/sensibilidad?escenario=S3").json()} == {"S3"}


def test_orden_de_rutas_sensibilidad_antes_que_kpi_id(cliente):
    rutas = [r.path for r in cliente.app.routes]
    assert rutas.index("/kpis/sensibilidad") < rutas.index("/kpis/{kpi_id}")
    assert cliente.get("/kpis/sensibilidad").json()[0]["escenario"] == "S0"


def test_comunas_es_k6_tal_como_esta(cliente):
    df = pd.read_csv(ROOT / "data" / "gold" / "kpis_gold.csv")
    k6 = df[df.kpi_id == "K6"].reset_index(drop=True)
    r = cliente.get("/comunas").json()
    assert [x["comuna"] for x in r] == [g.removeprefix("comuna_") for g in k6.grupo]
    for fila, real in zip(k6.to_dict("records"), r):
        assert abs(fila["valor"] - real["tasa"]) < 1e-9 and fila["numerador"] == real["severos"] and fila["denominador"] == real["n_con_datos"]


def test_composicion_y_total_de_construcciones_coinciden_con_pandas(cliente):
    g = pd.read_csv(ROOT / "data" / "gold" / "gold_final.csv", dtype=ST)
    assert cliente.get("/construcciones").json()["total"] == len(g)
    sub = g[(g.sin_datos == False) & g.comuna.notna() & g.estrato.notna()].copy()  # noqa: E712
    sub["grupo_estrato"] = sub.estrato.map(lambda e: "1-2" if e in (1, 2) else "3-5" if e in (3, 4, 5) else "6")
    sub["sev"] = sub.severo_estricto.astype(str).eq("True")
    esperado = sub.groupby(["comuna", "grupo_estrato"]).agg(n=("sev", "size"), s=("sev", "sum")).reset_index()
    real = {(x["comuna"], x["grupo_estrato"]): (x["n_con_datos"], x["severos"]) for x in cliente.get("/composicion").json()}
    assert real == {(f.comuna, f.grupo_estrato): (f.n, int(f.s)) for f in esperado.itertuples()}
    sev = cliente.get("/construcciones", params={"severo_estricto": True, "limit": 1}).json()["total"]
    assert sev == int(g.severo_estricto.astype(str).eq("True").sum())
    assert cliente.get("/construcciones", params={"comuna": "19", "estrato": 5}).json()["total"] == len(g[(g.comuna == "19") & (g.estrato == 5)])


def test_calidad_es_igual_a_quality_report(cliente):
    q = json.loads((ROOT / "data" / "silver" / "quality_report.json").read_text(encoding="utf-8"))
    r = cliente.get("/calidad").json()
    for k in ("cobertura_llave", "cobertura_estrato_valido", "pct_nombre_validado", "llave_confianza"):
        assert r[k] == q[k]


def test_revision_de_llave_coincide_con_silver(cliente):
    s = pd.read_csv(ROOT / "data" / "silver" / "silver_integrated.csv", dtype=ST)
    mal = s[s.nombre_validado.astype(str).eq("False")]
    r = cliente.get("/llave/revision").json()
    assert r["total_codigos"] == mal.codigo_barrio.nunique() and sum(x["n_construcciones"] for x in r["items"]) == len(mal)
    assert r["documento"] == "docs/revision_codigos_barrio.md"


def test_solo_existen_rutas_get_y_los_demas_metodos_dan_405(cliente):
    for ruta in cliente.app.routes:
        metodos = getattr(ruta, "methods", None)
        if metodos is not None and ruta.path not in ("/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"):
            assert metodos <= {"GET", "HEAD"}, ruta.path
    for ruta in ["/kpis", "/construcciones", "/health"]:
        for metodo in ("post", "put", "delete", "patch"):
            r = getattr(cliente, metodo)(ruta)
            assert r.status_code == 405 and r.json()["error"]["codigo"] == "metodo_no_permitido"


def test_la_conexion_es_de_solo_lectura(tmp_path):
    copia = tmp_path / "copia.db"
    shutil.copy(DB, copia)
    repo = RepositorioSqlite(copia)
    try:
        with pytest.raises(sqlite3.OperationalError):
            repo._conn.execute("INSERT INTO kpis_gold (kpi_id) VALUES ('K9')")
        with pytest.raises(sqlite3.OperationalError):
            repo._conn.execute("DELETE FROM gold_final")
    finally:
        repo.cerrar()
    assert repo._conn is None


def test_base_ausente_da_503_y_health_degradado(tmp_path):
    c = TestClient(crear_app(tmp_path / "no_existe.db"), raise_server_exceptions=False)
    assert c.get("/kpis").status_code == 503 and c.get("/kpis").json()["error"]["codigo"] == "base_no_disponible"
    h = c.get("/health").json()
    assert h["estado"] == "degradado" and h["base_disponible"] is False


def test_un_error_interno_da_500_sin_trazas_ni_rutas(monkeypatch):
    def falla(self, *a, **k):
        raise RuntimeError("fallo con ruta " + str(ROOT))
    monkeypatch.setattr(RepositorioSqlite, "kpis", falla)
    r = TestClient(crear_app(), raise_server_exceptions=False).get("/kpis")
    assert r.status_code == 500 and r.json()["error"]["codigo"] == "error_interno"
    assert "Traceback" not in r.text and str(ROOT) not in r.text and "RuntimeError" not in r.text


def test_consultar_todos_los_endpoints_no_escribe_en_data_ni_en_la_base(cliente):
    antes = _huellas()
    for ruta in ENDPOINTS + ["/kpis/K6", "/construcciones?limit=200&offset=200", "/kpis/sensibilidad?escenario=S2", "/openapi.json", "/docs"]:
        assert cliente.get(ruta).status_code == 200, ruta
    assert _huellas() == antes
    assert "gold/etl_sismo.db" in "".join(antes) and Path(DB).is_file()
