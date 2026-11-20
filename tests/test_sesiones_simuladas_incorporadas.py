"""Las sesiones simuladas que se incorporan al repositorio (D109): rotuladas, sin herramientas ni personas, sin cifras medidas y con su registro de la etapa 1 intacto.

Por qué existe: dos sesiones simuladas se hicieron fuera del repositorio con herramientas de elaboración, y lo único que puede entrar es lo que está completo, en su versión original y sin nombrar esas
herramientas (la declaración de la raíz es el único lugar que las nombra). Esta prueba comprueba que cada archivo de sesiones lleve el rótulo, que nada nombre herramientas fuera de la declaración,
que `sesiones_reales/` no tenga nada simulado, que el registro de la etapa 1 sea el que se firmó con su sha256 y cumpla el guion, y que el inventario de la carpeta de trabajo detecte lo que debe.
Qué NO demuestra: que el texto sea el que escribió quien simuló la sesión (hay un respaldo, no el original), que las correcciones posteriores sean todas las posibles ni que el panel sea usable.
"""
import hashlib
import importlib.util
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
GUION = (USUARIOS / "guion_sesion.md").read_text(encoding="utf-8")
BANNER = "Sesión simulada, no realizada con una persona real"
# Las cadenas se parten para que este archivo no se detecte a sí mismo.
NOMBRES_NUEVOS = re.compile("Co" + "dex|Anti" + "gravity|GP" + r"T-?\d")
PERSONAS = ("Daniel", "Brand", "Gordillo", "Castellanos", "Diego", "Jhoan", "Zulma", "Cuervo")
SUFIJOS = {".md", ".py", ".txt", ".yaml", ".yml", ".ini", ".ipynb", ".csv", ".json", ".jsonl", ".diff", ".sha256", ".xml", ".example"}


def _bloque_del_registro():
    return re.search(r"```text\n(.*?)\n```", REGISTRO.read_text(encoding="utf-8"), re.S).group(1)


# ---------------------------------------------------------------- rótulo, herramientas y carpeta de sesiones reales
def test_cada_archivo_de_sesiones_simuladas_y_su_resumen_llevan_el_rotulo():
    mds = sorted(SIMULADAS.glob("*.md")) + [USUARIOS / "resultados_sesiones_simuladas.md"]
    assert {p.name for p in mds} >= {"README.md", "plantilla_registro.md", "participante_simulado_1_etapa_1.md", "resultados_sesiones_simuladas.md"}
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
    assert not (SIMULADAS / "registro.csv").exists() and not (SIMULADAS / "cuestionarios.csv").exists(), "sin el original de la etapa 2 no se reconstruyen los CSV"


# ---------------------------------------------------------------- registro de la etapa 1 del participante 1
def test_el_registro_de_la_etapa_1_es_el_firmado_y_cumple_el_guion():
    texto = REGISTRO.read_text(encoding="utf-8")
    bloque = _bloque_del_registro()
    sha_limpio = hashlib.sha256((bloque + "\n").encode("utf-8")).hexdigest()
    assert f"`{sha_limpio}`" in texto, "el sha256 del texto limpio citado debe ser el del bloque"
    original = re.search(r"antes de limpiar:\*\* `([0-9a-f]{64})`", texto).group(1)
    assert original != sha_limpio and original == "78db8ba7958db5a77709deb927efdf438ca2997acc0eec7f1f1ee1ab5a1221c8"
    assert inv.auditar_registro(bloque, GUION, PERSONAS) == []
    assert bloque.split("\n")[-1] == inv.LINEA_DE_CONGELACION and len(bloque.split("\n")) == 68
    assert "\r" not in texto and "Participante simulado 1" in texto and "`habitante`" in texto and "2026-11-18" in texto


def test_las_correcciones_posteriores_citan_lineas_del_registro_y_no_lo_reescriben():
    texto = REGISTRO.read_text(encoding="utf-8")
    n = len(_bloque_del_registro().split("\n"))
    filas = re.findall(r"^\| (C\d) \| ([^|]+) \|", texto, re.M)
    assert [f[0] for f in filas] == [f"C{i}" for i in range(1, 9)]
    for _, lineas in filas:
        assert all(1 <= int(x) <= n for x in re.findall(r"\d+", lineas)), lineas
    assert "El registro de arriba no se toca" in texto
    assert "no lo reconstruimos desde un informe" in texto


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
                           "Cla" + "ude Code", "Request Review", "Solicitar aprobación", "Get-Content -LiteralPath", "comuna vecina", "Decidimos", "siguen pendientes", "No tenemos", "[COMPLETAR POR EL EQUIPO",
                           "78db8ba7958db5a77709deb927efdf438ca2997acc0eec7f1f1ee1ab5a1221c8", "feedback de personas usuarias")


def problemas_de_la_declaracion(texto):
    """Lo que falta o sobra en la sección de sesiones simuladas de la declaración (lista vacía si cumple)."""
    if "## 6. Sesiones de usuario simuladas" not in texto or "## 7." not in texto:
        return ["falta la sección 6 o la 7"]
    seccion = texto.split("## 6. Sesiones de usuario simuladas", 1)[1].split("## 7.", 1)[0]
    errores = [f"falta: {d}" for d in DATOS_DE_LA_DECLARACION if d not in seccion]
    if len(set(re.findall(r"`([0-9a-f]{64})`", seccion))) != 5:
        errores.append("deben citarse 5 sha256 distintos: los dos archivos de instrucciones, el respaldo y los dos informes")
    if "Cumple" in seccion:
        errores.append("la sección no puede declarar que un ítem cumple")
    return errores


def test_la_declaracion_cita_las_dos_sesiones_con_sus_datos_y_lo_pendiente():
    assert problemas_de_la_declaracion((ROOT / ("DECLARACION" + "_USO_IA.md")).read_text(encoding="utf-8")) == []


def test_negativas_de_la_declaracion_cada_dato_que_falta_o_sobra_se_detecta():
    base = (ROOT / ("DECLARACION" + "_USO_IA.md")).read_text(encoding="utf-8")
    for dato in ("Solicitar aprobación", "comuna vecina", "No tenemos", "2026-11-18", "GP" + "T-6.1 Terra"):
        assert problemas_de_la_declaracion(base.replace(dato, "otra cosa")), dato
    sha = "78db8ba7958db5a77709deb927efdf438ca2997acc0eec7f1f1ee1ab5a1221c8"
    assert problemas_de_la_declaracion(base.replace(sha, "0" * 64)), "un sha256 distinto del conservado"
    assert problemas_de_la_declaracion(base.replace(sha, "e47916832e38f7664bc6621b344e0f7cf68a2257bbbbfbf4a84e4f76af550f2f")), "dos sha256 iguales dejan 4 distintos"
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
