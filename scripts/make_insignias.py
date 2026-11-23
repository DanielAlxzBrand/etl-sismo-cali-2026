"""Genera las insignias estáticas del README (SVG en grises y negro) en `docs/img/insignias/`, sin red y sin servicios externos.

Uso, desde la raíz:  python scripts/make_insignias.py [--pruebas N] [--cobertura "77 %"]
Cada valor sale de un archivo del repositorio: Python de la cabecera de `requirements.txt`, Airflow del `FROM` de `orquestacion/Dockerfile`, el número de pruebas de la recolección
de pytest (o de `--pruebas`), la licencia de `LICENSE`, la fecha de EV-100 del manifiesto de evidencias. La cobertura no se mide aquí: se pasa con `--cobertura` y debe salir de una medición registrada en `docs/evidencias/readme/`.
Qué NO hace: no promete nada que el repositorio no pueda comprobar (no hay insignia del flujo de integración continua porque todavía no ha corrido en GitHub).
`tests/test_readme_cifras.py` comprueba que el texto de cada insignia coincida con lo que miden esos archivos.
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
DESTINO = ROOT / "docs" / "img" / "insignias"
ANCHO_CARACTER = 6.9   # píxeles por carácter a 11 px de Verdana/DejaVu Sans (aproximación suficiente para cajas en blanco y negro)


def python_soportado():
    return re.search(r"(?m)^# Python soportado: (\d+\.\d+)", (ROOT / "requirements.txt").read_text(encoding="utf-8")).group(1)


def airflow():
    return re.search(r"(?m)^FROM apache/airflow:(\d+\.\d+\.\d+)", (ROOT / "orquestacion" / "Dockerfile").read_text(encoding="utf-8")).group(1)


def pruebas_recolectadas():
    r = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"})
    m = re.search(r"(\d+) tests? collected", r.stdout)
    return int(m.group(1))


def licencia():
    primera = (ROOT / "LICENSE").read_text(encoding="utf-8").splitlines()[0]
    return primera.replace(" License", "")


def ultima_verificacion():
    """Fecha de EV-100 en el manifiesto de evidencias: la guía del modo completo seguida desde un zip nuevo."""
    m = re.search(r"(?m)^\| EV-100 \|.*?\| (\d{4}-\d{2}-\d{2}) \| docs/evidencias/", (ROOT / "docs" / "evidencias" / "manifiesto.md").read_text(encoding="utf-8"))
    return m.group(1)


def insignia(etiqueta, valor):
    """SVG de dos tramos: etiqueta en gris oscuro y valor en negro, texto en blanco."""
    w1, w2 = int(len(etiqueta) * ANCHO_CARACTER + 16), int(len(valor) * ANCHO_CARACTER + 16)
    t = escape(f"{etiqueta}: {valor}")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n' + f'<svg xmlns="http://www.w3.org/2000/svg" width="{w1 + w2}" height="22" role="img" aria-label="{t}"><title>{t}</title>'
            f'<rect width="{w1}" height="22" fill="#555555"/><rect x="{w1}" width="{w2}" height="22" fill="#111111"/>'
            f'<g fill="#ffffff" font-family="Verdana, DejaVu Sans, sans-serif" font-size="11" text-anchor="middle">'
            f'<text x="{w1 / 2:.1f}" y="15">{escape(etiqueta)}</text><text x="{w1 + w2 / 2:.1f}" y="15">{escape(valor)}</text></g></svg>\n')


def insignias(pruebas, cobertura=None):
    """Lista de (archivo, etiqueta, valor) de las insignias del README."""
    out = [("python.svg", "Python", python_soportado()), ("airflow.svg", "Airflow", airflow()), ("mysql.svg", "MySQL", "8.0"),
           ("pruebas.svg", "pruebas", str(pruebas)), ("licencia.svg", "licencia", licencia()), ("madurez.svg", "madurez", "MVP académico"),
           ("verificacion.svg", "última verificación", ultima_verificacion())]
    if cobertura:
        out.append(("cobertura.svg", "cobertura de src", cobertura))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pruebas", type=int)
    ap.add_argument("--cobertura")
    a = ap.parse_args()
    DESTINO.mkdir(parents=True, exist_ok=True)
    for archivo, etiqueta, valor in insignias(a.pruebas or pruebas_recolectadas(), a.cobertura):
        (DESTINO / archivo).write_text(insignia(etiqueta, valor), encoding="utf-8", newline="\n")
        print(f"{archivo}: {etiqueta}: {valor}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
