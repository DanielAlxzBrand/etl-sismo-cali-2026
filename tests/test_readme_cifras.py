"""Las cifras que el README afirma deben coincidir con lo que mide el repositorio hoy.

El README se escribe a mano (D106). Cada prueba extrae del texto la cifra que afirma y la compara con la medida: una cifra editada o desactualizada hace fallar la prueba.
Las cifras del análisis (indicadores, coberturas, población) se vigilan en `tests/test_resultados_cifras.py`.
"""
import os
import re
import subprocess
import sys
from collections import Counter

from src.common import ROOT

README = (ROOT / "README.md").read_text(encoding="utf-8").replace("−", "-")


def _recolectadas():
    """Pruebas por archivo según `pytest --collect-only` (funciones y métodos de clase)."""
    r = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"], cwd=ROOT, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"})
    return Counter(l.split("::")[0].split("/")[-1] for l in r.stdout.splitlines() if "::" in l)


def cifras_de_pruebas(texto):
    """Cifras que un texto afirma como total de pruebas: «**N pruebas**» y «N passed» (sin separador de miles)."""
    return sorted({int(n) for n in re.findall(r"\*\*(\d+) pruebas\*\*", texto)} | {int(n) for n in re.findall(r"\b(\d+) passed\b", texto)})


def cifras_de_rutas(texto):
    """Cifras que un texto afirma como número de rutas GET de la API: «N rutas GET»."""
    return sorted({int(n) for n in re.findall(r"\b(\d+) rutas GET\b", texto)})


def test_numero_de_pruebas_en_readme():
    n = sum(_recolectadas().values())
    assert n > 0
    afirmadas = cifras_de_pruebas(README)
    assert afirmadas == [n], f"el README afirma {afirmadas} y la recolección da {n}"
    assert f"**{n} pruebas**" in README and f"{n} passed" in README


def test_una_cifra_de_pruebas_editada_se_detecta():
    assert cifras_de_pruebas("Hay **100 pruebas** y `100 passed`") == [100]
    assert cifras_de_pruebas("Hay **100 pruebas** y `99 passed`") == [99, 100]
    assert cifras_de_pruebas("no dice nada") == []


def test_las_rutas_de_la_api_del_readme_coinciden_con_la_aplicacion():
    from src.api.app import app

    rutas = sorted({r.path for r in app.routes if getattr(r, "methods", None) and r.path not in ("/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc")})
    assert cifras_de_rutas(README) == [len(rutas)], (cifras_de_rutas(README), len(rutas))
    for ruta in rutas:
        assert f"`{ruta}`" in README, ruta


def test_una_cifra_de_rutas_editada_se_detecta():
    assert cifras_de_rutas("Tiene **11 rutas GET**") == [11]
    assert cifras_de_rutas("Tiene **12 rutas GET** y 11 rutas GET") == [11, 12]


def test_comandos_de_la_capa_de_servicio_en_el_readme():
    for frase in ("127.0.0.1", "python -m uvicorn src.api.app:app", "hallazgos: 0", "solo lectura"):
        assert frase in README, frase


def test_rutas_citadas_en_readme_existen():
    rutas = set(re.findall(r"`((?:docs|src|tests|scripts|notebooks|config|data)/[^`\s]*)`", README))
    rutas |= set(re.findall(r"\]\(((?:docs|src|tests)/[^)]+)\)", README))
    faltan = []
    for r in rutas:
        if any(c in r for c in "…*<>|") or r.endswith(("N.json", "…")) or "snap_" in r:
            continue
        if not (ROOT / r.split("#")[0].rstrip("/")).exists():
            faltan.append(r)
    assert faltan == []


def test_el_readme_cita_el_documento_de_resultados():
    assert "docs/gold/resultados.md" in README
    assert (ROOT / "docs" / "gold" / "resultados.md").is_file()


# --- una ruta citada con un nombre que no existe se detecta aunque la misma ruta aparezca bien escrita en otro lugar ---
RUTAS_QUE_NO_SON_DE_LA_API = ("/opt/", "/tmp/", "/entrypoint", "/usr/", "/var/", "/api/", "/execution/", "/docs", "/redoc", "/openapi.json")


def rutas_de_api_mal_citadas(texto, validas):
    """Fragmentos en línea que parecen una ruta de la API (empiezan por «/») y no son una ruta real ni una ruta conocida de otro servicio."""
    citadas = re.findall(r"`(/[a-z_][a-z_/{}.]*)`", texto)
    return sorted({c for c in citadas if c not in validas and not c.startswith(RUTAS_QUE_NO_SON_DE_LA_API)})


def test_ninguna_ruta_citada_en_el_readme_es_inexistente():
    from src.api.app import app

    validas = {r.path for r in app.routes if getattr(r, "methods", None)}
    assert rutas_de_api_mal_citadas(README, validas) == []


def test_una_ruta_mal_escrita_se_detecta_aunque_otra_aparicion_este_bien():
    validas = {"/llave/revision", "/kpis"}
    assert rutas_de_api_mal_citadas("`/llave/revision` y luego `/llave/revisar`", validas) == ["/llave/revisar"]
    assert rutas_de_api_mal_citadas("`/kpis` y `/opt/airflow/x` y `/docs`", validas) == []


# --- insignias: cada una dice lo que miden los archivos del repositorio ---
INSIGNIAS = ROOT / "docs" / "img" / "insignias"


def texto_de_insignia(ruta):
    """(etiqueta, valor) de una insignia SVG, leído de su `<title>`."""
    m = re.search(r"<title>([^<:]+): ([^<]+)</title>", ruta.read_text(encoding="utf-8"))
    return m.group(1), m.group(2)


def valor_medido_de_cobertura():
    """Porcentaje de cobertura de `src/` registrado en la evidencia de la medición (línea «Cobertura de src/: N %»)."""
    for ev in sorted((ROOT / "docs" / "evidencias" / "readme").glob("EV-1*_cobertura_de_src*.txt"), reverse=True):   # la medición más reciente primero
        m = re.search(r"(?m)^Cobertura de src/: (\d+ %)", ev.read_text(encoding="utf-8"))
        if m:
            return m.group(1)
    return None


