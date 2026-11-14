"""Usuario de MySQL para Docker (sismo_airflow): origen validado, permisos mínimos sobre la base real, contraseñas solo en .env y creación idempotente, con conexiones simuladas."""
import argparse
import logging

import pytest
from dotenv import dotenv_values

from test_configurar_mysql import BASES, CLAVE_ADMIN, ConexionFalsa, cm

ORIGEN = "192.168.65.3"
GRANTS_OK = ["GRANT USAGE ON *.* TO `sismo_airflow`@`192.168.65.3`",
             f"GRANT SELECT, INSERT, CREATE, INDEX, REFERENCES ON `{BASES[0]}`.* TO `sismo_airflow`@`192.168.65.3`"]


def _args(**kw):
    return argparse.Namespace(**{"usuario_admin": "root", "rotar": False, "solo_verificar": False, "usuario_docker": True, "origen": ORIGEN, **kw})


@pytest.fixture()
def entorno(tmp_path, monkeypatch):
    monkeypatch.setattr(cm, "env_ignorado_y_no_versionado", lambda raiz=None: True)
    env = tmp_path / ".env"
    env.write_text("HTTP_USER_AGENT=Equipo-Prueba\n", encoding="utf-8")
    return env


def _correr(env, admin, **kw):
    pedidas = []

    def pedir(mensaje):
        pedidas.append(mensaje)
        return CLAVE_ADMIN
    from src.common import load_config
    return cm.configurar_docker(load_config(), _args(**kw), lambda u, c: admin, pedir_clave=pedir, ruta_env=env), pedidas


@pytest.mark.parametrize("origen", ["192.168.65.3", "10.0.0.0/255.255.0.0", "172.20.0.0/255.255.240.0", "host.docker.internal", "gateway.docker.internal", "localhost", "127.0.0.1"])
def test_origenes_validos(origen):
    assert cm.validar_origen(origen) == origen


@pytest.mark.parametrize("origen", ["", "   ", "%", "192.168.%", "10.%.%.%", "host_docker", "0.0.0.0", "8.8.8.8", "127.0.0.0/255.255.0.0", "10.0.0.0/255.0.0.0", "10.0.0.0/255.255.0.255",
                                    "8.8.0.0/255.255.0.0", "10.0.0.0/16", "10.0.0.0/", "a b", "x'; DROP USER 'y", "192.168.1.*", None])
def test_origenes_rechazados(origen):
    with pytest.raises(cm.ConfiguracionError):
        cm.validar_origen(origen)


def test_los_permisos_son_los_minimos_de_la_carga():
    assert set(cm.PRIVILEGIOS_DOCKER) == {"SELECT", "INSERT", "CREATE", "INDEX", "REFERENCES"}
    assert not {"UPDATE", "DELETE", "DROP", "ALTER", "ALL", "GRANT OPTION"} & set(cm.PRIVILEGIOS_DOCKER)
    assert cm.USUARIO_DOCKER == "sismo_airflow" and cm.USUARIO_DOCKER != cm.USUARIO


def test_crea_el_usuario_con_permisos_solo_sobre_la_base_real_y_escribe_nombres(entorno):
    admin = ConexionFalsa(concesiones=GRANTS_OK)
    escritas, pedidas = _correr(entorno, admin)
    assert escritas == ["MYSQL_DOCKER_USER", "MYSQL_DOCKER_PASSWORD", "MYSQL_DOCKER_ORIGEN"] and len(pedidas) == 1
    sql = [(s, p) for s, p in admin.llamadas]
    crear = [x for x in sql if x[0].startswith("CREATE USER")]
    grants = [x for x in sql if x[0].startswith("GRANT")]
    assert len(crear) == 1 and crear[0][1][:2] == ("sismo_airflow", ORIGEN)
    assert len(grants) == 1 and f"`{BASES[0]}`.*" in grants[0][0] and BASES[1] not in grants[0][0] and "GRANT OPTION" not in grants[0][0].upper() and "*.*" not in grants[0][0]
    v = dotenv_values(entorno)
    assert v["MYSQL_DOCKER_USER"] == "sismo_airflow" and v["MYSQL_DOCKER_ORIGEN"] == ORIGEN and v["HTTP_USER_AGENT"] == "Equipo-Prueba"
    assert cm.clave_fuerte(v["MYSQL_DOCKER_PASSWORD"])
    assert admin.cerrada


def test_las_contrasenas_nunca_van_en_sql_ni_en_registro_y_la_del_admin_no_llega_a_env(entorno, caplog):
    admin = ConexionFalsa(concesiones=GRANTS_OK)
    with caplog.at_level(logging.DEBUG):
        _correr(entorno, admin)
    clave = dotenv_values(entorno)["MYSQL_DOCKER_PASSWORD"]
    crear = [p for s, p in admin.llamadas if s.startswith("CREATE USER")][0]
    assert crear[2] == clave                                   # la contraseña viaja como parámetro
    assert all(clave not in s and CLAVE_ADMIN not in s for s, _ in admin.llamadas)
    assert CLAVE_ADMIN not in entorno.read_text(encoding="utf-8") and clave not in caplog.text and CLAVE_ADMIN not in caplog.text


def test_env_se_escribe_solo_despues_de_comprobar_los_permisos(entorno):
    antes = entorno.read_text(encoding="utf-8")
    excesivos = ["GRANT USAGE ON *.* TO `sismo_airflow`@`192.168.65.3`", f"GRANT ALL PRIVILEGES ON `{BASES[0]}`.* TO `sismo_airflow`@`192.168.65.3`"]
    with pytest.raises(cm.ConfiguracionError):
        _correr(entorno, ConexionFalsa(concesiones=excesivos))
    assert entorno.read_text(encoding="utf-8") == antes


