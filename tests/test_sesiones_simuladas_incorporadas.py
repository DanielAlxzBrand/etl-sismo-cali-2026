"""Las sesiones simuladas que se incorporan al repositorio (D109): rotuladas, sin herramientas ni personas, sin cifras medidas y con su registro de la etapa 1 intacto.

Por qué existe: dos sesiones simuladas se hicieron fuera del repositorio con herramientas de elaboración, y lo único que puede entrar es lo que está completo, en su versión original y sin nombrar esas
herramientas (la declaración de la raíz es el único lugar que las nombra). Esta prueba comprueba que cada archivo de sesiones lleve el rótulo, que nada nombre herramientas fuera de la declaración,
que `sesiones_reales/` no tenga nada simulado, que el registro de la etapa 1 sea el que se firmó con su sha256 y cumpla el guion, y que el inventario de la carpeta de trabajo detecte lo que debe.
Qué NO demuestra: que el texto sea el que escribió quien simuló la sesión (hay un respaldo, no el original), que las correcciones posteriores sean todas las posibles ni que el panel sea usable.
"""
import hashlib
import importlib.util
import json
import re
import subprocess

import pytest

from src.common import ROOT

_spec = importlib.util.spec_from_file_location("inventariar_sesiones_simuladas", ROOT / "scripts" / "usuarios" / "inventariar_sesiones_simuladas.py")
inv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(inv)
_spec_md = importlib.util.spec_from_file_location("make_dist_sesiones", ROOT / "scripts" / "make_dist.py")
make_dist = importlib.util.module_from_spec(_spec_md)
_spec_md.loader.exec_module(make_dist)

USUARIOS = ROOT / "docs" / "usuarios"
SIMULADAS = USUARIOS / "sesiones_simuladas"
REALES = USUARIOS / "sesiones_reales"
REGISTRO = SIMULADAS / "participante_simulado_1_etapa_1.md"
REGISTRO_2 = SIMULADAS / "participante_simulado_2_etapa_1.md"
GUION = (USUARIOS / "guion_sesion.md").read_text(encoding="utf-8")
BANNER = "Sesión simulada, no realizada con una persona real"
# Las cadenas se parten para que este archivo no se detecte a sí mismo.
NOMBRES_NUEVOS = re.compile("Co" + "dex|Anti" + "gravity|GP" + r"T-?\d")
PERSONAS = ("Daniel", "Brand", "Gordillo", "Castellanos", "Diego", "Jhoan", "Zulma", "Cuervo")
SUFIJOS = {".md", ".py", ".txt", ".yaml", ".yml", ".ini", ".ipynb", ".csv", ".json", ".jsonl", ".diff", ".sha256", ".xml", ".example"}


def _bloque_del_registro(ruta=REGISTRO):
    return re.search(r"```text\n(.*?)\n```", ruta.read_text(encoding="utf-8"), re.S).group(1)


# (archivo, participante, perfil, sha256 del texto recuperado antes de limpiar, líneas del bloque, filas de correcciones)
REGISTROS = [(REGISTRO, "Participante simulado 1", "habitante", "78db8ba7958db5a77709deb927efdf438ca2997acc0eec7f1f1ee1ab5a1221c8", 68, 8),
             (REGISTRO_2, "Participante simulado 2", "institucional", "328649c9e1d071ecc95733a76365ce57cea3d0644aa465729dc24ab500d779d5", 54, 3)]


# ---------------------------------------------------------------- rótulo, herramientas y carpeta de sesiones reales
def test_cada_archivo_de_sesiones_simuladas_y_su_resumen_llevan_el_rotulo():
    mds = sorted(SIMULADAS.glob("*.md")) + [USUARIOS / "resultados_sesiones_simuladas.md"]
    assert {p.name for p in mds} >= {"README.md", "plantilla_registro.md", "participante_simulado_1_etapa_1.md", "participante_simulado_2_etapa_1.md", "resultados_sesiones_simuladas.md"}
    for p in mds:
        assert BANNER in p.read_text(encoding="utf-8"), f"{p.name} sin el rótulo «{BANNER}»"
    for p in sorted(SIMULADAS.glob("*.csv")):
        assert "simulada" in p.read_text(encoding="utf-8"), f"{p.name}: sus filas llevan origen = simulada"


def _archivos_del_zip():
    for p in make_dist.listar(ROOT):
        rel = p.relative_to(ROOT).as_posix()
        if p.suffix in SUFIJOS and rel.split("/")[0] != "data" and not make_dist.es_documento_aislado(rel):
            yield rel, p.read_text(encoding="utf-8", errors="ignore")


def test_ningun_archivo_del_zip_nombra_las_herramientas_de_las_sesiones_simuladas_fuera_de_la_declaracion():
    n, hallazgos = 0, []
    for rel, texto in _archivos_del_zip():
        n += 1
        if NOMBRES_NUEVOS.search(texto) or inv.HERRAMIENTAS.search(texto) and rel.startswith(("docs/usuarios/", "docs/evidencias/usuarios/")):
            hallazgos.append(rel)
    assert n > 300
    assert hallazgos == []


def test_la_negativa_del_nombre_de_una_herramienta_se_dispara():
    assert NOMBRES_NUEVOS.search("la hizo " + "Co" + "dex") and NOMBRES_NUEVOS.search("modelo " + "GP" + "T-6.1")
    assert not NOMBRES_NUEVOS.search("el registro de la etapa 1, sin cifras")


def test_sesiones_reales_no_trae_nada_simulado_ni_un_participante_simulado():
    assert list(REALES.rglob("*simulad*")) == []
    for p in sorted(REALES.rglob("*")):
        if p.is_file() and p.suffix in SUFIJOS:
            texto = p.read_text(encoding="utf-8")
            assert not re.search(r"Participante simulado \d", texto) and "simulado, no medido" not in texto, p.name


