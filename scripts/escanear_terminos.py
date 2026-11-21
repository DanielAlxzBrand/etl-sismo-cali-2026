"""Escáner determinista de términos prohibidos: árbol de archivos, metadatos de imágenes y PDF y, con `--historial`, mensajes de commit y etiquetas.

    python scripts/escanear_terminos.py               # árbol (en un repositorio mira lo versionado; en un zip, todos los archivos)
    python scripts/escanear_terminos.py --historial   # además, mensajes de commit y etiquetas de las ramas y etiquetas vivas
    python scripts/escanear_terminos.py --autoprueba  # el canario: comprueba que cada vía de detección salta ante un término plantado

Qué mira: el texto de cada archivo, las cadenas de Python ya unidas aunque se escriban partidas con `+`, los fragmentos de texto de los PNG (sin los píxeles), los PDF sin sus
flujos comprimidos, los mensajes de commit y los nombres y mensajes de etiquetas. Los términos están en `scripts/terminos_vigilados.py` como sha256, así que este archivo no los nombra.
Qué NO hace: no mira el contenido comprimido de un PDF ni las bases de datos, no interpreta el contexto de una palabra y no corrige nada. Termina con código 1 si halla algo.
"""
import ast
import re
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import terminos_vigilados as tv  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OCULTAS_Y_AJENAS = {".git", ".venv", "venv", "env", "dist", "logs", "__pycache__", ".pytest_cache", ".ipynb_checkpoints"}
SIG_PNG = b"\x89PNG\r\n\x1a\n"
CHUNKS_DE_IMAGEN = {b"IHDR", b"PLTE", b"IDAT", b"IEND", b"tRNS", b"gAMA", b"cHRM", b"sRGB", b"pHYs", b"sBIT", b"bKGD", b"iCCP"}
SIN_ESCANEAR = {".db", ".zip", ".gz", ".pyc", ".woff", ".woff2", ".ttf", ".ico", ".jpg", ".jpeg"}


def _linea(texto, pos):
    return texto.count("\n", 0, pos) + 1


def _cadenas_de_python(texto):
    """Cadenas de un módulo de Python con las concatenaciones `"a" + "b"` ya resueltas (las partidas no esconden un término)."""
    try:
        arbol = ast.parse(texto)
    except SyntaxError:
        return []

    def plegar(nodo):
        if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
            return nodo.value
        if isinstance(nodo, ast.BinOp) and isinstance(nodo.op, ast.Add):
            izq, der = plegar(nodo.left), plegar(nodo.right)
            if izq is not None and der is not None:
                return izq + der
        return None

    salida, vistos = [], set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.BinOp) and id(nodo) not in vistos:
            valor = plegar(nodo)
            if valor is not None:
                salida.append((nodo.lineno, valor))
                for hijo in ast.walk(nodo):
                    vistos.add(id(hijo))
    return salida


def hallazgos_de_texto(nombre, texto, conjunto=tv.HERRAMIENTAS):
    res = [(nombre, _linea(texto, p), "término vigilado") for p in tv.encuentra(texto, conjunto)]
    if nombre.endswith(".py"):
        for linea, valor in _cadenas_de_python(texto):
            if tv.contiene(valor, conjunto):
                res.append((nombre, linea, "término vigilado en cadenas unidas"))
    return res


def hallazgos_de_png(nombre, datos):
    res = []
    i = 8
    while i + 12 <= len(datos):
        n = struct.unpack(">I", datos[i:i + 4])[0]
        tipo, cuerpo = datos[i + 4:i + 8], datos[i + 8:i + 8 + n]
        if tipo not in CHUNKS_DE_IMAGEN:
            if tipo == b"caBX":
                res.append((nombre, 0, "bloque de procedencia de contenido (caBX)"))
            elif tv.contiene(cuerpo.decode("latin-1"), tv.HERRAMIENTAS):
                res.append((nombre, 0, f"término vigilado en el metadato {tipo.decode('latin-1')}"))
        i += 12 + n
    return res


def hallazgos_de_pdf(nombre, datos):
    sin_flujos = re.sub(rb"stream\r?\n.*?endstream", b"", datos, flags=re.S)
    if tv.contiene(sin_flujos.decode("latin-1"), tv.HERRAMIENTAS):
        return [(nombre, 0, "término vigilado en los metadatos del PDF")]
    return []


def hallazgos_de_archivo(nombre, ruta):
    sufijo = Path(nombre).suffix.lower()
    datos = Path(ruta).read_bytes()
    if sufijo == ".png" and datos[:8] == SIG_PNG:
        return hallazgos_de_png(nombre, datos)
    if sufijo == ".pdf":
        return hallazgos_de_pdf(nombre, datos)
    if sufijo in SIN_ESCANEAR:
        return []
    try:
        texto = datos.decode("utf-8")
    except UnicodeDecodeError:
        return []
    return hallazgos_de_texto(nombre, texto)


