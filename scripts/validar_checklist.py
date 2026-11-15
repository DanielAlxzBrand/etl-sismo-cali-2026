"""Comprueba, ítem por ítem, lo que el repositorio dice tener para cada verificación del checklist: requisito, estado, archivos, pruebas, evidencias y comando.

Uso, desde la raíz del repositorio:
    python scripts/validar_checklist.py --item 4.2              # comprueba un ítem y muestra su trazabilidad
    python scripts/validar_checklist.py --item 4.2 --ejecutar   # además corre solo las pruebas de ese ítem con pytest
    python scripts/validar_checklist.py --todos                 # comprueba los 30 ítems y el grupo de guardianes; código 1 si algo falla
    python scripts/validar_checklist.py --listar                # una línea por ítem: estado, tipo y cuántas pruebas y evidencias tiene
    python scripts/validar_checklist.py --escribir              # regenera docs/checklist/trazabilidad.md desde el CSV

Fuente única: `docs/checklist/trazabilidad.csv` (una fila por ítem y una fila `G` con las pruebas y evidencias que vigilan la coherencia del repositorio sin ser de un ítem). La tabla
`docs/checklist/trazabilidad.md` se genera desde ese CSV y no se edita a mano; `tests/test_trazabilidad.py` comprueba que el CSV coincide con `estado_checklist.md` (requisito y estado) y con el
manifiesto de evidencias.
Qué comprueba por ítem: que existan los archivos y las pruebas (el archivo y, si se nombra, la función), que cada evidencia esté en el manifiesto con el ítem correspondiente y que su archivo
tenga el sha256 registrado. Con `--ejecutar` corre las pruebas del ítem: no ejecuta Docker, MySQL ni nada externo.
Qué NO hace: no modifica ningún archivo salvo `trazabilidad.md` con `--escribir`, no marca estados y no sustituye la revisión de los documentos; los ítems con sesiones reales o con hechos externos
muestran qué falta, no lo inventan.
"""
import argparse
import ast
import csv
import hashlib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "docs" / "checklist" / "trazabilidad.csv"
MD = ROOT / "docs" / "checklist" / "trazabilidad.md"
ESTADO = ROOT / "docs" / "checklist" / "estado_checklist.md"
MANIFIESTO = ROOT / "docs" / "evidencias" / "manifiesto.md"
COLUMNAS = ["item", "requisito", "estado", "tipo", "archivos", "pruebas", "evidencias", "comando", "que_no_demuestra"]
TIPOS = ("automática", "automática y manual", "manual", "externa")
GRUPO = "G"


def lista(celda):
    """Elementos de una celda separada por punto y coma."""
    return [x.strip() for x in (celda or "").split(";") if x.strip()]


