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


def test_lista_incluye_referencias_y_documentos_del_proyecto():
    """`make_dist` no excluye por extensión: los PDF de `docs/proyecto/referencias/` y los documentos de `docs/` entran al zip."""
    nombres = [p.relative_to(ROOT).as_posix() for p in make_dist.listar(ROOT)]
    assert any(n.startswith("docs/proyecto/referencias/") and n.endswith(".pdf") for n in nombres)
    assert "docs/README.md" in nombres and any(n.startswith("docs/retroalimentacion/") for n in nombres)


# --- lista de inclusión ---
PERMITIDOS = ["main.py", "requirements.txt", "README.md", "pytest.ini", ".env.example", ".gitignore", ".gitattributes", "DECLARACION_USO_IA.md",
              "config/c.yaml", "src/a.py", "scripts/s.py", "tests/t.py", "notebooks/n.ipynb", "docs/README.md", "data/gold/etl_sismo.db"]


def _empaquetar(tmp_path, extra=()):
    raiz = tmp_path / "proyecto"
    _escribir(raiz, PERMITIDOS + list(extra))
    return make_dist.empaquetar(raiz, tmp_path / "salida")[1]


def test_lo_permitido_entra_y_el_zip_pasa_la_verificacion(tmp_path):
    nombres = _empaquetar(tmp_path)
    assert sorted(nombres) == sorted(PERMITIDOS)
    make_dist.verificar(nombres)
    assert "data/gold/etl_sismo.db" in nombres


def test_un_archivo_suelto_de_la_raiz_fuera_de_la_lista_no_entra(tmp_path):
    nombres = _empaquetar(tmp_path, ["notas.txt", "apuntes.md", "suelto.py", "datos.csv"])
    assert not {"notas.txt", "apuntes.md", "suelto.py", "datos.csv"} & set(nombres)
    assert make_dist.fuera_de_la_lista(nombres) == []


def test_una_carpeta_de_la_raiz_fuera_de_la_lista_no_entra(tmp_path):
    nombres = _empaquetar(tmp_path, ["borradores/a.md", "otro/b.py"])
    assert not any(n.startswith(("borradores/", "otro/")) for n in nombres)


def test_los_pdf_de_docs_solo_entran_desde_referencias_y_retroalimentacion(tmp_path):
    nombres = _empaquetar(tmp_path, ["docs/proyecto/referencias/ref.pdf", "docs/retroalimentacion/r.pdf", "docs/otro/x.pdf", "docs/suelto.pdf", "docs/validacion/v.pdf"])
    assert "docs/proyecto/referencias/ref.pdf" in nombres and "docs/retroalimentacion/r.pdf" in nombres
    assert make_dist.pdf_no_permitidos(nombres) == []
    assert not any(n in nombres for n in ("docs/otro/x.pdf", "docs/suelto.pdf", "docs/validacion/v.pdf"))


def test_dags_entra_cuando_existe_y_no_falla_cuando_no_existe(tmp_path):
    assert not any(n.startswith("dags/") for n in _empaquetar(tmp_path / "sin"))
    con = _empaquetar(tmp_path / "con", ["dags/pipeline.py"])
    assert "dags/pipeline.py" in con


def test_orquestacion_entra_cuando_existe_y_no_falla_cuando_no_existe(tmp_path):
    assert not any(n.startswith("orquestacion/") for n in _empaquetar(tmp_path / "sin"))
    con = _empaquetar(tmp_path / "con", ["orquestacion/Dockerfile", "orquestacion/requirements-airflow.txt"])
    assert {"orquestacion/Dockerfile", "orquestacion/requirements-airflow.txt"} <= set(con)


def test_el_repo_real_empaqueta_el_dag_y_la_carpeta_de_orquestacion():
    nombres = [p.relative_to(ROOT).as_posix() for p in make_dist.listar(ROOT)]
    assert "dags/medallon_etl_dag.py" in nombres and "orquestacion/Dockerfile" in nombres and "orquestacion/requirements-airflow.txt" in nombres
    assert make_dist.fuera_de_la_lista(nombres) == []


