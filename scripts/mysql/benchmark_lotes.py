"""Mide la carga fila a fila frente a lotes de 500, 1000 y 2000 sobre la base de PRUEBA y propone el tamaño de lote.

Uso:  .\\.venv\\Scripts\\python.exe scripts\\mysql\\benchmark_lotes.py [--repeticiones 5] [--evidencia] [--fijar]
Cada estrategia hace 1 carga de calentamiento (no se cuenta) y N repeticiones; cada una parte de las tablas vacías y mide solo la carga
(la lectura y conversión de los CSV se hace una vez, antes). Informa mediana, p95 y filas por segundo.
Criterio: gana la menor mediana entre los lotes; si otro lote queda a menos de 5 % de la mejor mediana se prefiere el más pequeño.
Con --fijar escribe el valor elegido en `almacenamiento.lote` de config/config.yaml (solo esa línea). Con --evidencia guarda tabla, CSV y gráfico saneados.
"""
import argparse
import re
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.common import load_config  # noqa: E402
from src.load import conexion, esquema, relacional  # noqa: E402
from src.logger import get_logger  # noqa: E402

log = get_logger(__name__)
ESTRATEGIAS = [("fila a fila", 1), ("lote 500", 500), ("lote 1000", 1000), ("lote 2000", 2000)]
TOLERANCIA = 0.05
TABLAS = ("kpi_sensibilidad", "kpi", "construccion", "barrio_estrato", "corrida_archivo", "corrida", "comuna")


def _vaciar(conn):
    cur = conn.cursor()
    try:
        for t in TABLAS:
            cur.execute(f"DROP TABLE IF EXISTS {t}")
        conn.commit()
    finally:
        cur.close()
    esquema.aplicar(conn, "mysql")


def percentil(valores, p):
    """Percentil p (0 a 100) por interpolación lineal; con pocas repeticiones se acerca al máximo."""
    v = sorted(valores)
    k = (len(v) - 1) * p / 100
    i, f = int(k), k - int(k)
    return v[i] if i + 1 >= len(v) else v[i] * (1 - f) + v[i + 1] * f


def elegir(resumen):
    """Tamaño de lote elegido: la menor mediana entre los lotes de 500 o más; con empate técnico (< 5 %) el más pequeño."""
    lotes = {n: m for n, (_, m) in resumen.items() if n > 1}
    mejor = min(lotes.values())
    return min(n for n, m in lotes.items() if m <= mejor * (1 + TOLERANCIA))


def medir(conn, paq, cfg, repeticiones):
    """{lote: ([tiempos], mediana)}; el primer ciclo de cada estrategia es de calentamiento y no se cuenta."""
    resumen = {}
    for nombre, lote in ESTRATEGIAS:
        tiempos = []
        for i in range(repeticiones + 1):
            _vaciar(conn)
            t0 = time.perf_counter()
            r = relacional.cargar(conn, "mysql", lote=lote, cfg=cfg, paquete=paq)
            dt = time.perf_counter() - t0
            assert r["estado"] == "cargada"
            if i > 0:
                tiempos.append(dt)
        resumen[lote] = (tiempos, statistics.median(tiempos))
        log.info("%s: mediana %.2f s", nombre, resumen[lote][1])
    return resumen


