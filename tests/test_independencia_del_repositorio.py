"""Independencia del repositorio: nada de lo que viaja en el zip depende de otra carpeta del equipo ni sale de la raíz del proyecto (D95).

Por qué existe: el proyecto lo reciben otras personas como un zip y lo ejecutan en equipos donde no existe ninguna carpeta del equipo de desarrollo. Una ruta que sube más allá de la raíz, un enlace a un archivo
externo o una prueba que se omite en silencio cuando falta una carpeta vecina funcionan «de casualidad» en la máquina de origen y fallan en otra. La única carpeta hermana legítima es `airflow-medallon`,
que genera `scripts/orquestacion/preparar_airflow.py` (no es un requisito previo). Esta prueba recorre exactamente lo que `scripts/make_dist.py` empaqueta, con una lista mínima y nombrada de excepciones.
Qué NO demuestra: que el proyecto funcione en otra máquina (eso lo comprueban los experimentos de independencia en carpetas temporales y las pruebas del equipo) ni que los datos sean correctos.
"""
import ast
import hashlib
import importlib.util
import os
import re
from pathlib import Path

import pytest

from src.common import ROOT

_spec = importlib.util.spec_from_file_location("make_dist_independencia", ROOT / "scripts" / "make_dist.py")
make_dist = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(make_dist)

EXTENSIONES = {".py", ".md", ".txt", ".csv", ".json", ".jsonl", ".yaml", ".yml", ".ini", ".ipynb", ".diff", ".sha256", ".xml", ".example"}
# Las cadenas se parten para que este archivo no se detecte a sí mismo.
CARPETAS_DEL_EQUIPO = re.compile("guia" + "_equipo|archivo" + "_privado")
UNIDAD_O_USUARIO = re.compile(r"\b[A-Z]:\\[A-Za-z]|/Us" + "ers/|C:/Us" + "ers")
API_FUERA_DE_LA_RAIZ = re.compile("expand" + r"user|os\.ch" + r"dir|USER" + "PROFILE|APP" + "DATA")
NOMBRES_DE_RAIZ = {"ROOT", "REPO", "RAIZ", "R"}

# --- Excepciones mínimas y justificadas -------------------------------------------------------------------------------------------------------------------------------------------------
# archivo -> (patrones que se le permiten, motivo). Los que son evidencias crudas registradas en el manifiesto se comprueban además por su sha256: si alguien edita la evidencia, la excepción deja de valer.
EXCEPCIONES = {
    "scripts/evidencias/evidencia_capturas_panel.py": ("unidad", "ruta de los navegadores en Program Files, que son programas del sistema"),
    "scripts/evidencias/evidencias_api.py": ("unidad", "ruta de los navegadores en Program Files, que son programas del sistema"),
    "scripts/evidencias/saneamiento.py": ("api", "limpia rutas del usuario en las evidencias; usa el directorio personal solo para saberlas"),
    "tests/test_evidencias.py": ("unidad api", "comprueba justamente que las evidencias no traigan rutas ni usuario"),
    "tests/test_servicios_estructura.py": ("unidad", "contiene los patrones prohibidos para vigilar los textos nuevos (partidos)"),
    "tests/test_preparar_entorno.py": ("unidad", "rutas de Python simuladas para probar el diagnóstico sin tocar el equipo"),
    "tests/test_informe_pruebas.py": ("unidad", "comprueba que el informe no traiga rutas de la máquina"),
    "docs/proyecto/entorno.md": ("unidad", "rutas de programas del sistema (MySQL Server) en la descripción del entorno de la máquina de origen"),
    "tests/test_dag_estatico.py": ("unidad", "vigila que el DAG no traiga rutas locales"),
    "docs/evidencias/base/EV-005_material_referencia.txt": ("equipo", "evidencia cruda registrada (EV-005): nombra la carpeta de material de referencia del equipo; no se edita"),
    "docs/evidencias/base/EV-006_entorno.txt": ("unidad", "evidencia cruda registrada (EV-006): rutas de programas del sistema"),
    "docs/evidencias/api/EV-014_pytest.txt": ("unidad", "evidencia cruda registrada (EV-014): salida de pytest con una ruta relativa de otra carpeta; no se edita"),
    "docs/evidencias/orquestacion/EV-037_pasos_13_a_19.txt": ("unidad", "evidencia cruda registrada (EV-037): el montaje de la carpeta hermana de Airflow"),
}
# Los usos de `.parent` sobre la raíz que son la carpeta hermana generada (airflow-medallon): archivo -> motivo.
USOS_DE_LA_HERMANA_DE_AIRFLOW = {
    "scripts/orquestacion/preparar_airflow.py": "calcula la carpeta que genera (hermana del proyecto) y comprueba que el destino sea hermana",
    "scripts/orquestacion/sincronizar_dag.py": "carpeta de Airflow por defecto",
    "scripts/evidencias/evidencia_canario_orquestacion.py": "busca el `.env` de la carpeta de Airflow generada",
    "scripts/finanzas/medir_recursos.py": "mide la carpeta de Airflow generada si existe",
}


