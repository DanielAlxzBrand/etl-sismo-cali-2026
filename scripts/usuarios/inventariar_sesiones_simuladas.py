"""Inventario de la carpeta de trabajo de las sesiones simuladas y auditoría del registro de la etapa 1 (solo lectura).

Uso:
    python scripts/usuarios/inventariar_sesiones_simuladas.py --carpeta <carpeta> --commit <sha> [--repo <repo>] [--externo etiqueta=ruta ...] [--omitir <carpeta> ...] [--registro <archivo>] [--nombre <texto> ...] [--salida <archivo>]

Qué hace, sin escribir nada fuera de `--salida`:
  1. Lista cada archivo de la carpeta (ruta relativa, tamaño, sha256 y fecha), sin los de la copia maestra ni las carpetas de `--omitir`.
  2. Compara con la copia maestra cada carpeta de participante (las que terminan en `_etapa_N`): archivos iguales, modificados y de más (los que creó alguien que no es la copia).
  3. Comprueba la copia maestra contra el commit: cada archivo de `git ls-tree` con el mismo hash de blob (sin filtros de saltos de línea) y ningún archivo de más.
  4. Cita tamaño y sha256 de los archivos externos que se pasen con `--externo etiqueta=ruta` (la etiqueta es el nombre con el que se cita, no la ruta).
  5. Con `--registro`, audita el texto de una etapa 1 contra el guion: enunciados literales, preguntas de cierre, línea de congelación, marca «no verificado: lectura»,
     nombres de herramientas o de personas, guiones largos y frases que afirmen haber usado el panel.
Qué NO hace: no certifica quién escribió un texto, ni que lo que dice un registro sea verdad, ni que una herramienta no haya leído más de lo permitido; solo compara bytes y busca las marcas listadas.
"""
import argparse
import hashlib
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAESTRA = "etl_sismo_cali_3157ee2"
CARPETA_DE_PARTICIPANTE = re.compile(r"_etapa_\d+$")   # solo estas carpetas se comparan con la copia maestra
LINEA_DE_CONGELACION = "REGISTRO DE LA ETAPA 1 CONGELADO"
MARCA = "no verificado: lectura"
CAMPOS = ("Lo que me piden:", "Dónde busco y por qué:", "Lo que pienso en voz alta:", "Mi respuesta, con mis palabras:", "Lo que no pude comprobar:", "Lo que me confundió o me faltó:")
# Las cadenas se parten para que este archivo no se detecte a sí mismo en las pruebas de criterio de texto.
HERRAMIENTAS = re.compile("Cla" + "ude|Anthro" + "pic|Chat" + "GPT|Co" + "pilot|Gem" + "ini|Open" + "AI|Co" + "dex|Anti" + "gravity|GP" + r"T-?\d|(?i:\bpro" + r"mpt\b)")
USO_DEL_PANEL = re.compile(r"(?i)\b(hice clic|hice click|abrí el panel|abri el panel|ejecuté|ejecute|usé el panel|use el panel|filtré|filtre|probé el panel)\b")
GUION_LARGO = re.compile("[\u2013\u2014]")
EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF]")
CIFRA_MEDIDA = re.compile(r"(?i)\b\d+\s*(?:s|seg|segundos|minutos|min|ayudas|errores|%)\b")


def sha256(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def sha1_de_blob(datos):
    """Hash que git da a un archivo sin ningún filtro de saltos de línea."""
    return hashlib.sha1(b"blob %d\0" % len(datos) + datos).hexdigest()


def fecha(ruta):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ruta.stat().st_mtime))


def archivos(raiz):
    return sorted(p for p in raiz.rglob("*") if p.is_file())


def inventario(carpeta, maestra=MAESTRA, omitir=()):
    """Filas (ruta relativa, tamaño, sha256, fecha) de todo lo que hay en la carpeta, sin la copia maestra ni las carpetas de primer nivel de `omitir` (se citan aparte, con `--externo`)."""
    filas = []
    for p in archivos(carpeta):
        rel = p.relative_to(carpeta).as_posix()
        if rel.split("/")[0] == maestra or rel.split("/")[0] in omitir:
            continue
        filas.append({"ruta": rel, "tamano": p.stat().st_size, "sha256": sha256(p), "fecha": fecha(p)})
    return filas


