"""Genera el catálogo de fuentes y metadatos (docs/bronze/catalogo_fuentes_metadatos.md y catalogo_fuentes.json).

Lee el manifiesto de Bronze, config/config.yaml, la capa de metadatos guardada en Bronze, quality_report.json, docs/gold/KPIs.md y
docs/bronze/muestras/. No usa la fecha de ejecución: dos corridas dan archivos idénticos. Solo lee; escribe únicamente los dos archivos de salida.
"""
import csv
import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.common import load_config, read_manifest, sha256_file  # noqa: E402

SALIDA_JSON = "docs/bronze/catalogo_fuentes.json"
SALIDA_MD = "docs/bronze/catalogo_fuentes_metadatos.md"
TIPOS_ARCGIS = {"esriFieldTypeOID": "entero (identificador)", "esriFieldTypeInteger": "entero", "esriFieldTypeString": "texto", "esriFieldTypeDouble": "decimal"}
USADAS_EDIF = {
    "OBJECTID": "identificador de la construcción (se conserva como objectid)",
    "COMUNA": "código catastral de la comuna (2 dígitos, texto); entra a la llave del JOIN",
    "BARRIO": "código catastral del barrio dentro de la comuna (2 dígitos, texto); entra a la llave del JOIN",
    "NPISOS": "número de pisos declarado en la capa",
    "Indice_Escombros": "índice continuo de cambio de textura entre las imágenes pre y post; nulo si no hay datos satelitales",
    "Estado_Estructural": "etiqueta de clase de la capa (se agrupa en cuatro clases estables); no es una evaluación estructural",
}
DESC_SILVER_ESTRATO = {
    "codigo_barrio": "código del barrio (llave del JOIN)", "barrio": "nombre del barrio en el CSV 2015", "lados_e1": "lados de manzana de estrato 1",
    "lados_e2": "lados de manzana de estrato 2", "lados_e3": "lados de manzana de estrato 3", "lados_e4": "lados de manzana de estrato 4",
    "lados_e5": "lados de manzana de estrato 5", "lados_e6": "lados de manzana de estrato 6", "sin_vivienda": "lados de manzana sin vivienda",
    "lados_total": "suma de los lados de manzana por estrato (1 a 6)", "estrato_moda_original": "estrato moda tal como viene en el CSV",
    "estrato": "estrato moda validado (1 a 6; nulo si NR)", "pureza_estrato": "max(lados 1..6)/suma(lados 1..6), sin «Sin vivienda»"}
DESC_HUERFANAS = {"objectid": "identificador de la construcción", "comuna": "código de comuna", "barrio": "código de barrio", "codigo_barrio": "llave construida",
                  "codigo_poligono": "código del polígono 2026 donde cae el centroide", "nombre_poligono": "nombre del polígono", "clase_dano": "clase de la capa",
                  "causa": "motivo por el que la construcción no cruza con el CSV"}
DESC_KPIS = {"kpi_id": "identificador del indicador (K1 a K6)", "nombre": "nombre del indicador", "valor": "valor del indicador (tasa, razón o proporción)",
             "numerador": "numerador (por ejemplo, severos estrictos)", "denominador": "denominador (construcciones con datos satelitales)",
             "grupo": "grupo o corte del indicador", "fecha_corte": "fecha de corte de la capa", "fuente": "fuente declarada del cálculo",
             "ic95_inf": "límite inferior del intervalo al 95 %", "ic95_sup": "límite superior del intervalo al 95 %", "n_sin_datos": "construcciones sin datos satelitales",
             "pct_sin_datos": "proporción sin datos satelitales", "muestra_baja": "verdadero si hay menos de 30 severos", "cota_inf": "cota inferior por «sin datos»",
             "cota_sup": "cota superior por «sin datos»", "nota": "nota del indicador"}