def archivos_del_arbol(root):
    root = Path(root)
    r = subprocess.run(["git", "-C", str(root), "ls-files"], capture_output=True, text=True, encoding="utf-8")
    if r.returncode == 0 and r.stdout.strip():
        return [(n, root / n) for n in r.stdout.splitlines() if (root / n).is_file()]
    salida = []
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        if p.is_file() and not any(x in OCULTAS_Y_AJENAS for x in rel.parts):
            salida.append((rel.as_posix(), p))
    return salida


def escanear_arbol(root=ROOT):
    res = []
    for nombre, ruta in archivos_del_arbol(root):
        res += hallazgos_de_archivo(nombre, ruta)
    return res


def escanear_historial(root=ROOT):
    """Mensajes de commit y etiquetas de las ramas y etiquetas vivas (no mira refs/original ni las de respaldo)."""
    def git(*a):
        return subprocess.run(["git", "-C", str(root), *a], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    res = []
    for bloque in git("log", "--branches", "--tags", "--format=%h%x1f%B%x1e").split("\x1e"):
        if "\x1f" not in bloque:
            continue
        corto, mensaje = bloque.strip("\n").split("\x1f", 1)
        if tv.contiene(mensaje):
            res.append((f"commit {corto.strip()}", 0, "término vigilado en el mensaje"))
    for fila in git("for-each-ref", "refs/tags", "--format=%(refname:short)%1f%(objecttype)%1f%(contents)%1e").split("\x1e"):
        if fila.count("\x1f") < 2:
            continue
        nombre, tipo, mensaje = fila.strip("\n").split("\x1f", 2)
        # el mensaje solo cuenta en una etiqueta anotada: en una ligera `%(contents)` es el mensaje del commit, que ya se revisó arriba
        if tv.contiene(nombre) or (tipo == "tag" and tv.contiene(mensaje)):
            res.append((f"etiqueta {nombre.strip()}", 0, "término vigilado en el nombre o el mensaje"))
    return res


def autoprueba():
    """Planta el canario por cada vía y devuelve las vías que NO lo detectaron (lista vacía si todo salta)."""
    c = tv.canario()
    fallos = []
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        (t / "a.md").write_text(f"un texto con {c.upper()} dentro", encoding="utf-8")
        (t / "b.py").write_text(f'X = "{c[:2]}" + "{c[2:]}"\n', encoding="utf-8")
        (t / "c.png").write_bytes(SIG_PNG + _chunk(b"IHDR", b"\x00" * 13) + _chunk(b"tEXt", b"Software\x00" + c.encode()) + _chunk(b"IEND", b""))
        (t / "d.png").write_bytes(SIG_PNG + _chunk(b"IHDR", b"\x00" * 13) + _chunk(b"caBX", b"jumb") + _chunk(b"IEND", b""))
        (t / "e.pdf").write_bytes(b"%PDF-1.4\n/Producer (" + c.encode() + b")\nstream\nxx\nendstream\n")
        (t / "limpio.md").write_text("texto sin nada raro", encoding="utf-8")
        hallado = {n for n, _, _ in escanear_arbol(t)}
        for nombre in ("a.md", "b.py", "c.png", "d.png", "e.pdf"):
            if nombre not in hallado:
                fallos.append(nombre)
        if "limpio.md" in hallado:
            fallos.append("limpio.md (falso positivo)")
        repo = t / "repo"
        repo.mkdir()
        g = lambda *a: subprocess.run(["git", "-C", str(repo), "-c", "user.name=prueba", "-c", "user.email=prueba@example.org", *a], capture_output=True, text=True, encoding="utf-8")
        g("init", "-q")
        (repo / "x.txt").write_text("x", encoding="utf-8")
        g("add", "-A")
        g("commit", "-q", "-m", f"mensaje con {c}")
        g("tag", f"etiqueta-{c}")
        h = escanear_historial(repo)
        if not any(n.startswith("commit") for n, _, _ in h):
            fallos.append("mensaje de commit")
        if not any(n.startswith("etiqueta") for n, _, _ in h):
            fallos.append("etiqueta")
    return fallos


def _chunk(tipo, cuerpo):
    import zlib
    return struct.pack(">I", len(cuerpo)) + tipo + cuerpo + struct.pack(">I", zlib.crc32(tipo + cuerpo) & 0xFFFFFFFF)


def main(argv):
    if "--autoprueba" in argv:
        fallos = autoprueba()
        print("autoprueba:", "todas las vías detectan el canario" if not fallos else f"NO detectan: {fallos}")
        return 1 if fallos else 0
    res = escanear_arbol()
    if "--historial" in argv:
        res += escanear_historial()
    for nombre, linea, que in res:
        print(f"{nombre}{':' + str(linea) if linea else ''}: {que}")
    print(f"hallazgos: {len(res)}")
    return 1 if res else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
