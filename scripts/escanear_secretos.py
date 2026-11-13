"""Escáner de secretos: árbol de trabajo, historial de git, salidas de notebooks, logs y el contenido de un zip.

Reporta archivo, línea y NOMBRE del patrón; nunca el valor. Código de salida 1 si encuentra algo.
Uso: python scripts/escanear_secretos.py [--raiz CARPETA] [--zip ARCHIVO.zip] [--sin-historial]
Los patrones se construyen por concatenación para que este archivo y sus pruebas no se detecten a sí mismos.
"""
import argparse
import math
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUIR_DIRS = {".git", "__pycache__", ".pytest_cache", ".ipynb_checkpoints", "dist", "site-packages"}
EXCLUIR_PREFIJOS = (".venv",)
EXTENSIONES_BINARIAS = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".db", ".zip", ".pyc", ".docx", ".xlsx", ".ico", ".woff", ".woff2"}
MAX_BYTES = 8_000_000          # archivos de texto más grandes se omiten (datos crudos de Bronze)
MAX_LINEA = 20_000             # líneas más largas son datos, no credenciales
ENTROPIA_MIN = 4.2
HEX = re.compile(r"^[0-9a-fA-F]+$")
PARAMS = "token|app_token|apptoken|key|password|passwd|secret|apikey|api_key|access_token"