def comparar(carpeta_de_participante, carpeta_maestra):
    """Iguales, modificados y de más de una carpeta de participante frente a la copia maestra (listas de rutas relativas)."""
    iguales, distintos, de_mas = [], [], []
    for p in archivos(carpeta_de_participante):
        rel = p.relative_to(carpeta_de_participante).as_posix()
        m = carpeta_maestra / rel
        if not m.is_file():
            de_mas.append(rel)
        elif sha256(p) == sha256(m):
            iguales.append(rel)
        else:
            distintos.append(rel)
    return {"iguales": iguales, "distintos": distintos, "de_mas": de_mas}


def verificar_maestra(carpeta_maestra, repo, commit):
    """Compara la copia maestra con `git ls-tree -r <commit>`: hash de blob de cada archivo; devuelve esperados, idénticos, distintos, faltan y de más."""
    salida = subprocess.run(["git", "-C", str(repo), "ls-tree", "-r", "-z", commit], capture_output=True, check=True).stdout.decode("utf-8")
    esperados = {}
    for entrada in filter(None, salida.split("\0")):
        cabecera, ruta = entrada.split("\t", 1)
        esperados[ruta] = cabecera.split()[2]
    identicos, distintos, faltan = 0, [], []
    for ruta, blob in esperados.items():
        p = carpeta_maestra / ruta
        if not p.is_file():
            faltan.append(ruta)
        elif sha1_de_blob(p.read_bytes()) == blob:
            identicos += 1
        else:
            distintos.append(ruta)
    de_mas = sorted(p.relative_to(carpeta_maestra).as_posix() for p in archivos(carpeta_maestra) if p.relative_to(carpeta_maestra).as_posix() not in esperados)
    return {"esperados": len(esperados), "identicos": identicos, "distintos": distintos, "faltan": faltan, "de_mas": de_mas}


def enunciados_del_guion(texto):
    """({T1..T6: enunciado entre «»}, [tres preguntas de cierre]) leídos del guion."""
    tareas = dict(re.findall(r"^\| (T[1-6]) \| («[^|]*») \|", texto, re.M))
    cierre = re.findall(r"^\s+- («¿Qué [^\n]*»)$", texto, re.M)
    return tareas, cierre


def auditar_registro(texto, guion, nombres=()):
    """Hallazgos (lista de textos; vacía si no hay) del registro de una etapa 1 frente al guion."""
    texto = texto.replace("\r\n", "\n")
    hallazgos = []
    tareas, cierre = enunciados_del_guion(guion)
    if len(tareas) != 6 or len(cierre) != 3:
        return ["el guion no trae las seis tareas y las tres preguntas de cierre"]
    bloques = re.split(r"(?m)^TAREA (T[1-6])$", texto)
    orden = bloques[1::2]
    if orden != [f"T{i}" for i in range(1, 7)]:
        hallazgos.append(f"las tareas no son T1 a T6 en orden: {orden}")
    for t, cuerpo in zip(orden, bloques[2::2]):
        posiciones = [cuerpo.find(c) for c in CAMPOS]
        if -1 in posiciones or posiciones != sorted(posiciones):
            hallazgos.append(f"{t}: faltan campos o no están en el orden del formato")
            continue
        if f"Lo que me piden: {tareas.get(t)}" not in cuerpo:
            hallazgos.append(f"{t}: el enunciado no es el literal del guion")
        no_pude = cuerpo.split("Lo que no pude comprobar:", 1)[1].split("\n", 1)[0]
        if MARCA not in no_pude:
            hallazgos.append(f"{t}: «Lo que no pude comprobar» no lleva la marca «{MARCA}»")
    for q in cierre:
        if f"{q}:" not in texto:
            hallazgos.append(f"falta la respuesta a {q}")
    lineas = [l for l in texto.split("\n") if l.strip()]
    if not lineas or lineas[-1] != LINEA_DE_CONGELACION or texto.count(LINEA_DE_CONGELACION) != 1:
        hallazgos.append("la línea de congelación no está una sola vez y al final")
    for etiqueta, patron in (("herramienta o modelo", HERRAMIENTAS), ("afirma haber usado el panel o ejecutado algo", USO_DEL_PANEL), ("guion largo o medio", GUION_LARGO), ("emoji", EMOJI), ("cifra medida", CIFRA_MEDIDA)):
        for n, l in enumerate(texto.split("\n"), 1):
            if patron.search(l):
                hallazgos.append(f"línea {n}: {etiqueta}")
    for nombre in nombres:
        for n, l in enumerate(texto.split("\n"), 1):
            if nombre.lower() in l.lower():
                hallazgos.append(f"línea {n}: nombre de persona")
    return hallazgos


