"""Registro de ejecucion: consola y archivo diario logs/etl_YYYYMMDD.log, con enmascarado de secretos."""
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import yaml
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
_PATRON = re.compile(r"(?i)(x-app-token|api[_-]?key|token|password|passwd|secret)(\s*[:=]\s*)(\S+)")
_AUTH = re.compile(r"(?i)(authorization)(\s*[:=]\s*)(.+)")  # la cabecera puede traer "Bearer <valor>"
_configurado = False


class EnmascararSecretos(logging.Filter):
    """Reemplaza por *** cabeceras de autenticación, pares clave=valor sensibles y cualquier valor de .env."""

    def __init__(self):
        super().__init__()
        vals = [v for v in dotenv_values(ROOT / ".env").values() if v and len(v) >= 4]
        self._valores = sorted(set(vals), key=len, reverse=True)

    def filter(self, record):
        msg = record.getMessage()
        msg = _AUTH.sub(lambda m: m.group(1) + m.group(2) + "***", msg)
        msg = _PATRON.sub(lambda m: m.group(1) + m.group(2) + "***", msg)
        for v in self._valores:
            msg = msg.replace(v, "***")
        record.msg, record.args = msg, ()
        return True


def _cfg():
    with open(ROOT / "config" / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)["logging"]


def _configurar():
    """Crea una sola vez los manejadores (consola y archivo) según la sección logging de config.yaml."""
    global _configurado
    if _configurado:
        return
    c = _cfg()
    raiz = logging.getLogger("etl")
    raiz.setLevel(getattr(logging, c["level"].upper()))
    raiz.propagate = False
    fmt = logging.Formatter(c["format"], c["datefmt"])
    carpeta = ROOT / c["dir"]
    carpeta.mkdir(parents=True, exist_ok=True)
    archivo = carpeta / datetime.now().strftime(c["file_pattern"])
    manejadores = [logging.StreamHandler(sys.stderr), logging.FileHandler(archivo, encoding="utf-8", delay=True)]
    for h in manejadores:
        h.setFormatter(fmt)
        h.addFilter(EnmascararSecretos())
        raiz.addHandler(h)
    _configurado = True


def get_logger(nombre):
    """Devuelve un logger hijo de 'etl' (el nombre se recorta a su último componente)."""
    _configurar()
    return logging.getLogger("etl." + nombre.split(".")[-1])
