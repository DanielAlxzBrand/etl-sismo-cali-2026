"""Integra en los documentos las latencias medidas (EV-018), leídas del CSV; no se copian a mano.

Actualiza la métrica de valor V4 en `03_objetivo_alcance_okr_kpi.md` y la sección de rendimiento de `arquitectura.md`. Idempotente.
Uso: .\\.venv\\Scripts\\python.exe scripts\\evidencias\\integrar_latencias.py
"""
import csv
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from src.logger import get_logger  # noqa: E402

log = get_logger(__name__)
CSV = REPO / "docs/evidencias/api/EV-018_latencia_api.csv"
DOC03 = REPO / "docs/estrategia/03_objetivo_alcance_okr_kpi.md"
ARQ = REPO / "docs/api/arquitectura.md"
INI, FIN = "<!-- latencias:inicio -->", "<!-- latencias:fin -->"
CSV_LOTES = REPO / "docs/evidencias/almacenamiento/EV-030_benchmark_lotes.csv"
CSV_MYSQL = REPO / "docs/evidencias/almacenamiento/EV-032_latencia_api_mysql_vs_sqlite.csv"


def c(x):
    """Número con una cifra decimal y coma decimal."""
    return f"{x:.1f}".replace(".", ",")


def resumen(filas):
    med = [float(f["mediana_ms"]) for f in filas]
    p95 = [float(f["p95_ms"]) for f in filas]
    return min(med), max(med), max(p95), filas[0]["repeticiones"], filas[0]["calentamiento"]


def carga_al_almacen():
    """Frase con el tiempo de carga al almacén y la latencia de la API sobre MySQL, leída de los CSV de almacenamiento (vacía si no existen)."""
    if not (CSV_LOTES.exists() and CSV_MYSQL.exists()):
        return ""
    from src.common import load_config
    lote = int(load_config()["almacenamiento"]["lote"])
    lotes = {int(f["lote"]): f for f in csv.DictReader(open(CSV_LOTES, encoding="utf-8"))}
    elegido, fila = lotes[lote], lotes[1]
    por_almacen = {}
    for f in csv.DictReader(open(CSV_MYSQL, encoding="utf-8")):
        por_almacen.setdefault(f["almacen"], []).append(float(f["mediana_ms"]))
    med = {a: sorted(v)[len(v) // 2] for a, v in por_almacen.items()}
    return (f"tiempo de carga al almacén: mediana de {c(float(elegido['mediana_s']) * 1000)} ms para {elegido['filas_cargadas']} filas con lote de {lote} frente a {c(float(fila['mediana_s']) * 1000)} ms fila a fila "
            f"({elegido['repeticiones']} repeticiones tras 1 de calentamiento, EV-030); API sobre MySQL: mediana de las medianas de {c(med['mysql'])} ms frente a {c(med['sqlite'])} ms con SQLite (EV-032)")


def main():
    filas = list(csv.DictReader(open(CSV, encoding="utf-8")))
    mn, mx, p95, rep, cal = resumen(filas)
    texto = (f"latencia de la API: mediana entre {c(mn)} y {c(mx)} ms por ruta y percentil 95 de hasta {c(p95)} ms ({rep} repeticiones tras {cal} de calentamiento, "
             "servidor real en 127.0.0.1; medición local de una máquina, EV-018)")
    almacen = carga_al_almacen()
    texto_v4 = texto + ("; " + almacen if almacen else "")
    resto = "el resto se mide cuando existan los componentes en construcción"
    s = DOC03.read_text(encoding="utf-8")
    s, n1 = re.subn(r"^\| V4 Componentes del proyecto \|.*$",
                    "| V4 Componentes del proyecto | latencia de la API; tiempo de carga al almacén; tasa de éxito del DAG; tiempo de carga del dashboard | pruebas de cada componente; `docs/evidencias/api/EV-018_latencia_api.csv`, `docs/evidencias/almacenamiento/EV-030_benchmark_lotes.csv`, `docs/evidencias/almacenamiento/EV-032_latencia_api_mysql_vs_sqlite.csv` | "
                    + f"{texto_v4}; {resto} | Medición local, no representa un despliegue; sin valor para los componentes que aún no existen |", s, flags=re.M)
    s, n2 = re.subn(r"^\| Componentes del proyecto \|.*$",
                    "| Componentes del proyecto | latencia de la API y tiempo de carga al almacén medidos (EV-018, EV-030 y EV-032); el resto se mide cuando existan los componentes en construcción | V4 | se define en cada componente | pruebas de cada componente |", s, flags=re.M)
    assert n1 == 1 and n2 == 1, (n1, n2)
    DOC03.write_text(s, encoding="utf-8", newline="\n")
    tabla = ["| ruta | mediana (ms) | percentil 95 (ms) | máximo (ms) |", "|---|---|---|---|"] + [f"| `{f['endpoint']}` | {c(float(f['mediana_ms']))} | {c(float(f['p95_ms']))} | {c(float(f['maximo_ms']))} |" for f in filas]
    bloque = (f"{INI}\n### Rendimiento (medición local)\nLatencia por ruta con el **servidor real** en `127.0.0.1` (no el cliente de pruebas): {rep} solicitudes de medición tras {cal} de calentamiento, "
              "en una sola máquina; el percentil 95 es por rango más cercano. Son mediciones locales y no representan un despliegue. [Evidencia en el repo: `docs/evidencias/api/EV-018_latencia_api.csv`]\n\n"
              + "\n".join(tabla) + f"\n{FIN}")
    a = ARQ.read_text(encoding="utf-8")
    if INI in a:
        a = re.sub(re.escape(INI) + r".*?" + re.escape(FIN), lambda m: bloque, a, flags=re.S)
    else:
        marca = "## 9. Seguridad y amenazas"
        assert marca in a
        a = a.replace(marca, bloque + "\n\n" + marca, 1)
    ARQ.write_text(a, encoding="utf-8", newline="\n")
    log.info("latencias integradas: %s rutas; mediana %.1f a %.1f ms; p95 máx. %.1f ms", len(filas), mn, mx, p95)


if __name__ == "__main__":
    main()
