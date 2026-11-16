"""Comprobación compartida de `.env` frente a `.gitignore` cuando la carpeta puede no ser un repositorio de Git (por ejemplo, el zip descomprimido).

Quién la usa: `scripts/mysql/configurar_mysql.py` (no guarda credenciales si `.env` podría versionarse) y `scripts/escanear_secretos.py` (reporta si `.env` no queda ignorado). Viaja en el zip porque `scripts/`
entera viaja; si faltara, esos dos scripts no arrancarían.
Por qué existe: sin repositorio, Git no puede responder (`git check-ignore` termina con código 128) pero `.env` tampoco puede estar versionado; lo único que protege entonces es que el `.gitignore` lo ignore de verdad
si más adelante se usa Git. Aquí vive una sola copia de esa regla para que los dos scripts no discrepen.
Qué NO hace: no ejecuta nada con `.env` ni lo lee; no cubre todas las rarezas de `.gitignore` (patrones con carpetas intermedias, por ejemplo, nunca coinciden con el archivo `.env` de la raíz y se descartan).
"""
import fnmatch
import subprocess
from pathlib import Path

BARRA_INVERTIDA = chr(92)      # escapa el primer carácter de una línea de `.gitignore` (por ejemplo, para ignorar un archivo que empieza con # o !)


def gitignore_ignora_env(texto):
    """True si, aplicando las líneas de un `.gitignore` en orden (gana la última que coincide, como en Git), el archivo `.env` de la raíz queda ignorado.

    Una línea `!.env` posterior lo reincorpora, un patrón de carpeta (`.env/`) no vale para un archivo y `.env.example` no es `.env`."""
    ignorado = False
    for cruda in texto.lstrip(chr(0xFEFF)).splitlines():
        linea = cruda.rstrip()
        if not linea or linea.startswith("#"):
            continue
        niega = linea.startswith("!")
        patron = linea[1:] if niega else linea
        if patron.startswith(BARRA_INVERTIDA):
            patron = patron[1:]
        patron = patron.lstrip("/")        # anclado a la raíz: la raíz es la única carpeta donde vive `.env`
        while patron.startswith("**/"):
            patron = patron[3:]
        # un patrón con «/» (de carpeta, como `.env/`, o con carpetas intermedias) nunca coincide con el nombre `.env`: fnmatch ya lo descarta
        if fnmatch.fnmatchcase(".env", patron):
            ignorado = not niega
    return ignorado


def hay_repositorio(raiz):
    """(hay_repositorio, git_disponible). Hay repositorio si Git lo dice o si existe un `.git` en la carpeta o por encima (así un Git que falla, por ejemplo por propiedad dudosa de la carpeta,
    nunca abre la puerta a la comprobación más laxa); sin el programa git no se puede preguntar y se mira solo la presencia de `.git`."""
    raiz = Path(raiz).resolve()
    hay_git_en_disco = any((p / ".git").exists() for p in (raiz, *raiz.parents))
    try:
        r = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=raiz, capture_output=True, text=True, encoding="utf-8", errors="replace")
    except OSError:
        return hay_git_en_disco, False
    return hay_git_en_disco or (r.returncode == 0 and r.stdout.strip() == "true"), True
