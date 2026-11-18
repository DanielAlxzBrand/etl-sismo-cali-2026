"""Guardianes del método para quitar el pie «Co-Authored-By» de los mensajes de commit (`scripts/historial/limpiar_pies_de_coautoria.py`) y de los hashes que citan los documentos.

Por qué existe: reescribir mensajes cambia el hash de todos los commits desde el primero afectado, y los documentos y las evidencias citan esos hashes. Aquí se comprueba, sin reescribir nada: (1) que el filtro
quite el pie y nada más; (2) las reglas con las que se juzga una reescritura (mismo árbol, autor y fechas; mensaje igual salvo el pie; hash distinto solo desde el primer commit afectado; etiquetas en el
commit equivalente con su tipo y su anotación), con casos dañados a propósito; (3) el mapa de commits y su lectura; y (4) que todo hash de commit que un documento cita exista en el historial o figure en el
mapa de commits (`docs/evidencias/mapa_de_commits.md`, que se escribe al reescribir). El ensayo completo sobre un clon es `python scripts/historial/limpiar_pies_de_coautoria.py --ensayo` (EV-118).
Qué NO demuestra: que la reescritura se haya aplicado (no se ha aplicado) ni que no queden hashes citados con otra forma que la de siete caracteres.
"""
import csv
import importlib.util
import re
import shutil
import subprocess
import sys

from src.common import ROOT

CARPETA = ROOT / "scripts" / "historial"


def _cargar():
    espec = importlib.util.spec_from_file_location("limpiar_pies_de_coautoria", CARPETA / "limpiar_pies_de_coautoria.py")
    modulo = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(modulo)
    return modulo


lp = _cargar()
PIE = "Co-Authored-By: Alguien <alguien@ejemplo.invalido>"


# ---------------------------------------------------------------- el filtro
def test_el_filtro_quita_el_pie_y_la_linea_en_blanco_que_lo_precede():
    assert lp.quitar_pie(f"Asunto\n\nCuerpo con texto.\n\n{PIE}\n") == "Asunto\n\nCuerpo con texto.\n"
    assert lp.quitar_pie(f"Asunto\n\n{PIE}\n") == "Asunto\n"
    assert lp.quitar_pie(f"Asunto\n\n{PIE}\n{PIE.lower()}\n\n\n") == "Asunto\n", "dos pies y líneas en blanco al final"
    assert lp.quitar_pie("Asunto\r\n\r\nCuerpo\r\n") == "Asunto\n\nCuerpo\n", "los saltos de línea de Windows pasan a LF"


def test_el_filtro_no_toca_un_mensaje_sin_pie_ni_una_linea_que_solo_menciona_la_palabra():
    sin_pie = "Asunto\n\nCuerpo en dos líneas.\nSegunda línea.\n"
    assert lp.quitar_pie(sin_pie) == sin_pie
    mencion = "Asunto\n\nSe quitó el pie Co-Authored-By de los mensajes.\n"
    assert lp.quitar_pie(mencion) == mencion, "solo se quita una línea que EMPIEZA con el pie"
    assert lp.quitar_pie(lp.quitar_pie(f"A\n\n{PIE}\n")) == "A\n", "aplicarlo dos veces da lo mismo"


def test_el_filtro_funciona_como_comando_de_git_filter_branch():
    r = subprocess.run([sys.executable, str(CARPETA / "limpiar_pies_de_coautoria.py"), "--filtrar-mensaje"], input=f"Asunto\n\ncuerpo\n\n{PIE}\n".encode("utf-8"), capture_output=True, cwd=ROOT)
    assert r.returncode == 0 and r.stdout.decode("utf-8") == "Asunto\n\ncuerpo\n"


# ---------------------------------------------------------------- las reglas con las que se juzga una reescritura
def _commit(n, mensaje="Asunto\n"):
    return {"hash": str(n) * 40, "arbol": "a" * 39 + str(n), "autor": f"Ana <a@x> 2026-11-0{n}T10:00:00-05:00", "committer": f"Ana <a@x> 2026-11-0{n}T10:00:00-05:00", "mensaje": mensaje}


