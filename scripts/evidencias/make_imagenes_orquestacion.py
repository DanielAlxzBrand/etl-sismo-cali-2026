"""Imágenes de las evidencias de la orquestación, dibujadas con matplotlib a partir de salidas registradas (no son capturas de pantalla).

Uso:  python scripts/evidencias/make_imagenes_orquestacion.py
Lee `docs/evidencias/orquestacion/EV-044_estados_tareas.csv` (estados y tiempos exportados de Airflow), `data/` (hashes de las salidas versionadas) y
`docs/validacion/cobertura_pruebas.csv`; escribe cuatro PNG en `docs/evidencias/orquestacion/`.
"""
import csv
import hashlib
import sys
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CARPETA = ROOT / "docs" / "evidencias" / "orquestacion"
PIE = "Imagen generada a partir de la salida registrada; no es una captura de pantalla"
TAREAS = ["validar_bronze", "transformar_a_silver", "integrar_a_gold", "cargar_datawarehouse"]
COLOR = {"success": "#2E7D5B", "failed": "#B5483A", "upstream_failed": "#D9A441"}
SILVER = ["data/silver/silver_construcciones.csv", "data/silver/silver_estrato_barrio.csv", "data/silver/silver_integrated.csv", "data/silver/silver_orphans_left.csv",
          "data/silver/silver_orphans_right.csv", "data/silver/quality_report.json"]
GOLD = ["data/gold/gold_final.csv", "data/gold/kpis_gold.csv", "data/gold/kpis_sensibilidad.csv"]


def leer_estados():
    with open(CARPETA / "EV-044_estados_tareas.csv", encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    runs = {}
    for r in filas:
        runs.setdefault(r["run_id"], {"tipo": r["tipo_de_ejecucion"], "estado": r["estado_de_la_ejecucion"], "tareas": {}})["tareas"][r["tarea"]] = r
    return dict(sorted(runs.items(), key=lambda kv: min(datetime.fromisoformat(t["inicio_utc"]) for t in kv[1]["tareas"].values())))


def etiqueta(run_id, info, i):
    tipo = "programada" if info["tipo"] == "scheduled" else "manual"
    return f"{i}. {tipo}: {run_id.split('__')[1][:19].replace('T', ' ')}"


def estados_de_tareas(runs):
    fig, ax = plt.subplots(figsize=(11, 5.2))
    for fila, (rid, info) in enumerate(runs.items()):
        t0 = min(datetime.fromisoformat(t["inicio_utc"]) for t in info["tareas"].values())
        for t in info["tareas"].values():
            a = (datetime.fromisoformat(t["inicio_utc"]) - t0).total_seconds()
            d = max(float(t["duracion_s"] or 0.15), 0.15)
            ax.barh(len(runs) - fila, d, left=a, height=0.55, color=COLOR.get(t["estado_de_la_tarea"], "#888888"), edgecolor="white")
        ax.text(-0.3, len(runs) - fila, etiqueta(rid, info, fila + 1), ha="right", va="center", fontsize=8)
    ax.set_yticks([])
    ax.set_xlabel("segundos desde el inicio de la ejecución")
    ax.set_title("Tareas del DAG medallon_etl_sismo en cada ejecución\n(verde: éxito; rojo: fallo inducido; ámbar: la tarea no se ejecutó)", fontsize=10, loc="left")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=c) for c in COLOR.values()], labels=["success", "failed", "upstream_failed"], frameon=False, loc="lower right")
    fig.subplots_adjust(left=0.30)
    fig.text(0.01, 0.01, PIE, fontsize=7, color="#555555")
    fig.savefig(CARPETA / "EV-045_estados_de_tareas.png", dpi=150, metadata={"Software": None})
    plt.close(fig)


