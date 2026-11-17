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
    for ev in sorted((ROOT / "docs" / "evidencias" / "readme").glob("EV-109_*.txt")):
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
    return {n.lower(): v for n, v in re.findall(r"(?m)^\| `?([A-Za-z][\w .+-]*?)`? \| (\d+(?:\.\d+)*) \|", texto)}


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
        f"`Salida: construcciones={miles(len(gold))} barrios={barrios} integrado={miles(len(gold))} | cobertura de llave={rep['cobertura_llave']['pct'] * 100:.4f}% (pasa)`",
        f"`Salida: gold_final={miles(len(gold))} filas | kpis_gold={len(k)} filas ({k.kpi_id.nunique()} indicadores) | sensibilidades={len(s)} filas`",
        f"`kpis_gold.csv` tiene {len(k)} filas (K1 a K6) y `kpis_sensibilidad.csv` tiene {len(s)} (escenarios S0 a S5)",
        f"una fila por construcción ({miles(len(gold))})", f"({lineas_manifiesto} en total)",
    ]
    for e in esperadas:
        assert e in README, e
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


def test_la_cobertura_del_readme_es_la_medida_en_ev_109():
    assert set(re.findall(r"(\d+ %) de las líneas de `src/`", README)) == {valor_medido_de_cobertura()}


# --- los tiempos y consumos que el README cita están en la evidencia que dice como origen ---
EV100 = "docs/evidencias/modo_completo/EV-100_guia_seguida_desde_un_zip_nuevo.txt"
RECURSOS = "docs/finanzas/recursos_medidos.csv"
TIEMPOS_CITADOS = [
    ("251 s", EV100, ["instalación de requirements.txt y pip check en 251 s"]),
    ("| 8,9 s |", EV100, ["$ docker compose build\n# código de salida: 0 · segundos: 8.9 "]),
    ("| 42,2 s |", EV100, ["$ docker compose up airflow-init\n# código de salida: 0 · segundos: 42.2 "]),
    ("| 55 s |", EV100, ["$ docker compose up -d\n# código de salida: 0 · segundos: 55 "]),
    ("unos 12 s", EV100, ["terminaron en success en unos 12 s"]),
    ("288 s en [EV-083]", "docs/evidencias/servicios/EV-083_suite_sin_utf8_antes.txt", ["288"]),
    ("323 s con 1.007 pruebas y 319 MiB de pico", "docs/evidencias/auditoria/EV-097_memoria_de_la_suite.txt", ["1007 passed", "in 323.61s", "319 MiB"]),
    ("3,4 s y 148 MB de pico", RECURSOS, ["tiempo_main_todas_las_etapas,3.4,", "pico_memoria_main_todas_las_etapas,148,"]),
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
    editado = README.replace("| 42,2 s |", "| 4,2 s |", 1)
    assert tiempos_que_no_coinciden(editado, TIEMPOS_CITADOS, _leer), "un tiempo cambiado en el README"
    otros = [(c, a, ["segundos: 99.9"]) if c == "| 42,2 s |" else (c, a, f) for c, a, f in TIEMPOS_CITADOS]
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
    assert problemas_de_sesiones(otra, False), "la mención de los datos personales cambiada"


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
    assert "todavía no hay un canal de contacto público" in seccion


def test_todo_lo_que_el_readme_enlaza_viaja_en_el_zip():
    from tests.test_criterio_de_texto import make_dist

    en_el_zip = {p.relative_to(ROOT).as_posix() for p in make_dist.listar(ROOT)}
    destinos = {d.split("#")[0] for d in re.findall(r"\]\(([^)\s]+)\)", re.sub(r"(?s)```.*?```", "", README)) if not d.startswith(("http://", "https://", "#"))}
    assert destinos and sorted(d for d in destinos if d not in en_el_zip) == []
