"""Batería de verificación en vivo contra MySQL, solo sobre la base de PRUEBA (`sismo_cali_prueba`); nunca toca la base real.

Uso (PowerShell, raíz del proyecto, servicio MySQL80 activo y `.env` ya creado por configurar_mysql.py):
    .\\.venv\\Scripts\\python.exe scripts\\mysql\\verificar_mysql.py [--evidencia] [--solo-conexion]
Comprueba: privilegios, esquema desde cero, carga con conciliación al 100 %, idempotencia, equivalencia de endpoints con SQLite, corrida nueva
con entradas alteradas, reversión completa ante un fallo a mitad de carga, rechazo de violaciones de integridad (con su código de error) y sesión de solo lectura.
Con --evidencia escribe docs/evidencias/almacenamiento/ (saneado). Devuelve 0 si todo pasa. No imprime ni guarda credenciales.
"""
import argparse
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.common import load_config  # noqa: E402
from src.load import conciliacion, conexion, esquema, relacional  # noqa: E402
from src.logger import get_logger  # noqa: E402

log = get_logger(__name__)
TABLAS_HIJAS_A_PADRES = ("kpi_sensibilidad", "kpi", "construccion", "barrio_estrato", "corrida_archivo", "corrida", "comuna")


class Resultados:
    def __init__(self):
        self.filas = []

    def anotar(self, nombre, ok, detalle=""):
        self.filas.append((nombre, bool(ok), detalle))
        log.info("%s %s%s", "OK " if ok else "FALLA", nombre, f" - {detalle}" if detalle else "")

    @property
    def ok(self):
        return all(f[1] for f in self.filas)


def _una(conn, sql, params=()):
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        return cur.fetchone()
    finally:
        cur.close()


def _todas(conn, sql, params=()):
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        cur.close()


def _vaciar(conn):
    """Elimina las tablas del proyecto de la base de prueba (hijas primero)."""
    cur = conn.cursor()
    try:
        for t in TABLAS_HIJAS_A_PADRES:
            cur.execute(f"DROP TABLE IF EXISTS {t}")
        conn.commit()
    finally:
        cur.close()


def _conteos(conn):
    return {t: int(_una(conn, f"SELECT COUNT(*) FROM {t}")[0]) for t in TABLAS_HIJAS_A_PADRES}


def _copiar_entradas(destino):
    """Copia a `destino` solo los archivos que lee la carga, para alterarlos sin tocar data/."""
    csvs, qr = relacional.entradas()
    for ruta in [*csvs.values(), qr]:
        o = destino / ruta
        o.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / ruta, o)


def _alterar_npisos(raiz, valor):
    """Cambia el número de pisos de la primera construcción en la copia (valor válido: no rompe ninguna restricción)."""
    ruta = raiz / relacional.ENTRADAS_GOLD["construccion"]
    lineas = ruta.read_text(encoding="utf-8").split("\n")
    cab = lineas[0].split(",")
    i = cab.index("npisos")
    campos = lineas[1].split(",")
    campos[i] = str(valor)
    lineas[1] = ",".join(campos)
    ruta.write_text("\n".join(lineas), encoding="utf-8", newline="")


def _clonar_construccion(conn, corrida_id, cambios):
    """INSERT ... SELECT de una construcción existente con columnas reemplazadas por valores literales (parámetros)."""
    cols = [c["nombre"] for c in esquema.tablas(esquema.leer("mysql"))["construccion"]]
    expr = ", ".join("%s" if c in cambios else c for c in cols)
    params = [cambios[c] for c in cols if c in cambios]
    cur = conn.cursor()
    try:
        cur.execute(f"INSERT INTO construccion ({', '.join(cols)}) SELECT {expr} FROM construccion WHERE corrida_id = %s ORDER BY objectid LIMIT 1", (*params, corrida_id))
    finally:
        cur.close()