# ---------------------------------------------------------------- registro de la etapa 1 del participante 1
@pytest.mark.parametrize("ruta, participante, perfil, sha_original, n_lineas, _n", REGISTROS)
def test_el_registro_de_la_etapa_1_es_el_firmado_y_cumple_el_guion(ruta, participante, perfil, sha_original, n_lineas, _n):
    texto = ruta.read_text(encoding="utf-8")
    bloque = _bloque_del_registro(ruta)
    sha_limpio = hashlib.sha256((bloque + "\n").encode("utf-8")).hexdigest()
    assert f"`{sha_limpio}`" in texto, "el sha256 del texto limpio citado debe ser el del bloque"
    original = re.search(r"antes de limpiar:\*\* `([0-9a-f]{64})`", texto).group(1)
    assert original != sha_limpio and original == sha_original
    assert inv.auditar_registro(bloque, GUION, PERSONAS) == []
    assert bloque.split("\n")[-1] == inv.LINEA_DE_CONGELACION and len(bloque.split("\n")) == n_lineas
    assert "\r" not in texto and participante in texto and f"`{perfil}`" in texto and "2026-11-18" in texto
    assert BANNER in texto and "El registro de arriba no se toca" in texto


@pytest.mark.parametrize("ruta, participante, perfil, sha_original, n_lineas, n_correcciones", REGISTROS)
def test_las_correcciones_posteriores_citan_lineas_del_registro_y_no_lo_reescriben(ruta, participante, perfil, sha_original, n_lineas, n_correcciones):
    texto = ruta.read_text(encoding="utf-8")
    n = len(_bloque_del_registro(ruta).split("\n"))
    seccion = texto.split("## Correcciones posteriores", 1)[1].split("\n## ", 1)[0]   # la tabla original; la reconciliación posterior tiene la suya
    filas = re.findall(r"^\| (C\d) \| ([^|]+) \|", seccion, re.M)
    assert [f[0] for f in filas] == [f"C{i}" for i in range(1, n_correcciones + 1)]
    for _, lineas in filas:
        assert all(1 <= int(x) <= n for x in re.findall(r"\d+", lineas)), lineas


def _csv_de_un_participante(nombre, participante):
    """Cabecera más las filas de un participante, tal como estaba su CSV original."""
    lineas = (SIMULADAS / nombre).read_text(encoding="utf-8").split("\n")
    return "\n".join([lineas[0]] + [l for l in lineas[1:] if l.startswith(participante + ",")]) + "\n"


def test_los_csv_de_cada_participante_son_identicos_a_sus_originales_y_los_registros_citan_su_sha256():
    texto_1, texto_2 = REGISTRO.read_text(encoding="utf-8"), REGISTRO_2.read_text(encoding="utf-8")
    originales_1 = {"registro.csv": "61b33af5154a77c3cd924cafcaa470f328df3d08cbf47b14e9f0684a0d645621", "cuestionarios.csv": "3603749cabc9b406d7614111524b439a8ea2c862a4a5a79f4bcacb96651429cf"}
    originales_2 = {"registro.csv": "0326f148b8d1e25ee6ae64778649a2535c3235a5827a8805199f3398466c3033", "cuestionarios.csv": "81f447c53ae38a31e049972360c6b0312c849083db8179a5335061aa1aaeda2e"}
    for nombre in ("registro.csv", "cuestionarios.csv"):
        assert hashlib.sha256(_csv_de_un_participante(nombre, "Participante simulado 1").encode("utf-8")).hexdigest() == originales_1[nombre], f"{nombre}: filas del participante 1"
        assert hashlib.sha256(_csv_de_un_participante(nombre, "Participante simulado 2").encode("utf-8")).hexdigest() == originales_2[nombre], f"{nombre}: filas del participante 2"
        assert f"`{originales_2[nombre]}`" in texto_2, f"{nombre}: el sha256 citado del participante 2"
    for sha in originales_1.values():
        assert f"`{sha}`" in texto_1, "el sha256 citado del participante 1"
    assert "no lo reconstruimos desde un informe" not in texto_1 and "`registro.csv`" in texto_1 and "`cuestionarios.csv`" in texto_1
    assert "Bloque D de la etapa 2: no es la fuente" in texto_2 and "omitió el signo de apertura" in texto_2 and "`7374c40b68166d347fb6ec7a2906424c4224c1341121d72b92816a793fd50a60`" in texto_2


def test_los_csv_de_sesiones_simuladas_son_de_los_dos_participantes_y_los_acepta_el_analizador():
    spec = importlib.util.spec_from_file_location("analizar_sesiones_incorporadas", ROOT / "scripts" / "usuarios" / "analizar_sesiones.py")
    an = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(an)
    registro, cuestionarios = an.cargar_simuladas(SIMULADAS)
    assert [f["participante"] for f in registro] == ["Participante simulado 1"] * 6 + ["Participante simulado 2"] * 6, "primero las seis filas del 1 y luego las del 2"
    assert [f["tarea"] for f in registro] == [f"T{i}" for i in range(1, 7)] * 2 and [f["participante"] for f in cuestionarios] == ["Participante simulado 1", "Participante simulado 2"]
    assert {(f["participante"], f["perfil"]) for f in registro + cuestionarios} == {("Participante simulado 1", "habitante"), ("Participante simulado 2", "institucional")}
    assert {f["fecha"] for f in registro + cuestionarios} == {"2026-11-18"} and {f["origen"] for f in registro + cuestionarios} == {"simulada"}
    medidas = [f[c] for f in registro for c in ("resultado", "tiempo_s", "ayudas", "errores")] + [v for f in cuestionarios for k, v in f.items() if k.startswith(("sus_", "csat"))]
    assert len(medidas) == 24 * 2 + 11 * 2 and set(medidas) == {"simulado, no medido"}, "ninguna cifra medida: 35 campos por participante"
    for f in registro:
        assert not re.search(r"\d", f["comentario_breve"]) and not inv.HERRAMIENTAS.search(f["comentario_breve"]) and not any(p in f["comentario_breve"] for p in PERSONAS)
    for ruta in (SIMULADAS / "registro.csv", SIMULADAS / "cuestionarios.csv"):
        datos = ruta.read_bytes()
        assert b"\r" not in datos and datos.endswith(b"\n") and not datos.startswith(b"\xef\xbb\xbf")
    from tests.test_readme_cifras import hay_sesiones_reales
    assert hay_sesiones_reales(SIMULADAS) is False, "las filas simuladas no cuentan como reales"
    assert (USUARIOS / "resultados_sesiones_simuladas.md").read_text(encoding="utf-8") == an.redactar_simuladas(registro, cuestionarios, an.registros_de_etapa_1(SIMULADAS))


