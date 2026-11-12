"""Utilidades comunes: rutas, config, sha256 y manifiesto de Bronze."""
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import yaml
from dotenv import load_dotenv

from src.logger import get_logger

ROOT = Path(__file__).resolve().parents[1]
log = get_logger(__name__)
DEFAULT_UA = "Mozilla/5.0 (UAO-ETL-proyecto-estudiantil)"


def load_config():
    """Lee config/config.yaml."""
    with open(ROOT / "config" / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def user_agent():
    """User-Agent desde .env (HTTP_USER_AGENT) o uno genérico."""
    load_dotenv(ROOT / ".env")
    return os.getenv("HTTP_USER_AGENT") or DEFAULT_UA


def utc_now():
    return datetime.now(timezone.utc)


def snapshot_name():
    """Nombre de snapshot con fecha UTC; un refresco nunca reutiliza uno existente."""
    return "snap_" + utc_now().strftime("%Y%m%dT%H%M%SZ")


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest_path():
    return ROOT / load_config()["paths"]["manifest"]


def read_manifest():
    p = manifest_path()
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def manifest_for(source_id):
    return [m for m in read_manifest() if m["source_id"] == source_id]


def save_bronze(content, rel_path, source_id, url, params, http_status, rows):
    """Escribe bytes crudos en Bronze (modo 'xb': nunca sobrescribe) y añade su línea al manifiesto."""
    dest = ROOT / rel_path
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "xb") as f:
        f.write(content)
    entry = {
        "source_id": source_id,
        "url": url,
        "params": params,  # nunca incluye tokens
        "fetched_at_utc": utc_now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "http_status": http_status,
        "rows": rows,
        "bytes": len(content),
        "sha256": sha256_bytes(content),
        "path": Path(rel_path).as_posix(),
    }
    with open(manifest_path(), "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def verify_files(entries):
    """True si todos los archivos del manifiesto existen y su sha256 coincide."""
    ok = True
    for e in entries:
        p = ROOT / e["path"]
        if not p.exists() or sha256_file(p) != e["sha256"]:
            log.warning("sha256 diferente o archivo ausente: %s", e["path"])
            ok = False
    return ok


def latest_snapshot_dir(base_rel):
    """Último snapshot (por nombre, que lleva fecha UTC) bajo una carpeta de Bronze."""
    snaps = sorted(p for p in (ROOT / base_rel).glob("snap_*") if p.is_dir())
    return snaps[-1] if snaps else None


def registrar_regla(reglas, rid, hallazgo, columnas, filas, justificacion):
    """Agrega una regla de Silver con su hallazgo y las filas afectadas (alimenta reglas_silver.md)."""
    reglas.append({"id": rid, "hallazgo": hallazgo, "columnas": columnas,
                   "filas_afectadas": int(filas), "justificacion": justificacion})
