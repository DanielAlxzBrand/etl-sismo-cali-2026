"""Ensaya, en un clon fuera del repositorio, cómo quitar el pie «Co-Authored-By» de los mensajes de commit sin tocar árboles, autores ni fechas.

Uso, desde la raíz del repositorio:
    python scripts/historial/limpiar_pies_de_coautoria.py --ensayo [--carpeta CARPETA] [--sin-pruebas] [--json ARCHIVO]
    python scripts/historial/limpiar_pies_de_coautoria.py --inventariar          escribe docs/evidencias/hashes_de_commits_citados.csv
    python scripts/historial/limpiar_pies_de_coautoria.py --filtrar-mensaje      filtro de `git filter-branch --msg-filter` (lee un mensaje por la entrada estándar)

Qué hace `--ensayo` (el repositorio original NO se modifica; todo ocurre en `CARPETA`, que por omisión es una carpeta temporal):
  1. Comprueba que el repositorio no tenga cambios sin commitear.
  2. Respaldo: `git clone --mirror` fuera del repositorio, verificado con `git fsck` y con los mismos refs y el mismo árbol en cada commit.
  3. Reescritura en un clon de trabajo: `git filter-branch --msg-filter` con el filtro de este archivo y `--tag-name-filter cat`, para que las etiquetas se muevan con su commit y conserven nombre,
     tipo y anotación.
  4. Verificación commit por commit contra el respaldo: mismo árbol, mismo autor y quien commitea con sus fechas, el mensaje igual salvo el pie, el mismo hash en los commits anteriores al primero
     afectado y otro hash desde ese commit, ningún pie en ninguna rama ni etiqueta y todas las etiquetas en el commit equivalente.
  5. `docs/evidencias/mapa_de_commits.md` (hash anterior, hash nuevo y asunto) escrito en el clon de trabajo, y la prueba `tests/test_limpieza_de_pies.py` corrida allí con el mapa (debe pasar) y
     sin él (debe fallar con los hashes citados que faltan).
  6. En una COPIA del clon de trabajo, la limpieza de lo que deja la reescritura: borrar `refs/original`, caducar el reflog y `git gc --prune=now`; comprobar con `git fsck` que el clon queda
     íntegro y que los commits anteriores a la reescritura ya no existen. En el clon de trabajo esa limpieza NO se hace: en la aplicación real se hace solo después de la última verificación completa.
Qué NO hace: no reescribe el historial del repositorio original, no mueve sus etiquetas, no sube nada a ningún sitio (no hay remoto) y no decide si se aplica.
"""
import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PIE = re.compile(r"(?i)^co-authored-by:")
INVENTARIO = ROOT / "docs" / "evidencias" / "hashes_de_commits_citados.csv"
MAPA = "docs/evidencias/mapa_de_commits.md"
ARCHIVOS_SIN_ESCANEAR = {"docs/evidencias/hashes_de_commits_citados.csv", MAPA}
SUFIJOS_BINARIOS = (".png", ".pdf", ".zip", ".db", ".svg", ".ipynb", ".csv.gz")


# ---------------------------------------------------------------------------------------------- el filtro del mensaje
def quitar_pie(mensaje):
    """El mensaje sin las líneas «Co-Authored-By: ...» y sin líneas en blanco al final, terminado en un salto de línea."""
    lineas = [l for l in mensaje.replace("\r\n", "\n").split("\n") if not PIE.match(l)]
    return "\n".join(lineas).rstrip("\n") + "\n"


# ---------------------------------------------------------------------------------------------- git
def git(cwd, *args, entrada=None, comprobar=True):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", input=entrada)
    if comprobar and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} falló: {r.stderr.strip()[:400]}")
    return r.stdout


def commits_con_pie(repo):
    """Hashes completos de los commits (en ramas y etiquetas) cuyo mensaje trae un pie, del más antiguo al más nuevo."""
    return git(repo, "log", "--branches", "--tags", "-i", "--grep=co-authored-by", "--reverse", "--topo-order", "--format=%H").split()


def existe_commit(repo, hash_):
    return subprocess.run(["git", "cat-file", "-e", f"{hash_}^{{commit}}"], cwd=repo, capture_output=True).returncode == 0


