"""`scripts/orquestacion/preparar_airflow.py` en carpetas temporales y sin Docker: estructura, `.env` que no se sobrescribe, nombre de carpeta detectado, puerto ocupado y ningún valor secreto en pantalla (D91).

Por qué existe: quien reciba el zip prepara Airflow con este script; si sobrescribiera un `.env` perdería su contraseña, si el nombre de la carpeta fuera fijo el compose montaría el lugar equivocado
y si imprimiera un valor lo dejaría en la consola. Aquí se comprueba cada cosa con un proyecto de mentira (con espacios en el nombre) y un Docker simulado. La verificación en vivo es EV-084.
"""
import hashlib
import importlib.util
import subprocess
import sys

import pytest
from dotenv import dotenv_values

from src.common import ROOT

RUTA = ROOT / "scripts" / "orquestacion"
sys.path.insert(0, str(RUTA))
_espec = importlib.util.spec_from_file_location("preparar_airflow_prueba", RUTA / "preparar_airflow.py")
pa = importlib.util.module_from_spec(_espec)
_espec.loader.exec_module(pa)

DAG = b"# dag de prueba\nprint('hola')\n"
MYSQL_DOCKER = "MYSQL_DOCKER_USER=u_docker\nMYSQL_DOCKER_PASSWORD=Docker-ficticia-0123456789\nMYSQL_DOCKER_ORIGEN=localhost\nMYSQL_PORT=3306\nMYSQL_DATABASE=sismo_cali\n"


def _docker_ok(cmd, **kw):
    salida = "29.0.0\n" if "version" in cmd and "--format" in cmd else "5.0.0\n"
    return subprocess.CompletedProcess(cmd, 0, stdout=salida, stderr="")


def _docker_apagado(cmd, **kw):
    return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="Cannot connect to the Docker daemon")


@pytest.fixture()
def proyecto(tmp_path):
    """Proyecto de mentira con espacios y tilde en el nombre, junto al lugar donde irá la carpeta de Airflow."""
    raiz = tmp_path / "Proyecto sísmico de prueba"
    (raiz / "orquestacion").mkdir(parents=True)
    (raiz / "dags").mkdir()
    (raiz / "dags" / "medallon_etl_dag.py").write_bytes(DAG)
    for nombre, texto in (("docker-compose.yaml", "services: {}\n"), ("Dockerfile", "FROM apache/airflow:3.3.2\n"), ("requirements-airflow.txt", "pandas==3.0.6\n")):
        (raiz / "orquestacion" / nombre).write_text(texto, encoding="utf-8")
    (raiz / "orquestacion" / "dag.sha256").write_text(f"{hashlib.sha256(DAG).hexdigest()}  dags/medallon_etl_dag.py\n", encoding="utf-8")
    (raiz / ".env").write_text(MYSQL_DOCKER, encoding="utf-8")
    return raiz


def _preparar(raiz, **kw):
    args = {"raiz": raiz, "destino": raiz.parent / "airflow-medallon", "puerto": 8082, "ejecutar": _docker_ok, "comprobar_puerto": lambda p: True}
    args.update(kw)
    return pa.preparar(**args)


def test_crea_la_estructura_copia_los_archivos_y_el_dag_con_su_sha256(proyecto):
    hecho = _preparar(proyecto)
    destino = proyecto.parent / "airflow-medallon"
    assert all((destino / c).is_dir() for c in ("dags", "logs", "plugins", "config"))
    assert all((destino / n).read_bytes() == (proyecto / "orquestacion" / n).read_bytes() for n in pa.ARCHIVOS)
    assert (destino / "dags" / "medallon_etl_dag.py").read_bytes() == DAG
    assert hecho["env"] == "creado" and hecho["faltan_en_env"] == [] and hecho["faltan_mysql"] == []


def test_el_nombre_de_la_carpeta_del_proyecto_se_detecta_y_no_es_fijo(proyecto):
    assert pa.nombre_del_proyecto(proyecto) == "Proyecto sísmico de prueba"
    _preparar(proyecto)
    v = dotenv_values(proyecto.parent / "airflow-medallon" / ".env")
    assert v["PROYECTO_NOMBRE"] == "Proyecto sísmico de prueba" and v["AIRFLOW_PUERTO"] == "8082" and v["AIRFLOW_UID"] == "50000"
    assert "etl_sismo_cali_2026" not in (proyecto.parent / "airflow-medallon" / ".env").read_text(encoding="utf-8")
    assert pa.nombre_del_proyecto(proyecto.parent / "otro nombre distinto") == "otro nombre distinto"


