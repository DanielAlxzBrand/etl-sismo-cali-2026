"""Carga relacional sin servidor MySQL: esquema, conversión, carga completa, conciliación, idempotencia, historial, reversión, integridad y equivalencia con la API de SQLite.

Todo corre sobre SQLite con claves foráneas activas y el mismo esquema relacional; lo que exige MySQL vive en scripts/mysql/verificar_mysql.py.
"""
import hashlib
import importlib.util
import shutil
import sqlite3
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from src.api.app import crear_app
from src.api.repositorio import RepositorioRelacional
from src.common import ROOT
from src.load import conciliacion, conexion, esquema, relacional

ESPERADAS = {"barrio_estrato": 346, "construccion": 5146, "kpi": 23, "kpi_sensibilidad": 107}


def _cargar_script(nombre):
    espec = importlib.util.spec_from_file_location(nombre, ROOT / "scripts" / f"{nombre}.py")
    modulo = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(modulo)
    return modulo


@pytest.fixture(scope="module")
def paquete():
    return relacional.preparar()


@pytest.fixture(scope="module")
def base_cargada(tmp_path_factory, paquete):
    """Archivo SQLite con una corrida cargada (se abre con conexiones nuevas en cada prueba)."""
    ruta = tmp_path_factory.mktemp("rel") / "relacional.db"
    conn = conexion.conectar_sqlite(ruta)
    relacional.cargar(conn, "sqlite", paquete=paquete)
    conn.close()
    return ruta


@pytest.fixture()
def conn(base_cargada, tmp_path):
    copia = tmp_path / "copia.db"
    shutil.copy2(base_cargada, copia)
    c = conexion.conectar_sqlite(copia)
    yield c
    c.close()


def _copiar_entradas(destino):
    csvs, qr = relacional.entradas()
    for ruta in [*csvs.values(), qr]:
        o = destino / ruta
        o.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / ruta, o)


def _cambiar_campo(raiz, columna, valor, fila=1):
    ruta = raiz / relacional.ENTRADAS_GOLD["construccion"]
    lineas = ruta.read_text(encoding="utf-8").split("\n")
    i = lineas[0].split(",").index(columna)
    campos = lineas[fila].split(",")
    campos[i] = valor
    lineas[fila] = ",".join(campos)
    ruta.write_text("\n".join(lineas), encoding="utf-8", newline="")


def _conteos(c):
    return {t: c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in ("corrida", "corrida_archivo", "comuna", *relacional.ORDEN_TABLAS)}


def _huellas_data():
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT / "data").rglob("*")) if p.is_file()}


# ---------------------------------------------------------------- esquema
def test_los_dos_esquemas_declaran_las_mismas_tablas_y_columnas_en_el_mismo_orden():
    assert esquema.paridad() == []
    assert list(esquema.tablas(esquema.leer("mysql"))) == ["corrida", "corrida_archivo", "comuna", "barrio_estrato", "construccion", "kpi", "kpi_sensibilidad"]


def test_cada_columna_y_cada_tabla_tienen_comentario_para_el_diccionario():
    texto = esquema.leer("mysql")
    for tabla, columnas in esquema.tablas(texto).items():
        assert all(c["comentario"] for c in columnas), tabla
    assert len(esquema.comentarios_de_tabla(texto)) == 7


def test_el_diccionario_de_datos_esta_al_dia_con_el_esquema():
    modelo = _cargar_script("make_modelo_datos")
    actual = (ROOT / "docs" / "almacenamiento" / "modelo_datos.md").read_text(encoding="utf-8").replace("\r\n", "\n")
    assert actual == modelo.markdown(modelo.analizar())