def datos_de_commits(repo):
    """Por cada commit de la rama actual, del más antiguo al más nuevo: hash, árbol, autor, quien commitea, fechas y mensaje."""
    sep, fin = "\x1f", "\x1e"
    formato = sep.join(["%H", "%T", "%an", "%ae", "%aI", "%cn", "%ce", "%cI", "%B"]) + fin
    texto = git(repo, "log", "--reverse", "--topo-order", f"--format={formato}", "HEAD")
    filas = []
    for bloque in texto.split(fin):
        if not bloque.strip("\n"):
            continue
        h, arbol, an, ae, ad, cn, ce, cd, mensaje = bloque.lstrip("\n").split(sep, 8)
        filas.append({"hash": h, "arbol": arbol, "autor": f"{an} <{ae}> {ad}", "committer": f"{cn} <{ce}> {cd}", "mensaje": mensaje.rstrip("\n") + "\n"})
    return filas


def datos_de_etiquetas(repo):
    """{nombre: (tipo, commit al que apunta, tagger, anotación)} de las etiquetas; las ligeras no tienen tagger ni anotación."""
    sep = "\x1f"
    formato = sep.join(["%(refname:short)", "%(objecttype)", "%(objectname)", "%(*objectname)", "%(taggername)", "%(taggeremail)", "%(taggerdate:iso-strict)", "%(contents)"])
    salida = {}
    for linea in git(repo, "for-each-ref", "refs/tags", f"--format={formato}\x1e").split("\x1e"):
        linea = linea.lstrip("\n")
        if not linea:
            continue
        nombre, tipo, objeto, apuntado, tn, te, td, contenido = linea.split(sep, 7)
        salida[nombre] = (tipo, apuntado or objeto, f"{tn} {te} {td}".strip(), contenido.strip())
    return salida


# ---------------------------------------------------------------------------------------------- verificación (pura: recibe datos, no toca git)
def problemas_de_la_reescritura(viejos, nuevos, etiquetas_viejas, etiquetas_nuevas, primer_afectado):
    """Lista de problemas de una reescritura (vacía si todo coincide). `viejos` y `nuevos` son las listas de `datos_de_commits`; `primer_afectado` es el hash completo del primer commit con pie."""
    errores = []
    if len(viejos) != len(nuevos):
        return [f"no hay el mismo número de commits: {len(viejos)} antes y {len(nuevos)} después"]
    indice = next((i for i, c in enumerate(viejos) if c["hash"] == primer_afectado), None)
    if indice is None:
        return ["el primer commit afectado no está en la rama"]
    mapa = {v["hash"]: n["hash"] for v, n in zip(viejos, nuevos)}
    for i, (v, n) in enumerate(zip(viejos, nuevos)):
        etiqueta = v["hash"][:7]
        if v["arbol"] != n["arbol"]:
            errores.append(f"{etiqueta}: el árbol cambió")
        if v["autor"] != n["autor"] or v["committer"] != n["committer"]:
            errores.append(f"{etiqueta}: cambió el autor, quien commitea o alguna fecha")
        if n["mensaje"] != quitar_pie(v["mensaje"]):
            errores.append(f"{etiqueta}: el mensaje cambió más que el pie")
        if any(PIE.match(l) for l in n["mensaje"].splitlines()):
            errores.append(f"{etiqueta}: el mensaje nuevo todavía trae un pie")
        if i < indice and v["hash"] != n["hash"]:
            errores.append(f"{etiqueta}: un commit anterior al primero afectado cambió de hash")
        if i >= indice and v["hash"] == n["hash"]:
            errores.append(f"{etiqueta}: un commit desde el primero afectado conservó su hash")
    if sorted(etiquetas_viejas) != sorted(etiquetas_nuevas):
        errores.append(f"las etiquetas no son las mismas: faltan {sorted(set(etiquetas_viejas) - set(etiquetas_nuevas))} y sobran {sorted(set(etiquetas_nuevas) - set(etiquetas_viejas))}")
    for nombre, (tipo, destino, tagger, nota) in etiquetas_viejas.items():
        if nombre not in etiquetas_nuevas:
            continue
        t2, d2, g2, n2 = etiquetas_nuevas[nombre]
        if t2 != tipo or (tipo == "tag" and (g2 != tagger or n2 != nota)):
            errores.append(f"etiqueta {nombre}: cambió su tipo, su tagger o su anotación")
        esperado = mapa.get(destino, destino)
        if d2 != esperado:
            errores.append(f"etiqueta {nombre}: apunta a {d2[:7]} y debía apuntar a {esperado[:7]}")
    return errores


