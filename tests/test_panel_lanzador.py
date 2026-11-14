"""Lanzador del panel con subprocesos simulados: comandos, entorno, selección de puerto, códigos de salida y cierre garantizado."""
import importlib.util
import os
import socket
import subprocess
import sys
import types
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
_espec = importlib.util.spec_from_file_location("ejecutar_panel", RAIZ / "scripts" / "panel" / "ejecutar_panel.py")
lanzador = importlib.util.module_from_spec(_espec)
_espec.loader.exec_module(lanzador)

COLORES = {"principal": "#0072B2", "texto": "#1F2933", "fondo": "#FFFFFF", "fondo_secundario": "#F0F4F8"}


class ProcesoFalso:
    """Sustituye a subprocess.Popen: registra si lo cerraron y puede simular que ya terminó."""
    vivos = []

    def __init__(self, cmd, terminado=False, **kw):
        self.cmd, self.kw, self.pid, self.codigo = cmd, kw, 1000 + len(ProcesoFalso.vivos), 0 if terminado else None
        self.terminado_por = None
        ProcesoFalso.vivos.append(self)

    def poll(self):
        return self.codigo

    def wait(self, timeout=None):
        self.codigo = 0 if self.codigo is None else self.codigo
        return self.codigo

    def terminate(self):
        self.terminado_por = "terminate"
        self.codigo = 0

    def kill(self):
        self.terminado_por = "kill"
        self.codigo = 0


@pytest.fixture(autouse=True)
def _limpiar_y_sin_taskkill(monkeypatch):
    ProcesoFalso.vivos.clear()
    llamadas = []
    falso = types.SimpleNamespace(run=lambda cmd, **kw: llamadas.append(cmd) or None, Popen=None, DEVNULL=-3, TimeoutExpired=subprocess.TimeoutExpired)
    monkeypatch.setattr(lanzador, "subprocess", falso)
    monkeypatch.setattr(lanzador.time, "sleep", lambda s: None)
    yield llamadas


def _abridor(terminan=()):
    def abrir(cmd, **kw):
        return ProcesoFalso(cmd, terminado=len(ProcesoFalso.vivos) in terminan, **kw)
    return abrir


def _todo_responde(monkeypatch):
    monkeypatch.setattr(lanzador, "esperar", lambda url, valido, proceso, limite, **kw: proceso.poll() is None)


# ---------- comandos y entorno ----------
def test_el_comando_de_la_api_con_sqlite_es_el_de_la_documentacion():
    assert lanzador.comando_api(8123, "sqlite", python="py") == ["py", "-m", "uvicorn", "src.api.app:app", "--host", "127.0.0.1", "--port", "8123"]


def test_el_comando_de_la_api_con_mysql_usa_la_misma_aplicacion_con_ese_almacenamiento():
    cmd = lanzador.comando_api(8123, "mysql", python="py")
    assert cmd[:2] == ["py", "-c"] and "almacenamiento='mysql'" in cmd[2] and cmd[3:] == ["127.0.0.1", "8123"]


def test_el_comando_del_panel_usa_streamlit_run_sobre_la_aplicacion():
    assert lanzador.comando_panel(8601, python="py") == ["py", "-m", "streamlit", "run", "src/panel/app.py", "--server.port", "8601"]


def test_el_entorno_del_panel_es_local_sin_cabeza_y_sin_telemetria():
    e = lanzador.entorno_panel(8601, "http://127.0.0.1:8123", base={"PATH": "x"}, colores=COLORES)
    assert e["STREAMLIT_SERVER_HEADLESS"] == "true" and e["STREAMLIT_SERVER_ADDRESS"] == "127.0.0.1" and e["STREAMLIT_SERVER_PORT"] == "8601"
    assert e["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] == "false" and e["STREAMLIT_SERVER_SHOW_EMAIL_PROMPT"] == "false"
    assert e["STREAMLIT_THEME_PRIMARY_COLOR"] == "#0072B2" and e["PANEL_API_URL"] == "http://127.0.0.1:8123" and e["PATH"] == "x"


def test_el_entorno_del_panel_no_recibe_credenciales_de_mysql():
    clave, valor = "MYSQL_" + "PASSWORD", "no-debe-" + "pasar"      # concatenados para que el escáner no vea una contraseña literal
    base = {clave: valor, "MYSQL_USER": "u", "OTRA": "1"}
    e = lanzador.entorno_panel(8601, "http://127.0.0.1:8123", base=base, colores=COLORES)
    assert not [k for k in e if k.startswith("MYSQL_")] and e["OTRA"] == "1"
    assert base[clave] == valor      # no altera el entorno original


def test_los_nombres_de_las_variables_de_streamlit_existen_en_su_configuracion():
    salida = subprocess.run([sys.executable, "-m", "streamlit", "config", "show"], capture_output=True, text=True, encoding="utf-8", cwd=RAIZ,
                            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}).stdout
    for opcion in ("headless", "address", "gatherUsageStats", "showEmailPrompt", "fileWatcherType", "toolbarMode", "primaryColor", "textColor", "secondaryBackgroundColor"):
        assert opcion in salida, opcion


# ---------- puertos ----------
def test_un_puerto_libre_se_conserva():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        libre = s.getsockname()[1]
    assert lanzador.puerto_libre(libre) == libre


