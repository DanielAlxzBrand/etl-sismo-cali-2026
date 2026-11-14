"""Humo de extremo a extremo de solo lectura (D23): la API real en un subproceso sobre una copia temporal, el cliente real del panel por HTTP de verdad
y AppTest recorriendo las 8 páginas, con valores iguales a las salidas del pipeline. El subproceso se cierra siempre; la espera está acotada."""
import csv
import hashlib
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

from src.panel import formato, registro
from src.panel.cliente_api import ClienteApi
from tests import panel_apoyo as pa

RAIZ = Path(__file__).resolve().parents[1]
LIMITE_ARRANQUE_S = 40
LANZADOR = "import sys,uvicorn; from src.api.app import crear_app; uvicorn.run(crear_app(ruta_db=sys.argv[1]), host='127.0.0.1', port=int(sys.argv[2]), log_level='warning')"


def _puerto_libre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _huellas_data():
    return {p.relative_to(RAIZ).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((RAIZ / "data").rglob("*")) if p.is_file()}


@pytest.fixture(scope="module")
def servidor_real():
    antes = _huellas_data()
    carpeta, ruta = pa.copia_temporal_de_la_base()
    puerto = _puerto_libre()
    url = f"http://127.0.0.1:{puerto}"
    proceso = subprocess.Popen([sys.executable, "-c", LANZADOR, str(ruta), str(puerto)], cwd=RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    cliente = None
    try:
        fin = time.monotonic() + LIMITE_ARRANQUE_S
        while time.monotonic() < fin:
            try:
                if httpx.get(url + "/health", timeout=2).status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(0.3)
        else:
            pytest.fail("la API real no arrancó a tiempo")
        cliente = ClienteApi(url)
        yield url, cliente, antes
    finally:
        if cliente is not None:
            cliente.cerrar()
        proceso.terminate()
        try:
            proceso.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proceso.kill()
            proceso.wait(timeout=15)
        shutil.rmtree(carpeta, ignore_errors=True)


def _csv(ruta):
    with open(ruta, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_el_cliente_real_lee_por_http_las_once_rutas_de_la_api(servidor_real):
    _, cliente, _ = servidor_real
    for ruta in ("/health", "/metadata", "/fuentes", "/kpis", "/kpis/K1", "/kpis/sensibilidad", "/comunas", "/composicion", "/construcciones", "/calidad", "/llave/revision"):
        r = cliente.obtener(ruta)
        assert r.ok, (ruta, r.error)


def test_las_ocho_paginas_se_recorren_con_el_cliente_real_sin_excepciones(servidor_real):
    _, cliente, _ = servidor_real
    api = pa.como_consulta(cliente)
    for p in registro.PAGINAS:
        at = pa.pagina(p.id, api, tiempo=60)
        assert len(at.exception) == 0, p.id
        assert at.title[0].value == p.titulo
        assert "proxy de daño" in pa.textos(at)


def test_los_valores_por_http_real_coinciden_con_las_salidas(servidor_real):
    _, cliente, _ = servidor_real
    api = pa.como_consulta(cliente)
    kpis = {(r["kpi_id"], r["grupo"]): r for r in _csv(RAIZ / "data" / "gold" / "kpis_gold.csv")}
    m = {x.label: x.value for x in pa.pagina("respuesta", api, tiempo=60).metric}
    assert m["Tasa 3-5"] == formato.porcentaje(float(kpis[("K2", "estratos_3-5")]["valor"]))
    assert m["Diferencia (3-5 menos 1-2)"] == formato.puntos_porcentuales(float(kpis[("K2", "diferencia_3-5_menos_1-2")]["valor"]))
    assert m["Estrato válido"] == "99,845 %"
    gold = _csv(RAIZ / "data" / "gold" / "gold_final.csv")
    f = {x.label: x.value for x in pa.pagina("fuentes", api, tiempo=60).metric}
    assert f["Construcciones"] == formato.numero(len(gold))
    at = pa.pagina("construcciones", api, tiempo=60)
    assert f"{formato.numero(len(gold))} construcciones con estos filtros" in pa.textos(at)


def test_el_panel_no_puede_escribir_y_data_no_cambia(servidor_real):
    url, cliente, antes = servidor_real
    assert httpx.post(url + "/kpis", json={}).status_code == 405
    assert httpx.delete(url + "/kpis").status_code == 405
    pa.pagina("estratos", pa.como_consulta(cliente), tiempo=60)
    assert _huellas_data() == antes


def test_con_la_api_apagada_el_panel_muestra_el_aviso_sin_trazas():
    cliente = ClienteApi(f"http://127.0.0.1:{_puerto_libre()}", reintentos_conexion=0)
    try:
        at = pa.pagina("respuesta", pa.como_consulta(cliente), tiempo=60)
    finally:
        cliente.cerrar()
    assert len(at.exception) == 0 and "No se pudo conectar con la API" in pa.textos(at)