def tabla_del_mapa(viejos, nuevos, primer_afectado):
    """Texto Markdown del mapa de commits: solo los que cambiaron de hash, con el asunto de su mensaje."""
    indice = next(i for i, c in enumerate(viejos) if c["hash"] == primer_afectado)
    filas = ["# Mapa de commits", "",
             "Los commits desde el primero afectado cambiaron de hash cuando se quitó el pie de sus mensajes: el árbol, el autor y las fechas de cada uno son los mismos. Los documentos y las evidencias que citan un hash viejo se dejaron como estaban; esta tabla dice a qué commit corresponde hoy.",
             "", "| Hash anterior | Hash nuevo | Asunto |", "|---|---|---|"]
    for v, n in zip(viejos[indice:], nuevos[indice:]):
        asunto = v["mensaje"].splitlines()[0].replace("|", "/")
        filas.append(f"| {v['hash'][:7]} | {n['hash'][:7]} | {asunto} |")
    return "\n".join(filas) + "\n"


def leer_mapa(texto):
    """{hash anterior (7 caracteres): hash nuevo} de un mapa escrito por `tabla_del_mapa`."""
    return {m.group(1): m.group(2) for m in re.finditer(r"(?m)^\| ([0-9a-f]{7}) \| ([0-9a-f]{7}) \|", texto)}


# ---------------------------------------------------------------------------------------------- inventario de hashes citados
def archivos_a_escanear(repo=ROOT):
    return [f for f in git(repo, "ls-files").splitlines()
            if not f.startswith("data/") and f not in ARCHIVOS_SIN_ESCANEAR and not f.endswith(SUFIJOS_BINARIOS)]


def citas_de_commits(repo, hashes7):
    """[(archivo, hash7)] de los archivos versionados que citan alguno de los `hashes7` como palabra aparte."""
    patron = re.compile(r"\b[0-9a-f]{7,40}\b")
    citas = []
    for f in archivos_a_escanear(repo):
        try:
            texto = (Path(repo) / f).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for h in sorted({m.group(0)[:7] for m in patron.finditer(texto) if len(m.group(0)) < 64} & set(hashes7)):
            citas.append((f, h))
    return citas


def inventariar(repo=ROOT):
    """Escribe el inventario (archivo, hash) de las citas a commits desde el primero con pie; devuelve las filas."""
    afectados = commits_con_pie(repo)
    if not afectados:
        raise SystemExit("ningún commit trae un pie: no hay nada que inventariar")
    primero = afectados[0]
    rango = git(repo, "rev-list", f"{primero}^..HEAD").split()
    filas = citas_de_commits(repo, {h[:7] for h in rango})
    with open(INVENTARIO, "w", encoding="utf-8", newline="") as f:
        f.write(f"# primer_commit_afectado: {primero[:7]}\n")
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["archivo", "hash"])
        w.writerows(filas)
    return filas


