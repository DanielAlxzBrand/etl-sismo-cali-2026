"""Las cifras que el documento de arquitectura y sus ADR afirman deben coincidir con lo que mide el repositorio hoy (D106), y no deben repetir los errores que el README ya corrigió.

Cada prueba extrae del texto lo que afirma y lo compara con la medida: pruebas, rutas, tablas, índices, defectos, mutaciones, cobertura, casos, número de ADR, última decisión, volumen, tiempos y cifras de calidad.
Una cifra alterada en un solo lugar hace fallar la prueba. Las pruebas negativas usan textos sintéticos. La forma y la redacción se vigilan en `tests/test_arquitectura_guardiana.py`.
"""
import csv
import json
import re
import subprocess

import pandas as pd
import yaml

from src.common import ROOT
from tests.test_arquitectura_guardiana import ADRS, DOC, archivos_adr
from tests.test_readme_cifras import EV113, RECURSOS, _recolectadas, cifras_de_pruebas, clasificar_defectos, tiempos_que_no_coinciden, valor_medido_de_cobertura

DOC_TEXTO = DOC.read_text(encoding="utf-8")
ADR_TEXTO = {r.name: r.read_text(encoding="utf-8") for r in archivos_adr()}
TODO = DOC_TEXTO + "\n" + "\n".join(ADR_TEXTO.values())
README = (ROOT / "README.md").read_text(encoding="utf-8")
DECISIONES = (ROOT / "docs" / "DECISIONES.md").read_text(encoding="utf-8")
REP = json.loads((ROOT / "data" / "silver" / "quality_report.json").read_text(encoding="utf-8"))
GOLD = pd.read_csv(ROOT / "data" / "gold" / "gold_final.csv", dtype={"comuna": str, "codigo_barrio": str})


def _miles(n):
    return f"{int(n):,}".replace(",", ".")


def _coma(v, d):
    from decimal import ROUND_HALF_UP, Decimal
    return str(Decimal(repr(float(v))).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP)).replace(".", ",")


def _leer(ruta):
    return (ROOT / ruta).read_text(encoding="utf-8").replace("\r\n", "\n")


# ---------------------------------------------------------------- funciones de extracción (con pruebas negativas más abajo)
def cifras_con_patron(texto, patron):
    return sorted({m for m in re.findall(patron, texto)})


def defectos_sin_demostrar_en(texto, n):
    """Identificadores declarados sin demostración tras «para los otros N no se demostró (...)», con rangos «DEF-022 a DEF-025» (sin distinguir mayúsculas)."""
    m = re.search(rf"(?i)para los otros {n} no se demostró \(([^)]+)\)", texto)
    if not m:
        return None
    ids = set(re.findall(r"DEF-\d+", re.sub(r"DEF-(\d+) a DEF-(\d+)", "", m.group(1))))
    for a, b in re.findall(r"DEF-(\d+) a DEF-(\d+)", m.group(1)):
        ids |= {f"DEF-{i:03d}" for i in range(int(a), int(b) + 1)}
    return ids


def frases_prohibidas_presentes(texto, frases):
    """Frases prohibidas que aparecen, sin distinguir mayúsculas."""
    return [f for f in frases if f.lower() in texto.lower()]


def barrio_norm_sin_aclarar(texto):
    """Párrafos que nombran `barrio_norm` sin decir que D-FUENTES modificó la decisión."""
    return [p for p in texto.split("\n\n") if "barrio_norm" in p and "D-FUENTES" not in p]


# ---------------------------------------------------------------- cifras medidas
def test_el_numero_de_pruebas_del_documento_es_el_de_la_recoleccion():
    n = sum(_recolectadas().values())
    assert cifras_de_pruebas(DOC_TEXTO) == [n], (cifras_de_pruebas(DOC_TEXTO), n)
    assert not re.search(r"\b\d{4} en total\b", DOC_TEXTO), "un recuento escrito sin el formato **N pruebas**"


