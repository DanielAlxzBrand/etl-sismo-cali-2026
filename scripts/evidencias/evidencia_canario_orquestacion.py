"""Comprobación canario con las credenciales de MySQL, del usuario de Docker y de la interfaz de Airflow: árbol, registros, historial, evidencias, carpeta `airflow-medallon`, imagen y un zip de prueba.

Uso:  python scripts/evidencias/evidencia_canario_orquestacion.py [--airflow RUTA] [--nombre EV-049_canario_orquestacion.txt]
Los valores sensibles de los dos `.env` se leen en memoria y se buscan; el informe solo tiene NOMBRES de variables y conteos, nunca valores. Guarda la evidencia saneada.
"""
import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import evidencia  # noqa: E402


def cargar(nombre):
    espec = importlib.util.spec_from_file_location(nombre, ROOT / "scripts" / f"{nombre}.py")
    m = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(m)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--airflow", default=str(ROOT.parent / "airflow-medallon"))
    ap.add_argument("--nombre", default="canario_orquestacion.txt")
    a = ap.parse_args()
    t0 = time.perf_counter()
    airflow = Path(a.airflow).resolve()
    esc = cargar("escanear_secretos")
    extra = airflow / ".env"
    can = esc.canarios(ROOT, [extra])
    L = [f"Variables sensibles usadas como canarios (solo nombres): {', '.join(sorted(can))}", f"Cantidad de canarios: {len(can)} (proyecto: {len(esc.canarios(ROOT))}; Airflow: {len(can) - len(esc.canarios(ROOT))})", ""]
    ok = len(can) >= 3
    estado = esc.estado_de_env(ROOT)
    ok &= not estado
    L.append(f"1. `.env` del proyecto ignorado por git y no versionado: {'sí' if not estado else 'NO ' + str(estado)}")
    arbol = esc.canario_arbol(ROOT, can)
    ok &= not arbol
    L.append(f"2. Árbol del proyecto (incluye `data/`, `docs/`, evidencias, notebooks y la copia versionada del DAG; excluye `.env`, `.git`, entornos y cachés): {len(arbol)} hallazgos")
    logs = []
    for p in sorted((ROOT / "logs").glob("*.log")):
        logs += esc._buscar_en(p.name, p.read_bytes(), can)
    ok &= not logs
    L.append(f"3. Registros del proyecto (`logs/*.log`, {len(list((ROOT / 'logs').glob('*.log')))} archivos): {len(logs)} hallazgos")
    hist = esc.canario_historial(ROOT, can)
    ok &= not hist
    n_commits = int(subprocess.run(["git", "rev-list", "--all", "--count"], cwd=ROOT, capture_output=True, text=True).stdout.strip() or 0)
    L.append(f"4. Historial de git completo ({n_commits} commits, todas las ramas y etiquetas): {len(hist)} hallazgos")
    if airflow.is_dir():
        propios = {k: v for k, v in can.items() if "@" not in k}   # las del proyecto; las de Airflow viven en su .env, que se excluye como raíz
        todas_en_airflow = esc.canario_arbol(airflow, {**propios, **{k.split("@")[0]: v for k, v in can.items() if "@" in k}})
        n_arch = sum(1 for p in airflow.rglob("*") if p.is_file())
        n_logs = sum(1 for p in (airflow / "logs").rglob("*.log")) if (airflow / "logs").is_dir() else 0
        # el .env de Airflow solo debe tener variables de Airflow
        nombres_env = sorted(esc.dotenv_values(extra)) if hasattr(esc, "dotenv_values") else []
        if not nombres_env:
            from dotenv import dotenv_values
            nombres_env = sorted(dotenv_values(extra))
        solo_airflow = all(n.upper().startswith(("AIRFLOW", "_AIRFLOW")) for n in nombres_env)
        ok &= not todas_en_airflow and solo_airflow
        L.append(f"5. Carpeta `airflow-medallon` ({n_arch} archivos, incluidos {n_logs} registros de tareas, el compose, el Dockerfile y el DAG vivo; `.env` excluido como raíz): {len(todas_en_airflow)} hallazgos de las contraseñas del proyecto y del usuario de Docker")
        L.append(f"   Variables de `airflow-medallon/.env` (solo nombres): {', '.join(nombres_env)}; solo variables de Airflow: {'sí' if solo_airflow else 'NO'}")
        # la contraseña de la interfaz tampoco debe estar en el árbol del proyecto ni en la carpeta de Airflow salvo su .env
        ui = {k: v for k, v in can.items() if "@" in k}
        ui_en_airflow = [h for h in esc.canario_arbol(airflow, {k: v for k, v in ui.items()}) if h[0] != ".env"]
        ok &= not ui_en_airflow
        L.append(f"6. La contraseña de la interfaz fuera de `airflow-medallon/.env` (compose, registros, DAG): {len(ui_en_airflow)} hallazgos")
    else:
        L.append("5. La carpeta `airflow-medallon` no existe: no se revisó")
        ok = False
    # imagen: variables de entorno y capas declaradas
    try:
        r = subprocess.run(["docker", "image", "inspect", "airflow-medallon-airflow-worker"], capture_output=True, timeout=60)
        datos = r.stdout
        h = [k for k, v in can.items() if v.encode() in datos]
        h2 = subprocess.run(["docker", "history", "--no-trunc", "airflow-medallon-airflow-worker"], capture_output=True, timeout=60).stdout
        h += [k for k, v in can.items() if v.encode() in h2]
        ok &= r.returncode == 0 and not h
        L.append(f"7. Imagen `airflow-medallon-airflow-worker` (variables de entorno y capas de `docker image inspect` y `docker history`): {len(h)} hallazgos")
    except (OSError, subprocess.SubprocessError):
        L.append("7. Imagen: no se pudo inspeccionar (Docker no responde)")
        ok = False
    with tempfile.TemporaryDirectory() as tmp:
        clon = Path(tmp) / "clon"
        subprocess.run(["git", "clone", "--quiet", "--no-hardlinks", str(ROOT), str(clon)], check=True, capture_output=True)
        salida = Path(tmp) / "zip"
        salida.mkdir()
        subprocess.run([sys.executable, "-c", f"import sys; sys.path.insert(0, r'{clon}'); import importlib.util as u; "
                        f"e=u.spec_from_file_location('md', r'{clon / 'scripts' / 'make_dist.py'}'); m=u.module_from_spec(e); e.loader.exec_module(m); "
                        f"from pathlib import Path; m.empaquetar(Path(r'{clon}'), Path(r'{salida}'))"], cwd=clon, check=True, capture_output=True)
        z = sorted(salida.glob("*.zip"))[-1]
        zhall = esc.canario_zip(z, can)
        with zipfile.ZipFile(z) as zf:
            nombres = zf.namelist()
        trae_env = any(n == ".env" or n.endswith("/.env") for n in nombres)
        trae_dag = "dags/medallon_etl_dag.py" in nombres and "orquestacion/Dockerfile" in nombres
    ok &= not zhall and not trae_env and trae_dag
    L.append(f"8. Zip de prueba armado con `scripts/make_dist.py` en una carpeta temporal ({len(nombres)} entradas; trae `.env`: {'sí' if trae_env else 'no'}; trae `dags/` y `orquestacion/`: {'sí' if trae_dag else 'NO'}): {len(zhall)} hallazgos")
    gen = esc.escanear_arbol(ROOT) + esc.escanear_historial(ROOT)
    ok &= not gen
    L.append(f"9. Escáner de patrones de secretos (árbol e historial del proyecto): {len(gen)} hallazgos")
    L += ["", f"Resultado: {'0 hallazgos: ninguna contraseña aparece fuera de su `.env`' if ok else 'HAY HALLAZGOS (se informan archivo y variable, nunca el valor)'}."]
    cuerpo = "\n".join(L) + "\n"
    print(cuerpo)
    extras = [(str(airflow), "<AIRFLOW>")]
    ruta = evidencia.guardar("orquestacion", a.nombre, "Comprobación canario de las credenciales de MySQL, del usuario de Docker y de la interfaz de Airflow",
                             "python scripts/evidencias/evidencia_canario_orquestacion.py", 0 if ok else 1, time.perf_counter() - t0, evidencia.limpiar(cuerpo, extras=extras))
    print("evidencia:", ruta.relative_to(ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
