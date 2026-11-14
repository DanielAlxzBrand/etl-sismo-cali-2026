"""Registro de componentes y aislamiento del panel (análisis estático): solo habla con la API, solo GET, sin recursos externos ni cifras escritas a mano."""
import ast
import csv
import json
import re
from pathlib import Path

import pytest

from src.api.app import crear_app
from src.panel import registro

RAIZ = Path(__file__).resolve().parents[1]
PANEL = RAIZ / "src" / "panel"
ARCHIVOS = sorted(PANEL.rglob("*.py"))
IMPORTS_PROHIBIDOS = ("sqlite3", "pymysql", "cryptography", "dotenv", "requests", "src.api", "src.load", "src.transform", "src.extract", "src.common")
METODOS_PROHIBIDOS = (".post(", ".put(", ".patch(", ".delete(", ".request(")
LLAMADAS_PROHIBIDAS = ("eval", "exec", "compile", "__import__")
SIN_CIFRAS = {"claves.py", "registro.py"}   # identificadores de datos y definición de componentes
# constantes de método que no vienen de los datos: nivel de confianza de los intervalos, el valor nulo «0» de la diferencia y rótulos de grupos de la API (1-2, 3-5)
PERMITIDO_CON_DIGITOS = re.compile(r"95 %|\b0\b|\bic95_(?:inf|sup)\b|\bnombre_csv_2015\b|utf-8|\b[1-6]-[1-6]\b|\bK[1-6]\b|\bS[0-5]\b|\bE[1-6]\b|%[sd]|\{[^}]*\}")


@pytest.fixture(scope="module")
def rutas_api():
    return set(crear_app().openapi()["paths"])


def _ruta_openapi(ruta, disponibles):
    if ruta in disponibles:
        return True
    return any(re.fullmatch(re.sub(r"\{[^}]+\}", "[^/]+", d), ruta) for d in disponibles)


def _encabezado_csv(ruta):
    with open(RAIZ / ruta, encoding="utf-8", newline="") as f:
        return next(csv.reader(f))


# ---------- registro ----------
def test_los_ids_son_unicos_y_las_paginas_tienen_componentes():
    ids = [c.id for c in registro.COMPONENTES]
    assert len(ids) == len(set(ids))
    assert len(registro.PAGINAS) == 8
    for p in registro.PAGINAS:
        assert registro.componentes_de(p.id), p.id
        assert p.url_path and p.pregunta and p.rutas


def test_cada_componente_apunta_a_una_pagina_del_registro():
    paginas = {p.id for p in registro.PAGINAS}
    assert {c.pagina for c in registro.COMPONENTES} <= paginas
    assert all(c.id.startswith(c.pagina + ".") for c in registro.COMPONENTES)


def test_cada_ruta_de_los_componentes_y_las_paginas_existe_en_el_openapi_de_la_api(rutas_api):
    usadas = {r for c in registro.COMPONENTES for r in c.rutas} | {r for p in registro.PAGINAS for r in p.rutas}
    assert usadas
    for r in usadas:
        assert _ruta_openapi(r, rutas_api), r


def test_las_rutas_de_un_componente_estan_entre_las_de_su_pagina():
    for c in registro.COMPONENTES:
        assert set(c.rutas) <= set(registro.pagina(c.pagina).rutas), c.id


def test_cada_kpi_de_los_componentes_existe_en_los_archivos_de_salida():
    with open(RAIZ / registro.KPIS, encoding="utf-8", newline="") as f:
        existentes = {r["kpi_id"] for r in csv.DictReader(f)}
    for c in registro.COMPONENTES:
        if c.kpi:
            assert c.kpi in existentes, c.id


def test_cada_campo_de_los_componentes_existe_en_el_archivo_de_salida_que_declaran():
    for c in registro.COMPONENTES:
        ruta = RAIZ / c.fuente
        assert ruta.is_file(), c.fuente
        if c.fuente.endswith(".csv"):
            assert set(c.campos) <= set(_encabezado_csv(c.fuente)), c.id
        else:
            texto = ruta.read_text(encoding="utf-8")
            for campo in c.campos:
                assert campo in texto, (c.id, campo)


def test_cada_componente_declara_una_advertencia_y_un_tipo_valido():
    for c in registro.COMPONENTES:
        assert c.advertencia.strip(), c.id
        assert c.tipo in {"metrica", "grafico", "tabla", "texto", "aviso", "descarga"}, c.id


def test_las_8_paginas_de_la_aplicacion_salen_del_registro():
    from src.panel import app
    assert set(app.MODULOS) == {p.id for p in registro.PAGINAS}
    for modulo in app.MODULOS.values():
        assert callable(modulo.render)


def test_el_registro_detecta_una_ruta_inexistente(rutas_api):
    assert not _ruta_openapi("/no-existe", rutas_api) and _ruta_openapi("/kpis/K1", rutas_api) and _ruta_openapi("/kpis/sensibilidad", rutas_api)


# ---------- aislamiento (6.5) ----------
def _arbol(ruta):
    return ast.parse(ruta.read_text(encoding="utf-8"))