def _registro_valido():
    return _bloque_del_registro()


@pytest.mark.parametrize("cambio, esperado", [
    (lambda t: t.replace("no verificado: lectura", "sin marca", 1), "marca"),
    (lambda t: t.replace("«¿Hay algún estrato", "«Hay algún estrato", 1), "literal"),
    (lambda t: t.replace("TAREA T3", "TAREA T9", 1), "T1 a T6"),
    (lambda t: t + "\nuna línea más", "congelación"),
    (lambda t: t.replace("Me confundieron términos", "Con Co" + "dex me confundieron términos", 1), "herramienta o modelo"),
    (lambda t: t.replace("Como no tengo el panel abierto", "Hice clic en el panel y como no tengo el panel abierto", 1), "afirma haber usado"),
    (lambda t: t.replace("Lo que me confundió o me faltó: Me confundieron", "Lo que me confundió o me faltó: En 12 segundos me confundieron", 1), "cifra medida"),
    (lambda t: t.replace("Me faltó ver los datos", "Daniel dijo que me faltó ver los datos", 1), "nombre de persona"),
    (lambda t: t.replace("«¿Qué cambiaría para que le resultara más claro?»", "«otra pregunta»", 1), "falta la respuesta"),
    (lambda t: t.replace("Dónde busco y por qué:", "Dónde busco:", 1), "campos"),
])
def test_negativas_la_auditoria_detecta_cada_cambio_al_registro(cambio, esperado):
    cambiado = cambio(_registro_valido())
    assert cambiado != _registro_valido(), "la mutación debe cambiar el texto"
    assert any(esperado in h for h in inv.auditar_registro(cambiado, GUION, PERSONAS))


# ---------------------------------------------------------------- declaración de la raíz
DATOS_DE_LA_DECLARACION = ("Anti" + "gravity", "Gem" + "ini 3.8 Flash", "Co" + "dex", "GP" + "T-6.1 Terra", "alto", "2026-11-18", "3157ee2a450e8adfd834c11ae43d880d9adaf57f", "636 de 636",
                           "Cla" + "ude Code", "Request Review", "Solicitar aprobación", "Get-Content -LiteralPath", "comuna vecina", "Decidimos", "siguen pendientes", "No tenemos", "[COMPLETAR POR DANIEL",
                           "78db8ba7958db5a77709deb927efdf438ca2997acc0eec7f1f1ee1ab5a1221c8", "feedback de personas usuarias", "Chat" + "GPT", "EV-120", "Co" + "dexSandboxUsers", "una línea de 48 distinta",
                           "726a5aa036ab03179aa279e04d88d31f38aa0df40b0d44364acbd1c02eaceaf4", "7374c40b68166d347fb6ec7a2906424c4224c1341121d72b92816a793fd50a60", "reconstrucciones a partir de resultados comunicados",
                           "Entrega recuperada del participante 1", "f4b83480839008060abadd1d6f69e1938974fa2d1d3cf592306a2403abeca78c", "1c357e22f896ba58d91228728b8153332c92f68c5f867dfb8b75eb36552647f7",
                           "no son fuentes independientes", "385 líneas idénticas", "no los damos por equivalentes")


def problemas_de_la_declaracion(texto):
    """Lo que falta o sobra en la sección de sesiones simuladas de la declaración (lista vacía si cumple)."""
    if "## 6. Sesiones de usuario simuladas" not in texto or "## 7." not in texto:
        return ["falta la sección 6 o la 7"]
    seccion = texto.split("## 6. Sesiones de usuario simuladas", 1)[1].split("## 7.", 1)[0]
    errores = [f"falta: {d}" for d in DATOS_DE_LA_DECLARACION if d not in seccion]
    if len(set(re.findall(r"`([0-9a-f]{64})`", seccion))) != 35:
        errores.append("deben citarse 35 sha256 distintos: los dos archivos de instrucciones, el respaldo, los dos informes, los 8 de la entrega del participante 2, los 12 de la del participante 1 y las 10 capturas")
    if re.search(r"(?i)exclusivamente (documental|por lectura)", texto):
        errores.append("no se dice «exclusivamente documental»")
    if "COMPLETAR POR DANIEL" not in texto or "COMPLETAR POR EL EQUIPO" not in texto:
        errores.append("deben quedar marcados los pendientes: los de Daniel y los del equipo")
    insignia = re.search(r'aria-label="pruebas: (\d+)"', (ROOT / "docs" / "img" / "insignias" / "pruebas.svg").read_text(encoding="utf-8"))
    cita = re.search(r"pasó (\d+) pruebas el", texto)
    if not (insignia and cita and insignia.group(1) == cita.group(1)):
        errores.append("el recuento de pruebas de la declaración debe ser el de la insignia del README")
    viejas = ("Avan" + "ce 2", "pasa 28 " + "pruebas", "`docs/prueba_entorno" + "_limpio.md`", "`docs/verificacion" + "_logging.md`", "`docs/investigacion" + "_fuentes.md`", "`docs/verificacion" + "_fuentes.md`")
    if any(v in texto for v in viejas):
        errores.append("cifras o rutas viejas en la declaración")
    if "Cumple" in seccion:
        errores.append("la sección no puede declarar que un ítem cumple")
    if "## 7. Excepción de evidencia simulada" not in texto or "## 8. Fecha de la declaración" not in texto:
        errores.append("falta la sección 7 de la excepción o la 8 de la fecha")
    else:
        excepcion = texto.split("## 7. Excepción de evidencia simulada", 1)[1].split("## 8.", 1)[0]
        errores += [f"la sección 7 debe decir: {d}" for d in ("el do" + "cente responsable de la lista de verificación", "La auto" + "rización fue verbal", "ningún registro escrito", "no se pedirá otra confirmación",
                                                          "fecha no recordada con precisión", "D111", "nunca «Cumple» a secas", "evidencia simulada, sin personas reales", "se anotan aparte") if d not in excepcion]
        if re.search(r"(?i)\b(pro" + "fesor|nombre del do" + "cente)\b", excepcion):
            errores.append("la sección 7 no nombra al docente")
    return errores


