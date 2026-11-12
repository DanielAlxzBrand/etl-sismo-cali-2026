"""Extraccion de APIs hacia Bronze (ArcGIS FeatureServer de edificaciones y WFS de barrios)."""
import json
import time

import pandas as pd
import requests

from src.common import (ROOT, latest_snapshot_dir, load_config, manifest_for,
                        save_bronze, snapshot_name, user_agent, verify_files)
from src.logger import get_logger

log = get_logger(__name__)

SRC = "edificaciones"
SRC_GEO = "poligonos_barrios"
BASE = "data/bronze/api/edificaciones"
BASE_GEO = "data/bronze/geo/poligonos_barrios"


def http_get(session, url, params, cfg):
    """GET con timeout y reintentos simples; devuelve la respuesta (aunque sea 4xx/5xx tras agotar reintentos)."""
    h = cfg["http"]
    r = None
    for intento in range(1, h["retries"] + 1):
        try:
            # timeout: sin él una red caída dejaría el script colgado
            r = session.get(url, params=params, timeout=h["timeout_s"])
            if r.status_code < 500:
                return r
        except requests.RequestException as e:
            log.warning("intento %s falló: %s", intento, type(e).__name__)
        time.sleep(h["request_delay_s"] * intento)
    if r is None:
        raise RuntimeError(f"sin respuesta de {url}")
    return r


def extract_edificaciones(refresh=False):
    """Descarga conteo, metadatos de capa y páginas crudas; no sobrescribe nada."""
    cfg = load_config()
    existing = manifest_for(SRC) if manifest_for(SRC + "_count_despues") else []  # completa solo si terminó
    if existing and not refresh:
        todas = [m for k in (SRC, SRC + "_count_antes", SRC + "_count_despues", SRC + "_capa_meta")
                 for m in manifest_for(k)]
        if verify_files(todas):
            log.info("%s: ya existe, sha256 coincide (%s páginas)", SRC, len(existing))
        return
    s = cfg["sources"]["edificaciones"]
    layer, url = s["layer"], s["url"]
    snap = f"{BASE}/{snapshot_name()}"
    size = s["max_record_count"]
    session = requests.Session()
    session.headers["User-Agent"] = user_agent()
    try:
        cnt = {"where": "1=1", "returnCountOnly": "true", "f": "json"}
        r = http_get(session, url, cnt, cfg)
        n_antes = r.json().get("count")
        save_bronze(r.content, f"{snap}/count_antes.json", SRC + "_count_antes", url, cnt, r.status_code, n_antes)
        r = http_get(session, layer, {"f": "pjson"}, cfg)
        save_bronze(r.content, f"{snap}/capa_meta.json", SRC + "_capa_meta", layer, {"f": "pjson"},
                    r.status_code, len(r.json().get("fields", [])))
        total, offset, pagina = 0, 0, 1
        while True:
            # paginación: resultOffset + orden estable por OBJECTID; la capa admite máx. 2000 por página
            p = {"where": "1=1", "outFields": "*", "returnGeometry": "true", "outSR": 4326,
                 "orderByFields": "OBJECTID", "resultOffset": offset, "resultRecordCount": size, "f": "json"}
            r = http_get(session, url, p, cfg)
            if r.status_code != 200:
                raise RuntimeError(f"HTTP {r.status_code} en página {pagina}")
            d = r.json()
            if "error" in d:
                raise RuntimeError(f"error de API en página {pagina}: {d['error']}")
            n = len(d["features"])
            save_bronze(r.content, f"{snap}/page_{pagina:04d}.json", SRC, url, p, r.status_code, n)
            log.info("%s: página %s con %s filas", SRC, pagina, n)
            total += n
            offset += n
            pagina += 1
            if not d.get("exceededTransferLimit") or n < size:
                break
            time.sleep(cfg["http"]["request_delay_s"])
        r = http_get(session, url, cnt, cfg)
        n_despues = r.json().get("count")
        save_bronze(r.content, f"{snap}/count_despues.json", SRC + "_count_despues", url, cnt, r.status_code, n_despues)
    finally:
        session.close()
    log.info("%s: %s filas en %s páginas; conteo antes=%s después=%s", SRC, total, pagina - 1, n_antes, n_despues)
    if total != n_antes or n_antes != n_despues:
        log.warning("el conteo cambió durante la extracción o no coincide con lo descargado")


def extract_poligonos(refresh=False):
    """Polígonos de barrios (WFS, EPSG:4326 pedido al servidor). Solo para validar la llave en el EDA."""
    cfg = load_config()
    if manifest_for(SRC_GEO) and not refresh:
        if verify_files(manifest_for(SRC_GEO)):
            log.info("%s: ya existe, sha256 coincide", SRC_GEO)
        return
    url = cfg["sources"]["poligonos_barrios"]["url"].split()[0]
    p = {"service": "WFS", "version": "1.0.0", "request": "GetFeature", "typeName": "dapm:pdt_dpa_barrios_sectores",
         "outputFormat": "application/json", "srsName": "EPSG:4326"}
    session = requests.Session()
    session.headers["User-Agent"] = user_agent()
    try:
        r = http_get(session, url, p, cfg)
        if r.status_code != 200:
            raise RuntimeError(f"HTTP {r.status_code} en WFS")
        n = len(r.json()["features"])
        save_bronze(r.content, f"{BASE_GEO}/{snapshot_name()}/barrios.geojson", SRC_GEO, url, p, r.status_code, n)
    finally:
        session.close()
    log.info("%s: %s polígonos", SRC_GEO, n)


def _snapshot_pages():
    snap = latest_snapshot_dir(BASE)
    if snap is None:
        raise FileNotFoundError("no hay Bronze de edificaciones; corre main.py --stage extract")
    return snap, sorted(snap.glob("page_*.json"))


def load_edificaciones_raw():
    """Lee el último snapshot Bronze y devuelve (DataFrame de atributos, lista de geometrías); no modifica nada."""
    _, pages = _snapshot_pages()
    filas, geoms = [], []
    for p in pages:
        for f in json.loads(p.read_bytes())["features"]:
            filas.append(f["attributes"])
            geoms.append(f.get("geometry"))
    return pd.DataFrame(filas), geoms


def load_json_bronze(rel_name):
    """Carga count_antes.json, count_despues.json o capa_meta.json del último snapshot."""
    snap, _ = _snapshot_pages()
    return json.loads((snap / rel_name).read_bytes())


def load_poligonos_raw():
    snap = latest_snapshot_dir(BASE_GEO)
    return json.loads((snap / "barrios.geojson").read_bytes())