def test_las_rutas_el_panel_y_las_tablas_del_documento_son_los_de_la_aplicacion_y_los_almacenes():
    import sqlite3

    from src.api.app import app
    from src.panel import registro

    rutas = {r.path for r in app.routes if getattr(r, "methods", None) and r.path not in ("/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc")}
    assert cifras_con_patron(TODO, r"(\d+) rutas GET") == [str(len(rutas))]
    paginas = {m[0] for m in re.findall(r"(\d+) páginas( y (\d+) componentes)?", TODO)}
    assert paginas == {str(len(registro.PAGINAS))}, paginas
    assert set(re.findall(r"(\d+) páginas y (\d+) componentes", ADR_TEXTO["adr-012_panel_solo_sobre_la_api.md"])) == {(str(len(registro.PAGINAS)), str(len(registro.COMPONENTES)))}
    conn = sqlite3.connect((ROOT / "data" / "gold" / "etl_sismo.db").as_uri() + "?mode=ro", uri=True)
    try:
        sqlite = [f[0] for f in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    finally:
        conn.close()
    sql = _leer("src/load/sql/esquema_mysql.sql")
    mysql = re.findall(r"CREATE TABLE IF NOT EXISTS (\w+)", sql)
    indices = re.findall(r"(?m)^\s+KEY (ix_\w+)", sql)
    palabras = {"una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12}
    mencionadas = {palabras.get(m) or int(m) for m in re.findall(r"\b(\d+|" + "|".join(palabras) + r") tablas", TODO)}
    silver = len(list((ROOT / "data" / "silver").glob("silver_*.csv")))   # «cinco tablas» de Silver
    indicadores = len(list((ROOT / "data" / "gold").glob("kpis_*.csv")))   # «dos tablas» de indicadores
    assert mencionadas == {len(sqlite), len(mysql), silver, indicadores}, mencionadas
    assert "con 4 tablas" in DOC_TEXTO and "7 tablas" in DOC_TEXTO
    assert cifras_con_patron(TODO, r"(\d+) índices secundarios") == [str(len(indices))]
    for nombre in sqlite + mysql:
        assert f"`{nombre}`" in DOC_TEXTO, nombre


def test_defectos_mutaciones_cobertura_casos_y_reglas_del_documento_son_los_medidos():
    registro = _leer("docs/validacion/registro_defectos.md")
    si, no = clasificar_defectos(registro)
    assert len(si) + len(no) == 25 and cifras_con_patron(DOC_TEXTO, r"\((\d+) defectos") == ["25"] and cifras_con_patron(ADR_TEXTO["adr-008_pruebas_sin_servidor_y_regresion.md"], r"\*\*(\d+) defectos\*\*") == ["25"]
    for texto in (DOC_TEXTO, ADR_TEXTO["adr-008_pruebas_sin_servidor_y_regresion.md"]):
        assert re.search(rf"(?i)para {len(si)} se demostró que su prueba de regresión falla sin la corrección", texto)
        assert defectos_sin_demostrar_en(texto, len(no)) == set(no)
    ev = _leer("docs/evidencias/modo_completo/EV-103_mutaciones_modo_completo.txt")
    total = sum(int(a) for a in re.findall(r"(?m)^Total: (\d+) de \d+ detectadas\.", ev))
    assert f"({total} en total)" in DOC_TEXTO
    assert cifras_con_patron(TODO, r"cobertura de `src/`(?:,| es) de (\d+ %)") == [valor_medido_de_cobertura()]
    casos = len(list(csv.DictReader((ROOT / "docs" / "validacion" / "matriz_casos_prueba.csv").open(encoding="utf-8", newline=""))))
    assert cifras_con_patron(DOC_TEXTO, r"\((\d+) casos\)") == [str(casos)]
    reglas = max(int(n) for n in re.findall(r"\bR(\d\d)\b", _leer("docs/silver/reglas_silver.md")))
    assert f"{reglas} reglas (R01 a R{reglas})" in DOC_TEXTO and f"R01 a R{reglas}" in ADR_TEXTO["adr-014_gold_lee_solo_silver.md"] and f"Silver aplica {reglas} reglas sobre ellos" in ADR_TEXTO["adr-014_gold_lee_solo_silver.md"]
    observaciones = len(re.findall(r"(?m)^\| \d+ \| «", _leer("docs/retroalimentacion/registro_de_cambios.md")))
    assert f"cinco observaciones" in DOC_TEXTO and observaciones == 5


def test_el_numero_de_adr_y_la_ultima_decision_del_documento_y_de_los_enlaces_son_los_reales():
    n = len(archivos_adr())
    assert n == 14
    assert cifras_con_patron(DOC_TEXTO, r"los (\d+) ADR") == [str(n)]
    filas = re.findall(r"(?m)^\| \[ADR-\d{3}\]\(adr/", DOC_TEXTO)
    assert len(filas) == n
    ultima = max(int(x) for x in re.findall(r"\*\*D(\d+) ·", DECISIONES) + re.findall(r"(?m)^\| D(\d+) \|", DECISIONES))
    assert cifras_con_patron(DOC_TEXTO, r"D1 a D(\d+)") == [str(ultima)]
    # los enlaces al documento: README, índice de docs, checklist, guía de evidencias y trazabilidad dicen el mismo número
    for ruta, patron in (("README.md", r"con (\d+) registros de decisión"), ("docs/README.md", r"(\d+) registros de decisión"), ("docs/checklist/estado_checklist.md", r"con (\d+) registros de decisión"),
                         ("docs/checklist/guia_de_evidencias.md", r"con (\d+) registros de decisión")):
        assert cifras_con_patron(_leer(ruta), patron) == [str(n)], ruta


def test_el_volumen_y_la_calidad_de_los_datos_del_documento_son_los_medidos():
    miles = _miles
    barrios = len(pd.read_csv(ROOT / "data" / "silver" / "silver_estrato_barrio.csv"))
    con_datos = int((~GOLD.sin_datos).sum())
    lineas = len(_leer("data/bronze/manifest.jsonl").splitlines())
    with (ROOT / RECURSOS).open(encoding="utf-8", newline="") as f:
        recursos = {r["magnitud"]: r["valor"] for r in csv.DictReader(f)}
    esperado = [f"{miles(len(GOLD))} ({miles(con_datos)} con datos satelitales)", f"{barrios}, más 23 filas resumen", f"{lineas} líneas de manifiesto",
                f"{_coma(recursos['tamano_data_mb'], 1)} MB", f"{_coma(recursos['tamano_base_sqlite_mb'], 1)} MB"]
    for e in esperado:
        assert e in DOC_TEXTO, e
    assert "5.655 en 7 tablas" in DOC_TEXTO and "5.655 filas" in _leer("docs/evidencias/modo_completo/EV-102_capturas_de_daniel.txt")
    assert round(float(recursos["tamano_data_mb"])) == 11 and "11 MB en total" in ADR_TEXTO["adr-001_bronze_crudo_inmutable.md"]
    dos = ADR_TEXTO["adr-002_llave_codigo_catastral.md"]
    k, e, nv, cp = REP["cobertura_llave"], REP["cobertura_estrato_valido"], REP["pct_nombre_validado"]["global"], REP["pct_coincide_poligono"]
    for esperado_adr in (f"{_coma(k['pct'] * 100, 3)} % ({miles(k['num'])} de {miles(k['den'])}", f"{_coma(e['pct'] * 100, 3)} %", f"{_coma(nv['pct'] * 100, 2)} %", f"{_coma(cp['pct'] * 100, 2)} %",
                         f"{_coma(100 - cp['pct'] * 100, 1)} %", f"{REP['huerfanos']['izquierda']} quedan como huérfanos a la izquierda"):
        assert esperado_adr in dos, esperado_adr
    assert "73 %" in dos and "solo el 73 %" in DECISIONES
    nueve = ADR_TEXTO["adr-009_fuentes_por_criterios_de_aceptacion.md"]
    assert f"{_coma(k['pct'] * 100, 2)} %" in nueve and f"({k['den'] - k['num']} sin coincidencia)" in nueve
    manifiesto = [json.loads(l) for l in _leer("data/bronze/manifest.jsonl").splitlines()]
    poligonos = [m["bytes"] for m in manifiesto if m["source_id"] == "poligonos_barrios"]
    csv_estrato = [m["bytes"] for m in manifiesto if m["source_id"] == "estrato_barrio"]
    catorce = ADR_TEXTO["adr-014_gold_lee_solo_silver.md"]
    todos_los_bytes = sorted({_miles(m["bytes"]) for m in manifiesto})   # las 8 líneas del manifiesto: tres páginas, dos conteos, el metadato, el CSV y el GeoJSON
    assert len(manifiesto) == 8 and set(cifras_con_patron(catorce, r"([\d.]+) bytes")) <= set(todos_los_bytes), "toda cifra de bytes es una medida del manifiesto"
    assert all(b in catorce for b in todos_los_bytes), "las 8 líneas del manifiesto están enumeradas con su tamaño"
    assert "342 polígonos" in catorce and "8 archivos crudos" in catorce


EV102_ET = "docs/evidencias/modo_completo/EV-102_capturas_de_daniel.txt"
TIEMPOS_DEL_DOCUMENTO = [
    ("2,9 s y 148 MB de pico (mediana de 3)", EV113, ["mediana 2,92 s y 148,4 MB"]),
    ("2,415 s frente a 0,715 s", RECURSOS, ["carga_a_mysql_fila_a_fila_mediana,2.415,", "carga_a_mysql_lote_2000_mediana,0.715,"]),
    ("de 3,6 a 13,9 ms", RECURSOS, ["latencia_api_sqlite_mediana_por_ruta,3.6 a 13.9,"]),
    ("de 4,8 a 126,9 ms", RECURSOS, ["latencia_api_mysql_mediana_por_ruta,4.8 a 126.9,"]),
    ("unos 160 MiB", RECURSOS, ["memoria_api_mas_panel_en_reposo,161,"]),
    ("1.970 MiB", RECURSOS, ["memoria_en_reposo_total_contenedores_de_airflow,1970,"]),
]


def test_los_tiempos_y_consumos_del_documento_estan_en_su_evidencia():
    assert tiempos_que_no_coinciden(DOC_TEXTO, TIEMPOS_DEL_DOCUMENTO, _leer) == []
    # toda aparición de una cifra de memoria es una medida (no basta con que la cifra correcta aparezca en otro lugar)
    for nombre, texto in [("documento", DOC_TEXTO)] + list(ADR_TEXTO.items()):
        assert set(re.findall(r"([\d.]+) MiB", texto)) <= {"1.970", "160"}, (nombre, set(re.findall(r"([\d.]+) MiB", texto)))
    adr = {"adr-003_almacenamiento_dual_sin_orm.md": [("0,715 s con lotes de 2.000 filas", RECURSOS, ["carga_a_mysql_lote_2000_mediana,0.715,"]), ("1,6 MB", RECURSOS, ["tamano_base_sqlite_mb,1.6,"])],
           "adr-004_historial_por_corrida_idempotente.md": [("0,715 s frente a 2,415 s", RECURSOS, ["carga_a_mysql_lote_2000_mediana,0.715,", "carga_a_mysql_fila_a_fila_mediana,2.415,"])],
           "adr-005_orquestacion_con_airflow.md": [("1.970 MiB", RECURSOS, ["memoria_en_reposo_total_contenedores_de_airflow,1970,"]), ("de 9 a 12 segundos (EV-064 y EV-100)", RECURSOS, ["duracion_dag_cuatro_tareas,9,"])],
           "adr-012_panel_solo_sobre_la_api.md": [("unos 160 MiB", RECURSOS, ["memoria_api_mas_panel_en_reposo,161,"])],
           "adr-013_dos_modos_de_instalacion.md": [("1.970 MiB", RECURSOS, ["memoria_en_reposo_total_contenedores_de_airflow,1970,"]), ("160 MiB", RECURSOS, ["memoria_api_mas_panel_en_reposo,161,"])]}
    for nombre, citas in adr.items():
        assert tiempos_que_no_coinciden(ADR_TEXTO[nombre], citas, _leer) == [], nombre
    assert "unos 12 s" in _leer("docs/evidencias/modo_completo/EV-100_guia_seguida_desde_un_zip_nuevo.txt").replace("en unos 12 s", "unos 12 s")


# ---------------------------------------------------------------- errores que el README ya corrigió
FRASES_PROHIBIDAS = ("cada uno con una prueba de regresión que falla sin su corrección", "seis contenedores", "se integra a `main`", "integra a `main`", "la única secreta", "única credencial",
                     "deja vacía la clave Fernet", "secreto JWT de ejemplo", "contraseña de ejemplo", "unas décimas", "Todo lo que afirmamos se puede comprobar", "no tratamos datos personales", "Ítem 7.3", "60 a 120 ms frente", "Avan" + "ce 2")   # la etiqueta del avance anterior se parte para que este archivo no se detecte a sí mismo


def test_el_documento_y_los_adr_no_repiten_errores_ya_corregidos_en_el_readme():
    assert frases_prohibidas_presentes(TODO, FRASES_PROHIBIDAS) == []
    assert barrio_norm_sin_aclarar(TODO) == []
    assert "siete contenedores" in DOC_TEXTO and "siete contenedores" in ADR_TEXTO["adr-005_orquestacion_con_airflow.md"]


def test_los_contenedores_las_ramas_y_los_secretos_del_documento_son_los_del_repositorio():
    compose = yaml.safe_load(_leer("orquestacion/docker-compose.yaml"))["services"]
    servicios = {n for n, s in compose.items() if "profiles" not in s and n != "airflow-init"}
    assert len(servicios) == 7
    ramas = set(re.findall(r"la rama `(\w+)`", DOC_TEXTO))
    assert ramas == {"desarrollo", "master"} and "No hay rama `main`" in DOC_TEXTO
    r = subprocess.run(["git", "for-each-ref", "--format=%(refname:short)", "refs/heads", "refs/remotes"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if (ROOT / ".git").exists() and r.returncode == 0:
        assert ramas <= {n.split("/", 1)[1] if n.startswith("origin/") else n for n in r.stdout.split()}
    seguridad = DOC_TEXTO.split("## 12. Seguridad y cumplimiento")[1].split("\n## ")[0]
    for pieza in ("clave Fernet", "secreto JWT", "contraseñas de la interfaz y de Postgres", "los exige desde el `.env` de Airflow"):
        assert pieza in seguridad, pieza
    assert "${FERNET_KEY:?" in _leer("orquestacion/docker-compose.yaml")
    assert "**Modificada por D57 y D92:**" in DECISIONES and "**Modificada por D106**" in DECISIONES


def test_los_enlaces_al_documento_existen_en_el_readme_el_indice_y_la_checklist():
    assert "[docs/arquitectura/arquitectura_del_sistema.md](docs/arquitectura/arquitectura_del_sistema.md)" in README and "[docs/arquitectura/adr/](docs/arquitectura/adr/)" in README
    assert README.index("arquitectura_del_sistema.md") > README.index("## 16. Decisiones de arquitectura") and README.index("arquitectura_del_sistema.md") < README.index("## 17. Contribución y estándares")
    assert "[arquitectura_del_sistema.md](arquitectura/arquitectura_del_sistema.md)" in _leer("docs/README.md") and "[adr/](arquitectura/adr/)" in _leer("docs/README.md")
    for ruta in ("docs/checklist/estado_checklist.md", "docs/checklist/guia_de_evidencias.md"):
        assert "docs/arquitectura/arquitectura_del_sistema.md" in _leer(ruta), ruta
    fila = next(l for l in _leer("docs/checklist/trazabilidad.csv").splitlines() if l.startswith("7.3,"))
    assert "docs/arquitectura/arquitectura_del_sistema.md" in fila and "tests/test_arquitectura_cifras.py" in fila and "tests/test_arquitectura_guardiana.py" in fila and "En curso" in fila
    assert "Borrador" in fila


# ---------------------------------------------------------------- pruebas negativas con textos sintéticos
def test_una_cifra_alterada_en_un_solo_lugar_se_detecta():
    assert cifras_de_pruebas("Hay **100 pruebas** y **99 pruebas**") == [99, 100]
    assert cifras_con_patron("Tiene 11 rutas GET y 12 rutas GET", r"(\d+) rutas GET") == ["11", "12"]
    assert cifras_con_patron("los 14 ADR y los 13 ADR", r"los (\d+) ADR") == ["13", "14"]


def test_una_lista_de_defectos_sin_demostrar_incompleta_o_con_otro_rango_se_detecta():
    base = "para los otros 3 no se demostró (DEF-003, DEF-010 y DEF-022 a DEF-023)"
    assert defectos_sin_demostrar_en(base, 3) == {"DEF-003", "DEF-010", "DEF-022", "DEF-023"}
    assert defectos_sin_demostrar_en(base.replace("DEF-003, ", ""), 3) != {"DEF-003", "DEF-010", "DEF-022", "DEF-023"}
    assert defectos_sin_demostrar_en(base.replace("DEF-023", "DEF-024"), 3) != {"DEF-003", "DEF-010", "DEF-022", "DEF-023"}
    assert defectos_sin_demostrar_en(base, 4) is None, "otro número declarado"


def test_las_frases_de_errores_corregidos_y_barrio_norm_sin_aclarar_se_detectan():
    assert frases_prohibidas_presentes("Hay seis contenedores y la única secreta es la de MySQL", FRASES_PROHIBIDAS) == ["seis contenedores", "la única secreta"]
    assert frases_prohibidas_presentes("Hay siete contenedores", FRASES_PROHIBIDAS) == []
    assert barrio_norm_sin_aclarar("La llave era `barrio_norm`.\n\nOtro párrafo.") != []
    assert barrio_norm_sin_aclarar("La llave era `barrio_norm`, modificada por D-FUENTES.") == []
    assert tiempos_que_no_coinciden("2,9 s", [("3,9 s", EV113, ["mediana 2,92 s"])], _leer), "una cita que no está en el documento"


# ---------------------------------------------------------------- correcciones de la revisión: latencias, filas de MySQL, reintentos, puertos, autoría y evidencias citadas
def tabla_de_latencias(texto):
    """{ruta: (mediana SQLite, mediana MySQL)} de la tabla de latencias de EV-032."""
    inicio = texto.index("| Ruta | SQLite mediana")
    filas = re.findall(r"(?m)^\| `([^`]+)` \| ([\d.]+) \| ([\d.]+) \| ([\d.]+) \| ([\d.]+) \|$", texto[inicio:])
    return {ruta: (float(a), float(c)) for ruta, a, _, c, _ in filas}


def test_las_latencias_del_documento_y_de_adr_010_son_las_de_ev_032():
    ev = _leer("docs/evidencias/almacenamiento/EV-032_api_mysql_vs_sqlite.txt")
    medianas = tabla_de_latencias(ev)
    assert len(medianas) == 17
    usan_almacen = {r: v for r, v in medianas.items() if r not in ("/fuentes", "/calidad")}
    sq, my = [v[0] for v in usan_almacen.values()], [v[1] for v in usan_almacen.values()]
    rango = lambda xs, f: f"{round(f(xs))}"   # noqa: E731
    adr = ADR_TEXTO["adr-010_api_de_solo_lectura_local.md"]
    assert f"de {rango(my, min)} a {rango(my, max)} ms con MySQL frente a {rango(sq, min)} a {rango(sq, max)} ms con SQLite" in adr
    m = re.search(r"Mediana de las medianas: SQLite ([\d.]+) ms y MySQL ([\d.]+) ms", ev)
    sqlite_mediana, mysql_mediana = m.group(1), m.group(2)
    assert f"{_coma(mysql_mediana, 1)} ms" in DOC_TEXTO and f"{_coma(sqlite_mediana, 1)} ms" in DOC_TEXTO
    par = f"{_coma(mysql_mediana, 1)} ms frente a {_coma(sqlite_mediana, 1)} ms"
    assert DOC_TEXTO.count(par) == 2, "el par de medianas aparece en los cuellos de botella y en la tabla de compromisos"
    assert f"mediana de medianas de {par} con SQLite" in DOC_TEXTO
    assert f"unos {round((float(mysql_mediana) - float(sqlite_mediana)) / 10) * 10} ms más por consulta con MySQL ({par}, EV-032)" in DOC_TEXTO
    assert f"{_coma(mysql_mediana, 1)} y {_coma(sqlite_mediana, 1)} ms" in adr and f"unos {round((float(mysql_mediana) - float(sqlite_mediana)) / 10) * 10} ms" in adr
    assert medianas["/fuentes"][0] < 10 and medianas["/fuentes"][1] < 10 and medianas["/calidad"][1] < 10, "las rutas que no usan el almacén responden en pocos milisegundos con ambos"
    assert "la diferencia de las demás se debe a que la API abre una conexión nueva" in ev, "EV-032 lo plantea como una lectura, no como una medición del costo de la conexión"


def test_la_nota_de_filas_de_mysql_suma_lo_medido_y_nombra_las_entradas_y_las_comunas():
    from pathlib import Path

    from src.load import relacional

    nota = DOC_TEXTO.split("**Nota sobre las filas de MySQL.**")[1].split("\n\n")[0]
    estrato = pd.read_csv(ROOT / "data" / "silver" / "silver_estrato_barrio.csv", dtype=str)
    datos = {"barrio_estrato": len(estrato), "construccion": len(GOLD), "kpi": len(pd.read_csv(ROOT / "data/gold/kpis_gold.csv")), "kpi_sensibilidad": len(pd.read_csv(ROOT / "data/gold/kpis_sensibilidad.csv"))}
    comunas = sorted({f"{int(c) // 100:02d}" for c in estrato.codigo_barrio} | set(GOLD.comuna.dropna().astype(str).str.zfill(2)))
    csvs, qr = relacional.entradas()
    archivos = [Path(r).name for r in csvs.values()] + [Path(qr).name]
    assert len(archivos) == 5 and sum(datos.values()) + len(comunas) + 1 + len(archivos) == 5655
    for tabla, n in datos.items():
        assert f"`{tabla}` {_miles(n)}" in nota, tabla
    assert f"las {_miles(sum(datos.values()))} filas de datos" in nota and f"más {len(comunas)} de `comuna`, 1 de `corrida` y {len(archivos)} de `corrida_archivo`" in nota
    for a in archivos:
        assert f"`{a}`" in nota, a
    assert "no archivos de Bronze" in nota
    adicionales = [c for c in comunas if int(c) > 22]
    assert all(f"{n:02d}" in comunas for n in range(1, 23)) and "01 a 22, " + ", ".join(adicionales[:-1]) + " y " + adicionales[-1] in nota
    analizadas = sorted(GOLD.comuna.dropna().astype(str).str.zfill(2).unique())
    assert len(analizadas) == 7 and "7 comunas (" + ", ".join(str(int(c)).zfill(2) for c in analizadas[:-1]) + " y " + analizadas[-1] + ")" in nota
    assert set(analizadas) <= set(comunas)
    assert "el repositorio no documenta qué son los códigos 51 a 56" in nota
    for fila in ("| Carga a MySQL de 5.622 filas de datos (las cuatro tablas de datos)",):
        assert fila in DOC_TEXTO
    assert "5.622 filas de datos" in ADR_TEXTO["adr-003_almacenamiento_dual_sin_orm.md"] and "5.622 filas de datos" in ADR_TEXTO["adr-004_historial_por_corrida_idempotente.md"]


def pausas_de_reintento(retardo, intentos):
    fmt = lambda v: f"{v:g}".replace(".", ",")   # noqa: E731
    return [fmt(retardo * i) for i in range(1, intentos + 1)]


def test_los_reintentos_y_la_espera_de_la_descarga_del_documento_son_los_de_config():
    from src.common import load_config

    h = load_config()["http"]
    p = pausas_de_reintento(h["request_delay_s"], h["retries"])
    assert f"hasta {h['retries']} intentos por petición" in DOC_TEXTO
    assert f"una pausa de {p[0]} s, {p[1]} s y {p[2]} s después de cada intento fallido" in DOC_TEXTO
    assert f"espera como máximo {h['timeout_s']} s por intento" in DOC_TEXTO and "no el tiempo total" in DOC_TEXTO
    codigo = _leer("src/extract/extract_api.py")
    assert 'timeout=h["timeout_s"]' in codigo and 'time.sleep(h["request_delay_s"] * intento)' in codigo and "r.status_code < 500" in codigo


def test_los_reintentos_calculados_y_la_cifra_de_espera_se_detectan_si_cambian():
    assert pausas_de_reintento(0.5, 3) == ["0,5", "1", "1,5"]
    assert pausas_de_reintento(1, 2) == ["1", "2"]


def test_los_puertos_y_flower_del_documento_estan_respaldados_por_los_compose_y_las_evidencias():
    compose = yaml.safe_load(_leer("orquestacion/docker-compose.yaml"))["services"]
    assert "Flower" in DOC_TEXTO and "flower" in compose and all(p.startswith("127.0.0.1:") for p in compose["flower"]["ports"])
    pma = yaml.safe_load(_leer("servicios/phpmyadmin/docker-compose.yaml"))["services"]
    assert all(p.startswith("127.0.0.1:") for s in pma.values() for p in s.get("ports", []))
    assert "def test_airflow_publica_todos_sus_puertos_solo_en_127_0_0_1" in _leer("tests/test_servicios_compose.py")
    evidencias_de_puertos = [
        ("api", "EV-016_respuestas_api"),
        ("endurecimiento", "EV-064_airflow_en_vivo"),
        ("servicios", "EV-085_phpmyadmin_en_vivo"),
        ("modo_completo", "EV-102_capturas_de_daniel"),
    ]
    for carpeta, nombre in evidencias_de_puertos:
        ev = f"{carpeta}/{nombre}.txt"
        assert f"evidencias/{ev}" in DOC_TEXTO and (ROOT / "docs" / "evidencias" / ev).is_file(), ev
        assert "127.0.0.1" in _leer(f"docs/evidencias/{ev}"), ev
    assert "no sabemos en qué interfaces escucha" in DOC_TEXTO and "no hay una comprobación de sockets en escucha" in DOC_TEXTO
    assert "no usan TLS configurado por el proyecto" in DOC_TEXTO and "ssl" not in _leer("src/load/conexion.py").lower()
    assert "MySQL escucha solo en" not in DOC_TEXTO


def autores_de(lista):
    return sorted(set(l.strip() for l in lista if l.strip()))


def test_si_todos_los_commits_son_de_una_persona_el_documento_lo_dice_y_si_no_lo_quita():
    frase = "Todos los commits del historial son de la misma persona"
    assert frase in DOC_TEXTO
    if not (ROOT / ".git").exists():
        return   # el zip no trae historial
    r = subprocess.run(["git", "log", "--format=%an"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode == 0:
        assert len(autores_de(r.stdout.splitlines())) == 1, "hay más de un autor: la fila de riesgo de concentración debe cambiar"


def test_el_detector_de_autores_distingue_una_persona_de_varias():
    assert autores_de(["Ana", "Ana", ""]) == ["Ana"]
    assert len(autores_de(["Ana", "Luis"])) == 2


def test_la_seccion_de_riesgos_y_la_hoja_de_ruta_dicen_lo_acordado_sobre_la_concentracion():
    fila = next(l for l in DOC_TEXTO.splitlines() if l.startswith("| Todos los commits del historial"))
    assert "| organizativo | alta | alta |" in fila and "la ejecución desde cero en otros equipos está pendiente de comprobar" in fila
    assert not re.search(r"\d+ commits", DOC_TEXTO), "ninguna cifra de commits"
    assert "aún no ejecutaron" not in DOC_TEXTO and "comprobar la ejecución desde cero en otros equipos" in DOC_TEXTO


def test_las_mutaciones_citadas_en_el_apartado_de_pruebas_son_las_de_ev_115():
    ev = _leer("docs/evidencias/arquitectura/EV-115_mutaciones_de_las_pruebas_de_arquitectura.txt")
    series = re.findall(r"(?m)^## .*?: (\d+) de (\d+) detectadas$", ev)
    assert len(series) >= 3
    detectadas, total = sum(int(a) for a, _ in series), sum(int(b) for _, b in series)
    assert detectadas == total
    assert f"[EV-115](../evidencias/arquitectura/EV-115_mutaciones_de_las_pruebas_de_arquitectura.txt)): {detectadas} de {total} detectadas" in DOC_TEXTO
    assert "@@" not in DOC_TEXTO


def test_los_hechos_citados_por_adr_007_y_adr_014_estan_en_el_registro_y_en_las_evidencias():
    registro = _leer("docs/validacion/registro_defectos.md")
    assert "3 celdas del decimal 12" in registro and "799 celdas de `indice_escombros`" in registro and "2026-11-13" in registro
    siete = ADR_TEXTO["adr-007_reproducibilidad_de_versiones.md"]
    assert "DEF-011, 2026-11-13" in siete and "No registramos la magnitud de las 799 celdas" in siete and "1e-9" in siete
    assert "No matching distribution found for numpy==2.5.4" in _leer("docs/evidencias/endurecimiento/EV-062_instalacion_desde_cero.txt") and "EV-062" in siete
    assert "Pillow" in _leer("docs/evidencias/readme/EV-113_primera_vez_y_suite_en_clon_y_zip.txt") and "el 2026-11-16, en el clon nuevo de EV-113" in siete
    assert "columnas vacías, en grados o sin uso en Gold" in _leer("docs/silver/reglas_silver.md")
    catorce = ADR_TEXTO["adr-014_gold_lee_solo_silver.md"]
    assert "columnas vacías, en grados o sin uso de la regla R10" in catorce and "geopandas y consulta por punto" in catorce
    assert "geopandas; consulta por punto" in DECISIONES and "D5 registró alternativas para la herramienta" in catorce
    assert "No se registraron alternativas.\n" in catorce


CLAUSULA_POR_CAPA = ("en Bronze vienen las columnas catastrales que publica la fuente, entre ellas identificadores de predio (`PREDIO`, `NUMEPRED` e `ID_PREDIO`); "
                     "Silver los descarta (regla R10) y Gold conserva las coordenadas del centroide de cada construcción")


def columnas_de_predio(cabecera):
    """Columnas de una cabecera CSV que identifican o describen un predio catastral."""
    return [c for c in cabecera.split(",") if re.search(r"(?i)pred|catast|manzana|terreno|matric", c)]


def test_la_clausula_por_capa_de_los_predios_del_documento_es_la_de_los_archivos():
    import json

    assert CLAUSULA_POR_CAPA in DOC_TEXTO, "sección 12"
    assert "Bronze trae columnas catastrales con identificadores de predio, que Silver descarta (regla R10), y Gold conserva las coordenadas del centroide de cada construcción" in DOC_TEXTO, "sección 3"
    assert "con su ubicación y las columnas catastrales" not in DOC_TEXTO, "la redacción anterior no dice en qué capa están"
    for capa in ("data/silver/silver_integrated.csv", "data/gold/gold_final.csv"):
        with open(ROOT / capa, encoding="utf-8") as f:
            cabecera = f.readline().strip()
        assert columnas_de_predio(cabecera) == [], f"{capa} conserva una columna de predio"
    assert {"lon", "lat"} <= set(GOLD.columns)
    pagina = sorted((ROOT / "data" / "bronze" / "api" / "edificaciones").glob("snap_*/page_0001.json"))[0]
    campos = {c["name"] for c in json.loads(pagina.read_text(encoding="utf-8"))["fields"]}
    assert {"PREDIO", "NUMEPRED", "ID_PREDIO"} <= campos


def test_el_detector_de_columnas_de_predio_del_documento_las_encuentra_y_no_inventa():
    assert columnas_de_predio("objectid,PREDIO,lon") == ["PREDIO"]
    assert columnas_de_predio("a,ID_PREDIO,NUMEPRED,b") == ["ID_PREDIO", "NUMEPRED"]
    assert columnas_de_predio("comuna,barrio,codigo_barrio,lon,lat") == []
