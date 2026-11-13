"""Carga relacional (independiente de las etapas del pipeline): copia los CSV de Silver y Gold al esquema relacional con historial.

Uso:  python scripts/cargar_mysql.py --destino mysql [--base principal|prueba] [--lote N]
      python scripts/cargar_mysql.py --destino sqlite --sqlite-ruta RUTA.db [--lote N]   (la ruta no puede estar dentro de data/)
Lee solo data/ y no modifica main.py ni load_database.py. Informa en el registro (sin credenciales) y devuelve 0 si cargó o ya estaba cargada.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.load import conexion, relacional  # noqa: E402
from src.logger import get_logger  # noqa: E402

log = get_logger(__name__)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Carga relacional por lotes con historial")
    ap.add_argument("--destino", choices=["mysql", "sqlite"], required=True)
    ap.add_argument("--base", choices=["principal", "prueba"], default="principal")
    ap.add_argument("--lote", type=int, default=None)
    ap.add_argument("--sqlite-ruta", default=None)
    a = ap.parse_args(argv)
    conn = None
    try:
        if a.destino == "mysql":
            conn = conexion.conectar_mysql(prueba=a.base == "prueba")
        else:
            if not a.sqlite_ruta:
                log.error("con --destino sqlite hay que indicar --sqlite-ruta (fuera de data/)")
                return 2
            ruta = Path(a.sqlite_ruta).resolve()
            if (ROOT / "data").resolve() in ruta.parents:
                log.error("la base SQLite de destino no puede estar dentro de data/")
                return 2
            conn = conexion.conectar_sqlite(ruta)
        r = relacional.cargar(conn, a.destino, lote=a.lote)
        log.info("resultado: %s; corrida %s; filas por tabla %s", r["estado"], r["corrida_id"], r["filas"])
        return 0
    except conexion.ConexionError as e:
        log.error("%s", e)
        return 3
    except Exception as e:  # noqa: BLE001 - el mensaje no lleva credenciales: pymysql no las incluye en sus errores
        log.error("la carga falló: %s: %s", type(e).__name__, e)
        return 1
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    sys.exit(main())
