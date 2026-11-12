"""El README debe contener las cifras de los archivos de salida, tal como salen de ellos (con coma decimal)."""
import json
import os
import re
import subprocess
import sys
from collections import Counter
from decimal import ROUND_HALF_UP, Decimal

import pandas as pd

from src.common import ROOT

README = (ROOT / "README.md").read_text(encoding="utf-8").replace("−", "-")
KP = pd.read_csv(ROOT / "data/gold/kpis_gold.csv")
GOLD = pd.read_csv(ROOT / "data/gold/gold_final.csv", dtype={"comuna": str})
REP = json.loads((ROOT / "data/silver/quality_report.json").read_text(encoding="utf-8"))


def _redondeo(v, d, signo=False):
    """Redondeo half-up sobre el valor decimal tal como está escrito en los archivos (igual criterio que el generador del README)."""
    q = (Decimal(repr(float(v))) * 100).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP)
    return (f"{q:+}" if signo else f"{q}").replace(".", ",")


def _pc(v):
    return _redondeo(v, 3) + " %"


def _pp(v):
    return _redondeo(v, 2, signo=True)


def _miles(n):
    return f"{int(n):,}".replace(",", ".")


def test_k5_en_readme():
    k5 = KP[KP.kpi_id == "K5"].set_index("grupo").valor
    for g in ("cobertura_llave", "cobertura_estrato_valido", "pct_nombre_validado"):
        assert _pc(k5[g]) in README, g


def test_k2_diferencia_y_newcombe_en_readme():
    d = KP[KP.grupo == "diferencia_3-5_menos_1-2"].iloc[0]
    for v in (d.valor, d.ic95_inf, d.ic95_sup):
        assert _pp(v) in README
    assert f"entre {_pp(d.ic95_inf)} y {_pp(d.ic95_sup)} puntos porcentuales" in README


def test_estructura_de_respuesta_y_licencias():
    for frase in ("(a) Con este proxy y esta muestra no se detecta diferencia", "(b) Los datos son compatibles con diferencias entre",
                  "(c) Esto no equivale a decir que el estrato no influye", "(d) El signo de la diferencia no es estable",
                  "(e) Las tasas por comuna oscilan", "(f) La Comuna 19 concentra", "KR1", "KR5", "CC BY 4.0",
                  "licencia no declarada en el servicio", "Creative Commons Attribution Share-Alike", "CC0"):
        assert frase in README, frase


def test_cifras_de_gold_bronze_y_silver_en_readme():
    assert f"**{_miles(len(GOLD))} filas**" in README
    paginas = [json.loads(x) for x in (ROOT / "data/bronze/manifest.jsonl").read_text(encoding="utf-8").splitlines()
               if '"source_id": "edificaciones"' in x]
    assert ", ".join(_miles(p["rows"]) for p in paginas) in README
    con = GOLD[~GOLD.sin_datos & GOLD.comuna.notna()]
    sin_estrato = int(con.estrato.isna().sum())
    assert f"Nota: {sin_estrato} construcciones con datos satelitales no tienen estrato válido" in README
    assert f"({_miles(con.estrato.notna().sum())}) es menor que el total con datos y comuna asignada ({_miles(len(con))})" in README
    assert _pc(REP["cobertura_llave"]["pct"]) in README
    assert f"{REP['duplicados_marcados']['geom_duplicada_filas']} construcciones con geometría idéntica" in README


def _recolectadas():
    """Pruebas por archivo según `pytest --collect-only` (funciones y métodos de clase)."""
    r = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"], cwd=ROOT, capture_output=True,
                       text=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    return Counter(l.split("::")[0].split("/")[-1] for l in r.stdout.splitlines() if "::" in l)


def test_numero_de_pruebas_en_readme():
    por_archivo = _recolectadas()
    n = sum(por_archivo.values())
    assert n > 0 and f"Hay **{n} pruebas**" in README and f"`pytest -q` → `{n} passed`" in README
    for nombre, k in por_archivo.items():
        assert f"- `tests/{nombre}` ({k}):" in README, nombre


def test_readme_sin_terminos_prohibidos_ni_rutas_locales():
    for t in ("TODO", "[COMPLETAR", "DECLARACION", "make_readme"):
        assert t not in README, t
    assert not re.search(r"\bfases?\b", README, re.I)
    assert not re.search(r"[A-Za-z]:\\Users", README)  # sin rutas absolutas locales