def test_la_declaracion_cita_las_dos_sesiones_con_sus_datos_y_lo_pendiente():
    assert problemas_de_la_declaracion((ROOT / ("DECLARACION" + "_USO_IA.md")).read_text(encoding="utf-8")) == []


def test_negativas_de_la_declaracion_cada_dato_que_falta_o_sobra_se_detecta():
    base = (ROOT / ("DECLARACION" + "_USO_IA.md")).read_text(encoding="utf-8")
    for dato in ("Solicitar aprobación", "comuna vecina", "No tenemos", "2026-11-18", "GP" + "T-6.1 Terra"):
        assert problemas_de_la_declaracion(base.replace(dato, "otra cosa")), dato
    sha = "78db8ba7958db5a77709deb927efdf438ca2997acc0eec7f1f1ee1ab5a1221c8"
    assert problemas_de_la_declaracion(base.replace(sha, "0" * 64)), "un sha256 distinto del conservado"
    assert problemas_de_la_declaracion(base.replace(sha, "e47916832e38f7664bc6621b344e0f7cf68a2257bbbbfbf4a84e4f76af550f2f")), "dos sha256 iguales dejan 24 distintos"
    assert problemas_de_la_declaracion(base.replace("f4b83480839008060abadd1d6f69e1938974fa2d1d3cf592306a2403abeca78c", "0" * 64)), "un sha256 de la entrega del participante 1"
    assert problemas_de_la_declaracion(base.replace("EV-120", "EV-999")) and problemas_de_la_declaracion(base.replace("una línea de 48 distinta", "otra cosa")), "la evidencia y la incidencia comprobada del participante 2"
    assert problemas_de_la_declaracion(base.replace("siguen pendientes", "Cumple")), "una sesión simulada no cumple ningún ítem"
    assert problemas_de_la_declaracion(base.replace("## 7.", "## 8.")), "sin la sección 7 no hay dónde acaba la 6"


# ---------------------------------------------------------------- inventario de la carpeta de trabajo
def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=prueba", "-c", "user.email=prueba@example.org", "-c", "core.autocrlf=false", *args], check=True, capture_output=True)


@pytest.fixture
def carpeta(tmp_path):
    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    (repo / "docs" / "a.md").write_bytes(b"uno\ndos\r\n")
    (repo / "b.txt").write_bytes(b"b\n")
    _git(repo, "init", "-q")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    trabajo = tmp_path / "trabajo"
    for destino in (trabajo / inv.MAESTRA, trabajo / "p1_etapa_1"):
        (destino / "docs").mkdir(parents=True)
        (destino / "docs" / "a.md").write_bytes(b"uno\ndos\r\n")
    (trabajo / inv.MAESTRA / "b.txt").write_bytes(b"b\n")
    (trabajo / "varios").mkdir()
    (trabajo / "varios" / "p.txt").write_text("texto", encoding="utf-8")
    return repo, trabajo


def _commit(repo):
    return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, capture_output=True, text=True, encoding="utf-8").stdout.strip()


def test_el_inventario_lista_lo_que_hay_sin_la_copia_maestra_con_tamano_y_sha256(carpeta):
    _, trabajo = carpeta
    filas = {f["ruta"]: f for f in inv.inventario(trabajo)}
    assert set(filas) == {"p1_etapa_1/docs/a.md", "varios/p.txt"}
    assert set(f["ruta"] for f in inv.inventario(trabajo, omitir=("varios",))) == {"p1_etapa_1/docs/a.md"}, "una carpeta omitida no se lista"
    assert filas["p1_etapa_1/docs/a.md"]["tamano"] == 9 and filas["p1_etapa_1/docs/a.md"]["sha256"] == hashlib.sha256(b"uno\ndos\r\n").hexdigest()


def test_la_comparacion_distingue_iguales_modificados_y_de_mas(carpeta):
    _, trabajo = carpeta
    assert inv.comparar(trabajo / "p1_etapa_1", trabajo / inv.MAESTRA) == {"iguales": ["docs/a.md"], "distintos": [], "de_mas": []}
    (trabajo / "p1_etapa_1" / "docs" / "a.md").write_bytes(b"cambiado")
    (trabajo / "p1_etapa_1" / "nota.txt").write_text("de más", encoding="utf-8")
    r = inv.comparar(trabajo / "p1_etapa_1", trabajo / inv.MAESTRA)
    assert r["distintos"] == ["docs/a.md"] and r["de_mas"] == ["nota.txt"] and r["iguales"] == []


def test_la_verificacion_de_la_copia_maestra_usa_el_hash_de_blob_sin_filtros_y_detecta_cambios(carpeta):
    repo, trabajo = carpeta
    maestra = trabajo / inv.MAESTRA
    v = inv.verificar_maestra(maestra, repo, _commit(repo))
    assert v == {"esperados": 2, "identicos": 2, "distintos": [], "faltan": [], "de_mas": []}, "los saltos de línea CRLF no cambian el hash"
    (maestra / "docs" / "a.md").write_bytes(b"uno\ndos\n")
    (maestra / "b.txt").unlink()
    (maestra / "extra.txt").write_text("x", encoding="utf-8")
    v = inv.verificar_maestra(maestra, repo, _commit(repo))
    assert v["distintos"] == ["docs/a.md"] and v["faltan"] == ["b.txt"] and v["de_mas"] == ["extra.txt"] and v["identicos"] == 0


def test_el_informe_completo_no_nombra_herramientas_ni_rutas_absolutas_y_cita_los_externos_por_etiqueta(carpeta, tmp_path):
    repo, trabajo = carpeta
    externo = tmp_path / "informe externo.txt"
    externo.write_text("contenido", encoding="utf-8")
    texto = inv.redactar(trabajo, _commit(repo), repo, [("informe_de_la_ejecucion", externo)], REGISTRO, USUARIOS / "guion_sesion.md", PERSONAS, omitir=("varios",))
    assert "p1_etapa_1: 1 iguales, 0 modificados, 0 de más" in texto and "varios" not in texto.split("== Cada carpeta")[1] and "2 archivos esperados, 2 idénticos" in texto
    assert f"informe_de_la_ejecucion | 9 | {hashlib.sha256(b'contenido').hexdigest()}" in texto and "hallazgos automáticos: 0" in texto
    assert str(tmp_path) not in texto and not NOMBRES_NUEVOS.search(texto) and not inv.HERRAMIENTAS.search(texto)


