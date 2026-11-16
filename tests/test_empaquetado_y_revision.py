"""Empaquetado sin entornos virtuales (scripts/make_dist.py) y cobertura de la revisión de códigos de barrio."""
import importlib.util

from src.common import ROOT

_spec = importlib.util.spec_from_file_location("make_dist", ROOT / "scripts" / "make_dist.py")
make_dist = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(make_dist)


def _escribir(raiz, rutas):
    for r in rutas:
        p = raiz / r
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x", encoding="utf-8")


def test_make_dist_excluye_entornos_virtuales_con_cualquier_nombre(tmp_path):
    raiz = tmp_path / "proyecto"
    validos = ["main.py", "requirements.txt", "src/a.py", "data/gold/g.csv", ".env.example"]
    _escribir(raiz, validos + [".env", "logs/e.log", ".pytest_cache/v", "src/__pycache__/a.pyc", "dist/viejo.zip",
                               ".venv_test/pyvenv.cfg", ".venv_test/Scripts/python.exe", "venv/Lib/site-packages/m.py", "env/bin/python",
                               "mi_entorno/pyvenv.cfg", "mi_entorno/Lib/site-packages/pandas/__init__.py",
                               "otro/entorno_x/pyvenv.cfg", "otro/entorno_x/bin/python"])
    _, nombres = make_dist.empaquetar(raiz)
    assert sorted(nombres) == sorted(validos)


def test_make_dist_verificacion_del_zip_detecta_entornos():
    malos = make_dist.prohibidos(["a/pyvenv.cfg", "x/venv/y.py", "Lib/site-packages/m.py", ".env", "logs/a.log", "dist/z.zip", "ok/main.py", ".env.example"])
    assert malos == ["a/pyvenv.cfg", "x/venv/y.py", "Lib/site-packages/m.py", ".env", "logs/a.log", "dist/z.zip"]


def test_make_dist_sobre_el_repo_no_incluye_entorno():
    nombres = [p.relative_to(ROOT).as_posix() for p in make_dist.listar(ROOT)]
    assert nombres and make_dist.prohibidos(nombres) == []


def test_revision_de_codigos_cubre_los_casos_pedidos():
    txt = (ROOT / "docs" / "silver" / "revision_codigos_barrio.md").read_text(encoding="utf-8")
    for c in (1011, 1802, 1898, 1905, 1922, 1999, 2098, 1920):
        assert f"### Código {c}" in txt, c
    assert txt.count("| revisión visual del equipo | pendiente |") == 8
    assert "333" in txt and "S1" in txt and "Qué NO demuestra" in txt


def test_categorias_de_la_revision_suman_las_construcciones_sin_nombre_validado():
    """a + b + c de docs/silver/revision_codigos_barrio.md = construcciones sin nombre validado calculadas desde Silver; y el documento de resultados las cita."""
    import re

    import pandas as pd

    silver = pd.read_csv(ROOT / "data" / "silver" / "silver_integrated.csv", usecols=["nombre_validado"])
    n = int((silver.nombre_validado == False).sum())  # noqa: E712
    resumen = (ROOT / "docs" / "silver" / "revision_codigos_barrio.md").read_text(encoding="utf-8").split("## Resumen")[1].split("\n## ")[0]
    cats = {m[0]: int(m[1]) for m in re.findall(r"^\| \((\w)\) \| \d+ \| [^|]+ \| (\d+) \|", resumen, re.M)}
    assert sorted(cats) == ["a", "b", "c"] and sum(cats.values()) == n
    resultados = (ROOT / "docs" / "gold" / "resultados.md").read_text(encoding="utf-8")
    assert f"De las {n} construcciones sin nombre validado, {cats['a']} (" in resultados
    assert "conservamos 93,52 %" in resultados and "sigue pendiente" in resultados
