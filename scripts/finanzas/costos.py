"""Costo por ejecución del pipeline con los precios como PARÁMETROS (config/parametros_costos.yaml); no contiene ninguna cifra monetaria.

Uso:  python scripts/finanzas/costos.py [--parametros config/parametros_costos.yaml] [--recursos docs/finanzas/recursos_medidos.csv]
Siempre muestra el consumo medido (tiempo de ejecución, memoria, almacenamiento). Si falta algún parámetro necesario, escribe «costo no calculado: faltan parámetros: …» y no inventa ninguno;
si están todos, calcula con las fórmulas de docs/finanzas/estructura_costos.md. Un parámetro con valor pero sin fuente o sin fecha se rechaza (código de salida 2).
"""
import argparse
import csv
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
PARAMETROS = ROOT / "config" / "parametros_costos.yaml"
RECURSOS = ROOT / "docs" / "finanzas" / "recursos_medidos.csv"

# Parámetros que necesita cada componente del costo por ejecución.
NECESARIOS = {
    "computo": ("precio_hora_computo",),
    "almacenamiento": ("precio_gb_mes_almacenamiento", "ejecuciones_por_mes"),
    "equipo": ("tarifa_hora_equipo", "horas_equipo_por_ejecucion"),
}
# Magnitudes medidas (docs/finanzas/recursos_medidos.csv) que usan las fórmulas.
MEDIDAS = {"tiempo_main_s": "tiempo_main_todas_las_etapas", "almacenamiento_mb": "tamano_data_mb"}


class ParametroNoValido(ValueError):
    """Un parámetro tiene valor sin fuente o sin fecha, o no es un número."""


def cargar_parametros(ruta=PARAMETROS):
    """Diccionario {nombre: {valor, unidad, descripcion, fuente, fecha}} del archivo YAML."""
    datos = yaml.safe_load(Path(ruta).read_text(encoding="utf-8"))
    return datos


def revisar_parametros(parametros):
    """Errores de los parámetros: todo valor no nulo necesita fuente y fecha, y los valores numéricos deben serlo."""
    errores = []
    for nombre, p in parametros.items():
        if p.get("valor") is None:
            continue
        if not p.get("fuente") or not p.get("fecha"):
            errores.append(f"{nombre}: tiene valor pero le falta la fuente o la fecha")
        if nombre != "moneda" and (isinstance(p["valor"], bool) or not isinstance(p["valor"], (int, float))):
            errores.append(f"{nombre}: el valor debe ser un número")
    return errores


def leer_recursos(ruta=RECURSOS):
    """{magnitud: valor} del CSV de recursos medidos (magnitud, valor, unidad, origen, fecha); vacío si no existe."""
    if not Path(ruta).is_file():
        return {}
    with open(ruta, encoding="utf-8", newline="") as f:
        return {fila["magnitud"]: fila["valor"] for fila in csv.DictReader(f)}


def faltantes(parametros, componentes=tuple(NECESARIOS)):
    """Nombres de los parámetros vacíos que necesitan los componentes pedidos (sin repetir y en orden)."""
    vistos = []
    for c in componentes:
        for n in NECESARIOS[c]:
            if parametros.get(n, {}).get("valor") is None and n not in vistos:
                vistos.append(n)
    return vistos


def costo_por_ejecucion(parametros, tiempo_s, almacenamiento_mb):
    """Costo por ejecución = tiempo (h) × precio por hora de cómputo + almacenamiento (GB) × precio por GB-mes ÷ ejecuciones por mes + horas de equipo × tarifa por hora.

    Devuelve un diccionario con cada componente y el total, o lanza ParametroNoValido si falta algún parámetro (no calcula con valores supuestos).
    """
    falta = faltantes(parametros)
    if falta:
        raise ParametroNoValido("faltan parámetros: " + ", ".join(falta))
    v = {n: p["valor"] for n, p in parametros.items()}
    if v["ejecuciones_por_mes"] <= 0:
        raise ParametroNoValido("ejecuciones_por_mes debe ser mayor que cero")
    computo = (tiempo_s / 3600) * v["precio_hora_computo"]
    almacenamiento = (almacenamiento_mb / 1024) * v["precio_gb_mes_almacenamiento"] / v["ejecuciones_por_mes"]
    equipo = v["horas_equipo_por_ejecucion"] * v["tarifa_hora_equipo"]
    return {"computo": computo, "almacenamiento": almacenamiento, "equipo": equipo, "total": computo + almacenamiento + equipo}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--parametros", default=str(PARAMETROS))
    ap.add_argument("--recursos", default=str(RECURSOS))
    a = ap.parse_args(argv)
    parametros = cargar_parametros(a.parametros)
    errores = revisar_parametros(parametros)
    if errores:
        print("error: " + "; ".join(errores), file=sys.stderr)
        return 2
    recursos = leer_recursos(a.recursos)
    print("Consumo medido (mediciones locales de una máquina):")
    if not recursos:
        print("  no hay mediciones: ejecute scripts/finanzas/medir_recursos.py")
    for magnitud, valor in recursos.items():
        print(f"  {magnitud}: {valor}")
    falta = faltantes(parametros)
    if falta:
        print("costo no calculado: faltan parámetros: " + ", ".join(falta))
        return 0
    try:
        tiempo, mb = float(recursos[MEDIDAS["tiempo_main_s"]]), float(recursos[MEDIDAS["almacenamiento_mb"]])
    except (KeyError, ValueError):
        print("costo no calculado: faltan mediciones de tiempo o de almacenamiento")
        return 0
    c = costo_por_ejecucion(parametros, tiempo, mb)
    moneda = parametros["moneda"]["valor"] or "(moneda no indicada)"
    print(f"Costo por ejecución ({moneda}): cómputo {c['computo']:.4f}; almacenamiento {c['almacenamiento']:.4f}; equipo {c['equipo']:.4f}; total {c['total']:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