# nombre del patrón -> expresión regular (los literales se parten con "+" para no autodetectarse)
PATRONES = {
    "clave_aws": re.compile("AK" + "IA[0-9A-Z]{16}"),
    "token_github": re.compile("gh" + r"[pousr]_[A-Za-z0-9]{36,}"),
    "token_slack": re.compile("xo" + r"x[baprs]-[A-Za-z0-9-]{10,}"),
    "clave_google": re.compile("AI" + r"za[0-9A-Za-z_-]{35}"),
    "jwt": re.compile("ey" + r"J[A-Za-z0-9_-]{10,}\.ey" + r"J[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    "clave_privada": re.compile("-----BEGIN (?:[A-Z]+ )?PRIV" + "ATE KEY-----"),
    "url_con_credenciales": re.compile(r"[a-z][a-z0-9+.-]*://[^/\s:@'\"]+:[^/\s@'\"]{3,}@"),
    "parametro_url_sensible": re.compile(r"[?&](?:" + PARAMS + r")=[^&\s'\"]{6,}", re.I),
    "cabecera_autorizacion": re.compile(r"authorization[\"']?\s*[:=]\s*[\"']?(?:bearer|basic|token)\s+[A-Za-z0-9._~+/=-]{8,}", re.I),
    "cabecera_token_app": re.compile(r"x-app-" + r"token[\"']?\s*[:=]\s*[\"']?[A-Za-z0-9]{8,}", re.I),
    "asignacion_mysql_password": re.compile("MYSQL" + r"_PASS" + r"WORD\s*[:=]\s*[\"']?(?![<$\s\"'`])[^\s\"'`]{4,}"),
    "asignacion_literal_sensible": re.compile(r"(?:pass" + r"word|passwd|secret|api[_-]?key|app[_-]?token|access[_-]?token)[\"']?\s*[:=]\s*[\"'][A-Za-z0-9_+/=.!@#$%^&*-]{8,}[\"']", re.I),
}
CANDIDATO = re.compile(r"[A-Za-z0-9+/_=-]{32,128}")


def entropia(s):
    return -sum((s.count(c) / len(s)) * math.log2(s.count(c) / len(s)) for c in set(s))


def _alta_entropia(linea):
    """Cadena larga con mayúsculas, minúsculas y dígitos, de alta entropía, que no sea una huella hexadecimal, una ruta ni parte de una URL."""
    for m in CANDIDATO.finditer(linea):
        t = m.group(0)
        if HEX.match(t) or not (re.search(r"[a-z]", t) and re.search(r"[A-Z]", t) and re.search(r"\d", t)):
            continue
        ini = linea.rfind(" ", 0, m.start()) + 1
        fin = linea.find(" ", m.end())
        palabra = linea[ini:fin if fin >= 0 else len(linea)]
        if "://" in palabra or "/" in palabra[:m.start() - ini] or "\\" in palabra:   # URL o ruta: los segmentos largos no son secretos
            continue
        if t.count("/") >= 2 or re.fullmatch(r"[A-Za-z]+(?:[_-][A-Za-z0-9]+)+", t):   # rutas e identificadores con palabras
            continue
        if entropia(t) >= ENTROPIA_MIN:
            return True
    return False


def revisar_linea(linea):
    """Nombres de los patrones que coinciden con una línea (vacío si ninguno)."""
    if len(linea) > MAX_LINEA:
        return []
    nombres = [n for n, p in PATRONES.items() if p.search(linea)]
    if not nombres and _alta_entropia(linea):
        nombres.append("cadena_de_alta_entropia")
    return nombres


def _es_texto(datos):
    return b"\x00" not in datos[:4096]


def escanear_bytes(nombre, datos):
    if not _es_texto(datos):
        return []
    hallazgos = []
    for n, linea in enumerate(datos.decode("utf-8", errors="replace").splitlines(), 1):
        if "image/png" in linea or "image/jpeg" in linea:   # imágenes base64 de notebooks
            continue
        hallazgos += [(nombre, n, p) for p in revisar_linea(linea)]
    return hallazgos


def _archivos(raiz):
    for p in sorted(raiz.rglob("*")):
        rel = p.relative_to(raiz)
        if not p.is_file() or any(x in EXCLUIR_DIRS or x.startswith(EXCLUIR_PREFIJOS) for x in rel.parts[:-1]):
            continue
        if p.suffix.lower() in EXTENSIONES_BINARIAS or p.stat().st_size > MAX_BYTES:
            continue
        if rel.parts[0] == "data" and len(rel.parts) > 1 and rel.parts[1] == "bronze":   # respuestas públicas crudas con huellas
            continue
        yield rel, p


def escanear_arbol(raiz):
    """Árbol de trabajo (incluye notebooks con sus salidas y logs). `.env` local queda fuera: su control es que git no lo versione."""
    hallazgos = []
    for rel, p in _archivos(raiz):
        if rel.as_posix() == ".env":
            continue
        hallazgos += escanear_bytes(rel.as_posix(), p.read_bytes())
    return hallazgos


def escanear_historial(raiz):
    """Líneas añadidas en `git log --all -p`, en streaming; si no es un repositorio, no hay historial."""
    if not (raiz / ".git").exists():
        return []
    proc = subprocess.Popen(["git", "log", "--all", "-p", "--no-color", "--no-ext-diff"], cwd=raiz, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    hallazgos, commit, archivo, n = [], "?", "?", 0
    try:
        for crudo in proc.stdout:
            linea = crudo.decode("utf-8", errors="replace").rstrip("\n")
            if linea.startswith("commit ") and re.fullmatch(r"commit [0-9a-f]{40}.*", linea):
                commit = linea[7:15]
            elif linea.startswith("diff --git "):
                archivo, n = linea.split(" b/", 1)[-1], 0
            elif linea.startswith("@@"):
                m = re.search(r"\+(\d+)", linea)
                n = int(m.group(1)) - 1 if m else 0
            elif linea.startswith("+") and not linea.startswith("+++"):
                n += 1
                if archivo.endswith(".env") or archivo == ".env":
                    hallazgos.append((f"historial:{commit}:{archivo}", n, "archivo_env_en_el_historial"))
                    continue
                if archivo.startswith("data/bronze/") or "image/png" in linea or "image/jpeg" in linea:
                    continue
                hallazgos += [(f"historial:{commit}:{archivo}", n, p) for p in revisar_linea(linea[1:])]
            elif not linea.startswith("-"):
                n += 1
    finally:
        proc.stdout.close()
        proc.wait()
    return hallazgos


def escanear_zip(ruta):
    hallazgos = []
    with zipfile.ZipFile(ruta) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            nombre = info.filename
            if Path(nombre).name == ".env" or "/.env/" in nombre:
                hallazgos.append((f"zip:{nombre}", 0, "archivo_env_en_el_zip"))
                continue
            if Path(nombre).suffix.lower() in EXTENSIONES_BINARIAS or info.file_size > MAX_BYTES:
                continue
            hallazgos += escanear_bytes(f"zip:{nombre}", z.read(info))
    return hallazgos


SENSIBLE = re.compile(r"PASSWORD|TOKEN|SECRET|KEY", re.I)


def canarios(raiz):
    """{nombre: valor} de las variables sensibles de `.env`, leídas EN MEMORIA (los valores nunca se imprimen ni se guardan)."""
    from dotenv import dotenv_values
    ruta = Path(raiz) / ".env"
    if not ruta.exists():
        return {}
    return {k: v for k, v in dotenv_values(ruta).items() if v and len(v) >= 6 and SENSIBLE.search(k)}


def _buscar_en(nombre, datos, can):
    """(archivo, línea, 'canario:NOMBRE') por cada variable cuyo valor aparece en los bytes; la línea es 0 si el archivo no es texto."""
    out = []
    for var, valor in can.items():
        b = valor.encode("utf-8")
        if b not in datos:
            continue
        if _es_texto(datos):
            out += [(nombre, n, f"canario:{var}") for n, l in enumerate(datos.split(bytes([10])), 1) if b in l]
        else:
            out.append((nombre, 0, f"canario:{var}"))
    return out


def canario_arbol(raiz, can):
    """Árbol de trabajo completo (también data/bronze, logs, evidencias y binarios), salvo `.env`, `.git`, entornos y cachés."""
    out = []
    for p in sorted(Path(raiz).rglob("*")):
        rel = p.relative_to(raiz)
        if not p.is_file() or rel.as_posix() == ".env" or any(x in EXCLUIR_DIRS or x.startswith(EXCLUIR_PREFIJOS) for x in rel.parts[:-1]) or p.stat().st_size > 64_000_000:
            continue
        out += _buscar_en(rel.as_posix(), p.read_bytes(), can)
    return out


def canario_historial(raiz, can):
    """Historial de git completo (mensajes y cambios, líneas añadidas y quitadas)."""
    if not (Path(raiz) / ".git").exists() or not can:
        return []
    proc = subprocess.Popen(["git", "log", "--all", "-p", "--no-color", "--no-ext-diff"], cwd=raiz, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    out, commit, archivo, n = [], "?", "?", 0
    claves = {v.encode("utf-8"): k for k, v in can.items()}
    try:
        for crudo in proc.stdout:
            if crudo.startswith(b"commit ") and re.fullmatch(rb"commit [0-9a-f]{40}.*\s*", crudo):
                commit = crudo[7:15].decode()
            elif crudo.startswith(b"diff --git "):
                archivo, n = crudo.decode("utf-8", "replace").split(" b/", 1)[-1].strip(), 0
            n += 1
            out += [(f"historial:{commit}:{archivo}", n, f"canario:{v}") for b, v in claves.items() if b in crudo]
    finally:
        proc.stdout.close()
        proc.wait()
    return out


def canario_zip(ruta, can):
    out = []
    with zipfile.ZipFile(ruta) as z:
        for info in z.infolist():
            if not info.is_dir():
                out += _buscar_en(f"zip:{info.filename}", z.read(info), can)
    return out


def estado_de_env(raiz):
    """`.env` debe estar ignorado por git y no versionado; devuelve los hallazgos (vacío si todo está bien)."""
    raiz = Path(raiz)
    if not (raiz / ".git").exists():
        return []
    ign = subprocess.run(["git", "check-ignore", "-q", ".env"], cwd=raiz, capture_output=True).returncode == 0
    ver = subprocess.run(["git", "ls-files", "--error-unmatch", ".env"], cwd=raiz, capture_output=True).returncode == 0
    return ([(".env", 0, "env_no_ignorado")] if not ign else []) + ([(".env", 0, "env_versionado")] if ver else [])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--raiz", default=str(ROOT))
    ap.add_argument("--zip", default=None)
    ap.add_argument("--sin-historial", action="store_true")
    ap.add_argument("--canario-env", action="store_true", help="comprueba que los valores sensibles de .env no aparecen en ningún otro lugar")
    a = ap.parse_args(argv)
    raiz = Path(a.raiz).resolve()
    hallazgos = escanear_arbol(raiz) + estado_de_env(raiz)
    if a.canario_env:
        can = canarios(raiz)
        print(f"canarios leídos de .env (variables): {', '.join(sorted(can)) or 'ninguna'}")
        hallazgos += canario_arbol(raiz, can)
        if not a.sin_historial:
            hallazgos += canario_historial(raiz, can)
        if a.zip:
            hallazgos += canario_zip(a.zip, can)
    if not a.sin_historial:
        hallazgos += escanear_historial(raiz)
    if a.zip:
        hallazgos += escanear_zip(a.zip)
    for archivo, linea, patron in hallazgos:
        print(f"{archivo}:{linea}: {patron}")
    print(f"hallazgos: {len(hallazgos)}")
    return 1 if hallazgos else 0


if __name__ == "__main__":
    sys.exit(main())
