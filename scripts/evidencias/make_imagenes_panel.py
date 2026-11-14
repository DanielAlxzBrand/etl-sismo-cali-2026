"""Tres imágenes de las evidencias del panel, dibujadas con matplotlib desde salidas registradas (no son capturas de pantalla).

Uso:  python scripts/evidencias/make_imagenes_panel.py
Lee `docs/evidencias/panel/EV-055_mediciones_panel.csv` (latencias), `docs/validacion/cobertura_pruebas.csv` (cobertura) y el registro de componentes;
escribe EV-058 (latencias por ruta y almacén), EV-059 (cobertura de las pruebas por módulo del panel) y EV-060 (componentes por página y tipo).
"""
import csv
import sys
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.panel import registro  # noqa: E402

CARPETA = ROOT / "docs" / "evidencias" / "panel"
PIE = "Imagen generada a partir de la salida registrada; no es una captura de pantalla"
AZUL, NARANJA, GRIS = "#0072B2", "#D55E00", "#595959"


def _filas(ruta):
    with open(ruta, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def latencias():
    filas = [f for f in _filas(CARPETA / "EV-055_mediciones_panel.csv") if f["tipo"] == "ruta"]
    rutas = list(dict.fromkeys(f["elemento"] for f in filas))
    med = {a: [float(next(f["mediana_ms"] for f in filas if f["elemento"] == r and f["almacen"] == a)) for r in rutas] for a in ("sqlite", "mysql")}
    fig, ax = plt.subplots(figsize=(10.5, 5.6))
    y = range(len(rutas))
    ax.barh([i + 0.2 for i in y], med["sqlite"], height=0.4, label="SQLite", color=AZUL)
    ax.barh([i - 0.2 for i in y], med["mysql"], height=0.4, label="MySQL", color=NARANJA)
    ax.set_yticks(list(y))
    ax.set_yticklabels([r if len(r) < 48 else r[:45] + "…" for r in rutas], fontsize=7.5)
    ax.invert_yaxis()
    ax.set_xlabel("mediana de la latencia del cliente del panel (ms)")
    ax.set_title("Latencia del cliente del panel por ruta y almacén (mediciones locales de una máquina)", fontsize=10.5, loc="left")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.005, PIE, fontsize=7, color=GRIS)
    fig.savefig(CARPETA / "EV-058_latencias_cliente.png", dpi=150, bbox_inches="tight", metadata={"Software": None})
    plt.close(fig)


def cobertura():
    filas = sorted((f for f in _filas(ROOT / "docs" / "validacion" / "cobertura_pruebas.csv") if "panel" in f["modulo"]), key=lambda f: float(f["cobertura_pct"]))
    valores = [float(f["cobertura_pct"]) for f in filas]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh([f["modulo"] for f in filas], valores, color=[NARANJA if v < 70 else AZUL for v in valores])
    for i, v in enumerate(valores):
        ax.text(v + 1, i, f"{v:.0f} %".replace(".", ","), va="center", fontsize=7.5)
    ax.set_xlim(0, 110)
    ax.set_xticks(range(0, 101, 20))
    ax.set_xlabel("cobertura de líneas (%)")
    ax.set_title("Cobertura de líneas de las pruebas por módulo del panel y su lanzador (naranja: menos de 70 %)", fontsize=10, loc="left")
    ax.tick_params(axis="y", labelsize=7.5)
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.005, PIE, fontsize=7, color=GRIS)
    fig.savefig(CARPETA / "EV-059_cobertura_panel.png", dpi=150, bbox_inches="tight", metadata={"Software": None})
    plt.close(fig)


def trazabilidad():
    tipos = ["metrica", "grafico", "tabla", "texto", "aviso", "descarga"]
    cuenta = Counter((c.pagina, c.tipo) for c in registro.COMPONENTES)
    fig, ax = plt.subplots(figsize=(10, 5.2))
    izq = [0] * len(registro.PAGINAS)
    colores = [AZUL, NARANJA, "#009E73", GRIS, "#CC79A7", "#56B4E9"]
    for t, c in zip(tipos, colores):
        v = [cuenta[(p.id, t)] for p in registro.PAGINAS]
        ax.barh([p.titulo for p in registro.PAGINAS], v, left=izq, label=t, color=c, edgecolor="white")
        izq = [a + b for a, b in zip(izq, v)]
    ax.invert_yaxis()
    ax.set_xlabel("componentes registrados (cada uno con su ruta de la API y su campo de salida)")
    ax.set_title("Trazabilidad de la interfaz: componentes por página y tipo", fontsize=10.5, loc="left")
    ax.legend(frameon=False, ncol=6, loc="lower center", bbox_to_anchor=(0.5, -0.28), fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.005, PIE, fontsize=7, color=GRIS)
    fig.savefig(CARPETA / "EV-060_trazabilidad_componentes.png", dpi=150, bbox_inches="tight", metadata={"Software": None})
    plt.close(fig)


def main():
    latencias()
    cobertura()
    trazabilidad()
    print("imágenes escritas: 3")
    return 0


if __name__ == "__main__":
    sys.exit(main())
