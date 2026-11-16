"""El documento de resultados (docs/gold/resultados.md) debe contener las cifras de los archivos de salida, tal como salen de ellos (con coma decimal).

Estas pruebas vigilaban el README cuando lo generaba un script; al pasar el análisis a este documento (D106) se trasladaron aquí sin cambiar lo que comprueban.
"""
import json
import re

import pandas as pd

from src.common import ROOT

RUTA = ROOT / "docs" / "gold" / "resultados.md"
RESULTADOS = RUTA.read_text(encoding="utf-8").replace("−", "-")
KP = pd.read_csv(ROOT / "data/gold/kpis_gold.csv")
GOLD = pd.read_csv(ROOT / "data/gold/gold_final.csv", dtype={"comuna": str})
REP = json.loads((ROOT / "data/silver/quality_report.json").read_text(encoding="utf-8"))
KPIS_MD = (ROOT / "docs/gold/KPIs.md").read_text(encoding="utf-8")


def _redondeo(v, d, signo=False):
    """Redondeo half-up sobre el valor decimal tal como está escrito en los archivos (la misma regla de formato que usa el panel)."""
    from decimal import ROUND_HALF_UP, Decimal
    q = (Decimal(repr(float(v))) * 100).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP)
    return (f"{q:+}" if signo else f"{q}").replace(".", ",")


def _pc(v):
    return _redondeo(v, 3) + " %"


def _pp(v):
    return _redondeo(v, 2, signo=True)


def _miles(n):
    return f"{int(n):,}".replace(",", ".")


def test_k5_en_resultados():
    k5 = KP[KP.kpi_id == "K5"].set_index("grupo").valor
    for g in ("cobertura_llave", "cobertura_estrato_valido", "pct_nombre_validado"):
        assert _pc(k5[g]) in RESULTADOS, g


def test_k2_diferencia_y_newcombe_en_resultados():
    d = KP[KP.grupo == "diferencia_3-5_menos_1-2"].iloc[0]
    for v in (d.valor, d.ic95_inf, d.ic95_sup):
        assert _pp(v) in RESULTADOS
    assert f"entre {_pp(d.ic95_inf)} y {_pp(d.ic95_sup)} puntos porcentuales" in RESULTADOS


def test_estructura_de_respuesta_y_licencias():
    for frase in ("(a) Con este proxy y esta muestra no se detecta diferencia", "(b) Los datos son compatibles con diferencias entre",
                  "(c) Esto no equivale a decir que el estrato no influye", "(d) El signo de la diferencia no es estable",
                  "(e) Las tasas por comuna oscilan", "(f) La Comuna 19 concentra", "KR1", "KR5", "CC BY 4.0",
                  "licencia no declarada en el servicio", "Creative Commons Attribution Share-Alike", "CC0"):
        assert frase in RESULTADOS, frase


def test_cifras_de_gold_bronze_y_silver_en_resultados():
    assert f"**{_miles(len(GOLD))} filas**" in RESULTADOS
    paginas = [json.loads(x) for x in (ROOT / "data/bronze/manifest.jsonl").read_text(encoding="utf-8").splitlines()
               if '"source_id": "edificaciones"' in x]
    assert ", ".join(_miles(p["rows"]) for p in paginas) in RESULTADOS
    con = GOLD[~GOLD.sin_datos & GOLD.comuna.notna()]
    sin_estrato = int(con.estrato.isna().sum())
    assert f"Nota: {sin_estrato} construcciones con datos satelitales no tienen estrato válido" in RESULTADOS
    assert f"({_miles(con.estrato.notna().sum())}) es menor que el total con datos y comuna asignada ({_miles(len(con))})" in RESULTADOS
    assert _pc(REP["cobertura_llave"]["pct"]) in RESULTADOS
    assert f"{REP['duplicados_marcados']['geom_duplicada_filas']} construcciones con geometría idéntica" in RESULTADOS


def test_resultados_sin_marcas_pendientes_ni_rutas_locales():
    for t in ("TODO", "[COMPLETAR", "DECLARACION", "make_readme"):
        assert t not in RESULTADOS, t
    assert not re.search(r"\bfases?\b", RESULTADOS, re.I)
    assert not re.search(r"[A-Za-z]:\\Users", RESULTADOS)  # sin rutas absolutas locales


def test_rutas_y_enlaces_citados_en_resultados_existen():
    rutas = set(re.findall(r"`((?:docs|src|tests|scripts|notebooks|config|data)/[^`\s]*)`", RESULTADOS))
    faltan = []
    for r in rutas:
        if any(c in r for c in "…*<>|") or r.endswith(("N.json", "…")) or "snap_" in r:
            continue
        if not (ROOT / r.rstrip("/")).exists():
            faltan.append(r)
    for destino in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", RESULTADOS):
        if destino.startswith(("http://", "https://")):
            continue
        if not (RUTA.parent / destino).exists():
            faltan.append(destino)
    assert faltan == []


