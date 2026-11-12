"""Carga Silver integrado, Gold y KPI a SQLite (data/gold/etl_sismo.db)."""
import sqlite3
import time

import pandas as pd

from src.common import ROOT, load_config
from src.logger import get_logger

log = get_logger(__name__)

DB = "data/gold/etl_sismo.db"
TABLAS = {"silver_integrated": "paths_silver:integrated", "gold_final": "data/gold/gold_final.csv",
          "kpis_gold": "data/gold/kpis_gold.csv", "kpis_sensibilidad": "data/gold/kpis_sensibilidad.csv"}
STR = {"comuna": str, "barrio": str, "codigo_barrio": str, "codigo_poligono": str}


def _ruta(valor, cfg):
    if valor.startswith("paths_silver:"):
        return cfg["paths_silver"][valor.split(":")[1]]
    return valor


def load_to_sqlite():
    """Reemplaza las tablas de la base; la conexión se cierra siempre."""
    t0 = time.perf_counter()
    log.info("Inicio etapa load")
    cfg = load_config()
    # conn = None antes del try: si connect() falla, el finally no lanza NameError
    conn = None
    try:
        conn = sqlite3.connect(ROOT / DB)
        for nombre, ruta in TABLAS.items():
            df = pd.read_csv(ROOT / _ruta(ruta, cfg), dtype=STR)
            df.to_sql(nombre, conn, if_exists="replace", index=False)
            log.info("%s: %s filas cargadas", nombre, len(df))
        conn.commit()
    except (sqlite3.Error, OSError) as e:
        log.exception("error al cargar SQLite: %s", e)
        raise
    finally:
        if conn is not None:
            conn.close()
    log.info("Fin etapa load (%.2f s)", time.perf_counter() - t0)
