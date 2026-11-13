"""API con almacenamiento MySQL frente a SQLite: mismas respuestas y latencias, con servidores reales en 127.0.0.1.

Uso:  python scripts/evidencias/evidencia_api_mysql.py
Arranca dos servidores locales (uno por almacén, puertos 8761 y 8762), consulta las mismas rutas en ambos, compara los cuerpos (ignorando solo el campo que nombra el motor),
mide la latencia (calentamiento y repeticiones), comprueba que no se puede escribir (405) y que `data/` no cambió. Guarda la evidencia saneada (texto, CSV y un gráfico).
No imprime credenciales: los servidores leen `.env` por su cuenta.
"""
import csv
import hashlib
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import httpx  # noqa: E402

import evidencia  # noqa: E402
from src.load.conciliacion import RUTAS_EQUIVALENCIA, _sin_motor  # noqa: E402

PUERTOS = {"sqlite": 8761, "mysql": 8762}
REPETICIONES, CALENTAMIENTO = 50, 5
LANZADOR = "import sys,uvicorn; from src.api.app import crear_app; uvicorn.run(crear_app(almacenamiento=sys.argv[1]), host='127.0.0.1', port=int(sys.argv[2]), log_level='warning')"


def huellas_data():
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT / "data").rglob("*")) if p.is_file()}


