"""Construccion de Gold: construcciones integradas, KPI con intervalos, cotas y sensibilidades (solo lee Silver)."""
import math
import random
import time

import pandas as pd

from src.common import ROOT, load_config
from src.logger import get_logger

log = get_logger(__name__)

Z = 1.96
BOOL = ["cruza_llave", "npisos_cero", "sin_datos", "severo_estricto", "dano_visible", "geom_duplicada", "coincide_poligono",
        "nombre_validado", "muestra_baja"]
STR = ["comuna", "barrio", "codigo_barrio", "codigo_poligono"]
FUENTE = ("Capa ArcGIS Impacto_Satelital_en_Edificaciones_por_Terremoto_Cali_2026 (datos.gov.co 5vy8-gpw8) + "
          "estrato por barrio 2015 (datos.cali.gov.co); Silver de este proyecto")
EXPUESTO, REFERENCIA = (3, 4, 5), (1, 2)


def _p(x):
    """Porcentaje con coma decimal para las notas."""
    return f"{x * 100:.1f}".replace(".", ",") + " %"


def wilson(k, n, z=Z):
    """Intervalo de Wilson al 95 % para k/n; (nan, nan) si n = 0."""
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def newcombe(k1, n1, k0, n0):
    """Diferencia de tasas p1 - p0 con intervalo de Newcombe (scores híbridos de Wilson)."""
    p1, p0 = k1 / n1, k0 / n0
    l1, u1 = wilson(k1, n1)
    l0, u0 = wilson(k0, n0)
    d = p1 - p0
    return d, d - math.sqrt((p1 - l1) ** 2 + (u0 - p0) ** 2), d + math.sqrt((u1 - p1) ** 2 + (p0 - l0) ** 2)


def mantel_haenszel(d, col):
    """RR de Mantel-Haenszel (estratos 3-5 vs 1-2) ajustado por comuna; devuelve (rr, comunas usadas, excluidas, totales a/c/n1/n0)."""
    num = den = 0.0
    usadas, excluidas = [], []
    tot = {"a": 0, "c": 0, "n1": 0, "n0": 0}
    for c, g in d[d.comuna.notna() & ~d.sin_datos].groupby("comuna"):  # n1, n0 = tamaños CON datos satelitales
        e = g[g.estrato.isin(EXPUESTO)]
        r = g[g.estrato.isin(REFERENCIA)]
        n1, n0 = len(e), len(r)
        if n1 == 0 or n0 == 0:
            excluidas.append(c)
            continue
        a, cc, N = int(e[col].sum()), int(r[col].sum()), n1 + n0
        for key, v in (("a", a), ("c", cc), ("n1", n1), ("n0", n0)):
            tot[key] += v
        num += a * n0 / N
        den += cc * n1 / N
        usadas.append(c)
    return (num / den if den else float("nan")), usadas, excluidas, tot


def spearman_perm(x, y, n_perm=5000, seed=0):
    """Spearman (pandas) y p-valor de permutación bilateral con random.Random(seed): (1 + #{|rho*| >= |rho|}) / (n_perm + 1)."""
    df = pd.DataFrame({"x": list(x), "y": list(y)})
    rho = df.corr(method="spearman").iloc[0, 1]
    rx, ry = df.x.rank().tolist(), df.y.rank().tolist()
    n = len(rx)
    mx = sum(rx) / n
    sxx = sum((a - mx) ** 2 for a in rx)
    my = sum(ry) / n
    syy = sum((b - my) ** 2 for b in ry)
    rng = random.Random(seed)
    ge = 0
    for _ in range(n_perm):
        rng.shuffle(ry)
        r = sum((a - mx) * (b - my) for a, b in zip(rx, ry)) / math.sqrt(sxx * syy)
        if abs(r) >= abs(rho) - 1e-12:
            ge += 1
    return float(rho), round((1 + ge) / (n_perm + 1), 4)


def leer_integrado():
    """Lee silver_integrated.csv con tipos explícitos."""
    P = load_config()["paths_silver"]
    return pd.read_csv(ROOT / P["integrated"], dtype={**{c: "str" for c in STR}, **{c: "boolean" for c in BOOL}})


