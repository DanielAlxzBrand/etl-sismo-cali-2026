"""Dibuja los diagramas del README en escala de grises a partir de su fuente en texto (`docs/diagramas/*.yaml`).

Uso, desde la raíz:  python scripts/make_diagramas.py [--comprobar]
Cada fuente describe un lienzo de 100 unidades de ancho: `grupos` (marcos con título), `cajas` (texto en varias líneas) y `flechas` (de una caja o grupo a otro, por un lado).
Escribe `<nombre>.svg` (el texto sigue siendo texto) y `<nombre>.png` junto a la fuente. Solo usa matplotlib y PyYAML, que ya son dependencias; no usa red ni color.
Con `--comprobar` no escribe nada: termina con código 1 si la fuente no produce un diagrama válido (ids repetidos, flechas a elementos que no existen).
Qué NO hace: no calcula posiciones; las coordenadas las escribe quien edita la fuente y se revisan mirando la imagen.
"""
import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import yaml  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CARPETA = ROOT / "docs" / "diagramas"
NEGRO, GRIS_OSCURO, GRIS_MEDIO, GRIS_CLARO, BLANCO = "#000000", "#4d4d4d", "#8c8c8c", "#eeeeee", "#ffffff"
ANCHO_IN = 12.0
TAMANO_TEXTO = 12.0


def cargar(ruta):
    return yaml.safe_load(Path(ruta).read_text(encoding="utf-8"))


def elementos(spec):
    """Diccionario id -> elemento (grupos y cajas), con error si hay ids repetidos."""
    out = {}
    for tipo in ("grupos", "cajas"):
        for e in spec.get(tipo, []):
            if e["id"] in out:
                raise ValueError(f"id repetido: {e['id']}")
            out[e["id"]] = {**e, "tipo": tipo}
    return out


def ancla(e, lado):
    x, y, w, h = e["x"], e["y"], e["w"], e["h"]
    return {"izq": (x, y + h / 2), "der": (x + w, y + h / 2), "arriba": (x + w / 2, y + h), "abajo": (x + w / 2, y)}[lado]


def validar(spec):
    els = elementos(spec)
    for f in spec.get("flechas", []):
        for k in ("de", "a"):
            if f[k] not in els:
                raise ValueError(f"flecha a un elemento que no existe: {f[k]}")
    return els


def dibujar(spec, salida_base):
    els = validar(spec)
    ancho, alto = 100.0, float(spec["alto"])
    fig, ax = plt.subplots(figsize=(ANCHO_IN, ANCHO_IN * alto / ancho), dpi=200)
    ax.set_xlim(0, ancho)
    ax.set_ylim(0, alto)
    ax.axis("off")
    fig.patch.set_facecolor(BLANCO)
    fig.subplots_adjust(0, 0, 1, 1)
    for g in spec.get("grupos", []):
        ax.add_patch(FancyBboxPatch((g["x"], g["y"]), g["w"], g["h"], boxstyle="round,pad=0,rounding_size=1.2", fc=GRIS_CLARO, ec=GRIS_MEDIO, lw=1.2, zorder=1))
        ax.text(g["x"] + g["w"] / 2, g["y"] + g["h"] - 1.8, g["titulo"], ha="center", va="top", fontsize=TAMANO_TEXTO, fontweight="bold", color=NEGRO, zorder=3)
    for c in spec.get("cajas", []):
        discontinua = c.get("estilo") == "nota"
        ax.add_patch(FancyBboxPatch((c["x"], c["y"]), c["w"], c["h"], boxstyle="round,pad=0,rounding_size=0.9", fc=BLANCO, ec=GRIS_OSCURO if discontinua else NEGRO,
                                    lw=1.2, ls="--" if discontinua else "-", zorder=2))
        titulo, _, resto = c["texto"].partition("\n")
        if resto:
            ax.text(c["x"] + c["w"] / 2, c["y"] + c["h"] / 2, titulo + "\n" + resto, ha="center", va="center", fontsize=TAMANO_TEXTO - 1, color=NEGRO, linespacing=1.35, zorder=3)
        else:
            ax.text(c["x"] + c["w"] / 2, c["y"] + c["h"] / 2, titulo, ha="center", va="center", fontsize=TAMANO_TEXTO - 1, color=NEGRO, zorder=3)
    for f in spec.get("flechas", []):
        p0, p1 = ancla(els[f["de"]], f.get("lado_de", "der")), ancla(els[f["a"]], f.get("lado_a", "izq"))
        discontinua = f.get("estilo") == "punteada"
        ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=14, lw=1.4, color=GRIS_OSCURO if discontinua else NEGRO, ls="--" if discontinua else "-",
                                     shrinkA=2, shrinkB=2, connectionstyle=f"arc3,rad={f.get('curva', 0)}", zorder=4))
        if f.get("etiqueta"):
            ax.text((p0[0] + p1[0]) / 2 + f.get("dx", 0), (p0[1] + p1[1]) / 2 + f.get("dy", 0.8), f["etiqueta"], ha="center", va="bottom", fontsize=TAMANO_TEXTO - 2,
                    color=GRIS_OSCURO, bbox=dict(fc=BLANCO, ec="none", pad=1.2), zorder=5)
    salida_base = Path(salida_base)
    matplotlib.rcParams["svg.fonttype"] = "none"
    fig.savefig(salida_base.with_suffix(".svg"), format="svg", facecolor=BLANCO)
    fig.savefig(salida_base.with_suffix(".png"), format="png", dpi=200, facecolor=BLANCO)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--comprobar", action="store_true")
    a = ap.parse_args()
    fuentes = sorted(CARPETA.glob("*.yaml"))
    if not fuentes:
        print("no hay fuentes en docs/diagramas/")
        return 1
    for f in fuentes:
        try:
            spec = cargar(f)
            if a.comprobar:
                validar(spec)
            else:
                dibujar(spec, f.with_suffix(""))
        except (ValueError, KeyError) as e:
            print(f"{f.name}: {e}")
            return 1
        print(("comprobado " if a.comprobar else "dibujado ") + f.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
