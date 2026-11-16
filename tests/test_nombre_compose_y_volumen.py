"""Guardián de `--nombre-compose` y del aviso de volumen previo de `scripts/orquestacion/preparar_airflow.py` (sin Docker real).

Por qué existe: sin `name:` en el compose, Compose usa el nombre de la carpeta de Airflow (`airflow-medallon`) como proyecto, así que el volumen de Postgres es el mismo para cualquier zip que se descomprima
junto a una carpeta con ese nombre; si ese volumen viene de otra instalación, tiene otra contraseña y el apiserver queda «unhealthy» con «password authentication failed for user airflow». El aviso lo dice antes
de que ocurra (y sin borrar nada) y `--nombre-compose` permite usar otro proyecto, y por tanto otro volumen, sin tocar el viejo. COMPOSE_PROJECT_NAME es opcional: no entra en las siete variables obligatorias.
Qué NO demuestra: el comportamiento de Docker de verdad (el formato de la fecha de `docker volume inspect` y la elección del volumen se comprobaron en la prueba desde el zip, EV aparte).
"""
import hashlib
import importlib.util
import subprocess
import sys
from datetime import datetime, timedelta, timezone

import pytest
from dotenv import dotenv_values

from src.common import ROOT

RUTA = ROOT / "scripts" / "orquestacion"
sys.path.insert(0, str(RUTA))
_espec = importlib.util.spec_from_file_location("preparar_airflow_volumen", RUTA / "preparar_airflow.py")
pa = importlib.util.module_from_spec(_espec)
_espec.loader.exec_module(pa)

DAG = b"# dag de prueba\n"
MYSQL_DOCKER = "MYSQL_DOCKER_USER=u\nMYSQL_DOCKER_PASSWORD=Docker-ficticia-0123456789\nMYSQL_PORT=3306\nMYSQL_DATABASE=sismo_cali\n"
VOLUMEN = datetime(2026, 11, 13, 22, 3, 0, tzinfo=timezone(timedelta(hours=-5)))        # una fecha fija, como la devuelve Docker (RFC 3339)


class DockerFalso:
    """Docker simulado: responde a `version` y `compose version`; a `volume inspect` con la fecha dada (o «no existe» si es None) y anota cada comando."""

    def __init__(self, fecha=VOLUMEN, apagado_en_volumen=False, salida=None):
        self.fecha, self.apagado_en_volumen, self.salida, self.comandos = fecha, apagado_en_volumen, salida, []

    def __call__(self, cmd, **kw):
        self.comandos.append(cmd)
        if cmd[1] == "volume":
            if self.apagado_en_volumen:
                raise FileNotFoundError("docker")
            if self.fecha is None:
                return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="Error: No such volume")
            return subprocess.CompletedProcess(cmd, 0, stdout=self.salida if self.salida is not None else self.fecha.isoformat() + "\n", stderr="")
        salida = "29.0.0\n" if "version" in cmd and "--format" in cmd else "5.0.0\n"
        return subprocess.CompletedProcess(cmd, 0, stdout=salida, stderr="")


@pytest.fixture()
def proyecto(tmp_path):
    raiz = tmp_path / "Proyecto de prueba"
    (raiz / "orquestacion").mkdir(parents=True)
    (raiz / "dags").mkdir()
    (raiz / "dags" / "medallon_etl_dag.py").write_bytes(DAG)
    for nombre, texto in (("docker-compose.yaml", "services: {}\n"), ("Dockerfile", "FROM apache/airflow:3.3.2\n"), ("requirements-airflow.txt", "pandas==3.0.6\n")):
        (raiz / "orquestacion" / nombre).write_text(texto, encoding="utf-8")
    (raiz / "orquestacion" / "dag.sha256").write_text(f"{hashlib.sha256(DAG).hexdigest()}  dags/medallon_etl_dag.py\n", encoding="utf-8")
    (raiz / ".env").write_text(MYSQL_DOCKER, encoding="utf-8")
    return raiz


