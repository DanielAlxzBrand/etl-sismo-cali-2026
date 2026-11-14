"""Ejecución real del panel con el lanzador: API y panel como procesos de verdad, salud de ambos, las ocho páginas con el cliente real y cierre limpio sin procesos huérfanos.

Uso:  python scripts/evidencias/evidencia_panel_ejecucion.py
Arranca `scripts/panel/ejecutar_panel.py --duracion 150` (almacenamiento SQLite), comprueba la salud de la API y del panel, que la aplicación entrega su página (HTTP 200),
recorre las ocho páginas con AppTest y el cliente HTTP real, espera a que el lanzador se cierre solo (código 0) y confirma que no queda ningún proceso ni puerto abierto, que
`git status` sigue limpio y que no se creó `.streamlit/`. Guarda EV-052.
"""
import hashlib
import socket
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

DURACION = 150


def puerto_abierto(url):
    host, puerto = url.replace("http://", "").split(":")
    with socket.socket() as s:
        s.settimeout(1)
        return s.connect_ex((host, int(puerto))) == 0


def huellas_data():
    return {p.relative_to(REPO).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((REPO / "data").rglob("*")) if p.is_file()}


def estado_git():
    return subprocess.run(["git", "status", "--short"], cwd=REPO, capture_output=True, text=True, encoding="utf-8").stdout.strip()


def main():
    t0 = time.perf_counter()
    antes, git_antes, ok = huellas_data(), estado_git(), True
    lineas = [f"Se lanza `python scripts/panel/ejecutar_panel.py --duracion {DURACION}` con el almacenamiento SQLite (puertos {panel_vivo.PUERTO_API} y {panel_vivo.PUERTO_PANEL}).", ""]
    with panel_vivo.panel_en_marcha(duracion=DURACION) as (urls, proceso, salida):
        api, panel = urls["api"], urls["panel"]
        lineas += ["Salida del lanzador:", *[f"    {l}" for l in salida if l.strip()], ""]
        h = httpx.get(api + "/health", timeout=5).json()
        s = httpx.get(panel + "/_stcore/health", timeout=5)
        raiz = httpx.get(panel + "/", timeout=5)
        ok &= h["estado"] == "ok" and s.text.strip() == "ok" and raiz.status_code == 200
        lineas += ["Salud:", f"- API `/health`: estado «{h['estado']}», almacenamiento «{h['almacenamiento']}», fecha de corte {h['fecha_corte']}.",
                   f"- Panel `/_stcore/health`: «{s.text.strip()}» (HTTP {s.status_code}).", f"- Panel `/`: HTTP {raiz.status_code}, {len(raiz.content)} bytes de la aplicación (la interfaz se dibuja en el navegador; ver EV-054).", ""]
        cliente = ClienteApi(api)
        lineas += ["Las ocho páginas, con el cliente HTTP real y AppTest (la misma lectura de datos que hace la aplicación):", "| Página | Rutas de la API | Resultado | Elementos |", "|---|---|---|---|"]
        for p in registro.PAGINAS:
            at, dt = panel_vivo.renderizar(p.id, lambda ruta, **params: cliente.obtener(ruta, params))
            bien = not at.exception and "proxy de daño" in panel_vivo.textos(at)
            ok &= bien
            lineas.append(f"| {p.titulo} | {', '.join(p.rutas)} | {'correcta' if bien else 'CON FALLO'} ({dt:.1f} s) | {len(at.metric)} métricas, {len(at.dataframe) + len(at.table)} tablas, {len(at.markdown)} textos |")
        cliente.cerrar()
        lineas += [""]
        try:
            codigo = proceso.wait(timeout=DURACION + 60)
        except subprocess.TimeoutExpired:
            codigo = None
        lineas.append(f"Cierre: el lanzador terminó solo con código de salida {codigo} tras los {DURACION} s.")
        ok &= codigo == 0
    time.sleep(2)
    cerrados = not puerto_abierto(api) and not puerto_abierto(panel)
    huerfanos = panel_vivo.procesos_del_panel()
    ok &= cerrados and not huerfanos
    limpio = estado_git() == git_antes and not (REPO / ".streamlit").exists()
    ok &= limpio and huellas_data() == antes
    lineas += [f"- Puertos de la API y del panel cerrados: {'sí' if cerrados else 'NO'}.", f"- Procesos uvicorn o streamlit del panel que quedan: {len(huerfanos)}.",
               f"- `git status` igual que antes y sin carpeta `.streamlit/`: {'sí' if limpio else 'NO'}.", f"- sha256 de los {len(antes)} archivos de `data/` sin cambios: {'sí' if huellas_data() == antes else 'NO'}.",
               "", f"Resultado: {'todo correcto' if ok else 'HAY FALLOS'}."]
    cuerpo = "\n".join(lineas) + "\n"
    print(cuerpo)
    evidencia.guardar("panel", "EV-052_ejecucion_real.txt", "Ejecución real del panel con el lanzador: salud, ocho páginas y cierre limpio", f"python scripts/panel/ejecutar_panel.py --duracion {DURACION}",
                      0 if ok else 1, time.perf_counter() - t0, cuerpo)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