def _g(d, col, n_baja):
    """k, n, n_sin_datos y métricas de un grupo (denominador = construcciones con datos satelitales)."""
    con = d[~d.sin_datos]
    k, n, sd = int(con[col].sum()), len(con), int(d.sin_datos.sum())
    lo, hi = wilson(k, n)
    tot = n + sd
    return {"numerador": k, "denominador": n, "valor": k / n if n else float("nan"), "ic95_inf": lo, "ic95_sup": hi,
            "n_sin_datos": sd, "pct_sin_datos": sd / tot if tot else float("nan"), "muestra_baja": k < n_baja,
            "cota_inf": k / tot if tot else float("nan"), "cota_sup": (k + sd) / tot if tot else float("nan")}


def _frase(lo1, hi1, lo0, hi0, dlo, dhi):
    """Regla de redacción: no afirmar ausencia de efecto."""
    if (dlo <= 0 <= dhi) or (lo1 <= hi0 and lo0 <= hi1):
        return "con este proxy y esta muestra no se detecta diferencia"
    return "los intervalos no se solapan y la diferencia excluye 0 (descriptivo; no implica causa)"


def calcular(df, col, n_baja):
    """K1, K2 y K6 sobre un subconjunto de construcciones y un indicador (severo_estricto o dano_visible)."""
    filas = []
    e = df[df.estrato.notna()]
    for s in range(1, 7):
        m = _g(e[e.estrato == s], col, n_baja)
        filas.append({"kpi_id": "K1", "nombre": "Tasa por estrato", "grupo": f"estrato_{s}", **m, "nota": ""})
    exp, ref = e[e.estrato.isin(EXPUESTO)], e[e.estrato.isin(REFERENCIA)]
    gx, gr = _g(exp, col, n_baja), _g(ref, col, n_baja)
    filas.append({"kpi_id": "K2", "nombre": "Tasa estratos 3-5", "grupo": "estratos_3-5", **gx, "nota": "E6 queda fuera de K2"})
    filas.append({"kpi_id": "K2", "nombre": "Tasa estratos 1-2", "grupo": "estratos_1-2", **gr, "nota": ""})
    vacio = {k: float("nan") for k in ("numerador", "denominador", "ic95_inf", "ic95_sup", "n_sin_datos", "pct_sin_datos", "cota_inf", "cota_sup")}
    ok = gr["numerador"] > 0 and gr["denominador"] > 0 and gx["denominador"] > 0
    razon = gx["valor"] / gr["valor"] if ok else float("nan")
    filas.append({"kpi_id": "K2", "nombre": "Razón de tasas (3-5 / 1-2)", "grupo": "razon_3-5_vs_1-2", **vacio, "valor": razon, "muestra_baja": gr["muestra_baja"],
                  "nota": "vacío si la tasa de 1-2 es 0" if not ok else ""})
    if gx["denominador"] and gr["denominador"]:
        dif, dlo, dhi = newcombe(gx["numerador"], gx["denominador"], gr["numerador"], gr["denominador"])
        frase = _frase(gx["ic95_inf"], gx["ic95_sup"], gr["ic95_inf"], gr["ic95_sup"], dlo, dhi)
    else:
        dif = dlo = dhi = float("nan"); frase = ""
    filas.append({"kpi_id": "K2", "nombre": "Diferencia de tasas (3-5 menos 1-2), Newcombe", "grupo": "diferencia_3-5_menos_1-2", **vacio,
                  "valor": dif, "ic95_inf": dlo, "ic95_sup": dhi, "muestra_baja": gr["muestra_baja"], "nota": frase})
    rr, us, ex, tot = mantel_haenszel(e, col)
    if len(us) == 1:
        aviso = (f"; no es interpretable: descansa solo en la Comuna {us[0]} ({tot['n1']} construcciones expuestas con {tot['a']} severas y "
                 f"{tot['n0']} de referencia con {tot['c']} severas); el estrato está confundido con la ubicación")
    elif not us:
        aviso = "; no es interpretable: ninguna comuna tiene ambos grupos"
    else:
        aviso = ""
    filas.append({"kpi_id": "K2", "nombre": "Razón de tasas ajustada por comuna (Mantel-Haenszel)", "grupo": "razon_MH_ajustada_comuna", **vacio,
                  "valor": rr, "muestra_baja": gr["muestra_baja"],
                  "nota": f"comunas usadas: {','.join(us)}; excluidas por no tener ambos grupos: {','.join(ex) or 'ninguna'}{aviso}"})
    for c, g in df[df.comuna.notna()].groupby("comuna"):
        m = _g(g, col, n_baja)
        filas.append({"kpi_id": "K6", "nombre": "Tasa por comuna", "grupo": f"comuna_{c}", **m, "nota": ""})
    return filas