DESC_SENS = {"escenario": "escenario de sensibilidad (S0 a S5)", "kpi_id": "indicador", "grupo": "grupo o corte", "k": "severos", "n": "construcciones con datos",
             "tasa": "k / n", "ic95_inf": "límite inferior del intervalo al 95 %", "ic95_sup": "límite superior del intervalo al 95 %", "nota": "descripción del escenario"}
DESCARTADAS = [
    ("sgc_eval_int", "SGC · Mapa de Intensidades Evaluadas (ArcGIS REST)", "Granularidad por sitio o centro poblado, no por barrio; ningún ID_SISMO identificable como el evento (V9).", "§2 ficha 5; verificacion_fuentes.md V9"),
    ("sgc_municipios", "SGC · SIMMA Capas Generales, Municipios", "Solo polígonos municipales para el Plan B; no es amenaza por barrio.", "§2 ficha 6"),
    ("area_barrios", "Área barrios de Cali 2015 (CSV, respaldo)", "Solo estrato moda por barrio; respaldo del CSV principal, no se usa en el JOIN.", "§2 ficha 3; V5"),
    ("estrato_comunas", "Estratificación por comunas 2015 (CSV)", "Solo 22 filas; sirve para una llave por comuna, no por barrio.", "§2 ficha 3; V5"),
    ("rud", "RUD (UNGRD) vía monitor «Datos del terremoto»", "Archivo JSON estático de un monitor de un solo mantenedor, registro declarativo, sin código DIVIPOLA; Plan B municipal.", "§2 ficha 8; V11"),
    ("divipola", "DIVIPOLA (Socrata gdxc-w37w)", "Códigos municipales; solo útiles en el Plan B municipal.", "§2 ficha 9; V12"),
    ("socrata_hbdu_4927", "Socrata hbdu-4927 (portal SGC)", "Es un enlace federado sin filas; la API devuelve HTTP 400.", "§2 ficha 7"),
    ("mapageologia", "ArcGIS MAPAGEOLOGIA (fallas)", "Geología a escala nacional, sin llave a barrio.", "§2 ficha 6"),
    ("copernicus_emsr916", "Copernicus EMSR916 / ICube-SERTIT", "Solo 21 y 94 edificios en zonas parciales de Cali, sin edificios en común; uso no comercial.", "§2 ficha 11"),
]


def _tipo(s):
    if pd.api.types.is_bool_dtype(s):
        return "lógico"
    if pd.api.types.is_integer_dtype(s):
        return "entero"
    if pd.api.types.is_float_dtype(s):
        return "decimal"
    vals = set(s.dropna().astype(str).unique())
    return "lógico (con nulos)" if vals and vals <= {"True", "False"} else "texto"


def _leer(ruta, **kw):
    return pd.read_csv(ROOT / ruta, dtype=kw.get("dtype", None))


def _desc_gold():
    """Diccionario de gold_final.csv leído de la tabla de docs/gold/KPIs.md (sin duplicarlo a mano)."""
    texto = (ROOT / "docs/gold/KPIs.md").read_text(encoding="utf-8")
    bloque = texto.split("## Diccionario de columnas de `gold_final.csv`")[1]
    d = {}
    for fila in re.findall(r"^\| ((?:`[^`]+`(?:, )?)+) \| (.+?) \|$", bloque, re.M):
        for col in re.findall(r"`([^`]+)`", fila[0]):
            d[col] = fila[1]
    return d


def _archivo(ruta, desc, dtype=None):
    p = ROOT / ruta
    if p.suffix == ".csv":
        df = pd.read_csv(p, dtype=dtype)
        cols = [{"nombre": c, "tipo": _tipo(df[c]), "descripcion": desc[c]} for c in df.columns]
        filas = len(df)
    else:
        cols, filas = None, None
    return {"ruta": ruta, "filas": filas, "bytes": p.stat().st_size, "sha256": sha256_file(p), "columnas": cols}


