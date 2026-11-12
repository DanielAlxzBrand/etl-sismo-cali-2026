"""Empaquetado: detección de entornos virtuales por contenido, aunque no tengan `pyvenv.cfg` ni un nombre conocido."""
import importlib.util

from src.common import ROOT

_spec = importlib.util.spec_from_file_location("make_dist", ROOT / "scripts" / "make_dist.py")
make_dist = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(make_dist)

VALIDOS = ["main.py", "requirements.txt", "src/a.py", "data/gold/g.csv", ".env.example"]


def _escribir(raiz, rutas):
    for r in rutas:
        p = raiz / r
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x", encoding="utf-8")


def test_entorno_sin_pyvenv_cfg_no_entra_al_zip(tmp_path):
    raiz = tmp_path / "proyecto"
    _escribir(raiz, VALIDOS + ["entorno_linux/bin/python", "entorno_linux/bin/pip", "entorno_win/Scripts/python.exe", "entorno_win/Scripts/pip.exe",
                               "entorno_conda/conda-meta/historial.json", "entorno_conda/python.exe", "otro/lib/python3.13/site-packages/m.py"])
    assert not any((raiz / d / "pyvenv.cfg").exists() for d in ("entorno_linux", "entorno_win", "entorno_conda"))
    _, nombres = make_dist.empaquetar(raiz, tmp_path / "salida")
    assert sorted(nombres) == sorted(VALIDOS)


def test_verificacion_del_zip_falla_con_huellas_de_entorno():
    for entrada in ("e/bin/python", "e/Scripts/python.exe", "e/python.exe", "c/conda-meta/x.json", "e/lib/site-packages/m.py"):
        assert make_dist.prohibidos(["main.py", entrada]) == [entrada], entrada
    assert make_dist.prohibidos(["scripts/make_dist.py", "src/python_utils.py", "docs/python.md"]) == []


def test_repo_real_sigue_sin_entorno_en_la_lista():
    nombres = [p.relative_to(ROOT).as_posix() for p in make_dist.listar(ROOT)]
    assert nombres and make_dist.prohibidos(nombres) == []
    assert not any(n.startswith(".venv") for n in nombres)
