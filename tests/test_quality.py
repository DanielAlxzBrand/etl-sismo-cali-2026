"""Pruebas de calidad: cobertura del JOIN, Gold y KPI en rango (sin red)."""
import json

import pandas as pd

from src.common import ROOT, load_config

CAMPOS_REPORTE = ["fuentes", "duplicados_eliminados_por_regla", "nulos_antes_bronze", "nulos_despues_construcciones", "tratamiento",
                  "cobertura_llave", "cobertura_estrato_valido", "umbral_cobertura_join", "resultado_umbral", "huerfanos",
                  "sin_estrato_valido", "sin_datos", "severos", "pct_coincide_poligono", "pct_nombre_validado", "llave_confianza",
                  "reglas_aplicadas"]


def _reporte():
    return json.loads((ROOT / "data/silver/quality_report.json").read_text(encoding="utf-8"))


def test_reporte_con_todos_los_campos():
    r = _reporte()
    assert [c for c in CAMPOS_REPORTE if c not in r] == []
    assert len(r["huerfanos"]["izquierda_detalle"]) == r["huerfanos"]["izquierda"] == 6


def test_cobertura_join_supera_umbral():
    r, cfg = _reporte(), load_config()
    assert r["cobertura_llave"]["pct"] >= cfg["thresholds"]["join_coverage_min"]
    assert r["resultado_umbral"] == "pasa"


def test_gold_minimo_de_filas_y_sin_duplicados():
    g = pd.read_csv(ROOT / "data/gold/gold_final.csv")
    assert len(g) >= load_config()["thresholds"]["gold_min_rows"]
    assert g.objectid.is_unique


def test_kpis_presentes_y_en_rango():
    k = pd.read_csv(ROOT / "data/gold/kpis_gold.csv")
    assert sorted(k.kpi_id.unique()) == ["K1", "K2", "K3", "K4", "K5", "K6"]
    tasas = k[~k.grupo.str.startswith(("razon", "diferencia")) & (k.kpi_id != "K4")]
    assert tasas.valor.between(0, 1).all()
    assert -1 <= k[k.kpi_id == "K4"].valor.iloc[0] <= 1
    assert (k.fecha_corte == load_config()["fechas"]["fecha_edicion_capa"]).all()
