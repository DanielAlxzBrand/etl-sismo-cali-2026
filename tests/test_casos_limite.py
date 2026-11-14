"""Casos límite explícitos: un solo registro, entrada vacía y extremos de paginación, sin tocar el código de src ni los datos."""
import csv
import json
import math
import shutil

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.api.app import crear_app
from src.common import ROOT
from src.extract.extract_excel import latest_csv, read_csv_raw
from src.load import conciliacion, conexion, relacional
from src.transform.build_gold import calcular, mantel_haenszel, newcombe, wilson
from src.transform.clean_excel import limpiar_estrato
from src.transform.keys import codigo_barrio, normalize_key


# ---------------------------------------------------------------- estadística con un solo registro
@pytest.mark.parametrize("k", [0, 1])
def test_wilson_con_un_solo_registro_da_un_intervalo_valido(k):
    lo, hi = wilson(k, 1)
    assert 0.0 <= lo <= k <= hi <= 1.0 and lo < hi


def test_wilson_sin_registros_da_nan_en_lugar_de_dividir_por_cero():
    lo, hi = wilson(0, 0)
    assert math.isnan(lo) and math.isnan(hi)


def test_newcombe_con_un_registro_por_grupo_incluye_la_diferencia_observada():
    d, lo, hi = newcombe(1, 1, 0, 1)
    assert d == 1.0 and -1.0 <= lo <= d <= hi <= 1.0


def _uno(sev=True, estrato=3.0, comuna="18"):
    return pd.DataFrame({"comuna": [comuna], "estrato": [estrato], "sin_datos": [False],
                         "severo_estricto": pd.array([sev], dtype="boolean"), "dano_visible": pd.array([sev], dtype="boolean")})


def test_mantel_haenszel_con_un_registro_no_inventa_una_razon():
    rr, usadas, excluidas, tot = mantel_haenszel(_uno(), "severo_estricto")
    assert math.isnan(rr) and usadas == [] and excluidas == ["18"] and tot == {"a": 0, "c": 0, "n1": 0, "n0": 0}


def test_los_indicadores_con_un_solo_registro_se_calculan_y_los_grupos_vacios_quedan_en_cero():
    filas = calcular(_uno(), "severo_estricto", 30)
    k1 = {f["grupo"]: f for f in filas if f["kpi_id"] == "K1"}
    assert (k1["estrato_3"]["numerador"], k1["estrato_3"]["denominador"]) == (1, 1) and k1["estrato_3"]["muestra_baja"] is True
    assert all(k1[f"estrato_{e}"]["denominador"] == 0 and math.isnan(k1[f"estrato_{e}"]["valor"]) for e in (1, 2, 4, 5, 6))
    razon = next(f for f in filas if f["grupo"] == "razon_3-5_vs_1-2")
    assert math.isnan(razon["valor"]) and "vacío" in razon["nota"]


def test_la_limpieza_del_estrato_acepta_una_sola_fila_real():
    crudo, codificacion = read_csv_raw(latest_csv())
    barrios, resumen, _ = limpiar_estrato(crudo.head(1), [])
    assert codificacion == "utf-8" and len(barrios) == 1 and barrios.codigo_barrio.is_unique


def test_las_llaves_aceptan_entradas_minimas():
    assert normalize_key("") == "" and normalize_key("A") == "A"
    assert codigo_barrio("1", "1") == "101"


# ---------------------------------------------------------------- carga con una sola fila y con entrada vacía
ENTRADAS = {"barrio": "data/silver/silver_estrato_barrio.csv", "gold": "data/gold/gold_final.csv", "kpi": "data/gold/kpis_gold.csv", "sens": "data/gold/kpis_sensibilidad.csv"}


def _recortar(origen, destino, elegir=None, solo_cabecera=False):
    with open(ROOT / origen, encoding="utf-8", newline="") as f:
        lector = csv.DictReader(f)
        filas = [] if solo_cabecera else [next(r for r in lector if elegir is None or elegir(r))]
        campos = lector.fieldnames
    destino.parent.mkdir(parents=True, exist_ok=True)
    with open(destino, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos, lineterminator="\n")
        w.writeheader()
        w.writerows(filas)


def _carpeta_minima(tmp, vacia=None):
    for clave, ruta in ENTRADAS.items():
        elegir = (lambda r: r["cruza_llave"] == "False") if clave == "gold" else None
        _recortar(ruta, tmp / ruta, elegir, solo_cabecera=(clave == vacia))
    shutil.copy2(ROOT / "data/silver/quality_report.json", tmp / "data/silver/quality_report.json")
    return tmp


