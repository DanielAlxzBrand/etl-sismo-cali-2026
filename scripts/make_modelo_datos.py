"""Genera docs/almacenamiento/modelo_datos.md (diccionario de datos) y docs/almacenamiento/img/modelo_er.png a partir de src/load/sql/esquema_mysql.sql.

Uso:  python scripts/make_modelo_datos.py [--verificar]
Con --verificar no escribe nada: devuelve 1 si los archivos generados difieren de los que hay en disco (el diccionario no puede desactualizarse).
Solo escribe dentro de docs/almacenamiento/.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.load import esquema  # noqa: E402

SALIDA_MD = ROOT / "docs" / "almacenamiento" / "modelo_datos.md"
SALIDA_PNG = ROOT / "docs" / "almacenamiento" / "img" / "modelo_er.png"
LEYENDA = "Diagrama generado a partir del esquema; no es una captura de pantalla"


def _cuerpos(texto):
    """{tabla: cuerpo del CREATE TABLE} (entre el paréntesis de apertura y el de cierre)."""
    salida = {}
    for s in esquema.sentencias(texto):
        m = re.match(r"CREATE TABLE IF NOT EXISTS (\w+) \(", s)
        if not m:
            continue
        resto, nivel, en_cadena = s[m.end():], 1, False
        for i, c in enumerate(resto):
            if c == "'":
                en_cadena = not en_cadena
            if en_cadena:
                continue
            nivel += (c == "(") - (c == ")")
            if nivel == 0:
                salida[m.group(1)] = resto[:i]
                break
    return salida


def analizar(texto=None):
    """Estructura del esquema: columnas, claves primarias, claves foráneas, restricciones CHECK e índices por tabla."""
    texto = texto or esquema.leer("mysql")
    cols, coms, cuerpos = esquema.tablas(texto), esquema.comentarios_de_tabla(texto), _cuerpos(texto)
    modelo = {}
    for t, cuerpo in cuerpos.items():
        partes = esquema._separar(cuerpo)
        pk, fks, checks, indices = [], [], [], []
        for p in partes:
            if p.startswith("PRIMARY KEY"):
                pk = [c.strip() for c in re.search(r"\(([^)]*)\)", p).group(1).split(",")]
            elif p.startswith("UNIQUE KEY"):
                m = re.match(r"UNIQUE KEY (\w+) \(([^)]*)\)", p)
                indices.append((m.group(1), m.group(2), True))
            elif p.startswith("KEY"):
                m = re.match(r"KEY (\w+) \(([^)]*)\)", p)
                indices.append((m.group(1), m.group(2), False))
            elif p.startswith("CONSTRAINT") and "FOREIGN KEY" in p:
                m = re.match(r"CONSTRAINT (\w+) FOREIGN KEY \(([^)]*)\) REFERENCES (\w+) \(([^)]*)\)", p)
                fks.append({"nombre": m.group(1), "columnas": m.group(2), "destino": m.group(3), "destino_columnas": m.group(4)})
            elif p.startswith("CONSTRAINT") and " CHECK " in p:
                m = re.match(r"CONSTRAINT (\w+) CHECK \((.*)\)$", p, re.S)
                checks.append((m.group(1), " ".join(m.group(2).split())))
        modelo[t] = {"columnas": cols[t], "comentario": coms[t], "pk": pk, "fks": fks, "checks": checks, "indices": indices}
    return modelo


def markdown(modelo):
    """Texto del diccionario de datos."""
    L = ["# Modelo de datos relacional", "",
         "Este documento se genera con `scripts/make_modelo_datos.py` a partir de `src/load/sql/esquema_mysql.sql`; no se edita a mano. "
         "El mismo modelo existe para SQLite en `src/load/sql/esquema_sqlite.sql` y una prueba comprueba que ambos archivos declaren las mismas tablas y columnas, en el mismo orden.", "",
         "![Modelo entidad-relación](img/modelo_er.png)", "",
         "## Cómo se organiza", "",
         "- Una **corrida** es una carga completa del estrato por barrio, las construcciones de Gold y los indicadores. Cada fila de las tablas de datos lleva el identificador de su corrida, de modo que la historia es la suma de corridas y comparar dos cargas es una consulta.",
         "- `comuna` es la única tabla sin `corrida_id`: reúne los códigos de comuna presentes en el CSV de estrato 2015 y en las construcciones; los códigos no cambian entre corridas y por eso se cargan una sola vez.",
         "- Todas las claves foráneas usan `ON DELETE RESTRICT`: no se puede borrar una corrida que tenga datos ni una comuna que alguien use.",
         "- Las 4 construcciones cuyo código de barrio no está en el CSV de estrato 2015 se cargan con `barrio_estrato_codigo` nulo; no se descarta ninguna ni se inventa un barrio.", "",
         "## Relaciones", "", "| Tabla | Columnas | Referencia | Columnas referenciadas |", "|---|---|---|---|"]
    for t, d in modelo.items():
        for f in d["fks"]:
            L.append(f"| `{t}` | `{f['columnas']}` | `{f['destino']}` | `{f['destino_columnas']}` |")
    L += ["", "## Tablas", ""]
    for t, d in modelo.items():
        L += [f"### `{t}`", "", d["comentario"][0].upper() + d["comentario"][1:] + ".", "",
              f"Clave primaria: `{', '.join(d['pk'])}`.", "", "| Columna | Tipo | Nulo | Descripción |", "|---|---|---|---|"]
        for c in d["columnas"]:
            L.append(f"| `{c['nombre']}` | `{c['tipo']}` | {'no' if c['no_nulo'] else 'sí'} | {c['comentario']} |")
        if d["indices"]:
            L += ["", "Índices: " + "; ".join(f"`{n}` ({c}{', único' if u else ''})" for n, c, u in d["indices"]) + "."]
        if d["checks"]:
            L += ["", "Restricciones de validación:", ""] + [f"- `{n}`: `{e}`" for n, e in d["checks"]]
        L.append("")
    return "\n".join(L).rstrip() + "\n"


def dibujar(modelo, ruta):
    """Diagrama entidad-relación con matplotlib (solo escribe el PNG)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_xlim(0, 102)
    ax.set_ylim(-11, 72)
    ax.axis("off")
    ax.set_title("Modelo relacional de la carga: tablas, claves y relaciones", fontsize=14, fontweight="bold", loc="left")
    pos = {"corrida": (32, 48), "corrida_archivo": (2, 52), "comuna": (2, 6), "barrio_estrato": (32, 8), "construccion": (72, 3), "kpi": (72, 52), "kpi_sensibilidad": (72, 36)}
    ancho = {"corrida": 26, "corrida_archivo": 26, "comuna": 20, "barrio_estrato": 26, "construccion": 28, "kpi": 28, "kpi_sensibilidad": 28}
    clave = {t: set(d["pk"]) for t, d in modelo.items()}
    foranea = {t: {c.strip() for f in d["fks"] for c in f["columnas"].split(",")} for t, d in modelo.items()}
    mostrar = {"corrida": ["id", "clave_corrida", "cargada_en", "fecha_corte", "n_construcciones", "..."], "corrida_archivo": ["corrida_id", "nombre", "sha256", "filas"],
               "comuna": ["codigo", "nombre"], "barrio_estrato": ["corrida_id", "codigo_barrio", "barrio", "comuna", "estrato", "pureza_estrato", "..."],
               "construccion": ["corrida_id", "objectid", "comuna", "barrio_estrato_codigo", "estrato", "severo_estricto", "lon", "lat", "..."],
               "kpi": ["corrida_id", "kpi_id", "grupo", "valor", "ic95_inf", "ic95_sup", "..."], "kpi_sensibilidad": ["corrida_id", "...", "(ver diccionario)"]}
    alto_linea, caja_xy = 2.1, {}
    for t, (x, y) in pos.items():
        filas = mostrar[t]
        h = 3.4 + alto_linea * len(filas)
        w = ancho[t]
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2,rounding_size=0.6", fc="#FFFFFF", ec="#555555", lw=1.3))
        ax.add_patch(FancyBboxPatch((x, y + h - 3), w, 3, boxstyle="round,pad=0.2,rounding_size=0.6", fc="#DCEBDD" if t not in ("kpi", "kpi_sensibilidad") else "#FFF1D6", ec="#555555", lw=1.3))
        ax.text(x + w / 2, y + h - 1.5, t, ha="center", va="center", fontsize=10, fontweight="bold")
        for i, c in enumerate(filas):
            marca = "PK " if c in clave[t] else ("FK " if c in foranea[t] else "   ")
            ax.text(x + 1, y + h - 4.8 - i * alto_linea, marca + c, ha="left", va="center", fontsize=8, family="monospace", color="#1F4E79" if c in clave[t] else "#333333")
        caja_xy[t] = (x, y, w, h)

    def borde(t, lado):
        x, y, w, h = caja_xy[t]
        return {"izqarr": (x + 2, y + h), "izq": (x, y + h / 2), "der": (x + w, y + h / 2), "arr": (x + w / 2, y + h), "aba": (x + w / 2, y)}[lado]

    rel = [("corrida_archivo", "corrida", "der", "izq", "", (0, 0)), ("barrio_estrato", "corrida", "arr", "aba", "", (0, 0)), ("construccion", "corrida", "izqarr", "der", "", (0, 0)),
           ("kpi", "corrida", "izq", "der", "", (0, 0)), ("kpi_sensibilidad", "corrida", "izq", "der", "", (0, 0)), ("barrio_estrato", "comuna", "izq", "der", "comuna", (0, 0)),
           ("construccion", "barrio_estrato", "izq", "der", "corrida_id y barrio", (0, 1.6)), ("construccion", "comuna", "aba", "aba", "comuna", (0, 0))]
    for o, d, lo, ld, txt, (dx, dy) in rel:
        a, b = borde(o, lo), borde(d, ld)
        radio = 0.0 if not (o == "construccion" and d == "comuna") else -0.12
        ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=11, lw=1.2, color="#7A5200", connectionstyle=f"arc3,rad={radio}"))
        if txt:
            ax.text((a[0] + b[0]) / 2 + dx, (a[1] + b[1]) / 2 + dy, txt, ha="center", fontsize=7, color="#7A5200", style="italic")
    ax.text(1, -8, "Las flechas van de la tabla hija a la tabla referenciada (ON DELETE RESTRICT). PK: clave primaria; FK: clave foránea.", fontsize=8, color="#444444")
    ax.text(1, -10, LEYENDA, fontsize=8, color="#666666", style="italic")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta, dpi=200, bbox_inches="tight", metadata={"Software": None})
    plt.close(fig)


def main(argv=None):
    verificar = "--verificar" in (argv if argv is not None else sys.argv[1:])
    modelo = analizar()
    texto = markdown(modelo)
    if verificar:
        actual = SALIDA_MD.read_text(encoding="utf-8") if SALIDA_MD.exists() else ""
        if actual.replace("\r\n", "\n") != texto:
            print("docs/almacenamiento/modelo_datos.md no coincide con el esquema: ejecuten scripts/make_modelo_datos.py")
            return 1
        print("el diccionario de datos coincide con el esquema")
        return 0
    SALIDA_MD.parent.mkdir(parents=True, exist_ok=True)
    SALIDA_MD.write_text(texto, encoding="utf-8", newline="\n")
    dibujar(modelo, SALIDA_PNG)
    print(f"escrito {SALIDA_MD.relative_to(ROOT)} y {SALIDA_PNG.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
