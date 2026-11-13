"""Configuración de MySQL y manejo de credenciales, sin servidor: conexiones simuladas, `.env` atómico, enmascarado del registro y comprobación canario."""
import argparse
import importlib.util
import logging
import re
import subprocess

import pytest

from src.common import ROOT, load_config
from src.logger import EnmascararSecretos


def _cargar(ruta, nombre):
    espec = importlib.util.spec_from_file_location(nombre, ROOT / ruta)
    modulo = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(modulo)
    return modulo


cm = _cargar("scripts/mysql/configurar_mysql.py", "configurar_mysql_prueba")
esc = _cargar("scripts/escanear_secretos.py", "escanear_secretos_prueba")
CLAVE_ADMIN = "clave-del-administrador-ficticia"   # valor inventado: la prueba comprueba que jamás se guarda ni se pasa a SQL
BASES = ("sismo_cali", "sismo_cali_prueba")


class CursorFalso:
    def __init__(self, conn):
        self.conn = conn

    def execute(self, sql, params=()):
        self.conn.llamadas.append((sql, tuple(params)))
        self.filas = self.conn.responder(sql)

    def fetchall(self):
        return self.filas

    def close(self):
        pass


class ConexionFalsa:
    """Registra todo lo que se ejecuta; `responder` decide las filas según la consulta."""

    def __init__(self, existe=False, concesiones=None):
        self.llamadas, self.cerrada, self.existe = [], False, existe
        self.concesiones = concesiones if concesiones is not None else [
            "GRANT USAGE ON *.* TO `sismo_etl`@`localhost`",
            f"GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, INDEX, REFERENCES ON `{BASES[0]}`.* TO `sismo_etl`@`localhost`",
            f"GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, INDEX, REFERENCES ON `{BASES[1]}`.* TO `sismo_etl`@`localhost`"]

    def responder(self, sql):
        if "VERSION()" in sql:
            return [("8.0.45",)]
        if "lower_case_table_names" in sql:
            return [(1,)]
        if "character_set_server" in sql:
            return [("utf8mb4",)]
        if "mysql.user" in sql:
            return [(1 if self.existe else 0,)]
        if "SHOW GRANTS" in sql:
            return [(g,) for g in self.concesiones]
        return []

    def cursor(self):
        return CursorFalso(self)

    def close(self):
        self.cerrada = True


@pytest.fixture()
def entorno(tmp_path, monkeypatch):
    monkeypatch.setattr(cm, "env_ignorado_y_no_versionado", lambda raiz=None: True)
    env = tmp_path / ".env"
    env.write_text("HTTP_USER_AGENT=Equipo-Prueba\n# comentario que debe conservarse\n", encoding="utf-8")
    return env


def _args(**kw):
    return argparse.Namespace(**{"usuario_admin": "root", "rotar": False, "solo_verificar": False, **kw})


def _ejecutar(env, admin, usuario, pedidas=None, **kw):
    registro = []

    def pedir(mensaje):
        registro.append(mensaje)
        return CLAVE_ADMIN
    escritas = cm.configurar(load_config(), _args(**kw), lambda u, c: admin, lambda c, b: usuario, pedir_clave=pedir, ruta_env=env)
    if pedidas is not None:
        pedidas.extend(registro)
    return escritas, registro