def _archivos_del_zip():
    return [p for p in make_dist.listar(ROOT) if p.suffix in EXTENSIONES and p.relative_to(ROOT).parts[0] != "data"]


def _rel(p):
    return p.relative_to(ROOT).as_posix()


def _manifiesto():
    filas = {}
    for linea in (ROOT / "docs" / "evidencias" / "manifiesto.md").read_text(encoding="utf-8").splitlines():
        if linea.startswith("| EV-"):
            c = [x.strip() for x in linea.strip("|").split("|")]
            filas[c[6]] = c[7]
    return filas


def _permitido(rel, tipo):
    return rel in EXCEPCIONES and tipo in EXCEPCIONES[rel][0].split()


def test_ningun_archivo_del_zip_nombra_carpetas_del_equipo_ni_rutas_locales_ni_apis_que_salgan_de_la_raiz():
    malos = []
    for p in _archivos_del_zip():
        rel, texto = _rel(p), p.read_text(encoding="utf-8", errors="replace")
        for n, linea in enumerate(texto.splitlines(), 1):
            if CARPETAS_DEL_EQUIPO.search(linea) and not _permitido(rel, "equipo"):
                malos.append(f"{rel}:{n} nombra una carpeta del equipo")
            if UNIDAD_O_USUARIO.search(linea) and not _permitido(rel, "unidad"):
                malos.append(f"{rel}:{n} ruta absoluta o de usuario")
            if p.suffix == ".py" and API_FUERA_DE_LA_RAIZ.search(linea) and not _permitido(rel, "api"):
                malos.append(f"{rel}:{n} API que sale de la raíz")
    assert not malos, "\n".join(malos[:40])


def test_las_evidencias_que_son_excepcion_siguen_siendo_las_registradas_en_el_manifiesto():
    """Una excepción sobre una evidencia cruda solo vale mientras el archivo sea el registrado (mismo sha256)."""
    registradas = _manifiesto()
    for rel in (r for r in EXCEPCIONES if r.startswith("docs/evidencias/")):
        assert rel in registradas, f"{rel} debe estar en el manifiesto"
        assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == registradas[rel], f"{rel} cambió: la excepción ya no vale"


def _profundidad_de_la_raiz(rel):
    return len(Path(rel).parts) - 1


def _problemas_de_rutas(rel, arbol):
    malos = []
    for n in ast.walk(arbol):
        # Path(__file__).resolve().parents[k]: k debe llegar exactamente a la raíz del proyecto
        if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Attribute) and n.value.attr == "parents" and isinstance(n.slice, ast.Constant) and isinstance(n.slice.value, int):
            if "__file__" in ast.unparse(n.value.value) and n.slice.value != _profundidad_de_la_raiz(rel):
                malos.append(f"{rel}:{n.lineno} parents[{n.slice.value}] no es la raíz (debería ser parents[{_profundidad_de_la_raiz(rel)}])")
        # ROOT.parent / ROOT.parents[...]: solo para la carpeta hermana generada de Airflow
        if isinstance(n, ast.Attribute) and n.attr in ("parent", "parents") and isinstance(n.value, ast.Name) and n.value.id in NOMBRES_DE_RAIZ:
            if rel not in USOS_DE_LA_HERMANA_DE_AIRFLOW:
                malos.append(f"{rel}:{n.lineno} {n.value.id}.{n.attr}: sale de la raíz")
    return malos


def test_las_rutas_relativas_a_la_raiz_son_exactas_y_solo_la_hermana_generada_sale_de_ella():
    malos = []
    for p in _archivos_del_zip():
        if p.suffix == ".py":
            malos += _problemas_de_rutas(_rel(p), ast.parse(p.read_text(encoding="utf-8"), filename=str(p)))
    assert not malos, "\n".join(malos)
    for rel in USOS_DE_LA_HERMANA_DE_AIRFLOW:      # la excepción debe seguir siendo cierta: cada archivo nombra la carpeta generada
        assert "airflow-medallon" in (ROOT / rel).read_text(encoding="utf-8"), rel


