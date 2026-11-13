"""Respaldo lógico (CSV con manifiesto sha256) y restauración con conciliación, sin herramientas externas.

Uso (PowerShell, raíz del proyecto):
    .\\.venv\\Scripts\\python.exe scripts\\mysql\\respaldar_restaurar.py [--origen principal|prueba] [--carpeta RUTA] [--evidencia]
Lee la base de origen con una sesión de solo lectura, escribe un CSV por tabla y `manifiesto_respaldo.json` (sha256 y filas) en una carpeta FUERA del repositorio
(por defecto una carpeta temporal), restaura en la base de PRUEBA (que se reconstruye desde cero; nunca en la real) y concilia tabla por tabla con una huella de todas las filas.
Alternativa con herramientas del servidor (no se ejecuta aquí): `mysqldump --single-transaction --no-tablespaces -u sismo_etl -p sismo_cali > respaldo.sql`; la contraseña se escribe cuando
la herramienta la pide, nunca en la línea de comandos.
"""
import argparse
import csv
import hashlib
import json
import sys
import tempfile
import time
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.common import load_config  # noqa: E402
from src.load import conexion, esquema, relacional  # noqa: E402
from src.logger import get_logger  # noqa: E402

log = get_logger(__name__)
ORDEN = ("comuna", "corrida", "corrida_archivo", "barrio_estrato", "construccion", "kpi", "kpi_sensibilidad")
NULO = "\\N"   # marca de NULL en los CSV: ningún dato del proyecto la contiene
MANIFIESTO = "manifiesto_respaldo.json"


class RespaldoError(Exception):
    """El respaldo o la restauración no se pudo completar o no concilia."""


def _texto(valor):
    """Valor de la base como texto estable (el mismo para el CSV y para la huella de conciliación)."""
    if valor is None:
        return NULO
    if isinstance(valor, bool):
        return "1" if valor else "0"
    if isinstance(valor, (datetime, date)):
        return valor.isoformat(sep=" ") if isinstance(valor, datetime) else valor.isoformat()
    if isinstance(valor, float):
        return repr(valor)
    if isinstance(valor, Decimal):
        return format(valor, "f")
    t = str(valor)
    if t == NULO:
        raise RespaldoError("un dato coincide con la marca de nulo del respaldo")
    return t


def _columnas(tabla):
    return [c for c in esquema.tablas(esquema.leer("mysql"))[tabla]]


def _filas(conn, tabla, columnas):
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT {', '.join(c['nombre'] for c in columnas)} FROM {tabla} ORDER BY {', '.join(str(i + 1) for i in range(len(columnas)))}")
        return cur.fetchall()
    finally:
        cur.close()


def huella_tabla(conn, tabla):
    """(filas, sha256) de todas las filas de la tabla en texto estable y orden total."""
    cols = _columnas(tabla)
    h = hashlib.sha256()
    n = 0
    for fila in _filas(conn, tabla, cols):
        h.update(("\x1f".join(_texto(v) for v in fila) + "\n").encode("utf-8"))
        n += 1
    return n, h.hexdigest()


