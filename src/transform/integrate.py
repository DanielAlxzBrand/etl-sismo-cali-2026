"""Integracion Silver: JOIN construcciones <-> estrato por barrio, huerfanos, validacion de llave y reporte de calidad."""
import json
import re
import time
from difflib import SequenceMatcher

import pandas as pd

from src.common import ROOT, load_config, registrar_regla
from src.extract.extract_api import load_edificaciones_raw, load_poligonos_raw
from src.extract.extract_excel import latest_csv, read_csv_raw
from src.logger import get_logger
from src.transform.clean_api import limpiar_construcciones
from src.transform.clean_excel import LADOS, limpiar_estrato
from src.transform.keys import normalize_key

log = get_logger(__name__)


def _csv(df, ruta):
    """Escritura determinista: UTF-8, saltos LF, sin índice ni fechas de ejecución."""
    p = ROOT / ruta
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(p, index=False, encoding="utf-8", lineterminator="\n")


def _pct(num, den):
    return {"num": int(num), "den": int(den), "pct": round(num / den, 6) if den else None}


def agregar_estrato(m, umbral):
    """H11: conteos por estrato (solo construcciones con datos) y bandera de muestra baja."""
    con = m[m.estrato.notna() & ~m.sin_datos]
    g = con.groupby("estrato").agg(n=("objectid", "size"), k=("severo_estricto", "sum"))
    m["n_con_datos_estrato"] = m.estrato.map(g.n).astype("Int64")
    m["n_severos_estrato"] = m.estrato.map(g.k).astype("Int64")
    m["muestra_baja"] = pd.array((m.n_severos_estrato < umbral).where(m.n_severos_estrato.notna()), dtype="boolean")
    return m


def validar_llave(m, sim_min):
    """H18: compara el nombre del CSV con el nombre dominante del polígono por cada código derivado."""
    filas = []
    for cod, d in m[m.cruza_llave].groupby("codigo_barrio"):
        nombres = d.nombre_poligono.dropna().value_counts()
        pol = sorted(nombres.items(), key=lambda t: (-t[1], t[0]))[0][0] if len(nombres) else None
        csv_nombre = d.nombre_barrio_csv.iloc[0]
        sim = SequenceMatcher(None, normalize_key(csv_nombre), normalize_key(pol)).ratio() if pol else 0.0
        cp = d.coincide_poligono.dropna()
        filas.append({"codigo_barrio": cod, "n_construcciones": len(d), "nombre_csv": csv_nombre, "nombre_poligono": pol,
                      "similitud": round(sim, 4), "pct_coincide_poligono": round(float(cp.mean()), 4) if len(cp) else None,
                      "nombre_validado": sim >= sim_min})
    t = pd.DataFrame(filas)
    return t.sort_values("codigo_barrio", key=lambda s: s.astype(int)).reset_index(drop=True)