def _preparar(raiz, docker=None, **kw):
    args = {"raiz": raiz, "destino": raiz.parent / "airflow-medallon", "puerto": 8082, "ejecutar": docker or DockerFalso(fecha=None), "comprobar_puerto": lambda p: True}
    args.update(kw)
    return pa.preparar(**args)


def _env(raiz):
    return raiz.parent / "airflow-medallon" / ".env"


# ---------------------------------------------------------------- --nombre-compose
@pytest.mark.parametrize("nombre", ["airflow-zip", "a1", "x_y", "0abc"])
def test_un_nombre_de_compose_valido_se_acepta(nombre):
    assert pa.validar_nombre_compose(nombre) == nombre


@pytest.mark.parametrize("nombre", ["", "Airflow", "-x", "_x", "con espacio", "ñandú", "a/b", "a.b", None])
def test_un_nombre_de_compose_invalido_se_rechaza_antes_de_escribir_nada(proyecto, nombre):
    with pytest.raises(pa.PrepararError, match="nombre de proyecto de Compose"):
        _preparar(proyecto, nombre_compose=nombre) if nombre is not None else pa.validar_nombre_compose(nombre)
    assert not (proyecto.parent / "airflow-medallon").exists()


def test_sin_la_opcion_nada_cambia_el_env_trae_exactamente_las_siete_variables_y_el_nombre_es_el_de_la_carpeta(proyecto):
    hecho = _preparar(proyecto)
    assert set(dotenv_values(_env(proyecto))) == set(pa.NOMBRES_ENV_AIRFLOW) and len(pa.NOMBRES_ENV_AIRFLOW) == 7
    assert hecho["compose_fijado"] is False and hecho["nombre_compose"] == "airflow-medallon"


