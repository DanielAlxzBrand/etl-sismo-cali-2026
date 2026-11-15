"""`scripts/preparar_entorno.py` con simulaciones de cada caso, sin tocar el equipo: Python equivocado, entorno ausente, requisitos distintos, `.env` incompleto, MySQL apagado, Docker apagado y puertos ocupados (D93).

Por qué existe: las otras dos personas del grupo tienen un Python más reciente que el 3.13 y deben poder saber, antes de ejecutar nada, qué les falta y qué hacer. El script solo lee (salvo `--instalar`, que pide
confirmación) y nunca muestra un valor del `.env`; aquí se comprueba cada diagnóstico con un proyecto de mentira y procesos simulados.
"""
import importlib.util
import subprocess
import sys

import pytest

from src.common import ROOT

sys.path.insert(0, str(ROOT / "scripts" / "orquestacion"))
_espec = importlib.util.spec_from_file_location("preparar_entorno_prueba", ROOT / "scripts" / "preparar_entorno.py")
pe = importlib.util.module_from_spec(_espec)
_espec.loader.exec_module(pe)

PY_L = " -V:3.13 *        C:\\Python313\\python.exe\n -V:3.11          C:\\Python311\\python.exe\n"
REQUISITOS = "pandas==3.0.6\nPyYAML==6.0.3\nrequests==2.34.2\n# comentario\n"
VALORES_SECRETOS = ("Clave-de-mysql-ficticia-0123", "Clave-docker-ficticia-0123", "Clave-lectura-ficticia-0123")


def _cp(salida="", codigo=0):
    return subprocess.CompletedProcess([], codigo, stdout=salida, stderr="")


class Mundo:
    """Ejecutor de procesos simulado: responde según el comando, y registra lo ejecutado."""

    def __init__(self, py=PY_L, venv="3.13", paquetes=None, check=0, docker=True, compose=True):
        self.py, self.venv, self.check, self.docker, self.compose = py, venv, check, docker, compose
        self.paquetes = paquetes if paquetes is not None else {"pandas": "3.0.6", "pyyaml": "6.0.3", "requests": "2.34.2"}
        self.llamadas = []

    def __call__(self, cmd, **kw):
        self.llamadas.append(cmd)
        if cmd[:2] == ["py", "-0p"]:
            if self.py is None:
                raise FileNotFoundError("py")
            return _cp(self.py)
        if cmd[0] == "docker":
            if not self.docker:
                return _cp("", 1)
            if cmd[1] == "version":
                return _cp("29.0.0\n")
            return _cp("5.0.0\n") if self.compose else _cp("", 1)
        if "import sys" in " ".join(cmd):
            return _cp(self.venv + "\n")
        if cmd[1:4] == ["-m", "pip", "list"]:
            import json
            return _cp(json.dumps([{"name": n, "version": v} for n, v in self.paquetes.items()]))
        if cmd[1:4] == ["-m", "pip", "check"]:
            return _cp("", self.check)
        return _cp("")


@pytest.fixture()
def proyecto(tmp_path):
    (tmp_path / ".venv" / "Scripts").mkdir(parents=True)
    (tmp_path / ".venv" / "Scripts" / "python.exe").write_bytes(b"")
    (tmp_path / "requirements.txt").write_text(REQUISITOS, encoding="utf-8")
    nombres = pe.NOMBRES_ENV_COMPLETO
    (tmp_path / ".env").write_text("".join(f"{n}={VALORES_SECRETOS[i % 3]}\n" for i, n in enumerate(nombres)), encoding="utf-8")
    return tmp_path


def _diag(proyecto, mundo=None, libres=lambda p: True, alcanzable=lambda h, p: True, actual=(3, 13)):
    return {r.nombre: r for r in pe.diagnosticar(proyecto, mundo or Mundo(), libres, alcanzable, actual)}


def test_todo_en_orden_da_todo_correcto_en_los_dos_modos(proyecto):
    r = _diag(proyecto)
    assert all(x.ok for x in r.values())
    for modo in pe.AMBOS:
        texto, bien = pe.formatear(list(r.values()), modo)
        assert bien and "✗" not in texto


