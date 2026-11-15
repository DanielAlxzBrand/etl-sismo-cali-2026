"""Dibuja la matriz poder-interés de los stakeholders (`docs/estrategia/img/matriz_poder_interes.png`) a partir de la tabla de puntajes de `docs/estrategia/02_stakeholders.md`.

Uso, desde la raíz del repositorio:
    python scripts/make_matriz_poder_interes.py [--salida RUTA.png]

Qué hace: lee la tabla de la sección 3 (stakeholder, poder = C1 + C2, interés = C3 + C4) y dibuja un punto numerado por stakeholder en su cuadrante; los puntos que caen en la misma
casilla se separan un poco en horizontal para poder leerlos. Guarda en el propio PNG, como metadato, la lista de puntos y nombres que dibujó, para que una prueba pueda comprobar que la
imagen corresponde a la tabla sin necesidad de leer píxeles.
Por qué es así: la imagen anterior no tenía un script que la generara y traía un rótulo viejo del equipo docente; ahora sale de la tabla, que es la única fuente de los puntajes, y no se inventa ningún valor.
Qué NO hace: no calcula ni cambia puntajes, no modifica la tabla ni la rúbrica R1 y no toca `data/`.
"""
import argparse
import json
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TABLA = ROOT / "docs" / "estrategia" / "02_stakeholders.md"
SALIDA = ROOT / "docs" / "estrategia" / "img" / "matriz_poder_interes.png"
FILA = re.compile(r"^\| (\d+) \| ([^|]+) \| ([0-3]) \| ([0-3]) \| ([0-3]) \| ([0-3]) \| (\d) \| (\d) \| ([^|]+) \|$", re.M)
UMBRAL = 3.5          # los cuadrantes se parten entre 3 y 4 (poder o interés mayor o igual que 4)
SEPARACION = 0.18     # desplazamiento horizontal entre puntos que caen en la misma casilla


def leer_puntos(texto):
    """[(n, nombre, interés, poder)] leído de la tabla de puntajes, comprobando que poder = C1 + C2 e interés = C3 + C4."""
    puntos = []
    for n, nombre, c1, c2, c3, c4, poder, interes, _ in FILA.findall(texto):
        if (int(poder), int(interes)) != (int(c1) + int(c2), int(c3) + int(c4)):
            raise ValueError(f"el stakeholder {n} no cumple poder = C1 + C2 e interés = C3 + C4")
        puntos.append((int(n), nombre.strip(), int(interes), int(poder)))
    if not puntos:
        raise ValueError("no se encontró la tabla de puntajes")
    return puntos


def posiciones(puntos):
    """[(n, x, y)]: la posición de cada punto, separando en horizontal los que comparten casilla."""
    vistos, salida = {}, []
    for n, _, interes, poder in puntos:
        k = vistos.get((interes, poder), 0)
        vistos[(interes, poder)] = k + 1
        salida.append((n, round(interes + k * SEPARACION, 2), poder))
    return salida


def rotulo(n, nombre):
    """Texto de la leyenda: el nombre se corta en una palabra completa si pasa de 52 caracteres."""
    corto = nombre if len(nombre) <= 52 else nombre[:52].rsplit(" ", 1)[0] + "…"
    return f"{n}. {corto}"


def dibujar(puntos, salida):
    """Dibuja y guarda la figura; devuelve el diccionario que quedó en los metadatos del PNG."""
    fig = plt.figure(figsize=(10, 7), dpi=200)
    ax = fig.add_axes([0.09, 0.12, 0.55, 0.76])
    ax.set_xlim(-0.5, 6.5)
    ax.set_ylim(-0.5, 6.5)
    ax.axvline(UMBRAL, color="#888888", linewidth=1)
    ax.axhline(UMBRAL, color="#888888", linewidth=1)
    for texto, x, y in (("Mantener satisfechos", 1.5, 5.8), ("Gestionar de cerca", 5.0, 5.8), ("Monitorear", 1.5, -0.25), ("Mantener informados", 5.0, -0.25)):
        ax.text(x, y, texto, ha="center", va="center", fontsize=10, style="italic", color="#444444")
    for n, x, y in posiciones(puntos):
        ax.scatter([x], [y], s=260, color="#2a6f97", zorder=3)
        ax.text(x, y, str(n), ha="center", va="center", color="white", fontsize=8, fontweight="bold", zorder=4)
    ax.set_xlabel("Interés (C3 + C4, de 0 a 6)", fontsize=10)
    ax.set_ylabel("Poder (C1 + C2, de 0 a 6)", fontsize=10)
    ax.set_xticks(range(7))
    ax.set_yticks(range(7))
    ax.tick_params(labelsize=9)
    ax.set_title("Matriz poder-interés de los stakeholders (rúbrica R1)", fontsize=13)
    fig.text(0.995, 0.5, "\n".join(rotulo(n, nombre) for n, nombre, _, _ in puntos), ha="right", va="center", fontsize=7, linespacing=1.55)
    fig.text(0.01, 0.012, "Diagrama generado a partir de la tabla de puntajes; criterio del equipo", fontsize=8, color="#444444")
    atestado = {"fuente": "docs/estrategia/02_stakeholders.md", "puntos": [[n, nombre, interes, poder] for n, nombre, interes, poder in puntos]}
    Path(salida).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(salida, format="png", metadata={"Software": None, "Description": json.dumps(atestado, ensure_ascii=False)})
    plt.close(fig)
    return atestado


def main(argv=None):
    """Lee la tabla y escribe el PNG."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--salida", type=Path, default=SALIDA, help="ruta del PNG (por defecto, la imagen del repositorio)")
    args = ap.parse_args(argv)
    atestado = dibujar(leer_puntos(TABLA.read_text(encoding="utf-8")), args.salida)
    print(f"figura escrita con {len(atestado['puntos'])} stakeholders")
    return 0


if __name__ == "__main__":
    sys.exit(main())