# --- retroalimentación recibida: alcance temporal, población analizada e indicador satelital ---
def _bloque(texto, titulo):
    """Texto del recuadro que sigue al encabezado `### titulo` (hasta el siguiente encabezado)."""
    assert f"### {titulo}" in texto, titulo
    return texto.split(f"### {titulo}")[1].split("\n#")[0]


def test_encabezados_de_alcance_en_resultados_y_kpis():
    for titulo in ("Alcance temporal", "Población analizada", "Indicador satelital frente a evaluación estructural"):
        assert f"### {titulo}" in RESULTADOS, titulo
        assert f"### {titulo}" in KPIS_MD, titulo


def test_recuadro_de_poblacion_coincide_con_gold():
    con = GOLD[~GOLD.sin_datos]
    comunas = sorted(GOLD.comuna.dropna().unique())
    assert len(comunas) == 7 and "02" not in comunas
    n_codigos = GOLD.codigo_barrio.nunique()
    for nombre, texto in (("resultados", RESULTADOS), ("KPIs.md", KPIS_MD)):
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
    for nombre, texto in (("resultados", RESULTADOS), ("KPIs.md", KPIS_MD)):
        caja = _bloque(texto, "Alcance temporal")
        for v in (f["fecha_imagen_pre"], f["fecha_imagen_post"], f["fecha_edicion_capa"], "2015", "once años", "desconocido"):
            assert v in caja, (nombre, v)
        assert "no el estrato vigente" in caja, nombre


def test_tabla_satelital_frente_a_estructural_con_cifras_reportadas():
    for nombre, texto in (("resultados", RESULTADOS), ("KPIs.md", KPIS_MD)):
        caja = _bloque(texto, "Indicador satelital frente a evaluación estructural")
        for frase in ("3.403", "1.078", "1.272", "1.053", "23-sep-2026", "no las cotejamos con una fuente oficial descargable",
                      "predio", "no se compara ni se mezcla"):
            assert frase in caja, (nombre, frase)
    assert 1078 + 1272 + 1053 == 3403


def test_cobertura_de_estrato_valido_igual_en_todo_el_documento_y_en_el_reporte():
    """Todas las apariciones del porcentaje deben coincidir entre sí y con quality_report.json redondeado a 3 decimales (half-up)."""
    apariciones = re.findall(r"[Cc]obertura de estrato válido:? \*{0,2}(\d+,\d+ %)", RESULTADOS)
    esperado = _pc(REP["cobertura_estrato_valido"]["pct"])
    assert len(apariciones) >= 2 and set(apariciones) == {esperado}, (apariciones, esperado)
    assert esperado == "99,845 %"



# --- una cifra repetida no puede quedar desactualizada en un solo lugar ---
def apariciones(patron, texto):
    """Valores capturados por `patron` en todo el texto, en orden."""
    return re.findall(patron, texto)


def test_toda_aparicion_de_una_cifra_repetida_coincide_con_la_medida():
    k5 = KP[KP.kpi_id == "K5"].set_index("grupo").valor
    d = KP[KP.grupo == "diferencia_3-5_menos_1-2"].iloc[0]
    esperadas = {
        "cobertura de llave": (r"[Cc]obertura de llave:? \*{0,2}(\d+,\d+ %)", _pc(k5["cobertura_llave"])),
        "nombre validado": (r"[Nn]ombre validado:? \*{0,2}(\d+,\d+ %)", _pc(k5["pct_nombre_validado"])),
        "diferencia de K2 en el texto": (r"diferencia ([+-]?\d+,\d+) p", _pp(d.valor)),
        "diferencia de K2 en S0": (r"\| S0 \|[^\n]*? \| ([+-]\d+,\d+) \[", _pp(d.valor)),
    }
    for nombre, (patron, esperado) in esperadas.items():
        halladas = apariciones(patron, RESULTADOS)
        assert len(halladas) >= 2 or nombre.endswith("en S0"), (nombre, halladas)
        assert halladas and set(halladas) == {esperado}, (nombre, halladas, esperado)


def test_toda_cifra_de_predios_de_la_evaluacion_estructural_es_la_misma_en_los_dos_documentos():
    for nombre, texto in (("resultados", RESULTADOS), ("KPIs.md", KPIS_MD)):
        halladas = apariciones(r"\b(\d\.\d{3}) predios", texto)
        assert len(halladas) >= 2 and set(halladas) == {"3.403"}, (nombre, halladas)


def test_una_aparicion_desactualizada_se_detecta_con_el_mismo_criterio():
    texto = "Cobertura de llave: 99,883 % y luego cobertura de llave 99,884 %"
    assert set(apariciones(r"[Cc]obertura de llave:? \*{0,2}(\d+,\d+ %)", texto)) == {"99,883 %", "99,884 %"}