def test_el_esquema_se_aplica_en_sqlite_con_claves_foraneas_activas():
    c = conexion.conectar_sqlite()
    assert c.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    esquema.aplicar(c, "sqlite")
    esquema.aplicar(c, "sqlite")   # IF NOT EXISTS: aplicarlo dos veces no falla ni duplica
    tablas = [f[0] for f in c.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    assert len(tablas) == 7
    assert sum(len(c.execute(f"PRAGMA foreign_key_list({t})").fetchall()) for t in tablas) == 9   # 8 relaciones; la compuesta cuenta dos columnas


def test_las_sentencias_no_dependen_de_separadores_dentro_de_los_textos():
    assert all(";" not in s for s in esquema.sentencias(esquema.leer("mysql")))
    for d in ("mysql", "sqlite"):
        assert sum(s.startswith("CREATE TABLE") for s in esquema.sentencias(esquema.leer(d))) == 7


# ---------------------------------------------------------------- conversión estricta
@pytest.mark.parametrize("valor,tipo,esperado", [("5.0", "SMALLINT UNSIGNED", 5), ("7", "INT UNSIGNED", 7), ("True", "TINYINT(1)", 1), ("False", "TINYINT(1)", 0),
                                                 ("-76.5123456", "DECIMAL(10,7)", Decimal("-76.5123456")), ("0.5", "DECIMAL(7,6)", Decimal("0.500000")),
                                                 ("0.25", "DOUBLE", 0.25), ("2026-08-10", "DATE", "2026-08-10"), ("texto", "VARCHAR(10)", "texto")])
def test_conversion_correcta(valor, tipo, esperado):
    assert relacional.convertir(valor, tipo, True) == esperado


@pytest.mark.parametrize("valor,tipo", [("5.5", "SMALLINT UNSIGNED"), ("-1", "INT UNSIGNED"), ("Si", "TINYINT(1)"), ("1", "TINYINT(1)"), ("abc", "DOUBLE"),
                                        ("0.1234567", "DECIMAL(7,6)"), ("12345678.1", "DECIMAL(10,7)"), ("2026-13-45", "DATE"), ("x" * 11, "VARCHAR(10)"), ("", "INT")])
def test_conversion_que_perderia_informacion_falla(valor, tipo):
    with pytest.raises(relacional.ConversionError):
        relacional.convertir(valor, tipo, True)


def test_vacio_es_nulo_solo_si_la_columna_lo_permite():
    assert relacional.convertir("", "INT", False) is None


# ---------------------------------------------------------------- carga, conciliación e integridad
def test_la_carga_completa_concilia_al_cien_por_ciento(conn, paquete):
    c = conciliacion.conciliar(conn, "sqlite", 1, paquete=paquete)
    assert c["ok"] is True
    for tabla, n in ESPERADAS.items():
        t = c["tablas"][tabla]
        assert (t["esperadas"], t["cargadas"], t["diferencias"]) == (n, n, 0), tabla
        assert t["valores"] > 0
    assert all(c["archivos"].values()) and c["resumen_corrida"] is True


def test_la_conciliacion_detecta_un_valor_alterado(conn, paquete):
    conn.execute("UPDATE construccion SET npisos = 99 WHERE corrida_id = 1 AND objectid = (SELECT MIN(objectid) FROM construccion)")
    c = conciliacion.conciliar(conn, "sqlite", 1, paquete=paquete)
    assert c["ok"] is False and c["tablas"]["construccion"]["diferencias"] == 1
    assert "npisos" in c["tablas"]["construccion"]["ejemplos"][0]


def test_la_integridad_referencial_no_deja_huerfanos(conn):
    assert all(v == 0 for v in conciliacion.estado_de_integridad(conn, "sqlite").values())
    assert conn.execute("PRAGMA foreign_key_check").fetchall() == []


def test_los_huerfanos_de_estrato_se_conservan_con_el_enlace_nulo(conn, paquete):
    sin_cruce = conn.execute("SELECT COUNT(*) FROM construccion WHERE cruza_llave = 0").fetchone()[0]
    assert sin_cruce >= 1
    assert conn.execute("SELECT COUNT(*) FROM construccion WHERE cruza_llave = 0 AND barrio_estrato_codigo IS NULL").fetchone()[0] == sin_cruce
    assert conn.execute("SELECT COUNT(*) FROM construccion WHERE cruza_llave = 1 AND barrio_estrato_codigo IS NULL").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM construccion").fetchone()[0] == 5146   # ninguna construcción se descarta


def test_la_carga_repetida_es_idempotente(conn, paquete):
    antes = _conteos(conn)
    r = relacional.cargar(conn, "sqlite", paquete=paquete)
    assert r["estado"] == "ya_cargada" and r["corrida_id"] == 1
    assert _conteos(conn) == antes


def test_la_clave_de_corrida_es_determinista_y_sensible_a_cada_entrada():
    hue = relacional.huellas()
    assert relacional.clave_corrida(hue) == relacional.clave_corrida(list(reversed(hue)))
    assert len(relacional.clave_corrida(hue)) == 64
    alterada = [(r, ("0" * 64) if i == 0 else s, n) for i, (r, s, n) in enumerate(hue)]
    assert relacional.clave_corrida(alterada) != relacional.clave_corrida(hue)
    assert relacional.clave_corrida(hue, version=2) != relacional.clave_corrida(hue)


def test_una_entrada_alterada_crea_una_corrida_nueva_y_conserva_la_anterior(conn, paquete, tmp_path):
    _copiar_entradas(tmp_path)
    _cambiar_campo(tmp_path, "npisos", "9")
    r = relacional.cargar(conn, "sqlite", raiz=tmp_path)
    assert r["estado"] == "cargada" and r["corrida_id"] == 2
    c = _conteos(conn)
    assert c["corrida"] == 2 and c["construccion"] == 2 * ESPERADAS["construccion"] and c["kpi"] == 2 * ESPERADAS["kpi"]
    distintas = conn.execute("SELECT COUNT(*) FROM construccion a JOIN construccion b ON a.objectid = b.objectid AND a.corrida_id = 1 AND b.corrida_id = 2 "
                             "WHERE a.npisos IS NOT b.npisos").fetchone()[0]
    assert distintas == 1
    assert conciliacion.conciliar(conn, "sqlite", 1, paquete=paquete)["ok"] is True


def test_un_fallo_a_mitad_de_la_carga_revierte_todo(tmp_path):
    ruta = tmp_path / "r.db"
    c = conexion.conectar_sqlite(ruta)

    def explota(tabla):
        if tabla == "construccion":
            raise RuntimeError("fallo inyectado")
    with pytest.raises(RuntimeError):
        relacional.cargar(c, "sqlite", gancho=explota)
    assert all(n == 0 for n in _conteos(c).values())
    assert relacional.cargar(c, "sqlite")["estado"] == "cargada"   # tras el fallo, una carga limpia funciona
    c.close()


def test_un_valor_ilegible_falla_antes_de_escribir_nada(tmp_path):
    _copiar_entradas(tmp_path)
    _cambiar_campo(tmp_path, "estrato", "alto")
    c = conexion.conectar_sqlite()
    with pytest.raises(relacional.ConversionError):
        relacional.cargar(c, "sqlite", raiz=tmp_path)
    assert c.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()[0] == 0   # ni siquiera se creó el esquema
    c.close()


def _clonar(conn, cambios):
    cols = [c["nombre"] for c in esquema.tablas(esquema.leer("sqlite"))["construccion"]]
    expr = ", ".join("?" if c in cambios else c for c in cols)
    conn.execute(f"INSERT INTO construccion ({', '.join(cols)}) SELECT {expr} FROM construccion WHERE corrida_id = 1 ORDER BY objectid LIMIT 1", [cambios[c] for c in cols if c in cambios])


@pytest.mark.parametrize("cambios", [{"corrida_id": 999, "objectid": 900000001}, {}, {"objectid": 900000002, "estrato": 9}, {"objectid": 900000003, "lat": 9.0},
                                     {"objectid": 900000004, "lon": -70.0}, {"objectid": 900000005, "cruza_llave": 1, "barrio_estrato_codigo": None},
                                     {"objectid": 900000006, "cruza_llave": 1, "barrio_estrato_codigo": "999999"}, {"objectid": 900000007, "cruza_llave": 2},
                                     {"objectid": 900000008, "sin_datos": 1}, {"objectid": 900000009, "comuna": "99"}],
                         ids=["corrida inexistente", "clave repetida", "estrato 9", "latitud fuera de Cali", "longitud fuera de Cali", "cruce sin enlace",
                              "barrio inexistente", "bandera fuera de 0 y 1", "sin datos con severo", "comuna inexistente"])
def test_las_violaciones_de_integridad_se_rechazan(conn, cambios):
    antes = _conteos(conn)
    with pytest.raises(sqlite3.IntegrityError):
        _clonar(conn, cambios)
    conn.rollback()
    assert _conteos(conn) == antes


def test_no_se_puede_borrar_una_corrida_con_datos(conn):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("DELETE FROM corrida WHERE id = 1")


def test_la_carga_no_escribe_en_data(tmp_path):
    antes = _huellas_data()
    c = conexion.conectar_sqlite(tmp_path / "x.db")
    relacional.cargar(c, "sqlite")
    c.close()
    assert _huellas_data() == antes


def test_el_cli_rechaza_una_base_de_destino_dentro_de_data():
    cli = _cargar_script("cargar_mysql")
    assert cli.main(["--destino", "sqlite", "--sqlite-ruta", str(ROOT / "data" / "gold" / "no_debe_existir.db")]) == 2
    assert not (ROOT / "data" / "gold" / "no_debe_existir.db").exists()
    assert cli.main(["--destino", "sqlite"]) == 2


def test_el_cli_carga_en_sqlite_fuera_de_data(tmp_path):
    cli = _cargar_script("cargar_mysql")
    destino = tmp_path / "cli.db"
    assert cli.main(["--destino", "sqlite", "--sqlite-ruta", str(destino)]) == 0
    assert cli.main(["--destino", "sqlite", "--sqlite-ruta", str(destino)]) == 0   # idempotente
    c = sqlite3.connect(destino)
    assert c.execute("SELECT COUNT(*) FROM corrida").fetchone()[0] == 1
    c.close()


# ---------------------------------------------------------------- repositorio relacional y API
def _cliente_relacional(ruta):
    return TestClient(crear_app(abrir_repositorio=lambda: RepositorioRelacional(conexion.conectar_sqlite(ruta, solo_lectura=True), "sqlite")), raise_server_exceptions=False)


def test_la_api_sirve_lo_mismo_desde_el_almacen_relacional_que_desde_sqlite(base_cargada):
    eq = conciliacion.equivalencia_endpoints(TestClient(crear_app(), raise_server_exceptions=False), _cliente_relacional(base_cargada))
    assert len(eq) >= 15
    assert [e for e in eq if not e[1]] == []
    assert all(e[2] in (200, 422) for e in eq)


def test_la_api_informa_el_almacenamiento_activo(base_cargada):
    assert TestClient(crear_app()).get("/health").json()["almacenamiento"] == "sqlite"
    h = _cliente_relacional(base_cargada).get("/health").json()
    assert h["estado"] == "ok" and h["filas_por_tabla"]["gold_final"] == 5146


def test_la_conexion_relacional_es_de_solo_lectura(base_cargada):
    c = conexion.conectar_sqlite(base_cargada, solo_lectura=True)
    with pytest.raises(sqlite3.OperationalError):
        c.execute("DELETE FROM kpi")
    c.close()


def test_una_base_sin_corridas_da_503_uniforme(tmp_path):
    vacia = tmp_path / "vacia.db"
    c = conexion.conectar_sqlite(vacia)
    esquema.aplicar(c, "sqlite")
    c.close()
    cliente = _cliente_relacional(vacia)
    r = cliente.get("/kpis")
    assert r.status_code == 503 and r.json()["error"]["codigo"] == "base_no_disponible"
    assert cliente.get("/health").json()["estado"] == "degradado"


def test_si_mysql_no_responde_la_api_da_503_sin_datos_de_conexion(monkeypatch):
    def falla(*a, **k):
        raise conexion.ConexionError("no se pudo conectar a MySQL: no hay un servidor")
    monkeypatch.setattr(conexion, "conectar_mysql", falla)
    cliente = TestClient(crear_app(almacenamiento="mysql"), raise_server_exceptions=False)
    r = cliente.get("/kpis")
    assert r.status_code == 503 and r.json()["error"]["codigo"] == "base_no_disponible"
    assert "MYSQL" not in r.text and "password" not in r.text.lower()
    h = cliente.get("/health").json()
    assert h["estado"] == "degradado" and h["almacenamiento"] == "mysql"


def test_un_almacenamiento_desconocido_se_rechaza():
    with pytest.raises(ValueError):
        crear_app(almacenamiento="oracle")