def _snapshot(entradas):
    """Snapshot de una fuente a partir de las líneas del manifiesto (filas de datos, bytes y sha256 por archivo)."""
    return {"ruta": str(Path(entradas[0]["path"]).parent.as_posix()), "extraccion_utc": entradas[0]["fetched_at_utc"],
            "archivos": [{"source_id": e["source_id"], "ruta": e["path"], "filas": e["rows"], "bytes": e["bytes"], "sha256": e["sha256"]} for e in entradas]}


def construir():
    cfg = load_config()
    man = read_manifest()
    por_id = {}
    for e in man:
        por_id.setdefault(e["source_id"], []).append(e)
    q = json.loads((ROOT / cfg["paths_silver"]["quality_report"]).read_text(encoding="utf-8"))
    edif = por_id["edificaciones"] + por_id["edificaciones_capa_meta"] + por_id["edificaciones_count_antes"] + por_id["edificaciones_count_despues"]
    snap_edif = _snapshot(edif)
    snap_edif["filas_de_datos"] = sum(e["rows"] for e in por_id["edificaciones"])
    snap_edif["bytes"] = sum(e["bytes"] for e in edif)
    snap_edif["paginas"] = [e["rows"] for e in por_id["edificaciones"]]
    meta = json.loads((ROOT / por_id["edificaciones_capa_meta"][0]["path"]).read_text(encoding="utf-8"))
    campos = {f["name"]: TIPOS_ARCGIS.get(f["type"], f["type"]) for f in meta["fields"]}
    cols_edif = [{"nombre": n, "tipo": campos[n], "significado": s} for n, s in USADAS_EDIF.items()]
    no_usadas = [n for n in campos if n not in USADAS_EDIF]
    lic_ckan = re.search(r'texto de licencia: "([^"]+)"', (ROOT / "docs/bronze/muestras/v4_ckan_licencia.txt").read_text(encoding="utf-8")).group(1)
    csv_est = por_id["estrato_barrio"][0]
    enc = pd.read_csv(ROOT / csv_est["path"], nrows=0).columns.tolist()
    geo = por_id["poligonos_barrios"][0]
    usgs = pd.read_csv(ROOT / "docs/bronze/muestras/v10_usgs_11.csv")
    ev = usgs.sort_values("mag", ascending=False).iloc[0]
    kpis_md = (ROOT / "docs/gold/KPIs.md").read_text(encoding="utf-8")
    url_prensa = re.search(r"https://www\.elpais\.com\.co/cali/alcaldia[^ )`]+", kpis_md).group(0)
    atc = re.search(r"3\.403 predios: [^.;|]+", kpis_md).group(0)
    f = cfg["fechas"]
    sd = q["sin_datos"]["total"]
    fuentes = [
        {"id": "edificaciones", "rol": "principal", "nombre": "Impacto Satelital en Edificaciones por Terremoto, Cali 2026", "publicador": "Capa catalogada en datos.gov.co (5vy8-gpw8); servicio ArcGIS FeatureServer",
         "url": cfg["sources"]["edificaciones"]["layer"], "url_consulta": cfg["sources"]["edificaciones"]["url"], "catalogo": "datos.gov.co 5vy8-gpw8",
         "protocolo": "ArcGIS REST (FeatureServer, consulta con paginación por resultOffset)", "formato": "JSON (geometría de polígonos, EPSG:4326)",
         "autenticacion": "ninguna (consulta pública sin token)", "limites_paginacion": f"maxRecordCount {cfg['sources']['edificaciones']['max_record_count']}; 3 páginas de {', '.join(str(p) for p in snap_edif['paginas'])} filas",
         "columnas_usadas": cols_edif, "columnas_no_usadas": no_usadas,
         "cobertura_temporal": f"imágenes pre {f['fecha_imagen_pre']} y post {f['fecha_imagen_post']}; capa editada el {f['fecha_edicion_capa']}",
         "cobertura_espacial": "construcciones dentro de los polígonos de afectación preliminar; 7 comunas de Cali (no es toda la ciudad)",
         "granularidad": "una fila por construcción (huella catastral)", "fechas": {"imagen_pre": f["fecha_imagen_pre"], "imagen_post": f["fecha_imagen_post"], "edicion_capa": f["fecha_edicion_capa"],
                                                                                 "consulta_utc": snap_edif["extraccion_utc"]},
         "licencia": cfg["licencia_capa"], "snapshot": snap_edif, "llave_union": "codigo_barrio = int(COMUNA)*100 + int(BARRIO) (texto)",
         "uso_en_pipeline": "Bronze → Silver (silver_construcciones) → base de todos los KPI de Gold",
         "calidad": {"construcciones": q["fuentes"]["construcciones"]["filas_salida"], "sin_datos_satelitales": sd["num"], "pct_sin_datos": sd["pct"], "geom_duplicada_filas": q["duplicados_marcados"]["geom_duplicada_filas"],
                     "nulos_antes_bronze": {k: q["nulos_antes_bronze"][k] for k in ("COMUNA", "BARRIO", "NPISOS", "Indice_Escombros")}},
         "riesgos_limitaciones": ["Proxy satelital: no es una evaluación estructural ni inspección en sitio.", "Solo incluye construcciones dentro de polígonos de afectación preliminar: la tasa es condicional a esa zona.",
                                  "El servicio no declara licencia (copyrightText vacío); la licencia se toma del catálogo.", "Las imágenes pre y post están separadas unos 4,5 meses y no hay grupo de control."]},
        {"id": "estrato_barrio", "rol": "principal", "nombre": "Estratificación socioeconómica según estrato, por barrio en Cali 2015", "publicador": "DAPM Cali (datos.cali.gov.co); catálogo datos.gov.co 6esn-pmy5",
         "url": cfg["sources"]["estrato_barrio"]["url"], "catalogo": "datos.gov.co 6esn-pmy5", "protocolo": "HTTP GET de un archivo", "formato": "CSV UTF-8",
         "autenticacion": "ninguna (requiere un User-Agent)", "limites_paginacion": "archivo único, sin paginación",
         "columnas_usadas": [{"nombre": c, "tipo": "texto" if c == "Barrio" else "entero (con guiones como nulo)", "significado": "ver columnas de silver_estrato_barrio"} for c in enc],
         "cobertura_temporal": "año 2015 (estrato por lados de manzana)", "cobertura_espacial": "Cali; 346 barrios y 23 filas resumen (comunas y «Otros»)", "granularidad": "una fila por barrio",
         "fechas": {"datos": "2015", "consulta_utc": csv_est["fetched_at_utc"]}, "licencia": lic_ckan, "snapshot": _snapshot(por_id["estrato_barrio"]), "llave_union": "Código único del barrio (codigo_barrio)",
         "uso_en_pipeline": "Bronze → Silver (silver_estrato_barrio) → estrato moda por barrio",
         "calidad": {"filas_entrada": q["fuentes"]["estrato_barrio"]["filas_entrada"], "filas_resumen_separadas": q["fuentes"]["estrato_barrio"]["filas_resumen_separadas"], "filas_salida": q["fuentes"]["estrato_barrio"]["filas_salida"],
                     "cobertura_estrato_valido": q["cobertura_estrato_valido"]["pct"]},
         "riesgos_limitaciones": ["Estrato de 2015: desfase temporal frente a las imágenes de 2026.", "Estrato asignado por barrio (moda), no por predio: falacia ecológica.", "Los códigos de barrio de 2026 están renumerados respecto de 2015 (ver docs/silver/revision_codigos_barrio.md)."]},
        {"id": "poligonos_barrios", "rol": "auxiliar (validación de la llave)", "nombre": "Polígonos de barrios y sectores (WFS dapm:pdt_dpa_barrios_sectores)", "publicador": "DAPM Cali (IDESC, GeoServer)",
         "url": cfg["sources"]["poligonos_barrios"]["url"], "protocolo": "OGC WFS 1.0.0 GetFeature", "formato": "GeoJSON (EPSG:4326)", "autenticacion": "ninguna",
         "limites_paginacion": "una sola respuesta", "columnas_usadas": [{"nombre": "barcodigo", "tipo": "texto", "significado": "código del polígono 2026"}, {"nombre": "barnombre", "tipo": "texto", "significado": "nombre del barrio o sector"},
                                                                       {"nombre": "geometry", "tipo": "polígono", "significado": "límite; se ubica el centroide de cada construcción"}],
         "cobertura_temporal": "polígonos vigentes en 2026 (acuerdo DIVIPOLA)", "cobertura_espacial": "Cali", "granularidad": "una fila por barrio o sector", "fechas": {"consulta_utc": geo["fetched_at_utc"]},
         "licencia": "no declarada en el servicio", "snapshot": _snapshot(por_id["poligonos_barrios"]), "llave_union": "centroide de la construcción dentro del polígono (no entra al JOIN)",
         "uso_en_pipeline": "solo valida la llave (coincide_poligono, nombre_validado)", "calidad": {"pct_coincide_poligono": q["pct_coincide_poligono"]["pct"], "pct_nombre_validado": q["pct_nombre_validado"]["global"]["pct"]},
         "riesgos_limitaciones": ["Los códigos de 2026 difieren de los de 2015 en parte de los barrios.", "El servicio es de un tercero y puede cambiar."]},
        {"id": "usgs", "rol": "contexto", "nombre": "USGS FDSN Event (catálogo de sismos)", "publicador": "U.S. Geological Survey", "url": cfg["sources"]["usgs"]["url"], "protocolo": "HTTP GET (FDSN)", "formato": "CSV",
         "autenticacion": "ninguna", "limites_paginacion": "limit 1 a 20.000", "columnas_usadas": [], "cobertura_temporal": "evento del 2026-08-10", "cobertura_espacial": "ventana de consulta cercana a Cali",
         "granularidad": "un evento por fila", "fechas": {"consulta": "2026-10-15"}, "licencia": "no declarada en esta verificación", "snapshot": None,
         "llave_union": "ninguna", "uso_en_pipeline": f"solo contexto del evento (id {ev['id']}, magnitud {ev['mag']}); no entra al pipeline ni a Bronze (muestra en docs/bronze/muestras/v10_usgs_11.csv)",
         "calidad": {"eventos_en_la_muestra": int(len(usgs))}, "riesgos_limitaciones": ["Sin llave a barrio o municipio: descartada como fuente del JOIN."]},
        {"id": "atc20_prensa", "rol": "contexto", "nombre": "Evaluación estructural ATC-20 de la Alcaldía (cifras de prensa)", "publicador": "El País Cali (reportando a la Alcaldía)", "url": url_prensa, "protocolo": "página web",
         "formato": "artículo", "autenticacion": "ninguna", "limites_paginacion": "no aplica", "columnas_usadas": [], "cobertura_temporal": "publicado el 23-sep-2026", "cobertura_espacial": "Cali (distribución por comuna desconocida)",
         "granularidad": "predio", "fechas": {"consulta": "2026-10-15"}, "licencia": "no aplica (cifras de prensa)", "snapshot": None, "llave_union": "ninguna",
         "uso_en_pipeline": "solo contexto; no se compara ni se mezcla con cifras de Gold", "calidad": {"cifras": atc},
         "riesgos_limitaciones": ["Cifras de prensa, no recotejadas con una fuente oficial descargable.", "La unidad (predios) no es la nuestra (construcciones)."]},
    ]
    gold_desc = _desc_gold()
    st = {"comuna": str, "barrio": str, "codigo_barrio": str, "codigo_poligono": str}
    capas = {
        "bronze": {"descripcion": "Bytes crudos de cada fuente con manifiesto de sha256; nunca se sobrescriben.", "archivos": [
            {"ruta": e["path"], "filas": e["rows"], "bytes": e["bytes"], "sha256": e["sha256"], "source_id": e["source_id"]} for e in man]},
        "silver": {"descripcion": "Datos limpios, tipificados e integrados; cada regla de limpieza está en docs/silver/reglas_silver.md.", "archivos": [
            _archivo(cfg["paths_silver"]["construcciones"], {c: gold_desc.get(c, "campo de la construcción; ver docs/silver/reglas_silver.md") for c in _leer(cfg["paths_silver"]["construcciones"], dtype=st).columns}, st),
            _archivo(cfg["paths_silver"]["estrato_barrio"], DESC_SILVER_ESTRATO),
            _archivo(cfg["paths_silver"]["integrated"], {c: gold_desc[c] for c in _leer(cfg["paths_silver"]["integrated"], dtype=st).columns}, st),
            _archivo(cfg["paths_silver"]["orphans_left"], DESC_HUERFANAS), _archivo(cfg["paths_silver"]["orphans_right"], DESC_SILVER_ESTRATO),
            {"ruta": cfg["paths_silver"]["quality_report"], "filas": None, "bytes": (ROOT / cfg["paths_silver"]["quality_report"]).stat().st_size, "sha256": sha256_file(ROOT / cfg["paths_silver"]["quality_report"]),
             "columnas": None}]},
        "gold": {"descripcion": "Tablas finales para análisis y servicio; diccionario de gold_final leído de docs/gold/KPIs.md.", "archivos": [
            _archivo("data/gold/gold_final.csv", {c: gold_desc[c] for c in _leer("data/gold/gold_final.csv", dtype=st).columns}, st),
            _archivo("data/gold/kpis_gold.csv", DESC_KPIS), _archivo("data/gold/kpis_sensibilidad.csv", DESC_SENS)]},
    }
    return {"version_catalogo": 1, "aviso": "Proxy satelital, no evaluación estructural. Alcance: 7 comunas con polígonos de afectación preliminar; estrato 2015.",
            "fuentes": fuentes, "descartadas": [{"id": i, "nombre": n, "motivo": m, "evidencia": f"docs/bronze/investigacion_fuentes.md {e}"} for i, n, m, e in DESCARTADAS], "diccionario": capas}