def test_primera_configuracion_crea_bases_usuario_y_escribe_solo_nombres(entorno):
    admin, usuario = ConexionFalsa(), ConexionFalsa()
    escritas, pedidas = _ejecutar(entorno, admin, usuario)
    assert escritas == ["MYSQL_HOST", "MYSQL_PORT", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE", "MYSQL_DATABASE_PRUEBA"]
    assert len(pedidas) == 1 and "no se muestra" in pedidas[0]
    sql = [s for s, _ in admin.llamadas]
    assert sum(s.startswith("CREATE DATABASE") for s in sql) == 2 and any(s.startswith("CREATE USER 'sismo_etl'@'localhost'") for s in sql)
    assert sum(s.startswith("GRANT") for s in sql) == 2 and all("ON `sismo_cali" in s for s in sql if s.startswith("GRANT"))
    assert admin.cerrada and usuario.cerrada


def test_la_contrasena_del_administrador_nunca_se_guarda_ni_llega_a_sql(entorno, caplog):
    admin, usuario = ConexionFalsa(), ConexionFalsa()
    with caplog.at_level(logging.DEBUG):
        _ejecutar(entorno, admin, usuario)
    assert CLAVE_ADMIN not in entorno.read_text(encoding="utf-8")
    assert all(CLAVE_ADMIN not in s and CLAVE_ADMIN not in str(p) for s, p in admin.llamadas + usuario.llamadas)
    assert CLAVE_ADMIN not in caplog.text


def test_la_contrasena_del_proyecto_va_como_parametro_y_solo_a_env(entorno, caplog):
    admin, usuario = ConexionFalsa(), ConexionFalsa()
    with caplog.at_level(logging.DEBUG):
        _ejecutar(entorno, admin, usuario)
    from dotenv import dotenv_values
    clave = dotenv_values(entorno)["MYSQL_PASSWORD"]
    assert cm.clave_fuerte(clave)
    crear = [(s, p) for s, p in admin.llamadas if s.startswith("CREATE USER")][0]
    assert "%s" in crear[0] and crear[1] == (clave,)
    assert all(clave not in s for s, _ in admin.llamadas + usuario.llamadas)   # nunca dentro del texto SQL
    assert clave not in caplog.text


def test_env_conserva_las_lineas_existentes_y_no_deja_temporales(entorno):
    _ejecutar(entorno, ConexionFalsa(), ConexionFalsa())
    texto = entorno.read_text(encoding="utf-8")
    assert "HTTP_USER_AGENT=Equipo-Prueba" in texto and "# comentario que debe conservarse" in texto
    assert sorted(p.name for p in entorno.parent.iterdir()) == [".env"]


def test_env_se_escribe_solo_si_la_conexion_del_usuario_funciona(entorno):
    class Falla(ConexionFalsa):
        def responder(self, sql):
            raise RuntimeError("acceso denegado")
    antes = entorno.read_text(encoding="utf-8")
    with pytest.raises(RuntimeError):
        _ejecutar(entorno, ConexionFalsa(), Falla())
    assert entorno.read_text(encoding="utf-8") == antes


def test_con_credenciales_validas_no_cambia_nada_ni_pide_la_contrasena_del_administrador(entorno):
    _ejecutar(entorno, ConexionFalsa(), ConexionFalsa())
    antes = entorno.read_text(encoding="utf-8")
    admin = ConexionFalsa()
    escritas, pedidas = _ejecutar(entorno, admin, ConexionFalsa())
    assert escritas == [] and pedidas == [] and admin.llamadas == []
    assert entorno.read_text(encoding="utf-8") == antes


def test_rotar_cambia_la_contrasena_con_alter_user(entorno):
    _ejecutar(entorno, ConexionFalsa(), ConexionFalsa())
    from dotenv import dotenv_values
    vieja = dotenv_values(entorno)["MYSQL_PASSWORD"]
    admin = ConexionFalsa(existe=True)
    escritas, pedidas = _ejecutar(entorno, admin, ConexionFalsa(), rotar=True)
    nueva = dotenv_values(entorno)["MYSQL_PASSWORD"]
    assert nueva != vieja and "MYSQL_PASSWORD" in escritas and len(pedidas) == 1
    assert any(s.startswith("ALTER USER 'sismo_etl'@'localhost'") for s, _ in admin.llamadas) and not any(s.startswith("CREATE USER") for s, _ in admin.llamadas)


def test_solo_verificar_no_modifica_ni_pide_la_contrasena(entorno):
    with pytest.raises(cm.ConfiguracionError):   # sin credenciales en .env no son válidas
        _ejecutar(entorno, ConexionFalsa(), ConexionFalsa(), solo_verificar=True)
    _ejecutar(entorno, ConexionFalsa(), ConexionFalsa())
    antes = entorno.read_text(encoding="utf-8")
    escritas, pedidas = _ejecutar(entorno, ConexionFalsa(), ConexionFalsa(), solo_verificar=True)
    assert escritas == [] and pedidas == [] and entorno.read_text(encoding="utf-8") == antes


@pytest.mark.parametrize("concesiones", [["GRANT ALL PRIVILEGES ON *.* TO `sismo_etl`@`localhost`"],
                                         ["GRANT USAGE ON *.* TO `sismo_etl`@`localhost`", f"GRANT SELECT ON `{BASES[0]}`.* TO `sismo_etl`@`localhost` WITH GRANT OPTION"],
                                         ["GRANT USAGE ON *.* TO `sismo_etl`@`localhost`", f"GRANT SELECT ON `{BASES[0]}`.* TO `sismo_etl`@`localhost`"],
                                         ["GRANT USAGE ON *.* TO `sismo_etl`@`localhost`", f"GRANT SELECT ON `{BASES[0]}`.* TO `sismo_etl`@`localhost`",
                                          f"GRANT SELECT ON `{BASES[1]}`.* TO `sismo_etl`@`localhost`", "GRANT SELECT ON `mysql`.* TO `sismo_etl`@`localhost`"]],
                         ids=["globales", "con GRANT OPTION", "falta una base", "base ajena"])
def test_privilegios_incorrectos_se_rechazan_y_no_se_escribe_env(entorno, concesiones):
    antes = entorno.read_text(encoding="utf-8")
    with pytest.raises(cm.ConfiguracionError):
        _ejecutar(entorno, ConexionFalsa(), ConexionFalsa(concesiones=concesiones))
    assert entorno.read_text(encoding="utf-8") == antes


def test_servidor_antiguo_se_rechaza(entorno):
    class Viejo(ConexionFalsa):
        def responder(self, sql):
            return [("5.7.44",)] if "VERSION()" in sql else super().responder(sql)
    with pytest.raises(cm.ConfiguracionError, match="8.0"):
        _ejecutar(entorno, Viejo(), ConexionFalsa())


def test_se_niega_a_guardar_credenciales_si_env_no_esta_ignorado(entorno, monkeypatch):
    monkeypatch.setattr(cm, "env_ignorado_y_no_versionado", lambda raiz=None: False)
    with pytest.raises(cm.ConfiguracionError, match="ignorado"):
        _ejecutar(entorno, ConexionFalsa(), ConexionFalsa())


def test_el_env_real_esta_ignorado_y_no_versionado():
    assert cm.env_ignorado_y_no_versionado(ROOT) is True


def test_la_contrasena_generada_es_fuerte_y_distinta_cada_vez():
    claves = {cm.generar_clave() for _ in range(50)}
    assert len(claves) == 50 and all(cm.clave_fuerte(c) for c in claves)
    assert not cm.clave_fuerte("corta") and not cm.clave_fuerte("a" * 40)
    assert all(re.fullmatch(r"[A-Za-z0-9_.+=-]+", c) for c in claves)   # sin comillas, espacios ni '#': segura en .env y en SQL


def test_actualizar_env_actualiza_agrega_y_conserva(tmp_path):
    env = tmp_path / ".env"
    env.write_text("A=1\n# nota\nB=2\n", encoding="utf-8")
    cm.actualizar_env(env, {"B": "otro", "C": "3"})
    assert env.read_text(encoding="utf-8").splitlines() == ["A=1", "# nota", "B=otro", "C=3"]
    cm.actualizar_env(tmp_path / "nuevo.env", {"X": "1"})
    assert (tmp_path / "nuevo.env").read_text(encoding="utf-8") == "X=1\n"


def test_el_script_de_configuracion_no_acepta_contrasenas_por_argumento():
    ap_texto = (ROOT / "scripts" / "mysql" / "configurar_mysql.py").read_text(encoding="utf-8")
    assert "--password" not in ap_texto and "--clave" not in ap_texto and "getpass" in ap_texto
    assert "os.environ" not in ap_texto.split("def main")[0].replace("os.environ.get", "")   # la contraseña del administrador no se lee del entorno


# ---------------------------------------------------------------- enmascarado del registro
def _mensaje(texto):
    r = logging.LogRecord("etl.prueba", logging.INFO, __file__, 1, texto, (), None)
    EnmascararSecretos().filter(r)
    return r.getMessage()


def test_el_registro_enmascara_el_valor_de_las_variables_de_env(tmp_path, monkeypatch):
    import src.logger as lg
    falso_root = tmp_path
    (falso_root / ".env").write_text("MYSQL_" + "PASSWORD" + "=Valor-De-Prueba-Con-Largo-Suficiente\nHTTP_USER_AGENT=Equipo\n", encoding="utf-8")
    monkeypatch.setattr(lg, "ROOT", falso_root)
    r = logging.LogRecord("etl.prueba", logging.INFO, __file__, 1, "fallo con Valor-De-Prueba-Con-Largo-Suficiente en el pie", (), None)
    EnmascararSecretos().filter(r)
    assert "Valor-De-Prueba" not in r.getMessage() and "***" in r.getMessage()
    r2 = logging.LogRecord("etl.prueba", logging.INFO, __file__, 1, "MYSQL_" + "PASSWORD" + "=algo-secreto-1234 y pass" + "word: otra-cosa", (), None)
    EnmascararSecretos().filter(r2)
    assert "algo-secreto" not in r2.getMessage() and "otra-cosa" not in r2.getMessage()


# ---------------------------------------------------------------- comprobación canario y escáner
VALOR = "Canario-" + "De-Prueba-" + "9f8e7d6c5b"   # valor inventado para sembrar


def _repo_con_env(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "prueba@ejemplo.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Prueba"], cwd=tmp_path, check=True)
    (tmp_path / ".gitignore").write_text(".env\n", encoding="utf-8")
    (tmp_path / ".env").write_text(f"MYSQL_{'PASSWORD'}={VALOR}\nHTTP_USER_AGENT=Equipo-Prueba\n", encoding="utf-8")
    (tmp_path / "limpio.txt").write_text("nada sensible\n", encoding="utf-8")
    subprocess.run(["git", "add", ".gitignore", "limpio.txt"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "inicio"], cwd=tmp_path, check=True)
    return tmp_path


