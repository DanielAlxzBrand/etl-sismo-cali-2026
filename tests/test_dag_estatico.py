"""Pruebas estáticas del DAG y de la imagen de Airflow: se analiza el archivo con `ast` (Airflow no se instala ni se importa en Windows)."""
import ast
import hashlib
import importlib.metadata as im
import importlib.util
import re

import pytest

from src.common import ROOT

DAG = ROOT / "dags" / "medallon_etl_dag.py"
TAREAS = ["validar_bronze", "transformar_a_silver", "integrar_a_gold", "cargar_datawarehouse"]
ARBOL = ast.parse(DAG.read_text(encoding="utf-8"))


def _con_dag():
    return next(n for n in ARBOL.body if isinstance(n, ast.With) and isinstance(n.items[0].context_expr, ast.Call) and getattr(n.items[0].context_expr.func, "id", "") == "DAG")


def _kw(llamada):
    return {k.arg: k.value for k in llamada.keywords}


def _tareas():
    return [f for f in _con_dag().body if isinstance(f, ast.FunctionDef) and any(getattr(d, "id", "") == "task" for d in f.decorator_list)]


def _llamadas(nodo):
    return [n for n in ast.walk(nodo) if isinstance(n, ast.Call)]


def _nombre_llamada(c):
    f = c.func
    return f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")


# ---------------------------------------------------------------- definición del DAG
def test_el_dag_tiene_el_identificador_y_los_parametros_acordados():
    kw = _kw(_con_dag().items[0].context_expr)
    assert ast.literal_eval(kw["dag_id"]) == "medallon_etl_sismo"
    assert ast.literal_eval(kw["catchup"]) is False
    assert ast.literal_eval(kw["schedule"]) in (None, "0 6 * * *")   # manual mientras se valida; luego diaria a las 06:00 de Bogotá
    assert ast.literal_eval(kw["tags"]) == ["etl", "medallion", "sismo"]


def test_start_date_lleva_la_zona_de_bogota():
    inicio = _kw(_con_dag().items[0].context_expr)["start_date"]
    zona = _kw(inicio)["tzinfo"]
    assert getattr(inicio.func, "id", "") == "datetime" and _nombre_llamada(zona) == "ZoneInfo" and ast.literal_eval(zona.args[0]) == "America/Bogota"


def test_las_cuatro_tareas_tienen_los_nombres_y_el_orden_de_la_guia():
    assert [t.name for t in _tareas()] == TAREAS


def test_las_dependencias_son_una_cadena_lineal():
    cuerpo = _con_dag().body
    asignaciones = {a.targets[0].id: _nombre_llamada(a.value) for a in cuerpo if isinstance(a, ast.Assign) and isinstance(a.value, ast.Call)}
    assert asignaciones == dict(zip(["bronze", "silver", "gold", "load"], TAREAS))
    cadena = next(e.value for e in cuerpo if isinstance(e, ast.Expr) and isinstance(e.value, ast.BinOp))
    nombres = []
    while isinstance(cadena, ast.BinOp) and isinstance(cadena.op, ast.RShift):
        nombres.insert(0, cadena.right.id)
        cadena = cadena.left
    nombres.insert(0, cadena.id)
    assert nombres == ["bronze", "silver", "gold", "load"]


def test_cada_tarea_usa_la_funcion_real_del_pipeline():
    esperado = {"validar_bronze": {"read_manifest", "verify_files"}, "transformar_a_silver": {"run_transform"}, "integrar_a_gold": {"run_gold"},
                "cargar_datawarehouse": {"load_to_sqlite", "conexion", "relacional"}}
    for t in _tareas():
        importados = {a.name for n in ast.walk(t) if isinstance(n, ast.ImportFrom) and (n.module or "").startswith("src") for a in n.names}
        assert esperado[t.name] <= importados, t.name
    carga = next(t for t in _tareas() if t.name == "cargar_datawarehouse")
    assert {"conectar_mysql", "cargar"} <= {_nombre_llamada(c) for c in _llamadas(carga)}


# ---------------------------------------------------------------- reglas de la copia de trabajo y del repositorio de solo lectura
def test_src_solo_se_importa_dentro_de_las_tareas():
    for n in ARBOL.body:
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            assert not ((getattr(n, "module", "") or "").startswith("src") or any(a.name.startswith("src") for a in n.names))
    hay = [n for t in _tareas() for n in ast.walk(t) if isinstance(n, ast.ImportFrom) and (n.module or "").startswith("src")]
    assert hay


