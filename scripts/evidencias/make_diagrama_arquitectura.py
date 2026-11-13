"""Dibuja docs/api/img/arquitectura_backend.png con matplotlib (solo escribe el PNG). Ejecutar con el .venv del proyecto."""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

SALIDA = Path(sys.argv[1])
fig, ax = plt.subplots(figsize=(14, 8.2))
ax.set_xlim(0, 100)
ax.set_ylim(0, 62)
ax.axis("off")
ax.set_title("Arquitectura del backend: capas del ETL y capa de servicio de solo lectura", fontsize=14, fontweight="bold", loc="left")
COL = {"fuente": "#E8EEF7", "capa": "#DCEBDD", "serv": "#FFF1D6", "futuro": "#F2F2F2", "cli": "#E6E0F2"}


def caja(x, y, w, h, titulo, detalle, color, futuro=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25,rounding_size=0.8", fc=COL[color], ec="#555555", lw=1.2, ls="--" if futuro else "-"))
    ax.text(x + w / 2, y + h - 1.4, titulo, ha="center", va="top", fontsize=9.5, fontweight="bold")
    ax.text(x + w / 2, y + h - 4.2, detalle, ha="center", va="top", fontsize=7.6, linespacing=1.35)


def flecha(a, b, texto="", color="#333333", ls="-"):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=12, lw=1.3, color=color, ls=ls))
    if texto:
        ax.text((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + 0.9, texto, ha="center", fontsize=7.2, color=color, style="italic")


# fila 1: fuentes y capas del ETL
caja(1, 44, 15, 14, "Fuentes", "Capa ArcGIS\n(construcciones)\nCSV de estrato 2015\nPolígonos WFS", "fuente")
caja(21, 44, 17, 14, "Bronze", "Respuestas crudas\nsnapshots con fecha UTC\nmanifest.jsonl + sha256", "capa")
caja(43, 44, 17, 14, "Silver", "Limpieza, llave, JOIN\nhuérfanos y quality_report\n(reglas R01 a R18)", "capa")
caja(65, 44, 15, 14, "Gold", "gold_final, kpis_gold,\nkpis_sensibilidad (CSV)\nWilson, Newcombe, MH", "capa")
caja(85, 44, 14, 14, "SQLite", "etl_sismo.db\n4 tablas\n(carga posterior)", "capa")
for x0, x1 in [(16.4, 20.6), (38.4, 42.6), (60.4, 64.6), (80.4, 84.6)]:
    flecha((x0, 51), (x1, 51))
# fila 2: capa de servicio
ax.add_patch(FancyBboxPatch((20, 15), 60, 23.5, boxstyle="round,pad=0.3,rounding_size=1", fc="#FFFBF0", ec="#B7791F", lw=1.6))
ax.text(21, 15.8, "Capa de servicio: src/api/ (solo lectura, 127.0.0.1)", fontsize=10, fontweight="bold", color="#7A5200", va="bottom")
caja(22, 19.5, 16, 14, "repositorio.py", "RepositorioGold (interfaz)\nRepositorioSqlite\nURI mode=ro, SQL con\nparámetros, listas blancas", "serv")
caja(42, 19.5, 17, 14, "app.py + esquemas.py", "11 rutas GET con modelos\ntipados y validación\nregistro de solicitudes\n(logger con enmascarado)", "serv")
caja(63, 19.5, 15, 14, "errores.py", "404, 405, 422, 503, 500\n{error: codigo, mensaje,\ndetalle}; sin trazas", "serv")
flecha((38.4, 26.5), (41.6, 26.5), "")
flecha((59.4, 26.5), (62.6, 26.5), "")
flecha((92, 43.4), (36, 34.2), "lee (solo lectura)", color="#B7791F")
caja(1, 19.5, 15, 14, "Catálogo", "make_catalogo_fuentes.py\ncatalogo_fuentes.json\n(manifiesto, config,\nquality_report)", "serv")
flecha((16.4, 26.5), (21.6, 26.5), "/fuentes", color="#B7791F")
flecha((29, 43.2), (8, 34.2), "genera", color="#555555", ls=":")
# fila 3: clientes y componentes futuros
caja(1, 1, 22, 11, "Clientes locales (hoy)", "Navegador en /docs (OpenAPI)\npruebas con TestClient\n(tests/test_api.py)", "cli")
caja(27, 1, 16, 11, "MySQL 8.0", "segundo repositorio por\nconfiguración; en construcción", "futuro", True)
caja(47, 1, 16, 11, "Airflow", "orquestación del pipeline;\nen construcción", "futuro", True)
caja(67, 1, 17, 11, "Dashboard", "Streamlit sobre la API;\nen construcción", "futuro", True)
flecha((50, 15), (12, 12.6), "HTTP GET", color="#5B4B8A")
flecha((35, 15), (35, 12.6), "", color="#999999", ls="--")
flecha((75, 15), (75, 12.6), "", color="#999999", ls="--")
ax.text(85.5, 6.5, "Borde y flecha punteados:" + chr(10) + "componentes futuros", ha="left", va="center", fontsize=7.5, color="#666666")
fig.text(0.01, 0.006, "Diagrama generado a partir del documento docs/api/arquitectura.md; no es una captura de pantalla.", fontsize=8, style="italic", color="#444444")
fig.savefig(SALIDA, dpi=200, bbox_inches="tight")
print("escrito", SALIDA)