def test_la_evidencia_de_la_incorporacion_existe_cita_la_copia_y_no_nombra_herramientas():
    ruta = ROOT / "docs" / "evidencias" / "usuarios" / "EV-119_incorporacion_de_sesiones_simuladas.txt"
    texto = ruta.read_text(encoding="utf-8")
    assert "636 archivos esperados, 636 idénticos, 0 distintos, 0 que faltan, 0 de más" in texto
    assert "habitante_etapa_1: 13 iguales, 0 modificados, 0 de más" in texto and "institucional_etapa_1: 14 iguales, 0 modificados, 0 de más" in texto
    assert "hallazgos automáticos: 0" in texto and "C:\\" not in texto and "AlexD" not in texto
    assert not NOMBRES_NUEVOS.search(texto) and not inv.HERRAMIENTAS.search(texto)


# ---------------------------------------------------------------- carpeta de entrega del participante 2
def _entrega(tmp_path, bom=True):
    e = tmp_path / "entrega"
    (e / "operaciones").mkdir(parents=True)
    (e / "respuestas").mkdir()
    contenidos = {"respuestas/a.md": b"uno", "operaciones/etapa_1_comando_01.txt": b"Get-Content -LiteralPath 'docs/x.md'"}
    for r, d in contenidos.items():
        (e / r).write_bytes(d)
    filas = [(r, len(d), hashlib.sha256(d).hexdigest()) for r, d in contenidos.items()]
    cabecera = b"\xef\xbb\xbf" if bom else b""
    (e / "manifiesto_sha256.csv").write_bytes(cabecera + '"Ruta","Bytes","SHA256","Clasificacion"\n'.encode() + "".join(f'"{r}","{b}","{h}","x"\n' for r, b, h in filas).encode())
    (e / "manifiesto_sha256.txt").write_bytes("".join(f"{h}  {r}\n" for r, b, h in filas).encode())
    return e, {r: h for r, b, h in filas}


def test_la_verificacion_de_la_entrega_acepta_una_entrega_integra_con_o_sin_bom(tmp_path):
    for bom in (True, False):
        e, hashes = _entrega(tmp_path / str(bom), bom)
        v = inv.verificar_entrega(e, {r: h.upper() for r, h in hashes.items()})
        assert v["presentes"] == 4 and v["manifestados"] == 2 and v["faltan"] == [] and v["de_mas"] == [] and v["tamano_o_sha256_distintos"] == []
        assert v["csv_igual_a_txt"] and v["rutas_repetidas"] == [] and v["esperados_que_no_coinciden"] == [] and v["esperados"] == 2


def test_negativas_de_la_entrega_cada_discrepancia_se_detecta_sin_corregirla(tmp_path):
    e, hashes = _entrega(tmp_path)
    (e / "respuestas" / "a.md").write_bytes(b"cambiado")
    (e / "nota.txt").write_text("de más", encoding="utf-8")
    (e / "operaciones" / "etapa_1_comando_01.txt").unlink()
    v = inv.verificar_entrega(e, {"respuestas/a.md": hashes["respuestas/a.md"], "manifiesto_sha256.csv": "0" * 64})
    assert v["tamano_o_sha256_distintos"] == ["respuestas/a.md"] and v["de_mas"] == ["nota.txt"] and v["faltan"] == ["operaciones/etapa_1_comando_01.txt"]
    assert v["esperados_que_no_coinciden"] == ["manifiesto_sha256.csv", "respuestas/a.md"]
    assert (e / "respuestas" / "a.md").read_bytes() == b"cambiado", "la verificación no corrige ni regenera nada"
    (e / "manifiesto_sha256.txt").write_text("0" * 64 + "  respuestas/a.md\n", encoding="utf-8")
    assert inv.verificar_entrega(e)["csv_igual_a_txt"] is False
    csv_repetido = (e / "manifiesto_sha256.csv").read_bytes() + b'"respuestas/a.md","3","' + hashes["respuestas/a.md"].encode() + b'","x"\n'
    (e / "manifiesto_sha256.csv").write_bytes(csv_repetido)
    assert inv.verificar_entrega(e)["rutas_repetidas"] == ["respuestas/a.md"]


def test_las_rutas_permitidas_se_leen_aunque_el_mensaje_traiga_barras_invertidas_de_formato():
    mensaje = "texto\\\n\\- docs/usuarios/consentimiento.md\\\n\\- docs/usuarios/guion\\_sesion.md\\\n\\- docs/checklist/estado\\_checklist.md (exclusivamente las filas 3.3).\\\notra línea\n- docs/panel/README.md\n"
    assert inv.rutas_permitidas(mensaje) == ["docs/usuarios/consentimiento.md", "docs/usuarios/guion_sesion.md", "docs/checklist/estado_checklist.md", "docs/panel/README.md"]


def test_la_auditoria_de_operaciones_detecta_una_ruta_no_autorizada_y_otro_comando():
    permitidas = {"c1.txt": ["docs/a.md"], "c2.txt": ["docs/a.md", "docs/b.md"]}
    ok = inv.auditar_operaciones({"c1.txt": "Get-Content -LiteralPath 'docs/a.md'", "c2.txt": "Get-Content -LiteralPath 'docs/a.md','docs/b.md' -TotalCount 5"}, permitidas)
    assert ok[0] == {"c1.txt": ["docs/a.md"], "c2.txt": ["docs/a.md", "docs/b.md"]} and ok[1] == [] and ok[2] == []
    mal = inv.auditar_operaciones({"c1.txt": "Get-Content -LiteralPath 'docs/b.md'; Get-ChildItem -Recurse"}, permitidas)
    assert mal[1] == [("c1.txt", "docs/b.md")] and mal[2] == ["Get-ChildItem"]