def test_el_canario_lee_solo_variables_sensibles(tmp_path):
    repo = _repo_con_env(tmp_path)
    assert esc.canarios(repo) == {"MYSQL_PASSWORD": VALOR}


def test_el_canario_no_encuentra_nada_en_un_repositorio_limpio(tmp_path):
    repo = _repo_con_env(tmp_path)
    can = esc.canarios(repo)
    assert esc.canario_arbol(repo, can) == [] and esc.canario_historial(repo, can) == [] and esc.estado_de_env(repo) == []


def test_el_canario_detecta_la_contrasena_sembrada_sin_imprimirla(tmp_path, capsys):
    repo = _repo_con_env(tmp_path)
    (repo / "notas.txt").write_text(f"copiado por error: {VALOR}\n", encoding="utf-8")
    subprocess.run(["git", "add", "notas.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "error"], cwd=repo, check=True)
    (repo / "notas.txt").unlink()
    subprocess.run(["git", "commit", "-q", "-am", "se quita"], cwd=repo, check=True)
    assert esc.main(["--raiz", str(repo), "--canario-env"]) == 1
    salida = capsys.readouterr().out
    assert VALOR not in salida and "canario:MYSQL_PASSWORD" in salida and "historial:" in salida   # sigue en el historial aunque se haya borrado


def test_el_canario_detecta_la_contrasena_en_el_arbol_y_en_un_zip(tmp_path):
    import zipfile
    repo = _repo_con_env(tmp_path)
    (repo / "config.txt").write_text(f"clave={VALOR}\n", encoding="utf-8")
    can = esc.canarios(repo)
    assert [h[0] for h in esc.canario_arbol(repo, can)] == ["config.txt"]
    z = tmp_path.parent / (tmp_path.name + ".zip")
    with zipfile.ZipFile(z, "w") as f:
        f.writestr("dist/config.txt", f"clave={VALOR}\n")
    assert [h[0] for h in esc.canario_zip(z, can)] == ["zip:dist/config.txt"]


def test_el_escaner_detecta_una_asignacion_literal_de_la_contrasena_de_mysql():
    linea = "MYSQL_" + "PASSWORD" + "=Valor1234abcd"
    assert any("mysql" in h for h in esc.revisar_linea(linea))
    assert not any("mysql" in h for h in esc.revisar_linea("MYSQL_" + "PASSWORD" + "=<definir en .env>"))
    assert not any("mysql" in h for h in esc.revisar_linea("MYSQL_" + "PASSWORD"))


def test_el_escaner_avisa_si_env_no_esta_ignorado(tmp_path):
    repo = _repo_con_env(tmp_path)
    (repo / ".gitignore").write_text("", encoding="utf-8")
    assert (".env", 0, "env_no_ignorado") in esc.estado_de_env(repo)