def escribir_validacion_llave(t, resumen, sim_min, sin_csv):
    """Genera docs/validacion_llave.md (determinista)."""
    def fila(r):
        v = "coincide" if r.nombre_validado else "NO coincide"
        pc = "—" if pd.isna(r.pct_coincide_poligono) else f"{r.pct_coincide_poligono * 100:.1f} %"
        return f"| {r.codigo_barrio} | {r.n_construcciones} | {r.nombre_csv} | {r.nombre_poligono} | {r.similitud:.2f} | {pc} | {v} |"
    cab = "| código | n construcciones | nombre CSV 2015 | nombre polígono 2026 (dominante) | similitud | % coincide polígono | veredicto |\n|---|---|---|---|---|---|---|"
    cero = t[t.pct_coincide_poligono == 0]
    L = ["# Validación semántica de la llave (H18)", "",
         f"Para cada código derivado `int(COMUNA)*100 + int(BARRIO)` se compara el nombre del barrio en el CSV de estrato (2015) con el nombre del polígono 2026 que domina entre sus construcciones (difflib.SequenceMatcher sobre `normalize_key`, umbral de similitud ≥ {sim_min}).",
         "", f"- Códigos validados: **{int(t.nombre_validado.sum())} de {len(t)}**.",
         f"- Construcciones en códigos con nombre validado: **{resumen['pct_nombre_validado']['global']['pct'] * 100:.2f} %** ({resumen['pct_nombre_validado']['global']['num']} de {resumen['pct_nombre_validado']['global']['den']}).",
         f"- Entre las construcciones cuyo código coincide con el polígono: {resumen['pct_nombre_validado']['coincide_poligono_true']['pct'] * 100:.2f} %; entre las que no coinciden: {resumen['pct_nombre_validado']['coincide_poligono_false']['pct'] * 100:.2f} %.",
         f"- **llave_confianza = {resumen['llave_confianza']}** (alta ≥ 0,90; media 0,80-0,90; baja < 0,80).", "",
         "**Qué NO demuestra:** que el nombre coincida no prueba que la llave sea perfecta (dos barrios distintos pueden llamarse parecido y un barrio puede haberse renombrado entre 2015 y 2026). Tampoco prueba lo contrario cuando no coincide. No se cambió la llave ni se crearon alias para mejorar estas cifras.", "",
         "**Casos a revisar a mano:** el código 2098 (\"Venezuela Urb. Cañaveralejo\" en el CSV frente a \"Venezuela\" en el polígono, similitud 0,51) es el más dudoso: puede ser un barrio distinto o solo un nombre más largo. Los demás códigos sin validar (1011, 1802, 1898, 1905, 1922, 1999) difieren sobre todo por prefijos o abreviaturas (\"Barrio\", \"Sector\", \"Urb.\", \"Unidad Res.\") y son probables falsos negativos de la métrica de texto; no se tocó la métrica ni se crearon alias.", "",
         f"## Códigos de H13 destacados: 0 % de coincidencia con el polígono ({len(cero) + len(sin_csv)})", "",
         f"{len(cero)} están en la tabla; los otros {len(sin_csv)} ({', '.join(f'{c} con {n} construcciones' for c, n in sin_csv)}) no existen en el CSV 2015 y por eso son huérfanos, no aparecen en la tabla.", "", cab] + [fila(r) for r in cero.itertuples()]
    L += ["", f"## Todos los códigos ({len(t)})", "", cab] + [fila(r) for r in t.itertuples()]
    (ROOT / "docs" / "validacion_llave.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")


def escribir_reglas(reglas):
    """Genera docs/reglas_silver.md a partir del registro de reglas (determinista)."""
    L = ["# Reglas de Silver", "",
         "Cada regla cita el hallazgo de `docs/hallazgos_eda.md` que la justifica. La unidad de análisis son las **construcciones** (huellas catastrales).", "",
         "| regla | hallazgo | columnas | filas afectadas | justificación |", "|---|---|---|---|---|"]
    for r in sorted(reglas, key=lambda r: r["id"]):
        L.append(f"| {r['id']} | {r['hallazgo']} | {r['columnas']} | {r['filas_afectadas']} | {r['justificacion']} |")
    L += ["", "**Cómo leer \"filas afectadas\":** cuenta filas (no celdas) salvo donde se indica. R01 = 0 porque solo fija el identificador y no modifica filas; "
          "R02 = 2 filas (4 celdas: COMUNA y BARRIO en blanco en 2 construcciones); R03 = 9 pares (18 filas con geometría idéntica); "
          "R10 = 5146 porque descarta columnas y afecta a todas las filas."]
    (ROOT / "docs" / "reglas_silver.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")


def hallazgos_faltantes(reglas):
    """Devuelve los H# citados por las reglas que no existen en docs/hallazgos_eda.md."""
    txt = (ROOT / "docs" / "hallazgos_eda.md").read_text(encoding="utf-8")
    existentes = set(re.findall(r"\| (H\d+) \|", txt))
    citados = {h for r in reglas for h in re.findall(r"H\d+", r["hallazgo"])}
    return sorted(citados - existentes)


