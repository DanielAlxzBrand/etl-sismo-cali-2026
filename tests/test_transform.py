"""Pruebas de transformacion: llaves, Silver (duplicados, tipos) y zona horaria (sin red)."""
import datetime as dt
import json
from zoneinfo import ZoneInfo

import pandas as pd

from src.common import ROOT, load_config, read_manifest
from src.transform.build_gold import newcombe, wilson
from src.transform.keys import codigo_barrio, codigo_csv, normalize_key


def test_wilson_vectores():
    lo, hi = wilson(5, 10)
    assert (round(lo, 4), round(hi, 4)) == (0.2366, 0.7634)
    lo, hi = wilson(0, 10)
    assert (round(lo, 4), round(hi, 4)) == (0.0, 0.2775)


def test_newcombe_simetrico():
    d, lo, hi = newcombe(10, 100, 10, 100)
    assert d == 0 and lo < 0 < hi


def test_normalize_key():
    assert normalize_key("Urbanización Tequendama") == "URBANIZACION TEQUENDAMA"
    assert normalize_key("  Camino   Real - J. Borrero S. ") == "CAMINO REAL J BORRERO S"
    assert normalize_key("San José") == "SAN JOSE"
    assert normalize_key("ñandú") == "NANDU"
    assert normalize_key(None) == ""
    assert normalize_key(float("nan")) == ""


def test_codigo_barrio():
    assert codigo_barrio("19", "04") == "1904"
    assert codigo_barrio("03", "05") == "305"
    assert codigo_barrio(" ", "05") is None
    assert codigo_barrio(None, None) is None
    assert codigo_csv("101") == "101" and codigo_csv(" - ") is None


def _silver(nombre):
    return pd.read_csv(ROOT / load_config()["paths_silver"][nombre],
                       dtype={"comuna": str, "barrio": str, "codigo_barrio": str, "codigo_poligono": str})


def test_cero_duplicados_por_llave_natural():
    assert _silver("construcciones").objectid.is_unique
    assert _silver("integrated").objectid.is_unique
    assert _silver("estrato_barrio").codigo_barrio.is_unique


def test_tipos_esperados_silver():
    d = _silver("integrated")
    assert pd.api.types.is_integer_dtype(d.objectid)
    assert pd.api.types.is_float_dtype(d.lon) and pd.api.types.is_float_dtype(d.lat)
    assert d.lon.between(-77, -76).all() and d.lat.between(3, 4).all()
    assert d.clase_dano.isin(["escombros", "techo", "sin_cambio", "sin_datos"]).all()
    assert set(d.sin_datos.unique()) <= {True, False}
    assert d.estrato.dropna().isin(range(1, 7)).all()
    # sin datos satelitales las banderas son nulas, no falsas
    assert d[d.sin_datos].severo_estricto.isna().all() and d[~d.sin_datos].severo_estricto.notna().all()
    assert not d.nombre_barrio_csv.fillna("").str.contains("Ã|�").any()


def test_zona_horaria_bogota():
    cfg = load_config()
    assert cfg["timezone"] == "America/Bogota"
    tz = ZoneInfo("America/Bogota")
    meta = next(m for m in read_manifest() if m["source_id"] == "edificaciones_capa_meta")
    ms = json.loads((ROOT / meta["path"]).read_bytes())["editingInfo"]["lastEditDate"]
    local = dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc).astimezone(tz)
    assert local.date().isoformat() == cfg["fechas"]["fecha_edicion_capa"]
    assert local.utcoffset() == dt.timedelta(hours=-5)