def test_la_ruta_del_proyecto_en_el_contenedor_es_la_de_la_guia():
    asignaciones = {a.targets[0].id: a.value for a in ARBOL.body if isinstance(a, ast.Assign) and isinstance(a.targets[0], ast.Name)}
    assert ast.literal_eval(asignaciones["PROJECT_DIR"].args[0]) == "/opt/airflow/medallon"


def test_nunca_se_escribe_ni_se_borra_nada_fuera_de_la_copia_de_trabajo():
    for c in _llamadas(ARBOL):
        if _nombre_llamada(c) == "rmtree":
            assert isinstance(c.args[0], ast.Name) and c.args[0].id == "trabajo"
    for f in [n for n in ast.walk(ARBOL) if isinstance(n, ast.FunctionDef)]:
        for c in _llamadas(f):
            if _nombre_llamada(c) in ("write_text", "write_bytes", "unlink", "mkdir", "touch"):
                # lo único que crea el DAG es la estructura de la copia: en _copiar_trabajo y sobre `destino` (la copia)
                assert f.name == "_copiar_trabajo" and "destino" in ast.unparse(c.func), f"escritura inesperada en {f.name}"
    destinos = [ast.unparse(c.args[1]) for f in ARBOL.body if isinstance(f, ast.FunctionDef) and f.name == "_copiar_trabajo" for c in _llamadas(f) if _nombre_llamada(c) in ("copytree", "copy2")]
    assert destinos and all(d.startswith("destino") for d in destinos)   # toda copia escribe en `destino`, nunca en PROJECT_DIR
    copiar = next(f for f in ARBOL.body if isinstance(f, ast.FunctionDef) and f.name == "_copiar_trabajo")
    carpetas = next(n for n in ast.walk(copiar) if isinstance(n, ast.For)).iter
    assert [ast.literal_eval(e) for e in carpetas.elts] == ["src", "config", "data"]   # sin .env, .venv, .git, dist, logs ni cachés
    cadenas = [n.value for cuerpo in copiar.body[1:] for n in ast.walk(cuerpo) if isinstance(n, ast.Constant) and isinstance(n.value, str)]   # sin el docstring
    assert not any(".env" in c for c in cadenas)


def test_la_copia_es_unica_por_ejecucion_y_esta_fuera_del_volumen_del_repositorio():
    texto = DAG.read_text(encoding="utf-8")
    assert "tempfile.gettempdir()" in texto and 're.sub(r"[^A-Za-z0-9]+", "_", run_id)' in texto
    assert 'BASE_TRABAJO = Path(tempfile.gettempdir())' in texto


def test_cada_tarea_compara_con_el_repositorio_y_la_carga_limpia_la_copia():
    for nombre, funciones in {"transformar_a_silver": "_comparar_con_repo", "integrar_a_gold": "_comparar_con_repo", "cargar_datawarehouse": "_huella_tablas"}.items():
        t = next(t for t in _tareas() if t.name == nombre)
        assert funciones in {_nombre_llamada(c) for c in _llamadas(t)}, nombre
    carga = next(t for t in _tareas() if t.name == "cargar_datawarehouse")
    assert any(isinstance(n, ast.Try) and n.finalbody and any(_nombre_llamada(c) == "rmtree" for f in n.finalbody for c in _llamadas(f)) for n in ast.walk(carga))
    comparar = next(f for f in ARBOL.body if isinstance(f, ast.FunctionDef) and f.name == "_comparar_con_repo")
    assert any(isinstance(n, ast.Raise) for n in ast.walk(comparar))   # si difiere, falla


def test_el_fallo_inducido_esta_en_las_cuatro_tareas_antes_de_producir_salidas():
    helper = next(f for f in ARBOL.body if isinstance(f, ast.FunctionDef) and f.name == "_fallo_inducido")
    assert any(isinstance(n, ast.Raise) for n in ast.walk(helper)) and "fallo_inducido" in ast.unparse(helper)
    for t in _tareas():
        orden = [_nombre_llamada(c) for c in _llamadas(t)]
        llamada = next(c for c in _llamadas(t) if _nombre_llamada(c) == "_fallo_inducido")
        assert ast.literal_eval(llamada.args[0]) == t.name
        assert orden.index("_fallo_inducido") < min(i for i, n in enumerate(orden) if n in ("_copiar_trabajo", "run_transform", "run_gold", "load_to_sqlite", "verify_files", "read_manifest")), t.name


