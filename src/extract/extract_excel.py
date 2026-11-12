"""Extraccion del CSV de estrato por barrio hacia Bronze (archivo original intacto)."""
import pandas as pd
import requests

from src.common import (ROOT, latest_snapshot_dir, load_config, manifest_for,
                        save_bronze, snapshot_name, user_agent, verify_files)
from src.logger import get_logger

log = get_logger(__name__)

SRC = "estrato_barrio"
BASE = "data/bronze/tabular/estrato_barrio"


def read_csv_raw(path):
    """Lee solo para inspección: dtype=str, prueba utf-8 y luego latin-1; no transforma nada."""
    for enc in ("utf-8", "latin-1"):
        try:
            return pd.read_csv(path, dtype=str, encoding=enc, keep_default_na=False), enc
        except UnicodeDecodeError:
            continue
    raise ValueError(f"no se pudo leer {path}")


def leer_tabular_raw(origen, nombre=None):
    """Lee CSV o Excel (.xlsx) solo para inspección, con dtype=str; origen puede ser una ruta o un buffer (con nombre)."""
    nombre = str(nombre or origen).lower()
    if nombre.endswith((".xlsx", ".xlsm")):
        return pd.read_excel(origen, dtype=str, keep_default_na=False, engine="openpyxl"), "excel"
    if hasattr(origen, "read"):
        return pd.read_csv(origen, dtype=str, keep_default_na=False), "csv"
    return read_csv_raw(origen)


def _filas(contenido, nombre):
    """Filas de datos de lo descargado: saltos de línea en CSV; filas de la primera hoja en Excel."""
    if nombre.lower().endswith((".xlsx", ".xlsm")):
        import io
        from openpyxl import load_workbook
        return max(load_workbook(io.BytesIO(contenido), read_only=True).worksheets[0].max_row - 1, 0)
    return max(contenido.count(b"\n") - 1, 0)


def _bajar(url, cfg):
    h = cfg["http"]
    session = requests.Session()
    session.headers["User-Agent"] = user_agent()
    try:
        # timeout: evita colgarse si datos.cali.gov.co no responde
        return session.get(url, timeout=h["timeout_s"])
    finally:
        session.close()


def extract_estrato(refresh=False):
    """Descarga el CSV principal (respaldo solo si falla) y lo guarda byte a byte."""
    cfg = load_config()
    if manifest_for(SRC) and not refresh:
        if verify_files(manifest_for(SRC)):
            log.info("%s: ya existe, sha256 coincide", SRC)
        return
    fuentes = cfg["sources"]
    intentos = [("estrato_barrio", SRC), ("area_barrios", "area_barrios")]
    for clave, sid in intentos:
        url = fuentes[clave]["url"]
        r = _bajar(url, cfg)
        if r.status_code == 200 and not r.content.lstrip().startswith(b"<"):
            nombre = url.rsplit("/", 1)[-1]
            ruta = f"{BASE if sid == SRC else 'data/bronze/tabular/' + sid}/{snapshot_name()}/{nombre}"
            filas = _filas(r.content, nombre)
            save_bronze(r.content, ruta, sid, url, {}, r.status_code, filas)
            log.info("%s: %s filas, %s bytes", sid, filas, len(r.content))
            return
        log.warning("%s falló (HTTP %s); se prueba el respaldo", clave, r.status_code)
    raise RuntimeError("ninguna fuente CSV respondió")


def latest_csv(base=BASE):
    snap = latest_snapshot_dir(base)
    return next(snap.glob("*.csv"))
