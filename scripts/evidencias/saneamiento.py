"""Saneamiento de evidencias: sustituye rutas, usuario y equipo por marcadores antes de guardar una salida.

Marcadores: <REPO>, <CLON>, <TEMP>, <VENV>, <USUARIO>, <EQUIPO>. Se usa en todas las corridas de evidencias (D-E3-25).
"""
import getpass
import os
import re
import socket
import tempfile
from pathlib import Path

RUTA_USUARIO = re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s\"'<>|]+", re.I)


def _variantes(ruta):
    """Una ruta en sus formas habituales: con barras invertidas, con barras normales y escapada para JSON."""
    r = str(ruta)
    return {r, r.replace("\\", "/"), r.replace("\\", "\\\\")}


class Saneador:
    """Aplica los reemplazos de más larga a más corta y comprueba que no queda nada sensible."""

    def __init__(self, repo, clon=None, raiz_tmp=None, extras=()):
        pares = []
        if clon:
            pares.append((clon, "<CLON>"))
        if raiz_tmp:
            pares.append((raiz_tmp, "<TEMP>"))
        pares += [(Path(repo) / ".venv", "<VENV>"), (repo, "<REPO>"), (tempfile.gettempdir(), "<TEMP>"), *extras]
        reemplazos = []
        for ruta, marcador in pares:
            for v in _variantes(ruta):
                reemplazos.append((v, marcador))
                reemplazos.append((v.lower(), marcador))
        self._rutas = sorted(set(reemplazos), key=lambda x: -len(x[0]))
        nombres = {getpass.getuser(), os.environ.get("USERNAME", ""), Path.home().name}
        equipos = {socket.gethostname(), os.environ.get("COMPUTERNAME", "")}
        self._nombres = sorted({n for n in nombres if len(n) >= 3}, key=lambda n: -len(n))
        self._equipos = sorted({e for e in equipos if len(e) >= 3}, key=lambda n: -len(n))

    def __call__(self, texto):
        for origen, marcador in self._rutas:
            texto = texto.replace(origen, marcador)
            texto = re.sub(re.escape(origen), marcador, texto, flags=re.I)
        texto = RUTA_USUARIO.sub("<USUARIO>", texto)
        for n in self._nombres:
            texto = re.sub(re.escape(n), "<USUARIO>", texto, flags=re.I)
        for e in self._equipos:
            texto = re.sub(re.escape(e), "<EQUIPO>", texto, flags=re.I)
        return texto

    def pendientes(self, texto):
        """Lo que todavía parece una ruta de usuario, un nombre de usuario o un equipo (vacío si el texto está limpio)."""
        hallado = []
        if RUTA_USUARIO.search(texto):
            hallado.append("ruta de usuario")
        hallado += [f"usuario ({len(n)} letras)" for n in self._nombres if re.search(re.escape(n), texto, re.I)]
        hallado += [f"equipo ({len(e)} letras)" for e in self._equipos if re.search(re.escape(e), texto, re.I)]
        return hallado

    def escribir(self, ruta, texto):
        """Guarda el texto saneado (UTF-8, saltos LF); falla si queda algo sensible."""
        limpio = self(texto)
        restos = self.pendientes(limpio)
        if restos:
            raise ValueError(f"saneamiento incompleto en {Path(ruta).name}: {restos}")
        Path(ruta).write_text(limpio, encoding="utf-8", newline="\n")
        return limpio


def quitar_hostname_junit(xml):
    """Elimina el atributo hostname del informe JUnit."""
    return re.sub(r'\s+hostname="[^"]*"', "", xml)
