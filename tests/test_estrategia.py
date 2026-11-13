"""Sección 1 del checklist (docs/estrategia): existencia, rastros de elaboración, cifras, rúbrica R1 y avisos de honestidad."""
import json
import re
from decimal import ROUND_HALF_UP, Decimal

import pandas as pd

from src.common import ROOT

E3 = ROOT / "docs"
CARPETA = E3 / "estrategia"
DOCS = ["01_data_thinking.md", "02_stakeholders.md", "03_objetivo_alcance_okr_kpi.md", "04_canvas_data_innovation_board.md", "05_mvp_criterios_aceptacion.md"]
ARCHIVOS = ["indice.md"] + DOCS
IMAGENES = [CARPETA / "img" / "matriz_poder_interes.png", CARPETA / "img" / "canvas_modelo_negocio.png"]
# Rastros de elaboración (las cadenas se parten para que este archivo no se detecte a sí mismo). La sigla de IA como concepto técnico está permitida.
RASTROS = ["Cla" + "ude", "Anthro" + "pic", "Chat" + "GPT", "Co" + "pilot", "Gem" + "ini", "Open" + "AI", "pro" + "mpt",
           "con ayuda de " + "IA", "asistente de " + "IA", "generado con " + "IA", "herramienta de " + "IA", "elaborado con " + "IA"]
OTROS = ["por validar por el " + "equipo", "[COMPLE" + "TAR", "TO" + "DO"]
SUFIJOS = (".md", ".py", ".txt", ".yaml", ".yml", ".ini", ".ipynb", ".csv", ".json", ".jsonl")


def _texto(nombre):
    return (CARPETA / nombre).read_text(encoding="utf-8")


def _miles(n):
    return f"{int(n):,}".replace(",", ".")


def _pc(v, d=3):
    q = (Decimal(repr(float(v))) * 100).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP)
    return str(q).replace(".", ",") + " %"


def test_existen_los_documentos_el_indice_y_las_dos_imagenes():
    assert [n for n in ARCHIVOS if not (CARPETA / n).is_file()] == []
    assert [str(p) for p in IMAGENES if not p.is_file() or p.stat().st_size < 10_000] == []


def test_cada_documento_tiene_el_bloque_de_defensa():
    for n in DOCS:
        t = _texto(n)
        bloque = t.split("## Cómo lo defendemos")[1]
        for campo in ("Qué afirmamos", "Con qué evidencia", "Qué NO afirmamos", "La pregunta más probable del profesor", "Cómo respondemos"):
            assert f"**{campo}:**" in bloque, (n, campo)


def test_sin_rastros_de_elaboracion_ni_marcas_pendientes_en_la_seccion_1():
    for n in ARCHIVOS:
        t = _texto(n)
        for p in RASTROS + OTROS:
            assert p not in t, (n, p)


def test_sin_rastros_de_elaboracion_en_el_resto_del_repo():
    """Recorre los archivos de texto versionables (sin .venv, .git, data/, dist/ ni la declaración de uso, que es del equipo)."""
    saltar = {".venv", ".git", "data", "dist", "logs", "__pycache__", ".pytest_cache", ".ipynb_checkpoints"}
    hallazgos = []
    for p in ROOT.rglob("*"):
        rel = p.relative_to(ROOT)
        if not p.is_file() or rel.parts[0] in saltar or any(x in saltar for x in rel.parts) or p.suffix not in SUFIJOS or p.name == "DECLARACION_USO_IA.md":
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")
        hallazgos += [(rel.as_posix(), x) for x in RASTROS if x in t]
    assert hallazgos == []


def test_cifras_de_1_3_y_1_5_coinciden_con_las_salidas():
    rep = json.loads((ROOT / "data/silver/quality_report.json").read_text(encoding="utf-8"))
    gold = pd.read_csv(ROOT / "data/gold/gold_final.csv")
    kpis = pd.read_csv(ROOT / "data/gold/kpis_gold.csv")
    cobertura, filas, n_kpis = _pc(rep["cobertura_llave"]["pct"]), _miles(len(gold)), len(kpis)
    for n in ("03_objetivo_alcance_okr_kpi.md", "05_mvp_criterios_aceptacion.md"):
        t = _texto(n)
        assert cobertura in t and f"{filas} filas" in t, n
    assert f"{n_kpis} filas con 6 indicadores" in _texto("03_objetivo_alcance_okr_kpi.md")
    assert sorted(kpis.kpi_id.unique()) == ["K1", "K2", "K3", "K4", "K5", "K6"]
    con = gold[~gold.sin_datos]
    assert f"{_miles(len(con))}" in _texto("01_data_thinking.md") and f"{_miles(len(gold))} construcciones" in _texto("03_objetivo_alcance_okr_kpi.md")


def test_rubrica_r1_y_matriz_poder_interes_son_consistentes():
    t = _texto("02_stakeholders.md")
    assert "Rúbrica R1" in t or "rúbrica R1" in t
    umbral = int(re.search(r"mayor o igual que (\d+)", t).group(1))
    filas = re.findall(r"^\| (\d+) \| ([^|]+) \| ([0-3]) \| ([0-3]) \| ([0-3]) \| ([0-3]) \| (\d) \| (\d) \| ([^|]+) \|$", t, re.M)
    assert len(filas) >= 10
    for _, nombre, c1, c2, c3, c4, poder, interes, cuadrante in filas:
        p, i = int(c1) + int(c2), int(c3) + int(c4)
        assert (int(poder), int(interes)) == (p, i), nombre
        esperado = ("Gestionar de cerca" if p >= umbral and i >= umbral else "Mantener satisfechos" if p >= umbral
                    else "Mantener informados" if i >= umbral else "Monitorear")
        assert cuadrante.strip() == esperado, nombre


def test_1_4_declara_hipotesis_sin_validar_y_no_estimado():
    t = _texto("04_canvas_data_innovation_board.md")
    assert "hipótesis sin validar" in t and "no estimado" in t and "Qué no afirmamos" in t
    assert len(re.findall(r"^\| H\d+ \|", t, re.M)) >= 8


def test_1_2_declara_que_no_hubo_contactos():
    t = _texto("02_stakeholders.md")
    assert "## 6. Contactos realizados" in t and "**Ninguno:**" in t
    assert "No hubo contacto ni validación con stakeholders" in t


def test_1_5_tiene_al_menos_24_criterios_y_no_marca_cumple_sin_verificar():
    t = _texto("05_mvp_criterios_aceptacion.md")
    filas = re.findall(r"^\| (AC\d+) \|.*\| \*\*([^*]+)\*\* \| (F\d) \| ([^|]+) \|$", t, re.M)
    assert len(filas) >= 24
    for _id, estado, fase, fecha in filas:
        if estado.startswith("no verificado"):
            assert fase in ("API, fuentes y credenciales", "Carga relacional", "Pruebas y orquestación", "Panel") and fecha.strip() == "—", _id
        else:
            assert estado in ("cumple", "no cumple") and fecha.strip() != "—", _id