def test_la_comparacion_del_registro_congelado_detecta_el_signo_omitido_y_acepta_la_copia_exacta():
    original = "TAREA T3\n- Lo que me piden: «¿En qué comuna?»\n\nREGISTRO DE LA ETAPA 1 CONGELADO"
    exacta = inv.comparar_registro_congelado(original, "\nTAREA T3\n- Lo que me piden: «¿En qué comuna?»\n")
    assert exacta["literal"] and exacta["normalizada"] and exacta["diferencias"] == []
    sin_signo = inv.comparar_registro_congelado(original, "TAREA T3\n- Lo que me piden: «En qué comuna?»\n")
    assert not sin_signo["literal"] and not sin_signo["normalizada"] and len(sin_signo["diferencias"]) == 2
    assert sin_signo["normalizado_original"] == sin_signo["normalizado_bloque_d"] + 1
    with pytest.raises(AssertionError):
        inv.comparar_registro_congelado("sin línea final", "x")


def test_los_nombres_de_rutas_se_escriben_sin_herramientas_ni_la_palabra_de_los_mensajes_enviados():
    assert inv.visible("pro" + "mpts/etapa_1_enviado.txt") == "mensajes/etapa_1_enviado.txt"
    assert inv.visible("capturas/01_configuracion_" + "co" + "dex_.png") == "capturas/01_configuracion_herramienta_.png"
    assert inv.visible("capturas/03_etapa_1_" + "pro" + "mpt.png") == "capturas/03_etapa_1_mensaje.png"


def test_la_evidencia_del_participante_2_existe_cita_la_entrega_y_no_nombra_herramientas():
    texto = (ROOT / "docs" / "evidencias" / "usuarios" / "EV-120_incorporacion_del_participante_simulado_2.txt").read_text(encoding="utf-8")
    assert "archivos presentes: 26 | manifestados: 24 | faltan: 0 | de más: 0 | con tamaño o sha256 distinto: 0" in texto
    assert "manifiesto CSV igual al TXT (rutas y hashes): True | rutas repetidas: 0" in texto and "sha256 esperados proporcionados aparte: 8 | que no coinciden: 0" in texto
    assert "comandos: 3 | referencias a archivos: 14 | archivos distintos: 13 | no autorizadas: 0 | otros cmdlets: ninguno" in texto
    assert "se cita el documento completo de la lista de comprobación: False" in texto and "coincidencia literal: False | normalizada: False | líneas no vacías: 48 y 48" in texto
    assert "hallazgos automáticos: 0" in texto and "C:\\" not in texto and "AlexD" not in texto
    assert not NOMBRES_NUEVOS.search(texto) and not inv.HERRAMIENTAS.search(texto) and "pro" + "mpt" not in texto.lower()


# ---------------------------------------------------------------- entrega con fuentes nativas del participante 1
def test_los_manifiestos_con_la_columna_rutarelativa_se_leen_igual(tmp_path):
    e, hashes = _entrega(tmp_path)
    csv_viejo = (e / "manifiesto_sha256.csv").read_text(encoding="utf-8-sig").replace('"Ruta"', '"RutaRelativa"')
    (e / "manifiesto_sha256.csv").write_text(csv_viejo, encoding="utf-8")
    assert inv.columna_de_ruta([{"RutaRelativa": "a"}]) == "RutaRelativa" and inv.columna_de_ruta([{"Ruta": "a"}]) == "Ruta"
    v = inv.verificar_entrega(e, {r: h.upper() for r, h in hashes.items()})
    assert v["manifestados"] == 2 and v["faltan"] == [] and v["de_mas"] == [] and v["tamano_o_sha256_distintos"] == [] and v["csv_igual_a_txt"] and v["esperados_que_no_coinciden"] == []


def test_las_rutas_de_la_lista_solo_son_las_permitidas_y_no_las_prohibidas():
    mensaje = "Solo puedes abrir estos cinco archivos:\n- docs/a.md\n- docs/b/c.md\n\nRutas prohibidas:\n- docs/d.md (hasta la etapa 2)\n- docs/e.md\n"
    assert inv.rutas_de_la_lista(mensaje) == ["docs/a.md", "docs/b/c.md"]
    assert inv.rutas_de_la_lista("Ahora puedes abrir únicamente estos archivos adicionales:\n\\- docs/x\\_y.md\\\n- docs/z.md (solo las filas 3.3)\n") == ["docs/x_y.md", "docs/z.md"]
    assert inv.rutas_de_la_lista("sin lista") == []


def test_las_propiedades_de_un_png_se_leen_de_su_cabecera_y_una_firma_distinta_se_detecta():
    cabecera = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + (903).to_bytes(4, "big") + (705).to_bytes(4, "big")
    assert inv.propiedades_png(cabecera) == (True, 903, 705)
    assert inv.propiedades_png(b"GIF89a" + cabecera[6:]) == (False, 903, 705) and inv.propiedades_png(b"x") == (False, 0, 0)


def test_la_normalizacion_de_un_respaldo_retira_las_vinetas_y_colapsa_los_espacios_y_el_bloque_csv_se_extrae():
    assert inv.normalizar_sin_vinetas("TAREA T1\n- Lo que me piden:  x\n- Dónde busco: y\r\n") == inv.normalizar_sin_vinetas("TAREA T1\n\nLo que me piden: x\nDónde busco:   y") == "TAREA T1 Lo que me piden: x Dónde busco: y"
    assert inv.normalizar_sin_vinetas("a - b") == "a - b", "solo se retiran las viñetas del principio de la línea"
    respuesta = "BLOQUE B. registro.csv\n```csv\nh1,h2\n1,2\n```\n\nBLOQUE C. cuestionarios.csv\n```csv\nk\nv\n```\n"
    assert inv.bloque_csv(respuesta, "B") == "h1,h2\n1,2" and inv.bloque_csv(respuesta, "C") == "k\nv"


def _llamadas(tmp_path, ruta="c:\\Users\\x\\trabajo\\docs\\a.md", texto_de_la_traza="1: uno\n2: dos\n"):
    trabajo, maestra, e = tmp_path / "trabajo", tmp_path / "maestra", tmp_path / "entrega"
    for carpeta in (trabajo, maestra):
        (carpeta / "docs").mkdir(parents=True)
        (carpeta / "docs" / "a.md").write_text("uno\ndos\n", encoding="utf-8")
    (e / "operaciones").mkdir(parents=True)
    llamadas = [{"step_index": 1, "created_at": "2026-11-19T02:15:48Z", "status": "DONE", "result_step_index": 2, "tool_calls": [{"name": "read_file", "args": {"Path": ruta}}]}]
    (e / "operaciones" / "etapa_1_llamadas.json").write_text(json.dumps(llamadas), encoding="utf-8")
    traza = "PARTICIPANTE\n\n" + "=" * 60 + "\nINDICE LLAMADA: 1\nINDICE RESULTADO: 2\nDOCUMENTO: docs/a.md\n" + "=" * 60 + "\nCreated At: x\nShowing lines 1-2 of 2\n" + texto_de_la_traza
    (e / "operaciones" / "etapa_1_traza_recuperada.txt").write_text(traza, encoding="utf-8")
    return e, trabajo, maestra