def _modulos_importados(arbol):
    for n in ast.walk(arbol):
        if isinstance(n, ast.Import):
            yield from (a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            yield n.module
            yield from (f"{n.module}.{a.name}" for a in n.names)


@pytest.mark.parametrize("ruta", ARCHIVOS, ids=lambda p: p.relative_to(PANEL).as_posix())
def test_el_panel_no_importa_almacenes_ni_capas_del_pipeline_ni_credenciales(ruta):
    for m in _modulos_importados(_arbol(ruta)):
        for prohibido in IMPORTS_PROHIBIDOS:
            assert not (m == prohibido or m.startswith(prohibido + ".")), (ruta.name, m)


def test_los_unicos_imports_de_src_son_logger_y_el_propio_panel():
    for ruta in ARCHIVOS:
        for m in _modulos_importados(_arbol(ruta)):
            if m == "src" or m.startswith("src."):
                assert m.startswith(("src.panel", "src.logger")), (ruta.name, m)


def test_solo_hay_consultas_get_y_ninguna_llamada_peligrosa():
    for ruta in ARCHIVOS:
        texto = ruta.read_text(encoding="utf-8")
        for metodo in METODOS_PROHIBIDOS:
            assert metodo not in texto, (ruta.name, metodo)
        for n in ast.walk(ast.parse(texto)):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
                assert n.func.id not in LLAMADAS_PROHIBIDAS, (ruta.name, n.func.id)


def test_sin_html_inseguro_javascript_recursos_externos_ni_credenciales():
    for ruta in ARCHIVOS:
        texto = ruta.read_text(encoding="utf-8")
        assert "unsafe_allow_html" not in texto and "components.html" not in texto and "<script" not in texto.lower(), ruta.name
        assert re.search(r"https?://", texto) is None, ruta.name
        assert "MYSQL" not in texto.upper().replace("MYSQL_DOCKER", "") or "mysql" in texto.lower() and "MYSQL_" not in texto, ruta.name
        assert re.search(r"(?i)(password|contraseña|secret|token)\s*[=:]\s*['\"]", texto) is None, ruta.name


def test_solo_la_configuracion_lee_archivos_y_solo_lee_yaml():
    for ruta in ARCHIVOS:
        texto = ruta.read_text(encoding="utf-8")
        if ruta.name in SIN_CIFRAS:
            continue   # solo nombran rutas de archivos de salida
        abre = re.search(r"\bopen\(|read_csv|read_json|read_text|read_bytes|sqlite|\.db\b|\.jsonl\b", texto)
        if ruta.name == "configuracion.py":
            assert "yaml.safe_load" in texto
        else:
            assert abre is None, (ruta.name, abre and abre.group(0))


def test_no_hay_carpetas_ocultas_ni_pages_ni_streamlit_en_el_repositorio():
    assert not (RAIZ / ".streamlit").exists() and not (PANEL / "pages").exists()
    ocultas = [p for p in RAIZ.rglob(".streamlit") if ".venv" not in p.parts]
    assert ocultas == []


def test_ninguna_cifra_escrita_a_mano_en_los_textos_del_panel():
    """Ningún texto del panel lleva dígitos propios: las cifras salen de la API. Se permiten el nivel de confianza y los rótulos de grupo."""
    for ruta in ARCHIVOS:
        if ruta.name in SIN_CIFRAS:
            continue
        arbol = _arbol(ruta)
        docstrings = {id(n.body[0].value) for n in ast.walk(arbol) if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body
                      and isinstance(n.body[0], ast.Expr) and isinstance(getattr(n.body[0], "value", None), ast.Constant)}
        for n in ast.walk(arbol):
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docstrings:
                if ruta.name in ("configuracion.py", "tema.py", "app.py"):
                    continue
                resto = PERMITIDO_CON_DIGITOS.sub("", n.value)
                resto = re.sub(r"#[0-9A-Fa-f]{6}|\.\d+f|'[^']*'|\[[^\]]*\]", "", resto)   # colores, formatos y clases de caracteres de las expresiones regulares
                assert not re.search(r"\d", resto), (ruta.name, n.value)


def test_el_analisis_detecta_un_panel_que_viola_las_reglas(tmp_path):
    falso = tmp_path / "x.py"
    falso.write_text("import sqlite3\nimport requests\nx = client.post('http://externo.org')\nst.markdown('<b>', unsafe_allow_html=True)\n", encoding="utf-8")
    mods = set(_modulos_importados(_arbol(falso)))
    assert "sqlite3" in mods and "requests" in mods
    texto = falso.read_text(encoding="utf-8")
    assert ".post(" in texto and "unsafe_allow_html" in texto and re.search(r"https?://", texto)


def test_pyproject_de_dependencias_fija_streamlit_y_altair_y_no_aparecen_en_los_requisitos_de_airflow():
    req = (RAIZ / "requirements.txt").read_text(encoding="utf-8")
    assert re.search(r"^streamlit==\d", req, re.M) and re.search(r"^altair==\d", req, re.M) and re.search(r"^pandas==3\.0\.6$", req, re.M)
    airflow = (RAIZ / "orquestacion" / "requirements-airflow.txt").read_text(encoding="utf-8").lower()
    assert "streamlit" not in airflow and "altair" not in airflow


def test_el_catalogo_json_de_la_api_se_puede_leer():
    json.loads((RAIZ / registro.CATALOGO).read_text(encoding="utf-8"))


def test_la_trazabilidad_generada_coincide_con_el_registro():
    import importlib.util
    espec = importlib.util.spec_from_file_location("generar_trazabilidad", RAIZ / "scripts" / "panel" / "generar_trazabilidad.py")
    m = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(m)
    assert m.main(["--verificar"]) == 0
    assert (RAIZ / "docs" / "panel" / "trazabilidad_ui.md").read_text(encoding="utf-8") == m.texto()
    for c in registro.COMPONENTES:
        assert c.id in m.texto()
