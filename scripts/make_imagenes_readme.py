"""Prepara las capturas del README: copia en escala de grises de cada captura original (los originales de evidencia no se modifican).

Uso, desde la raíz:  python scripts/make_imagenes_readme.py [--registro docs/evidencias/readme/EV-111_imagenes_para_el_readme.txt]
Lee las capturas de `docs/evidencias/` y escribe `docs/img/readme/<nombre>.png` en escala de grises. Dos imágenes se recortan a su parte útil (la documentación de la API sin la lista de
esquemas); el recorte se declara en el registro. Escribe un registro con el origen, el recorte y el sha256 del original y de la copia.
Qué NO hace: no retoca píxeles (solo convierte a gris y recorta), no tapa nada (las capturas originales ya no llevan rutas ni credenciales: se revisaron una por una).
"""
import argparse
import hashlib
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DESTINO = ROOT / "docs" / "img" / "readme"
# (copia, original, recorte (izq, arriba, der, abajo) o None, qué muestra)
IMAGENES = [
    ("airflow_dag.png", "docs/evidencias/modo_completo/EV-102_captura_airflow_cuatro_tareas.png", None, "cuadrícula del DAG con las cuatro tareas en verde (captura manual, 2026-11-16)"),
    ("phpmyadmin_tablas.png", "docs/evidencias/modo_completo/EV-102_captura_phpmyadmin_siete_tablas.png", None, "las siete tablas de la base con sus filas, con la cuenta de solo lectura (captura manual, 2026-11-16)"),
    ("phpmyadmin_insert_rechazado.png", "docs/evidencias/modo_completo/EV-102_captura_phpmyadmin_insert_rechazado.png", None, "un INSERT rechazado para la cuenta de solo lectura (captura manual, 2026-11-16)"),
    ("panel_respuesta.png", "docs/evidencias/readme/EV-110_captura_panel_respuesta.png", None, "página Respuesta del panel (captura automatizada del navegador)"),
    ("api_docs.png", "docs/evidencias/readme/EV-110_captura_api_docs.png", (0, 0, 1400, 1040), "documentación automática de la API, solo la lista de rutas (captura automatizada, recortada)"),
    # los diagramas los aporta Daniel en color (EV-112) con estos nombres; si los reemplaza, volver a ejecutar este script regenera las copias en gris
    ("arquitectura_gris.png", "docs/diagramas/arquitectura_nueva.png", None, "diagrama de la arquitectura aportado por Daniel (EV-112), solo convertido a gris"),
    ("flujo_dag_gris.png", "docs/diagramas/flujo_dag_nueva.png", None, "diagrama del flujo del DAG aportado por Daniel (EV-112), solo convertido a gris"),
]


def sha256(ruta):
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def preparar():
    DESTINO.mkdir(parents=True, exist_ok=True)
    filas = []
    for copia, origen, recorte, que in IMAGENES:
        im = Image.open(ROOT / origen)
        if recorte:
            im = im.crop(recorte)
        im = im.convert("L")
        destino = DESTINO / copia
        im.save(destino, format="PNG", optimize=True)
        filas.append((copia, origen, recorte, que, sha256(ROOT / origen), sha256(destino), im.size))
    return filas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--registro", default="docs/evidencias/readme/EV-111_imagenes_para_el_readme.txt")
    a = ap.parse_args()
    filas = preparar()
    lineas = ["EV-111 · Imágenes del README: copias en escala de grises de capturas reales, diagramas e insignias", "",
              "Comando: python scripts/make_imagenes_readme.py. Los originales no se modifican; la copia solo se convierte a gris y, donde se indica, se recorta.", "",
              "| Copia (docs/img/readme/) | Original | Recorte | Tamaño | Qué muestra | sha256 del original | sha256 de la copia |", "|---|---|---|---|---|---|---|"]
    for copia, origen, recorte, que, so, sc, tam in filas:
        lineas.append(f"| {copia} | {origen} | {'sin recorte' if recorte is None else 'izq, arriba, der, abajo = ' + str(recorte)} | {tam[0]}x{tam[1]} | {que} | {so} | {sc} |")
    lineas += ["", "Imágenes generadas desde su fuente en texto (no son capturas; las aportadas a mano, sin fuente, se registran en EV-112):", "", "| Archivo | Fuente | Comando | sha256 |", "|---|---|---|---|"]
    for ruta in sorted((ROOT / "docs" / "diagramas").glob("*.png")) + sorted((ROOT / "docs" / "diagramas").glob("*.svg")):
        if not ruta.with_suffix(".yaml").exists():
            continue
        lineas.append(f"| {ruta.relative_to(ROOT).as_posix()} | docs/diagramas/{ruta.stem}.yaml | python scripts/make_diagramas.py | {sha256(ruta)} |")
    for ruta in sorted((ROOT / "docs" / "img" / "insignias").glob("*.svg")):
        lineas.append(f"| {ruta.relative_to(ROOT).as_posix()} | valores medidos del repositorio | python scripts/make_insignias.py | {sha256(ruta)} |")
    cuerpo = "\n".join(lineas) + "\n"
    (ROOT / a.registro).write_text(cuerpo, encoding="utf-8", newline="\n")
    print(cuerpo)
    return 0


if __name__ == "__main__":
    sys.exit(main())
