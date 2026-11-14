"""Diagrama de la arquitectura de la orquestación, dibujado con matplotlib (no es una captura de pantalla).

Uso:  python scripts/orquestacion/make_arquitectura.py
Escribe `docs/orquestacion/img/arquitectura_orquestacion.png`. Los nombres de contenedores, rutas y puertos salen del compose, del DAG y de las evidencias EV-038 y EV-040.
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SALIDA = ROOT / "docs" / "orquestacion" / "img" / "arquitectura_orquestacion.png"
TINTA, GRIS, VERDE, AZUL, AMBAR = "#1F2933", "#E8EBEF", "#DCEBE3", "#DCE6F2", "#F4E6C8"


def caja(ax, x, y, w, h, texto, fondo=GRIS, borde="#9AA5B1", tam=8.5, negrita=False, ancla="center"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12", facecolor=fondo, edgecolor=borde, linewidth=1))
    if ancla == "center":
        ax.text(x + w / 2, y + h / 2, texto, ha="center", va="center", fontsize=tam, color=TINTA, fontweight="bold" if negrita else "normal")
    else:
        ax.text(x + 0.15, y + h - 0.15, texto, ha="left", va="top", fontsize=tam, color=TINTA, fontweight="bold" if negrita else "normal")


def flecha(ax, a, b, texto="", dy=0.0, estilo="-|>", color="#52606D"):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle=estilo, mutation_scale=11, color=color, linewidth=1.2))
    if texto:
        ax.text((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + dy, texto, ha="center", va="bottom", fontsize=7.5, color=color)


def main():
    fig, ax = plt.subplots(figsize=(12, 7.6))
    ax.set_xlim(0, 24)
    ax.set_ylim(0, 15.2)
    ax.axis("off")
    ax.text(0.2, 14.8, "Arquitectura de la orquestación: Airflow 3.3.2 en Docker Desktop (WSL2) sobre Windows 11", fontsize=11, fontweight="bold", color=TINTA, va="top")
    # Windows y Docker
    caja(ax, 0.2, 0.5, 23.6, 13.6, "Windows 11 (equipo del integrante)", fondo="#F7F8FA", negrita=True, ancla="arriba", tam=9)
    caja(ax, 0.6, 5.4, 14.6, 7.8, "Docker Desktop · WSL2 · <AIRFLOW> (compose oficial, CeleryExecutor)", fondo="#F0F4F8", ancla="arriba", negrita=True, tam=8.5)
    contenedores = [("airflow-apiserver\n127.0.0.1:8080", 0.9, 10.7), ("airflow-scheduler", 4.0, 10.7), ("airflow-dag-\nprocessor", 7.1, 10.7), ("airflow-triggerer", 10.2, 10.7),
                    ("airflow-worker\n(ejecuta las tareas)", 4.0, 8.3), ("postgres 16\n(metadatos)", 7.1, 8.3), ("redis 7.2\n(cola de Celery)", 10.2, 8.3)]
    for nombre, x, y in contenedores:
        caja(ax, x, y, 2.8, 1.6, nombre, fondo=AZUL, tam=7.8)
    caja(ax, 0.9, 8.3, 2.8, 1.6, "airflow-init\n(solo al inicio)", fondo=GRIS, tam=7.8)
    # DAG
    caja(ax, 0.9, 5.8, 13.8, 2.0, "", fondo=VERDE)
    ax.text(1.1, 7.6, "DAG medallon_etl_sismo · 0 6 * * * (America/Bogota) · catchup=False", fontsize=8, fontweight="bold", va="top", color=TINTA)
    tareas = ["validar_bronze", "transformar_a_silver", "integrar_a_gold", "cargar_datawarehouse"]
    xs = [1.1, 4.5, 8.0, 11.2]
    for t, x in zip(tareas, xs):
        caja(ax, x, 6.0, 3.0 if t != "cargar_datawarehouse" else 3.3, 1.0, t, fondo="white", tam=7.6)
    for i in range(3):
        flecha(ax, (xs[i] + (3.0), 6.5), (xs[i + 1], 6.5))
    # carpetas del anfitrión
    caja(ax, 16.0, 8.6, 7.5, 4.6, "", fondo=AMBAR)
    ax.text(16.2, 13.05, "Repositorio <REPO> (carpeta hermana)", fontsize=8.5, fontweight="bold", va="top", color=TINTA)
    ax.text(16.2, 12.45, "montado en solo lectura (:ro) en\n/opt/airflow/medallon", fontsize=7.8, va="top", color=TINTA)
    for k, (txt, y) in enumerate([("data/bronze (manifiesto y 8 sha256)", 11.0), ("data/silver y data/gold (versionados)", 10.2), ("src/, config/, dags/ (copia del DAG)", 9.4), (".env (lectura en memoria)", 8.7)]):
        caja(ax, 16.3, y, 6.9, 0.65, txt, fondo="white", tam=7.5)
    caja(ax, 16.0, 5.4, 7.5, 2.6, "", fondo=AMBAR)
    ax.text(16.2, 7.85, "<AIRFLOW>: dags/, logs/, .env", fontsize=8.5, fontweight="bold", va="top", color=TINTA)
    ax.text(16.2, 7.3, "dags/medallon_etl_dag.py (sincronizado con\nscripts/orquestacion/sincronizar_dag.py)\nregistros de tareas · .env solo con\nAIRFLOW_UID y la contraseña de la interfaz", fontsize=7.4, va="top", color=TINTA)
    # MySQL
    caja(ax, 16.0, 1.0, 7.5, 3.6, "", fondo=VERDE)
    ax.text(16.2, 4.45, "MySQL 8.0.45 en el anfitrión", fontsize=8.5, fontweight="bold", va="top", color=TINTA)
    ax.text(16.2, 3.85, "base `sismo_cali` (7 tablas, historial de corridas)\nusuario `sismo_airflow`@`localhost`:\nSELECT, INSERT, CREATE, INDEX, REFERENCES", fontsize=7.6, va="top", color=TINTA)
    caja(ax, 0.9, 1.0, 14.0, 3.6, "", fondo="#F7F8FA")
    ax.text(1.1, 4.45, "Copia de trabajo por ejecución (en el contenedor, fuera del repositorio)", fontsize=8.5, fontweight="bold", va="top", color=TINTA)
    ax.text(1.1, 3.85, "/tmp/medallon_<ejecución>: src, config, data y docs/silver/hallazgos_eda.md\n"
            "cada tarea compara lo que produce con lo versionado (CSV y JSON byte a byte; base, tabla a tabla)\n"
            "la copia se elimina al terminar o al fallar; el fallo inducido se pide con dag_run.conf", fontsize=7.6, va="top", color=TINTA)
    # flechas
    flecha(ax, (15.95, 11.0), (14.75, 11.0))
    ax.text(15.35, 11.15, "solo\nlectura", ha="center", va="bottom", fontsize=7, color="#52606D")
    flecha(ax, (11.0, 6.0), (11.0, 4.6))
    flecha(ax, (13.4, 6.0), (16.0, 3.0))
    ax.text(15.3, 5.0, "host.docker.internal:3306\n(llega como localhost)", ha="right", va="center", fontsize=7.2, color="#52606D")
    flecha(ax, (15.95, 6.6), (14.75, 6.6))
    ax.text(15.35, 6.75, "dags/", ha="center", va="bottom", fontsize=7, color="#52606D")
    ax.text(0.3, 0.1, "Imagen generada con matplotlib a partir del compose, del DAG y de las evidencias EV-038 y EV-040; no es una captura de pantalla", fontsize=7, color="#52606D")
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(SALIDA, dpi=150, bbox_inches="tight", metadata={"Software": None})
    print("escrito", SALIDA.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