def _md(c):
    L = ["# Catálogo de fuentes y metadatos", "",
         "**Archivo generado** por `scripts/make_catalogo_fuentes.py` a partir de `data/bronze/manifest.jsonl`, `config/config.yaml`, la capa de metadatos guardada en Bronze, `data/silver/quality_report.json`, `docs/gold/KPIs.md` y `docs/bronze/muestras/`. "
         "No contiene fechas de ejecución: dos corridas dan el mismo archivo. Se sirve en `GET /fuentes` como `docs/bronze/catalogo_fuentes.json`.", "",
         f"> {c['aviso']}", "", "## Fuentes", "", "| id | rol | publicador | formato | licencia | filas (snapshot) |", "|---|---|---|---|---|---|"]
    for s in c["fuentes"]:
        filas = s["snapshot"].get("filas_de_datos", s["snapshot"]["archivos"][0]["filas"]) if s["snapshot"] else "—"
        L.append(f"| `{s['id']}` | {s['rol']} | {s['publicador']} | {s['formato']} | {s['licencia']} | {filas} |")
    for s in c["fuentes"]:
        L += ["", f"### `{s['id']}` · {s['nombre']}", "", f"- **Rol:** {s['rol']}. **Uso en el pipeline:** {s['uso_en_pipeline']}.", f"- **URL:** {s['url']}",
              f"- **Protocolo:** {s['protocolo']}. **Autenticación:** {s['autenticacion']}. **Límites y paginación:** {s['limites_paginacion']}.",
              f"- **Cobertura temporal:** {s['cobertura_temporal']}. **Cobertura espacial:** {s['cobertura_espacial']}. **Granularidad:** {s['granularidad']}.",
              f"- **Fechas:** " + "; ".join(f"{k} = {v}" for k, v in s["fechas"].items()) + f". **Licencia:** {s['licencia']}.", f"- **Llave de unión:** {s['llave_union']}."]
        if s["snapshot"]:
            sn = s["snapshot"]
            L.append(f"- **Snapshot:** `{sn['ruta']}` · extracción UTC {sn['extraccion_utc']} · " + (f"{sn['filas_de_datos']} filas de datos, {sn['bytes']} bytes · " if "bytes" in sn else "") + f"{len(sn['archivos'])} archivo(s):")
            for a in sn["archivos"]:
                L.append(f"  - `{a['ruta']}` · filas {a['filas']} · {a['bytes']} bytes · sha256 `{a['sha256']}`")
        if s["columnas_usadas"]:
            L += ["", "| columna usada | tipo | significado |", "|---|---|---|"] + [f"| `{x['nombre']}` | {x['tipo']} | {x['significado']} |" for x in s["columnas_usadas"]]
        if s.get("columnas_no_usadas"):
            L.append("\nColumnas de la capa que el pipeline no usa: " + ", ".join(f"`{n}`" for n in s["columnas_no_usadas"]) + ".")
        L += ["", "- **Calidad:** " + "; ".join(f"{k} = {json.dumps(v, ensure_ascii=False)}" for k, v in s["calidad"].items()) + ".", "- **Riesgos y limitaciones:**"] + [f"  - {r}" for r in s["riesgos_limitaciones"]]
    L += ["", "## Fuentes descartadas", "", "| id | fuente | motivo | evidencia |", "|---|---|---|---|"] + [f"| `{d['id']}` | {d['nombre']} | {d['motivo']} | {d['evidencia']} |" for d in c["descartadas"]]
    L += ["", "## Diccionario de metadatos por capa"]
    for capa, v in c["diccionario"].items():
        L += ["", f"### {capa.capitalize()}", "", v["descripcion"], ""]
        for a in v["archivos"]:
            L.append(f"- `{a['ruta']}` · {a['filas'] if a['filas'] is not None else '—'} filas · {a['bytes']} bytes · sha256 `{a['sha256']}`")
            if a.get("columnas"):
                L += ["", "| columna | tipo | descripción |", "|---|---|---|"] + [f"| `{x['nombre']}` | {x['tipo']} | {x['descripcion']} |" for x in a["columnas"]] + [""]
    L += ["", "## Cómo lo defendemos", "",
          "- **Qué afirmamos:** cada fuente usada tiene su publicador, URL, formato, autenticación, límites, columnas, cobertura, fechas, licencia, snapshot con sha256 y riesgos. [Evidencia en el repo: `docs/bronze/catalogo_fuentes.json`]",
          "- **Con qué evidencia:** el catálogo se genera del manifiesto y la prueba `tests/test_catalogo.py` compara sha256, filas y bytes; `GET /fuentes` devuelve el mismo JSON.",
          "- **Qué NO afirmamos:** que las licencias estén verificadas jurídicamente (las tomamos de los catálogos y la fecha de consulta está indicada); que las cifras de prensa sean oficiales.",
          "- **Pregunta probable:** «¿cómo saben que el catálogo coincide con lo descargado?» **Respuesta:** porque se genera desde el manifiesto de Bronze y una prueba compara huellas, filas y bytes.", ""]
    return "\n".join(L)


def main():
    c = construir()
    (ROOT / SALIDA_JSON).write_text(json.dumps(c, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    (ROOT / SALIDA_MD).write_text(_md(c), encoding="utf-8", newline="\n")
    print(f"catálogo escrito: {SALIDA_JSON} y {SALIDA_MD}")


if __name__ == "__main__":
    main()
