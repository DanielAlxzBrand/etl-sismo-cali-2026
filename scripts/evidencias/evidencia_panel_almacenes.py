"""Equivalencia de almacenamientos para el panel (SQLite frente a MySQL) y mediciones locales de latencia del cliente y de renderizado de cada página.

Uso:  python scripts/evidencias/evidencia_panel_almacenes.py
Arranca dos APIs reales en 127.0.0.1 (una por almacén; la de MySQL lee `.env` por su cuenta y esta prueba nunca ve ni imprime credenciales), consulta con el cliente del panel
las rutas que usa cada página y compara las respuestas (se ignora solo el campo que nombra el almacén). Renderiza cada página con AppTest contra ambas y compara su contenido.
Mide: latencia del cliente por ruta (5 de calentamiento y 30 mediciones; mediana y p95) y tiempo de renderizado por página (1 de calentamiento y 7 mediciones).
Guarda EV-053 (equivalencia), EV-055 (mediciones), el CSV de las mediciones y comprueba que `data/` no cambió. Son mediciones locales de una máquina.
"""
import csv
import hashlib
import statistics
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import httpx  # noqa: E402

import evidencia  # noqa: E402
import panel_vivo  # noqa: E402
from src.panel import registro  # noqa: E402
from src.panel.cliente_api import ClienteApi  # noqa: E402

PUERTOS = {"sqlite": 8771, "mysql": 8772}
LANZADOR = "import sys,uvicorn; from src.api.app import crear_app; uvicorn.run(crear_app(almacenamiento=sys.argv[1]), host='127.0.0.1', port=int(sys.argv[2]), log_level='warning')"
CALENTAMIENTO_RUTAS, REPETICIONES_RUTAS = 5, 30
CALENTAMIENTO_PAGINAS, REPETICIONES_PAGINAS = 1, 7
RUTAS = [("/health", {}), ("/metadata", {}), ("/fuentes", {}), ("/kpis", {}), ("/kpis/K1", {}), ("/kpis/sensibilidad", {}), ("/comunas", {}), ("/composicion", {}),
         ("/construcciones", {"limit": 50, "offset": 0}), ("/construcciones", {"limit": 50, "offset": 0, "comuna": "20", "severo_estricto": True}), ("/calidad", {}), ("/llave/revision", {})]


def huellas_data():
    return {p.relative_to(REPO).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((REPO / "data").rglob("*")) if p.is_file()}


def sin_almacen(valor):
    """Copia del JSON sin los campos que nombran el almacén (única diferencia permitida)."""
    if isinstance(valor, dict):
        return {k: sin_almacen(v) for k, v in valor.items() if k != "almacenamiento"}
    if isinstance(valor, list):
        return [sin_almacen(v) for v in valor]
    return valor


