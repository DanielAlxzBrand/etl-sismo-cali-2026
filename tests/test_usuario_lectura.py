"""Usuario de MySQL de solo lectura (sismo_lectura) para phpMyAdmin (D91): solo SELECT sobre la base real, origen sin comodines, contraseña solo en .env e idempotencia, con conexiones simuladas.

Por qué existe: phpMyAdmin se usa para mirar los datos y no debe poder cambiarlos; la garantía es que la cuenta no tiene ningún privilegio de escritura, así que MySQL rechaza el intento
aunque alguien lo teclee en la pestaña SQL. Estas pruebas no necesitan MySQL; la comprobación en vivo (una escritura rechazada) está en EV-083.
"""
import argparse
import logging

import pytest
from dotenv import dotenv_values

from src.common import ROOT, load_config
from test_configurar_mysql import BASES, CLAVE_ADMIN, ConexionFalsa, cm, esc

GRANTS_OK = ["GRANT USAGE ON *.* TO `sismo_lectura`@`localhost`", f"GRANT SELECT ON `{BASES[0]}`.* TO `sismo_lectura`@`localhost`"]


def _args(**kw):
    return argparse.Namespace(**{"usuario_admin": "root", "rotar": False, "solo_verificar": False, "usuario_lectura": True, "usuario_docker": False, "origen": None, **kw})


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
    return cm.configurar_lectura(load_config(), _args(**kw), lambda u, c: admin, pedir_clave=pedir, ruta_env=env), pedidas


def test_el_unico_privilegio_es_select_y_la_cuenta_es_distinta_de_las_otras_dos():
    assert cm.PRIVILEGIOS_LECTURA == ("SELECT",)
    assert cm.USUARIO_LECTURA == "sismo_lectura" and cm.USUARIO_LECTURA not in (cm.USUARIO, cm.USUARIO_DOCKER)
    assert cm.NOMBRES_ENV_LECTURA == ("MYSQL_LECTURA_USER", "MYSQL_LECTURA_PASSWORD") and cm.ORIGEN_LECTURA == "localhost"


def test_el_grant_es_exactamente_select_sobre_la_base_real(entorno):
    admin = ConexionFalsa(concesiones=GRANTS_OK)
    escritas, pedidas = _correr(entorno, admin)
    assert escritas == ["MYSQL_LECTURA_USER", "MYSQL_LECTURA_PASSWORD"] and len(pedidas) == 1
    grants = [(s, p) for s, p in admin.llamadas if s.startswith("GRANT")]
    assert grants == [(f"GRANT SELECT ON `{BASES[0]}`.* TO %s@%s", ("sismo_lectura", "localhost"))]
    assert all(palabra not in grants[0][0].upper() for palabra in ("INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER", "INDEX", "REFERENCES", "ALL", "GRANT OPTION", "*.*", BASES[1].upper()))
    crear = [p for s, p in admin.llamadas if s.startswith("CREATE USER")]
    assert len(crear) == 1 and crear[0][:2] == ("sismo_lectura", "localhost")
    v = dotenv_values(entorno)
    assert v["MYSQL_LECTURA_USER"] == "sismo_lectura" and cm.clave_fuerte(v["MYSQL_LECTURA_PASSWORD"]) and v["HTTP_USER_AGENT"] == "Equipo-Prueba"
    assert admin.cerrada


@pytest.mark.parametrize("origen", ["%", "192.168.%", "10.%.%.%", "host_docker", "0.0.0.0", "8.8.8.8", "x'; DROP USER 'y", "192.168.1.*"])
def test_un_origen_con_comodin_o_publico_se_rechaza_antes_de_pedir_la_contrasena(entorno, origen):
    admin = ConexionFalsa(concesiones=GRANTS_OK)
    pedidas = []
    with pytest.raises(cm.ConfiguracionError):
        cm.configurar_lectura(load_config(), _args(origen=origen), lambda u, c: admin, pedir_clave=lambda m: pedidas.append(m) or CLAVE_ADMIN, ruta_env=entorno)
    assert admin.llamadas == [] and pedidas == []


def test_la_contrasena_nunca_va_en_sql_ni_en_el_registro_ni_en_pantalla_y_la_del_admin_no_llega_a_env(entorno, caplog, capsys):
    admin = ConexionFalsa(concesiones=GRANTS_OK)
    with caplog.at_level(logging.DEBUG):
        _correr(entorno, admin)
    clave = dotenv_values(entorno)["MYSQL_LECTURA_PASSWORD"]
    crear = [p for s, p in admin.llamadas if s.startswith("CREATE USER")][0]
    assert crear[2] == clave                                    # la contraseña viaja como parámetro, no dentro del texto SQL
    assert all(clave not in s and CLAVE_ADMIN not in s for s, _ in admin.llamadas)
    salida = capsys.readouterr()
    assert clave not in caplog.text + salida.out + salida.err and CLAVE_ADMIN not in caplog.text + salida.out + salida.err
    assert CLAVE_ADMIN not in entorno.read_text(encoding="utf-8")