def test_rutas_citadas_en_readme_existen():
    rutas = set(re.findall(r"`((?:docs|src|tests|scripts|notebooks|config|data)/[^`\s]*)`", README))
    rutas |= set(re.findall(r"\]\(((?:docs|src|tests)/[^)]+)\)", README))
    faltan = []
    for r in rutas:
        if any(c in r for c in "…*<>|") or r.endswith(("N.json", "…")) or "snap_" in r:
            continue
        if not (ROOT / r.rstrip("/")).exists():
            faltan.append(r)
    assert faltan == []


# --- retroalimentación del avance 2: alcance temporal, población analizada e indicador satelital ---
KPIS_MD = (ROOT / "docs/KPIs.md").read_text(encoding="utf-8")


def _bloque(texto, titulo):
    """Texto del recuadro que sigue al encabezado `### titulo` (hasta el siguiente encabezado)."""
    assert f"### {titulo}" in texto, titulo
    return texto.split(f"### {titulo}")[1].split("\n#")[0]


def test_encabezados_de_alcance_en_readme_y_kpis():
    for titulo in ("Alcance temporal", "Población analizada", "Indicador satelital frente a evaluación estructural"):
        assert f"### {titulo}" in README, titulo
        assert f"### {titulo}" in KPIS_MD, titulo


def test_recuadro_de_poblacion_coincide_con_gold():
    con = GOLD[~GOLD.sin_datos]
    comunas = sorted(GOLD.comuna.dropna().unique())
    assert len(comunas) == 7 and "02" not in comunas
    n_codigos = GOLD.codigo_barrio.nunique()
    for nombre, texto in (("README", README), ("KPIs.md", KPIS_MD)):
        caja = _bloque(texto, "Población analizada")
        assert f"**{_miles(len(GOLD))}** construcciones (**{_miles(len(con))}** con datos satelitales)" in caja, nombre
        assert f"**{len(comunas)} comunas**" in caja and f"**{n_codigos}** códigos de barrio" in caja, nombre
        assert ", ".join(comunas[:-1]) + " y " + comunas[-1] in caja, nombre
        for frase in ("Comuna 2", "polígonos de afectación preliminar", "no se extrapolan a las construcciones de Cali"):
            assert frase in caja, (nombre, frase)
    assert len(con) == REP["severos"]["total"]["n_con_datos"] and int(GOLD.severo_estricto.sum()) == REP["severos"]["total"]["k_severos"]


def test_recuadro_temporal_usa_las_fechas_de_config():
    from src.common import load_config
    f = load_config()["fechas"]
    for nombre, texto in (("README", README), ("KPIs.md", KPIS_MD)):
        caja = _bloque(texto, "Alcance temporal")
        for v in (f["fecha_imagen_pre"], f["fecha_imagen_post"], f["fecha_edicion_capa"], "2015", "once años", "desconocido"):
            assert v in caja, (nombre, v)
        assert "no el estrato vigente" in caja, nombre


def test_tabla_satelital_frente_a_estructural_con_cifras_reportadas():
    for nombre, texto in (("README", README), ("KPIs.md", KPIS_MD)):
        caja = _bloque(texto, "Indicador satelital frente a evaluación estructural")
        for frase in ("3.403", "1.078", "1.272", "1.053", "23-sep-2026", "no las cotejamos con una fuente oficial descargable",
                      "predio", "no se compara ni se mezcla"):
            assert frase in caja, (nombre, frase)
    assert 1078 + 1272 + 1053 == 3403


def test_cobertura_de_estrato_valido_igual_en_todo_el_readme_y_en_el_reporte():
    """Todas las apariciones del porcentaje deben coincidir entre sí y con quality_report.json redondeado a 3 decimales (half-up)."""
    apariciones = re.findall(r"[Cc]obertura de estrato válido:? \*{0,2}(\d+,\d+ %)", README)
    esperado = _pc(REP["cobertura_estrato_valido"]["pct"])
    assert len(apariciones) >= 2 and set(apariciones) == {esperado}, (apariciones, esperado)
    assert esperado == "99,845 %"
