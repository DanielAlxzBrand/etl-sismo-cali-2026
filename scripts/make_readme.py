"""Genera README.md leyendo las cifras de los archivos de salida (kpis, quality_report, gold_final, manifiesto, docs)."""
import io
import json
import os
import platform
import re
import sqlite3
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.common import load_config  # noqa: E402

URL_PAIS = ("https://www.elpais.com.co/cali/tras-el-sismo-cali-evalua-miles-de-estructuras-y-alista-la-reconstruccion-el-plan-es-que-de-aqui-a-"
            "diciembre-se-coloque-el-primer-ladrillo-1159.html")


def miles(n):
    return f"{int(n):,}".replace(",", ".")


def redondear(v, d, signo=False):
    """Única función de formato numérico: redondeo half-up sobre el valor decimal tal como está escrito (no truncamiento ni error binario)."""
    q = Decimal(repr(float(v))).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP)
    return (f"{q:+}" if signo else f"{q}").replace(".", ",")


def pc(v, d=3):
    return redondear(Decimal(repr(float(v))) * 100, d) + " %"


def pp(v):
    return redondear(Decimal(repr(float(v))) * 100, 2, signo=True).replace("-", "−")


def dec(v, d=3):
    return redondear(v, d)


def leer(p):
    return (ROOT / p).read_text(encoding="utf-8")


def pruebas_recolectadas():
    """Pruebas por archivo según `pytest --collect-only` (funciones y métodos de clase), ordenadas por nombre de archivo."""
    r = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"], cwd=ROOT, capture_output=True,
                       text=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    cuenta = Counter(l.split("::")[0].split("/")[-1] for l in r.stdout.splitlines() if "::" in l)
    assert cuenta, f"pytest no recolectó pruebas: {r.stdout[-300:]} {r.stderr[-300:]}"
    return dict(sorted(cuenta.items()))


def filas_tabla(texto, prefijo):
    """Filas de una tabla markdown cuya primera celda empieza por prefijo (devuelve listas de celdas)."""
    out = []
    for l in texto.splitlines():
        if l.startswith("| " + prefijo):
            out.append([c.strip() for c in l.strip().strip("|").split("|")])
    return out


