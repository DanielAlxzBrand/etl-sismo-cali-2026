"""Genera docs/panel/trazabilidad_ui.md desde el registro único de componentes (src/panel/registro.py).

Uso:  python scripts/panel/generar_trazabilidad.py [--verificar]
Cada fila liga un componente con la ruta de la API que lo alimenta, el campo del archivo de salida que muestra, el archivo, el KPI y la pregunta de negocio de su página.
Con --verificar no escribe: falla si el documento no coincide con el registro. No se edita a mano.
"""
import argparse
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from src.panel import registro  # noqa: E402

SALIDA = REPO / "docs" / "panel" / "trazabilidad_ui.md"


def texto():
    tipos = Counter(c.tipo for c in registro.COMPONENTES)
    L = ["# Trazabilidad de la interfaz: componente, ruta de la API, campo, archivo de salida y pregunta de negocio", "",
         "Este documento se genera con `python scripts/panel/generar_trazabilidad.py` desde el registro único de componentes (`src/panel/registro.py`); no se edita a mano. "
         "Una prueba comprueba que cada ruta existe en el OpenAPI de la API y que cada campo y cada KPI existen en los archivos de salida.", "",
         f"- **Páginas:** {len(registro.PAGINAS)}. **Componentes:** {len(registro.COMPONENTES)} ({', '.join(f'{n} de tipo {t}' for t, n in sorted(tipos.items()))}).",
         "- **Cómo se lee:** el panel no abre archivos: pide la ruta a la API y muestra el campo. La columna «archivo de salida» es donde está el número que la API sirve.",
         "- **Nombres de campos:** son las columnas del archivo de salida; la ruta `/comunas` los renombra (`tasa` = `valor`, `severos` = `numerador`, `n_con_datos` = `denominador`).", ""]
    for i, p in enumerate(registro.PAGINAS):
        direccion = "/` (página de inicio)" if i == 0 else f"/{p.url_path}`"
        L += [f"## {p.titulo}", f"**Pregunta de negocio:** {p.pregunta}", f"**Rutas de la API:** {', '.join(f'`{r}`' for r in p.rutas)}. **Dirección:** `{direccion}", "",
              "| Componente | Tipo | Ruta | Campos | Archivo de salida | KPI | Advertencia visible |", "|---|---|---|---|---|---|---|"]
        for c in registro.componentes_de(p.id):
            L.append(f"| {c.titulo} (`{c.id}`) | {c.tipo} | {', '.join(f'`{r}`' for r in c.rutas)} | {', '.join(f'`{x}`' for x in c.campos)} | `{c.fuente}` | {c.kpi or '—'} | {c.advertencia} |")
        L.append("")
    L += ["## Alcance y límites", "- **Qué afirmamos:** cada componente del panel tiene una ruta de la API, un campo y un archivo de salida declarados, y una prueba que los verifica.",
          "- **Qué NO afirmamos:** que el panel cubra todas las preguntas posibles ni que la lectura de los gráficos sustituya la lectura de las limitaciones.", ""]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--verificar", action="store_true")
    a = ap.parse_args(argv)
    nuevo = texto()
    if a.verificar:
        return 0 if SALIDA.exists() and SALIDA.read_text(encoding="utf-8") == nuevo else 1
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(nuevo, encoding="utf-8", newline="\n")
    print("escrito", SALIDA.relative_to(REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