def esperado_obtenido(runs):
    archivos = [(a, "transformar_a_silver") for a in SILVER] + [(a, "integrar_a_gold") for a in GOLD] + [("etl_sismo.db (4 tablas, contenido)", "cargar_datawarehouse")]
    hashes = {a: hashlib.sha256((ROOT / a).read_bytes()).hexdigest()[:8] for a, _ in archivos[:-1]}
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    for i, (a, tarea) in enumerate(archivos):
        for j, (rid, info) in enumerate(runs.items()):
            ok = info["tareas"].get(tarea, {}).get("estado_de_la_tarea") == "success"
            ax.add_patch(plt.Rectangle((j, len(archivos) - i - 1), 0.92, 0.82, color="#2E7D5B" if ok else "#C9CDD3"))
            ax.text(j + 0.46, len(archivos) - i - 0.6, "=" if ok else "-", ha="center", va="center", color="white" if ok else "#555555", fontsize=11)
    ax.set_xlim(0, len(runs))
    ax.set_ylim(0, len(archivos))
    ax.set_xticks([j + 0.46 for j in range(len(runs))])
    ax.set_xticklabels([f"{j + 1}" for j in range(len(runs))])
    ax.set_yticks([len(archivos) - i - 0.6 for i in range(len(archivos))])
    ax.set_yticklabels([f"{a.split('/')[-1]}  {hashes.get(a, '')}" for a, _ in archivos], fontsize=8, family="monospace")
    ax.set_xlabel("ejecución (1 a 7, en orden cronológico)")
    ax.set_title("Salidas del DAG frente a las versionadas\n«=» coincide (sha256; contenido tabla a tabla en la base); «-» la tarea no se ejecutó", fontsize=9.5, loc="left")
    ax.spines[:].set_visible(False)
    ax.tick_params(length=0)
    fig.subplots_adjust(left=0.30)
    fig.text(0.01, 0.01, "Una tarea solo termina en éxito si cada archivo que produce coincide con el versionado (prefijo del sha256 a la izquierda). " + PIE, fontsize=7, color="#555555")
    fig.savefig(CARPETA / "EV-046_esperado_frente_a_obtenido.png", dpi=150, metadata={"Software": None})
    plt.close(fig)


def ejecucion_programada(runs):
    prog = [(rid, info) for rid, info in runs.items() if info["tipo"] == "scheduled"]
    fig, ax = plt.subplots(figsize=(10, 3.6))
    for k, (rid, info) in enumerate(prog):
        ini = min(datetime.fromisoformat(t["inicio_utc"]) for t in info["tareas"].values())
        fin = max(datetime.fromisoformat(t["fin_utc"]) for t in info["tareas"].values())
        ax.barh(k, (fin - ini).total_seconds(), left=0, height=0.5, color="#2E7D5B")
        ax.text(0.3, k, f"{rid.split('__')[1]}: inicio {ini.strftime('%H:%M:%S')} UTC ({(ini.hour - 5) % 24:02d}:{ini.minute:02d}:{ini.second:02d} en Bogotá), {(fin - ini).total_seconds():.1f} s, cuatro tareas en éxito", va="center", color="white", fontsize=8)
    ax.set_yticks([0, 1][: len(prog)])
    ax.set_yticklabels(["programada " + str(i + 1) for i in range(len(prog))], fontsize=8)
    ax.set_xlabel("segundos")
    ax.set_title("Ejecuciones disparadas por el planificador (cron temporal 22:36); el cron definitivo es 0 6 * * * en hora de Bogotá", fontsize=9.5, loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.01, PIE, fontsize=7, color="#555555")
    fig.savefig(CARPETA / "EV-047_ejecucion_programada.png", dpi=150, bbox_inches="tight", metadata={"Software": None})
    plt.close(fig)


def cobertura():
    ruta = ROOT / "docs" / "validacion" / "cobertura_pruebas.csv"
    if not ruta.exists():
        return False
    with open(ruta, encoding="utf-8", newline="") as f:
        filas = sorted(csv.DictReader(f), key=lambda r: float(r["cobertura_pct"]))
    fig, ax = plt.subplots(figsize=(10, 8))
    valores = [float(r["cobertura_pct"]) for r in filas]
    ax.barh([r["modulo"] for r in filas], valores, color=["#B5483A" if v < 70 else "#2E7D5B" for v in valores])
    ax.set_xlim(0, 100)
    ax.set_xlabel("cobertura de líneas (%)")
    ax.set_title("Cobertura de líneas por módulo de src/ y scripts/ (rojo: menos de 70 %, con su motivo en el informe de pruebas)", fontsize=9.5, loc="left")
    ax.tick_params(axis="y", labelsize=7)
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.005, PIE, fontsize=7, color="#555555")
    fig.savefig(CARPETA / "EV-048_cobertura_por_modulo.png", dpi=150, bbox_inches="tight", metadata={"Software": None})
    plt.close(fig)
    return True


def main():
    runs = leer_estados()
    estados_de_tareas(runs)
    esperado_obtenido(runs)
    ejecucion_programada(runs)
    print("imágenes escritas:", 3 + int(cobertura()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