def verificar(res, solo_conexion=False):
    import pymysql
    from fastapi.testclient import TestClient

    from src.api.app import crear_app
    from src.api.repositorio import RepositorioRelacional
    import configurar_mysql as cm

    cfg = load_config()
    conn = conexion.conectar_mysql(prueba=True)
    try:
        version = _una(conn, "SELECT VERSION()")[0]
        base = _una(conn, "SELECT DATABASE()")[0]
        res.anotar("conexión con el usuario del proyecto", True, f"MySQL {version}, base {base}")
        if not base.endswith("_prueba"):
            res.anotar("la verificación solo corre sobre la base de prueba", False, base)
            return
        res.anotar("la verificación corre sobre la base de prueba", True, base)
        al = cfg["almacenamiento"]
        por_base = cm.verificar_privilegios(conn, [al["base"], al["base_prueba"]])
        res.anotar("privilegios: solo las dos bases, sin globales ni GRANT OPTION", True, "; ".join(f"{b}: {p}" for b, p in sorted(por_base.items())))
        if solo_conexion:
            return

        # --- esquema desde cero
        _vaciar(conn)
        esquema.aplicar(conn, "mysql")
        esperado = esquema.tablas(esquema.leer("mysql"))
        real = {}
        for nombre, columna in _todas(conn, "SELECT TABLE_NAME, COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() ORDER BY TABLE_NAME, ORDINAL_POSITION"):
            real.setdefault(nombre, []).append(columna)
        igual = {t: [c["nombre"] for c in cs] for t, cs in esperado.items()} == real
        res.anotar("esquema creado desde cero: tablas y columnas iguales al archivo SQL", igual, f"{len(real)} tablas, {sum(len(v) for v in real.values())} columnas")
        motores = _todas(conn, "SELECT DISTINCT ENGINE, TABLE_COLLATION FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE()")
        res.anotar("motor InnoDB y cotejamiento utf8mb4_0900_ai_ci en todas las tablas", motores == (("InnoDB", "utf8mb4_0900_ai_ci"),), str(motores))
        n_fk = _una(conn, "SELECT COUNT(*) FROM information_schema.REFERENTIAL_CONSTRAINTS WHERE CONSTRAINT_SCHEMA = DATABASE()")[0]
        n_ck = _una(conn, "SELECT COUNT(*) FROM information_schema.CHECK_CONSTRAINTS WHERE CONSTRAINT_SCHEMA = DATABASE()")[0]
        res.anotar("claves foráneas y restricciones CHECK creadas", n_fk == 8 and n_ck > 10, f"{n_fk} claves foráneas, {n_ck} restricciones CHECK")
        # --- carga y conciliación
        paq = relacional.preparar(cfg)
        r1 = relacional.cargar(conn, "mysql", paquete=paq, cfg=cfg)
        res.anotar("primera carga", r1["estado"] == "cargada", f"corrida {r1['corrida_id']}, filas {r1['filas']}, {r1['duracion_s']:.2f} s")
        c1 = conciliacion.conciliar(conn, "mysql", r1["corrida_id"], paquete=paq)
        celdas = sum(t["valores"] for t in c1["tablas"].values())
        dif = sum(t["diferencias"] for t in c1["tablas"].values())
        res.anotar("conciliación al 100 % (conteos, huellas e ida y vuelta de cada valor)", c1["ok"], f"{celdas} valores comparados, {dif} diferencias; " +
                   ", ".join(f"{t} {v['cargadas']}/{v['esperadas']}" for t, v in c1["tablas"].items()))
        hu = conciliacion.estado_de_integridad(conn, "mysql")
        res.anotar("integridad referencial: 0 filas huérfanas en cada relación", all(v == 0 for v in hu.values()), f"{len(hu)} relaciones revisadas")
        res.anotar("huérfanos de estrato: las construcciones sin cruce conservan el enlace nulo",
                   int(_una(conn, "SELECT COUNT(*) FROM construccion WHERE corrida_id = %s AND cruza_llave = 0 AND barrio_estrato_codigo IS NULL", (r1["corrida_id"],))[0]) ==
                   int(_una(conn, "SELECT COUNT(*) FROM construccion WHERE corrida_id = %s AND cruza_llave = 0", (r1["corrida_id"],))[0]))
        # --- idempotencia
        antes = _conteos(conn)
        r2 = relacional.cargar(conn, "mysql", paquete=paq, cfg=cfg)
        res.anotar("idempotencia: la misma entrada responde «ya cargada» y no escribe", r2["estado"] == "ya_cargada" and r2["corrida_id"] == r1["corrida_id"] and _conteos(conn) == antes,
                   f"corridas: {antes['corrida']}")
        # --- equivalencia con SQLite (antes de crear corridas alteradas)
        cliente_sqlite = TestClient(crear_app(almacenamiento="sqlite"), raise_server_exceptions=False)
        cliente_mysql = TestClient(crear_app(abrir_repositorio=lambda: RepositorioRelacional(conexion.conectar_mysql(prueba=True, solo_lectura=True), "mysql")), raise_server_exceptions=False)
        eq = conciliacion.equivalencia_endpoints(cliente_sqlite, cliente_mysql)
        res.anotar("la API sirve lo mismo desde MySQL que desde SQLite", all(e[1] for e in eq), f"{sum(e[1] for e in eq)} de {len(eq)} rutas idénticas (se ignora el campo que nombra el motor)")
        # --- entradas alteradas: corrida nueva
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            _copiar_entradas(raiz)
            _alterar_npisos(raiz, 9)
            r3 = relacional.cargar(conn, "mysql", cfg=cfg, raiz=raiz)
            distinta = r3["estado"] == "cargada" and r3["corrida_id"] != r1["corrida_id"] and r3["clave"] != r1["clave"]
            cont = _conteos(conn)
            res.anotar("entrada alterada: se crea una corrida nueva y la anterior queda intacta", distinta and cont["corrida"] == 2 and cont["construccion"] == 2 * antes["construccion"],
                       f"corridas {cont['corrida']}, construcciones {cont['construccion']}")
            diferentes = _una(conn, "SELECT COUNT(*) FROM construccion a JOIN construccion b ON a.objectid = b.objectid AND a.corrida_id = %s AND b.corrida_id = %s "
                                    "WHERE NOT (a.npisos <=> b.npisos)", (r1["corrida_id"], r3["corrida_id"]))[0]
            res.anotar("la historia permite comparar corridas con una consulta", int(diferentes) == 1, f"{diferentes} construcción con npisos distinto entre las dos corridas")
            res.anotar("la corrida original sigue conciliada al 100 %", conciliacion.conciliar(conn, "mysql", r1["corrida_id"], paquete=paq)["ok"])
        # --- fallo a mitad de carga
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            _copiar_entradas(raiz)
            _alterar_npisos(raiz, 8)
            antes_fallo = _conteos(conn)

            def explota(tabla):
                if tabla == "construccion":
                    raise RuntimeError("fallo inyectado tras insertar las construcciones")
            try:
                relacional.cargar(conn, "mysql", cfg=cfg, raiz=raiz, gancho=explota)
                fallo = False
            except RuntimeError:
                fallo = True
            res.anotar("fallo a mitad de carga: reversión completa", fallo and _conteos(conn) == antes_fallo, f"conteos antes y después iguales ({antes_fallo['corrida']} corridas)")
        # --- integridad: violaciones rechazadas
        cid = r1["corrida_id"]
        casos = [("corrida inexistente (clave foránea)", {"corrida_id": 999999, "objectid": 900000001}, {1452, 1216}),
                 ("clave primaria repetida", {}, {1062}),
                 ("estrato fuera de 1 a 6 (CHECK)", {"objectid": 900000002, "estrato": 9}, {3819}),
                 ("latitud fuera de Cali (CHECK)", {"objectid": 900000003, "lat": "9.0000000"}, {3819}),
                 ("cruza_llave con enlace nulo (CHECK)", {"objectid": 900000004, "cruza_llave": 1, "barrio_estrato_codigo": None}, {3819}),
                 ("barrio inexistente en la corrida (clave foránea compuesta)", {"objectid": 900000005, "cruza_llave": 1, "barrio_estrato_codigo": "999999"}, {1452, 1216})]
        base_n = _conteos(conn)
        for nombre, cambios, codigos in casos:
            codigo = None
            try:
                _clonar_construccion(conn, cid, cambios)
                conn.rollback()
            except pymysql.err.Error as e:
                conn.rollback()
                codigo = e.args[0]
            res.anotar(f"violación rechazada: {nombre}", codigo in codigos, f"código de error {codigo}")
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM corrida WHERE id = %s", (cid,))
            conn.rollback()
            codigo = None
        except pymysql.err.Error as e:
            conn.rollback()
            codigo = e.args[0]
        finally:
            cur.close()
        res.anotar("violación rechazada: borrar una corrida que tiene datos (RESTRICT)", codigo in (1451, 1217), f"código de error {codigo}")
        res.anotar("las pruebas de rechazo no dejaron filas", _conteos(conn) == base_n)
    finally:
        conn.close()
    # --- sesión de solo lectura
    ro = conexion.conectar_mysql(prueba=True, solo_lectura=True)
    try:
        try:
            cur = ro.cursor()
            cur.execute("DELETE FROM kpi")
            codigo = None
        except pymysql.err.Error as e:
            codigo = e.args[0]
        res.anotar("la conexión de solo lectura rechaza escrituras", codigo == 1792, f"código de error {codigo}")
    finally:
        ro.close()
    # --- 503 uniforme si MySQL no responde
    from src.api import errores
    def abrir_roto():
        raise errores.BaseNoDisponible("mysql")
    r = TestClient(crear_app(abrir_repositorio=abrir_roto), raise_server_exceptions=False).get("/kpis")
    res.anotar("si el almacén no responde la API contesta 503 con el JSON uniforme", r.status_code == 503 and r.json()["error"]["codigo"], f"estado {r.status_code}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Verificación en vivo de la carga relacional (base de prueba)")
    ap.add_argument("--evidencia", action="store_true", help="guarda la salida saneada en docs/evidencias/almacenamiento/")
    ap.add_argument("--solo-conexion", action="store_true", help="solo comprueba la conexión y los privilegios")
    ap.add_argument("--nombre", default="verificacion_mysql.txt")
    a = ap.parse_args(argv)
    res = Resultados()
    import time
    t0 = time.perf_counter()
    try:
        verificar(res, a.solo_conexion)
    except conexion.ConexionError as e:
        res.anotar("conexión con MySQL", False, str(e))
    except Exception as e:  # noqa: BLE001 - se informa el tipo y se falla; los errores de pymysql no llevan credenciales
        res.anotar("la verificación terminó con un error inesperado", False, f"{type(e).__name__}: {e}")
    dur = time.perf_counter() - t0
    cuerpo = "\n".join(f"- {'OK  ' if ok else 'FALLA'} {n}" + (f": {d}" if d else "") for n, ok, d in res.filas)
    cuerpo += f"\n\nResultado: {sum(f[1] for f in res.filas)} de {len(res.filas)} comprobaciones correctas.\n"
    print(cuerpo)
    if a.evidencia:
        sys.path.insert(0, str(ROOT / "scripts" / "evidencias"))
        import evidencia
        ruta = evidencia.guardar("almacenamiento", a.nombre, "Verificación en vivo de la carga relacional (base de prueba)",
                                 "python scripts/mysql/verificar_mysql.py --evidencia", 0 if res.ok else 1, dur, cuerpo)
        print("evidencia:", ruta.relative_to(ROOT))
    return 0 if res.ok else 1


if __name__ == "__main__":
    sys.exit(main())