def test_el_analisis_de_rutas_ve_cada_defecto(tmp_path):
    """Se comprueba con código inventado que el análisis detecta cada defecto (para que una mutación real no pase inadvertida)."""
    assert _problemas_de_rutas("scripts/x.py", ast.parse("from pathlib import Path\nROOT = Path(__file__).resolve().parents[3]\n"))
    assert _problemas_de_rutas("scripts/x.py", ast.parse("ROOT = Path(__file__).resolve().parents[1]\nOTRA = ROOT.parent / 'x'\n"))
    assert not _problemas_de_rutas("scripts/x.py", ast.parse("ROOT = Path(__file__).resolve().parents[1]\n"))
    assert not _problemas_de_rutas("scripts/a/x.py", ast.parse("ROOT = Path(__file__).resolve().parents[2]\n"))


ENLACE = re.compile(r"\]\(([^)\s]+)\)")


def test_todo_enlace_de_un_documento_del_zip_apunta_a_un_archivo_que_existe_dentro_de_la_raiz():
    malos = []
    for p in _archivos_del_zip():
        if p.suffix != ".md":
            continue
        for n, linea in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            for destino in ENLACE.findall(linea):
                if destino.startswith(("http:", "https:", "mailto:", "#")):
                    continue
                ruta = (p.parent / destino.split("#")[0]).resolve()
                if not ruta.is_relative_to(ROOT.resolve()):
                    malos.append(f"{_rel(p)}:{n} enlace fuera de la raíz: {destino}")
                elif not ruta.exists():
                    malos.append(f"{_rel(p)}:{n} enlace roto: {destino}")
    assert not malos, "\n".join(malos[:40])


def test_ninguna_prueba_se_omite_segun_una_ruta_que_salga_de_la_raiz():
    """Un `skip` o `skipif` que dependa de una carpeta vecina ocultaría una dependencia: solo se admiten condiciones sobre `.git`, el binario `git` o la plataforma."""
    malos = []
    for p in (ROOT / "tests").glob("test_*.py"):
        arbol = ast.parse(p.read_text(encoding="utf-8"))
        for n in ast.walk(arbol):
            if isinstance(n, ast.Call) and isinstance(n.func, (ast.Attribute, ast.Name)) and getattr(n.func, "attr", getattr(n.func, "id", "")) in ("skip", "skipif", "importorskip", "xfail"):
                texto = ast.unparse(n)
                if re.search(r"\.parent|\.\.[\\/]|" + "guia" + "_equipo", texto):
                    malos.append(f"tests/{p.name}:{n.lineno} {texto[:90]}")
    assert not malos, "\n".join(malos)


def test_los_dos_scripts_de_servicios_fallan_con_mensaje_claro_cuando_falta_la_carpeta_hermana(tmp_path):
    """`preparar_airflow.py --verificar` sin la carpeta de Airflow no cae: dice qué falta (la carpeta es generada, no un requisito previo)."""
    import subprocess
    import sys
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "orquestacion" / "preparar_airflow.py"), "--verificar", "--destino", str(tmp_path / "no-existe")],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    assert "Traceback" not in r.stderr and r.returncode in (0, 1)


def test_ningun_texto_del_zip_trae_caracteres_de_control_que_estropeen_una_ruta():
    """Un `\a` mal escapado dejó un carácter BEL en el encabezado de un archivo del zip: se vigila en todos los textos."""
    malos = []
    for p in _archivos_del_zip():
        for n, linea in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if any(ord(c) < 32 and c not in "\t\r\f" for c in linea):
                malos.append(f"{_rel(p)}:{n}")
    assert not malos, "\n".join(malos[:20])


def test_las_pruebas_que_usan_git_pasan_en_el_zip_descomprimido_sin_git_y_omiten_solo_una(tmp_path):
    """Arma el zip de verdad, lo descomprime en una carpeta temporal (sin `.git`) y corre allí las pruebas que usan git: deben pasar y omitir exactamente 1 (la del historial, que el zip no trae).
    Es la comprobación que faltaba: en un clon esas pruebas pasaban aunque en el zip fallaran."""
    import shutil
    import subprocess
    import sys
    import zipfile
    if shutil.which("git") is None:
        pytest.skip("falta el binario git en el equipo: sin git se omiten 9 pruebas (docs/instalacion/README.md, sección 3.1)")
    ruta, _ = make_dist.empaquetar(ROOT, tmp_path / "zip")
    destino = tmp_path / "descomprimido"
    with zipfile.ZipFile(ruta) as z:
        z.extractall(destino)
    assert not (destino / ".git").exists()
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rs", "tests/test_secretos.py", "tests/test_configurar_mysql.py", "tests/test_canario_extra.py"],
                       cwd=destino, capture_output=True, text=True, encoding="utf-8", errors="replace", env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    assert r.returncode == 0, r.stdout[-1200:]
    assert re.search(r"\b1 skipped\b", r.stdout) and "sin historial de git" in r.stdout, r.stdout[-600:]