def main(argv=None):
    ap = argparse.ArgumentParser(description="Compara tamaños de lote en la carga relacional")
    ap.add_argument("--repeticiones", type=int, default=5)
    ap.add_argument("--evidencia", action="store_true")
    ap.add_argument("--fijar", action="store_true", help="escribe el lote elegido en config/config.yaml")
    a = ap.parse_args(argv)
    cfg = load_config()
    paq = relacional.preparar(cfg)
    total = sum(paq["corrida"]["n"].values())
    t0 = time.perf_counter()
    try:
        conn = conexion.conectar_mysql(prueba=True)
    except conexion.ConexionError as e:
        log.error("%s", e)
        return 3
    try:
        base = conn.cursor()
        base.execute("SELECT DATABASE()")
        nombre_base = base.fetchone()[0]
        base.close()
        if not nombre_base.endswith("_prueba"):
            log.error("el benchmark solo corre sobre la base de prueba (conectado a %s)", nombre_base)
            return 2
        resumen = medir(conn, paq, cfg, a.repeticiones)
    finally:
        conn.close()
    elegido = elegir(resumen)
    filas = [["estrategia", "lote", "repeticiones", "mediana_s", "p95_s", "minimo_s", "filas_por_s", "filas_cargadas"]]
    lineas = ["| Estrategia | Lote | Mediana (s) | p95 (s) | Filas/s |", "|---|---|---|---|---|"]
    for nombre, lote in ESTRATEGIAS:
        tiempos, mediana = resumen[lote]
        p95 = percentil(tiempos, 95)
        filas.append([nombre, lote, len(tiempos), f"{mediana:.3f}", f"{p95:.3f}", f"{min(tiempos):.3f}", f"{total / mediana:.0f}", total])
        lineas.append(f"| {nombre} | {lote} | {mediana:.3f} | {p95:.3f} | {total / mediana:.0f} |")
    mejora = resumen[1][1] / resumen[elegido][1]
    cuerpo = (f"Cada estrategia: 1 carga de calentamiento y {a.repeticiones} repeticiones medidas, desde las tablas vacías, con {total} filas por carga (todas las tablas).\n\n" + "\n".join(lineas) +
              f"\n\nLote elegido: {elegido} (criterio: menor mediana; con diferencia menor de {TOLERANCIA:.0%} se prefiere el lote más pequeño). "
              f"Frente a la carga fila a fila es {mejora:.1f} veces más rápido.\nLos tiempos dependen de este equipo y de la fecha de la medición.\n")
    print(cuerpo)
    if a.fijar:
        ruta = ROOT / "config" / "config.yaml"
        texto = ruta.read_text(encoding="utf-8")
        nuevo, n = re.subn(r"(?m)^(  lote: )\d+(.*)$", rf"\g<1>{elegido}\g<2>", texto)
        if n != 1:
            log.error("no se encontró una sola clave `lote` en config.yaml; no se modifica")
            return 1
        ruta.write_text(nuevo, encoding="utf-8", newline="")
        log.info("config.yaml: almacenamiento.lote = %s", elegido)
    if a.evidencia:
        sys.path.insert(0, str(ROOT / "scripts" / "evidencias"))
        import evidencia
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        dur = time.perf_counter() - t0
        evidencia.guardar("almacenamiento", "benchmark_lotes.txt", "Medición de tamaños de lote de la carga relacional",
                          "python scripts/mysql/benchmark_lotes.py --evidencia", 0, dur, cuerpo)
        evidencia.guardar_csv("almacenamiento", "benchmark_lotes.csv", filas)
        fig, ax = plt.subplots(figsize=(8, 4.2))
        nombres = [n for n, _ in ESTRATEGIAS]
        medianas = [resumen[l][1] for _, l in ESTRATEGIAS]
        barras = ax.bar(nombres, medianas, color=["#B0B7C3" if l != elegido else "#2E7D5B" for _, l in ESTRATEGIAS])
        ax.bar_label(barras, labels=[f"{m:.2f} s" for m in medianas], padding=3, fontsize=9)
        ax.set_ylabel("mediana de la carga (s)")
        ax.set_title(f"Carga de {total} filas por estrategia (verde: lote elegido)", fontsize=11, loc="left")
        ax.spines[["top", "right"]].set_visible(False)
        fig.text(0.01, 0.01, "Gráfico generado por scripts/mysql/benchmark_lotes.py; no es una captura de pantalla", fontsize=7, color="#666666")
        destino = ROOT / "docs" / "evidencias" / "almacenamiento" / "benchmark_lotes.png"
        fig.savefig(destino, dpi=150, bbox_inches="tight", metadata={"Software": None})
        plt.close(fig)
        print("evidencia: docs/evidencias/almacenamiento/benchmark_lotes.*")
    return 0


if __name__ == "__main__":
    sys.exit(main())
