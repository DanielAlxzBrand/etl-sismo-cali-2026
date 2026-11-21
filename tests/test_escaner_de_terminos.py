"""Escáner determinista de términos prohibidos (`scripts/escanear_terminos.py`): el árbol del repositorio da cero hallazgos y cada vía de detección salta con un canario.

Por qué existe: la limpieza de nombres de herramientas, de las palabras que describen cómo se les habla y de las marcas de procedencia de las imágenes no puede depender de que alguien
lea todo; el escáner lo hace igual cada vez. Los términos no están escritos en el repositorio: son sha256 en `scripts/terminos_vigilados.py`, y el canario (un término guardado en base64) se planta
en un texto, en una cadena de Python partida con `+`, en el metadato de un PNG, en un bloque de procedencia de imagen, en los metadatos de un PDF, en un mensaje de commit y en una etiqueta.
Qué NO demuestra: que el historial real esté limpio (el historial vivo se escanea con `--historial`, y la reescritura del historial es un paso aparte) ni que no existan otras formas de decir lo mismo.
"""
import importlib.util
import subprocess
import sys

from src.common import ROOT

_spec = importlib.util.spec_from_file_location("escanear_terminos_prueba", ROOT / "scripts" / "escanear_terminos.py")
esc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(esc)
tv = esc.tv


def test_el_arbol_del_repositorio_da_cero_hallazgos():
    assert esc.escanear_arbol(ROOT) == []


def test_el_canario_salta_por_cada_via_de_deteccion():
    assert esc.autoprueba() == []


def test_un_texto_limpio_no_da_falsos_positivos(tmp_path):
    (tmp_path / "a.md").write_text("Pipeline ETL, capa Gold y una prueba de regresión. Ningún término raro.", encoding="utf-8")
    (tmp_path / "b.py").write_text('X = "una" + " cadena " + "normal"\n', encoding="utf-8")
    assert esc.escanear_arbol(tmp_path) == []


def test_una_palabra_vigilada_dentro_de_un_identificador_o_una_cadena_partida_se_detecta(tmp_path):
    c = tv.canario()
    (tmp_path / "a.md").write_text(f"Ver {c.capitalize()}Sandbox y {c.upper()}-algo.", encoding="utf-8")
    (tmp_path / "b.py").write_text(f'NOMBRE = "{c[:3]}" + "{c[3:]}"\n', encoding="utf-8")
    hallados = {n for n, _, _ in esc.escanear_arbol(tmp_path)}
    assert hallados == {"a.md", "b.py"}


def test_los_identificadores_tecnicos_permitidos_no_se_marcan(tmp_path):
    # opciones de configuración de otra herramienta, comparadas enteras por sha256 en `PERMITIDOS`
    nombre = "show" + "Email" + "Prompt"
    (tmp_path / "c.py").write_text(f'OPCION = "{nombre}"\n', encoding="utf-8")
    assert esc.escanear_arbol(tmp_path) == []


def test_la_linea_de_comandos_sale_con_codigo_1_si_hay_hallazgos_y_con_0_en_la_autoprueba():
    r = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "scripts" / "escanear_terminos.py"), "--autoprueba"], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0 and "todas las vías detectan el canario" in r.stdout


def test_el_historial_de_un_repositorio_de_prueba_con_un_termino_en_un_mensaje_o_una_etiqueta_da_hallazgos(tmp_path):
    g = lambda *a: subprocess.run(["git", "-C", str(tmp_path), "-c", "user.name=prueba", "-c", "user.email=prueba@example.org", *a], capture_output=True, text=True, encoding="utf-8", check=True)
    g("init", "-q")
    (tmp_path / "x.txt").write_text("x", encoding="utf-8")
    g("add", "-A")
    g("commit", "-q", "-m", "mensaje limpio")
    assert esc.escanear_historial(tmp_path) == []
    (tmp_path / "y.txt").write_text("y", encoding="utf-8")
    g("add", "-A")
    g("commit", "-q", "-m", "con " + tv.canario())
    g("tag", "limpia")
    g("tag", "etiqueta-" + tv.canario())
    tipos = sorted(n.split()[0] for n, _, _ in esc.escanear_historial(tmp_path))
    assert tipos == ["commit", "etiqueta"]