# ---------------------------------------------------------------------------------------------- ensayo
def ensayar(origen, carpeta, con_pruebas=True):
    """Ejecuta el ensayo completo y devuelve un diccionario con lo medido y la lista de problemas."""
    origen, carpeta = Path(origen), Path(carpeta)
    r = {"problemas": []}
    if git(origen, "status", "--porcelain").strip():
        raise SystemExit("el repositorio tiene cambios sin commitear: se commitea todo antes del ensayo")
    r["origen_head"] = git(origen, "rev-parse", "HEAD").strip()
    r["commits_totales"] = len(git(origen, "rev-list", "--all").split())
    con_pie = commits_con_pie(origen)
    r["commits_con_pie"] = len(con_pie)
    if not con_pie:
        raise SystemExit("ningún commit trae un pie: no hay nada que ensayar")
    primero = con_pie[0]
    r["primer_afectado"] = primero[:7]
    # 2. respaldo
    respaldo = carpeta / "respaldo.git"
    git(carpeta, "clone", "--quiet", "--mirror", str(origen), str(respaldo))
    git(respaldo, "fsck", "--full", "--no-dangling")
    refs_origen = git(origen, "for-each-ref", "--format=%(refname) %(objectname)", "refs/heads", "refs/tags")
    refs_respaldo = git(respaldo, "for-each-ref", "--format=%(refname) %(objectname)", "refs/heads", "refs/tags")
    if refs_origen != refs_respaldo:
        r["problemas"].append("el respaldo no tiene los mismos refs que el original")
    arboles_origen = git(origen, "log", "--all", "--format=%H %T").split("\n")
    arboles_respaldo = git(respaldo, "log", "--all", "--format=%H %T").split("\n")
    r["respaldo"] = {"refs_iguales": refs_origen == refs_respaldo, "commits_con_arbol_igual": len(set(arboles_origen) & set(arboles_respaldo)), "arboles_idénticos": sorted(arboles_origen) == sorted(arboles_respaldo)}
    if not r["respaldo"]["arboles_idénticos"]:
        r["problemas"].append("el respaldo no tiene los mismos commits con los mismos árboles")
    # 3. reescritura en un clon de trabajo
    trabajo = carpeta / "trabajo"
    git(carpeta, "clone", "--quiet", "--no-hardlinks", str(origen), str(trabajo))
    for rama in git(origen, "for-each-ref", "--format=%(refname:short)", "refs/heads").split():
        if git(trabajo, "rev-parse", "--verify", "--quiet", rama, comprobar=False).strip() == "":
            git(trabajo, "branch", "--track", rama, f"origin/{rama}")
    git(trabajo, "remote", "remove", "origin")      # sin los refs remotos, lo único que alcanza a los commits viejos es refs/original
    filtro = f"'{Path(sys.executable).as_posix()}' '{Path(__file__).resolve().as_posix()}' --filtrar-mensaje"
    entorno = {"FILTER_BRANCH_SQUELCH_WARNING": "1"}
    import os
    sub = subprocess.run(["git", "filter-branch", "-f", "--msg-filter", filtro, "--tag-name-filter", "cat", "--", "--branches", "--tags"], cwd=trabajo, capture_output=True, text=True,
                         encoding="utf-8", errors="replace", env={**os.environ, **entorno})
    if sub.returncode != 0:
        raise SystemExit(f"git filter-branch falló: {sub.stderr[-600:]}")
    # 4. verificación
    git(trabajo, "checkout", "--quiet", git(origen, "rev-parse", "--abbrev-ref", "HEAD").strip())
    viejos, nuevos = datos_de_commits(respaldo), datos_de_commits(trabajo)
    etiquetas_viejas, etiquetas_nuevas = datos_de_etiquetas(respaldo), datos_de_etiquetas(trabajo)
    r["problemas"] += problemas_de_la_reescritura(viejos, nuevos, etiquetas_viejas, etiquetas_nuevas, primero)
    indice = next(i for i, c in enumerate(viejos) if c["hash"] == primero)
    r["reescritura"] = {"commits_en_la_rama": len(viejos), "hash_cambiado": len(viejos) - indice, "hash_igual": indice,
                        "arboles_iguales": sum(v["arbol"] == n["arbol"] for v, n in zip(viejos, nuevos)), "autores_y_fechas_iguales": sum(v["autor"] == n["autor"] and v["committer"] == n["committer"] for v, n in zip(viejos, nuevos)),
                        "pies_que_quedan": len(commits_con_pie(trabajo)), "etiquetas": len(etiquetas_viejas), "etiquetas_movidas": sum(1 for n, v in etiquetas_viejas.items() if etiquetas_nuevas.get(n, v)[1] != v[1]),
                        "etiquetas_anotadas": sum(1 for v in etiquetas_viejas.values() if v[0] == "tag"), "refs_original_presentes": bool(git(trabajo, "for-each-ref", "refs/original").strip())}
    # 5. mapa y prueba de que ningún hash citado falta
    (trabajo / MAPA).write_text(tabla_del_mapa(viejos, nuevos, primero), encoding="utf-8", newline="\n")
    if con_pruebas:
        prueba = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--no-header", "tests/test_limpieza_de_pies.py", "-k", "hash"]
        con_mapa = subprocess.run(prueba, cwd=trabajo, capture_output=True, text=True, encoding="utf-8", errors="replace")
        (trabajo / MAPA).unlink()
        sin_mapa = subprocess.run(prueba, cwd=trabajo, capture_output=True, text=True, encoding="utf-8", errors="replace")
        (trabajo / MAPA).write_text(tabla_del_mapa(viejos, nuevos, primero), encoding="utf-8", newline="\n")
        r["prueba_de_hashes"] = {"con_el_mapa": con_mapa.stdout.strip().splitlines()[-1] if con_mapa.stdout.strip() else con_mapa.stderr[-200:], "con_el_mapa_codigo": con_mapa.returncode,
                                 "sin_el_mapa": sin_mapa.stdout.strip().splitlines()[-1] if sin_mapa.stdout.strip() else sin_mapa.stderr[-200:], "sin_el_mapa_codigo": sin_mapa.returncode}
        if con_mapa.returncode != 0:
            r["problemas"].append("la prueba de hashes citados falla con el mapa")
        if sin_mapa.returncode == 0:
            r["problemas"].append("la prueba de hashes citados no falla sin el mapa")
    # 6. limpieza en una copia
    copia = carpeta / "trabajo_limpio"
    shutil.copytree(trabajo, copia)
    antes = git(copia, "count-objects", "-v")
    for ref in git(copia, "for-each-ref", "--format=%(refname)", "refs/original").split():
        git(copia, "update-ref", "-d", ref)
    git(copia, "reflog", "expire", "--expire=now", "--all")
    git(copia, "gc", "--prune=now", "--quiet")
    git(copia, "fsck", "--full", "--no-dangling")
    anteriores_que_quedan = [c["hash"][:7] for c in viejos[indice:] if existe_commit(copia, c["hash"])]
    r["limpieza_en_una_copia"] = {"refs_original_borrados": not git(copia, "for-each-ref", "refs/original").strip(), "fsck_integro": True, "commits_anteriores_que_siguen_existiendo": anteriores_que_quedan,
                                  "objetos_antes": antes.split("count:")[1].split()[0] if "count:" in antes else "", "pies_que_quedan": len(commits_con_pie(copia)),
                                  "etiquetas_en_la_copia": len(datos_de_etiquetas(copia)), "rama_en_la_copia": git(copia, "rev-parse", "--abbrev-ref", "HEAD").strip()}
    if anteriores_que_quedan:
        r["problemas"].append(f"tras la limpieza siguen existiendo {len(anteriores_que_quedan)} commits anteriores a la reescritura")
    if r["origen_head"] != git(origen, "rev-parse", "HEAD").strip() or git(origen, "status", "--porcelain").strip() or sorted(datos_de_etiquetas(origen)) != sorted(etiquetas_viejas):
        r["problemas"].append("el repositorio original cambió durante el ensayo")
    r["carpeta"] = str(carpeta)
    return r


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    grupo = ap.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--ensayo", action="store_true", help="ensaya la limpieza en un clon fuera del repositorio")
    grupo.add_argument("--inventariar", action="store_true", help="escribe el inventario de hashes citados")
    grupo.add_argument("--filtrar-mensaje", action="store_true", help="filtro de git filter-branch: lee un mensaje y escribe el mismo sin el pie")
    ap.add_argument("--origen", type=Path, default=ROOT)
    ap.add_argument("--carpeta", type=Path, default=None, help="carpeta del ensayo (por omisión, una temporal que no se borra)")
    ap.add_argument("--sin-pruebas", action="store_true")
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)
    if a.filtrar_mensaje:
        sys.stdout.reconfigure(encoding="utf-8", newline="\n")
        sys.stdout.write(quitar_pie(sys.stdin.buffer.read().decode("utf-8", errors="replace")))
        return 0
    if a.inventariar:
        filas = inventariar(a.origen)
        print(f"inventario: {len(filas)} citas en {len({f for f, _ in filas})} archivos")
        return 0
    carpeta = a.carpeta or Path(tempfile.mkdtemp(prefix="ensayo_pies_"))
    carpeta.mkdir(parents=True, exist_ok=True)
    r = ensayar(a.origen, carpeta, con_pruebas=not a.sin_pruebas)
    texto = json.dumps(r, ensure_ascii=False, indent=2)
    if a.json:
        a.json.write_text(texto + "\n", encoding="utf-8")
    print(texto)
    for p in r["problemas"]:
        print("PROBLEMA:", p)
    return 1 if r["problemas"] else 0


if __name__ == "__main__":
    sys.exit(main())
