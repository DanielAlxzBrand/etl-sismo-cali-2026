"""Estructura de los servicios locales (phpMyAdmin, Airflow desde el zip y guía de instalación): los archivos existen, viajan en el zip, no llevan credenciales y las guías no dejan enlaces rotos ni marcas sin llenar (D91 a D94).

Por qué existe: lo que se entrega solo sirve si llega completo al equipo de otra persona y sin ningún secreto. Aquí se arma un zip de verdad con `scripts/make_dist.py`, se comprueba que trae lo que debe y nada que no debe,
y se leen las guías como texto. Qué NO demuestra: que los servicios arranquen (eso lo comprueban las ejecuciones en vivo, EV-085 y EV-087) ni que el zip sirva en una máquina limpia.
"""
import importlib.util
import re
import zipfile

import pytest

from src.common import ROOT

_spec = importlib.util.spec_from_file_location("make_dist_servicios", ROOT / "scripts" / "make_dist.py")
make_dist = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(make_dist)
_spec2 = importlib.util.spec_from_file_location("escanear_secretos_servicios", ROOT / "scripts" / "escanear_secretos.py")
esc = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(esc)

NUEVOS = ["servicios/phpmyadmin/docker-compose.yaml", "orquestacion/docker-compose.yaml", "orquestacion/docker-compose.diff", "scripts/orquestacion/preparar_airflow.py",
          "scripts/orquestacion/generar_compose.py", "scripts/preparar_entorno.py", "docs/instalacion/README.md", "docs/instalacion/modo_minimo.md", "docs/instalacion/modo_completo.md",
          "docs/instalacion/errores_comunes.md", "docs/almacenamiento/phpmyadmin.md", ".env.example"]
GUIAS = ["docs/instalacion/README.md", "docs/instalacion/modo_minimo.md", "docs/instalacion/modo_completo.md", "docs/instalacion/errores_comunes.md", "docs/almacenamiento/phpmyadmin.md",
         "docs/orquestacion/operacion.md", "docs/orquestacion/diferencias_con_la_guia.md"]
# las cadenas se parten para que este archivo no se detecte a sí mismo (como hace test_estrategia)
PROHIBIDAS = re.compile(r"(?i)pro" + r"fe(?:sor)?\b|\bpro" + r"mpt\b|DECLARACION_USO_" + r"IA|C:\\Us" + r"ers|Alex" + r"D|/Us" + r"ers/")


@pytest.fixture(scope="module")
def zip_de_prueba(tmp_path_factory):
    """Zip real armado con `make_dist.empaquetar` en una carpeta temporal (nunca en `dist/`)."""
    ruta, nombres = make_dist.empaquetar(ROOT, tmp_path_factory.mktemp("zip"))
    return ruta, nombres


def test_los_archivos_nuevos_existen_y_viajan_en_el_zip(zip_de_prueba):
    ruta, nombres = zip_de_prueba
    faltan = [n for n in NUEVOS if not (ROOT / n).is_file()]
    assert not faltan, faltan
    assert [n for n in NUEVOS if n not in nombres] == []
    assert make_dist.fuera_de_la_lista(nombres) == [] and "servicios" in make_dist.RAIZ_CARPETAS


def test_el_zip_no_trae_ningun_env_real_ni_el_valor_de_una_credencial(zip_de_prueba):
    ruta, nombres = zip_de_prueba
    assert not [n for n in nombres if n.split("/")[-1] in (".env", "airflow.env") or re.search(r"(^|/)\.env($|\.[^e])", n)]
    with zipfile.ZipFile(ruta) as z:
        assert not [n for n in z.namelist() if n.endswith(".env")]
    can = esc.canarios(ROOT)                 # lee en memoria las variables sensibles del `.env` real (si existe) y las busca dentro del zip, sin imprimirlas
    assert esc.canario_zip(ruta, can) == []


def test_las_guias_solo_enlazan_archivos_que_existen():
    rotos = []
    for rel in GUIAS:
        base = (ROOT / rel).parent
        for m in re.finditer(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", (ROOT / rel).read_text(encoding="utf-8")):
            destino = m.group(1)
            if destino.startswith(("http", "mailto")):
                continue
            if not (base / destino).exists():
                rotos.append((rel, destino))
    assert not rotos, rotos


def test_las_guias_no_dejan_marcas_sin_llenar():
    pendientes = [(rel, m.group(0)) for rel in GUIAS for m in re.finditer(r"⟦[^⟧]*⟧", (ROOT / rel).read_text(encoding="utf-8"))]
    assert not pendientes, pendientes


def test_los_textos_nuevos_no_llevan_rutas_locales_ni_palabras_prohibidas():
    archivos = [ROOT / n for n in NUEVOS if n != ".env.example"] + [ROOT / "orquestacion" / "docker-compose.yaml"]
    malos = [(a.relative_to(ROOT).as_posix(), n, linea.strip()[:80]) for a in archivos for n, linea in enumerate(a.read_text(encoding="utf-8").splitlines(), 1) if PROHIBIDAS.search(linea)]
    assert not malos, malos


def test_el_registro_de_recursos_trae_las_medidas_de_memoria_que_cita_la_guia():
    texto = (ROOT / "docs" / "finanzas" / "recursos_medidos.csv").read_text(encoding="utf-8")
    for magnitud in ("memoria_pico_suite_de_pruebas", "memoria_api_mas_panel_en_reposo", "memoria_en_reposo_phpmyadmin", "memoria_en_reposo_total_contenedores_de_airflow"):
        assert magnitud in texto, magnitud


def test_cada_guia_termina_con_lo_que_no_demuestra():
    for rel in ("docs/instalacion/README.md", "docs/instalacion/modo_minimo.md", "docs/instalacion/modo_completo.md", "docs/instalacion/errores_comunes.md", "docs/almacenamiento/phpmyadmin.md"):
        assert re.search(r"Qué NO (demuestra|afirmamos)", (ROOT / rel).read_text(encoding="utf-8")), rel


def test_las_guias_de_instalacion_citan_el_nombre_de_las_cuentas_y_los_comandos_de_mysql():
    texto = (ROOT / "docs" / "instalacion" / "modo_completo.md").read_text(encoding="utf-8")
    for pieza in ("configurar_mysql.py", "--usuario-docker --origen localhost", "--usuario-lectura", "sismo_etl", "sismo_airflow", "sismo_lectura", "preparar_airflow.py", "127.0.0.1"):
        assert pieza in texto, pieza
    assert "py -3.13" in (ROOT / "docs" / "instalacion" / "README.md").read_text(encoding="utf-8")
