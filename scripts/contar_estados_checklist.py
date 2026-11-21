"""Cuenta los ítems del checklist por estado y escribe (o comprueba) la línea de conteo de `estado_checklist.md`.

Por qué existe: el conteo lo escribíamos a mano y se desactualizó (decía 8 con matiz y 17 Cumple cuando la tabla tenía 9 y 16). Ahora la línea la
produce este script leyendo la columna «estado vigente» de la tabla de los 30 ítems, y ya nadie la escribe a mano.

Uso, desde la raíz del repositorio:
    python scripts/contar_estados_checklist.py              # imprime el conteo
    python scripts/contar_estados_checklist.py --verificar  # falla si la línea del documento no coincide con la tabla
    python scripts/contar_estados_checklist.py --escribir   # reescribe la línea del documento

No modifica nada más que esa línea; no lee `data/`.
"""
import argparse
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCUMENTO = ROOT / "docs" / "checklist" / "estado_checklist.md"
# Todos los estados, en el orden en que mostramos el conteo.
ESTADOS = ["Cumple", "Cumple con matiz", "En curso", "Pendiente (hecho externo)", "No iniciado", "N/A justificado", "No cumple"]
FILA_ITEM = re.compile(r"^\| (\d\.\d) \| «.*?» \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \| .*\|$", re.M)
LINEA_CONTEO = re.compile(r"^Conteo por estado vigente: .*$", re.M)


def estados_por_item(texto):
    """{id: estado vigente} de la tabla de los 30 ítems (sexta columna)."""
    return {fila[0]: fila[4].strip() for fila in FILA_ITEM.findall(texto)}


def contar(texto):
    """Cuántos ítems hay en cada estado, solo con los estados que aparecen."""
    cuenta = Counter(estados_por_item(texto).values())
    return {e: cuenta[e] for e in ESTADOS if cuenta[e]} | {e: n for e, n in cuenta.items() if e not in ESTADOS}


def linea_de_conteo(texto):
    """La línea que debe llevar el documento, calculada desde su tabla."""
    partes = ", ".join(f"{estado}: {n}" for estado, n in contar(texto).items())
    return f"Conteo por estado vigente: {partes}."


def revisar(texto):
    """Lista de errores: la línea del documento falta o no coincide con lo calculado."""
    esperada = linea_de_conteo(texto)
    encontradas = LINEA_CONTEO.findall(texto)
    if len(encontradas) != 1:
        return [f"debe haber exactamente una línea «Conteo por estado vigente» y hay {len(encontradas)}"]
    return [] if encontradas[0] == esperada else [f"la línea dice «{encontradas[0]}» y la tabla da «{esperada}»"]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    modo = ap.add_mutually_exclusive_group()
    modo.add_argument("--verificar", action="store_true", help="falla si la línea del documento no coincide con la tabla")
    modo.add_argument("--escribir", action="store_true", help="reescribe la línea del documento")
    ap.add_argument("--documento", type=Path, default=DOCUMENTO, help="documento a leer (por defecto, el del repositorio)")
    args = ap.parse_args(argv)
    texto = args.documento.read_text(encoding="utf-8")
    if args.escribir:
        nuevo = LINEA_CONTEO.sub(lambda _m: linea_de_conteo(texto), texto, count=1)
        args.documento.write_text(nuevo, encoding="utf-8", newline="\n")
        print(linea_de_conteo(texto))
        return 0
    if args.verificar:
        errores = revisar(texto)
        for e in errores:
            print(f"ERROR: {e}")
        print("OK" if not errores else "FALLA")
        return 1 if errores else 0
    print(linea_de_conteo(texto))
    print(f"ítems leídos: {len(estados_por_item(texto))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