def test_las_insignias_dicen_lo_que_miden_los_archivos_del_repositorio():
    esperadas = {
        "python.svg": ("Python", re.search(r"(?m)^# Python soportado: (\d+\.\d+)", (ROOT / "requirements.txt").read_text(encoding="utf-8")).group(1)),
        "airflow.svg": ("Airflow", re.search(r"(?m)^FROM apache/airflow:(\d+\.\d+\.\d+)", (ROOT / "orquestacion" / "Dockerfile").read_text(encoding="utf-8")).group(1)),
        "pruebas.svg": ("pruebas", str(sum(_recolectadas().values()))),
        "licencia.svg": ("licencia", (ROOT / "LICENSE").read_text(encoding="utf-8").splitlines()[0].replace(" License", "")),
        "madurez.svg": ("madurez", "MVP académico"),
        "mysql.svg": ("MySQL", "8.0"),
        "verificacion.svg": ("última verificación", re.search(r"(?m)^\| EV-100 \|.*\| (\d{4}-\d{2}-\d{2}) \| docs/evidencias/modo_completo/EV-100_", (ROOT / "docs" / "evidencias" / "manifiesto.md").read_text(encoding="utf-8")).group(1)),
    }
    for archivo, esperado in esperadas.items():
        assert texto_de_insignia(INSIGNIAS / archivo) == esperado, archivo
    assert "MySQL 8.0" in (ROOT / "docs" / "instalacion" / "modo_completo.md").read_text(encoding="utf-8")
    cobertura = INSIGNIAS / "cobertura.svg"
    if cobertura.exists():
        assert texto_de_insignia(cobertura) == ("cobertura de src", valor_medido_de_cobertura())


def test_una_insignia_desactualizada_se_detecta(tmp_path):
    from scripts.make_insignias import insignia
    f = tmp_path / "pruebas.svg"
    f.write_text(insignia("pruebas", "999999"), encoding="utf-8")
    assert texto_de_insignia(f) == ("pruebas", "999999") != ("pruebas", str(sum(_recolectadas().values())))


# --- el documento de atribución de datos coincide con el catálogo de fuentes ---
def test_el_documento_de_atribucion_dice_lo_que_declara_el_catalogo():
    import json

    doc = (ROOT / "docs" / "bronze" / "atribucion_y_terminos_de_datos.md").read_text(encoding="utf-8")
    catalogo = {f["id"]: f["licencia"].lower() for f in json.loads((ROOT / "docs" / "bronze" / "catalogo_fuentes.json").read_text(encoding="utf-8"))["fuentes"]}
    esperado = {"edificaciones": ("cc by 4.0", "CC BY 4.0"), "estrato_barrio": ("creative commons attribution share-alike", "Creative Commons Attribution Share-Alike"),
                "poligonos_barrios": ("no declarada", "No declarada"), "usgs": ("no declarada", "No declarada")}
    for fuente, (en_catalogo, en_documento) in esperado.items():
        assert en_catalogo in catalogo[fuente], fuente
        assert f"`{fuente}`" in doc and en_documento in doc, fuente
    assert "CC0" in doc and "más restrictiva" in doc and "por prudencia" in doc
    assert "no es asesoría jurídica" in doc.lower()


# --- el README real: cada cifra de sus secciones frente a lo que miden los archivos (D105) ---
def _medidas_del_repositorio():
    req = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    medidas = {m.group(1).lower(): m.group(2) for m in re.finditer(r"(?m)^([A-Za-z][\w.-]*)==([\d.]+)", req)}
    medidas["python"] = re.search(r"(?m)^# Python soportado: (\d+\.\d+)", req).group(1)
    medidas["airflow"] = re.search(r"(?m)^FROM apache/airflow:(\d+\.\d+\.\d+)", (ROOT / "orquestacion" / "Dockerfile").read_text(encoding="utf-8")).group(1)
    compose = (ROOT / "orquestacion" / "docker-compose.yaml").read_text(encoding="utf-8")
    medidas["postgres"] = re.search(r"image: postgres:(\d+(?:\.\d+)*)", compose).group(1)
    medidas["redis"] = re.search(r"image: redis:(\d+\.\d+)", compose).group(1)
    medidas["phpmyadmin"] = re.search(r"image: phpmyadmin:(\d+\.\d+\.\d+)", (ROOT / "servicios" / "phpmyadmin" / "docker-compose.yaml").read_text(encoding="utf-8")).group(1)
    assert "MySQL 8.0" in (ROOT / "docs" / "instalacion" / "modo_completo.md").read_text(encoding="utf-8")
    medidas["mysql"] = "8.0"
    return medidas


def versiones_afirmadas(texto):
    """{componente en minúsculas: versión} de las filas de la tabla del stack: «| `pandas` | 3.0.6 | ... |» o «| Airflow | 3.3.2 | ... |»."""
    return {n.lower(): v for n, v in re.findall(r"(?m)^\| `?([A-Za-z][\w +-]*?)`? \| (\d+(?:\.\d+)*) \|", texto)}


def test_las_versiones_del_stack_del_readme_son_las_de_los_archivos():
    afirmadas, medidas = versiones_afirmadas(README), _medidas_del_repositorio()
    for obligatorio in ("python", "pandas", "numpy", "fastapi", "streamlit", "pymysql", "airflow", "postgres", "redis", "phpmyadmin", "mysql"):
        assert obligatorio in afirmadas, obligatorio
    assert {n: (v, medidas.get(n)) for n, v in afirmadas.items() if medidas.get(n) != v} == {}


def test_una_version_editada_del_stack_se_detecta():
    medidas = _medidas_del_repositorio()
    editada = f"| `pandas` | 9.9.9 | x |\n| Airflow | {medidas['airflow']} | y |"
    assert versiones_afirmadas(editada) == {"pandas": "9.9.9", "airflow": medidas["airflow"]}
    assert versiones_afirmadas(editada)["pandas"] != medidas["pandas"]


def test_paginas_y_componentes_del_panel_en_readme():
    from src.panel import registro

    m = re.search(r"\*\*(\d+) páginas y (\d+) componentes\*\*", README)
    assert m and (int(m.group(1)), int(m.group(2))) == (len(registro.PAGINAS), len(registro.COMPONENTES))