def test_python_313_se_busca_con_py_0p_aunque_haya_uno_mas_nuevo_y_si_falta_se_dice_que_hacer(proyecto):
    assert pe.pythons_instalados(Mundo()) == {"3.13": "C:\\Python313\\python.exe", "3.11": "C:\\Python311\\python.exe"}
    nuevo = " -V:3.14 *   C:\\Python314\\python.exe\n -V:3.12   C:\\Python312\\python.exe\n"
    r = _diag(proyecto, Mundo(py=nuevo), actual=(3, 14))["Python 3.13"]
    assert not r.ok and "3.14" in r.detalle and "EN PARALELO" in r.accion and "py launcher" in r.accion
    con_ambos = _diag(proyecto, Mundo(py=nuevo + " -V:3.13   C:\\Python313\\python.exe\n"), actual=(3, 14))["Python 3.13"]
    assert con_ambos.ok and "3.14" in con_ambos.detalle           # lo avisa pero usa la 3.13
    sin_lanzador = _diag(proyecto, Mundo(py=None), actual=(3, 11))["Python 3.13"]
    assert not sin_lanzador.ok and "lanzador" in sin_lanzador.detalle
    assert _diag(proyecto, Mundo(py=None), actual=(3, 13))["Python 3.13"].ok         # sin lanzador pero ejecutando con 3.13


def test_el_formato_antiguo_del_lanzador_tambien_se_entiende():
    assert pe.pythons_instalados(Mundo(py=" -3.13-64 *        C:\\Python313\\python.exe\n -3.11-64          C:\\Python311\\python.exe\n")).keys() == {"3.13", "3.11"}


def test_entorno_virtual_ausente_o_de_otra_version(proyecto):
    (proyecto / ".venv" / "Scripts" / "python.exe").unlink()
    r = _diag(proyecto)["Entorno virtual .venv"]
    assert not r.ok and "py -3.13 -m venv .venv" in r.accion
    assert not _diag(proyecto)["Requisitos instalados"].ok and _diag(proyecto)["Requisitos instalados"].detalle == "falta el entorno virtual"
    (proyecto / ".venv" / "Scripts" / "python.exe").write_bytes(b"")
    otra = _diag(proyecto, Mundo(venv="3.11"))["Entorno virtual .venv"]
    assert not otra.ok and "3.11" in otra.detalle and "Bórrelo" in otra.accion


def test_requisitos_con_otra_version_o_con_conflictos_de_pip_check(proyecto):
    distinto = _diag(proyecto, Mundo(paquetes={"pandas": "3.1.1", "pyyaml": "6.0.3", "requests": "2.34.2"}))["Requisitos instalados"]
    assert not distinto.ok and "1 de 3" in distinto.detalle and "pandas" in distinto.detalle and "pip install -r requirements.txt" in distinto.accion
    ausente = _diag(proyecto, Mundo(paquetes={"pandas": "3.0.6"}))["Requisitos instalados"]
    assert not ausente.ok and "2 de 3" in ausente.detalle
    conflicto = _diag(proyecto, Mundo(check=1))["Requisitos instalados"]
    assert not conflicto.ok and "pip check" in conflicto.detalle
    assert pe.requisitos_fijados(proyecto) == {"pandas": "3.0.6", "pyyaml": "6.0.3", "requests": "2.34.2"}


def test_env_ausente_o_incompleto_dice_solo_los_nombres_que_faltan_y_nunca_un_valor(proyecto):
    (proyecto / ".env").write_text("MYSQL_HOST=127.0.0.1\nMYSQL_PASSWORD=" + VALORES_SECRETOS[0] + "\n", encoding="utf-8")
    r = _diag(proyecto)[".env del proyecto"]
    assert not r.ok and "MYSQL_LECTURA_PASSWORD" in r.detalle and "MYSQL_HOST" not in r.detalle and VALORES_SECRETOS[0] not in r.detalle + r.accion
    (proyecto / ".env").unlink()
    assert not _diag(proyecto)[".env del proyecto"].ok and "no existe" in _diag(proyecto)[".env del proyecto"].detalle


def test_mysql_apagado_se_detecta_con_un_socket_y_se_dice_que_servicio_iniciar(proyecto):
    r = _diag(proyecto, alcanzable=lambda h, p: False)["MySQL"]
    assert not r.ok and "MySQL80" in r.accion and "MYSQL_HOST" in r.detalle and "valor-propio" not in r.detalle      # nombra las variables, no su valor
    (proyecto / ".env").unlink()
    assert "127.0.0.1:3306" in _diag(proyecto, alcanzable=lambda h, p: False)["MySQL"].detalle                  # sin .env, el valor por defecto sí se dice
    visto = []
    _diag(proyecto, alcanzable=lambda h, p: visto.append((h, p)) or True)
    assert visto and visto[0][1] in ("3306", 3306, str(visto[0][1]))
    assert pe.mysql_alcanzable("127.0.0.1", 9, tiempo=0.2) in (True, False)        # el socket real no lanza excepciones


@pytest.mark.parametrize("mundo", [Mundo(docker=False), Mundo(compose=False), Mundo()], ids=["apagado", "sin compose", "encendido"])
def test_docker_apagado_o_sin_compose_o_encendido(proyecto, mundo):
    r = _diag(proyecto, mundo)["Docker"]
    assert r.ok == (mundo.docker and mundo.compose)
    if not r.ok:
        assert "Docker" in r.accion