def test_la_carga_con_una_sola_fila_por_tabla_concilia_al_cien_por_ciento(tmp_path):
    raiz = _carpeta_minima(tmp_path)
    conn = conexion.conectar_sqlite()
    r = relacional.cargar(conn, "sqlite", raiz=raiz)
    assert r["estado"] == "cargada" and r["filas"] == {"barrio_estrato": 1, "construccion": 1, "kpi": 1, "kpi_sensibilidad": 1}
    assert conciliacion.conciliar(conn, "sqlite", r["corrida_id"], raiz=raiz)["ok"] is True
    assert all(v == 0 for v in conciliacion.estado_de_integridad(conn, "sqlite").values())
    assert relacional.cargar(conn, "sqlite", raiz=raiz)["estado"] == "ya_cargada"
    conn.close()


@pytest.mark.parametrize("vacia", ["barrio", "gold", "kpi", "sens"])
def test_una_entrada_vacia_se_rechaza_sin_crear_nada_en_la_base(tmp_path, vacia):
    raiz = _carpeta_minima(tmp_path, vacia=vacia)
    conn = conexion.conectar_sqlite()
    with pytest.raises(Exception):   # el cargador falla al preparar los datos: ni siquiera se crea el esquema
        relacional.cargar(conn, "sqlite", raiz=raiz)
    assert conn.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()[0] == 0
    conn.close()


def test_un_archivo_de_entrada_ausente_se_rechaza_sin_tocar_la_base(tmp_path):
    raiz = _carpeta_minima(tmp_path)
    (raiz / ENTRADAS["kpi"]).unlink()
    conn = conexion.conectar_sqlite()
    with pytest.raises(FileNotFoundError):
        relacional.cargar(conn, "sqlite", raiz=raiz)
    assert conn.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()[0] == 0
    conn.close()


def test_el_reporte_de_calidad_de_la_carga_minima_conserva_las_coberturas(tmp_path):
    raiz = _carpeta_minima(tmp_path)
    conn = conexion.conectar_sqlite()
    r = relacional.cargar(conn, "sqlite", raiz=raiz)
    cobertura = conn.execute("SELECT cobertura_llave FROM corrida WHERE id = ?", (r["corrida_id"],)).fetchone()[0]
    esperado = json.loads((ROOT / "data/silver/quality_report.json").read_text(encoding="utf-8"))["cobertura_llave"]["pct"]
    assert abs(float(cobertura) - esperado) < 1e-6
    conn.close()


# ---------------------------------------------------------------- paginación en los extremos
@pytest.fixture(scope="module")
def cliente():
    return TestClient(crear_app(), raise_server_exceptions=False)


def test_la_pagina_de_un_solo_registro_y_la_pagina_final(cliente):
    total = cliente.get("/construcciones?limit=1").json()["total"]
    una = cliente.get("/construcciones?limit=1").json()
    assert len(una["items"]) == 1 and una["total"] == total == 5146
    ultima = cliente.get(f"/construcciones?limit=50&offset={total - 1}").json()
    assert len(ultima["items"]) == 1


def test_una_pagina_mas_alla_del_final_vuelve_vacia_con_el_mismo_total(cliente):
    r = cliente.get("/construcciones?limit=50&offset=5146")
    assert r.status_code == 200 and r.json()["items"] == [] and r.json()["total"] == 5146


def test_un_filtro_sin_coincidencias_da_pagina_vacia_y_total_cero(cliente):
    r = cliente.get("/construcciones?comuna=99")
    assert r.status_code == 200 and r.json()["items"] == [] and r.json()["total"] == 0


def test_los_extremos_de_los_parametros_se_aceptan_y_lo_siguiente_se_rechaza(cliente):
    assert cliente.get("/construcciones?limit=1").status_code == 200 and cliente.get("/construcciones?limit=200").status_code == 200
    assert cliente.get("/construcciones?limit=201").status_code == 422 and cliente.get("/construcciones?limit=0").status_code == 422
    assert cliente.get("/construcciones?estrato=1").status_code == 200 and cliente.get("/construcciones?estrato=6").status_code == 200
    assert cliente.get("/construcciones?estrato=7").status_code == 422 and cliente.get("/construcciones?offset=-1").status_code == 422
