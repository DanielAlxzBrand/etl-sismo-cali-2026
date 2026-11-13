"""Limpieza Silver de la fuente API: construcciones (huellas catastrales) con daño satelital."""
import pandas as pd
from shapely.geometry import Polygon, Point, shape
from shapely.strtree import STRtree

from src.common import registrar_regla
from src.transform.keys import codigo_barrio

CLASES = {"Alta": "escombros", "Posible": "techo", "Sin cambio": "sin_cambio", "Sin datos": "sin_datos"}
TEXTO = ["COMUNA", "BARRIO"]


def en_blanco_a_nulo(df, cols):
    """H4: texto vacío o solo espacios pasa a nulo."""
    for c in cols:
        s = df[c].astype("string").str.strip()
        df[c] = s.mask(s == "")
    return df


def clasificar(etiqueta):
    """H9: etiqueta de Estado_Estructural -> clase estable; una etiqueta nueva detiene el pipeline."""
    for prefijo, clase in CLASES.items():
        if str(etiqueta).startswith(prefijo):
            return clase
    raise ValueError(f"Estado_Estructural desconocido: {etiqueta!r}")


def marcar_geom_duplicada(geoms):
    """H2: True para todas las filas que comparten geometría idéntica con otra."""
    g = pd.Series([str(x["rings"]) if x else None for x in geoms])
    return g.duplicated(keep=False) & g.notna()


def centroides(geoms):
    """H13: centroide del anillo exterior, lon/lat redondeados a 7 decimales."""
    pts = []
    for g in geoms:
        if not g:
            pts.append(None)
            continue
        c = Polygon(g["rings"][0]).centroid
        pts.append(Point(round(c.x, 7), round(c.y, 7)))
    return pts


def asignar_poligono(pts, poligonos):
    """H13: punto en polígono; si cae en varios, el de menor código; si en ninguno, nulo."""
    feats = poligonos["features"]
    geoms = [shape(f["geometry"]) for f in feats]
    cods = [str(int(f["properties"]["barcodigo"])) for f in feats]
    nombres = [f["properties"]["barnombre"].strip() for f in feats]
    tree = STRtree(geoms)
    cod, nom = [], []
    for p in pts:
        idx = tree.query(p, predicate="within") if p is not None else []
        if len(idx) == 0:
            cod.append(None)
            nom.append(None)
        else:
            i = min(idx, key=lambda k: int(cods[k]))
            cod.append(cods[i])
            nom.append(nombres[i])
    return cod, nom


def limpiar_construcciones(raw, geoms, poligonos, reglas):
    """Aplica H1-H4, H9, H10, H16 y el paso espacial; devuelve la tabla Silver ordenada por OBJECTID."""
    df = raw.copy()
    n_in = len(df)
    geoms = list(geoms)
    # H1: la identidad de la construcción es OBJECTID; se elimina explícitamente cualquier OBJECTID repetido (0 en los datos actuales).
    mantener = ~df.OBJECTID.duplicated(keep="first")
    n_dup = int((~mantener).sum())
    df = df[mantener].reset_index(drop=True)
    geoms = [g for g, k in zip(geoms, mantener) if k]
    assert df.OBJECTID.is_unique
    registrar_regla(reglas, "R01", "H1", "OBJECTID", n_dup,
                    "Identificador = OBJECTID (único); la llave catastral se repite por predio con varias construcciones y no se deduplica.")
    blancos = sum(int((df[c].astype("string").str.strip() == "").sum()) for c in TEXTO)
    df = en_blanco_a_nulo(df, TEXTO)
    registrar_regla(reglas, "R02", "H4", "COMUNA, BARRIO", blancos,
                    "Texto vacío o solo espacios pasa a nulo; no se imputa.")
    df["geom_duplicada"] = marcar_geom_duplicada(geoms).values
    registrar_regla(reglas, "R03", "H2", "geom_duplicada", df.geom_duplicada.sum(),
                    "Bandera para las construcciones con geometría idéntica a otra; se conservan las filas.")
    df["clase_dano"] = df.Estado_Estructural.map(clasificar)
    registrar_regla(reglas, "R04", "H9", "clase_dano", len(df),
                    "Etiqueta de Estado_Estructural a 4 clases estables; Indice_Escombros no se imputa.")
    df["sin_datos"] = df.clase_dano.eq("sin_datos")
    registrar_regla(reglas, "R05", "H9, H12", "sin_datos", df.sin_datos.sum(),
                    "'Sin datos satelitales' queda como clase propia (no es 'sin daño'); sale del denominador.")
    con = ~df.sin_datos
    df["severo_estricto"] = pd.array(df.clase_dano.eq("escombros").where(con), dtype="boolean")
    df["dano_visible"] = pd.array(df.clase_dano.isin(["escombros", "techo"]).where(con), dtype="boolean")
    registrar_regla(reglas, "R06", "H10", "severo_estricto, dano_visible", con.sum(),
                    "Banderas D7; nulas (no falsas) cuando no hay datos satelitales.")
    npisos = df.NPISOS.astype("Int64")
    df["npisos"] = npisos
    df["npisos_cero"] = pd.array((npisos == 0), dtype="boolean")
    registrar_regla(reglas, "R07", "H16", "npisos, npisos_cero", (npisos == 0).sum(),
                    "NPISOS a entero nullable sin imputar; bandera para 0 pisos; no se usa como filtro.")
    df["codigo_barrio"] = [codigo_barrio(c, b) for c, b in zip(df.COMUNA.fillna(""), df.BARRIO.fillna(""))]
    registrar_regla(reglas, "R08", "H5", "codigo_barrio", df.codigo_barrio.notna().sum(),
                    "Llave del JOIN = int(COMUNA)*100 + int(BARRIO) como texto; nula si falta COMUNA o BARRIO.")
    pts = centroides(geoms)
    df["lon"] = [p.x if p is not None else None for p in pts]
    df["lat"] = [p.y if p is not None else None for p in pts]
    df["codigo_poligono"], df["nombre_poligono"] = asignar_poligono(pts, poligonos)
    df["coincide_poligono"] = pd.array(df.codigo_barrio.eq(df.codigo_poligono).where(df.codigo_barrio.notna() & df.codigo_poligono.notna()), dtype="boolean")
    registrar_regla(reglas, "R09", "H13, H18", "lon, lat, codigo_poligono, nombre_poligono, coincide_poligono", df.codigo_poligono.notna().sum(),
                    "Centroide de la huella (7 decimales) ubicado en los polígonos WFS 2026; solo valida la llave, no entra al JOIN.")
    out = df.rename(columns={"OBJECTID": "objectid", "COMUNA": "comuna", "BARRIO": "barrio", "Indice_Escombros": "indice_escombros",
                             "Estado_Estructural": "estado_estructural"})
    registrar_regla(reglas, "R10", "H3, H4", "OBJECTID_1, Shape__Area, Shape__Length, ID_PREDIO y demás columnas catastrales", n_in,
                    "Se descartan columnas vacías, en grados o sin uso en Gold; ver docs/silver/hallazgos_eda.md.")
    cols = ["objectid", "comuna", "barrio", "codigo_barrio", "npisos", "npisos_cero", "indice_escombros", "estado_estructural", "clase_dano",
            "sin_datos", "severo_estricto", "dano_visible", "geom_duplicada", "lon", "lat", "codigo_poligono", "nombre_poligono",
            "coincide_poligono"]
    return out[cols].sort_values("objectid").reset_index(drop=True)