def test_cada_puerto_ocupado_se_dice_por_separado_y_los_de_airflow_y_phpmyadmin_solo_cuentan_en_el_modo_completo(proyecto):
    r = _diag(proyecto, libres=lambda p: p not in (8501, 8080))
    assert not r["Puerto 8501 (panel)"].ok and not r["Puerto 8080 (Airflow)"].ok and r["Puerto 8000 (API)"].ok and r["Puerto 8081 (phpMyAdmin)"].ok
    minimo, bien_minimo = pe.formatear(list(r.values()), pe.MINIMO)
    completo, bien_completo = pe.formatear(list(r.values()), pe.COMPLETO)
    assert not bien_minimo and "✗ Puerto 8501" in minimo and "· Puerto 8080" in minimo and "✗ Puerto 8080" not in minimo
    assert not bien_completo and "✗ Puerto 8080" in completo
    solo_airflow = _diag(proyecto, libres=lambda p: p != 8080)
    assert pe.formatear(list(solo_airflow.values()), pe.MINIMO)[1] and not pe.formatear(list(solo_airflow.values()), pe.COMPLETO)[1]


def test_el_informe_no_contiene_ningun_valor_del_env(proyecto):
    texto, _ = pe.formatear(list(_diag(proyecto, alcanzable=lambda h, p: False, libres=lambda p: False).values()), pe.COMPLETO)
    assert all(v not in texto for v in VALORES_SECRETOS) and "valor-propio" not in texto
    from dotenv import dotenv_values
    assert all(v not in texto for v in dotenv_values(proyecto / ".env").values())


def test_el_diagnostico_es_de_solo_lectura_y_no_crea_nada(proyecto):
    antes = sorted(p.relative_to(proyecto).as_posix() for p in proyecto.rglob("*"))
    mundo = Mundo()
    _diag(proyecto, mundo)
    assert sorted(p.relative_to(proyecto).as_posix() for p in proyecto.rglob("*")) == antes
    assert not any(c[1:3] == ["-m", "venv"] or c[:3] == ["py", "-3.13", "-m"] or "install" in c for c in mundo.llamadas)


def test_instalar_pide_confirmacion_y_sin_un_si_no_hace_nada(proyecto, tmp_path):
    (proyecto / ".venv" / "Scripts" / "python.exe").unlink()
    mundo, texto = Mundo(), []
    assert pe.instalar(proyecto, preguntar=lambda m: "n", ejecutar=mundo, salida=texto.append) == 1
    assert mundo.llamadas == [] and "No se hizo nada." in texto
    assert pe.instalar(proyecto, preguntar=lambda m: "", ejecutar=mundo, salida=texto.append) == 1 and mundo.llamadas == []


def test_instalar_con_confirmacion_crea_el_entorno_con_py_313_e_instala_los_requisitos(proyecto):
    py = pe.python_del_entorno(proyecto)
    py.unlink()
    mundo = Mundo()
    assert pe.instalar(proyecto, preguntar=lambda m: "s", ejecutar=mundo, salida=lambda t: None) == 0
    assert mundo.llamadas[0][:4] == ["py", "-3.13", "-m", "venv"] and mundo.llamadas[1][1:] == ["-m", "pip", "install", "-r", "requirements.txt"]
    # con el entorno ya creado solo instala
    mundo2 = Mundo()
    py.write_bytes(b"")
    assert pe.instalar(proyecto, preguntar=lambda m: "si", ejecutar=mundo2, salida=lambda t: None) == 0 and len(mundo2.llamadas) == 1


def test_instalar_informa_si_falla_la_creacion_o_pip():
    class Falla:
        def __init__(self, en):
            self.en, self.n = en, 0

        def __call__(self, cmd, **kw):
            self.n += 1
            return _cp("", 1 if self.n == self.en else 0)
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as t:
        mensajes = []
        assert pe.instalar(Path(t), preguntar=lambda m: "s", ejecutar=Falla(1), salida=mensajes.append) == 1 and any("py -3.13" in m for m in mensajes)
        py = pe.python_del_entorno(t)
        py.parent.mkdir(parents=True)
        py.write_bytes(b"")
        mensajes = []
        assert pe.instalar(Path(t), preguntar=lambda m: "s", ejecutar=Falla(1), salida=mensajes.append) == 1 and any("requirements.txt falló" in m for m in mensajes)


def test_el_script_real_se_puede_ejecutar_y_no_instala_nada_sin_la_bandera():
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "preparar_entorno.py"), "--modo", "minimo"], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       cwd=ROOT, env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"})
    assert r.returncode in (0, 1) and "Python 3.13" in r.stdout and "Entorno virtual" in r.stdout and "Traceback" not in r.stderr
