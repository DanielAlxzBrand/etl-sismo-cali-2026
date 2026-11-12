"""Documentos de la sección 1 del checklist (docs/entrega_3/seccion_1): existencia, términos prohibidos, cifras y avisos de honestidad."""
import json
import re
from decimal import ROUND_HALF_UP, Decimal

import pandas as pd

from src.common import ROOT

CARPETA = ROOT / "docs" / "entrega_3" / "seccion_1"
ARCHIVOS = ["indice.md", "01_data_thinking.md", "02_stakeholders.md", "03_objetivo_alcance_okr_kpi.md",
            "04_canvas_data_innovation_board.md", "05_mvp_criterios_aceptacion.md"]
PROHIBIDOS = [r"Claude", r"Anthropic", r"ChatGPT", r"Copilot", r"Gemini", r"OpenAI", r"prompt", r"inteligencia artificial", r"\bIA\b", r"TODO",
              r"\[COMPLETAR"]


def _texto(nombre):
    return (CARPETA / nombre).read_text(encoding="utf-8")


def _miles(n):
    return f"{int(n):,}".replace(",", ".")


def _pc(v, d=3):
    q = (Decimal(repr(float(v))) * 100).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP)
    return str(q).replace(".", ",") + " %"


def test_existen_los_seis_archivos():
    assert [n for n in ARCHIVOS if not (CARPETA / n).is_file()] == []


def test_sin_cadenas_prohibidas():
    for n in ARCHIVOS:
        t = _texto(n)
        for p in PROHIBIDOS:
            assert not re.search(p, t), (n, p)


def test_cifras_clave_de_e3_y_e5_coinciden_con_las_salidas():
    rep = json.loads((ROOT / "data/silver/quality_report.json").read_text(encoding="utf-8"))
    gold = pd.read_csv(ROOT / "data/gold/gold_final.csv")
    kpis = pd.read_csv(ROOT / "data/gold/kpis_gold.csv")
    cobertura = _pc(rep["cobertura_llave"]["pct"])
    filas, n_kpis = _miles(len(gold)), len(kpis)
    for n in ("03_objetivo_alcance_okr_kpi.md", "05_mvp_criterios_aceptacion.md"):
        t = _texto(n)
        assert cobertura in t and f"{filas} filas" in t and f"{n_kpis} filas" in t, n
    assert f"{n_kpis} filas con 6 indicadores" in _texto("03_objetivo_alcance_okr_kpi.md")
    assert sorted(kpis.kpi_id.unique()) == ["K1", "K2", "K3", "K4", "K5", "K6"]


def test_e4_declara_hipotesis_sin_validar_y_no_estimado():
    t = _texto("04_canvas_data_innovation_board.md")
    assert "hipótesis sin validar" in t and "no estimado" in t
    assert "Qué no afirmamos" in t


def test_enlaces_entre_documentos_existen_y_no_se_afirman_contactos():
    for n in ARCHIVOS:
        t = _texto(n)
        for destino in re.findall(r"\]\(([^)#]+\.md)\)", t):
            assert (CARPETA / destino).is_file(), (n, destino)
    t2 = _texto("02_stakeholders.md")
    assert "No hubo contacto ni validación con stakeholders" in t2