@pytest.mark.parametrize("concesiones", [
    ["GRANT ALL PRIVILEGES ON *.* TO `sismo_lectura`@`localhost`"],
    GRANTS_OK[:1] + [f"GRANT SELECT ON `{BASES[0]}`.* TO `sismo_lectura`@`localhost` WITH GRANT OPTION"],
    GRANTS_OK[:1] + [f"GRANT SELECT, INSERT ON `{BASES[0]}`.* TO `sismo_lectura`@`localhost`"],
    GRANTS_OK[:1] + [f"GRANT SELECT, UPDATE, DELETE ON `{BASES[0]}`.* TO `sismo_lectura`@`localhost`"],
    GRANTS_OK[:1] + [f"GRANT ALL PRIVILEGES ON `{BASES[0]}`.* TO `sismo_lectura`@`localhost`"],
    GRANTS_OK + [f"GRANT SELECT ON `{BASES[1]}`.* TO `sismo_lectura`@`localhost`"],
    GRANTS_OK[:1],
], ids=["globales", "con GRANT OPTION", "SELECT e INSERT", "escritura y borrado", "ALL en la base", "también la base de prueba", "sin ningún permiso"])
def test_una_cuenta_con_algo_distinto_de_solo_select_se_rechaza_y_no_se_escribe_env(entorno, concesiones):
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
    vieja = dotenv_values(entorno)["MYSQL_LECTURA_PASSWORD"]
    admin = ConexionFalsa(existe=True, concesiones=GRANTS_OK)
    escritas, pedidas = _correr(entorno, admin, rotar=True)
    assert dotenv_values(entorno)["MYSQL_LECTURA_PASSWORD"] != vieja and "MYSQL_LECTURA_PASSWORD" in escritas and len(pedidas) == 1
    assert any(s.startswith("ALTER USER") for s, _ in admin.llamadas) and not any(s.startswith("CREATE USER") for s, _ in admin.llamadas)


def test_solo_verificar_no_escribe_y_exige_usuario_y_env(entorno):
    with pytest.raises(cm.ConfiguracionError):                       # sin variables en .env
        _correr(entorno, ConexionFalsa(existe=True, concesiones=GRANTS_OK), solo_verificar=True)
    _correr(entorno, ConexionFalsa(concesiones=GRANTS_OK))
    antes = entorno.read_text(encoding="utf-8")
    escritas, _ = _correr(entorno, ConexionFalsa(existe=True, concesiones=GRANTS_OK), solo_verificar=True)
    assert escritas == [] and entorno.read_text(encoding="utf-8") == antes
    with pytest.raises(cm.ConfiguracionError):                       # la cuenta no existe en el servidor
        _correr(entorno, ConexionFalsa(existe=False, concesiones=GRANTS_OK), solo_verificar=True)


def test_se_niega_si_env_no_esta_ignorado(entorno, monkeypatch):
    monkeypatch.setattr(cm, "env_ignorado_y_no_versionado", lambda raiz=None: False)
    with pytest.raises(cm.ConfiguracionError, match="ignorado"):
        _correr(entorno, ConexionFalsa(concesiones=GRANTS_OK))


def test_la_linea_de_comandos_no_mezcla_las_dos_cuentas_y_el_origen_solo_va_con_una_de_ellas():
    with pytest.raises(SystemExit):
        cm.main(["--usuario-lectura", "--usuario-docker", "--origen", "localhost"])
    with pytest.raises(SystemExit):
        cm.main(["--origen", "localhost"])
    with pytest.raises(SystemExit):
        cm.main(["--usuario-docker"])


def test_las_cuentas_de_docker_y_de_lectura_comparten_el_mismo_codigo_pero_no_los_privilegios(entorno):
    docker = ConexionFalsa(concesiones=["GRANT USAGE ON *.* TO `sismo_airflow`@`localhost`",
                                        f"GRANT SELECT, INSERT, CREATE, INDEX, REFERENCES ON `{BASES[0]}`.* TO `sismo_airflow`@`localhost`"])
    cm.aplicar_docker(docker, BASES[0], "localhost", False, "x")
    assert [s for s, _ in docker.llamadas if s.startswith("GRANT")] == [f"GRANT SELECT, INSERT, CREATE, INDEX, REFERENCES ON `{BASES[0]}`.* TO %s@%s"]
    assert not set(cm.PRIVILEGIOS_DOCKER) <= set(cm.PRIVILEGIOS_LECTURA)


# --- nombres de las variables: .env.example y comprobación canario del escáner
def test_env_example_lista_los_nombres_de_la_cuenta_de_lectura_sin_valores():
    texto = (ROOT / ".env.example").read_text(encoding="utf-8")
    for nombre in cm.NOMBRES_ENV_LECTURA:
        assert f"\n{nombre}=\n" in "\n" + texto + "\n", nombre


def test_el_escaner_trata_la_contrasena_de_lectura_como_canario_explicito():
    assert "MYSQL_LECTURA_PASSWORD" in esc.VARIABLES_CANARIO
    assert {"MYSQL_PASSWORD", "MYSQL_DOCKER_PASSWORD"} <= set(esc.VARIABLES_CANARIO)


def test_el_canario_encuentra_la_contrasena_de_lectura_en_otro_archivo_sin_imprimirla(tmp_path):
    (tmp_path / ".env").write_text("MYSQL_LECTURA_USER=sismo_lectura\nMYSQL_LECTURA_PASSWORD=Lectura-ficticia-0123456789\n", encoding="utf-8")
    assert "MYSQL_LECTURA_PASSWORD" in esc.canarios(tmp_path) and "MYSQL_LECTURA_USER" not in esc.canarios(tmp_path)
    (tmp_path / "notas.txt").write_text("copia de Lectura-ficticia-0123456789 por error\n", encoding="utf-8")
    hallazgos = esc.canario_arbol(tmp_path, esc.canarios(tmp_path))
    assert hallazgos == [("notas.txt", 1, "canario:MYSQL_LECTURA_PASSWORD")]
    assert "Lectura-ficticia" not in repr(hallazgos)