# ---------------------------------------------------------------- secretos y rutas de Windows
def test_el_dag_no_lleva_rutas_de_windows_ni_contrasenas_literales():
    texto = DAG.read_text(encoding="utf-8")
    assert not re.search(r"[A-Za-z]:\\", texto) and "C:/Users" not in texto and "Users\\" not in texto
    spec = importlib.util.spec_from_file_location("escanear_secretos_dag", ROOT / "scripts" / "escanear_secretos.py")
    esc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(esc)
    assert esc.escanear_bytes("dags/medallon_etl_dag.py", DAG.read_bytes()) == []


def test_las_credenciales_se_leen_en_memoria_y_nunca_se_imprimen():
    for c in _llamadas(ARBOL):
        if _nombre_llamada(c) == "print":
            assert "PASSWORD" not in ast.unparse(c) and "_credenciales_docker" not in ast.unparse(c)
    helper = next(f for f in ARBOL.body if isinstance(f, ast.FunctionDef) and f.name == "_credenciales_docker")
    texto = ast.unparse(helper)
    assert "dotenv_values" in texto and "host.docker.internal" in DAG.read_text(encoding="utf-8") and "MYSQL_DOCKER_PASSWORD" in texto
    assert not any(_nombre_llamada(c) in ("copy2", "copyfile", "write_text", "open") for c in _llamadas(helper))


def test_el_archivo_usa_print_como_la_guia_y_no_el_registro_del_proyecto_en_el_nivel_superior():
    assert any(_nombre_llamada(c) == "print" for t in _tareas() for c in _llamadas(t))
    assert "get_logger" not in DAG.read_text(encoding="utf-8")


# ---------------------------------------------------------------- imagen y requisitos
def test_los_requisitos_de_airflow_tienen_las_mismas_versiones_que_el_venv():
    lineas = [l.strip() for l in (ROOT / "orquestacion" / "requirements-airflow.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
    pines = dict(l.split("==") for l in lineas)
    assert set(pines) == {"pandas", "numpy", "PyYAML", "python-dotenv", "requests", "shapely", "PyMySQL", "cryptography"}
    assert {n: im.version(n) for n in pines} == pines


def test_pandas_es_la_version_con_la_que_se_generaron_los_archivos_de_la_linea_base():
    """Con pandas 3.1.1 el redondeo a 12 decimales y la lectura de CSV cambian la última cifra de `indice_escombros`; la línea base se produjo con 3.0.6."""
    assert im.version("pandas") == "3.0.6"
    pines = dict(l.split("==") for l in (ROOT / "orquestacion" / "requirements-airflow.txt").read_text(encoding="utf-8").split())
    assert pines["pandas"] == "3.0.6"


def test_el_dockerfile_separa_copy_y_run_y_declara_la_imagen_de_la_guia():
    lineas = (ROOT / "orquestacion" / "Dockerfile").read_text(encoding="utf-8").splitlines()
    assert lineas[0] == "FROM apache/airflow:3.3.2"
    copia = [l for l in lineas if l.startswith("COPY")]
    run = [i for i, l in enumerate(lineas) if l.startswith("RUN")]
    assert copia == ["COPY requirements-airflow.txt /requirements-airflow.txt"] and len(run) == 1
    assert not any("COPY" in l and "RUN" in l for l in lineas)
    assert any("-r /requirements-airflow.txt" in l for l in lineas)
    assert not any(l.startswith(("ENV", "ARG")) and re.search(r"PASS|TOKEN|SECRET|KEY", l, re.I) for l in lineas)   # nada secreto en la imagen


def test_la_copia_versionada_del_dag_coincide_con_el_hash_registrado():
    registrado = (ROOT / "orquestacion" / "dag.sha256").read_text(encoding="utf-8").split()[0]
    assert hashlib.sha256(DAG.read_bytes()).hexdigest() == registrado, "el DAG cambió: ejecute scripts/orquestacion/sincronizar_dag.py --registrar y vuelva a sincronizar"


def test_las_variables_de_docker_estan_en_el_ejemplo_sin_valores():
    lineas = (ROOT / ".env.example").read_text(encoding="utf-8").splitlines()
    for nombre in ("MYSQL_DOCKER_USER", "MYSQL_DOCKER_PASSWORD", "MYSQL_DOCKER_ORIGEN"):
        assert f"{nombre}=" in lineas
    assert all(l.split("=", 1)[1] == "" for l in lineas if "=" in l)


@pytest.mark.parametrize("fragmento", ["Windows", "WSL2", "Docker Desktop"])
def test_el_dag_no_nombra_el_entorno_de_desarrollo_en_su_codigo(fragmento):
    assert fragmento not in DAG.read_text(encoding="utf-8")