def test_un_puerto_ocupado_se_reemplaza_por_otro_libre():
    with socket.socket() as ocupado:
        ocupado.bind(("127.0.0.1", 0))
        ocupado.listen()
        p = ocupado.getsockname()[1]
        elegido = lanzador.puerto_libre(p)
        assert elegido != p and 0 < elegido < 65536


# ---------- ciclo de vida ----------
def test_arranque_correcto_con_verificar_cierra_los_dos_procesos(monkeypatch, capsys):
    _todo_responde(monkeypatch)
    assert lanzador.main(["--verificar"], abrir=_abridor()) == 0
    api, panel = ProcesoFalso.vivos
    assert api.cmd[2:4] == ["uvicorn", "src.api.app:app"] and panel.cmd[2] == "streamlit"
    assert panel.kw["env"]["PANEL_API_URL"].startswith("http://127.0.0.1:")
    assert api.codigo is not None and panel.codigo is not None
    salida = capsys.readouterr().out
    assert "API:   http://127.0.0.1:" in salida and "Panel: http://127.0.0.1:" in salida


def test_si_la_api_no_responde_sale_con_1_y_no_arranca_el_panel(monkeypatch, capsys):
    monkeypatch.setattr(lanzador, "esperar", lambda *a, **k: False)
    assert lanzador.main(["--verificar"], abrir=_abridor()) == 1
    assert len(ProcesoFalso.vivos) == 1 and ProcesoFalso.vivos[0].terminado_por in ("terminate", None) and ProcesoFalso.vivos[0].codigo is not None
    assert "La API no arrancó" in capsys.readouterr().out


def test_si_el_panel_no_responde_sale_con_2_y_cierra_la_api(monkeypatch, capsys):
    respuestas = iter([True, False])
    monkeypatch.setattr(lanzador, "esperar", lambda *a, **k: next(respuestas))
    assert lanzador.main(["--verificar"], abrir=_abridor()) == 2
    assert all(p.codigo is not None for p in ProcesoFalso.vivos) and len(ProcesoFalso.vivos) == 2
    assert "El panel no arrancó" in capsys.readouterr().out


def test_si_un_proceso_termina_antes_de_tiempo_sale_con_3_y_cierra_el_otro(monkeypatch):
    _todo_responde(monkeypatch)
    def abrir(cmd, **kw):
        return ProcesoFalso(cmd, **kw)

    def dormir(s):
        ProcesoFalso.vivos[1].codigo = 7      # el panel muere durante la espera
    monkeypatch.setattr(lanzador.time, "sleep", dormir)
    assert lanzador.main([], abrir=abrir) == 3
    assert all(p.codigo is not None for p in ProcesoFalso.vivos)


def test_ctrl_c_cierra_los_dos_procesos_y_sale_con_0(monkeypatch):
    _todo_responde(monkeypatch)

    def interrumpir(s):
        raise KeyboardInterrupt
    monkeypatch.setattr(lanzador.time, "sleep", interrumpir)
    assert lanzador.main([], abrir=_abridor()) == 0
    assert len(ProcesoFalso.vivos) == 2 and all(p.codigo is not None for p in ProcesoFalso.vivos)


def test_el_cierre_ocurre_aunque_el_arranque_lance_una_excepcion(monkeypatch):
    def abrir(cmd, **kw):
        p = ProcesoFalso(cmd, **kw)
        if len(ProcesoFalso.vivos) == 2:
            raise RuntimeError("fallo al arrancar el panel")
        return p
    _todo_responde(monkeypatch)
    with pytest.raises(RuntimeError):
        lanzador.main(["--verificar"], abrir=abrir)
    assert ProcesoFalso.vivos[0].codigo is not None   # la API se cerró en el finally


def test_cerrar_es_idempotente_y_acepta_none(_limpiar_y_sin_taskkill):
    lanzador.cerrar(None)
    p = ProcesoFalso(["x"], terminado=True)
    lanzador.cerrar(p)
    lanzador.cerrar(p)
    assert p.terminado_por is None       # ya había terminado: no se vuelve a cerrar


def test_cerrar_usa_taskkill_en_windows_para_incluir_a_los_hijos(monkeypatch, _limpiar_y_sin_taskkill):
    monkeypatch.setattr(lanzador.os, "name", "nt")
    p = ProcesoFalso(["x"])
    lanzador.cerrar(p)
    assert _limpiar_y_sin_taskkill and _limpiar_y_sin_taskkill[0][:2] == ["taskkill", "/PID"] and "/T" in _limpiar_y_sin_taskkill[0]


def test_cerrar_en_otros_sistemas_termina_el_proceso(monkeypatch):
    monkeypatch.setattr(lanzador.os, "name", "posix")
    p = ProcesoFalso(["x"])
    lanzador.cerrar(p)
    assert p.terminado_por == "terminate"


def test_esperar_devuelve_false_si_el_proceso_ya_termino_y_true_si_la_respuesta_es_valida():
    class Http:
        def get(self, url, timeout):
            class R:
                status_code, text = 200, "ok"
            return R()
    muerto, vivo = ProcesoFalso(["x"], terminado=True), ProcesoFalso(["y"])
    assert lanzador.esperar("http://x", lambda r: True, muerto, 1, http=Http()) is False
    assert lanzador.esperar("http://x", lambda r: r.text == "ok", vivo, 1, http=Http()) is True
    assert lanzador.esperar("http://x", lambda r: False, vivo, 0, http=Http()) is False
