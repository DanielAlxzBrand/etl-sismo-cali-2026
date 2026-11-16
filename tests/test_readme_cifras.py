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