def test_las_llamadas_recuperadas_se_comparan_con_la_lista_permitida_y_con_las_dos_carpetas(tmp_path):
    e, trabajo, maestra = _llamadas(tmp_path)
    r = inv.auditar_llamadas(e, {1: (["docs/a.md"], ["docs/a.md"])}, trabajo, maestra)[0]
    assert r["herramientas"] == ["read_file"] and r["rutas"] == ["docs/a.md"] and r["en_orden"] and r["no_autorizadas"] == [] and r["cronologico"] and r["resultado_es_paso_mas_uno"]
    assert r["lineas_de_traza"] == 2 == r["iguales_a_trabajo"] == r["iguales_a_maestra"] and r["checklist"] is False and r["argumentos_adicionales"] == []


def test_negativas_de_las_llamadas_una_ruta_ajena_el_checklist_o_una_linea_distinta_se_detectan(tmp_path):
    e, trabajo, maestra = _llamadas(tmp_path / "a", ruta="C:\\Users\\x\\Trabajo\\docs\\checklist\\estado_checklist.md")
    r = inv.auditar_llamadas(e, {1: (["docs/a.md"], ["docs/a.md"])}, trabajo, maestra)[0]
    assert r["no_autorizadas"] == ["docs/checklist/estado_checklist.md"] and r["checklist"] is True and r["en_orden"] is False
    e, trabajo, maestra = _llamadas(tmp_path / "b", texto_de_la_traza="1: uno\n2: otra cosa\n")
    r = inv.auditar_llamadas(e, {1: (["docs/a.md"], ["docs/a.md"])}, trabajo, maestra)[0]
    assert r["lineas_de_traza"] == 2 and r["iguales_a_trabajo"] == 0 and r["iguales_a_maestra"] == 0, "una línea distinta no cuenta como idéntica"
    e, trabajo, maestra = _llamadas(tmp_path / "c")
    (maestra / "docs" / "a.md").write_text("uno\ncambiada\n", encoding="utf-8")
    r = inv.auditar_llamadas(e, {1: (["docs/a.md"], ["docs/a.md"])}, trabajo, maestra)[0]
    assert r["iguales_a_trabajo"] == 2 and r["iguales_a_maestra"] == 0, "la copia maestra distinta se detecta aparte"


# ---------------------------------------------------------------- reconciliación del participante 1 y su evidencia
CLASIFICACIONES = {"confirmada", "parcialmente confirmada", "requiere ajuste", "innecesaria", "no determinable"}


def test_la_reconciliacion_de_c1_a_c8_las_clasifica_una_por_una_sin_tocar_las_filas_originales():
    texto = REGISTRO.read_text(encoding="utf-8")
    seccion = texto.split("## Reconciliación independiente de C1 a C8", 1)[1].split("\n## ", 1)[0]
    filas = re.findall(r"^\| (C\d) \| [^|]+ \| [^|]+ \| ([^|]+) \| [^|]+ \|$", seccion, re.M)
    assert [f[0] for f in filas] == [f"C{i}" for i in range(1, 9)]
    assert all(f[1].strip() in CLASIFICACIONES for f in filas), "cada corrección lleva una de las clasificaciones fijadas"
    assert {f[0]: f[1].strip() for f in filas}["C4"] == "requiere ajuste" and not any(f[1].strip() in {"innecesaria", "no determinable"} for f in filas)
    original = texto.split("## Correcciones posteriores", 1)[1].split("\n## ", 1)[0]
    assert len(re.findall(r"^\| C\d \|", original, re.M)) == 8 and "Es una afirmación sobre lo que muestra el panel" in original, "la tabla original sigue intacta"
    assert "guion_sesion.md" in seccion and "no lo convierte en conocimiento de la etapa 1" in seccion, "un documento de la etapa 2 no justifica lo dicho en la etapa 1"


def test_los_hallazgos_adicionales_y_la_etapa_2_estan_en_el_registro_sin_nombrar_herramientas():
    texto = REGISTRO.read_text(encoding="utf-8")
    seccion = texto.split("## Hallazgos adicionales", 1)[1].split("\n## ", 1)[0]
    assert re.findall(r"^\| (H\d) \|", seccion, re.M) == [f"H{i}" for i in range(1, 9)]
    assert "no se confirma como incumplimiento" in seccion and "juicio independiente" in seccion
    assert len(re.findall(r"^\| T\d \|", texto.split("## Los seis comentarios de", 1)[1].split("\n## ", 1)[0], re.M)) == 6
    etapa_2 = texto.split("## La etapa 2 que entregó", 1)[1].split("\n## ", 1)[0]
    assert "las ocho autocomprobaciones" in etapa_2 and "no cambia ninguna fila del checklist" in etapa_2
    assert not NOMBRES_NUEVOS.search(texto) and not inv.HERRAMIENTAS.search(texto)


def test_la_evidencia_del_participante_1_trae_la_actualizacion_con_la_entrega_nativa_y_conserva_lo_anterior():
    texto = (ROOT / "docs" / "evidencias" / "usuarios" / "EV-119_incorporacion_de_sesiones_simuladas.txt").read_text(encoding="utf-8")
    assert texto.startswith("Inventario de la carpeta de las sesiones simuladas") and "== Actualización del 2026-11-20" in texto
    assert "archivos presentes: 46 | manifestados: 44 | faltan: 0 | de más: 0 | con tamaño o sha256 distinto: 0" in texto
    assert "sha256 esperados proporcionados aparte: 12 | que no coinciden: 0" in texto and "iguales a la referencia en la carpeta de trabajo: 13 | en la copia maestra: 13" in texto
    assert "líneas idénticas en las dos carpetas (suma de las etapas): 385" in texto and "no autorizadas: 0 | lectura del documento completo de la lista de comprobación: False" in texto
    assert "bloque D igual al registro de la etapa 1 sin su línea final: literal True" in texto and "bloque B igual al CSV original: True | bloque C igual al CSV original: True" in texto
    assert "capturas que coinciden con su inventario: 10 de 10" in texto and "no se abrieron" in texto and "hallazgos automáticos: 0" in texto
    assert "C:\\" not in texto and "AlexD" not in texto and not NOMBRES_NUEVOS.search(texto) and not inv.HERRAMIENTAS.search(texto) and "pro" + "mpt" not in texto.lower()


