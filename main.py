"""Puerta de entrada del ETL: python main.py --stage extract|transform|gold|all."""
import argparse
import time

from src.extract.extract_api import extract_edificaciones, extract_poligonos
from src.extract.extract_excel import extract_estrato
from src.load.load_database import load_to_sqlite
from src.logger import get_logger
from src.transform.build_gold import run_gold
from src.transform.integrate import run_transform

log = get_logger("main")


def run_extract(refresh):
    t0 = time.perf_counter()
    log.info("Inicio etapa extract")
    extract_edificaciones(refresh)
    extract_estrato(refresh)
    extract_poligonos(refresh)
    log.info("Fin etapa extract (%.2f s)", time.perf_counter() - t0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=["extract", "transform", "gold", "all"])
    ap.add_argument("--refresh", action="store_true", help="crea un snapshot nuevo en Bronze")
    a = ap.parse_args()
    if a.stage in ("extract", "all"):
        run_extract(a.refresh)
    if a.stage in ("transform", "all"):
        run_transform()
    if a.stage in ("gold", "all"):
        run_gold()
        load_to_sqlite()


if __name__ == "__main__":
    main()