def _historia():
    """Cuatro commits; el tercero (índice 2) es el primero con pie. Devuelve (viejos, nuevos, etiquetas viejas, etiquetas nuevas)."""
    viejos = [_commit(1), _commit(2), _commit(3, f"Tres\n\n{PIE}\n"), _commit(4, f"Cuatro\n\n{PIE}\n")]
    nuevos = [dict(viejos[0]), dict(viejos[1]), {**viejos[2], "hash": "b3" * 20, "mensaje": "Tres\n"}, {**viejos[3], "hash": "b4" * 20, "mensaje": "Cuatro\n"}]
    ev = {"antes": ("commit", viejos[1]["hash"], "", ""), "despues": ("commit", viejos[3]["hash"], "", ""), "anotada": ("tag", viejos[2]["hash"], "Ana <a@x> 2026-11-03", "Nota")}
    en = {"antes": ("commit", nuevos[1]["hash"], "", ""), "despues": ("commit", nuevos[3]["hash"], "", ""), "anotada": ("tag", nuevos[2]["hash"], "Ana <a@x> 2026-11-03", "Nota")}
    return viejos, nuevos, ev, en


def test_una_reescritura_correcta_no_tiene_problemas():
    viejos, nuevos, ev, en = _historia()
    assert lp.problemas_de_la_reescritura(viejos, nuevos, ev, en, viejos[2]["hash"]) == []


def test_una_reescritura_defectuosa_se_detecta_en_cada_regla():
    viejos, nuevos, ev, en = _historia()
    primero = viejos[2]["hash"]

    def con(i, **cambios):
        otros = [dict(n) for n in nuevos]
        otros[i] = {**otros[i], **cambios}
        return otros
    assert lp.problemas_de_la_reescritura(viejos, con(3, arbol="b" * 40), ev, en, primero), "el árbol cambió"
    assert lp.problemas_de_la_reescritura(viejos, con(2, autor="Otra <o@x> 2026-11-03T10:00:00-05:00"), ev, en, primero), "cambió el autor"
    assert lp.problemas_de_la_reescritura(viejos, con(2, committer="Ana <a@x> 2026-12-01T10:00:00-05:00"), ev, en, primero), "cambió una fecha"
    assert lp.problemas_de_la_reescritura(viejos, con(3, mensaje="Cuatro y algo más\n"), ev, en, primero), "el mensaje cambió más que el pie"
    assert lp.problemas_de_la_reescritura(viejos, con(3, mensaje=f"Cuatro\n\n{PIE}\n"), ev, en, primero), "queda un pie"
    assert lp.problemas_de_la_reescritura(viejos, con(0, hash="9" * 40), ev, en, primero), "un commit anterior cambió de hash"
    assert lp.problemas_de_la_reescritura(viejos, con(2, hash=viejos[2]["hash"]), ev, en, primero), "un commit afectado conservó su hash"
    assert lp.problemas_de_la_reescritura(viejos, nuevos[:3], ev, en, primero), "faltan commits"
    assert lp.problemas_de_la_reescritura(viejos, nuevos, ev, en, "f" * 40), "el primer afectado no está en la rama"


def test_las_etiquetas_se_comprueban_por_nombre_tipo_anotacion_y_destino():
    viejos, nuevos, ev, en = _historia()
    primero = viejos[2]["hash"]
    sin_una = {k: v for k, v in en.items() if k != "anotada"}
    assert lp.problemas_de_la_reescritura(viejos, nuevos, ev, sin_una, primero), "falta una etiqueta"
    assert lp.problemas_de_la_reescritura(viejos, nuevos, ev, {**en, "otra": ("commit", nuevos[0]["hash"], "", "")}, primero), "sobra una etiqueta"
    assert lp.problemas_de_la_reescritura(viejos, nuevos, ev, {**en, "despues": ("commit", viejos[3]["hash"], "", "")}, primero), "una etiqueta quedó en el commit viejo"
    assert lp.problemas_de_la_reescritura(viejos, nuevos, ev, {**en, "anotada": ("tag", nuevos[2]["hash"], "Ana <a@x> 2026-11-03", "Otra nota")}, primero), "cambió la anotación"
    assert lp.problemas_de_la_reescritura(viejos, nuevos, ev, {**en, "anotada": ("commit", nuevos[2]["hash"], "", "")}, primero), "una etiqueta anotada pasó a ligera"
    assert lp.problemas_de_la_reescritura(viejos, nuevos, ev, {**en, "antes": ("commit", nuevos[0]["hash"], "", "")}, primero), "una etiqueta de commits anteriores se movió"