def texto_del_registro(texto):
    """El registro que se audita: el bloque ```text de un archivo del repositorio, o el texto entero si no lo trae (un respaldo)."""
    m = re.search(r"```text\n(.*?)\n```", texto.replace("\r\n", "\n"), re.S)
    return m.group(1) if m else texto


def redactar(carpeta, commit, repo, externos, registro, guion, nombres, omitir=()):
    L = ["Inventario de la carpeta de las sesiones simuladas (solo lectura)", f"Commit de la copia maestra: {commit}", "Rutas relativas a la carpeta; sha256 completo; la fecha es la de modificación del archivo.", ""]
    L += ["== Archivos fuera de la copia maestra (ruta | tamaño en bytes | sha256 | fecha) =="]
    if omitir:
        L += [f"({len(omitir)} carpeta(s) de primer nivel omitida(s) aquí y citada(s) aparte, archivo por archivo, en la sección de externos)"]
    filas = inventario(carpeta, omitir=omitir)
    L += [f"{f['ruta']} | {f['tamano']} | {f['sha256']} | {f['fecha']}" for f in filas]
    L += [f"total: {len(filas)} archivos", ""]
    maestra = carpeta / MAESTRA
    L += ["== Cada carpeta de participante frente a la copia maestra =="]
    for d in sorted(p for p in carpeta.iterdir() if p.is_dir() and p.name != MAESTRA and CARPETA_DE_PARTICIPANTE.search(p.name)):
        r = comparar(d, maestra)
        L += [f"{d.name}: {len(r['iguales'])} iguales, {len(r['distintos'])} modificados, {len(r['de_mas'])} de más"]
        L += [f"  modificado: {x}" for x in r["distintos"]] + [f"  de más (no está en la copia maestra): {x}" for x in r["de_mas"]]
    L += [""]
    v = verificar_maestra(maestra, repo, commit)
    L += ["== Copia maestra frente al commit (hash de blob sin filtros) ==",
          f"{v['esperados']} archivos esperados, {v['identicos']} idénticos, {len(v['distintos'])} distintos, {len(v['faltan'])} que faltan, {len(v['de_mas'])} de más"]
    L += [f"  distinto: {x}" for x in v["distintos"]] + [f"  falta: {x}" for x in v["faltan"]] + [f"  de más: {x}" for x in v["de_mas"]] + [""]
    if externos:
        L += ["== Archivos externos citados (etiqueta | tamaño en bytes | sha256) =="]
        for etiqueta, ruta in externos:
            L += [f"{etiqueta} | {ruta.stat().st_size} | {sha256(ruta)}" if ruta.is_file() else f"{etiqueta} | no existe"]
        L += [""]
    if registro is not None:
        h = auditar_registro(texto_del_registro(registro.read_text(encoding="utf-8")), guion.read_text(encoding="utf-8"), nombres)
        L += ["== Auditoría del registro de la etapa 1 frente al guion ==", f"hallazgos automáticos: {len(h)}"] + [f"  {x}" for x in h] + [""]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Inventario de las sesiones simuladas (solo lectura)")
    ap.add_argument("--carpeta", required=True, type=Path)
    ap.add_argument("--commit", required=True)
    ap.add_argument("--repo", type=Path, default=ROOT)
    ap.add_argument("--externo", action="append", default=[], metavar="ETIQUETA=RUTA")
    ap.add_argument("--registro", type=Path)
    ap.add_argument("--guion", type=Path, default=ROOT / "docs" / "usuarios" / "guion_sesion.md")
    ap.add_argument("--nombre", action="append", default=[])
    ap.add_argument("--omitir", action="append", default=[], help="carpeta de primer nivel que no se lista (se cita con --externo)")
    ap.add_argument("--salida", type=Path)
    a = ap.parse_args(argv)
    externos = [(e.split("=", 1)[0], Path(e.split("=", 1)[1])) for e in a.externo]
    texto = redactar(a.carpeta, a.commit, a.repo, externos, a.registro, a.guion, a.nombre, tuple(a.omitir))
    if a.salida:
        a.salida.write_text(texto, encoding="utf-8", newline="\n")
        print(f"escrito {a.salida.name}")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(texto, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