def kpis_barrio(d, min_n):
    """Tasa de severo_estricto y estrato moda por barrio (solo barrios con >= min_n construcciones con datos)."""
    con = d[~d.sin_datos & d.codigo_barrio.notna()]
    b = con.groupby("codigo_barrio").agg(n=("objectid", "size"), k=("severo_estricto", "sum"), estrato=("estrato", "first")).reset_index()
    b["tasa"] = b.k / b.n
    return b


def construir():
    """Calcula todo Gold en memoria: (gold_final, kpis_gold, kpis_sensibilidad)."""
    cfg = load_config()
    n_baja, min_n = cfg["silver"]["muestra_baja_severos"], cfg["thresholds"]["min_edificios_por_barrio"]
    fecha = cfg["fechas"]["fecha_edicion_capa"]
    d = leer_integrado()
    gold = d.sort_values("objectid").reset_index(drop=True)
    assert gold.objectid.is_unique
    base = calcular(gold, "severo_estricto", n_baja)
    cc = gold[~gold.sin_datos & gold.comuna.notna()]
    Nc, Sc = len(cc), int(cc.severo_estricto.sum())
    for f in base:
        if f["kpi_id"] == "K6":
            sub = cc[cc.comuna == f["grupo"].split("_")[1]]
            f["nota"] = (f"{_p(int(sub.severo_estricto.sum()) / Sc)} de los severos y {_p(len(sub) / Nc)} de las construcciones con datos "
                         f"(base: comunas asignadas, {Sc} severos y {Nc} construcciones)")
    kp = [{**f, "fecha_corte": fecha, "fuente": FUENTE} for f in base if f["kpi_id"] in ("K1", "K2")]
    # K3: concentración del daño severo en los 10 barrios con más severos (empates por código ascendente)
    sev = gold[(gold.severo_estricto == True) & gold.codigo_barrio.notna()]  # noqa: E712
    c = sev.groupby("codigo_barrio").size().rename("k").reset_index()
    c = c.sort_values(["k", "codigo_barrio"], key=lambda s: (-s if s.name == "k" else s.astype(int))).head(10)
    cd = gold[~gold.sin_datos & gold.codigo_barrio.notna()]
    en_top = int(cd.codigo_barrio.isin(set(c.codigo_barrio)).sum())
    kp.append({"kpi_id": "K3", "nombre": "Concentración del daño severo en los 10 barrios con más severos", "grupo": "top10_barrios",
               "numerador": int(c.k.sum()), "denominador": len(sev), "valor": int(c.k.sum()) / len(sev), "muestra_baja": False,
               "nota": ("códigos:severos " + "; ".join(f"{a}:{b}" for a, b in zip(c.codigo_barrio, c.k)) +
                    f"; esos barrios reúnen {_p(en_top / len(cd))} de las construcciones con datos ({en_top} de {len(cd)})"), "fecha_corte": fecha, "fuente": FUENTE})
    # K4: Spearman estrato moda vs tasa de severos por barrio
    b = kpis_barrio(gold, min_n)
    b = b[(b.n >= min_n) & b.estrato.notna()]
    rho, p = spearman_perm(b.estrato, b.tasa)
    kp.append({"kpi_id": "K4", "nombre": "Spearman estrato moda vs tasa de severos por barrio", "grupo": f"barrios_con_>={min_n}_construcciones_con_datos",
               "denominador": len(b), "valor": rho, "muestra_baja": False,
               "nota": f"n_barrios={len(b)}; p_permutacion={p} (5000 permutaciones, seed 0); descriptivo, no causal", "fecha_corte": fecha, "fuente": FUENTE})
    # K5: calidad del JOIN
    lk = gold[gold.cruza_llave == True]  # noqa: E712
    for g, num, den in (("cobertura_llave", int(gold.cruza_llave.sum()), len(gold)),
                        ("cobertura_estrato_valido", int(gold.estrato.notna().sum()), len(gold)),
                        ("pct_nombre_validado", int(lk.nombre_validado.sum()), len(lk))):
        kp.append({"kpi_id": "K5", "nombre": "Calidad del JOIN", "grupo": g, "numerador": num, "denominador": den, "valor": num / den,
                   "muestra_baja": False, "nota": "", "fecha_corte": fecha, "fuente": FUENTE})
    kp += [{**f, "fecha_corte": fecha, "fuente": FUENTE} for f in base if f["kpi_id"] == "K6"]
    cols = ["kpi_id", "nombre", "valor", "numerador", "denominador", "grupo", "fecha_corte", "fuente", "ic95_inf", "ic95_sup", "n_sin_datos",
            "pct_sin_datos", "muestra_baja", "cota_inf", "cota_sup", "nota"]
    k = pd.DataFrame(kp).reindex(columns=cols)
    # sensibilidades S0-S5 (K1, K2, K6)
    esc = [("S0", "base", gold, "severo_estricto"),
           ("S1", "nombre_validado = true (principal para la llave)", gold[gold.nombre_validado == True], "severo_estricto"),  # noqa: E712
           ("S2", "coincide_poligono = true (secundaria; no sustituye a S1)", gold[gold.coincide_poligono == True], "severo_estricto"),  # noqa: E712
           ("S3", "pureza_estrato >= 0,8", gold[gold.pureza_estrato >= 0.8], "severo_estricto"),
           ("S4", "dano_visible en lugar de severo_estricto (baja confianza)", gold, "dano_visible"),
           ("S5", "sin geom_duplicada", gold[gold.geom_duplicada == False], "severo_estricto")]  # noqa: E712
    sens = []
    for sid, nom, sub, col in esc:
        for f in calcular(sub, col, n_baja):
            sens.append({"escenario": sid, "kpi_id": f["kpi_id"], "grupo": f["grupo"], "k": f["numerador"], "n": f["denominador"],
                         "tasa": f["valor"], "ic95_inf": f["ic95_inf"], "ic95_sup": f["ic95_sup"],
                         "nota": (nom + ("; " + f["nota"] if f["nota"] else ""))})
    s = pd.DataFrame(sens)
    return gold, k, s