def respaldar(conn, carpeta):
    """Escribe un CSV por tabla y el manifiesto en `carpeta` (debe estar fuera de data/ y del repositorio). Devuelve el manifiesto."""
    carpeta = Path(carpeta).resolve()
    if ROOT in carpeta.parents or carpeta == ROOT:
        raise RespaldoError("la carpeta del respaldo debe estar fuera del repositorio")
    carpeta.mkdir(parents=True, exist_ok=True)
    archivos = {}
    for tabla in ORDEN:
        cols = _columnas(tabla)
        ruta = carpeta / f"{tabla}.csv"
        n = 0
        with open(ruta, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow([c["nombre"] for c in cols])
            for fila in _filas(conn, tabla, cols):
                w.writerow([_texto(v) for v in fila])
                n += 1
        archivos[tabla] = {"archivo": ruta.name, "filas": n, "sha256": relacional.sha256_file(ruta), "bytes": ruta.stat().st_size}
    huellas = {t: huella_tabla(conn, t) for t in ORDEN}
    manifiesto = {"version_esquema": esquema.VERSION_ESQUEMA, "tablas": archivos, "huellas_de_filas": {t: {"filas": n, "sha256": h} for t, (n, h) in huellas.items()}}
    (carpeta / MANIFIESTO).write_text(json.dumps(manifiesto, indent=2, sort_keys=True), encoding="utf-8", newline="\n")
    return manifiesto


def _desde_texto(texto, tipo, no_nulo, contexto):
    """Convierte un valor del CSV de respaldo al tipo de la columna (los booleanos del respaldo son 0 y 1)."""
    if texto == NULO:
        if no_nulo:
            raise RespaldoError(f"nulo en una columna obligatoria ({contexto})")
        return None
    t = tipo.upper()
    if t == "TINYINT(1)":
        if texto not in ("0", "1"):
            raise RespaldoError(f"booleano no válido ({contexto})")
        return int(texto)
    if t.startswith("DATETIME"):
        return texto
    return relacional.convertir(texto, tipo, no_nulo, contexto)


def verificar_manifiesto(carpeta):
    """Comprueba que cada CSV coincide con el sha256 del manifiesto antes de restaurar; devuelve el manifiesto."""
    carpeta = Path(carpeta)
    man = json.loads((carpeta / MANIFIESTO).read_text(encoding="utf-8"))
    for tabla, info in man["tablas"].items():
        if relacional.sha256_file(carpeta / info["archivo"]) != info["sha256"]:
            raise RespaldoError(f"el archivo {info['archivo']} no coincide con el manifiesto: el respaldo está alterado o incompleto")
    if man["version_esquema"] != esquema.VERSION_ESQUEMA:
        raise RespaldoError("el respaldo es de otra versión del esquema")
    return man


def restaurar(conn, dialecto, carpeta, lote=1000, reiniciar=True):
    """Restaura el respaldo en la base indicada (esquema desde cero con `reiniciar`) dentro de UNA transacción; con error no queda nada a medias."""
    man = verificar_manifiesto(carpeta)
    cur = conn.cursor()
    try:
        if reiniciar:
            for t in reversed(ORDEN):
                cur.execute(f"DROP TABLE IF EXISTS {t}")
            conn.commit()
        esquema.aplicar(conn, dialecto)
        for t in ORDEN:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            if cur.fetchone()[0]:
                raise RespaldoError(f"la tabla {t} del destino no está vacía: no se restaura encima de datos")
        for tabla in ORDEN:
            cols = _columnas(tabla)
            with open(Path(carpeta) / man["tablas"][tabla]["archivo"], encoding="utf-8", newline="") as f:
                lector = csv.reader(f)
                cab = next(lector)
                if cab != [c["nombre"] for c in cols]:
                    raise RespaldoError(f"las columnas de {tabla}.csv no coinciden con el esquema")
                filas = [tuple(_desde_texto(v, c["tipo"], c["no_nulo"], f"{tabla}, fila {i}, {c['nombre']}") for v, c in zip(r, cols)) for i, r in enumerate(lector, 1)]
            relacional._insertar(cur, dialecto, tabla, cab, filas, lote)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
    return man


def conciliar(origen, destino, manifiesto):
    """[(tabla, filas_origen, filas_destino, huella_igual)] comparando la huella de todas las filas del origen (en el manifiesto) con la del destino restaurado."""
    salida = []
    for tabla in ORDEN:
        n, h = huella_tabla(destino, tabla)
        esperado = manifiesto["huellas_de_filas"][tabla]
        n0, h0 = huella_tabla(origen, tabla)
        salida.append((tabla, n0, n, h == h0 == esperado["sha256"]))
    return salida


def main(argv=None):
    ap = argparse.ArgumentParser(description="Respaldo lógico y restauración con conciliación")
    ap.add_argument("--origen", choices=["principal", "prueba"], default="principal")
    ap.add_argument("--carpeta", default=None, help="carpeta del respaldo (fuera del repositorio; por defecto una carpeta temporal)")
    ap.add_argument("--evidencia", action="store_true")
    a = ap.parse_args(argv)
    cfg = load_config()
    destino_prueba = a.origen == "principal"
    if a.origen == "prueba":
        log.error("restaurar sobre el mismo origen no tiene sentido: use --origen principal")
        return 2
    t0 = time.perf_counter()
    carpeta = Path(a.carpeta) if a.carpeta else Path(tempfile.mkdtemp(prefix="respaldo_sismo_"))
    try:
        origen = conexion.conectar_mysql(solo_lectura=True)
        destino = conexion.conectar_mysql(prueba=True)
    except conexion.ConexionError as e:
        log.error("%s", e)
        return 3
    try:
        cur = destino.cursor()
        cur.execute("SELECT DATABASE()")
        base = cur.fetchone()[0]
        cur.close()
        if not destino_prueba or not base.endswith("_prueba"):
            log.error("la restauración solo se hace en la base de prueba (conectado a %s)", base)
            return 2
        t1 = time.perf_counter()
        man = respaldar(origen, carpeta)
        t_resp = time.perf_counter() - t1
        t1 = time.perf_counter()
        restaurar(destino, "mysql", carpeta, lote=int(cfg["almacenamiento"]["lote"]))
        t_rest = time.perf_counter() - t1
        resultado = conciliar(origen, destino, man)
    except (RespaldoError, Exception) as e:  # noqa: BLE001 - se informa el tipo y el mensaje; ninguno trae credenciales
        log.error("respaldo o restauración fallidos: %s: %s", type(e).__name__, e)
        return 1
    finally:
        origen.close()
        destino.close()
    ok = all(r[3] and r[1] == r[2] for r in resultado)
    lineas = ["| Tabla | Filas respaldadas | Filas restauradas | Huella de filas | sha256 del CSV (12 primeros) |", "|---|---|---|---|---|"]
    for tabla, n0, n1, igual in resultado:
        lineas.append(f"| {tabla} | {n0} | {n1} | {'igual' if igual else 'DISTINTA'} | {man['tablas'][tabla]['sha256'][:12]} |")
    total = sum(r[1] for r in resultado)
    cuerpo = (f"Respaldo lógico de la base real en CSV (una carpeta fuera del repositorio) y restauración en la base de prueba reconstruida desde cero.\n\n" + "\n".join(lineas) +
              f"\n\nFilas totales: {total}. Respaldo: {t_resp:.2f} s. Restauración: {t_rest:.2f} s. Conciliación: {'correcta en todas las tablas' if ok else 'CON DIFERENCIAS'}.\n"
              "El manifiesto del respaldo (sha256 de cada CSV) se verificó antes de restaurar.\n"
              "Alternativa con herramientas del servidor, no ejecutada: mysqldump con --single-transaction; la contraseña se escribe cuando la herramienta la pide.\n")
    print(cuerpo)
    if a.evidencia:
        sys.path.insert(0, str(ROOT / "scripts" / "evidencias"))
        import evidencia
        evidencia.guardar("almacenamiento", "respaldo_restauracion.txt", "Respaldo lógico y restauración con conciliación",
                          "python scripts/mysql/respaldar_restaurar.py --evidencia", 0 if ok else 1, time.perf_counter() - t0, cuerpo)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
