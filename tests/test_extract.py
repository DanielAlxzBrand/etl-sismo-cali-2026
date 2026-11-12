"""Pruebas de Bronze: manifiesto, sha256 y coherencia de filas (sin red)."""
import json
from collections import Counter

from src.common import ROOT, read_manifest, sha256_file


def test_manifiesto_existe_y_no_vacio():
    assert (ROOT / "data/bronze/manifest.jsonl").exists()
    assert len(read_manifest()) > 0


def test_campos_del_manifiesto_sin_tokens():
    campos = {"source_id", "url", "params", "fetched_at_utc", "http_status", "rows", "bytes", "sha256", "path"}
    for m in read_manifest():
        assert campos <= set(m)
        assert "token" not in json.dumps(m).lower()


def test_archivos_existen_y_sha256_coincide():
    for m in read_manifest():
        p = ROOT / m["path"]
        assert p.exists(), m["path"]
        assert p.stat().st_size == m["bytes"], m["path"]
        assert sha256_file(p) == m["sha256"], m["path"]


def test_sin_paths_duplicados():
    c = Counter(m["path"] for m in read_manifest())
    assert [p for p, n in c.items() if n > 1] == []


def test_rows_coherente_con_el_contenido():
    for m in read_manifest():
        raw = (ROOT / m["path"]).read_bytes()
        sid = m["source_id"]
        if sid == "edificaciones":
            assert len(json.loads(raw)["features"]) == m["rows"]
        elif sid in ("edificaciones_count_antes", "edificaciones_count_despues"):
            assert json.loads(raw)["count"] == m["rows"]
        elif sid == "edificaciones_capa_meta":
            assert len(json.loads(raw)["fields"]) == m["rows"]
        elif sid == "poligonos_barrios":
            assert len(json.loads(raw)["features"]) == m["rows"]
        elif sid == "estrato_barrio":
            assert max(raw.count(b"\n") - 1, 0) == m["rows"]


def test_paginas_suman_el_conteo_oficial():
    ms = read_manifest()
    paginas = sum(m["rows"] for m in ms if m["source_id"] == "edificaciones")
    antes = next(m["rows"] for m in ms if m["source_id"] == "edificaciones_count_antes")
    despues = next(m["rows"] for m in ms if m["source_id"] == "edificaciones_count_despues")
    assert paginas == antes == despues
