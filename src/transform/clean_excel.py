"""Limpieza Silver del CSV de estrato por barrio (UTF-8)."""
import re

import numpy as np
import pandas as pd

from src.common import registrar_regla
from src.transform.keys import codigo_csv

COLS = ["cod", "barrio"] + [f"lados_e{i}" for i in range(1, 7)] + ["sin_vivienda", "moda"]
LADOS = [f"lados_e{i}" for i in range(1, 7)]


def a_conteo(serie):
    """H7: guion y vacío = 0 lados; se quita la coma de miles."""
    s = serie.astype("string").str.replace(",", "", regex=False).str.strip()
    return pd.to_numeric(s.mask(s.isin(["", "-"]), "0"), errors="raise").astype("Int64")


def limpiar_estrato(raw, reglas):
    """Aplica H5-H8 y H14; devuelve (barrios, filas_resumen, info de verificación)."""
    df = raw.copy()
    df.columns = COLS
    n_in = len(df)
    df["cod_n"] = df.cod.map(codigo_csv)
    resumen = df[df.cod_n.isna()].copy()
    registrar_regla(reglas, "R11", "H6", "cod", len(resumen),
                    "Filas 'Comuna N' y 'Otros' (código '-') se separan; no entran al JOIN.")
    b = df[df.cod_n.notna()].copy()
    n_dup_cod = int(b.cod_n.duplicated(keep="first").sum())
    b = b.drop_duplicates("cod_n", keep="first")  # H6: un barrio por código; 0 duplicados en los datos actuales
    vacios = {c: b.loc[b[c].str.strip() == "", ["cod_n", "barrio"]].values.tolist() for c in ("lados_e1", "lados_e4")}
    n_vacios = sum(len(v) for v in vacios.values())
    num_cols = LADOS + ["sin_vivienda"]
    n_fmt = int(b[num_cols].apply(lambda s: s.str.strip().isin(["", "-"]) | s.str.contains(",", regex=False)).any(axis=1).sum())
    for c in num_cols:
        b[c] = a_conteo(b[c])
    registrar_regla(reglas, "R12", "H7", ", ".join(num_cols), n_fmt,
                    "Guion y vacío = 0 lados, coma de miles eliminada, columnas a entero.")
    nombre_antes = b.barrio.copy()
    b["barrio"] = b.barrio.str.strip().str.replace(r"\s+", " ", regex=True)
    registrar_regla(reglas, "R13", "H7", "barrio", int((nombre_antes != b.barrio).sum()),
                    "strip y espacios internos colapsados; el archivo se lee como UTF-8.")
    malos = b[b.barrio.str.contains("Ã|�", regex=True)]
    assert malos.empty, f"nombres con codificación dañada: {malos.barrio.tolist()}"
    moda = pd.to_numeric(b.moda.str.strip(), errors="coerce")
    b["estrato"] = moda.where(moda.between(1, 6)).astype("Int64")
    registrar_regla(reglas, "R14", "H8", "estrato", int(b.estrato.isna().sum()),
                    "estrato = moda solo si es 1-6; 'NR' queda nulo y no se convierte en estrato.")
    total = b[LADOS].sum(axis=1)
    b["lados_total"] = total
    b["pureza_estrato"] = (b[LADOS].max(axis=1) / total.where(total > 0)).astype(float).round(6)
    registrar_regla(reglas, "R15", "H14", "pureza_estrato", int(b.pureza_estrato.notna().sum()),
                    "max(lados 1..6)/suma(lados 1..6) sin 'Sin vivienda'; nula si el total es 0.")
    b = b.rename(columns={"cod_n": "codigo_barrio", "moda": "estrato_moda_original"})
    b = b[["codigo_barrio", "barrio"] + LADOS + ["sin_vivienda", "lados_total", "estrato_moda_original", "estrato", "pureza_estrato"]]
    b = b.sort_values("codigo_barrio", key=lambda s: s.astype(int)).reset_index(drop=True)
    # verificación: tratar los vacíos como 0 no debe cambiar el estrato moda
    arg = b[LADOS].to_numpy().argmax(axis=1) + 1
    chequeo = []
    for c, filas in vacios.items():
        for cod, nombre in filas:
            r = b[b.codigo_barrio == cod].iloc[0]
            chequeo.append({"columna": c, "codigo_barrio": cod, "barrio": r.barrio, "estrato_moda": None if pd.isna(r.estrato) else int(r.estrato),
                            "estrato_con_mas_lados": int(arg[r.name]), "lados_total": int(r.lados_total),
                            "sin_cambio": bool(pd.isna(r.estrato) or int(r.estrato) == int(arg[r.name]))})
    cr = b[b.barrio.str.contains("Camino Real", case=False)][["codigo_barrio", "barrio"]]
    info = {"vacios_tratados_como_cero": chequeo, "camino_real": cr.values.tolist(), "n_vacios": n_vacios,
            "filas_entrada": n_in, "filas_resumen": len(resumen), "duplicados_codigo": n_dup_cod}
    return b, resumen, info