def test_con_la_opcion_se_guarda_una_octava_variable_opcional_que_no_cuenta_como_obligatoria(proyecto):
    hecho = _preparar(proyecto, nombre_compose="airflow-zip")
    valores = dotenv_values(_env(proyecto))
    assert valores[pa.NOMBRE_COMPOSE] == "airflow-zip" and set(valores) == set(pa.NOMBRES_ENV_AIRFLOW) | {pa.NOMBRE_COMPOSE}
    assert hecho["compose_fijado"] is True and hecho["nombre_compose"] == "airflow-zip" and hecho["faltan_en_env"] == []
    assert pa.NOMBRE_COMPOSE not in pa.NOMBRES_ENV_AIRFLOW and len(pa.NOMBRES_ENV_AIRFLOW) == 7
    nombres = [l.strip() for l in (ROOT / "orquestacion" / "airflow-env.nombres.txt").read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    assert pa.NOMBRE_COMPOSE not in nombres and len(nombres) == 7


def test_en_un_env_existente_solo_se_toca_esa_variable_y_repetirlo_no_cambia_nada(proyecto):
    _preparar(proyecto)
    antes = _env(proyecto).read_text(encoding="utf-8")
    _preparar(proyecto, nombre_compose="airflow-zip")
    despues = _env(proyecto).read_text(encoding="utf-8")
    assert despues.splitlines()[:-1] == antes.splitlines() and despues.splitlines()[-1] == "COMPOSE_PROJECT_NAME=airflow-zip"
    _preparar(proyecto, nombre_compose="airflow-zip")
    assert _env(proyecto).read_text(encoding="utf-8") == despues
    _preparar(proyecto, nombre_compose="otro-nombre")
    assert dotenv_values(_env(proyecto))[pa.NOMBRE_COMPOSE] == "otro-nombre" and _env(proyecto).read_text(encoding="utf-8").count(pa.NOMBRE_COMPOSE) == 1


def test_regenerar_conserva_el_nombre_de_compose_que_ya_tenia_y_la_opcion_lo_reemplaza(proyecto):
    _preparar(proyecto, nombre_compose="airflow-zip")
    clave_antes = dotenv_values(_env(proyecto))["POSTGRES_PASSWORD"]
    _preparar(proyecto, regenerar=True)
    v = dotenv_values(_env(proyecto))
    assert v["POSTGRES_PASSWORD"] != clave_antes and v[pa.NOMBRE_COMPOSE] == "airflow-zip"        # contraseñas nuevas, pero el mismo proyecto (y volumen) de Compose
    _preparar(proyecto, regenerar=True, nombre_compose="airflow-b")
    assert dotenv_values(_env(proyecto))[pa.NOMBRE_COMPOSE] == "airflow-b"


def test_completar_agrega_lo_que_falta_y_fija_el_nombre(proyecto):
    destino = proyecto.parent / "airflow-medallon"
    destino.mkdir()
    (destino / ".env").write_text("AIRFLOW_UID=50000\n", encoding="utf-8")
    hecho = _preparar(proyecto, completar=True, nombre_compose="airflow-zip")
    v = dotenv_values(destino / ".env")
    assert v["AIRFLOW_UID"] == "50000" and v[pa.NOMBRE_COMPOSE] == "airflow-zip" and hecho["faltan_en_env"] == [] and "PROYECTO_NOMBRE" in hecho["agregadas"]


def test_el_nombre_efectivo_sin_la_variable_es_el_de_la_carpeta_normalizado(tmp_path):
    assert pa.nombre_compose_efectivo(tmp_path / "Airflow Medallón (2)") == "airflowmedalln2"
    assert pa.nombre_compose_efectivo(tmp_path / "airflow-medallon") == "airflow-medallon"


# ---------------------------------------------------------------- aviso de volumen previo
def test_con_un_volumen_previo_y_un_env_nuevo_avisa_con_el_nombre_el_sintoma_y_los_dos_remedios_sin_borrar_nada(proyecto):
    docker = DockerFalso()
    hecho = _preparar(proyecto, docker=docker)
    aviso = " ".join(a for a in hecho["avisos"] if "volumen" in a)
    assert "airflow-medallon_postgres-db-volume" in aviso and "password authentication failed for user airflow" in aviso
    assert "--nombre-compose" in aviso and "down -v" in aviso and "2026-11-1" in aviso
    comandos = [" ".join(c) for c in docker.comandos]
    assert not any(" rm" in c or "prune" in c or "down" in c for c in comandos)               # solo mira: ningún comando destructivo
    assert any("volume inspect airflow-medallon_postgres-db-volume" in c for c in comandos)
    assert all(v not in aviso for v in dotenv_values(_env(proyecto)).values())                  # ningún valor del .env


def test_el_volumen_que_se_mira_es_el_del_nombre_elegido(proyecto):
    docker = DockerFalso(fecha=None)
    _preparar(proyecto, docker=docker, nombre_compose="airflow-zip")
    assert any("airflow-zip_postgres-db-volume" in " ".join(c) for c in docker.comandos)
    assert not any("airflow-medallon_postgres-db-volume" in " ".join(c) for c in docker.comandos)


@pytest.mark.parametrize("docker, hay_aviso", [(DockerFalso(fecha=None), False), (DockerFalso(apagado_en_volumen=True), False), (DockerFalso(salida="5.0.0\n"), False), (DockerFalso(salida=""), False)],
                         ids=["no existe", "docker falla al preguntar", "respuesta que no es una fecha", "respuesta vacía"])
def test_sin_un_volumen_legible_no_hay_aviso_ni_error(proyecto, docker, hay_aviso):
    hecho = _preparar(proyecto, docker=docker)
    assert not any("volumen" in a for a in hecho["avisos"]) and hecho["faltan_en_env"] == []


def test_si_el_volumen_es_anterior_al_env_avisa_y_si_es_posterior_no(proyecto):
    _preparar(proyecto)                                                                         # crea el .env (sin Docker que mirar)
    destino = proyecto.parent / "airflow-medallon"
    creado = datetime.now(timezone.utc)
    assert pa.aviso_de_volumen("airflow-medallon", destino, DockerFalso(fecha=creado - timedelta(days=2)), creacion_env=creado) is not None
    assert pa.aviso_de_volumen("airflow-medallon", destino, DockerFalso(fecha=creado + timedelta(minutes=5)), creacion_env=creado) is None
    assert pa.aviso_de_volumen("airflow-medallon", destino, DockerFalso(fecha=creado), creacion_env=creado) is None


def test_una_fecha_sin_zona_horaria_se_toma_como_utc():
    docker = DockerFalso(fecha=datetime(2026, 11, 13, 22, 3, 0))
    assert pa.fecha_del_volumen("airflow-medallon", docker).tzinfo is not None


# ---------------------------------------------------------------- verificar y la línea de comandos
def _principal(monkeypatch, proyecto, docker, argv):
    monkeypatch.setattr(pa, "ROOT", proyecto)
    monkeypatch.setattr(pa, "puerto_libre", lambda p, host="127.0.0.1": True)
    monkeypatch.setattr(pa.subprocess, "run", docker)
    return pa.main(argv)


def test_verificar_muestra_el_aviso_con_signo_de_exclamacion_y_no_cambia_el_codigo_de_salida(proyecto, monkeypatch, capsys):
    _preparar(proyecto)
    antes = {p: p.read_bytes() for p in (proyecto.parent / "airflow-medallon").rglob("*") if p.is_file()}
    codigo = _principal(monkeypatch, proyecto, DockerFalso(fecha=datetime(2000, 1, 1, tzinfo=timezone.utc)), ["--destino", str(proyecto.parent / "airflow-medallon"), "--verificar"])
    salida = capsys.readouterr().out
    assert codigo == 0 and "! ya existe el volumen airflow-medallon_postgres-db-volume" in salida and "✗" not in salida
    assert "nombre de proyecto de Compose: airflow-medallon (el de la carpeta de Airflow, por defecto)" in salida
    assert {p: p.read_bytes() for p in (proyecto.parent / "airflow-medallon").rglob("*") if p.is_file()} == antes       # solo lectura


def test_verificar_con_docker_apagado_no_pregunta_por_volumenes_ni_agrega_errores(proyecto, monkeypatch, capsys):
    _preparar(proyecto)

    def apagado(cmd, **kw):
        apagado.llamadas.append(cmd)
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="Cannot connect to the Docker daemon")
    apagado.llamadas = []
    codigo = _principal(monkeypatch, proyecto, apagado, ["--destino", str(proyecto.parent / "airflow-medallon"), "--verificar"])
    salida = capsys.readouterr().out
    assert codigo == 1 and "Docker está instalado pero no responde" in salida and "volumen" not in salida
    assert not any(c[1] == "volume" for c in apagado.llamadas)