def test_los_cuatro_secretos_son_aleatorios_distintos_entre_si_y_la_fernet_es_valida(proyecto):
    _preparar(proyecto)
    v1 = dotenv_values(proyecto.parent / "airflow-medallon" / ".env")
    assert len(v1["_AIRFLOW_WWW_USER_PASSWORD"]) >= 24 and len(v1["POSTGRES_PASSWORD"]) >= 24 and len(v1["AIRFLOW__API_AUTH__JWT_SECRET"]) >= 32
    import base64
    assert len(base64.urlsafe_b64decode(v1["FERNET_KEY"])) == 32
    _preparar(proyecto, regenerar=True)
    v2 = dotenv_values(proyecto.parent / "airflow-medallon" / ".env")
    assert v2["FERNET_KEY"] != v1["FERNET_KEY"] and v2["_AIRFLOW_WWW_USER_PASSWORD"] != v1["_AIRFLOW_WWW_USER_PASSWORD"]
    assert v2["POSTGRES_PASSWORD"] != v1["POSTGRES_PASSWORD"] and v2["AIRFLOW__API_AUTH__JWT_SECRET"] != v1["AIRFLOW__API_AUTH__JWT_SECRET"]
    secretos = [v1[k] for k in ("_AIRFLOW_WWW_USER_PASSWORD", "FERNET_KEY", "POSTGRES_PASSWORD", "AIRFLOW__API_AUTH__JWT_SECRET")]
    assert len(set(secretos)) == 4 and "airflow" not in (v1["POSTGRES_PASSWORD"], v1["AIRFLOW__API_AUTH__JWT_SECRET"])


def test_un_env_existente_no_se_sobrescribe(proyecto):
    destino = proyecto.parent / "airflow-medallon"
    destino.mkdir()
    propio = "AIRFLOW_UID=50000\n_AIRFLOW_WWW_USER_PASSWORD=Contrasena-que-ya-tenia-0123\nFERNET_KEY=clave-propia-0123456789abcdef=\nPOSTGRES_PASSWORD=pg-propia-0123456789\nAIRFLOW__API_AUTH__JWT_SECRET=jwt-propio-0123456789\nPROYECTO_NOMBRE=otra\nAIRFLOW_PUERTO=9000\n"
    (destino / ".env").write_text(propio, encoding="utf-8")
    hecho = _preparar(proyecto)
    assert (destino / ".env").read_text(encoding="utf-8") == propio and hecho["env"] == "sin cambios"
    assert any("PROYECTO_NOMBRE" in a for a in hecho["avisos"]) and any("AIRFLOW_PUERTO" in a for a in hecho["avisos"])    # avisa de lo que no coincide, sin cambiarlo
    assert "Contrasena-que-ya-tenia" not in " ".join(hecho["avisos"])


def test_regenerar_si_sobrescribe_y_completar_solo_agrega_lo_que_falta(proyecto):
    destino = proyecto.parent / "airflow-medallon"
    destino.mkdir()
    (destino / ".env").write_text("AIRFLOW_UID=50000\n_AIRFLOW_WWW_USER_PASSWORD=Contrasena-que-ya-tenia-0123\n", encoding="utf-8")
    hecho = _preparar(proyecto, completar=True)
    v = dotenv_values(destino / ".env")
    assert v["_AIRFLOW_WWW_USER_PASSWORD"] == "Contrasena-que-ya-tenia-0123" and v["AIRFLOW_UID"] == "50000"
    assert set(hecho["agregadas"]) == {"FERNET_KEY", "POSTGRES_PASSWORD", "AIRFLOW__API_AUTH__JWT_SECRET", "PROYECTO_NOMBRE", "AIRFLOW_PUERTO"} and hecho["faltan_en_env"] == []
    antes = (destino / ".env").read_text(encoding="utf-8")
    assert _preparar(proyecto, completar=True)["env"] == "sin cambios" and (destino / ".env").read_text(encoding="utf-8") == antes
    _preparar(proyecto, regenerar=True)
    assert dotenv_values(destino / ".env")["_AIRFLOW_WWW_USER_PASSWORD"] != "Contrasena-que-ya-tenia-0123"


def test_con_el_puerto_ocupado_se_avisa_se_sugiere_otro_y_no_se_escribe_nada(proyecto):
    with pytest.raises(pa.PrepararError, match="8082 está ocupado.*--puerto 8084"):
        _preparar(proyecto, comprobar_puerto=lambda p: p not in (8082, 8083))
    assert not (proyecto.parent / "airflow-medallon").exists()
    _preparar(proyecto, puerto=8084, comprobar_puerto=lambda p: p == 8084)      # con otro puerto sí acepta


def test_puerto_libre_detecta_un_puerto_ocupado_de_verdad():
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        ocupado = s.getsockname()[1]
        assert pa.puerto_libre(ocupado) is False
    assert pa.siguiente_puerto_libre(1, comprobar=lambda p: p == 3) == 3


@pytest.mark.parametrize("ejecutor", [_docker_apagado, lambda cmd, **kw: (_ for _ in ()).throw(FileNotFoundError("docker"))], ids=["apagado", "no instalado"])
def test_sin_docker_se_avisa_y_no_se_escribe_nada(proyecto, ejecutor):
    with pytest.raises(pa.PrepararError, match="Docker"):
        _preparar(proyecto, ejecutar=ejecutor)
    assert not (proyecto.parent / "airflow-medallon").exists()


