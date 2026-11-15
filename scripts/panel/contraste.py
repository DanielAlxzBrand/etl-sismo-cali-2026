"""Relación de contraste WCAG 2.x de los pares de colores del panel (texto, fondos y colores de los gráficos), calculada desde config/config.yaml.

Uso:  python scripts/panel/contraste.py [--evidencia]
Imprime una tabla con los valores calculados. No afirma un nivel de conformidad: solo informa la relación y si supera 4,5 (texto normal), 3 (objetos gráficos y texto grande) o 7.
Con --evidencia guarda EV-057 en docs/evidencias/panel/. Los pies se calculan al 60 % del color del texto, que es como los pinta Streamlit; los demás colores que Streamlit define por su cuenta no se calculan aquí.
"""
import argparse
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts" / "evidencias"))
from src.panel.tema import colores, contraste  # noqa: E402


def _mezcla(texto, fondo, alfa):
    """Color que resulta de pintar `texto` con opacidad `alfa` sobre `fondo` (así dibuja Streamlit los pies)."""
    a, b = (tuple(int(h.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)) for h in (texto, fondo))
    return "#%02x%02x%02x" % tuple(round(alfa * x + (1 - alfa) * y) for x, y in zip(a, b))


def pares():
    c = dict(colores())
    c["pie"] = _mezcla(c["texto"], c["fondo"], 0.6)
    return [("texto sobre el fondo", "texto", "fondo", "texto"), ("texto sobre el fondo secundario", "texto", "fondo_secundario", "texto"),
            ("pies y subtítulos (Streamlit los pinta al 60 % del texto) sobre el fondo", "pie", "fondo", "texto"),
            ("texto de los ejes y leyendas de los gráficos sobre el fondo", "texto_secundario", "fondo", "texto"),
            ("color principal (barras, puntos) sobre el fondo", "principal", "fondo", "gráfico"), ("color secundario (muestra baja, línea de cero) sobre el fondo", "secundario", "fondo", "gráfico"),
            ("color de apoyo (clase de daño) sobre el fondo", "apoyo", "fondo", "gráfico"), ("color neutro (clase sin cambio) sobre el fondo", "neutro", "fondo", "gráfico"),
            ("barras de error (color del texto) sobre el fondo", "texto", "fondo", "gráfico"), ("principal frente al secundario (dos categorías vecinas)", "principal", "secundario", "gráfico")], c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidencia", action="store_true")
    a = ap.parse_args()
    t0 = time.perf_counter()
    lista, c = pares()
    filas = ["| Par | Colores | Relación de contraste | Supera 3 | Supera 4,5 | Supera 7 |", "|---|---|---|---|---|---|"]
    for nombre, x, y, _ in lista:
        r = contraste(c[x], c[y])
        sup = lambda u: "sí" if r >= u else "no"   # noqa: E731
        filas.append(f"| {nombre} | {c[x]} sobre {c[y]} | {str(round(r, 2)).replace('.', ',')} a 1 | {sup(3)} | {sup(4.5)} | {sup(7)} |")
    cuerpo = ("Relación de contraste de la paleta del panel, calculada con la fórmula de luminancia relativa de WCAG 2.x (valores calculados, no un nivel declarado).\n\n" + "\n".join(filas) +
              "\n\nLo que se calcula con una suposición: los pies y subtítulos los pinta Streamlit al 60 % del color del texto (medido en EV-075 y EV-079). "
              "Lo que no se calcula: los demás colores que Streamlit define por su cuenta (bordes, iconos); el significado de los gráficos "
              "no depende solo del color (la muestra baja y la clase de daño llevan además texto o forma).\n")
    print(cuerpo)
    if a.evidencia:
        import evidencia
        evidencia.guardar("panel", "EV-057_contrastes.txt", "Relaciones de contraste calculadas de la paleta del panel", "python scripts/panel/contraste.py --evidencia", 0, time.perf_counter() - t0, cuerpo)
    return 0


if __name__ == "__main__":
    sys.exit(main())