def test_un_entorno_simulado_sin_pyvenv_cfg_dentro_de_una_carpeta_permitida_no_entra(tmp_path):
    nombres = _empaquetar(tmp_path, ["src/entorno_a/bin/python", "src/entorno_a/lib.py", "notebooks/entorno_b/Scripts/python.exe", "tests/entorno_c/python.exe",
                                     "docs/entorno_d/conda-meta/h.json", "scripts/entorno_e/lib/python3.13/site-packages/m.py"])
    assert sorted(nombres) == sorted(PERMITIDOS)


def test_las_exclusiones_se_aplican_siempre(tmp_path):
    prohibidas = [".env", "logs/etl.log", "src/logs/x.log", "dist/z.zip", ".git/config", ".venv/pyvenv.cfg", ".venv_test/a", "venv/a", "env/a", ".pytest_cache/v", "herramienta_local.md",
                  ".herramienta_local/s.json", "src/__pycache__/a.pyc", "src/b.pyc", "notebooks/.ipynb_checkpoints/n-checkpoint.ipynb"]
    nombres = _empaquetar(tmp_path, prohibidas)
    assert sorted(nombres) == sorted(PERMITIDOS)


def test_la_verificacion_falla_con_mensajes_claros():
    import pytest
    base = ["requirements.txt", "main.py"]
    with pytest.raises(AssertionError, match="fuera de la lista permitida"):
        make_dist.verificar(base + ["notas.txt"])
    with pytest.raises(AssertionError, match="prohibidos"):
        make_dist.verificar(base + ["src/e/bin/python"])
    with pytest.raises(AssertionError, match="PDF de docs"):
        make_dist.verificar(base + ["docs/otro/x.pdf"])
    with pytest.raises(AssertionError, match="requirements.txt"):
        make_dist.verificar(["main.py"])
    make_dist.verificar(base + ["docs/proyecto/referencias/ref.pdf"])


def test_el_repo_real_solo_empaqueta_primer_nivel_permitido():
    nombres = [p.relative_to(ROOT).as_posix() for p in make_dist.listar(ROOT)]
    assert make_dist.fuera_de_la_lista(nombres) == [] and make_dist.pdf_no_permitidos(nombres) == []
    assert "requirements.txt" in nombres and "data/gold/etl_sismo.db" in nombres and ".env" not in nombres
    assert not any(n.startswith(("logs/", "dist/")) for n in nombres)


def test_una_carpeta_llamada_env_con_punto_no_entra(tmp_path):
    assert sorted(_empaquetar(tmp_path, [".env/a", ".env/b.txt"])) == sorted(PERMITIDOS)


def test_ninguna_carpeta_oculta_dentro_de_las_carpetas_permitidas_entra(tmp_path):
    nombres = _empaquetar(tmp_path, ["src/.herramienta_local/x.json", "docs/.otra/y.md", "tests/.cache_local/z.txt", "scripts/a/.oculta/b.py"])
    assert sorted(nombres) == sorted(PERMITIDOS)
    assert make_dist.prohibidos(["src/.herramienta_local/x.json"]) == ["src/.herramienta_local/x.json"]


def test_el_repo_real_empaqueta_el_panel_y_su_lanzador_sin_carpetas_ocultas_ni_credenciales():
    nombres = [p.relative_to(ROOT).as_posix() for p in make_dist.listar(ROOT)]
    assert "src/panel/app.py" in nombres and "src/panel/cliente_api.py" in nombres and "src/panel/paginas/respuesta.py" in nombres
    assert "scripts/panel/ejecutar_panel.py" in nombres and "tests/test_panel_paginas.py" in nombres
    assert not [n for n in nombres if any(parte.startswith(".") and parte != ".env.example" and parte != ".gitignore" and parte != ".gitattributes" for parte in n.split("/"))]
    assert ".env" not in nombres and make_dist.fuera_de_la_lista(nombres) == []


def test_una_carpeta_de_configuracion_de_streamlit_o_sus_credenciales_no_entran_al_zip(tmp_path):
    nombres = _empaquetar(tmp_path, [".streamlit/config.toml", ".streamlit/secrets.toml", "src/panel/.streamlit/credentials.toml", "scripts/panel/.streamlit/secrets.toml"])
    assert sorted(nombres) == sorted(PERMITIDOS)
