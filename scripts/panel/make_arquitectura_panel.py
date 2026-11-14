"""Diagrama de la arquitectura del panel, dibujado con matplotlib (no es una captura de pantalla).

Uso:  python scripts/panel/make_arquitectura_panel.py
Escribe `docs/panel/img/arquitectura_panel.png`: navegador, Streamlit, cliente HTTP de solo lectura, API, repositorio y almacenamiento (SQLite o MySQL).
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SALIDA = ROOT / "docs" / "panel" / "img" / "arquitectura_panel.png"
TINTA, GRIS, VERDE, AZUL, AMBAR = "#1F2933", "#E8EBEF", "#DCEBE3", "#DCE6F2", "#F4E6C8"


def caja(ax, x, y, w, h, titulo, detalle="", fondo=GRIS):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12", facecolor=fondo, edgecolor="#9AA5B1", linewidth=1))
    ax.text(x + w / 2, y + h - 0.35, titulo, ha="center", va="top", fontsize=9.5, fontweight="bold", color=TINTA)
    if detalle:
        ax.text(x + w / 2, y + h - 0.95, detalle, ha="center", va="top", fontsize=7.8, color=TINTA, linespacing=1.35)


def flecha(ax, a, b, texto="", color="#52606D", dy=0.18):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=12, color=color, linewidth=1.3))
    if texto:
        ax.text((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + dy, texto, ha="center", va="bottom", fontsize=7.6, color=color)


def main():
    fig, ax = plt.subplots(figsize=(13, 6.4))
    ax.set_xlim(0, 26)
    ax.set_ylim(0, 12.5)
    ax.axis("off")
    ax.text(0.2, 12.2, "Arquitectura del panel: una interfaz de solo lectura que habla únicamente con la API", fontsize=11, fontweight="bold", color=TINTA, va="top")
    ax.add_patch(FancyBboxPatch((0.2, 0.4), 25.6, 10.6, boxstyle="round,pad=0.02,rounding_size=0.15", facecolor="#F7F8FA", edgecolor="#C5CBD3", linewidth=1))
    ax.text(0.5, 10.75, "Una sola máquina (127.0.0.1): nada se publica fuera del equipo", fontsize=8.5, color="#52606D", va="top")
    caja(ax, 0.6, 3.6, 3.6, 5.2, "Navegador", "persona usuaria\n\nlee páginas,\nfiltra y descarga\nel CSV de lo\nque se muestra", AZUL)
    caja(ax, 5.4, 3.6, 5.0, 5.2, "Streamlit (src/panel)", "app.py: navegación\nocho páginas: render(api)\ncomponentes y redacción\nregistro único de\ncomponentes\nsin HTML propio ni\nrecursos externos", VERDE)
    caja(ax, 11.6, 3.6, 3.8, 5.2, "Cliente HTTP", "cliente_api.py\nsolo GET, caché con\ntiempo de vida,\nerrores tipados en\nespañol, un reintento\nde conexión", VERDE)
    caja(ax, 16.6, 3.6, 4.0, 5.2, "API (src/api)", "11 rutas GET\nerrores JSON uniformes\nsin escritura\n\nrepositorio con\ninterfaz común", AMBAR)
    caja(ax, 21.8, 6.4, 3.7, 2.4, "SQLite", "etl_sismo.db\nmodo solo lectura", GRIS)
    caja(ax, 21.8, 3.6, 3.7, 2.4, "MySQL", "última corrida,\nconexión de solo\nlectura", GRIS)
    flecha(ax, (4.2, 6.2), (5.4, 6.2), "HTTP local")
    flecha(ax, (10.4, 6.2), (11.6, 6.2), "consulta")
    flecha(ax, (15.4, 6.2), (16.6, 6.2), "GET")
    flecha(ax, (20.6, 7.6), (21.8, 7.6), "por defecto")
    flecha(ax, (20.6, 4.8), (21.8, 4.8), "api.almacenamiento")
    ax.text(13.0, 2.3, "El panel no abre bases ni archivos de datos, no lee .env ni credenciales y no importa las capas del pipeline:\nuna prueba de análisis estático lo comprueba en cada ejecución.", ha="center", va="top", fontsize=8.5, color=TINTA)
    ax.text(0.3, 0.05, "Diagrama generado con matplotlib; no es una captura de pantalla", fontsize=7, color="#52606D")
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(SALIDA, dpi=150, bbox_inches="tight", metadata={"Software": None})
    print("escrito", SALIDA.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
