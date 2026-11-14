"""Sincroniza el DAG versionado del repositorio (dags/medallon_etl_dag.py) con el DAG vivo de la carpeta hermana airflow-medallon/dags.

Uso:  python scripts/orquestacion/sincronizar_dag.py              copia el DAG del repositorio a airflow-medallon/dags
      python scripts/orquestacion/sincronizar_dag.py --verificar  solo compara los sha256 de ambos (código 0 si son iguales)
      python scripts/orquestacion/sincronizar_dag.py --registrar  anota el sha256 del DAG versionado en orquestacion/dag.sha256 (una prueba lo exige)
La carpeta de Airflow se busca junto al proyecto (`../airflow-medallon`) o se indica con --airflow. El repositorio solo se lee.
"""
import argparse
import hashlib
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.logger import get_logger  # noqa: E402

log = get_logger(__name__)
NOMBRE = "medallon_etl_dag.py"
REGISTRO = ROOT / "orquestacion" / "dag.sha256"


def sha256(ruta):
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def rutas(airflow=None):
    """(DAG del repositorio, DAG vivo) con la carpeta hermana airflow-medallon por defecto."""
    base = Path(airflow).resolve() if airflow else ROOT.parent / "airflow-medallon"
    return ROOT / "dags" / NOMBRE, base / "dags" / NOMBRE


def sincronizar(origen, destino):
    """Copia el DAG; devuelve el sha256 común. La carpeta dags de Airflow debe existir (la crea el paso 13 de la guía)."""
    if not destino.parent.is_dir():
        raise FileNotFoundError(f"no existe la carpeta de DAG de Airflow: {destino.parent.name}")
    shutil.copy2(origen, destino)
    return sha256(destino)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--verificar", action="store_true", help="solo compara los sha256")
    ap.add_argument("--registrar", action="store_true", help="anota el sha256 del DAG versionado en orquestacion/dag.sha256")
    ap.add_argument("--airflow", default=None, help="carpeta airflow-medallon (por defecto, la hermana del proyecto)")
    a = ap.parse_args(argv)
    origen, destino = rutas(a.airflow)
    if not origen.exists():
        log.error("no existe el DAG versionado %s", origen.relative_to(ROOT))
        return 2
    if a.registrar:
        REGISTRO.write_text(f"{sha256(origen)}  dags/{NOMBRE}\n", encoding="utf-8", newline="\n")
        log.info("registrado el sha256 %s en orquestacion/dag.sha256", sha256(origen)[:12])
        return 0
    if a.verificar:
        if not destino.exists():
            log.error("el DAG vivo no existe todavía en airflow-medallon/dags")
            return 1
        igual = sha256(origen) == sha256(destino)
        log.info("DAG del repositorio %s; DAG vivo %s: %s", sha256(origen)[:12], sha256(destino)[:12], "iguales" if igual else "DISTINTOS")
        return 0 if igual else 1
    try:
        h = sincronizar(origen, destino)
    except FileNotFoundError as e:
        log.error("%s", e)
        return 2
    log.info("DAG copiado a airflow-medallon/dags; sha256 %s", h[:12])
    return 0


if __name__ == "__main__":
    sys.exit(main())