def arrancar(almacen):
    proc = subprocess.Popen([sys.executable, "-c", LANZADOR, almacen, str(PUERTOS[almacen])], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{PUERTOS[almacen]}"
    for _ in range(60):
        try:
            if httpx.get(url + "/health", timeout=2).status_code == 200:
                return proc, url
        except httpx.HTTPError:
            time.sleep(0.5)
    proc.terminate()
    raise RuntimeError(f"el servidor {almacen} no arrancó")


def medir(url, ruta):
    tiempos = []
    with httpx.Client(base_url=url, timeout=30) as cliente:   # una conexión persistente, como en la medición de la API
        for i in range(CALENTAMIENTO + REPETICIONES):
            t0 = time.perf_counter()
            r = cliente.get(ruta)
            dt = (time.perf_counter() - t0) * 1000
            assert r.status_code == 200, (ruta, r.status_code)
            if i >= CALENTAMIENTO:
                tiempos.append(dt)
    tiempos.sort()
    return statistics.median(tiempos), tiempos[int(0.95 * (len(tiempos) - 1))]


def main():
    t0 = time.perf_counter()
    antes = huellas_data()
    servidores = {}
    filas, lineas, ok = [["ruta", "almacen", "repeticiones", "calentamiento", "mediana_ms", "p95_ms"]], [], True
    try:
        for a in PUERTOS:
            servidores[a] = arrancar(a)
        urls = {a: s[1] for a, s in servidores.items()}
        salud = {a: httpx.get(u + "/health").json() for a, u in urls.items()}
        lineas.append("Servidores locales (127.0.0.1) con el mismo código y distinto almacén:")
        for a, h in salud.items():
            lineas.append(f"- {a}: /health : estado {h['estado']}, almacenamiento «{h['almacenamiento']}», filas por tabla {h['filas_por_tabla']}")
        ok &= all(h["estado"] == "ok" for h in salud.values()) and salud["mysql"]["almacenamiento"] == "mysql" and salud["sqlite"]["almacenamiento"] == "sqlite"
        lineas += ["", "Equivalencia de respuestas (cuerpo y código de estado; se ignora solo el campo que nombra el motor):", "| Ruta | Código SQLite | Código MySQL | Respuesta |", "|---|---|---|---|"]
        iguales = 0
        for ruta in RUTAS_EQUIVALENCIA:
            a, b = httpx.get(urls["sqlite"] + ruta, timeout=30), httpx.get(urls["mysql"] + ruta, timeout=30)
            igual = a.status_code == b.status_code and _sin_motor(a.json()) == _sin_motor(b.json())
            iguales += igual
            lineas.append(f"| `{ruta}` | {a.status_code} | {b.status_code} | {'idéntica' if igual else 'DISTINTA'} |")
        ok &= iguales == len(RUTAS_EQUIVALENCIA)
        lineas.append(f"\nRutas idénticas: {iguales} de {len(RUTAS_EQUIVALENCIA)}.")
        escritura = {a: httpx.post(u + "/kpis", json={}).status_code for a, u in urls.items()}
        ok &= all(c == 405 for c in escritura.values())
        lineas.append(f"Escritura: POST /kpis responde {escritura['sqlite']} (SQLite) y {escritura['mysql']} (MySQL): el servicio solo ofrece GET.")
        rutas_lat = [r for r in RUTAS_EQUIVALENCIA if r != "/construcciones?limit=100&offset=1000"] + ["/construcciones?limit=100&offset=1000"]
        lineas += ["", f"Latencia ({REPETICIONES} repeticiones tras {CALENTAMIENTO} de calentamiento; mediana y percentil 95 en ms, cliente httpx en el mismo equipo):", "| Ruta | SQLite mediana | SQLite p95 | MySQL mediana | MySQL p95 |", "|---|---|---|---|---|"]
        medianas = {"sqlite": [], "mysql": []}
        for ruta in dict.fromkeys(rutas_lat):
            m = {a: medir(urls[a], ruta) for a in PUERTOS}
            for a in PUERTOS:
                filas.append([ruta, a, REPETICIONES, CALENTAMIENTO, f"{m[a][0]:.2f}", f"{m[a][1]:.2f}"])
                medianas[a].append(m[a][0])
            lineas.append(f"| `{ruta}` | {m['sqlite'][0]:.1f} | {m['sqlite'][1]:.1f} | {m['mysql'][0]:.1f} | {m['mysql'][1]:.1f} |")
        lineas.append(f"\nMediana de las medianas: SQLite {statistics.median(medianas['sqlite']):.1f} ms y MySQL {statistics.median(medianas['mysql']):.1f} ms. Son mediciones locales de una máquina.")
        lineas.append("Lectura: las rutas que no consultan el almacén (`/fuentes` y `/calidad`) responden en pocos milisegundos con ambos motores, así que la diferencia de las demás se debe a que la API abre una "
                      "conexión nueva a MySQL en cada solicitud (decisión D52: conexión de solo lectura por solicitud, cerrada al terminar). No hay un conjunto de conexiones reutilizables; para el uso local de este proyecto no se justifica.")
    finally:
        for proc, _ in servidores.values():
            proc.terminate()
            proc.wait(timeout=15)
    sin_cambios = huellas_data() == antes
    ok &= sin_cambios
    lineas.append(f"Sin escritura: los sha256 de los {len(antes)} archivos de `data/` son idénticos antes y después de consultar ambos servidores: {'sí' if sin_cambios else 'NO'}.")
    lineas.append(f"\nResultado: {'todo correcto' if ok else 'HAY DIFERENCIAS'}.")
    cuerpo = "\n".join(lineas) + "\n"
    print(cuerpo)
    evidencia.guardar("almacenamiento", "EV-032_api_mysql_vs_sqlite.txt", "API sobre MySQL frente a SQLite: equivalencia y latencias", "python scripts/evidencias/evidencia_api_mysql.py",
                      0 if ok else 1, time.perf_counter() - t0, cuerpo)
    evidencia.guardar_csv("almacenamiento", "EV-032_latencia_api_mysql_vs_sqlite.csv", filas)
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rutas = list(dict.fromkeys(f[0] for f in filas[1:]))
    med = {a: [float(f[4]) for f in filas[1:] if f[1] == a] for a in PUERTOS}
    fig, ax = plt.subplots(figsize=(10, 5.2))
    y = range(len(rutas))
    ax.barh([i + 0.2 for i in y], med["sqlite"], height=0.4, label="SQLite", color="#B0B7C3")
    ax.barh([i - 0.2 for i in y], med["mysql"], height=0.4, label="MySQL", color="#2E7D5B")
    ax.set_yticks(list(y))
    ax.set_yticklabels(rutas, fontsize=7)
    ax.invert_yaxis()
    ax.set_xlabel("mediana de la latencia (ms)")
    ax.set_title("Latencia de la API por ruta y almacén (servidor local, 50 repeticiones)", fontsize=11, loc="left")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.005, "Gráfico generado por scripts/evidencias/evidencia_api_mysql.py; no es una captura de pantalla", fontsize=7, color="#666666")
    fig.savefig(ROOT / "docs" / "evidencias" / "almacenamiento" / "EV-032_latencia_api_mysql_vs_sqlite.png", dpi=150, bbox_inches="tight", metadata={"Software": None})
    plt.close(fig)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