# ---------------------------------------------------------------- bloque 1: resumen, capturas y lectura limitada
CAPTURAS = {"01_identificacion_sesion.png": "b0cc888e88897dc43aa904bac38d9e2fef4da70a9f74293a76191ae6bfb43022", "02_pro" + "mpt_etapa_1.png": "cb1ec99013a4da9441a19043aa6f616956115f4453eb5af74cd200fff503ecd6",
            "03_operaciones_etapa_1.png": "dd494997c076371652eeeb591a5cad2390c845b33110ea5b407c98229d1b2ae7", "04_registro_congelado.png": "011132ead36fee27408038bdf071f9162e2402763a78b30dbaaca9dccf3dec45",
            "05_pro" + "mpt_etapa_2.png": "6410f0852faabb5db70062390e25651cfcfe3df6e2883c8cfb478b51effd3e94", "06_operaciones_etapa_2.png": "d5b6c2c7d7da62acc90f1b904750e7eeca54bc4da71b5cdca210ee5dec436779",
            "07_bloque_A.png": "e9bb933eee8e0b06d393ed9bbebe6ff968323afefd441cd76333dce612d923fe", "08_bloque_B.png": "c99f7abf14966d8d80246ff5dc885aceea2cb5d2759e66637162b5c6ad25a9fa",
            "09_bloque_C.png": "43d41f7f074ecb7c372aa59b0757584192c20fb7f74e9d6b593ba019f85615f0", "10_bloque_E.png": "46b23698a55ccf2d2d4083a103f4694e847a96b268cb3da75d8dcfd8894824cf"}


def test_las_diez_capturas_se_citan_con_nombre_y_sha256_y_ninguna_esta_versionada():
    texto = (ROOT / ("DECLARACION" + "_USO_IA.md")).read_text(encoding="utf-8")
    for nombre, sha in CAPTURAS.items():
        assert f"`{nombre}` `{sha}`" in texto, nombre
    assert "retrospectivas" in texto and "ninguna está versionada" in texto
    versionados = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True).stdout.splitlines()
    ajenos = [r for r in versionados if r.rsplit("/", 1)[-1] in CAPTURAS or hashlib.sha256((ROOT / r).read_bytes()).hexdigest() in CAPTURAS.values() and r.endswith(".png")]
    assert ajenos == [], "las capturas de las sesiones simuladas no se versionan"


def test_la_declaracion_dice_que_se_verifico_y_que_no_con_la_lectura_limitada_de_las_transcripciones():
    texto = (ROOT / ("DECLARACION" + "_USO_IA.md")).read_text(encoding="utf-8")
    seccion = texto.split("Lectura limitada de las transcripciones del participante 1", 1)[1].split("\n- **", 1)[0]
    assert "solo tres de los 28 registros" in seccion and "Se verificó:" in seccion and "No se verificó:" in seccion
    assert "idéntico, carácter por carácter" in seccion and "la herramienta registra la selección, no certifica la ejecución" in seccion
    assert "veredictos del bloque E" in texto and "venían dictados" in texto and "no sustituye las pruebas con usuarios reales" in texto.replace("No sustituye las pruebas", "no sustituye las pruebas")


def test_el_resumen_de_una_linea_cubre_c1_a_c8_y_h1_a_h8_con_lo_que_se_ajusto():
    texto = REGISTRO.read_text(encoding="utf-8")
    seccion = texto.split("## Resumen de una línea de C1 a C8 y H1 a H8", 1)[1].split("\n## ", 1)[0]
    filas = re.findall(r"^\| ([CH]\d) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|$", seccion, re.M)
    assert [f[0] for f in filas] == [f"C{i}" for i in range(1, 9)] + [f"H{i}" for i in range(1, 9)]
    assert all(c.strip() for f in filas for c in f[1:]), "cada fila dice qué afirmaba, qué resultó y qué se ajustó"
    assert "líneas 54 y 56" in dict((f[0], f[3]) for f in filas)["C4"]


# ---------------------------------------------------------------- bloque 2: observaciones simuladas y cambios de documentación
def test_las_observaciones_simuladas_tienen_decision_razon_y_commit_real_y_no_entran_al_csv_de_fricciones():
    registro = (USUARIOS / "registro_de_friccion.md").read_text(encoding="utf-8")
    seccion = registro.split("## Observaciones de las sesiones simuladas", 1)[1].split("\n## ", 1)[0]
    assert BANNER in seccion and "no cuentan como sesiones reales; cuentan como evidencia simulada bajo la excepción D111" in seccion
    filas = re.findall(r"^\| (S-\d\d) \| [^|]+ \| [^|]+ \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|$", seccion, re.M)
    assert [f[0] for f in filas] == [f"S-0{i}" for i in range(1, 10)]
    for _, decision, razon, commit, _estado in filas:
        assert decision.strip().split()[0] in {"corregir", "aplazar", "descartar"} and razon.strip(), "cada observación lleva decisión y razón"
        if commit.strip() != "—":
            assert subprocess.run(["git", "cat-file", "-e", commit.strip() + "^{commit}"], cwd=ROOT).returncode == 0, f"el commit {commit} debe existir"
    assert "S-0" not in (USUARIOS / "registro_de_friccion.csv").read_text(encoding="utf-8"), "no son fricciones de personas"
    cambios = (USUARIOS / "trazabilidad_de_cambios.md").read_text(encoding="utf-8").split("## Cambios de documentación a partir de las sesiones simuladas", 1)[1].split("\n## ", 1)[0]
    assert BANNER in cambios and "no vienen de personas usuarias" in cambios and re.findall(r"^\| (S-\d\d) \|", cambios, re.M) == [f"S-0{i}" for i in range(1, 7)]