def main():
    cfg = load_config()
    F = cfg["fechas"]
    kp = pd.read_csv(ROOT / "data/gold/kpis_gold.csv")
    sens = pd.read_csv(ROOT / "data/gold/kpis_sensibilidad.csv")
    rep = json.loads(leer("data/silver/quality_report.json"))
    g = pd.read_csv(ROOT / "data/gold/gold_final.csv", dtype={"comuna": str, "barrio": str, "codigo_barrio": str, "codigo_poligono": str})
    man = [json.loads(x) for x in leer("data/bronze/manifest.jsonl").splitlines() if x.strip()]
    kpis_md = leer("docs/KPIs.md")
    reglas_md = leer("docs/reglas_silver.md")
    decis_md = leer("docs/DECISIONES.md")
    compr = leer("docs/comprension_proyecto1.md")
    invest = leer("docs/investigacion_fuentes.md")
    con = g[~g.sin_datos]
    cc = con[con.comuna.notna()]
    k5 = kp[kp.kpi_id == "K5"].set_index("grupo")
    dif = kp[kp.grupo == "diferencia_3-5_menos_1-2"].iloc[0]
    assert dif.ic95_inf <= 0 <= dif.ic95_sup, "el intervalo excluye 0: hay que reescribir la redacción (a)"
    x35 = kp[kp.grupo == "estratos_3-5"].iloc[0]
    x12 = kp[kp.grupo == "estratos_1-2"].iloc[0]
    razon = kp[kp.grupo == "razon_3-5_vs_1-2"].iloc[0].valor
    mh = kp[kp.grupo == "razon_MH_ajustada_comuna"].iloc[0]
    k1 = kp[kp.kpi_id == "K1"]
    k6 = kp[kp.kpi_id == "K6"].copy()
    k6["c"] = k6.grupo.str.replace("comuna_", "")
    kmin, kmax = k6.loc[k6.valor.idxmin()], k6.loc[k6.valor.idxmax()]
    k3 = kp[kp.kpi_id == "K3"].iloc[0]
    k4 = kp[kp.kpi_id == "K4"].iloc[0]
    e1 = k1[k1.grupo == "estrato_1"].iloc[0]
    e2 = k1[k1.grupo == "estrato_2"].iloc[0]

    # --- hechos del evento (USGS, muestra guardada en docs/muestras)
    usgs = pd.read_csv(io.StringIO(leer("docs/muestras/v10_usgs_11.csv")))
    ev = usgs[usgs.id == "us6000tjl2"].iloc[0]
    t_utc = datetime.strptime(ev.time[:19], "%Y-%m-%dT%H:%M:%S")
    t_bog = t_utc + timedelta(hours=-5)
    assert "878" in compr and "5.545" in compr and "Capri" in compr
    zonas = re.search(r"Zonas más golpeadas según Alcaldía \(11-oct\) \| ([^|]+) \|", invest).group(1).strip()
    v3 = json.loads(leer("docs/muestras/v3_socrata_views_5vy8.json"))
    v4 = json.loads(leer("docs/muestras/v4_socrata_views_6esn.json"))
    cf3, cf4 = v3["metadata_custom_fields"]["Common Core"], v4["custom_fields"]["Common Core"]

    # --- Bronze
    utc = min(datetime.strptime(m["fetched_at_utc"], "%Y-%m-%dT%H:%M:%SZ") for m in man)
    snap = f"{utc:%Y-%m-%d %H:%M:%S} UTC ({utc + timedelta(hours=-5):%Y-%m-%d %H:%M:%S} hora de Bogotá)"
    pag = [m for m in man if m["source_id"] == "edificaciones"]
    cuenta = {m["source_id"]: m["rows"] for m in man}
    csvm = next(m for m in man if m["source_id"] == "estrato_barrio")
    polm = next(m for m in man if m["source_id"] == "poligonos_barrios")
    mb_api = sum(m["bytes"] for m in pag) / 1024 / 1024

    # --- Silver
    R = {r[0]: r for r in filas_tabla(reglas_md, "R")}
    dup = rep["duplicados_eliminados_por_regla"]
    na = rep["nulos_antes_bronze"]
    cob, cobe = rep["cobertura_llave"], rep["cobertura_estrato_valido"]
    pv = rep["pct_nombre_validado"]
    sin_est = cc[cc.estrato.isna()]
    por_com = ", ".join(f"Comuna {c}: {n}" for c, n in sin_est.groupby("comuna").size().items())
    e = cc[cc.estrato.notna()].copy()
    e["grupo"] = e.estrato.map(lambda s: "1-2" if s in (1, 2) else ("3-5" if s in (3, 4, 5) else "6"))
    comp = e.groupby(["comuna", "grupo"]).agg(n=("objectid", "size"), k=("severo_estricto", "sum")).unstack(fill_value=0)
    ej = g.iloc[0]
    # --- lectura de las construcciones sin nombre validado (cifras de Silver y de la revisión documental)
    silver_int = pd.read_csv(ROOT / "data/silver/silver_integrated.csv", usecols=["nombre_validado"])
    n_noval = int((silver_int.nombre_validado == False).sum())  # noqa: E712
    n_val, n_den = int((silver_int.nombre_validado == True).sum()), int(silver_int.nombre_validado.notna().sum())  # noqa: E712
    cat = {r[0]: (r[2], int(r[3])) for r in filas_tabla(leer("docs/revision_codigos_barrio.md").split("## Resumen")[1].split("\n## ")[0], "(")}
    assert sum(v[1] for v in cat.values()) == n_noval, "la revisión de códigos no suma las construcciones sin nombre validado"
    (_, n_a), (cod_b, n_b), (cod_c, n_c) = cat["(a)"], cat["(b)"], cat["(c)"]
    cod_c_txt = ("código " if "," not in cod_c else "códigos ") + cod_c
    pct_noval = lambda n: redondear(Decimal(n) * 100 / Decimal(n_noval), 1) + " %"  # noqa: E731
    n_con = int(len(con))
    n_sin = int(g.sin_datos.sum())
    comunas_txt = [str(c) for c in sorted(g.comuna.dropna().unique())]
    n_comunas = len(comunas_txt)
    lista_comunas = ", ".join(comunas_txt[:-1]) + " y " + comunas_txt[-1]
    n_codigos = int(g.codigo_barrio.nunique())
    assert n_con == rep["severos"]["total"]["n_con_datos"] and n_con + n_sin == len(g) == rep["sin_datos"]["total"]["den"]
    n_sev = int(g.severo_estricto.sum())
    assert n_sev == rep["severos"]["total"]["k_severos"]
    pct_sev = pc(n_sev / n_con, 2)
    F_pre, F_post, F_ed = F["fecha_imagen_pre"], F["fecha_imagen_post"], F["fecha_edicion_capa"]
    URL_ATC = ("https://www.elpais.com.co/cali/alcaldia-de-cali-entrega-balance-de-gestion-tras-el-sismo-mas-de-3400-edificaciones-evaluadas-y-"
               "45000-familias-damnificadas-2338.html")

    # --- pruebas
    tests = pruebas_recolectadas()
    n_tests = sum(tests.values())

    # --- ejemplo SQL ejecutado de verdad sobre la base
    consulta = ("SELECT estrato, SUM(severo_estricto) AS severos, COUNT(severo_estricto) AS con_datos\n"
                "FROM gold_final WHERE estrato IS NOT NULL GROUP BY estrato ORDER BY estrato;")
    conn = None
    try:
        conn = sqlite3.connect(ROOT / "data/gold/etl_sismo.db")
        filas_sql = conn.execute(consulta).fetchall()
        tablas = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    finally:
        if conn is not None:
            conn.close()
    sql_res = "\n".join(f"{int(a)} | {int(b)} | {int(c)}" for a, b, c in filas_sql)

    # --- tablas de resultados
    filas_k1 = ["| estrato | n con datos | severos | tasa | IC 95 % Wilson | % sin datos | cotas por sin datos | muestra baja |", "|---|---|---|---|---|---|---|---|"]
    for r in k1.itertuples():
        filas_k1.append(f"| {r.grupo.replace('estrato_', 'E')} | {miles(r.denominador)} | {int(r.numerador)} | {pc(r.valor, 2)} | {pc(r.ic95_inf, 2)} – {pc(r.ic95_sup, 2)} | {pc(r.pct_sin_datos, 1)} | {pc(r.cota_inf, 1)} – {pc(r.cota_sup, 1)} | {'sí' if r.muestra_baja else 'no'} |")
    filas_k6 = ["| comuna | n con datos | severos | tasa | IC 95 % Wilson | % de los severos | % de las construcciones | muestra baja |", "|---|---|---|---|---|---|---|---|"]
    S, N = int(cc.severo_estricto.sum()), len(cc)
    for r in k6.itertuples():
        sub = cc[cc.comuna == r.c]
        filas_k6.append(f"| C{r.c} | {miles(r.denominador)} | {int(r.numerador)} | {pc(r.valor, 2)} | {pc(r.ic95_inf, 2)} – {pc(r.ic95_sup, 2)} | {pc(sub.severo_estricto.sum() / S, 1)} | {pc(len(sub) / N, 1)} | {'sí' if r.muestra_baja else 'no'} |")
    filas_comp = ["| comuna | 1-2: n / severos | 3-5: n / severos | 6: n / severos |", "|---|---|---|---|"]
    for c, r in comp.iterrows():
        filas_comp.append(f"| {c} | {int(r[('n', '1-2')])} / {int(r[('k', '1-2')])} | {int(r[('n', '3-5')])} / {int(r[('k', '3-5')])} | {int(r[('n', '6')])} / {int(r[('k', '6')])} |")
    nombres_esc = {"S0": "base (todas las construcciones con estrato válido)", "S1": "solo `nombre_validado = true` (sensibilidad principal de la llave)",
                   "S2": "solo `coincide_poligono = true` (secundaria; no sustituye a S1)", "S3": "solo `pureza_estrato ≥ 0,8`",
                   "S4": "`dano_visible` en lugar de `severo_estricto` (baja confianza)", "S5": "sin construcciones con `geom_duplicada`"}
    filas_s = ["| escenario | qué cambia | tasa 3-5 | tasa 1-2 | diferencia [Newcombe] (pp) | RR Mantel-Haenszel |", "|---|---|---|---|---|---|"]
    for sid in nombres_esc:
        x = sens[sens.escenario == sid].set_index("grupo")
        d = x.loc["diferencia_3-5_menos_1-2"]
        m_ = x.loc["razon_MH_ajustada_comuna", "tasa"]
        filas_s.append(f"| {sid} | {nombres_esc[sid]} | {pc(x.loc['estratos_3-5', 'tasa'], 2)} | {pc(x.loc['estratos_1-2', 'tasa'], 2)} | {pp(d.tasa)} [{pp(d.ic95_inf)}; {pp(d.ic95_sup)}] | {dec(m_) if pd.notna(m_) else 'no calculable'} |")
    s0 = sens[(sens.escenario != "S0") & (sens.grupo == "diferencia_3-5_menos_1-2")].set_index("escenario")
    negativos = ", ".join(s0[s0.tasa < 0].index) or "ninguno"
    comun_lo, comun_hi = k6.ic95_inf.max(), k6.ic95_sup.min()
    baja_e = (f" (ambas con muestra baja: {int(kmin.numerador)} y {int(kmax.numerador)} severos)" if kmin.muestra_baja and kmax.muestra_baja
              else f" (severos: {int(kmin.numerador)} y {int(kmax.numerador)})")
    c19_sev = cc[cc.comuna == "19"].severo_estricto.sum() / S
    c19_n = (cc.comuna == "19").mean()
    sev_b = g[(g.severo_estricto == True) & g.codigo_barrio.notna()].groupby("codigo_barrio").size().rename("k").reset_index()  # noqa: E712
    top10 = sev_b.assign(c=sev_b.codigo_barrio.astype(int)).sort_values(["k", "c"], ascending=[False, True]).head(10).codigo_barrio
    con_b = con[con.codigo_barrio.notna()]
    pct_top = con_b.codigo_barrio.isin(set(top10)).mean()
    n_p = k4.nota.split(";")[0].replace("n_barrios=", "")
    p_perm = k4.nota.split(";")[1].strip().split(" (")[0].replace("p_permutacion=", "")
    dic = filas_tabla(kpis_md.split("## Diccionario de columnas")[1], "`")
    dic_md = "\n".join(["| columna | descripción |", "|---|---|"] + [f"| {r[0]} | {r[1]} |" for r in dic])
    limites = "\n".join(l for l in kpis_md.split("## Qué NO se puede concluir")[1].split("\n## ")[0].splitlines() if re.match(r"^\d+\. ", l))
    limites = "\n".join(l + (f" La Alcaldía de Cali mencionó la Comuna 2 entre las de mayor pérdida de daños (El País Cali, 11-oct-2026: {URL_PAIS}); esa comuna no está en la capa satelital." if l.startswith("2. ") else "") for l in limites.splitlines())
    decis = filas_tabla(decis_md.split("## D-FUENTES")[0], "D")
    dec_md = "\n".join(["| id | decisión | razón |", "|---|---|---|"] + [f"| {r[0]} | {r[1]} | {r[3]} |" for r in decis if re.fullmatch(r"D\d+", r[0])])
    reglas_tema = [
        ("Identificadores y duplicados", ["R01", "R03", "R11"]),
        ("Nulos", ["R02", "R05", "R06", "R14"]),
        ("Tipos y formatos", ["R04", "R07", "R12", "R13", "R15"]),
        ("Llave y ubicación espacial", ["R08", "R09"]),
        ("JOIN y validación", ["R16", "R17", "R18"]),
        ("Columnas descartadas", ["R10"]),
    ]
    reglas_txt = [f"**{tema}.** " + " ".join(f"({i}, {R[i][1]}, {miles(R[i][3])} filas) {R[i][4]}" for i in ids) for tema, ids in reglas_tema]
    arbol = [
        ("main.py", "puerta de entrada: `--stage extract|transform|gold|all` y `--refresh`"),
        ("config/config.yaml", "parámetros: URL de las fuentes, umbrales, fechas, rutas y registro de ejecución"),
        ("requirements.txt", "dependencias con versión mínima"),
        ("pytest.ini", "configuración de las pruebas (carpeta de pruebas y ruta de importación)"),
        (".env.example", "variables opcionales sin valores (`HTTP_USER_AGENT`)"),
        ("src/common.py", "rutas, configuración, sha256 y manifiesto de Bronze"),
        ("src/logger.py", "registro de ejecución con enmascarado de secretos"),
        ("src/extract/extract_api.py", "descarga paginada de la capa ArcGIS y de los polígonos (WFS)"),
        ("src/extract/extract_excel.py", "descarga y lectura del archivo tabular (CSV o Excel)"),
        ("src/transform/clean_api.py", "limpieza de las construcciones"),
        ("src/transform/clean_excel.py", "limpieza del CSV de estrato"),
        ("src/transform/keys.py", "llave del JOIN y normalización de nombres"),
        ("src/transform/integrate.py", "JOIN, huérfanos, validación de la llave y reporte de calidad"),
        ("src/transform/build_gold.py", "Gold, KPI, intervalos y sensibilidades"),
        ("src/load/load_database.py", "carga a SQLite"),
        ("data/bronze/", "respuestas crudas, CSV original, polígonos y `manifest.jsonl`"),
        ("data/silver/", "tablas limpias, huérfanos y `quality_report.json`"),
        ("data/gold/", "`gold_final.csv`, `kpis_gold.csv`, `kpis_sensibilidad.csv`, `etl_sismo.db`"),
        ("notebooks/", "cinco notebooks ejecutados (conexión, EDA, Silver, Gold y validación)"),
        ("tests/", f"{n_tests} pruebas automáticas"),
        ("scripts/make_dist.py", "empaqueta la entrega en `dist/` sin entornos virtuales ni cachés"),
        ("docs/DECISIONES.md", "decisiones con alternativas, razón y riesgo"),
        ("docs/hallazgos_eda.md", "hallazgos H1-H18 del análisis exploratorio"),
        ("docs/reglas_silver.md", "reglas R01-R18 con su hallazgo"),
        ("docs/validacion_llave.md", "validación semántica de la llave por código"),
        ("docs/KPIs.md", "definición de cada KPI y diccionario de columnas de Gold"),
        ("docs/verificacion_fuentes.md", "verificación previa de las fuentes (V1-V14)"),
        ("docs/verificacion_entrega.md", "verificación de la entrega contra el enunciado"),
        ("docs/prueba_entorno_limpio.md", "ejecución en una copia limpia"),
        ("docs/verificacion_logging.md", "verificación del registro de ejecución"),
        ("docs/investigacion_fuentes.md", "investigación y selección de fuentes"),
        ("docs/comprension_proyecto1.md", "comprensión del Proyecto 1"),
        ("docs/revision_codigos_barrio.md", "revisión de los códigos de barrio con diferencias en la validación semántica"),
        ("docs/referencias/", "documento de contexto del Avance 1"),
        ("docs/avance_2/", "retroalimentación recibida y registro de cambios del Avance 2"),
        ("docs/entrega_3/", "documentos de la Entrega 3: sección 1 del checklist de Data Thinking"),
        ("docs/entrega_3/decisiones_tecnicas.md", "decisiones técnicas de la Entrega 3 (API, MySQL, dashboard, orquestación, MLOps)"),
        ("docs/entrega_3/seccion_1/", "sección 1 del checklist: Data Thinking, stakeholders, OKR y KPI, Canvas y MVP"),
        ("docs/muestras/", "muestras de texto de cada fuente probada (no es Bronze)"),
        ("docs/enunciado_flujo.png", "imagen del enunciado de la entrega"),
    ]
    for ruta, _ in arbol:
        assert (ROOT / ruta).exists(), f"ruta citada inexistente: {ruta}"
    arbol_md = "\n".join(f"- `{r}`: {d}" for r, d in arbol) + "\n- `logs/`: archivos de registro diarios (se crean al ejecutar; no se versionan)"
    desc_tests = {"test_extract.py": "manifiesto, sha256, filas y páginas de Bronze (sin red)", "test_transform.py": "llaves, `normalize_key`, duplicados, tipos, zona horaria, vectores de Wilson",
                  "test_quality.py": "campos del reporte, cobertura frente al umbral, mínimo de filas de Gold, KPI en rango", "test_kpis.py": "regresión numérica de los KPI, Newcombe, Mantel-Haenszel y regresión del defecto",
                  "test_readme_cifras.py": "las cifras de este README coinciden con los archivos de salida; recuadros de alcance, población e indicador satelital", "test_logger.py": "enmascarado de secretos y nombre de los loggers",
                  "test_empaquetado_y_revision.py": "el empaquetado excluye entornos virtuales con cualquier nombre; la revisión de códigos de barrio cubre los casos pedidos y suma las construcciones sin nombre validado",
                  "test_dist.py": "el empaquetado detecta entornos virtuales por su contenido, aunque no tengan `pyvenv.cfg`",
                  "test_entrega_3_seccion_1.py": "documentos de la sección 1 del checklist: existencia, términos prohibidos, cifras y avisos"}
    tests_md = "\n".join(f"- `tests/{n}` ({k}): {desc_tests.get(n, '')}." for n, k in tests.items())
    barrio_ej = str(ej.barrio).zfill(2) if pd.notna(ej.barrio) else ""

    txt = f"""# Avance 2 · ETL medallion del sismo M7.4 del 10-ago-2026

**Autores:** Diego Fernando Gordillo Londoño, Jhoan Sebastián Castellanos Mayor y Daniel Alexander Brand García.
**Curso:** ETL · **Universidad:** Universidad Autónoma de Occidente (UAO).
**Entorno:** Python {platform.python_version()} en Windows (PowerShell).

Este repositorio contiene un pipeline ETL con arquitectura medallion (Bronze → Silver → Gold → Validación) que integra una API y un archivo tabular para estudiar, con un indicador satelital, el cambio visible en las construcciones de 7 comunas de Cali tras el sismo. Este documento explica el proyecto de principio a fin: el contexto, las fuentes, qué hace cada capa, cómo leer los resultados, cómo reproducirlos y qué no se puede concluir.

## 1. Título, autores y entorno
Ver el encabezado. Todo el código usa `pathlib` para las rutas y se probó en Windows con PowerShell; los comandos de este documento están escritos para PowerShell.

## 2. Contexto del problema
**El evento.** El {t_utc:%d-%m-%Y} a las {t_utc:%H:%M:%S} UTC ({t_bog:%H:%M:%S} hora de Colombia) ocurrió un sismo de magnitud {ev.magType.capitalize()} {dec(ev.mag, 1)} (identificador USGS `{ev.id}`), con epicentro "{ev.place.split(',')[0]}" (Chocó), en {dec(ev.latitude, 4)}° N y {dec(abs(ev.longitude), 4)}° O. La profundidad vigente en el catálogo USGS al 15-oct-2026 es de {dec(ev.depth, 2)} km (registro actualizado el {ev.updated[:10]}); esta cifra ha tenido revisiones. Fuente: USGS FDSN Event, `https://earthquake.usgs.gov/fdsnws/event/1/` (muestra en `docs/muestras/v10_usgs_11.csv`, consulta del 15-oct-2026).

**Por qué importa Cali.** Cali fue una de las ciudades con mayor nivel de afectación. Las cifras oficiales cambian con el tiempo: el Avance 1 usó el corte del 18 de agosto de la Alcaldía (878 edificaciones verificadas de 5.545 reportes ciudadanos; 24 colapsos totales, 127 parciales y 192 con daño estructural), y reportes posteriores hablan de miles de predios evaluados. Por eso en este proyecto cada cifra lleva su fecha de corte. Según la Alcaldía (El País Cali, 11-oct-2026), las zonas más golpeadas fueron {zonas}.

**Lo que decía el Avance 1.** Había un patrón visible a simple vista: barrios como Capri, Guadalupe, Pampalinda, Tequendama, San Fernando y Cuarto de Legua, de estratos 3 a 5 y con construcciones antiguas, aparecían muy afectados. La hipótesis era que el daño lo explican mejor los factores geotécnicos y constructivos de cada zona que el estrato socioeconómico, pero **no estaba comprobada** (`docs/comprension_proyecto1.md`).

## 3. Pregunta de negocio y alcance
> **En las construcciones evaluadas por satélite en {n_comunas} comunas de Cali tras el sismo, ¿la proporción con cambio satelital severo (severo estricto, proxy de daño) cambia entre los estratos 1-6 de su barrio, o se concentra por zona?**

Es la porción del Proyecto 1 que se puede medir hoy con datos abiertos estructurados: el estrato es la única variable de control con fuente tabular, y la capa satelital es la única fuente abierta a nivel de construcción. El costo es que el indicador es un proxy satelital y no una evaluación estructural (ATC-20) de la Alcaldía; no los mezclamos (ver la tabla «Indicador satelital frente a evaluación estructural»).

| KR | estado | evidencia |
|---|---|---|
| KR1 concentración de daño severo (proxy satelital) | parcial | K3 y K6; solo 7 comunas |
| KR2 contraste con amenaza sísmica oficial | no cubierto | no se usó amenaza sísmica oficial; trabajo futuro |
| KR3 antigüedad constructiva | fuera de alcance | cualitativo, no es ETL |
| KR4 daño por estrato | cubierto con el proxy satelital | K1 y K2 |
| KR5 avance de verificación | fuera de alcance | seguimiento, no es ETL |

### Alcance temporal
> **Alcance temporal.** El estrato por barrio es de **2015** (DAPM Cali, medido en lados de manzana). Las construcciones se evaluaron con imágenes del **{F_pre}** y del **{F_post}**, y la capa se editó por última vez el **{F_ed}** (`config/config.yaml`, sección `fechas`). Los polígonos de barrios que usamos para validar son de 2026 y están renumerados respecto a 2015 (H13, H18). Entre el estrato y las imágenes hay unos **once años** de distancia. **Regla de lectura:** los resultados por estrato describen el estrato de 2015 asignado al barrio, no el estrato vigente. Lo que cambió en los barrios entre 2015 y 2026 es **desconocido** para nosotros y no lo estimamos.

### Población analizada
> **Población analizada.** **{miles(len(g))}** construcciones (**{miles(n_con)}** con datos satelitales) de **{n_comunas} comunas** de Cali ({lista_comunas}), repartidas en **{n_codigos}** códigos de barrio. Criterio de inclusión: la capa solo incluye construcciones dentro de los polígonos de afectación preliminar del visor de emergencia del IGAC, según la descripción del dataset. Quedan fuera las comunas ausentes, entre ellas la **Comuna 2** (la Alcaldía la mencionó entre las de mayor pérdida), y la zona rural. **Regla:** las tasas describen esta muestra; no se extrapolan a las construcciones de Cali ni a la ciudad.

### Indicador satelital frente a evaluación estructural
| aspecto | indicador satelital (este proyecto) | evaluación estructural (ATC-20, Alcaldía de Cali) |
|---|---|---|
| qué es | cambio de textura entre dos imágenes de satélite sobre la huella de la construcción; el severo estricto es la clase "Alta probabilidad de escombros" | inspección técnica en sitio que clasifica el predio con un sticker: rojo (inseguro), amarillo (uso restringido) o verde |
| quién lo produce | Fondo Adaptación (capa catalogada en datos.gov.co, `5vy8-gpw8`) | Alcaldía de Cali |
| cómo se obtiene | análisis de imágenes del {F_pre} y {F_post}, sin inspección directa | evaluación directa de cada predio |
| qué ve y qué no ve | ve cambio visible desde arriba; no ve daño interno ni daño sin cambio visible, y no da seguridad de uso | evalúa la seguridad de uso del predio; no tenemos sus datos por predio |
| unidad de análisis | construcción (huella catastral) | predio |
| cobertura | {miles(len(g))} construcciones de {n_comunas} comunas, dentro de los polígonos de afectación preliminar | 3.403 predios caracterizados (no conocemos su distribución por comuna) |
| cifras disponibles | {miles(n_con)} con datos satelitales; {n_sev} severos estrictos ({pct_sev}) | 3.403 predios: 1.078 rojo, 1.272 amarillo y 1.053 verde, publicado por El País Cali el 23-sep-2026 ({URL_ATC}) |
| uso en este proyecto | es la base de todos los KPI de Gold | solo contexto: no se compara ni se mezcla con ninguna cifra de Gold |

Las cifras de la evaluación estructural son cifras reportadas por la prensa citando a la Alcaldía; no las cotejamos con una fuente oficial descargable. La unidad (predios) no es la nuestra (construcciones), por lo que no las comparamos ni las mezclamos con ninguna cifra de Gold.

## 4. Mapa del flujo
```
 API (ArcGIS) ─┐                                                              ┌─ gold_final.csv
               ├─> BRONZE ──> SILVER ──> JOIN por código de barrio ──> GOLD ──┼─ kpis_gold.csv, kpis_sensibilidad.csv
 CSV estrato ──┘  (crudo)    (limpio)   (LEFT, con huérfanos)                  └─ etl_sismo.db (SQLite)
                                          VALIDACIÓN: pruebas, recálculo SQL, evidencias en docs/
```
| capa | entra | qué se hace | sale |
|---|---|---|---|
| **Bronze** | la capa ArcGIS (API), el CSV de estrato y los polígonos de barrios | se guarda tal como llegó, con sha256 y manifiesto | `data/bronze/api/…/page_000N.json`, `data/bronze/tabular/…csv`, `data/bronze/geo/…geojson`, `data/bronze/manifest.jsonl` |
| **Silver** | Bronze (solo lectura) | duplicados, nulos, tipos y formatos, llave, JOIN y validación de calidad | `silver_construcciones.csv`, `silver_estrato_barrio.csv`, `silver_integrated.csv`, `silver_orphans_left.csv`, `silver_orphans_right.csv`, `quality_report.json` |
| **Gold** | `silver_integrated.csv` (nunca Bronze) | indicadores, intervalos, cotas y sensibilidades | `gold_final.csv`, `kpis_gold.csv`, `kpis_sensibilidad.csv`, `etl_sismo.db` |
| **Validación** | todo lo anterior | pruebas, recálculo independiente con SQL, verificación de sha256, notebooks | `docs/`, `notebooks/`, `tests/` |

## 5. Fuentes de datos
Todas se consultaron el 15-oct-2026 (hora de Bogotá). El snapshot de Bronze del manifiesto está en UTC: **{snap}**.

### 5.1 Capa de impacto satelital en construcciones (API)
- **Qué es:** "Impacto Satelital en Edificaciones por Terremoto. Cali 2026". Analiza la huella de cada construcción de la capa catastral "Construcciones" (Geoportal Catastral Cali, 2024) y calcula el diferencial de textura entre una imagen anterior ({F['fecha_imagen_pre']}) y una posterior ({F['fecha_imagen_post']}). Solo incluye construcciones dentro de los polígonos de afectación preliminar del visor de emergencia del IGAC.
- **Quién la publica y cómo se accede:** Fondo Adaptación, catalogada en datos.gov.co (`5vy8-gpw8`, publicada {cf3['Issued'][:10]}). El endpoint Socrata del catálogo **no es tabular**: es un enlace federado (`assetType: federated_href`, `columns: []`) y `/resource/5vy8-gpw8.json` responde HTTP 403 ("no row or column access to non-tabular tables"). Por eso usamos el **FeatureServer de ArcGIS** al que enlaza el propio catálogo (`https://services3.arcgis.com/Hf3YbZrlZ0OA2COM/arcgis/rest/services/Impacto_Satelital_en_Edificaciones_por_Terremoto_Cali_2026/FeatureServer/0`): es la misma capa, con paginación (`resultOffset`, máximo 2.000 filas por página) y sin token.
- **Columnas que usamos:** `OBJECTID`, `COMUNA`, `BARRIO` (códigos catastrales de 2 dígitos, no nombres), `NPISOS`, `Indice_Escombros`, `Estado_Estructural` y la geometría (polígonos en EPSG:4326).
- **Última edición:** {F['fecha_edicion_capa']} (hora de Bogotá). **Atribución y licencia:** Fondo Adaptación; CC BY 4.0 según los metadatos del catálogo (`{cf3['License']}`); licencia no declarada en el servicio ArcGIS (su `copyrightText` está vacío).

### 5.2 Estratificación por barrio 2015 (archivo tabular)
- **Qué es:** "Estratificación socioeconómica según estrato, por barrio en Cali 2015": para cada barrio, el número de lados de manzana en cada estrato (1 a 6), los lados sin vivienda y el estrato moda.
- **Quién la publica y cómo se accede:** Departamento Administrativo de Planeación Municipal (DAPM) de Cali; publicada {cf4['Issued'][:10]}, última actualización {cf4['Last Update'][:10]}. El catálogo de datos.gov.co enlaza al portal datos.cali.gov.co, de donde descargamos el CSV con un `User-Agent` (la descarga directa `rows.csv` de datos.gov.co falla porque es un enlace federado).
- **Columnas:** `Código único` (llave), `Barrio`, `Lados de manzana por estrato 1…6`, `Sin vivienda`, `Estrato moda`. Tiene {miles(csvm['rows'])} filas: 346 barrios y 23 filas resumen (22 comunas y "Otros").
- **Por qué CSV y no Excel:** el requisito del curso admite CSV o Excel y esta tabla solo se publica como CSV. El módulo se llama `extract_excel.py` porque su lector (`leer_tabular_raw`) soporta los dos formatos (CSV y `.xlsx` vía `openpyxl`).
- **Licencia:** el CSV figura como Creative Commons Attribution Share-Alike en datos.cali.gov.co y como CC0 en datos.gov.co (`docs/muestras/v4_ckan_licencia.txt`); atribuimos a DAPM Cali. Gold contiene datos derivados de este CSV (por ejemplo el estrato de cada construcción); los datos derivados se comparten con atribución a DAPM Cali y bajo la misma licencia.

### 5.3 Polígonos de barrios (solo validación)
Servicio WFS del IDESC / DAPM Cali (`https://ws-idesc.cali.gov.co/geoserver/dapm/ows`, capa `dapm:pdt_dpa_barrios_sectores`), pedido en EPSG:4326: {polm['rows']} polígonos (324 barrios y 18 sectores). Los usamos para comprobar la llave, no para el JOIN. Licencia no verificada.

### 5.4 USGS (solo contexto)
La consulta de USGS devuelve 11 eventos y no trae ninguna llave hacia un barrio o municipio (solo un texto con el lugar), por lo que no puede entrar al JOIN. Solo describimos el evento en este documento. Licencia no verificada.

## 6. Capa Bronze
**Qué guardamos.** La respuesta cruda de cada petición, byte a byte: {len(pag)} páginas de la API ({', '.join(miles(m['rows']) for m in pag)} filas; {dec(mb_api, 1)} MB en total), los conteos oficiales de la capa antes y después de descargar ({miles(cuenta['edificaciones_count_antes'])} y {miles(cuenta['edificaciones_count_despues'])}), el metadato de la capa (`capa_meta.json`: campos, fecha de edición y extensión), el CSV original ({miles(csvm['bytes'])} bytes) y los polígonos ({miles(polm['bytes'])} bytes).

**Por qué es inmutable.** Si Bronze cambiara, no podríamos demostrar de dónde salió cada cifra. Los archivos se abren en modo exclusivo (`"xb"`): un archivo existente nunca se sobrescribe. No se renombran columnas, no se parsean fechas, no se corrigen tipos ni se eliminan filas.

**El manifiesto.** `data/bronze/manifest.jsonl` tiene una línea por archivo con `source_id`, `url`, `params`, `fetched_at_utc`, `http_status`, `rows`, `bytes`, `sha256` y `path`. Nunca incluye tokens. Se verifica en PowerShell comparando el hash de cada archivo con el del manifiesto (debe imprimir `True` en las {len(man)} líneas):
```powershell
Get-Content data\\bronze\\manifest.jsonl | ForEach-Object {{ $m = $_ | ConvertFrom-Json; $h = (Get-FileHash $m.path -Algorithm SHA256).Hash.ToLower(); "{{0}}  {{1}}" -f ($h -eq $m.sha256), $m.path }}
```
**Repetir sin duplicar.** Si Bronze ya existe, `python main.py --stage extract` verifica los sha256 y escribe "ya existe, sha256 coincide": no crea archivos ni agrega líneas al manifiesto. **Refresco.** `python main.py --stage extract --refresh` (necesita red) crea un snapshot nuevo `snap_<fecha UTC>` sin tocar el anterior. Una extracción se considera completa solo si existe el conteo posterior; las páginas se leen con `resultOffset` y orden estable por `OBJECTID`.

## 7. Capa Silver
Silver solo lee Bronze y escribe tablas limpias. Cada regla cita el hallazgo del análisis exploratorio (`docs/hallazgos_eda.md`, H1-H18) que la justifica; sin hallazgo no hay regla. Las 18 reglas (R01-R18, `docs/reglas_silver.md`), agrupadas por tema, con su hallazgo y las filas que afectan:

{chr(10).join('- ' + t for t in reglas_txt)}

### Duplicados: qué encontramos y qué decidimos
- `OBJECTID` es único: **{dup['objectid']} duplicados eliminados** por esa llave (se aplica `duplicated(keep="first")` de forma explícita). La llave catastral (comuna, barrio, manzana, terreno, condición, edificio, predio) sí se repite en 3.719 filas porque un predio tiene varias construcciones; **no** se deduplica por ella ({dup['llave_catastral']} eliminadas). En el CSV, el código de barrio es único ({dup['codigo_barrio_csv']} eliminados).
- Hay **{rep['duplicados_marcados']['geom_duplicada_filas']} construcciones con geometría idéntica a otra (9 parejas)**. Las marcamos con `geom_duplicada` y las conservamos: tienen `OBJECTID` distinto y no hay evidencia de doble conteo (H2); eliminarlas sería arbitrario.

### Nulos
Texto vacío o solo espacios pasa a nulo real (`COMUNA` y `BARRIO`: {na['COMUNA']} y {na['BARRIO']} construcciones, que no se imputan y terminan como huérfanas). `Indice_Escombros` es nulo en {na['Indice_Escombros']} construcciones, exactamente las de "Sin datos satelitales": no se imputa y esas construcciones salen del denominador de las tasas. Las banderas `severo_estricto` y `dano_visible` son **nulas, no falsas**, cuando no hay datos. `NPISOS` queda como entero nullable ({na['NPISOS']} nulos). En el CSV, un guion o un vacío en los lados de manzana vale 0, y el estrato moda `NR` queda como estrato nulo.

### La llave del JOIN
Las construcciones no traen el nombre del barrio, solo `COMUNA` y `BARRIO` (dos dígitos cada uno), y el CSV trae un `Código único`. La llave es `int(COMUNA)*100 + int(BARRIO)` como texto sin ceros a la izquierda. Ejemplo real: una construcción con comuna `{ej.comuna}` y barrio `{barrio_ej}` tiene la llave `{ej.codigo_barrio}`, que en el CSV corresponde a "{ej.nombre_barrio_csv}" (estrato moda {int(ej.estrato)}). Es un `LEFT JOIN` desde las construcciones, para que ninguna construcción desaparezca aunque no tenga estrato.

### Las tres coberturas
1. **Cobertura de llave: {pc(cob['pct'])}** ({miles(cob['num'])} de {miles(cob['den'])}): construcciones cuya llave existe en el CSV. Es la que se compara con el umbral ({dec(rep['umbral_cobertura_join'], 2)}): {rep['resultado_umbral']}.
2. **Cobertura de estrato válido: {pc(cobe['pct'])}** ({miles(cobe['num'])}): además de existir la llave, el barrio tiene un estrato moda entre 1 y 6 (se excluyen los barrios `NR`).
3. **Nombre validado: {pc(pv['global']['pct'])}** ({miles(pv['global']['num'])} de {miles(pv['global']['den'])}): el nombre del barrio en el CSV de 2015 coincide (similitud ≥ 0,85) con el del polígono 2026 donde cae la construcción. Es un control de la llave, no un filtro; `llave_confianza` = **{rep['llave_confianza']}** (`docs/validacion_llave.md`).

### Huérfanos
Se guardan, no se descartan. A la izquierda (`silver_orphans_left.csv`): {rep['huerfanos']['izquierda']} construcciones sin llave en el CSV ({'; '.join(f'{k}: {v}' for k, v in rep['huerfanos']['causas'].items())}). A la derecha (`silver_orphans_right.csv`): {rep['huerfanos']['derecha_barrios_sin_construcciones']} barrios del CSV sin ninguna construcción, esperable porque la capa solo cubre 7 comunas.

### Por qué los polígonos 2026 no son la llave
El código derivado coincide con el código del polígono 2026 en {pc(rep['pct_coincide_poligono']['pct'], 2)} de las construcciones. La diferencia se debe sobre todo a renumeración de códigos entre 2015 y 2026: entre las construcciones que no coinciden con el polígono, el {pc(pv['coincide_poligono_false']['pct'], 2)} tiene el nombre validado, es decir, es el mismo barrio con otro código. Por eso la llave es el código catastral que sí existe en el CSV de 2015 y los polígonos solo validan.

**Lectura de las construcciones sin nombre validado.** De las {n_noval} construcciones sin nombre validado, {n_a} ({pct_noval(n_a)}) corresponden a diferencias de escritura (prefijos como «Barrio» o «Sector», abreviaturas), {n_b} ({pct_noval(n_b)}) a nombres ampliados o cambiados y {n_c} ({pct_noval(n_c)}) a un posible cambio de límites ({cod_c_txt}). Si se aceptaran las de la primera categoría, el porcentaje de nombre validado sería {pc((n_val + n_a) / n_den, 2)}; conservamos {pc(pv['global']['pct'], 2)} porque el umbral de similitud se fijó antes de ver los resultados y no se ajusta a posteriori. La revisión visual de estos códigos sobre el mapa sigue pendiente.

**Revisión de los códigos con diferencias.** Revisamos uno por uno los 7 códigos sin nombre validado, el código 1920 y las 2 construcciones sin comuna ni barrio, sin cambiar ninguna columna ni cifra: [docs/revision_codigos_barrio.md](docs/revision_codigos_barrio.md). La revisión visual en el mapa sigue pendiente.

## 8. Capa Gold
**`gold_final.csv`** tiene **{miles(len(g))} filas**, una por construcción (`objectid` único), sin duplicados. **`kpis_gold.csv`** tiene {len(kp)} filas con los indicadores K1-K6 (valor, numerador, denominador, grupo, fecha de corte, intervalo de Wilson, cotas por "sin datos", bandera de muestra baja y una nota). **`kpis_sensibilidad.csv`** repite K1, K2 y K6 en seis escenarios (S0-S5, {len(sens)} filas). **`etl_sismo.db`** (SQLite) tiene las tablas {', '.join(f'`{t}`' for t in tablas)}.

Diccionario de columnas de `gold_final.csv`:

{dic_md}

Ejemplo de consulta (se ejecuta con `sqlite3` o con `pandas.read_sql_query`); devuelve, por estrato, los severos y las construcciones con datos satelitales:
```sql
{consulta}
```
Resultado (estrato | severos | con_datos):
```
{sql_res}
```

## 9. Cómo leer los resultados
- **(a) Tasa de severos estrictos.** Es k / n, con k = construcciones con cambio satelital severo (severo estricto, proxy de daño: clase "Alta probabilidad de escombros") y n = construcciones **con datos satelitales** del grupo. Las "Sin datos satelitales" salen del denominador y se reportan aparte; nunca se tratan como "sin daño".
- **(b) Intervalo de Wilson.** Una tasa calculada sobre una muestra es incierta; el intervalo de Wilson al 95 % da el rango de valores compatibles con lo observado. Ejemplo real (K1, estrato 1): {int(e1.numerador)} severas de {miles(e1.denominador)} = {pc(e1.valor, 2)}, intervalo {pc(e1.ic95_inf, 2)} – {pc(e1.ic95_sup, 2)}. Con pocos casos el intervalo es ancho; con muchos, angosto.
- **(c) Cotas por "sin datos satelitales".** Para cada grupo, la cota inferior supone que todas las construcciones sin datos no son severas, y la superior que todas lo son: `k/(n + sin datos)` y `(k + sin datos)/(n + sin datos)`. Son extremos poco realistas, pero muestran cuánto podría mover el resultado la falta de datos. El estrato 2 es especial: {pc(e2.pct_sin_datos, 1)} de sus construcciones no tiene datos, y su cota va de {pc(e2.cota_inf, 1)} a {pc(e2.cota_sup, 1)}. Si las cotas de dos grupos se solapan, el orden entre ellos no es identificable.
- **(d) Muestra baja.** Un grupo tiene muestra baja si tiene menos de 30 severos; sus tasas son inestables y se marcan.
- **(e) Intervalo de Newcombe de la diferencia (K2).** K2 compara los estratos 3-5 con los 1-2 y reporta la diferencia de tasas con un intervalo de Newcombe. Si el intervalo incluye 0 (aquí {pp(dif.ic95_inf)} a {pp(dif.ic95_sup)} puntos porcentuales), los datos son compatibles con que no haya diferencia, y la redacción permitida es "con este proxy y esta muestra no se detecta diferencia"; nunca "el estrato no influye".
- **(f) Mantel-Haenszel.** Calcula una razón de tasas ajustada por comuna, para quitar el efecto de la ubicación. Aquí **no es interpretable**: solo la Comuna 18 tiene construcciones con datos en ambos grupos (44 expuestas y 52 de referencia), y el valor ({dec(mh.valor)}) descansa en esas 96 construcciones. Es una señal de que estrato y ubicación están confundidos, no un resultado.
- **(g) K3, K4 y K5.** *K3 (concentración):* qué porcentaje de las construcciones severas está en los 10 barrios con más severos. *K4 (Spearman):* correlación de rangos entre el estrato moda de un barrio y su tasa de severos, para barrios con al menos 10 construcciones con datos; es descriptiva, a nivel de barrio. *K5 (calidad del JOIN):* las tres coberturas de la sección 7.

## 10. Resultados
> **Recordatorio.** Los resultados por estrato describen el estrato de 2015 asignado al barrio, no el vigente (ver «Alcance temporal»), y las tasas describen las {miles(n_con)} construcciones con datos de {n_comunas} comunas, no las de Cali (ver «Población analizada»).

### Respuesta a la pregunta de negocio
(a) Con este proxy y esta muestra no se detecta diferencia en la proporción de construcciones con cambio satelital severo (severo estricto, proxy de daño) entre los estratos 3-5 y 1-2 ({pc(x35.valor, 2)} frente a {pc(x12.valor, 2)}; diferencia {pp(dif.valor)} puntos porcentuales).
(b) Los datos son compatibles con diferencias entre {pp(dif.ic95_inf)} y {pp(dif.ic95_sup)} puntos porcentuales (intervalo de Newcombe al 95 %).
(c) Esto no equivale a decir que el estrato no influye.
(d) El signo de la diferencia no es estable entre escenarios (negativo en: {negativos}) y la razón ajustada por comuna ({dec(mh.valor, 2)}) solo usa la Comuna 18 (44 construcciones expuestas y 52 de referencia), por lo que no es interpretable.
(e) Las tasas por comuna oscilan entre {pc(kmin.valor, 2)} (C{kmin.c}) y {pc(kmax.valor, 2)} (C{kmax.c}){baja_e}; {'todos los intervalos de Wilson comparten un tramo común (' + pc(comun_lo, 2) + ' a ' + pc(comun_hi, 2) + ')' if comun_lo <= comun_hi else 'los intervalos no comparten un tramo común'}.
(f) La Comuna 19 concentra {pc(c19_sev, 1)} de los severos y {pc(c19_n, 1)} de las construcciones con datos (comunas asignadas), así que la concentración se explica por tamaño en esta muestra.

No concluimos causalidad ni validamos o refutamos la hipótesis geotécnica del Avance 1.

### K1 · Tasa por estrato (fecha de corte {F['fecha_edicion_capa']})
{chr(10).join(filas_k1)}

### K2-K5
- Tasa estratos 3-5: {int(x35.numerador)}/{miles(x35.denominador)} = {pc(x35.valor, 2)}; estratos 1-2: {int(x12.numerador)}/{int(x12.denominador)} = {pc(x12.valor, 2)} (muestra baja); razón {dec(razon)}; diferencia {pp(dif.valor)} pp, Newcombe [{pp(dif.ic95_inf)}; {pp(dif.ic95_sup)}]. E6 queda fuera de K2 (11 construcciones).
- K3: los 10 barrios con más severos reúnen {int(k3.numerador)} de {int(k3.denominador)} severos ({pc(k3.valor, 1)}); esos 10 barrios reúnen {pc(pct_top, 1)} de las construcciones con datos; concentración de casos no es mayor riesgo.
- K4: Spearman entre estrato moda y tasa por barrio = {dec(k4.valor)} (n = {n_p} barrios; p de permutación = {p_perm.replace('.', ',')}); descriptivo.
- K5 (calidad del JOIN): cobertura de llave {pc(k5.loc['cobertura_llave'].valor)}; cobertura de estrato válido {pc(k5.loc['cobertura_estrato_valido'].valor)}; nombre validado {pc(k5.loc['pct_nombre_validado'].valor)}.

### K6 · Tasa por comuna
{chr(10).join(filas_k6)}

### Sensibilidades S0-S5
Repiten K2 cambiando una decisión cada vez. En todos los escenarios el intervalo de la diferencia incluye 0.

{chr(10).join(filas_s)}

### Composición del grupo de estratos 1-2 (construcciones con datos / severos)
{chr(10).join(filas_comp)}

Nota: {len(sin_est)} construcciones con datos satelitales no tienen estrato válido ({por_com}); por eso la suma de la tabla ({miles(len(e))}) es menor que el total con datos y comuna asignada ({miles(len(cc))}).

El grupo de estratos 1-2 está formado, casi por completo, por las Comunas 20 y 18; K2 compara en la práctica la Comuna 20 con el resto de la muestra.

### Interpretación honesta
**Se puede afirmar:** con este proxy y esta muestra no detectamos diferencia entre los estratos 3-5 y 1-2; la proporción de construcciones con cambio visible severo ronda {pc(con.severo_estricto.mean(), 1)} y no varía de forma clara entre estratos ni entre comunas; la concentración de severos en la Comuna 19 coincide con su tamaño. **No se puede afirmar:** que el estrato no influya, que el cambio satelital severo sea mayor o menor en algún estrato, ni nada sobre las causas (geotécnicas o constructivas). El indicador es un proxy que mide cambio visible desde satélite, no una evaluación estructural, la muestra la definieron los polígonos de afectación y el estrato está asignado por barrio.

## 11. Limitaciones y alcance
{limites}

Además: la capa viene de un servicio ArcGIS Online de un tercero y puede cambiar; la **reproducibilidad la garantiza el snapshot de Bronze con su manifiesto y sha256**, no el servicio. El estrato es de **2015** y se mide en **lados de manzana**, no por construcción.

## 12. Cómo reproducir
1. **Entorno** (PowerShell, en la raíz del repositorio):
```powershell
py -3 -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
```
Debe terminar sin errores (Python {platform.python_version()}).
2. **Variables opcionales:** `Copy-Item .env.example .env` (solo `HTTP_USER_AGENT`; no se necesitan tokens).
3. **Pipeline completo:** `python main.py --stage all`. Con Bronze presente no necesita red. Al terminar el registro muestra, entre otras líneas, `Salida: construcciones={miles(len(g))} barrios=346 integrado={miles(len(g))} | cobertura de llave={cob['pct'] * 100:.4f}% (pasa)` y `Salida: gold_final={miles(len(g))} filas | kpis_gold={len(kp)} filas (6 indicadores) | sensibilidades={len(sens)} filas`. Ejecutarlo dos veces seguidas deja los mismos sha256 en `data/silver` y `data/gold`:
```powershell
Get-FileHash -Algorithm SHA256 data\\silver\\*.csv, data\\silver\\quality_report.json, data\\gold\\*.csv
```
4. **Pruebas:** `pytest -q` → `{n_tests} passed`.
5. **Notebooks** (cada uno se ejecuta de arriba a abajo sin errores):
```powershell
jupyter nbconvert --to notebook --execute --inplace notebooks\\05_validacion_evidencias.ipynb
```
6. **Verificar Bronze:** el comando de la sección 6 debe imprimir `True` en las {len(man)} líneas.
7. **Refresco (solo con red):** `python main.py --stage extract --refresh` crea un snapshot nuevo; después `python main.py --stage transform` y `--stage gold` regeneran Silver y Gold (los resultados pueden cambiar si la fuente cambió).

**Registro de ejecución (logs).** Cada ejecución escribe en consola y en `logs\\etl_AAAAMMDD.log`, con el formato `fecha hora NIVEL módulo mensaje`. Cada etapa registra su inicio, su fin con la duración, y las filas de entrada y salida. Las advertencias de calidad usan `WARNING` (construcciones sin llave, geometrías duplicadas, grupos con muestra baja); `ERROR` solo aparece si algo falla. Un filtro oculta tokens, cabeceras de autenticación y valores de `.env`. Se leen con `Get-Content logs\\etl_*.log -Tail 20` y `Select-String " WARNING " logs\\*.log`. El formato, el nivel y la carpeta se configuran en la sección `logging` de `config/config.yaml`. Los logs no entran en Silver, Gold ni Bronze, por lo que no alteran los sha256.

## 13. Estructura del repositorio
{arbol_md}

## 14. Pruebas y validación
Hay **{n_tests} pruebas** automáticas, sin red:
{tests_md}

Además: (1) el **recálculo independiente de los KPI con SQL** sobre SQLite (notebook 04, diferencia máxima inferior a 1e-9), con implementaciones independientes de Wilson, Newcombe, Mantel-Haenszel y Spearman; (2) la **regresión del defecto de Mantel-Haenszel**: ese recálculo detectó que se contaban construcciones sin datos satelitales en los tamaños de grupo; se corrigió y una prueba fija el comportamiento (`docs/DECISIONES.md`); (3) las evidencias en `docs/`: `verificacion_entrega.md`, `prueba_entorno_limpio.md`, `verificacion_fuentes.md`, `verificacion_logging.md` y los hashes de antes y después del registro.

## 15. Decisiones principales y trazabilidad
El detalle, con alternativas, razón y riesgo de cada decisión, está en [docs/DECISIONES.md](docs/DECISIONES.md).

{dec_md}

Decisiones de las fuentes: el plan elegido es el de las construcciones de la capa satelital, en 7 comunas de Cali (la verificación previa de las fuentes cumplió los criterios de acceso, columnas, cobertura y volumen); el endpoint Socrata no es tabular y se usa el FeatureServer enlazado; la llave es el código catastral y no un nombre; el indicador principal es `severo_estricto` y `dano_visible` queda como sensibilidad de baja confianza.

**Cómo leer los identificadores:** `H#` = hallazgo del análisis exploratorio (`docs/hallazgos_eda.md`); `R##` = regla de Silver (`docs/reglas_silver.md`); `K#` = indicador de Gold (`docs/KPIs.md`); `S#` = escenario de sensibilidad; `V#` = verificación de una fuente (`docs/verificacion_fuentes.md`); `D#` = decisión (`docs/DECISIONES.md`).

## 16. Glosario
- **Construcción:** huella catastral de una edificación (una fila de la capa); no es un edificio completo ni un predio.
- **Estrato moda:** el estrato con más lados de manzana en un barrio; se asigna a todas sus construcciones.
- **Lados de manzana:** unidad con la que el DAPM mide el estrato (un lado de manzana tiene un estrato).
- **Proxy satelital:** medida indirecta del daño: cambio de textura entre dos imágenes de satélite sobre la huella de la construcción; no es una inspección técnica ni una evaluación estructural.
- **Evaluación estructural (ATC-20):** inspección técnica en sitio, hecha por la Alcaldía sobre predios, que los clasifica con sticker rojo (inseguro), amarillo (uso restringido) o verde. No es nuestro indicador ni usamos sus datos por predio.
- **Intervalo de Wilson:** rango de valores compatibles con una proporción observada (95 %).
- **Intervalo de Newcombe:** el equivalente para la diferencia entre dos proporciones.
- **Mantel-Haenszel:** razón de tasas ajustada por una variable de estratificación (aquí, la comuna).
- **Spearman:** correlación entre los rangos de dos variables.
- **Huérfano:** fila de una tabla que no encuentra pareja en el JOIN; se conserva en un archivo aparte.
- **Snapshot:** copia fechada (UTC) de lo descargado; no se sobrescribe.
- **Medallion:** organización por capas (Bronze crudo, Silver limpio, Gold listo para análisis).

## 17. Trabajo futuro y atribución
**Trabajo futuro.** Incorporar la amenaza sísmica oficial para cubrir KR2; ampliar la cobertura a la Comuna 2 y a las demás comunas ausentes; comparar el proxy satelital con las inspecciones ATC-20 de la Alcaldía; repetir el análisis con un estrato actualizado (el de 2015 puede estar desfasado).

**Atribución.** Capa de impacto satelital: Fondo Adaptación, catálogo datos.gov.co `5vy8-gpw8` (CC BY 4.0 según el catálogo; consulta del 15-oct-2026). Estratificación por barrio 2015: DAPM Cali, datos.cali.gov.co (consulta del 15-oct-2026). Polígonos de barrios: IDESC / DAPM Cali (consulta del 15-oct-2026). Evento: USGS `{ev.id}` (consulta del 15-oct-2026). Contexto externo: El País Cali, 11-oct-2026.
"""
    (ROOT / "README.md").write_text(txt, encoding="utf-8", newline="\n")
    print("README.md generado")


if __name__ == "__main__":
    main()