def test_el_destino_debe_ser_hermano_del_proyecto_y_el_dag_debe_ser_el_registrado(proyecto, tmp_path):
    with pytest.raises(pa.PrepararError, match="hermana"):
        _preparar(proyecto, destino=proyecto / "dentro")
    with pytest.raises(pa.PrepararError, match="hermana"):
        _preparar(proyecto, destino=tmp_path / "otro" / "airflow")
    (proyecto / "dags" / "medallon_etl_dag.py").write_bytes(DAG + b"# cambiado\n")
    with pytest.raises(pa.PrepararError, match="sha256"):
        _preparar(proyecto)
    assert not (proyecto.parent / "airflow-medallon").exists()


def test_si_faltan_las_variables_de_mysql_del_proyecto_lo_dice_por_nombre_y_da_el_comando(proyecto, capsys, monkeypatch):
    (proyecto / ".env").write_text("MYSQL_PORT=3306\n", encoding="utf-8")
    hecho = _preparar(proyecto)
    assert hecho["faltan_mysql"] == ["MYSQL_DOCKER_USER", "MYSQL_DOCKER_PASSWORD", "MYSQL_DATABASE"]
    assert "--usuario-docker --origen localhost" in pa.COMANDO_MYSQL


def test_ningun_valor_secreto_se_imprime_ni_se_registra(proyecto, capsys, caplog, monkeypatch):
    monkeypatch.setattr(pa, "ROOT", proyecto)
    monkeypatch.setattr(pa, "comprobar_docker", lambda ejecutar=None: (True, "Docker 29.0.0 y Compose 5.0.0"))
    monkeypatch.setattr(pa, "puerto_libre", lambda p, host="127.0.0.1": True)
    with caplog.at_level("DEBUG"):
        codigo = pa.main(["--destino", str(proyecto.parent / "airflow-medallon"), "--puerto", "8082"])
    assert codigo == 0
    salida = capsys.readouterr()
    todo = salida.out + salida.err + caplog.text
    secretos = [v for k, v in dotenv_values(proyecto.parent / "airflow-medallon" / ".env").items() if k in ("_AIRFLOW_WWW_USER_PASSWORD", "FERNET_KEY", "POSTGRES_PASSWORD", "AIRFLOW__API_AUTH__JWT_SECRET")]
    secretos.append("Docker-ficticia-0123456789")
    assert len(secretos) == 5 and all(s not in todo for s in secretos)
    assert "docker compose up airflow-init" in todo and "http://127.0.0.1:8082" in todo and "_AIRFLOW_WWW_USER_PASSWORD" in todo


def test_verificar_es_de_solo_lectura_e_idempotente_y_detecta_un_nombre_distinto(proyecto):
    ejecutar = {"ejecutar": _docker_ok, "comprobar_puerto": lambda p: True}
    destino = proyecto.parent / "airflow-medallon"
    assert any(not ok for ok, _ in pa.verificar(proyecto, destino, **ejecutar))          # antes de preparar hay cosas que faltan
    assert not destino.exists()                                                           # y verificar no creó nada
    _preparar(proyecto)

    def foto():
        return {p.relative_to(destino).as_posix(): (p.stat().st_mtime_ns, p.read_bytes()) for p in destino.rglob("*") if p.is_file()}
    antes = foto()
    primera = pa.verificar(proyecto, destino, **ejecutar)
    segunda = pa.verificar(proyecto, destino, **ejecutar)
    assert all(ok for ok, _ in primera) and primera == segunda and foto() == antes
    renombrado = proyecto.parent / "Otro nombre"
    proyecto.rename(renombrado)
    filas = pa.verificar(renombrado, destino, **ejecutar)
    assert any((not ok) and "PROYECTO_NOMBRE" in texto for ok, texto in filas)


def test_los_valores_con_espacios_se_escriben_entre_comillas_y_se_leen_igual(tmp_path):
    ruta = tmp_path / ".env"
    pa.escribir_env(ruta, {"A": "Proyecto con espacios", "B": "sin-espacios_1=", "C": "con$dolar"})
    assert dotenv_values(ruta)["A"] == "Proyecto con espacios" and dotenv_values(ruta)["B"] == "sin-espacios_1="
    assert "$$" in ruta.read_text(encoding="utf-8")        # Compose interpreta `$`: se duplica para que llegue tal cual


def test_el_script_reutiliza_la_copia_del_dag_de_sincronizar_dag_sin_duplicarla():
    texto = (RUTA / "preparar_airflow.py").read_text(encoding="utf-8")
    assert "sincronizar_dag.sincronizar(" in texto and "shutil.copy2(dag" not in texto and "hashlib" not in texto
