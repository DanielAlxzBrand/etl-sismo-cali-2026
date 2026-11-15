"""Precarga el registro de fricciones SOLO con los hallazgos de la evaluación heurística interna (fuente = heuristica, decisión = pendiente).

Uso:  python scripts/usuarios/precargar_friccion.py [--base docs/usuarios]
Lee la tabla de hallazgos F-nn de `evaluacion_heuristica.md` y escribe `registro_de_friccion.csv` y `registro_de_friccion.md`. No agrega filas de observación ni de entrevista: esas las anota el
equipo con sesiones reales. Vuelve a generar los dos archivos a partir de la evaluación, así que los cambios de decisión se anotan en el CSV DESPUÉS de generarlo y el script rechaza
sobrescribir un registro cuyas decisiones ya no estén todas «pendiente» (para no borrar el trabajo del equipo), salvo con --forzar.
"""
import argparse
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
USUARIOS = ROOT / "docs" / "usuarios"
CAMPOS = ("id", "fuente", "participante", "pagina", "descripcion", "severidad", "frecuencia", "decision", "razon", "cambio", "antes", "despues", "verificacion", "estado")
FUENTES = ("heuristica", "observacion", "grabacion", "entrevista")
DECISIONES = ("pendiente", "corregir", "aplazar", "descartar")


def leer_hallazgos(texto):
    """[{id, pagina, heuristica, descripcion, capturas, severidad, recomendacion}] de la tabla de hallazgos de la evaluación heurística."""
    hallazgos = []
    for linea in texto.splitlines():
        if not re.match(r"^\| F-\d+ \|", linea):
            continue
        c = [x.strip() for x in linea[2:-2].split(" | ")]
        if len(c) != 7:
            raise ValueError(f"fila de hallazgo con {len(c)} celdas y no 7: {c[0]}")
        hallazgos.append({"id": c[0], "pagina": c[1], "heuristica": c[2], "descripcion": c[3], "capturas": re.findall(r"`([^`]+\.png)`", c[4]), "severidad": int(c[5]), "recomendacion": c[6]})
    return hallazgos


def filas_del_registro(hallazgos):
    """Filas del registro de fricciones para esos hallazgos: fuente «heuristica», sin participante y con la decisión «pendiente»."""
    return [{"id": h["id"], "fuente": "heuristica", "participante": "", "pagina": h["pagina"], "descripcion": h["descripcion"], "severidad": h["severidad"],
             "frecuencia": "no medida (sin personas)", "decision": "pendiente", "razon": "", "cambio": "", "antes": "; ".join(h["capturas"]), "despues": "", "verificacion": "", "estado": "abierta"} for h in hallazgos]


def redactar(filas, hallazgos):
    por_id = {h["id"]: h for h in hallazgos}
    orden = sorted(filas, key=lambda f: (-int(f["severidad"]), f["id"]))
    L = ["# Registro de fricciones", "",
         "**Ítem del checklist:** 6.3 (registro con severidad, fuente con consentimiento, priorización y decisión por fricción, y trazabilidad a cambios del panel) · **Estado:** precargado solo con los hallazgos de la [evaluación heurística interna](evaluacion_heuristica.md); **sin fricciones de observación ni de entrevista, porque no hay sesiones reales**.", "",
         "> Este archivo se genera con `scripts/usuarios/precargar_friccion.py` y su CSV es [registro_de_friccion.csv](registro_de_friccion.csv). Una fricción de fuente `heuristica` es una iteración técnica interna y **no** una validación con personas usuarias.", "",
         "## Cómo se usa", "",
         "1. Cada fricción tiene `fuente` (`heuristica`, `observacion`, `grabacion` o `entrevista`), el participante (`P01`, `P02`… solo si la fuente es una sesión con su consentimiento; vacío en las heurísticas), la página, la severidad de 0 a 4, la frecuencia (cuántas personas la tuvieron, «no medida» si aún no hay sesiones) y su estado.",
         "2. La `decision` empieza en `pendiente` y pasa a `corregir`, `aplazar` o `descartar` **con su razón** en la columna `razon`; no se decide sin escribir por qué.",
         "3. Cuando se corrige, `cambio` lleva el commit, `antes` y `despues` las capturas y `verificacion` la prueba o la medición que lo comprueba; el detalle va en [trazabilidad_de_cambios.md](trazabilidad_de_cambios.md).",
         "4. Las fricciones de sesiones reales se agregan con la plantilla [`sesiones_reales/plantilla_friccion.csv`](sesiones_reales/plantilla_friccion.csv) y solo con el consentimiento de la persona.", "",
         "## Fricciones precargadas (todas de la evaluación heurística; decisión pendiente)", "",
         "El orden es por severidad y es solo una **propuesta de prioridad**, no una decisión.", "",
         "| Id | Fuente | Página | Severidad | Resumen | Decisión | Estado |", "|---|---|---|---|---|---|---|"]
    for f in orden:
        resumen = re.split(r"(?<=\.)\s", f["descripcion"], maxsplit=1)[0]
        L.append(f"| {f['id']} | {f['fuente']} | {f['pagina']} | {f['severidad']} | {resumen[:170]}{'…' if len(resumen) > 170 else ''} | {f['decision']} | {f['estado']} |")
    L += ["", "## Fricciones de sesiones reales", "", "Ninguna todavía: no se han hecho sesiones con personas usuarias.", "",
          "## Alcance y límites",
          "- **Qué afirmamos:** las fricciones listadas salen de la evaluación heurística, cada una con su captura, y ninguna se ha corregido.",
          "- **Con qué evidencia:** [evaluacion_heuristica.md](evaluacion_heuristica.md) y EV-066 a EV-069.",
          "- **Qué NO afirmamos:** que sean las que encontrarían las personas usuarias, que la severidad refleje su frecuencia real ni que alguna decisión esté tomada."]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", default=str(USUARIOS))
    ap.add_argument("--forzar", action="store_true")
    a = ap.parse_args(argv)
    base = Path(a.base)
    hallazgos = leer_hallazgos((base / "evaluacion_heuristica.md").read_text(encoding="utf-8"))
    destino = base / "registro_de_friccion.csv"
    if destino.is_file() and not a.forzar:
        with open(destino, encoding="utf-8", newline="") as f:
            if any(fila["decision"] != "pendiente" or fila["fuente"] != "heuristica" for fila in csv.DictReader(f)):
                print("error: el registro ya tiene decisiones o fricciones de sesiones; no se sobrescribe (use --forzar si es lo que se quiere)", file=sys.stderr)
                return 2
    filas = filas_del_registro(hallazgos)
    with open(destino, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS, lineterminator="\n")
        w.writeheader()
        w.writerows(filas)
    (base / "registro_de_friccion.md").write_text(redactar(filas, hallazgos), encoding="utf-8", newline="\n")
    print(f"registro de fricciones: {len(filas)} fricciones de la evaluación heurística, todas con decisión pendiente")
    return 0


if __name__ == "__main__":
    sys.exit(main())