def leer_csv(ruta=CSV):
    """Filas del CSV de trazabilidad como diccionarios."""
    with open(ruta, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def expandir_evidencias(celda):
    """Números de evidencia de una celda como `EV-028;EV-066..EV-069` (los rangos incluyen sus extremos)."""
    numeros = set()
    for parte in lista(celda):
        m = re.fullmatch(r"EV-(\d+)\.\.EV-(\d+)", parte)
        if m:
            numeros |= set(range(int(m[1]), int(m[2]) + 1))
        elif re.fullmatch(r"EV-\d+", parte):
            numeros.add(int(parte[3:]))
        else:
            raise ValueError(f"evidencia mal escrita: {parte!r}")
    return sorted(numeros)


def comprimir_evidencias(numeros):
    """Inversa de `expandir_evidencias`: agrupa los números consecutivos en rangos."""
    numeros, partes, i = sorted(set(numeros)), [], 0
    while i < len(numeros):
        j = i
        while j + 1 < len(numeros) and numeros[j + 1] == numeros[j] + 1:
            j += 1
        partes += [f"EV-{numeros[k]:03d}" for k in range(i, j + 1)] if j - i < 2 else [f"EV-{numeros[i]:03d}..EV-{numeros[j]:03d}"]
        i = j + 1
    return ";".join(partes)


def filas_del_manifiesto(ruta=MANIFIESTO):
    """{número de evidencia: [filas]} del manifiesto; cada fila trae id, ítems, ruta y sha256."""
    filas = {}
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if linea.startswith("| EV-"):
            c = [x.strip() for x in linea.strip().strip("|").split(" | ")]
            numero = int(re.match(r"EV-(\d+)", c[0]).group(1))
            items = [x for x in re.split(r"[,\s]+", c[1]) if x]
            filas.setdefault(numero, []).append({"id": c[0], "items": items, "ruta": c[-2].strip("` "), "sha256": c[-1].strip("` ")})
    return filas


def estados_del_documento(texto):
    """{ítem: (requisito literal, estado vigente)} de la tabla de los 30 ítems de `estado_checklist.md`."""
    return {f[0]: (f[1], f[5].strip()) for f in re.findall(r"^\| (\d\.\d) \| «(.*?)» \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \| .*\|$", texto, re.M)}


def prueba_existe(nodeid, raiz=ROOT):
    """(existe, motivo) para `tests/archivo.py` o `tests/archivo.py::funcion`: el archivo debe existir y, si se nombra, la función estar definida en él."""
    archivo, _, funcion = nodeid.partition("::")
    ruta = raiz / archivo
    if not ruta.is_file():
        return False, "no existe el archivo"
    if funcion:
        nombres = {n.name for n in ast.walk(ast.parse(ruta.read_text(encoding="utf-8"))) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        if funcion not in nombres:
            return False, f"el archivo no define «{funcion}»"
    return True, ""


def evidencia_ok(fila):
    """True si el archivo registrado existe y su sha256 es el del manifiesto."""
    p = ROOT / fila["ruta"]
    return p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest() == fila["sha256"]


def comprobar_fila(fila, manifiesto=None):
    """Problemas de una fila del CSV (lista vacía si cumple): archivos, pruebas, evidencias y tipo."""
    manifiesto = manifiesto if manifiesto is not None else filas_del_manifiesto()
    item, problemas = fila["item"], []
    if fila["tipo"] not in TIPOS:
        problemas.append(f"tipo {fila['tipo']!r} fuera de {TIPOS}")
    problemas += [f"archivo inexistente: {a}" for a in lista(fila["archivos"]) if not (ROOT / a).exists()]
    for p in lista(fila["pruebas"]):
        ok, motivo = prueba_existe(p)
        if not ok:
            problemas.append(f"prueba {p}: {motivo}")
    for n in expandir_evidencias(fila["evidencias"]):
        filas = manifiesto.get(n)
        if not filas:
            problemas.append(f"EV-{n:03d} no está en el manifiesto")
            continue
        if item != GRUPO and not any(item in f["items"] or f["items"] == ["0"] for f in filas):
            problemas.append(f"EV-{n:03d} no está asociada al ítem {item} en el manifiesto")
        problemas += [f"{f['id']}: el sha256 no coincide con el manifiesto" for f in filas if not evidencia_ok(f)]
    return problemas


def a_markdown(filas):
    """Tabla `trazabilidad.md` generada desde el CSV (no se edita a mano)."""
    cab = ("# Trazabilidad del checklist: ítem → requisito → archivos → pruebas → evidencias → comando\n\n"
           "> **Generado** por `python scripts/validar_checklist.py --escribir` desde [trazabilidad.csv](trazabilidad.csv), que es la única fuente; no se edita a mano. "
           "El estado de cada ítem es el de [estado_checklist.md](estado_checklist.md) y una prueba comprueba que coinciden. Para comprobar un ítem: "
           "`python scripts/validar_checklist.py --item 4.2` (añade `--ejecutar` para correr solo sus pruebas).\n\n"
           "| ítem | requisito | estado | comprobación | pruebas | evidencias | comando | qué NO demuestra |\n|---|---|---|---|---|---|---|---|\n")
    cuerpo = []
    for f in filas:
        n_pruebas = len(lista(f["pruebas"]))
        evs = f["evidencias"].replace(";", "; ") or "—"
        cuerpo.append(f"| {f['item']} | {f['requisito']} | {f['estado']} | {f['tipo']} | {n_pruebas} | {evs} | `{f['comando']}` | {f['que_no_demuestra']} |")
    return cab + "\n".join(cuerpo) + "\n"


def informe_de_item(fila, manifiesto):
    """Texto del informe de `--item` y la lista de problemas."""
    problemas = comprobar_fila(fila, manifiesto)
    nombre = "guardianes de coherencia (no son de un ítem)" if fila["item"] == GRUPO else f"ítem {fila['item']}"
    out = [f"{nombre.capitalize()} · {fila['requisito']}", f"Estado vigente: {fila['estado']} · Comprobación: {fila['tipo']}"]
    out.append(f"Archivos ({len(lista(fila['archivos']))}):")
    out += [f"  [{'ok' if (ROOT / a).exists() else 'FALTA'}] {a}" for a in lista(fila["archivos"])] or ["  (ninguno: no existe material en el repositorio)"]
    out.append(f"Pruebas ({len(lista(fila['pruebas']))}):")
    out += [f"  [{'ok' if prueba_existe(p)[0] else 'FALTA'}] {p}" for p in lista(fila["pruebas"])] or ["  (ninguna)"]
    nums = expandir_evidencias(fila["evidencias"])
    out.append(f"Evidencias ({len(nums)} números, {sum(len(manifiesto.get(n, [])) for n in nums)} filas del manifiesto):")
    for n in nums:
        filas = manifiesto.get(n, [])
        ok = bool(filas) and all(evidencia_ok(f) for f in filas)
        out.append(f"  [{'ok' if ok else 'FALTA'}] EV-{n:03d} ({len(filas)} fila(s), sha256 {'coincide' if ok else 'NO coincide'})")
    if not nums:
        out.append("  (ninguna)")
    out += [f"Comando: {fila['comando']}", f"Qué NO demuestra: {fila['que_no_demuestra']}", f"Resultado: {'OK' if not problemas else 'FALLA'}"]
    out += [f"  - {p}" for p in problemas]
    return "\n".join(out), problemas


def main(argv=None):
    """Punto de entrada de la línea de comandos."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    modo = ap.add_mutually_exclusive_group(required=True)
    modo.add_argument("--item", help="id del ítem (por ejemplo 4.2) o G para el grupo de guardianes")
    modo.add_argument("--todos", action="store_true", help="comprueba todas las filas del CSV")
    modo.add_argument("--listar", action="store_true", help="una línea por ítem")
    modo.add_argument("--escribir", action="store_true", help="regenera trazabilidad.md desde el CSV")
    ap.add_argument("--ejecutar", action="store_true", help="con --item: corre con pytest solo las pruebas del ítem")
    args = ap.parse_args(argv)
    filas = leer_csv()
    manifiesto = filas_del_manifiesto()
    if args.escribir:
        MD.write_text(a_markdown(filas), encoding="utf-8", newline="\n")
        print(f"escrito {MD.relative_to(ROOT).as_posix()} con {len(filas)} filas")
        return 0
    if args.listar:
        for f in filas:
            print(f"{f['item']:<4} {f['estado']:<27} {f['tipo']:<20} pruebas {len(lista(f['pruebas'])):>2}  evidencias {len(expandir_evidencias(f['evidencias'])):>2}")
        return 0
    if args.todos:
        malas = 0
        for f in filas:
            problemas = comprobar_fila(f, manifiesto)
            malas += bool(problemas)
            print(f"{f['item']:<4} {'OK' if not problemas else 'FALLA'}" + "".join(f"\n     - {p}" for p in problemas))
        print(f"{len(filas) - malas} de {len(filas)} filas sin problemas")
        return 1 if malas else 0
    fila = next((f for f in filas if f["item"] == args.item), None)
    if fila is None:
        print(f"no hay una fila para «{args.item}»; use --listar")
        return 2
    texto, problemas = informe_de_item(fila, manifiesto)
    print(texto)
    if args.ejecutar:
        objetivos = lista(fila["pruebas"])
        if not objetivos:
            print("Ejecución: este ítem no tiene pruebas que correr")
            return 1 if problemas else 0
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *objetivos], cwd=ROOT)
        return 1 if problemas or r.returncode else 0
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