@pytest.mark.parametrize("concesiones", [["GRANT ALL PRIVILEGES ON *.* TO `sismo_airflow`@`192.168.65.3`"],
                                         GRANTS_OK[:1] + [f"GRANT SELECT, INSERT, CREATE, INDEX, REFERENCES ON `{BASES[0]}`.* TO `sismo_airflow`@`192.168.65.3` WITH GRANT OPTION"],
                                         GRANTS_OK[:1] + [f"GRANT SELECT, INSERT, CREATE, INDEX, REFERENCES ON `{BASES[0]}`.* TO `sismo_airflow`@`192.168.65.3`",
                                                          f"GRANT SELECT ON `{BASES[1]}`.* TO `sismo_airflow`@`192.168.65.3`"],
                                         GRANTS_OK[:1] + [f"GRANT SELECT, INSERT, CREATE, INDEX, REFERENCES, DELETE ON `{BASES[0]}`.* TO `sismo_airflow`@`192.168.65.3`"],
                                         GRANTS_OK[:1] + [f"GRANT SELECT, INSERT ON `{BASES[0]}`.* TO `sismo_airflow`@`192.168.65.3`"]],
                         ids=["globales", "con GRANT OPTION", "otra base", "permiso de más", "permiso de menos"])
def test_permisos_distintos_de_los_esperados_se_rechazan(entorno, concesiones):
    antes = entorno.read_text(encoding="utf-8")
    with pytest.raises(cm.ConfiguracionError):
        _correr(entorno, ConexionFalsa(concesiones=concesiones))
    assert entorno.read_text(encoding="utf-8") == antes


def test_es_idempotente_y_no_pide_la_contrasena_si_el_env_esta_completo(entorno):
    _correr(entorno, ConexionFalsa(concesiones=GRANTS_OK))
    antes = entorno.read_text(encoding="utf-8")
    admin = ConexionFalsa(concesiones=GRANTS_OK)
    escritas, pedidas = _correr(entorno, admin)
    assert escritas == [] and pedidas == [] and admin.llamadas == [] and entorno.read_text(encoding="utf-8") == antes


def test_rotar_cambia_la_contrasena_con_alter_user(entorno):
    _correr(entorno, ConexionFalsa(concesiones=GRANTS_OK))
    vieja = dotenv_values(entorno)["MYSQL_DOCKER_PASSWORD"]
    admin = ConexionFalsa(existe=True, concesiones=GRANTS_OK)
    escritas, pedidas = _correr(entorno, admin, rotar=True)
    assert dotenv_values(entorno)["MYSQL_DOCKER_PASSWORD"] != vieja and "MYSQL_DOCKER_PASSWORD" in escritas and len(pedidas) == 1
    assert any(s.startswith("ALTER USER") for s, _ in admin.llamadas) and not any(s.startswith("CREATE USER") for s, _ in admin.llamadas)


def test_solo_verificar_no_escribe_y_exige_usuario_y_env(entorno):
    with pytest.raises(cm.ConfiguracionError):                       # sin variables en .env
        _correr(entorno, ConexionFalsa(existe=True, concesiones=GRANTS_OK), solo_verificar=True)
    _correr(entorno, ConexionFalsa(concesiones=GRANTS_OK))
    antes = entorno.read_text(encoding="utf-8")
    escritas, _ = _correr(entorno, ConexionFalsa(existe=True, concesiones=GRANTS_OK), solo_verificar=True)
    assert escritas == [] and entorno.read_text(encoding="utf-8") == antes
    with pytest.raises(cm.ConfiguracionError):                       # el usuario no existe para ese origen
        _correr(entorno, ConexionFalsa(existe=False, concesiones=GRANTS_OK), solo_verificar=True)


def test_un_origen_distinto_crea_otro_usuario_y_actualiza_el_env(entorno):
    _correr(entorno, ConexionFalsa(concesiones=GRANTS_OK))
    nuevo = "192.168.65.9"
    grants = [g.replace(ORIGEN, nuevo) for g in GRANTS_OK]
    admin = ConexionFalsa(concesiones=grants)
    escritas, _ = _correr(entorno, admin, origen=nuevo)
    assert "MYSQL_DOCKER_ORIGEN" in escritas and dotenv_values(entorno)["MYSQL_DOCKER_ORIGEN"] == nuevo


def test_un_origen_con_comodin_se_rechaza_antes_de_pedir_la_contrasena(entorno):
    admin = ConexionFalsa(concesiones=GRANTS_OK)
    with pytest.raises(cm.ConfiguracionError):
        _correr(entorno, admin, origen="192.168.%")
    assert admin.llamadas == []


def test_se_niega_si_env_no_esta_ignorado(entorno, monkeypatch):
    monkeypatch.setattr(cm, "env_ignorado_y_no_versionado", lambda raiz=None: False)
    with pytest.raises(cm.ConfiguracionError, match="ignorado"):
        _correr(entorno, ConexionFalsa(concesiones=GRANTS_OK))


def test_la_linea_de_comandos_exige_usuario_docker_y_origen_juntos():
    with pytest.raises(SystemExit):
        cm.main(["--usuario-docker"])
    with pytest.raises(SystemExit):
        cm.main(["--origen", ORIGEN])
