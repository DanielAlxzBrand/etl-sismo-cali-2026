"""Experimento de independencia del repositorio: el proyecto, solo en una carpeta temporal y sin ninguna otra carpeta del equipo al lado.

Uso, desde la raíz del repositorio:
    python scripts/evidencias/evidencia_independencia.py clon|zip [--puerto-api 8765] [--puerto-panel 8766] [--salida CARPETA]

Qué hace: arma (a) un clon del commit actual o (b) el zip de `make_dist.empaquetar` descomprimido, siempre dentro de una carpeta temporal cuyo único contenido es la
carpeta del proyecto; crea un entorno virtual nuevo de Python 3.13 e instala `requirements.txt`; corre la suite completa (sin `PYTHONUTF8` ni `PYTHONIOENCODING`),
`main.py --stage all` con SQLite, compara los 9 hashes de la línea base, `ejecutar_panel.py --verificar`, `preparar_entorno.py --modo completo` y
`preparar_airflow.py --verificar`. Escribe `resultado_<variante>.json` y `registro_<variante>.txt` en `--salida` (por defecto, la carpeta temporal del sistema).
Por qué es así: solo probando el zip de verdad aparecen las dependencias de `.git` o de carpetas vecinas (D95).
Qué NO hace: no toca el proyecto original, no escribe fuera de la carpeta temporal y de `--salida`, no usa Docker ni MySQL y no imprime valores de ningún `.env`.
Última ejecución real: EV-090 (hecha con el script de la sesión del que sale este archivo); esta versión solo se validó de forma estática.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENV = {k: v for k, v in os.environ.items() if not k.upper().startswith(("PYTHONUTF8", "PYTHONIOENCODING"))} | {"PYTHONDONTWRITEBYTECODE": "1", "PIP_DISABLE_PIP_VERSION_CHECK": "1"}
# Los ocho primeros caracteres del sha256 de las nueve salidas de la línea base.
ESPERADOS = {"data/silver/silver_construcciones.csv": "85ea33eb", "data/silver/silver_estrato_barrio.csv": "0815be18", "data/silver/silver_integrated.csv": "bc1d1c6b",
             "data/silver/silver_orphans_left.csv": "04bc074b", "data/silver/silver_orphans_right.csv": "da95c33f", "data/silver/quality_report.json": "fa66f7f2",
             "data/gold/gold_final.csv": "496ab49e", "data/gold/kpis_gold.csv": "6db3dbee", "data/gold/kpis_sensibilidad.csv": "0cf75f2d"}
RES, LOG = {}, []


def sh(cmd, nombre, cwd=None, timeout=1800):
    """Corre un comando, anota su código y su duración en el resumen y su salida en el registro."""
    t0 = time.perf_counter()
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV, timeout=timeout)
    dt = round(time.perf_counter() - t0, 1)
    LOG.append(f"## {nombre} (código {r.returncode}, {dt} s)\n{(r.stdout + r.stderr)[-2500:]}\n")
    RES[nombre] = {"codigo": r.returncode, "segundos": dt}
    return r


def armar_proyecto(variante, raiz, proyecto, trabajo):
    """Deja el proyecto en `proyecto`: un clon del commit actual o el zip descomprimido (el zip se arma en `trabajo`, fuera de `raiz`)."""
    if variante == "clon":
        sh(["git", "clone", "--quiet", "--no-hardlinks", str(ROOT), str(proyecto)], "clonar")
        return
    clon = trabajo / "clon_para_zip"
    sh(["git", "clone", "--quiet", "--no-hardlinks", str(ROOT), str(clon)], "clonar_para_zip")
    espec = importlib.util.spec_from_file_location("make_dist_del_clon", clon / "scripts" / "make_dist.py")
    md = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(md)
    ruta, nombres = md.empaquetar(clon, trabajo / "zip_salida")
    RES["zip"] = {"archivos": len(nombres), "mb": round(Path(ruta).stat().st_size / 1048576, 1)}
    with zipfile.ZipFile(ruta) as z:
        z.extractall(proyecto)


def experimento(variante, p_api, p_panel, trabajo):
    """Corre todos los pasos del experimento dentro de una carpeta temporal sin hermanas."""
    raiz = trabajo / variante          # carpeta que contiene SOLO la carpeta del proyecto
    proyecto = raiz / "proyecto"
    raiz.mkdir(parents=True)
    armar_proyecto(variante, raiz, proyecto, trabajo)
    RES["hermanas"] = sorted(p.name for p in raiz.iterdir())
    sh(["py", "-3.13", "-m", "venv", str(raiz / "venv")], "venv")
    py = str(raiz / "venv" / "Scripts" / "python.exe")
    sh([py, "-m", "pip", "install", "-r", "requirements.txt"], "pip_install", cwd=proyecto, timeout=2400)
    sh([py, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--no-header", "--color=no", "-rfs"], "suite", cwd=proyecto, timeout=2400)
    sh([py, "main.py", "--stage", "all"], "main_all", cwd=proyecto)
    ok = {k: (hashlib.sha256((proyecto / k).read_bytes()).hexdigest()[:8] == v) for k, v in ESPERADOS.items() if (proyecto / k).exists()}
    RES["hashes_iguales"] = f"{sum(ok.values())} de {len(ESPERADOS)}"
    RES["hashes_distintos"] = [k for k, v in ok.items() if not v]
    sh([py, "scripts/panel/ejecutar_panel.py", "--verificar", "--puerto-api", p_api, "--puerto-panel", p_panel], "panel_verificar", cwd=proyecto)
    sh([py, "scripts/preparar_entorno.py", "--modo", "completo"], "preparar_entorno", cwd=proyecto)
    sh([py, "scripts/orquestacion/preparar_airflow.py", "--verificar"], "preparar_airflow_verificar", cwd=proyecto)
    RES["hermanas_al_final"] = sorted(p.name for p in raiz.iterdir())
    RES["fuera_de_la_raiz_escrito"] = sorted(p.name for p in raiz.iterdir() if p.name not in ("proyecto", "venv"))


def main(argv=None):
    """Prepara las carpetas temporales, corre el experimento y escribe el resumen y el registro."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("variante", choices=("clon", "zip"))
    ap.add_argument("--puerto-api", default="8765")
    ap.add_argument("--puerto-panel", default="8766")
    ap.add_argument("--salida", type=Path, default=Path(tempfile.gettempdir()), help="carpeta donde se escriben el resultado y el registro")
    args = ap.parse_args(argv)
    args.salida.mkdir(parents=True, exist_ok=True)
    trabajo = Path(tempfile.mkdtemp(prefix="sismo_independencia_"))
    RES["variante"] = args.variante
    try:
        experimento(args.variante, args.puerto_api, args.puerto_panel, trabajo)
    finally:
        (args.salida / f"registro_{args.variante}.txt").write_text("\n".join(LOG), encoding="utf-8")
        (args.salida / f"resultado_{args.variante}.json").write_text(json.dumps(RES, ensure_ascii=False, indent=1), encoding="utf-8")
        shutil.rmtree(trabajo, ignore_errors=True)
    print(json.dumps(RES, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