def arrancar(almacen):
    proc = subprocess.Popen([sys.executable, "-c", LANZADOR, almacen, str(PUERTOS[almacen])], cwd=REPO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{PUERTOS[almacen]}"
    for _ in range(80):
        try:
            if httpx.get(url + "/health", timeout=2).status_code == 200:
                return proc, url
        except httpx.HTTPError:
            time.sleep(0.5)
    proc.terminate()
    raise RuntimeError(f"la API {almacen} no arrancó")


def consulta(cliente):
    def api(ruta, **params):
        return cliente.obtener(ruta, params)
    return api


def percentil(valores, p):
    v = sorted(valores)
    return v[int(p * (len(v) - 1))]


def main():
    t0 = time.perf_counter()
    antes = huellas_data()
    procesos, clientes, ok = {}, {}, True
    eq, med = ["Equivalencia de los datos que consume el panel entre los dos almacenes (APIs reales en 127.0.0.1; el panel solo habla con la API):", ""], []
    filas_csv = [["tipo", "elemento", "almacen", "repeticiones", "calentamiento", "mediana_ms", "p95_ms"]]
    try:
        for a in PUERTOS:
            procesos[a], url = arrancar(a)
            clientes[a] = ClienteApi(url, tiempo_espera=30)
        salud = {a: clientes[a].obtener("/health") for a in PUERTOS}
        for a, r in salud.items():
            eq.append(f"- {a}: estado «{r.datos['estado']}», almacenamiento «{r.datos['almacenamiento']}», filas por tabla {r.datos['filas_por_tabla']}")
        mysql_ok = salud["mysql"].ok and salud["mysql"].datos["estado"] == "ok" and salud["mysql"].datos["almacenamiento"] == "mysql"
        ok &= salud["sqlite"].ok and mysql_ok
        if not mysql_ok:
            eq.append("MySQL no está disponible: no se puede demostrar la equivalencia (el ítem 5.3 queda con matiz).")
        else:
            eq += ["", "Respuestas que consume el panel (comparación del cuerpo normalizado: se ignora solo el campo `almacenamiento`):", "| Ruta | Parámetros | Código SQLite | Código MySQL | Respuesta |", "|---|---|---|---|---|"]
            iguales = 0
            for ruta, params in RUTAS:
                a, b = clientes["sqlite"].obtener(ruta, params), clientes["mysql"].obtener(ruta, params)
                igual = a.ok and b.ok and sin_almacen(a.datos) == sin_almacen(b.datos)
                iguales += igual
                eq.append(f"| `{ruta}` | {params or '—'} | {'200' if a.ok else a.error.estado} | {'200' if b.ok else b.error.estado} | {'idéntica' if igual else 'DISTINTA'} |")
            ok &= iguales == len(RUTAS)
            eq.append(f"\nRespuestas idénticas: {iguales} de {len(RUTAS)}.")
            eq += ["", "Contenido de cada página renderizada con AppTest contra cada API (texto, métricas y tablas; se normaliza la línea del almacenamiento activo):", "| Página | Caracteres SQLite | Caracteres MySQL | Contenido |", "|---|---|---|---|"]
            for p in registro.PAGINAS:
                textos = {}
                for a in PUERTOS:
                    at, _ = panel_vivo.renderizar(p.id, consulta(clientes[a]))
                    assert not at.exception, (p.id, a)
                    textos[a] = panel_vivo.textos(at).replace("almacenamiento: " + a, "almacenamiento: <A>").replace("Almacenamiento activo: " + a, "Almacenamiento activo: <A>")
                igual = textos["sqlite"] == textos["mysql"]
                ok &= igual
                eq.append(f"| {p.titulo} | {len(textos['sqlite'])} | {len(textos['mysql'])} | {'idéntico' if igual else 'DISTINTO'} |")
        # mediciones
        med += ["Mediciones locales de una máquina (no generalizan a otro equipo ni a otro servidor). Son insumos técnicos; no sustituyen la evaluación de usabilidad con personas.", "",
                f"Latencia del cliente del panel por ruta (HTTP real a 127.0.0.1; {CALENTAMIENTO_RUTAS} de calentamiento y {REPETICIONES_RUTAS} mediciones; mediana y p95 en ms):", "| Ruta | SQLite mediana | SQLite p95 | MySQL mediana | MySQL p95 |", "|---|---|---|---|---|"]
        for ruta, params in RUTAS:
            fila = {}
            for a in PUERTOS:
                if a == "mysql" and not mysql_ok:
                    fila[a] = (float("nan"), float("nan"))
                    continue
                tiempos = []
                for i in range(CALENTAMIENTO_RUTAS + REPETICIONES_RUTAS):
                    t = time.perf_counter()
                    r = clientes[a].obtener(ruta, params)
                    dt = (time.perf_counter() - t) * 1000
                    assert r.ok, (a, ruta)
                    if i >= CALENTAMIENTO_RUTAS:
                        tiempos.append(dt)
                fila[a] = (statistics.median(tiempos), percentil(tiempos, 0.95))
                etiqueta = ruta + ("?" + "&".join(f"{k}={v}" for k, v in params.items()) if params else "")
                filas_csv.append(["ruta", etiqueta, a, REPETICIONES_RUTAS, CALENTAMIENTO_RUTAS, f"{fila[a][0]:.2f}", f"{fila[a][1]:.2f}"])
            etiqueta = ruta + ("?" + "&".join(f"{k}={v}" for k, v in params.items()) if params else "")
            med.append(f"| `{etiqueta}` | {fila['sqlite'][0]:.1f} | {fila['sqlite'][1]:.1f} | {fila['mysql'][0]:.1f} | {fila['mysql'][1]:.1f} |")
        med += ["", f"Tiempo de renderizado de cada página con AppTest, incluida la lectura de la API ({CALENTAMIENTO_PAGINAS} de calentamiento y {REPETICIONES_PAGINAS} mediciones; mediana y p95 en ms). No incluye el navegador ni la red hacia una persona:", "| Página | SQLite mediana | SQLite p95 | MySQL mediana | MySQL p95 |", "|---|---|---|---|---|"]
        for p in registro.PAGINAS:
            fila = {}
            for a in PUERTOS:
                if a == "mysql" and not mysql_ok:
                    fila[a] = (float("nan"), float("nan"))
                    continue
                tiempos = []
                for i in range(CALENTAMIENTO_PAGINAS + REPETICIONES_PAGINAS):
                    at, dt = panel_vivo.renderizar(p.id, consulta(clientes[a]))
                    assert not at.exception, (p.id, a)
                    if i >= CALENTAMIENTO_PAGINAS:
                        tiempos.append(dt * 1000)
                fila[a] = (statistics.median(tiempos), percentil(tiempos, 0.95))
                filas_csv.append(["pagina", p.id, a, REPETICIONES_PAGINAS, CALENTAMIENTO_PAGINAS, f"{fila[a][0]:.1f}", f"{fila[a][1]:.1f}"])
            med.append(f"| {p.titulo} | {fila['sqlite'][0]:.0f} | {fila['sqlite'][1]:.0f} | {fila['mysql'][0]:.0f} | {fila['mysql'][1]:.0f} |")
    finally:
        for c in clientes.values():
            c.cerrar()
        for proc in procesos.values():
            proc.terminate()
            try:
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                proc.kill()
    sin_cambios = huellas_data() == antes
    ok &= sin_cambios
    cierre = [f"Sin escritura: los sha256 de los {len(antes)} archivos de `data/` son idénticos antes y después: {'sí' if sin_cambios else 'NO'}.", f"Resultado: {'todo correcto' if ok else 'HAY DIFERENCIAS O FALTAS'}."]
    dur = time.perf_counter() - t0
    evidencia.guardar("panel", "EV-053_equivalencia_almacenes.txt", "Equivalencia de los datos del panel entre SQLite y MySQL", "python scripts/evidencias/evidencia_panel_almacenes.py", 0 if ok else 1, dur, "\n".join(eq + [""] + cierre) + "\n")
    evidencia.guardar("panel", "EV-055_mediciones_panel.txt", "Mediciones locales de latencia del cliente y de renderizado por página", "python scripts/evidencias/evidencia_panel_almacenes.py", 0 if ok else 1, dur, "\n".join(med) + "\n")
    destino = REPO / "docs" / "evidencias" / "panel" / "EV-055_mediciones_panel.csv"
    with open(destino, "w", encoding="utf-8", newline="") as f:
        csv.writer(f, lineterminator="\n").writerows(filas_csv)
    print("\n".join(eq + [""] + med + [""] + cierre))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