def test_verificar_dice_cuando_el_nombre_de_compose_esta_guardado(proyecto, monkeypatch, capsys):
    _preparar(proyecto, nombre_compose="airflow-zip")
    _principal(monkeypatch, proyecto, DockerFalso(fecha=None), ["--destino", str(proyecto.parent / "airflow-medallon"), "--verificar"])
    assert "nombre de proyecto de Compose: airflow-zip (guardado en el `.env` de Airflow)" in capsys.readouterr().out


def test_la_opcion_no_se_combina_con_verificar_y_main_la_pasa_a_preparar(proyecto, monkeypatch, capsys):
    with pytest.raises(SystemExit):
        _principal(monkeypatch, proyecto, DockerFalso(fecha=None), ["--verificar", "--nombre-compose", "x"])
    codigo = _principal(monkeypatch, proyecto, DockerFalso(fecha=None), ["--destino", str(proyecto.parent / "airflow-medallon"), "--puerto", "8082", "--nombre-compose", "airflow-zip"])
    salida = capsys.readouterr().out
    assert codigo == 0 and "nombre de proyecto de Compose: airflow-zip (guardado en el `.env` de Airflow)" in salida
    assert dotenv_values(_env(proyecto))[pa.NOMBRE_COMPOSE] == "airflow-zip"
    assert all(v not in salida for v in dotenv_values(_env(proyecto)).values() if len(v) > 8 and v != "airflow-zip")        # ningún secreto en pantalla
