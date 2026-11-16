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
