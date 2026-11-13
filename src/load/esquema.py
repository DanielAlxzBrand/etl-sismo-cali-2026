"""Esquema relacional: lectura de los archivos SQL, aplicación y análisis (tablas, columnas y diccionario)."""
import re
from pathlib import Path

VERSION_ESQUEMA = 1
CARPETA_SQL = Path(__file__).resolve().parent / "sql"
ARCHIVOS = {"mysql": "esquema_mysql.sql", "sqlite": "esquema_sqlite.sql"}
RESTRICCIONES = ("PRIMARY", "UNIQUE", "KEY", "CONSTRAINT", "INDEX", "FOREIGN", "CHECK")


def leer(dialecto):
    """Texto del archivo SQL del dialecto ('mysql' o 'sqlite')."""
    return (CARPETA_SQL / ARCHIVOS[dialecto]).read_text(encoding="utf-8")


def sentencias(texto):
    """Sentencias del archivo: sin comentarios de línea y separadas por ';' (los textos del esquema no llevan ';' dentro de cadenas)."""
    sin = "\n".join(l for l in texto.split("\n") if not l.strip().startswith("--"))
    return [s.strip() for s in sin.split(";") if s.strip()]


def aplicar(conn, dialecto):
    """Aplica el esquema (CREATE ... IF NOT EXISTS); en SQLite activa antes las claves foráneas. Confirma al final."""
    cur = conn.cursor()
    try:
        if dialecto == "sqlite":
            cur.execute("PRAGMA foreign_keys = ON")
        for s in sentencias(leer(dialecto)):
            cur.execute(s)
        conn.commit()
    finally:
        cur.close()


def _separar(cuerpo):
    """Parte el cuerpo de un CREATE TABLE por comas de primer nivel (ignora paréntesis y comas dentro de cadenas)."""
    partes, nivel, actual, en_cadena = [], 0, [], False
    for c in cuerpo:
        if c == "'":
            en_cadena = not en_cadena
        if not en_cadena:
            if c == "(":
                nivel += 1
            elif c == ")":
                nivel -= 1
            elif c == "," and nivel == 0:
                partes.append("".join(actual).strip())
                actual = []
                continue
        actual.append(c)
    if "".join(actual).strip():
        partes.append("".join(actual).strip())
    return partes


def tablas(texto):
    """{tabla: [ {nombre, tipo, no_nulo, comentario} ]} leído de un archivo SQL (en el orden en que se declaran)."""
    salida = {}
    for s in sentencias(texto):
        m = re.match(r"CREATE TABLE IF NOT EXISTS (\w+) \(", s)
        if not m:
            continue
        resto = s[m.end():]
        nivel, fin, en_cadena = 1, 0, False
        for i, c in enumerate(resto):
            if c == "'":
                en_cadena = not en_cadena
            if en_cadena:
                continue
            nivel += (c == "(") - (c == ")")
            if nivel == 0:
                fin = i
                break
        columnas = []
        for item in _separar(resto[:fin]):
            if item.split()[0].upper() in RESTRICCIONES:
                continue
            nombre, tipo = item.split()[0], re.match(r"\w+(?:\([^)]*\))?(?: UNSIGNED)?", item.split(None, 1)[1]).group(0)
            comentario = re.search(r"COMMENT '([^']*)'", item)
            columnas.append({"nombre": nombre, "tipo": tipo, "no_nulo": "NOT NULL" in item or "PRIMARY KEY" in item, "comentario": comentario.group(1) if comentario else ""})
        salida[m.group(1)] = columnas
    return salida


def comentarios_de_tabla(texto):
    """{tabla: comentario de la tabla} leído del archivo de MySQL."""
    return {m.group(1): m.group(2) for m in re.finditer(r"CREATE TABLE IF NOT EXISTS (\w+) \(.*?\) ENGINE=[^;]*? COMMENT='([^']*)'", texto, re.S)}


def paridad():
    """Diferencias entre los dos archivos: tablas y columnas (nombres y orden). Lista vacía si son equivalentes."""
    a, b = tablas(leer("mysql")), tablas(leer("sqlite"))
    errores = []
    if list(a) != list(b):
        errores.append(f"tablas distintas: {sorted(set(a) ^ set(b))}")
    for t in set(a) & set(b):
        na, nb = [c["nombre"] for c in a[t]], [c["nombre"] for c in b[t]]
        if na != nb:
            errores.append(f"{t}: columnas distintas ({na} frente a {nb})")
    return errores
