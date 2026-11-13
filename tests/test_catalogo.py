"""El catálogo de fuentes coincide con el manifiesto de Bronze, es determinista y /fuentes lo sirve tal cual."""
import hashlib
import importlib.util
import json

from fastapi.testclient import TestClient

from src.api.app import crear_app
from src.common import ROOT, read_manifest

JSON = ROOT / "docs" / "bronze" / "catalogo_fuentes.json"


def _generador():
    espec = importlib.util.spec_from_file_location("make_catalogo_fuentes", ROOT / "scripts" / "make_catalogo_fuentes.py")
    modulo = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(modulo)
    return modulo


def _catalogo():
    return json.loads(JSON.read_text(encoding="utf-8"))


def test_el_catalogo_coincide_con_el_manifiesto():
    cat = _catalogo()
    por_ruta = {a["ruta"]: a for s in cat["fuentes"] if s["snapshot"] for a in s["snapshot"]["archivos"]}
    for e in read_manifest():
        a = por_ruta[e["path"]]
        assert (a["sha256"], a["filas"], a["bytes"]) == (e["sha256"], e["rows"], e["bytes"]), e["path"]
        assert hashlib.sha256((ROOT / e["path"]).read_bytes()).hexdigest() == a["sha256"]
    assert len(por_ruta) == len(read_manifest())


def test_el_catalogo_cubre_todas_las_fuentes_del_manifiesto():
    cat = _catalogo()
    ids_manifiesto = {e["source_id"] for e in read_manifest()}
    cubiertas = {a["source_id"] for s in cat["fuentes"] if s["snapshot"] for a in s["snapshot"]["archivos"]}
    assert ids_manifiesto == cubiertas
    assert {"edificaciones", "estrato_barrio", "poligonos_barrios", "usgs", "atc20_prensa"} == {s["id"] for s in cat["fuentes"]}
    assert len(cat["descartadas"]) >= 5
    for s in cat["fuentes"]:
        for campo in ("url", "protocolo", "formato", "autenticacion", "licencia", "cobertura_temporal", "granularidad", "riesgos_limitaciones"):
            assert s[campo], (s["id"], campo)
    assert "cifras de prensa" in json.dumps(cat, ensure_ascii=False) or "Cifras de prensa" in json.dumps(cat, ensure_ascii=False)
    assert set(cat["diccionario"]) == {"bronze", "silver", "gold"}


def test_el_diccionario_de_gold_describe_todas_las_columnas():
    gold = {a["ruta"]: a for a in _catalogo()["diccionario"]["gold"]["archivos"]}
    cols = gold["data/gold/gold_final.csv"]["columnas"]
    assert len(cols) == 26 and all(c["descripcion"] for c in cols)


def test_dos_generaciones_son_identicas():
    g = _generador()
    a, b = g.construir(), g.construir()
    assert json.dumps(a, ensure_ascii=False) == json.dumps(b, ensure_ascii=False)
    assert g._md(a) == g._md(b)
    assert json.dumps(a, ensure_ascii=False, indent=2) + "\n" == JSON.read_text(encoding="utf-8")  # el archivo guardado está al día
    assert g._md(a) == (ROOT / g.SALIDA_MD).read_text(encoding="utf-8")


def test_fuentes_devuelve_el_mismo_json():
    r = TestClient(crear_app(), raise_server_exceptions=False).get("/fuentes")
    assert r.status_code == 200 and r.json() == _catalogo()