# ---------------------------------------------------------------- el mapa
def test_el_mapa_lista_solo_los_commits_que_cambian_y_se_lee_de_vuelta():
    viejos, nuevos, _, _ = _historia()
    texto = lp.tabla_del_mapa(viejos, nuevos, viejos[2]["hash"])
    mapa = lp.leer_mapa(texto)
    assert mapa == {viejos[2]["hash"][:7]: nuevos[2]["hash"][:7], viejos[3]["hash"][:7]: nuevos[3]["hash"][:7]}
    assert viejos[0]["hash"][:7] not in mapa and "| Tres |" in texto and "| Cuatro |" in texto
    assert lp.leer_mapa("| no es un hash | nada |") == {}


# ---------------------------------------------------------------- los hashes que citan los documentos
def _leer_inventario():
    lineas = (lp.INVENTARIO).read_text(encoding="utf-8").splitlines()
    primero = re.fullmatch(r"# primer_commit_afectado: ([0-9a-f]{7})", lineas[0]).group(1)
    return primero, list(csv.DictReader(lineas[1:]))


def _hay_git():
    return (ROOT / ".git").exists() and shutil.which("git") is not None


def test_cada_cita_del_inventario_sigue_en_su_archivo():
    _, filas = _leer_inventario()
    assert len(filas) >= 30
    faltan = [(f["archivo"], f["hash"]) for f in filas if not re.search(rf"\b{f['hash']}[0-9a-f]*\b", (ROOT / f["archivo"]).read_text(encoding="utf-8"))]
    assert faltan == [], "el inventario cita algo que el archivo ya no dice: hay que regenerarlo con --inventariar"


def test_todo_hash_citado_existe_en_el_historial_o_esta_en_el_mapa_de_commits():
    if not _hay_git():
        return   # el zip no trae el historial
    _, filas = _leer_inventario()
    mapa_ruta = ROOT / lp.MAPA
    mapa = lp.leer_mapa(mapa_ruta.read_text(encoding="utf-8")) if mapa_ruta.is_file() else {}
    faltan = sorted({(f["archivo"], f["hash"]) for f in filas if not lp.existe_commit(ROOT, f["hash"]) and f["hash"] not in mapa})
    assert faltan == [], f"estos hashes citados no existen y no están en el mapa de commits: {faltan[:6]}"
    nuevos = [n for v, n in mapa.items() if not lp.existe_commit(ROOT, n)]
    assert nuevos == [], f"hashes nuevos del mapa que no existen: {nuevos[:6]}"
    viejos_que_existen = [v for v in mapa if lp.existe_commit(ROOT, v)]
    assert viejos_que_existen == [], "un hash anterior del mapa todavía existe: el mapa no corresponde a este historial"


def test_el_inventario_incluye_toda_cita_a_un_commit_del_rango_mientras_esos_commits_existan_hash():
    if not _hay_git():
        return
    primero, filas = _leer_inventario()
    if not lp.existe_commit(ROOT, primero):
        return   # el historial ya se reescribió: las citas se comprueban contra el mapa
    rango = lp.git(ROOT, "rev-list", f"{primero}^..HEAD").split()
    citadas = {(f, h) for f, h in lp.citas_de_commits(ROOT, {h[:7] for h in rango})}
    inventariadas = {(f["archivo"], f["hash"]) for f in filas}
    assert sorted(citadas - inventariadas) == [], "hay citas a commits del rango que el inventario no trae: regenerarlo con --inventariar"


def test_la_comprobacion_de_hashes_falla_si_un_hash_citado_no_existe_ni_esta_en_el_mapa():
    mapa = lp.leer_mapa("| Hash anterior | Hash nuevo | Asunto |\n|---|---|---|\n| aaaaaaa | bbbbbbb | uno |\n")
    citados = ["aaaaaaa", "ccccccc"]
    assert [h for h in citados if h not in mapa] == ["ccccccc"], "un hash que no existe ni está en el mapa se detecta"
    assert mapa == {"aaaaaaa": "bbbbbbb"}