def run_transform():
    """Silver completo: limpia ambas fuentes, une por codigo_barrio y escribe CSV, huérfanos y reporte."""
    cfg = load_config()
    P = cfg["paths_silver"]
    reglas = []
    t0 = time.perf_counter()
    log.info("Inicio etapa transform")
    raw, geoms = load_edificaciones_raw()
    csv_raw, enc = read_csv_raw(latest_csv())
    log.info("Entrada: %s construcciones y %s filas del CSV de estrato", len(raw), len(csv_raw))
    assert enc == "utf-8", f"el CSV debía leerse como UTF-8 (H7), se leyó {enc}"
    cons = limpiar_construcciones(raw, geoms, load_poligonos_raw(), reglas)
    barr, resumen, info = limpiar_estrato(csv_raw, reglas)
    assert cons.objectid.is_unique and barr.codigo_barrio.is_unique
    # llave del JOIN: codigo_barrio = int(COMUNA)*100 + int(BARRIO) (H5); LEFT para conservar las construcciones sin estrato
    der = barr[["codigo_barrio", "barrio", "estrato", "pureza_estrato"]].rename(columns={"barrio": "nombre_barrio_csv"})
    m = cons.merge(der, on="codigo_barrio", how="left", validate="m:1")
    m["cruza_llave"] = m.nombre_barrio_csv.notna()
    registrar_regla(reglas, "R16", "H5, H6", "codigo_barrio", m.cruza_llave.sum(), "LEFT JOIN construcciones <- estrato por barrio; huérfanos guardados, no descartados.")
    m = agregar_estrato(m, cfg["silver"]["muestra_baja_severos"])
    registrar_regla(reglas, "R17", "H11", "n_con_datos_estrato, n_severos_estrato, muestra_baja", m.estrato.notna().sum(),
                    "Conteos por estrato sobre construcciones con datos satelitales y bandera de muestra baja (< 30 severos).")
    val = validar_llave(m, cfg["llave"]["similitud_nombre_min"])
    m["nombre_validado"] = pd.array(m.codigo_barrio.map(dict(zip(val.codigo_barrio, val.nombre_validado))), dtype="boolean")
    registrar_regla(reglas, "R18", "H18", "nombre_validado", m.nombre_validado.notna().sum(),
                    "Validación semántica de la llave (nombre CSV vs nombre de polígono); no cambia la llave.")
    # huérfanos
    ol = m[~m.cruza_llave].copy()
    ol["causa"] = ol.codigo_barrio.map(lambda c: "COMUNA o BARRIO en blanco" if pd.isna(c) else "código ausente del CSV 2015")
    ol = ol[["objectid", "comuna", "barrio", "codigo_barrio", "codigo_poligono", "nombre_poligono", "clase_dano", "causa"]]
    orr = barr[~barr.codigo_barrio.isin(set(m.codigo_barrio.dropna()))]
    cols_int = ["objectid", "comuna", "barrio", "codigo_barrio", "nombre_barrio_csv", "cruza_llave", "estrato", "pureza_estrato", "n_con_datos_estrato",
                "n_severos_estrato", "muestra_baja", "npisos", "npisos_cero", "indice_escombros", "estado_estructural", "clase_dano", "sin_datos",
                "severo_estricto", "dano_visible", "geom_duplicada", "lon", "lat", "codigo_poligono", "nombre_poligono", "coincide_poligono",
                "nombre_validado"]
    m = m[cols_int].sort_values("objectid").reset_index(drop=True)
    _csv(cons, P["construcciones"]); _csv(barr, P["estrato_barrio"]); _csv(m, P["integrated"])
    _csv(ol, P["orphans_left"]); _csv(orr, P["orphans_right"])
    # reporte de calidad (sin timestamps de ejecución)
    con = m[~m.sin_datos]
    nv = m[m.nombre_validado.notna()]
    def nv_pct(d):
        return _pct(int(d.nombre_validado.sum()), len(d))
    pct_nv = {"global": nv_pct(nv), "coincide_poligono_true": nv_pct(nv[nv.coincide_poligono == True]),  # noqa: E712
              "coincide_poligono_false": nv_pct(nv[nv.coincide_poligono == False])}  # noqa: E712
    g = pct_nv["global"]["pct"]
    conf = "alta" if g >= cfg["llave"]["confianza_alta"] else ("media" if g >= cfg["llave"]["confianza_media"] else "baja")
    cp = m.coincide_poligono.dropna()
    com = m.comuna.fillna("sin_comuna")
    def por(clave):
        out = {}
        for k, d in m.groupby(clave, dropna=True):
            dd = d[~d.sin_datos]
            out[str(k)] = {"n": len(d), "sin_datos": int(d.sin_datos.sum()), "pct_sin_datos": round(d.sin_datos.mean(), 6),
                           "n_con_datos": len(dd), "k_severos": int(dd.severo_estricto.sum())}
        return out
    nulos_antes = {c: int(raw[c].isna().sum() + (raw[c].astype("string").str.strip() == "").fillna(False).sum()) for c in raw.columns}
    umbral = cfg["thresholds"]["join_coverage_min"]
    cob = _pct(int(m.cruza_llave.sum()), len(m))
    rep = {
        "fuentes": {"construcciones": {"filas_entrada": len(raw), "filas_salida": len(cons)},
                    "estrato_barrio": {"filas_entrada": info["filas_entrada"], "filas_resumen_separadas": info["filas_resumen"], "filas_salida": len(barr)},
                    "integrado": {"filas_salida": len(m)}},
        "duplicados_eliminados_por_regla": {"objectid": next(r["filas_afectadas"] for r in reglas if r["id"] == "R01"),
                                            "codigo_barrio_csv": info["duplicados_codigo"], "llave_catastral": 0},
        "duplicados_marcados": {"geom_duplicada_filas": int(m.geom_duplicada.sum())},
        "nulos_antes_bronze": nulos_antes,
        "nulos_despues_construcciones": {c: int(cons[c].isna().sum()) for c in cons.columns},
        "nulos_despues_estrato": {c: int(barr[c].isna().sum()) for c in barr.columns},
        "tratamiento": {"COMUNA/BARRIO": "blancos a nulo (H4)", "Indice_Escombros": "no se imputa; nulo = sin datos satelitales (H9)",
                        "NPISOS": "entero nullable sin imputar (H16)", "lados_e1..6/sin_vivienda": "guion y vacío = 0 (H7)",
                        "estrato": "nulo si la moda no es 1-6 (H8)", "severo_estricto/dano_visible": "nulos si sin_datos (H10)"},
        "cobertura_llave": cob,
        "cobertura_estrato_valido": _pct(int(m.estrato.notna().sum()), len(m)),
        "umbral_cobertura_join": umbral, "resultado_umbral": "pasa" if cob["pct"] >= umbral else "no pasa",
        "huerfanos": {"izquierda": len(ol), "causas": ol.causa.value_counts().sort_index().to_dict(),
                      "izquierda_detalle": ol.drop(columns=["clase_dano"]).astype(object).where(ol.drop(columns=["clase_dano"]).notna(), None).to_dict("records"),
                      "derecha_barrios_sin_construcciones": len(orr)},
        "sin_estrato_valido": {"total": int(m.estrato.isna().sum()), "sin_llave": int((~m.cruza_llave).sum()),
                               "moda_NR": int((m.cruza_llave & m.estrato.isna()).sum())},
        "sin_datos": {"total": _pct(int(m.sin_datos.sum()), len(m)), "por_estrato": por("estrato"), "por_comuna": por(com)},
        "severos": {"total": {"n_con_datos": len(con), "k_severos": int(con.severo_estricto.sum()), "k_dano_visible": int(con.dano_visible.sum())},
                    "por_estrato": {k: {"n": v["n_con_datos"], "k": v["k_severos"]} for k, v in por("estrato").items()},
                    "por_comuna": {k: {"n": v["n_con_datos"], "k": v["k_severos"]} for k, v in por(com).items()}},
        "pct_coincide_poligono": _pct(int(cp.sum()), len(cp)),
        "pct_nombre_validado": pct_nv, "llave_confianza": conf,
        "verificaciones_csv": {"vacios_tratados_como_cero": info["vacios_tratados_como_cero"], "camino_real": info["camino_real"]},
        "fechas_fuente": cfg["fechas"], "licencia_capa": cfg["licencia_capa"],
        "reglas_aplicadas": sorted(reglas, key=lambda r: r["id"]),
    }
    (ROOT / P["quality_report"]).write_text(json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    sc = m[~m.cruza_llave & m.codigo_barrio.notna()].groupby("codigo_barrio").agg(n=("objectid", "size"), pc=("coincide_poligono", "mean"))
    sin_csv = [(c, int(r.n)) for c, r in sc.iterrows() if r.pc == 0]
    escribir_validacion_llave(val, rep, cfg["llave"]["similitud_nombre_min"], sin_csv)
    escribir_reglas(reglas)
    falt = hallazgos_faltantes(reglas)
    log.info("Salida: construcciones=%s barrios=%s integrado=%s | cobertura de llave=%.4f%% (%s) | huérfanos izquierda=%s derecha=%s",
             len(cons), len(barr), len(m), cob["pct"] * 100, rep["resultado_umbral"], len(ol), len(orr))
    log.info("llave_confianza=%s (nombre validado %.2f%%) | hallazgos faltantes: %s", conf, g * 100, falt or "ninguno")
    if cob["pct"] < umbral + 0.05:
        log.warning("cobertura de llave %.4f cerca del umbral %.2f", cob["pct"], umbral)
    if len(ol):
        log.warning("%s construcciones sin llave en el JOIN (%s)", len(ol), "; ".join(f"{k}: {v}" for k, v in rep["huerfanos"]["causas"].items()))
    if rep["duplicados_marcados"]["geom_duplicada_filas"]:
        log.warning("%s construcciones con geometría idéntica a otra (marcadas, no eliminadas)", rep["duplicados_marcados"]["geom_duplicada_filas"])
    if conf != "alta":
        log.warning("llave_confianza=%s", conf)
    if falt:
        log.warning("reglas que citan hallazgos inexistentes: %s", falt)
    log.info("Fin etapa transform (%.2f s)", time.perf_counter() - t0)