def _guardar(df, ruta):
    """Escritura determinista: UTF-8, LF, floats a 12 decimales, sin fechas de ejecución."""
    p = ROOT / ruta
    p.parent.mkdir(parents=True, exist_ok=True)
    df.round(12).to_csv(p, index=False, encoding="utf-8", lineterminator="\n")


def run_gold():
    """Etapa Gold: escribe gold_final.csv, kpis_gold.csv y kpis_sensibilidad.csv."""
    cfg = load_config()
    t0 = time.perf_counter()
    log.info("Inicio etapa gold")
    gold, k, s = construir()
    assert len(gold) >= cfg["thresholds"]["gold_min_rows"], "Gold por debajo del mínimo"
    _guardar(gold, "data/gold/gold_final.csv")
    _guardar(k, "data/gold/kpis_gold.csv")
    _guardar(s, "data/gold/kpis_sensibilidad.csv")
    log.info("Entrada: silver_integrated con %s construcciones", len(gold))
    log.info("Salida: gold_final=%s filas | kpis_gold=%s filas (%s indicadores) | sensibilidades=%s filas", len(gold), len(k), k.kpi_id.nunique(), len(s))
    bajas = k[k.muestra_baja & k.kpi_id.isin(["K1", "K2", "K6"]) & k.numerador.notna()].grupo.tolist()
    if bajas:
        log.warning("muestra baja (< %s severos) en: %s", cfg["silver"]["muestra_baja_severos"], ", ".join(bajas))
    log.info("Fin etapa gold (%.2f s)", time.perf_counter() - t0)
