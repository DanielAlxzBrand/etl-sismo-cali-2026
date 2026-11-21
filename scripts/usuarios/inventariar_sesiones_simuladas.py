"""Inventario de la carpeta de trabajo de las sesiones simuladas y auditoría del registro de la etapa 1 (solo lectura).

Uso:
    python scripts/usuarios/inventariar_sesiones_simuladas.py --carpeta <carpeta> --commit <sha> [--repo <repo>] [--externo etiqueta=ruta ...] [--omitir <carpeta> ...] [--registro <archivo>] [--nombre <texto> ...] [--salida <archivo>]
    python scripts/usuarios/inventariar_sesiones_simuladas.py --entrega <carpeta> --nativa --trabajo <carpeta> --copia-maestra <carpeta> [--esperado ruta=sha256 ...] [--salida <archivo>]

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
import csv
import difflib
import hashlib
import io
import json
import re
import struct
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import terminos_vigilados  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
MAESTRA = "etl_sismo_cali_3157ee2"
CARPETA_DE_PARTICIPANTE = re.compile(r"_etapa_\d+$")   # solo estas carpetas se comparan con la copia maestra
LINEA_DE_CONGELACION = "REGISTRO DE LA ETAPA 1 CONGELADO"
MARCA = "no verificado: lectura"
CAMPOS = ("Lo que me piden:", "Dónde busco y por qué:", "Lo que pienso en voz alta:", "Mi respuesta, con mis palabras:", "Lo que no pude comprobar:", "Lo que me confundió o me faltó:")
# Las cadenas se parten para que este archivo no se detecte a sí mismo en las pruebas de criterio de texto.
HERRAMIENTAS = terminos_vigilados.Vigilados()   # los términos están como sha256 en scripts/terminos_vigilados.py
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
        if f"{q}:" not in texto and f"{q[1:-1]} " not in texto:   # con las comillas «» y dos puntos, o la pregunta tal cual seguida de su respuesta
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


# ---------------------------------------------------------------------------------------------- carpeta de entrega de un participante
def columna_de_ruta(filas):
    """Los manifiestos de las entregas llaman a la columna de la ruta «Ruta» o «RutaRelativa»."""
    return "RutaRelativa" if filas and "RutaRelativa" in filas[0] else "Ruta"


def leer_manifiestos(entrega):
    """({ruta: (bytes, sha256 en minúsculas)} del CSV, {ruta: sha256} del TXT, filas del CSV); ambos pueden traer BOM."""
    filas = list(csv.DictReader(io.StringIO((entrega / "manifiesto_sha256.csv").read_text(encoding="utf-8-sig"))))
    col = columna_de_ruta(filas)
    en_csv = {f[col]: (int(f["Bytes"]), f["SHA256"].lower()) for f in filas}
    en_txt = {}
    for linea in (entrega / "manifiesto_sha256.txt").read_text(encoding="utf-8-sig").splitlines():
        if linea.strip():
            h, ruta = linea.split("  ", 1)
            en_txt[ruta] = h.lower()
    return en_csv, en_txt, filas


def verificar_entrega(entrega, esperados=None):
    """Compara la carpeta de entrega con sus dos manifiestos y con los sha256 esperados que se pasen ({ruta: sha256}); nada se escribe ni se corrige."""
    reales = {p.relative_to(entrega).as_posix(): p for p in archivos(entrega)}
    en_csv, en_txt, filas = leer_manifiestos(entrega)
    manifiestos = {"manifiesto_sha256.csv", "manifiesto_sha256.txt"}
    col = columna_de_ruta(filas)
    repetidas = sorted({f[col] for f in filas if sum(g[col] == f[col] for g in filas) > 1})
    distintos = sorted(r for r, (b, h) in en_csv.items() if r in reales and (reales[r].stat().st_size != b or sha256(reales[r]) != h))
    esperados = esperados or {}
    fuera_de_lo_esperado = sorted(r for r, h in esperados.items() if r not in reales or sha256(reales[r]).lower() != h.lower())
    return {"presentes": len(reales), "manifestados": len(en_csv), "faltan": sorted(set(en_csv) - set(reales)), "de_mas": sorted(set(reales) - set(en_csv) - manifiestos),
            "tamano_o_sha256_distintos": distintos, "csv_igual_a_txt": {r: h for r, (b, h) in en_csv.items()} == en_txt, "rutas_repetidas": repetidas, "esperados_que_no_coinciden": fuera_de_lo_esperado, "esperados": len(esperados)}


def rutas_permitidas(mensaje):
    """Rutas `docs/...` que un mensaje de instrucciones lista como permitidas (acepta los `\\` que deja copiar un mensaje con formato)."""
    texto = mensaje.replace("\r\n", "\n").replace("\\_", "_")
    return [r.replace("\\", "") for r in re.findall(r"^\\?- (docs/[^\s(]+)", texto, re.M)]


def auditar_operaciones(comandos, permitidas_por_comando):
    """Referencias a archivos de cada comando recuperado frente a la lista permitida de su etapa: ({comando: [rutas]}, no_autorizadas, cmdlets distintos de Get-Content)."""
    refs, no_autorizadas, otros = {}, [], set()
    for nombre, texto in comandos.items():
        refs[nombre] = re.findall(r"'([^']+)'", texto)
        no_autorizadas += [(nombre, r) for r in refs[nombre] if r not in permitidas_por_comando[nombre]]
        otros |= set(re.findall(r"[A-Za-z]+-[A-Za-z]+", re.sub(r"'[^']+'", "", texto))) - {"Get-Content"}
    return refs, no_autorizadas, sorted(otros)


def comparar_registro_congelado(original, bloque_d):
    """Compara el registro de la etapa 1 (con su línea final) con el bloque D de la etapa 2: caracteres, coincidencia literal y normalizada, y las líneas que difieren."""
    original, bloque_d = original.replace("\r\n", "\n"), bloque_d.replace("\r\n", "\n")
    cuerpo = original.rstrip("\n")
    assert cuerpo.endswith(LINEA_DE_CONGELACION), "el original no termina en la línea de congelación"
    antes = cuerpo[: -len(LINEA_DE_CONGELACION)]
    normalizar = lambda t: re.sub(r"\s+", " ", t).strip()   # noqa: E731
    a, b = [l for l in antes.split("\n") if l.strip()], [l for l in bloque_d.split("\n") if l.strip()]
    diferencias = [l for l in difflib.unified_diff(a, b, "original", "bloque D", lineterm="", n=0) if not l.startswith(("---", "+++", "@@"))]
    return {"caracteres_original": len(antes.rstrip()), "caracteres_bloque_d": len(bloque_d.strip()), "normalizado_original": len(normalizar(antes)), "normalizado_bloque_d": len(normalizar(bloque_d)),
            "literal": antes.strip() == bloque_d.strip(), "normalizada": normalizar(antes) == normalizar(bloque_d), "lineas_no_vacias": (len(a), len(b)), "diferencias": diferencias}


def visible(ruta):
    """Ruta tal como se escribe en un informe versionado: sin el nombre de la carpeta de mensajes ni el de una herramienta (los archivos reales conservan su nombre)."""
    return terminos_vigilados.sustituir(ruta)


def redactar_entrega(entrega, esperados, comando_de_etapa, registro_original, respuesta_etapa_2, guion, nombres):
    """Informe de la verificación de una carpeta de entrega: manifiestos, comandos frente a los mensajes enviados, registro congelado y auditoría automática del registro."""
    L = ["Verificación de la carpeta de entrega de un participante simulado (solo lectura)", "Rutas relativas a la carpeta de entrega; ningún archivo se corrige ni se regenera.",
         "En este informe, en las rutas, la carpeta y los nombres de los mensajes enviados figuran con la palabra «mensaje» y el nombre de una herramienta figura como «herramienta»; los archivos conservan su nombre real.", ""]
    v = verificar_entrega(entrega, esperados)
    L += ["== Manifiestos y archivos ==", f"archivos presentes: {v['presentes']} | manifestados: {v['manifestados']} | faltan: {len(v['faltan'])} | de más: {len(v['de_mas'])} | con tamaño o sha256 distinto: {len(v['tamano_o_sha256_distintos'])}",
          f"manifiesto CSV igual al TXT (rutas y hashes): {v['csv_igual_a_txt']} | rutas repetidas: {len(v['rutas_repetidas'])}",
          f"sha256 esperados proporcionados aparte: {v['esperados']} | que no coinciden: {len(v['esperados_que_no_coinciden'])}"]
    L += [f"  falta: {visible(x)}" for x in v["faltan"]] + [f"  de más: {visible(x)}" for x in v["de_mas"]] + [f"  distinto: {visible(x)}" for x in v["tamano_o_sha256_distintos"]] + [f"  esperado que no coincide: {visible(x)}" for x in v["esperados_que_no_coinciden"]]
    L += ["", "== Archivos de la entrega (ruta | tamaño en bytes | sha256) =="]
    L += [f"{visible(p.relative_to(entrega).as_posix())} | {p.stat().st_size} | {sha256(p)}" for p in archivos(entrega)]
    comandos = {p.name: p.read_text(encoding="utf-8") for p in sorted((entrega / "operaciones").glob("*comando*.txt"))}
    permitidas = {n: comando_de_etapa[n] for n in comandos}
    refs, malas, otros = auditar_operaciones(comandos, permitidas)
    todas = [r for rs in refs.values() for r in rs]
    L += ["", "== Comandos recuperados frente a los mensajes enviados ==", f"comandos: {len(comandos)} | referencias a archivos: {len(todas)} | archivos distintos: {len(set(todas))} | no autorizadas: {len(malas)} | otros cmdlets: {otros or 'ninguno'}",
          f"se cita el documento completo de la lista de comprobación: {any('estado_checklist' in r for r in todas)}"]
    L += [f"  {n}: {r}" for n, rs in refs.items() for r in rs] + [f"  NO AUTORIZADA en {n}: {r}" for n, r in malas]
    bloque_d = respuesta_etapa_2.split("BLOQUE D.", 1)[1].split("BLOQUE E.", 1)[0].split("\n", 1)[1]
    c = comparar_registro_congelado(registro_original, bloque_d)
    L += ["", "== Registro de la etapa 1 frente al bloque D de la etapa 2 ==",
          f"caracteres del original: {c['caracteres_original']} | del bloque D: {c['caracteres_bloque_d']} | normalizados (espacios colapsados): {c['normalizado_original']} y {c['normalizado_bloque_d']}",
          f"coincidencia literal: {c['literal']} | normalizada: {c['normalizada']} | líneas no vacías: {c['lineas_no_vacias'][0]} y {c['lineas_no_vacias'][1]}", "líneas que difieren:"] + [f"  {x}" for x in c["diferencias"]]
    h = auditar_registro(registro_original, guion, nombres)
    L += ["", "== Auditoría automática del registro de la etapa 1 frente al guion ==", f"hallazgos automáticos: {len(h)}"] + [f"  {x}" for x in h] + [""]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------------------------- entrega con fuentes nativas (llamadas en JSON)
def rutas_de_la_lista(mensaje):
    """Rutas `docs/...` de la primera lista de viñetas que sigue a una línea con «puedes abrir»; las listas de rutas prohibidas no cuentan."""
    lineas = mensaje.replace("\r\n", "\n").split("\n")
    for i, linea in enumerate(lineas):
        if "puedes abrir" in linea:
            rutas = []
            for x in lineas[i + 1:]:
                m = re.match(r"^\\?- (docs/[^\s(]+)", x)
                if not m:
                    break
                rutas.append(m.group(1).replace("\\", ""))
            if rutas:
                return rutas
    return []


def propiedades_png(datos):
    """(firma PNG correcta, ancho, alto) leídos de la cabecera; no se interpreta la imagen."""
    firma = datos[:8] == b"\x89PNG\r\n\x1a\n"
    ancho, alto = struct.unpack(">II", datos[16:24]) if len(datos) >= 24 else (0, 0)
    return firma, ancho, alto


def auditar_llamadas(entrega, permitidas_por_etapa, trabajo, maestra):
    """Llamadas recuperadas (`operaciones/etapa_N_llamadas.json`) frente a la lista permitida de la etapa y el texto que devolvieron (traza) frente a la carpeta de trabajo y a la copia maestra.
    Solo lee los documentos y las extracciones derivadas; no abre las transcripciones nativas."""
    salida = []
    base = "\\" + trabajo.name.lower() + "\\"
    for etapa, (propias, esperadas) in permitidas_por_etapa.items():   # propias: las que se añaden en la etapa; esperadas: las permitidas hasta ella
        llamadas = json.loads((entrega / "operaciones" / f"etapa_{etapa}_llamadas.json").read_text(encoding="utf-8-sig"))
        rutas, extra = [], []
        for p in llamadas:
            args = p["tool_calls"][0]["args"]
            ruta = args["Path"].replace("/", "\\")
            i = ruta.lower().find(base)
            rutas.append(ruta[i + len(base):].replace("\\", "/") if i >= 0 else args["Path"])
            extra += [f"{k}={v}" for k, v in args.items() if k != "Path"]
        tiempos = [datetime.strptime(p["created_at"], "%Y-%m-%dT%H:%M:%SZ") for p in llamadas]
        traza = (entrega / "operaciones" / f"etapa_{etapa}_traza_recuperada.txt").read_text(encoding="utf-8-sig")
        bloques = re.split(r"={60}\nINDICE LLAMADA: ", traza)[1:]
        lineas = iguales_trabajo = iguales_maestra = 0
        for b, ruta in zip(bloques, rutas):
            cuerpo = b.split("Showing lines", 1)[1].split("\n", 1)[1]
            texto = []
            for l in cuerpo.splitlines():
                m = re.match(r"^(\d+): ?(.*)$", l)
                if m:
                    texto.append((int(m.group(1)), m.group(2)))
            lineas += len(texto)
            for carpeta, nombre in ((trabajo, "trabajo"), (maestra, "maestra")):
                real = (carpeta / ruta).read_text(encoding="utf-8").splitlines() if (carpeta / ruta).is_file() else None
                if real is not None and len(real) == len(texto) and all(n == i + 1 and t == real[i] for i, (n, t) in enumerate(texto)):
                    if nombre == "trabajo":
                        iguales_trabajo += len(texto)
                    else:
                        iguales_maestra += len(texto)
        salida.append({"etapa": etapa, "pasos": len(llamadas), "herramientas": sorted({c["name"] for p in llamadas for c in p["tool_calls"]}),
                       "resultado_es_paso_mas_uno": all(p["result_step_index"] == p["step_index"] + 1 for p in llamadas), "estados": sorted({p["status"] for p in llamadas}),
                       "rutas": rutas, "no_autorizadas": [r for r in rutas if r not in esperadas], "en_orden": rutas == propias, "cronologico": tiempos == sorted(tiempos),
                       "argumentos_adicionales": extra, "bloques_de_traza": len(bloques), "lineas_de_traza": lineas, "iguales_a_trabajo": iguales_trabajo, "iguales_a_maestra": iguales_maestra,
                       "checklist": any("estado_checklist" in r for r in rutas)})
    return salida


def normalizar_sin_vinetas(texto):
    """Texto con los prefijos de viñeta «- » retirados y los espacios colapsados (la comparación que se hace con un respaldo copiado de una interfaz)."""
    return re.sub(r"\s+", " ", re.sub(r"^\s*-\s+", "", texto.replace("\r\n", "\n"), flags=re.M)).strip()


def bloque_csv(respuesta, etiqueta):
    """Contenido del bloque ```csv que sigue a «BLOQUE <etiqueta>.» en la respuesta de la etapa 2."""
    desde = respuesta.index(f"BLOQUE {etiqueta}.")
    m = re.search(r"```csv\n(.*?)\n```", respuesta[desde:], re.S)
    return m.group(1) if m else ""


def redactar_entrega_nativa(entrega, esperados, trabajo, maestra, guion, nombres):
    """Informe de la verificación de una entrega con fuentes nativas: manifiestos, trece documentos, llamadas, mensajes, respuestas originales, CSV y capturas (solo propiedades técnicas)."""
    L = ["Verificación de una entrega con fuentes nativas de un participante simulado (solo lectura)", "Rutas relativas a la carpeta de entrega; ningún archivo se corrige ni se regenera.",
         "No se abrieron las transcripciones nativas ni los registros nativos de los mensajes: de ellos solo se calcula tamaño y sha256. Las capturas se miden (firma, ancho, alto y sha256) sin interpretarlas.",
         "En este informe, en las rutas, la carpeta y los nombres de los mensajes enviados figuran con la palabra «mensaje»; los archivos conservan su nombre real.", ""]
    v = verificar_entrega(entrega, esperados)
    L += ["== Manifiestos y archivos ==", f"archivos presentes: {v['presentes']} | manifestados: {v['manifestados']} | faltan: {len(v['faltan'])} | de más: {len(v['de_mas'])} | con tamaño o sha256 distinto: {len(v['tamano_o_sha256_distintos'])}",
          f"manifiesto CSV igual al TXT (rutas y hashes): {v['csv_igual_a_txt']} | rutas repetidas: {len(v['rutas_repetidas'])}",
          f"sha256 esperados proporcionados aparte: {v['esperados']} | que no coinciden: {len(v['esperados_que_no_coinciden'])}"]
    L += [f"  falta: {visible(x)}" for x in v["faltan"]] + [f"  de más: {visible(x)}" for x in v["de_mas"]] + [f"  distinto: {visible(x)}" for x in v["tamano_o_sha256_distintos"]] + [f"  esperado que no coincide: {visible(x)}" for x in v["esperados_que_no_coinciden"]]
    L += ["", "== Archivos de la entrega (ruta | tamaño en bytes | sha256) =="] + [f"{visible(p.relative_to(entrega).as_posix())} | {p.stat().st_size} | {sha256(p)}" for p in archivos(entrega)]
    nativas = [p for p in archivos(entrega) if p.parent.name == "fuentes_nativas" or "registro_nativo" in p.name]
    L += ["", f"== Fuentes y registros nativos ({len(nativas)} archivos; no se abrieron) =="] + [f"{visible(p.relative_to(entrega).as_posix())} | {p.stat().st_size} | {sha256(p)}" for p in nativas]
    # trece documentos
    filas = list(csv.DictReader(io.StringIO((entrega / "auditoria" / "integridad_documentos.csv").read_text(encoding="utf-8-sig"))))
    ok_t = sum((trabajo / f["Documento"]).is_file() and sha256(trabajo / f["Documento"]).lower() == f["SHA256Referencia"].lower() for f in filas)
    ok_m = sum((maestra / f["Documento"]).is_file() and sha256(maestra / f["Documento"]).lower() == f["SHA256Referencia"].lower() for f in filas)
    L += ["", "== Documentos de la carpeta de trabajo frente a su referencia ==", f"documentos: {len(filas)} | iguales a la referencia en la carpeta de trabajo: {ok_t} | en la copia maestra: {ok_m}"]
    # mensajes
    carpeta_de_mensajes = next(d for d in sorted(entrega.iterdir()) if d.is_dir() and terminos_vigilados.contiene(d.name, frozenset(terminos_vigilados.MENSAJES)))
    m1 = (carpeta_de_mensajes / "etapa_1_enviado.txt").read_text(encoding="utf-8")
    m2 = (carpeta_de_mensajes / "etapa_2_enviado.txt").read_text(encoding="utf-8")
    preparado = next(iter(sorted(a for a in (entrega / "antecedentes").iterdir() if terminos_vigilados.contiene(a.name, frozenset(terminos_vigilados.MENSAJES)))), None)
    L += ["", "== Mensajes enviados =="]
    if preparado:
        L += [f"caracteres del texto preparado: {len(preparado.read_text(encoding='utf-8'))}"]
    L += [f"caracteres del mensaje de la etapa 1: {len(m1)} | de la etapa 2: {len(m2)} | concatenados con un separador de un carácter: {len(m1) + 1 + len(m2)}"]
    lista_1, lista_2 = rutas_de_la_lista(m1), rutas_de_la_lista(m2)
    permitidas = {1: (lista_1, lista_1), 2: (lista_2, lista_1 + lista_2)}
    L += [f"rutas permitidas en la etapa 1: {len(lista_1)} | añadidas en la etapa 2: {len(lista_2)}"]
    # llamadas
    L += ["", "== Llamadas recuperadas frente a las rutas permitidas y a la traza =="]
    total = 0
    for r in auditar_llamadas(entrega, permitidas, trabajo, maestra):
        L += [f"etapa {r['etapa']}: pasos {r['pasos']} | herramientas {r['herramientas']} | estados {r['estados']} | resultado en el paso siguiente: {r['resultado_es_paso_mas_uno']} | cronológico: {r['cronologico']}",
              f"  rutas en el orden permitido: {r['en_orden']} | no autorizadas: {len(r['no_autorizadas'])} | lectura del documento completo de la lista de comprobación: {r['checklist']} | argumentos adicionales: {r['argumentos_adicionales'] or 'ninguno'}",
              f"  bloques de traza: {r['bloques_de_traza']} | líneas devueltas: {r['lineas_de_traza']} | idénticas a la carpeta de trabajo: {r['iguales_a_trabajo']} | idénticas a la copia maestra: {r['iguales_a_maestra']}"]
        L += [f"  {x}" for x in r["rutas"]] + [f"  NO AUTORIZADA: {x}" for x in r["no_autorizadas"]]
        total += min(r["iguales_a_trabajo"], r["iguales_a_maestra"])
    L += [f"líneas idénticas en las dos carpetas (suma de las etapas): {total}", "Esto se limita a las llamadas recuperadas: no demuestra que no hubiera otras operaciones."]
    # respuestas
    r1 = (entrega / "respuestas" / "etapa_1_original.md").read_text(encoding="utf-8")
    r2 = (entrega / "respuestas" / "etapa_2_original.md").read_text(encoding="utf-8")
    reg = (entrega / "respuestas" / "etapa_2_registro_original.csv").read_bytes()
    cue = (entrega / "respuestas" / "etapa_2_cuestionarios_original.csv").read_bytes()
    bloque_d = r2.split("BLOQUE D.", 1)[1].split("BLOQUE E.", 1)[0].split("\n", 1)[1]
    c = comparar_registro_congelado(r1, bloque_d)
    antes = r1.rstrip("\n")[: -len(LINEA_DE_CONGELACION)]
    L += ["", "== Respuestas originales ==", f"caracteres de la etapa 1: {len(r1)} | de la etapa 2: {len(r2)} | antes de la línea de congelación: {len(antes)} | viñetas «- » en la etapa 1: {len(re.findall(r'^- ', r1, re.M))}",
          f"bloque D igual al registro de la etapa 1 sin su línea final: literal {c['literal']} | normalizada {c['normalizada']} | caracteres {c['caracteres_original']} y {c['caracteres_bloque_d']} | líneas que difieren: {len(c['diferencias'])}",
          f"la línea de congelación aparece dentro del bloque D: {LINEA_DE_CONGELACION in bloque_d} | el bloque D lleva correcciones posteriores: {'Correcciones posteriores' in bloque_d}",
          f"bloque B igual al CSV original: {(bloque_csv(r2, 'B') + chr(10)).encode('utf-8') == reg} | bloque C igual al CSV original: {(bloque_csv(r2, 'C') + chr(10)).encode('utf-8') == cue}"]
    candidato = entrega / "antecedentes" / "candidato_participante_1_registro.csv"
    if candidato.is_file():
        L += [f"candidato histórico del registro idéntico al CSV original, byte a byte: {candidato.read_bytes() == reg}"]
    respaldo = next(iter(sorted((entrega / "antecedentes").glob("respaldo_etapa_1*"))), None)
    if respaldo:
        t = respaldo.read_text(encoding="utf-8")
        L += [f"respaldo histórico: caracteres {len(t)} | viñetas «- » {len(re.findall(r'^- ', t, re.M))} | idéntico al original: {t == r1} | igual tras retirar viñetas y colapsar espacios: {normalizar_sin_vinetas(t) == normalizar_sin_vinetas(r1)} ({len(normalizar_sin_vinetas(t))} y {len(normalizar_sin_vinetas(r1))} caracteres)"]
    # capturas
    L += ["", "== Capturas (solo propiedades técnicas; no se interpretó su contenido) =="]
    inventario_capturas = list(csv.DictReader(io.StringIO((entrega / "auditoria" / "inventario_capturas.csv").read_text(encoding="utf-8-sig"))))
    n_ok = 0
    for f in inventario_capturas:
        d = (entrega / "capturas" / f["Archivo"]).read_bytes()
        firma, ancho, alto = propiedades_png(d)
        ok = firma and len(d) == int(f["Bytes"]) and hashlib.sha256(d).hexdigest().lower() == f["SHA256"].lower() and (ancho, alto) == (int(f["Ancho"]), int(f["Alto"]))
        n_ok += ok
        L += [f"{visible(f['Archivo'])} | {len(d)} | {ancho}x{alto} | {hashlib.sha256(d).hexdigest()} | coincide con su inventario: {ok}"]
    L += [f"capturas que coinciden con su inventario: {n_ok} de {len(inventario_capturas)}; la inspección visual y de privacidad sigue pendiente del facilitador"]
    h = auditar_registro(r1, guion, nombres)
    L += ["", "== Auditoría automática del registro de la etapa 1 frente al guion ==", f"hallazgos automáticos: {len(h)}"] + [f"  {x}" for x in h] + [""]
    return "\n".join(L) + "\n"


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
    ap.add_argument("--carpeta", type=Path)
    ap.add_argument("--commit")
    ap.add_argument("--entrega", type=Path, help="verifica en cambio una carpeta de entrega (manifiestos, comandos, registro congelado); usa --esperado, --mensaje-etapa-1, --mensaje-etapa-2, --respuesta-etapa-1 y --respuesta-etapa-2")
    ap.add_argument("--nativa", action="store_true", help="con --entrega: la entrega trae fuentes nativas y llamadas en JSON; usa --trabajo y --copia-maestra (no abre las transcripciones)")
    ap.add_argument("--trabajo", type=Path, help="carpeta de documentos de la etapa 1 del participante (con --nativa)")
    ap.add_argument("--copia-maestra", type=Path, help="copia maestra del commit (con --nativa)")
    ap.add_argument("--esperado", action="append", default=[], metavar="RUTA=SHA256")
    ap.add_argument("--mensaje-etapa-1", type=Path)
    ap.add_argument("--mensaje-etapa-2", type=Path)
    ap.add_argument("--respuesta-etapa-1", type=Path)
    ap.add_argument("--respuesta-etapa-2", type=Path)
    ap.add_argument("--repo", type=Path, default=ROOT)
    ap.add_argument("--externo", action="append", default=[], metavar="ETIQUETA=RUTA")
    ap.add_argument("--registro", type=Path)
    ap.add_argument("--guion", type=Path, default=ROOT / "docs" / "usuarios" / "guion_sesion.md")
    ap.add_argument("--nombre", action="append", default=[])
    ap.add_argument("--omitir", action="append", default=[], help="carpeta de primer nivel que no se lista (se cita con --externo)")
    ap.add_argument("--salida", type=Path)
    a = ap.parse_args(argv)
    if a.entrega and a.nativa:
        if not (a.trabajo and a.copia_maestra):
            ap.error("con --nativa hacen falta --trabajo y --copia-maestra")
        texto = redactar_entrega_nativa(a.entrega, {e.split("=", 1)[0]: e.split("=", 1)[1] for e in a.esperado}, a.trabajo, a.copia_maestra, a.guion.read_text(encoding="utf-8"), a.nombre)
    elif a.entrega:
        faltan = [n for n in ("mensaje_etapa_1", "mensaje_etapa_2", "respuesta_etapa_1", "respuesta_etapa_2") if getattr(a, n) is None]
        if faltan:
            ap.error(f"con --entrega hacen falta: {', '.join('--' + n.replace('_', '-') for n in faltan)}")
        m1 = rutas_permitidas(a.mensaje_etapa_1.read_text(encoding="utf-8"))
        m2 = rutas_permitidas(a.mensaje_etapa_2.read_text(encoding="utf-8"))
        etapa = lambda nombre: m1 if "etapa_1" in nombre else m1 + m2   # noqa: E731
        comando_de_etapa = {p.name: etapa(p.name) for p in (a.entrega / "operaciones").glob("*comando*.txt")}
        texto = redactar_entrega(a.entrega, {e.split("=", 1)[0]: e.split("=", 1)[1] for e in a.esperado}, comando_de_etapa, a.respuesta_etapa_1.read_text(encoding="utf-8"),
                                 a.respuesta_etapa_2.read_text(encoding="utf-8"), a.guion.read_text(encoding="utf-8"), a.nombre)
    else:
        if not (a.carpeta and a.commit):
            ap.error("hacen falta --carpeta y --commit (o --entrega)")
        texto = None
    if texto is not None:
        if a.salida:
            a.salida.write_text(texto, encoding="utf-8", newline="\n")
            print(f"escrito {a.salida.name}")
        else:
            sys.stdout.reconfigure(encoding="utf-8")
            print(texto, end="")
        return 0
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
