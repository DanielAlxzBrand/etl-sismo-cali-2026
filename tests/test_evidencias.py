"""Saneamiento de evidencias: ninguna salida guardada puede llevar rutas de usuario, el usuario ni el equipo."""
import getpass
import importlib.util
import socket
import sys
import tempfile
from pathlib import Path

from src.common import ROOT

CARPETA = ROOT / "scripts" / "evidencias"
sys.path.insert(0, str(CARPETA))
_spec = importlib.util.spec_from_file_location("saneamiento", CARPETA / "saneamiento.py")
san = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(san)
EVIDENCIAS = ROOT / "docs" / "evidencias"


def test_el_saneador_sustituye_rutas_usuario_y_equipo():
    clon = Path(tempfile.gettempdir()) / "evidencias_x" / "clon"
    s = san.Saneador(ROOT, clon, clon.parent)
    crudo = (f"{ROOT}\\.venv\\Scripts\\python.exe -m pytest\ncwd {clon}\ntemporal {tempfile.gettempdir()}\\x\nhogar {Path.home()}\\Descargas\n"
             f"usuario {getpass.getuser()} equipo {socket.gethostname()}\njson {str(ROOT).replace(chr(92), chr(92) * 2)}\notra D:\\Users\\alguien\\x")
    assert s.pendientes(crudo)
    limpio = s(crudo)
    assert s.pendientes(limpio) == []
    for marcador in ("<VENV>", "<CLON>", "<TEMP>", "<USUARIO>", "<EQUIPO>"):
        assert marcador in limpio, marcador


def test_escribir_guarda_el_texto_saneado(tmp_path):
    s = san.Saneador(ROOT)
    destino = tmp_path / "salida.txt"
    s.escribir(destino, f"ruta {ROOT}\\src\n")
    assert destino.read_text(encoding="utf-8") == "ruta <REPO>\\src\n"


def test_el_xml_de_junit_pierde_el_hostname():
    xml = '<testsuite name="pytest" hostname="UN-EQUIPO" tests="1"></testsuite>'
    assert "hostname" not in san.quitar_hostname_junit(xml)


def test_las_evidencias_guardadas_estan_saneadas():
    s = san.Saneador(ROOT)
    sucias = []
    for p in sorted(EVIDENCIAS.rglob("*")):
        if p.is_file() and p.suffix in (".txt", ".md", ".json", ".xml", ".csv"):
            if s.pendientes(p.read_text(encoding="utf-8", errors="replace")):
                sucias.append(p.relative_to(ROOT).as_posix())
    assert sucias == []
