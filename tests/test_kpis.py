"""Regresion numerica de los KPI: todo se recalcula desde gold_final.csv (sin red, sin cifras de datos escritas a mano)."""
import json

import pandas as pd

from src.common import ROOT
from src.transform.build_gold import mantel_haenszel, newcombe, wilson

GOLD = pd.read_csv(ROOT / "data/gold/gold_final.csv", dtype={"comuna": str, "codigo_barrio": str})
KP = pd.read_csv(ROOT / "data/gold/kpis_gold.csv")
CON = GOLD[~GOLD.sin_datos.astype(bool)]


def test_wilson_vectores():
    lo, hi = wilson(5, 10)
    assert round(lo, 4) == 0.2366 and round(hi, 4) == 0.7634
    lo, hi = wilson(0, 10)
    assert round(lo, 4) == 0.0 and round(hi, 4) == 0.2775


def test_newcombe_vector():
    d, lo, hi = newcombe(272, 4299, 23, 394)
    assert abs(d - 0.0049) < 2e-4 and abs(lo - (-0.0236)) < 2e-4 and abs(hi - 0.0255) < 2e-4


def _df(filas):
    return pd.DataFrame(filas, columns=["comuna", "estrato", "sin_datos", "sev"]).astype({"sin_datos": bool, "sev": "boolean"})


def _comuna18(extra_sin_datos=0):
    f = [("18", 4, False, i < 5) for i in range(44)] + [("18", 1, False, i < 3) for i in range(52)]
    f += [("18", 4, True, None)] * extra_sin_datos + [("18", 1, True, None)] * extra_sin_datos
    return _df(f)


def test_mantel_haenszel_una_comuna():
    rr, usadas, _, _ = mantel_haenszel(_comuna18(), "sev")
    assert usadas == ["18"] and round(rr, 4) == round(260 / 132, 4) == 1.9697


def test_regresion_defecto_mh_sin_datos_no_entra_en_mh():
    """El defecto detectado en el recálculo independiente contaba construcciones 'sin datos' en n1, n0 y N; agregarlas no debe cambiar RR_MH."""
    base = mantel_haenszel(_comuna18(), "sev")[0]
    con_extra = mantel_haenszel(_comuna18(extra_sin_datos=30), "sev")[0]
    assert con_extra == base


def test_consistencia_k1_k6_k5_y_rangos():
    sev = CON[CON.estrato.notna()]
    k1 = KP[KP.kpi_id == "K1"]
    assert int(k1.numerador.sum()) == int(sev.severo_estricto.sum())
    assert int(k1.denominador.sum()) == len(sev)
    k6 = KP[KP.kpi_id == "K6"]
    cc = CON[CON.comuna.notna()]
    assert int(k6.numerador.sum()) == int(cc.severo_estricto.sum()) and int(k6.denominador.sum()) == len(cc)
    rep = json.loads((ROOT / "data/silver/quality_report.json").read_text(encoding="utf-8"))
    k5 = KP[KP.kpi_id == "K5"].set_index("grupo").valor
    assert abs(k5["cobertura_llave"] - rep["cobertura_llave"]["pct"]) < 1e-6
    assert abs(k5["cobertura_estrato_valido"] - rep["cobertura_estrato_valido"]["pct"]) < 1e-6
    assert abs(k5["pct_nombre_validado"] - rep["pct_nombre_validado"]["global"]["pct"]) < 1e-6
    tasas = KP[KP.ic95_inf.notna() & ~KP.grupo.str.startswith("diferencia")]
    assert ((tasas.ic95_inf >= 0) & (tasas.ic95_inf <= tasas.valor) & (tasas.valor <= tasas.ic95_sup) & (tasas.ic95_sup <= 1)).all()
    cot = KP[KP.cota_inf.notna()]
    assert ((cot.cota_inf <= cot.valor + 1e-12) & (cot.valor <= cot.cota_sup + 1e-12)).all()


def test_k1_recalculado_desde_gold():
    for s in range(1, 7):
        g = CON[CON.estrato == s]
        fila = KP[KP.grupo == f"estrato_{s}"].iloc[0]
        assert int(fila.numerador) == int(g.severo_estricto.sum()) and int(fila.denominador) == len(g)
        assert abs(fila.valor - g.severo_estricto.sum() / len(g)) < 1e-9