def test_tablas_de_sqlite_y_de_mysql_en_readme():
    import sqlite3

    conn = sqlite3.connect((ROOT / "data" / "gold" / "etl_sismo.db").as_uri() + "?mode=ro", uri=True)
    try:
        sqlite = [f[0] for f in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    finally:
        conn.close()
    mysql = re.findall(r"CREATE TABLE IF NOT EXISTS (\w+)", (ROOT / "src" / "load" / "sql" / "esquema_mysql.sql").read_text(encoding="utf-8"))
    assert re.search(rf"\(`data/gold/etl_sismo\.db`\) tiene {len(sqlite)} tablas", README) and re.search(rf"MySQL tiene {len(mysql)} tablas", README)
    for nombre in sqlite + mysql:
        assert f"`{nombre}`" in README, nombre


def test_filas_y_conteos_del_pipeline_en_readme():
    import json

    import pandas as pd

    gold = pd.read_csv(ROOT / "data/gold/gold_final.csv")
    k = pd.read_csv(ROOT / "data/gold/kpis_gold.csv")
    s = pd.read_csv(ROOT / "data/gold/kpis_sensibilidad.csv")
    barrios = len(pd.read_csv(ROOT / "data/silver/silver_estrato_barrio.csv"))
    rep = json.loads((ROOT / "data/silver/quality_report.json").read_text(encoding="utf-8"))
    miles = lambda n: f"{n:,}".replace(",", ".")
    lineas_manifiesto = len((ROOT / "data/bronze/manifest.jsonl").read_text(encoding="utf-8").splitlines())
    esperadas = [
        f"`Salida: construcciones={len(gold)} barrios={barrios} integrado={len(gold)} | cobertura de llave={rep['cobertura_llave']['pct'] * 100:.4f}% (pasa)`",
        f"`Salida: gold_final={len(gold)} filas | kpis_gold={len(k)} filas ({k.kpi_id.nunique()} indicadores) | sensibilidades={len(s)} filas`",
        f"`kpis_gold.csv` tiene {len(k)} filas (K1 a K6) y `kpis_sensibilidad.csv` tiene {len(s)} (escenarios S0 a S5)",
        f"una fila por construcción ({miles(len(gold))})", f"({lineas_manifiesto} en total)",
    ]
    for e in esperadas:
        assert e in README, e
    # el registro imprime los números sin separador de miles: así salió en la consola de un clon nuevo y así está en el código
    assert '"Salida: construcciones=%s barrios=%s integrado=%s | cobertura de llave=%.4f%% (%s)' in (ROOT / "src" / "transform" / "integrate.py").read_text(encoding="utf-8")
    assert '"Salida: gold_final=%s filas | kpis_gold=%s filas (%s indicadores) | sensibilidades=%s filas"' in (ROOT / "src" / "transform" / "build_gold.py").read_text(encoding="utf-8")
    assert set(re.findall(r"\b(\d\.\d{3})\*{0,2} construcciones", README)) == {miles(len(gold))}


def test_reglas_de_silver_defectos_y_decisiones_en_readme():
    reglas = max(int(n) for n in re.findall(r"\bR(\d\d)\b", (ROOT / "docs" / "silver" / "reglas_silver.md").read_text(encoding="utf-8")))
    assert f"{reglas} reglas (R01 a R{reglas})" in README
    defectos = len(re.findall(r"(?m)^\| DEF-\d+", (ROOT / "docs" / "validacion" / "registro_defectos.md").read_text(encoding="utf-8")))
    assert f"**{defectos} defectos**" in README and f"DEF-{defectos:03d})" in README
    texto = (ROOT / "docs" / "DECISIONES.md").read_text(encoding="utf-8")
    ultima = max(int(n) for n in re.findall(r"\*\*D(\d+) ·", texto) + re.findall(r"(?m)^\| D(\d+) \|", texto))
    assert f"(D1 a D{ultima})" in README
    assert set(re.findall(r"\(D1 a D(\d+)\)", README)) == {str(ultima)}


def test_las_mutaciones_del_readme_son_las_registradas_en_ev_103():
    ev = (ROOT / "docs" / "evidencias" / "modo_completo" / "EV-103_mutaciones_modo_completo.txt").read_text(encoding="utf-8")
    tablas = [(int(a), int(b)) for a, b in re.findall(r"(?m)^Total: (\d+) de (\d+) detectadas\.", ev)]
    assert tablas and all(a == b for a, b in tablas)
    total = sum(a for a, _ in tablas)
    assert f"Resultado: {total} mutaciones en total, todas detectadas." in ev
    assert set(re.findall(r"registra (\d+) mutaciones en total", README)) == {str(total)}
    assert "no hay un comando único que las repita" in README, "no se presentan como reproducibles"
    # la descomposición por parte: cada fila de la tabla del README es una parte de la evidencia con su total
    partes = re.findall(r"(?m)^## Parte (\d+) · ", ev)
    assert [int(p) for p in partes] == list(range(1, len(tablas) + 1)), "una tabla de totales por parte de la evidencia"
    for numero, (detectadas, _) in zip(partes, tablas):
        assert re.search(rf"(?m)^\| Parte {numero} \| .+ \| {detectadas} \|$", README), (numero, detectadas)
    assert re.search(rf"(?m)^\| Total \| .+ \| {total} \|$", README)
    assert len(re.findall(r"(?m)^\| Parte \d+ \|", README)) == len(partes), "una parte de más o de menos en el README"


def test_la_cobertura_del_readme_es_la_de_la_medicion_mas_reciente():
    assert set(re.findall(r"(\d+ %) de las líneas de `src/`", README)) == {valor_medido_de_cobertura()}
    reciente = sorted((ROOT / "docs" / "evidencias" / "readme").glob("EV-1*_cobertura_de_src*.txt"))[-1].name
    assert reciente in README, "el README cita la evidencia de cobertura más reciente"


# --- los tiempos y consumos que el README cita están en la evidencia que dice como origen ---
EV100 = "docs/evidencias/modo_completo/EV-100_guia_seguida_desde_un_zip_nuevo.txt"
RECURSOS = "docs/finanzas/recursos_medidos.csv"
EV113 = "docs/evidencias/readme/EV-113_primera_vez_y_suite_en_clon_y_zip.txt"
EV121 = "docs/evidencias/readme/EV-121_tiempos_de_la_ejecucion_sobre_el_zip.txt"
TIEMPOS_CITADOS = [
    ("251 s", EV100, ["instalación de requirements.txt y pip check en 251 s"]),
    ("unos 12 s", EV100, ["terminaron en success en unos 12 s"]),
    ("| 9 s | EV-121 |", EV121, ["| docker compose build de Airflow | 9 s, código 0 |"]),
    ("| 112 s | EV-121 |", EV121, ["| docker compose up airflow-init | 112 s, código 0 |"]),
    ("| 261 s (con la descarga de imágenes) |", EV121, ["| docker compose up -d de Airflow (con descarga de imágenes) | 261 s, código 0 |"]),
    ("| 34 s la primera corrida", EV121, ["| 34 s (de 20:07:39 a 20:08:13) en success |"]),
    ("377 s (la última medición, de punta a punta con el entorno nuevo)", EV121, ["| 377 s, código 0 |"]),
    ("773 s con 1.466 pruebas", EV121, ["| 773 s |"]),
    ("unos 455 s con 1.466 pruebas", EV121, ["| 454,86 s |"]),
    ("288 s en [EV-083]", "docs/evidencias/servicios/EV-083_suite_sin_utf8_antes.txt", ["288"]),
    ("311 s en [EV-113]", EV113, ["| Entorno virtual | py -3.13 -m venv .venv | 13,9 s |", "python -m pip install -r requirements.txt | 296,8 s, código 0"]),
    ("9,6 s la primera vez; mediana de 3 repeticiones: 4,7 s y 149 MB de pico (en 2026-11-16: 10,3 s, y 2,9 s y 148 MB)", EV113, ["python main.py --stage all | 9,63 s, código 0", "mediana 4,7 s y 149 MB", "python main.py --stage all | 10,32 s, código 0", "mediana 2,92 s y 148,4 MB"]),
    ("4,7 s y 149 MB de pico (mediana de 3 repeticiones en un clon nuevo)", EV113, ["mediana 4,7 s y 149 MB"]),
    ("de 343 s a 409 s con 1.330 pruebas y de 323 a 452 MiB de pico", EV113, ["1330 passed, 0 omitidas, 1 aviso, en 343,00 s", "pico 323 MiB (185 procesos)", "1330 passed y 0 omitidas en 408,99 s", "pico 452 MiB (189 procesos)"]),
    ("de 267 s a 358 s con 1.329 pruebas y 1 omitida (EV-113)", EV113, ["1329 passed y 1 omitida en 267,30 s", "test_secretos.py:44", "1329 passed y 1 omitida en 357,82 s"]),
    ("la API responde a los 4,5 s y el panel a los 6,8 s (en 2026-11-16: 2,2 s y 5,4 s)", EV113, ["200 a los 4,5 s", "200 a los 6,8 s", "200 a los 2,2 s", "200 a los 5,4 s"]),
    ("de 3,6 a 13,9 ms", RECURSOS, ["latencia_api_sqlite_mediana_por_ruta,3.6 a 13.9,"]),
    ("2,415 s frente a 0,715 s", RECURSOS, ["carga_a_mysql_fila_a_fila_mediana,2.415,", "carga_a_mysql_lote_2000_mediana,0.715,"]),
    ("unos 160 MiB", RECURSOS, ["memoria_api_mas_panel_en_reposo,161,"]),
    ("1.970 MiB", RECURSOS, ["memoria_en_reposo_total_contenedores_de_airflow,1970,"]),
    ("| 33 MiB |", RECURSOS, ["memoria_en_reposo_phpmyadmin,33,"]),
]


def tiempos_que_no_coinciden(texto, citados, leer):
    """Citas del README que no están en su evidencia: lista de (cita, archivo, fragmento que falta)."""
    faltan = []
    for cita, archivo, fragmentos in citados:
        if cita not in texto:
            faltan.append((cita, "README", cita))
        for f in fragmentos:
            if f not in leer(archivo):
                faltan.append((cita, archivo, f))
    return faltan


def _leer(ruta):
    return (ROOT / ruta).read_text(encoding="utf-8").replace("\r\n", "\n")


def test_los_tiempos_del_readme_estan_en_su_evidencia():
    assert tiempos_que_no_coinciden(README, TIEMPOS_CITADOS, _leer) == []


def test_un_tiempo_editado_del_readme_se_detecta():
    editado = README.replace("| 112 s | EV-121 |", "| 11 s | EV-121 |", 1)
    assert tiempos_que_no_coinciden(editado, TIEMPOS_CITADOS, _leer), "un tiempo cambiado en el README"
    otros = [(c, a, ["segundos: 99.9"]) if c == "| 112 s | EV-121 |" else (c, a, f) for c, a, f in TIEMPOS_CITADOS]
    assert tiempos_que_no_coinciden(README, otros, _leer), "una evidencia que no dice lo que el README cita"


# --- el resumen, los tres recuadros y la línea de sesiones ---
def test_el_resumen_del_readme_usa_las_cifras_de_k2():
    from tests.test_resultados_cifras import KP, _pp, _redondeo

    tasas = {g: _redondeo(KP[KP.grupo == g].iloc[0].valor, 2) + " %" for g in ("estratos_3-5", "estratos_1-2")}
    diferencia = _pp(KP[KP.grupo == "diferencia_3-5_menos_1-2"].iloc[0].valor)
    assert f"({tasas['estratos_3-5']} frente a {tasas['estratos_1-2']}; diferencia {diferencia} puntos porcentuales)" in README
    assert set(re.findall(r"diferencia ([+-]?\d+,\d+) p", README)) == {diferencia}


def test_los_tres_recuadros_del_readme_son_los_del_documento_de_resultados():
    from tests.test_resultados_cifras import RESULTADOS, _bloque

    for titulo in ("Alcance temporal", "Población analizada", "Indicador satelital frente a evaluación estructural"):
        assert _bloque(README, titulo).strip() == _bloque(RESULTADOS, titulo).strip(), titulo


def hay_sesiones_reales(carpeta):
    """True si algún registro de sesiones de `carpeta` (sin las plantillas) trae una fila con origen = real."""
    import csv

    for ruta in sorted(carpeta.glob("*.csv")):
        if ruta.name.startswith("plantilla_"):
            continue
        with ruta.open(encoding="utf-8", newline="") as f:
            if any((fila.get("origen") or "").strip() == "real" for fila in csv.DictReader(f)):
                return True
    return False


def problemas_de_sesiones(texto, hay):
    """Lo que el texto dice de las sesiones con personas usuarias debe coincidir con el repositorio en TODOS sus lugares: si no hay registros reales, toda mención de «sesiones reales»
    es «sin sesiones reales» (al menos en la descripción, en la tabla de estado y en su nota) y se dice que aún no existen; si los hay, ninguna de esas frases puede quedar."""
    n_todas, n_sin = len(re.findall(r"sesiones reales", texto)), len(re.findall(r"sin sesiones reales", texto))
    aun_no_existen = "sesiones con personas usuarias aún no existen" in texto
    if not hay:
        return [] if (n_todas == n_sin and n_sin >= 3 and aun_no_existen) else ["el texto no dice en todos sus lugares que aún no hay sesiones reales"]
    return [] if (n_sin == 0 and not aun_no_existen) else ["el texto sigue diciendo que no hay sesiones reales y ya hay registros"]


def test_la_linea_de_sesiones_reales_dice_lo_que_hay_en_el_repositorio():
    hay = hay_sesiones_reales(ROOT / "docs" / "usuarios" / "sesiones_reales")
    assert problemas_de_sesiones(README, hay) == [], "el README debe decir «aún sin sesiones reales» en todos sus lugares si y solo si no hay registros reales"


def test_una_mencion_desactualizada_de_las_sesiones_se_detecta_en_cualquier_lugar():
    assert problemas_de_sesiones(README, True), "hay registros reales y el README dice lo contrario"
    una_sola = README.replace("**aún sin sesiones reales**", "**con sesiones reales**", 1)
    assert problemas_de_sesiones(una_sola, False), "una sola mención cambiada"
    otra = README.replace("Las sesiones con personas usuarias aún no existen", "Las sesiones con personas usuarias ya existen", 1)
    assert problemas_de_sesiones(otra, False), "la frase de que las sesiones aún no existen cambiada"
    sin_el_parrafo = README.replace("**Sesiones y retención.** Las sesiones con personas usuarias aún no existen", "**Sesiones y retención.** Las sesiones con personas usuarias están por hacerse", 1)
    assert problemas_de_sesiones(sin_el_parrafo, False), "el párrafo de sesiones y retención reescrito sin la frase"
    assert "**Datos de personas.** En ninguna capa hay nombres, documentos ni datos de contacto de personas." in README


def test_la_deteccion_de_sesiones_reales_distingue_plantillas_y_registros(tmp_path):
    (tmp_path / "plantilla_registro.csv").write_text("participante,origen\nP01,real\n", encoding="utf-8")
    assert not hay_sesiones_reales(tmp_path), "una plantilla no cuenta"
    (tmp_path / "registro.csv").write_text("participante,origen\nP01,simulado\n", encoding="utf-8")
    assert not hay_sesiones_reales(tmp_path), "una fila simulada no cuenta"
    (tmp_path / "registro.csv").write_text("participante,origen\nP01,real\n", encoding="utf-8")
    assert hay_sesiones_reales(tmp_path)


def test_la_seccion_de_contacto_nombra_a_las_tres_personas_con_su_responsabilidad():
    seccion = README.split("## 19. Contacto y responsables")[1].split("\n## ")[0]
    roles = {"Daniel Alexander Brand García": "Orquestador y responsable general del proyecto",
             "Diego Fernando Gordillo Londoño": "Responsable del protocolo y del análisis de las sesiones con personas usuarias",
             "Jhoan Sebastián Castellanos Mayor": "Responsable de la revisión y el mantenimiento de la documentación, y del guion y la grabación de la demostración"}
    for persona, rol in roles.items():
        assert re.search(rf"(?m)^\| {persona} \| {re.escape(rol)}", seccion), persona
    assert "@" not in seccion and "no describe quién hizo cada parte hasta hoy" in seccion
    assert "https://github.com/DanielAlxzBrand/etl-sismo-cali-2026/issues" in seccion and "por ahora es privado" in seccion, "el canal de contacto son los issues del repositorio"


def test_todo_lo_que_el_readme_enlaza_viaja_en_el_zip():
    from tests.test_criterio_de_texto import make_dist

    en_el_zip = {p.relative_to(ROOT).as_posix() for p in make_dist.listar(ROOT)}
    destinos = {d.split("#")[0] for d in re.findall(r"\]\(([^)\s]+)\)", re.sub(r"(?s)```.*?```", "", README)) if not d.startswith(("http://", "https://", "#"))}
    assert destinos and sorted(d for d in destinos if d not in en_el_zip and not (d.endswith("/") and any(z.startswith(d) for z in en_el_zip))) == []


# --- ronda de revisión: variables de entorno, umbrales, defectos, contenedores, índices, árbol, cabecera, fechas, ramas y escalado ---
def nombres_de_env_example():
    return [l.split("=")[0] for l in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines() if re.match(r"^[A-Z][A-Z0-9_]*=", l)]


def variables_de_la_tabla(texto):
    """Filas de la tabla de variables del README: (nombre, para qué sirve, obligatoria, modo)."""
    return re.findall(r"(?m)^\| `([A-Z][A-Z0-9_]+)` \| (.+?) \| (.+?) \| (.+?) \|$", texto)


def variables_que_no_coinciden(texto, esperadas):
    """(faltan, sobran, con_valor): nombres de `.env.example` que la tabla no tiene, nombres que sobran y filas que parecen traer un valor."""
    filas = variables_de_la_tabla(texto)
    nombres = [f[0] for f in filas]
    con_valor = [f[0] for f in filas if "=" in " ".join(f)]
    return [n for n in esperadas if n not in nombres], [n for n in nombres if n not in esperadas], con_valor


def test_la_tabla_de_variables_coincide_con_env_example():
    esperadas = nombres_de_env_example()
    assert len(esperadas) == 12 and "sus 12 variables" in README
    assert variables_que_no_coinciden(README, esperadas) == ([], [], [])
    assert [f[0] for f in variables_de_la_tabla(README)] == esperadas, "el mismo orden que el archivo"


def test_una_variable_que_falta_sobra_o_trae_valor_se_detecta():
    esperadas = ["A_UNO", "B_DOS"]
    assert variables_que_no_coinciden("| `A_UNO` | x | no | y |", esperadas) == (["B_DOS"], [], [])
    assert variables_que_no_coinciden("| `A_UNO` | x | no | y |\n| `B_DOS` | z | no | y |\n| `C_TRES` | z | no | y |", esperadas) == ([], ["C_TRES"], [])
    assert variables_que_no_coinciden("| `A_UNO` | x | no | y |\n| `B_DOS` | clave=abc | no | y |", esperadas)[2] == ["B_DOS"]


def umbrales_afirmados(texto):
    """Filas «| `seccion.clave` | valor | ... |» de la tabla de umbrales: lista de (sección, clave, valor)."""
    return [(s, k, float(v)) for s, k, v in re.findall(r"(?m)^\| `(\w+)\.(\w+)` \| ([\d.]+) \|", texto)]


def umbrales_que_no_coinciden(texto, cfg):
    return [(s, k, v, cfg.get(s, {}).get(k)) for s, k, v in umbrales_afirmados(texto) if cfg.get(s, {}).get(k) != v]


def test_los_umbrales_del_readme_son_los_de_config():
    from src.common import load_config

    cfg = load_config()
    claves = {k for _, k, _ in umbrales_afirmados(README)}
    assert {"join_coverage_min", "gold_min_rows", "min_edificios_por_barrio", "muestra_baja_severos"} <= claves
    assert umbrales_que_no_coinciden(README, cfg) == []


def test_un_umbral_editado_se_detecta():
    from src.common import load_config

    cfg = load_config()
    assert umbrales_que_no_coinciden("| `thresholds.gold_min_rows` | 201 | x |", cfg) == [("thresholds", "gold_min_rows", 201.0, 200)]
    assert umbrales_que_no_coinciden("| `thresholds.inexistente` | 1 | x |", cfg), "un parámetro que no existe"


def test_lo_que_el_readme_dice_que_pasa_al_incumplir_un_umbral_esta_en_el_codigo():
    integrate = (ROOT / "src" / "transform" / "integrate.py").read_text(encoding="utf-8")
    gold = (ROOT / "src" / "transform" / "build_gold.py").read_text(encoding="utf-8")
    assert '"no pasa"' in integrate and "umbral + 0.05" in integrate and "log.warning(\"cobertura de llave" in integrate
    assert 'assert len(gold) >= cfg["thresholds"]["gold_min_rows"], "Gold por debajo del mínimo"' in gold
    assert "b.n >= min_n" in gold and "log.warning(\"muestra baja" in gold
    assert "def test_cobertura_join_supera_umbral" in (ROOT / "tests" / "test_quality.py").read_text(encoding="utf-8")
    for frase in ("`resultado_umbral: no pasa`", "a menos de 0,05 del umbral", "«Gold por debajo del mínimo»", "deja fuera de K4"):
        assert frase in README, frase


def clasificar_defectos(registro):
    """(con_regresion_demostrada, sin_demostrar): identificadores de DEF cuya última columna empieza por «Sí» y los demás."""
    si, no = [], []
    for linea in registro.splitlines():
        m = re.match(r"\| (DEF-\d+) \|", linea)
        if m:
            columnas = [c.strip() for c in linea.strip().strip("|").split("|")]
            (si if columnas[6].startswith("Sí") else no).append(m.group(1))
    return si, no


def defectos_declarados_sin_demostrar(texto, n):
    """Identificadores que el texto declara sin demostración tras «Para los otros N no se demostró (...)», con rangos «DEF-022 a DEF-025»."""
    m = re.search(rf"Para los otros {n} no se demostró \(([^)]+)\)", texto)
    if not m:
        return None
    ids = set(re.findall(r"DEF-\d+", re.sub(r"DEF-(\d+) a DEF-(\d+)", "", m.group(1))))
    for a, b in re.findall(r"DEF-(\d+) a DEF-(\d+)", m.group(1)):
        ids |= {f"DEF-{i:03d}" for i in range(int(a), int(b) + 1)}
    return ids


def test_los_defectos_con_regresion_demostrada_y_los_que_no_son_los_del_registro():
    si, no = clasificar_defectos((ROOT / "docs" / "validacion" / "registro_defectos.md").read_text(encoding="utf-8"))
    assert len(si) + len(no) == 25 and "DEF-022" in no and "DEF-025" in no, "DEF-022 a DEF-025 no se reintroducen por reemplazo de texto"
    assert f"Para {len(si)} se demostró que su prueba de regresión falla sin la corrección" in README
    assert defectos_declarados_sin_demostrar(README, len(no)) == set(no)
    assert "cada uno con una prueba de regresión que falla sin su corrección" not in README


def test_una_lista_de_defectos_sin_demostrar_incompleta_se_detecta():
    si, no = clasificar_defectos((ROOT / "docs" / "validacion" / "registro_defectos.md").read_text(encoding="utf-8"))
    incompleto = README.replace("DEF-006, ", "", 1)
    assert defectos_declarados_sin_demostrar(incompleto, len(no)) != set(no)
    assert defectos_declarados_sin_demostrar(README.replace("DEF-022 a DEF-025", "DEF-022 a DEF-024"), len(no)) != set(no)
    assert clasificar_defectos("| DEF-001 | a | b | c | d | e | Sí (EV-036) |\n| DEF-002 | a | b | c | d | e | No aplica |") == (["DEF-001"], ["DEF-002"])


def test_los_contenedores_de_airflow_en_reposo_son_los_que_levanta_el_compose():
    import csv

    import yaml

    servicios = {n for n, s in yaml.safe_load((ROOT / "orquestacion" / "docker-compose.yaml").read_text(encoding="utf-8"))["services"].items()
                 if "profiles" not in s and n != "airflow-init"}
    with (ROOT / "docs" / "finanzas" / "recursos_medidos.csv").open(encoding="utf-8", newline="") as f:
        filas = {r["magnitud"]: float(r["valor"]) for r in csv.DictReader(f) if r["magnitud"].startswith("memoria_en_reposo_")}
    medidos = {n.removeprefix("memoria_en_reposo_") for n in filas} - {"total_contenedores_de_airflow", "phpmyadmin"}
    assert medidos == servicios and len(servicios) == 7
    assert sum(filas[f"memoria_en_reposo_{n}"] for n in servicios) == filas["memoria_en_reposo_total_contenedores_de_airflow"]
    for texto in (README, (ROOT / "docs" / "instalacion" / "README.md").read_text(encoding="utf-8")):
        assert "siete contenedores" in texto and "seis contenedores" not in texto
    for n in servicios:
        assert n.removeprefix("airflow-").lower() in README.lower(), n


def test_los_indices_de_mysql_del_readme_son_los_del_esquema():
    indices = re.findall(r"(?m)^\s+KEY (ix_\w+)", (ROOT / "src" / "load" / "sql" / "esquema_mysql.sql").read_text(encoding="utf-8"))
    assert f"define {len(indices)} índices secundarios" in README
    for citado in re.findall(r"`(ix_\w+)`", README):
        assert citado in indices, citado


def test_las_pruebas_omitidas_en_el_zip_del_readme_son_las_de_la_guia_de_instalacion():
    guia = (ROOT / "docs" / "instalacion" / "README.md").read_text(encoding="utf-8")
    assert re.search(r"\| clon con Git \| 0 \|", guia) and re.search(r"\| zip descomprimido, con Git instalado \| \*\*1\*\* \|", guia)
    assert re.search(r"\| zip descomprimido, sin Git \(o clon sin Git\) \| \*\*10\*\* \|", guia)
    assert "no se omite ninguna; en el zip descomprimido con Git se omite 1" in README and "sin Git se omiten 10" in README


# --- el árbol de directorios ---
def rutas_del_arbol(texto):
    """Rutas del primer bloque de código que dibuja el árbol (líneas «├── nombre» y «└── nombre»)."""
    bloque = re.search(r"(?s)```\n\.\n(.*?)```", texto).group(1)
    pila, rutas = [], []
    for linea in bloque.splitlines():
        m = re.match(r"^((?:│   |    )*)(?:├── |└── )(\S+)", linea)
        assert m, f"línea del árbol que no se entiende: {linea!r}"
        nivel, nombre = len(m.group(1)) // 4, m.group(2)
        rutas.append("/".join(pila[:nivel] + [nombre.rstrip("/")]))
        if nombre.endswith("/"):
            pila = pila[:nivel] + [nombre.rstrip("/")]
    return rutas


def test_toda_ruta_del_arbol_existe_y_toda_carpeta_principal_esta_en_el_arbol():
    rutas = rutas_del_arbol(README)
    assert [r for r in rutas if not (ROOT / r).exists()] == []
    ignoradas = {"dist", "logs", "__pycache__"}
    for base in ("", "src", "scripts", "docs", "tests"):
        carpeta = ROOT / base if base else ROOT
        for d in sorted(p for p in carpeta.iterdir() if p.is_dir() and not p.name.startswith(".") and p.name not in ignoradas):
            if base == "tests" or (base == "" and d.name == "tests"):
                continue
            ruta = f"{base}/{d.name}" if base else d.name
            assert ruta in rutas, f"falta en el árbol del README: {ruta}"


def test_una_ruta_inexistente_en_el_arbol_se_detecta():
    texto = "```\n.\n├── src/\n│   ├── api/\n│   └── no_existe/\n└── main.py\n```\n"
    assert rutas_del_arbol(texto) == ["src", "src/api", "src/no_existe", "main.py"]
    assert [r for r in rutas_del_arbol(texto) if not (ROOT / r).exists()] == ["src/no_existe"]


# --- la cabecera: insignias bajo el título, enlaces rápidos y la fecha de la última verificación ---
def fecha_de_ev_100():
    m = re.search(r"(?m)^\| EV-100 \|.*\| (\d{4}-\d{2}-\d{2}) \| docs/evidencias/modo_completo/EV-100_", (ROOT / "docs" / "evidencias" / "manifiesto.md").read_text(encoding="utf-8"))
    return m.group(1)


def test_las_insignias_van_bajo_el_titulo_y_hay_enlaces_rapidos():
    cabecera = README.split("\n## ")[0]
    for nombre in ("python", "airflow", "mysql", "pruebas", "cobertura", "licencia", "madurez", "verificacion"):
        assert f"](docs/img/insignias/{nombre}.svg)" in cabecera, nombre
    assert "## 2. Insignias" in README and "](docs/img/insignias/" not in README.split("## 2. Insignias")[1], "las insignias no se repiten en la sección 2"
    for destino in ("docs/README.md", "docs/gold/resultados.md", "data/", "docs/instalacion/README.md"):
        assert f"]({destino})" in cabecera, destino
    assert "no hay integración continua" in README and "pipeline passing" not in README.lower()


def test_una_insignia_fuera_de_la_cabecera_se_detecta():
    movido = README.replace(" ![Última verificación](docs/img/insignias/verificacion.svg)", "", 1).replace("## 2. Insignias\n", "## 2. Insignias\n![Última verificación](docs/img/insignias/verificacion.svg)\n", 1)
    assert "](docs/img/insignias/verificacion.svg)" not in movido.split("\n## ")[0]
    assert "](docs/img/insignias/" in movido.split("## 2. Insignias")[1]


def test_la_insignia_de_ultima_verificacion_es_la_fecha_de_ev_100():
    fecha = fecha_de_ev_100()
    assert texto_de_insignia(INSIGNIAS / "verificacion.svg") == ("última verificación", fecha)
    assert f"la última prueba completa desde un zip nuevo es del {fecha}" in README
    assert "EV-100" in README.split("## 2. Insignias")[1].split("## 3.")[0]


def test_una_insignia_de_verificacion_con_otra_fecha_se_detecta(tmp_path):
    from scripts.make_insignias import insignia

    f = tmp_path / "verificacion.svg"
    f.write_text(insignia("última verificación", "2026-01-01"), encoding="utf-8")
    assert texto_de_insignia(f) != ("última verificación", fecha_de_ev_100())


# --- fechas, ramas y escalado ---
def test_las_fechas_de_descarga_y_de_corte_del_readme_son_las_del_manifiesto_y_de_config():
    import json
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from src.common import load_config

    lineas = [json.loads(l) for l in (ROOT / "data" / "bronze" / "manifest.jsonl").read_text(encoding="utf-8").splitlines()]
    fechas = {datetime.fromisoformat(l["fetched_at_utc"].replace("Z", "+00:00")).astimezone(ZoneInfo("America/Bogota")).date().isoformat() for l in lineas}
    assert len(fechas) == 1
    assert f"descargada el {next(iter(fechas))} (hora de Bogotá)" in README
    assert f"última edición de la capa ({load_config()['fechas']['fecha_edicion_capa']})" in README


def test_las_ramas_citadas_en_el_readme_existen_en_el_repositorio():
    citadas = set(re.findall(r"la rama `(\w+)`", README))
    assert citadas == {"desarrollo", "master"} and "integra a `main`" not in README
    if not (ROOT / ".git").exists():
        return   # el zip no trae historial: sin repositorio no hay ramas que comprobar
    # en un clon solo la rama activa es local y las demás son ramas de seguimiento («origin/master»): se aceptan las dos
    r = subprocess.run(["git", "for-each-ref", "--format=%(refname:short)", "refs/heads", "refs/remotes"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode == 0:
        ramas = {n.split("/", 1)[1] if n.startswith("origin/") else n for n in r.stdout.split()}
        assert citadas <= ramas, (citadas, ramas)


def test_la_ruta_de_escalado_asigna_cada_tema_a_su_responsable():
    seccion = README.split("## 19. Contacto y responsables")[1].split("\n## ")[0]
    esperado = [("Preguntas generales y técnicas", "Daniel Alexander Brand García"), ("Sesiones con personas usuarias", "Diego Fernando Gordillo Londoño"),
                ("Documentación y demostración", "Jhoan Sebastián Castellanos Mayor")]
    for tema, persona in esperado:
        assert re.search(rf"(?m)^\| {tema}.* \| {persona} \|$", seccion), tema
    cambiado = seccion.replace("| Diego Fernando Gordillo Londoño |\n| Documentación", "| Jhoan Sebastián Castellanos Mayor |\n| Documentación")
    assert cambiado != seccion and not re.search(r"(?m)^\| Sesiones con personas usuarias.* \| Diego Fernando Gordillo Londoño \|$", cambiado)
    assert "@" not in seccion


def pausas_de_reintento(retardo, intentos):
    """Pausas tras cada intento fallido, como se escriben en el texto: 0,5 / 1 / 1,5 con retardo 0,5 y 3 intentos."""
    return [f"{retardo * i:g}".replace(".", ",") for i in range(1, intentos + 1)]


def renglon_de_descargas(texto):
    """El renglón «Descargas» del apartado de errores, reintentos y recuperación (sección 13 del README)."""
    apartado = texto.split("## 13. Errores, reintentos y recuperación")[1].split("\n## ")[0]
    return next(l for l in apartado.splitlines() if l.startswith("- **Descargas:**"))


def problemas_de_reintentos(renglon, reintentos, retardo, tiempo_maximo):
    """Frases que el renglón debe decir según la configuración y que no dice."""
    pausas = pausas_de_reintento(retardo, reintentos)
    texto_de_pausas = ", ".join(f"{p} s" for p in pausas[:-1]) + f" y {pausas[-1]} s"
    esperadas = [f"hasta {reintentos} intentos por petición", f"una pausa de {texto_de_pausas} después de cada intento fallido",
                 f"espera como máximo {tiempo_maximo:g} s por intento", "no el tiempo total", "`timeout_s` de `config/config.yaml`, sección `http`"]
    return [f for f in esperadas if f not in renglon]


def test_los_reintentos_de_la_descarga_del_readme_son_los_de_la_configuracion_y_del_codigo():
    from src.common import load_config

    h = load_config()["http"]
    assert problemas_de_reintentos(renglon_de_descargas(README), h["retries"], h["request_delay_s"], h["timeout_s"]) == []
    codigo = (ROOT / "src" / "extract" / "extract_api.py").read_text(encoding="utf-8")
    assert 'timeout=h["timeout_s"]' in codigo, "el tiempo máximo se aplica a cada petición, no al total"
    assert 'time.sleep(h["request_delay_s"] * intento)' in codigo, "la pausa crece con el intento"
    assert "r.status_code < 500" in codigo, "se reintenta con un 5xx"


def test_el_detector_de_reintentos_calcula_las_pausas_y_nota_cada_dato_cambiado():
    assert pausas_de_reintento(0.5, 3) == ["0,5", "1", "1,5"]
    assert pausas_de_reintento(1, 2) == ["1", "2"]
    renglon = renglon_de_descargas(README)
    assert problemas_de_reintentos(renglon, 3, 0.5, 30) == []
    assert problemas_de_reintentos(renglon, 4, 0.5, 30), "otro número de intentos"
    assert problemas_de_reintentos(renglon, 3, 1, 30), "otra pausa"
    assert problemas_de_reintentos(renglon, 3, 0.5, 60), "otro tiempo máximo"
    assert problemas_de_reintentos(renglon.replace("por intento", "en total"), 3, 0.5, 30), "el tiempo máximo presentado como total"
    assert problemas_de_reintentos(renglon.replace("no el tiempo total", ""), 3, 0.5, 30), "sin aclarar que no es el total"


CLAUSULA_POR_CAPA = ("en Bronze vienen las columnas catastrales que publica la fuente, entre ellas identificadores de predio (`PREDIO`, `NUMEPRED` e `ID_PREDIO`); "
                     "Silver los descarta (regla R10) y Gold conserva las coordenadas del centroide de cada construcción")


def columnas_de_predio(cabecera):
    """Columnas de una cabecera CSV que identifican o describen un predio catastral."""
    return [c for c in cabecera.split(",") if re.search(r"(?i)pred|catast|manzana|terreno|matric", c)]


def test_la_clausula_por_capa_de_los_predios_es_la_de_los_archivos():
    import json

    assert CLAUSULA_POR_CAPA in README
    for capa in ("data/silver/silver_integrated.csv", "data/silver/silver_construcciones.csv", "data/gold/gold_final.csv"):
        with open(ROOT / capa, encoding="utf-8") as f:
            cabecera = f.readline().strip()
        assert columnas_de_predio(cabecera) == [], f"{capa} conserva una columna de predio"
        if capa.endswith("gold_final.csv"):
            assert {"lon", "lat"} <= set(cabecera.split(",")), "Gold conserva las coordenadas"
    pagina = sorted((ROOT / "data" / "bronze" / "api" / "edificaciones").glob("snap_*/page_0001.json"))[0]
    campos = {c["name"] for c in json.loads(pagina.read_text(encoding="utf-8"))["fields"]}
    assert {"PREDIO", "NUMEPRED", "ID_PREDIO"} <= campos, "Bronze trae los identificadores de predio"
    r10 = next(l for l in (ROOT / "docs" / "silver" / "reglas_silver.md").read_text(encoding="utf-8").splitlines() if l.startswith("| R10 |"))
    assert "ID_PREDIO" in r10 and "columnas catastrales" in r10, "la regla R10 descarta los identificadores de predio"
    assert "centroide" in (ROOT / "src" / "transform" / "clean_api.py").read_text(encoding="utf-8"), "las coordenadas de Silver son el centroide del anillo exterior"


def test_el_detector_de_columnas_de_predio_las_encuentra_y_no_inventa():
    assert columnas_de_predio("objectid,PREDIO,lon") == ["PREDIO"]
    assert columnas_de_predio("a,ID_PREDIO,NUMEPRED,b") == ["ID_PREDIO", "NUMEPRED"]
    assert columnas_de_predio("comuna,barrio,codigo_barrio,lon,lat") == []
    assert README.replace("entre ellas identificadores de predio", "sin identificadores", 1) != README
