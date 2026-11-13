"""Escritura de evidencias del almacenamiento: cabecera de metadatos, saneamiento y comprobación de que no hay secretos.

Todas las evidencias nuevas pasan por aquí: sustituye rutas, usuario y equipo por marcadores y se niega a escribir si en el texto aparece el
valor de una variable sensible de `.env` (contraseñas, tokens, claves). Solo escribe dentro de `docs/evidencias/<tema>/`.
"""
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO), str(Path(__file__).parent)]
from dotenv import dotenv_values  # noqa: E402
from saneamiento import Saneador  # noqa: E402

TZ = ZoneInfo("America/Bogota")
SENSIBLES = re.compile(r"PASSWORD|TOKEN|SECRET|KEY", re.I)


def ahora():
    return datetime.now(TZ).isoformat(timespec="seconds")


def commit_corto():
    r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True, text=True, encoding="utf-8")
    return r.stdout.strip() or "sin-commit"


def valores_sensibles():
    """Valores de las variables sensibles de .env (solo en memoria, para comprobar que no se filtran)."""
    return [v for k, v in dotenv_values(REPO / ".env").items() if v and len(v) >= 4 and SENSIBLES.search(k)]


def limpiar(texto, extras=()):
    """Texto saneado; falla si queda algo sensible o el valor de una variable secreta."""
    san = Saneador(REPO, extras=extras)
    limpio = san(texto)
    restos = san.pendientes(limpio)
    if restos:
        raise ValueError(f"saneamiento incompleto: {restos}")
    if any(v in limpio for v in valores_sensibles()):
        raise ValueError("el texto contiene el valor de una variable sensible; no se escribe")
    return limpio


def cabecera(titulo, comando, codigo, duracion):
    return (f"# {titulo}\n- comando: `{comando}`\n- fecha: {ahora()} (America/Bogota)\n- código de salida: {codigo}\n- duración: {duracion:.1f} s\n"
            f"- Python: {sys.version.split()[0]}\n- commit del repositorio: {commit_corto()}\n\n")


def guardar(tema, nombre, titulo, comando, codigo, duracion, cuerpo):
    """Escribe docs/evidencias/<tema>/<nombre> con cabecera y saneamiento; devuelve la ruta."""
    destino = REPO / "docs" / "evidencias" / tema
    destino.mkdir(parents=True, exist_ok=True)
    ruta = destino / nombre
    ruta.write_text(limpiar(cabecera(titulo, comando, codigo, duracion) + cuerpo), encoding="utf-8", newline="\n")
    return ruta


def guardar_csv(tema, nombre, filas):
    """Escribe un CSV (lista de listas, la primera fila es la cabecera) saneado y sin secretos."""
    destino = REPO / "docs" / "evidencias" / tema
    destino.mkdir(parents=True, exist_ok=True)
    ruta = destino / nombre
    texto = "\n".join(",".join(str(c) for c in f) for f in filas) + "\n"
    ruta.write_text(limpiar(texto), encoding="utf-8", newline="\n")
    return ruta


class Cronometro:
    def __enter__(self):
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, *a):
        self.duracion = time.perf_counter() - self.t0
