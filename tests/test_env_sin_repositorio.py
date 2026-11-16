"""Guardián de la comprobación de `.env` de `scripts/mysql/configurar_mysql.py` cuando la carpeta NO es un repositorio de Git (por ejemplo, el zip descomprimido), y de que con Git sigue igual de estricta.

Por qué existe: quien prueba el modo completo desde el zip no tiene `.git`; la comprobación de siempre (`git check-ignore` y `git ls-files`) falla con código 128 y la persona leía «.env no está ignorado por git o
está versionado», un mensaje falso (sin repositorio no se puede versionar nada). Ahora, sin repositorio, se acepta solo si el `.gitignore` ignora `.env` de forma efectiva y se avisa; con repositorio no cambia nada.
Todas las pruebas con un Git simulado no necesitan el programa git (no agregan omisiones); la comparación del evaluador de texto con Git de verdad corre solo si git está instalado, sin omitirse cuando no lo está.
Qué NO demuestra: que el `.gitignore` de otra persona sea correcto en reglas que no listamos aquí (patrones con carpetas intermedias, por ejemplo), ni que `.env` no se copie a mano a otro lugar.
"""
import argparse
import importlib.util
import logging
import shutil
import subprocess

import pytest

from src.common import ROOT


def _cargar(ruta, nombre):
    espec = importlib.util.spec_from_file_location(nombre, ROOT / ruta)
    modulo = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(modulo)
    return modulo


cm = _cargar("scripts/mysql/configurar_mysql.py", "configurar_mysql_sin_repositorio")


class GitFalso:
    """Reemplaza `subprocess.run` para los comandos de git: dice si hay repositorio, si ignora `.env` y si lo versiona; `ausente` simula que el programa no está instalado."""

    def __init__(self, repo=True, ignora=True, versionado=False, ausente=False):
        self.repo, self.ignora, self.versionado, self.ausente, self.llamadas = repo, ignora, versionado, ausente, []

    def __call__(self, cmd, **kw):
        self.llamadas.append(cmd[1])
        if self.ausente:
            raise FileNotFoundError("git")
        if cmd[1] == "rev-parse":
            codigo, salida = (0, "true\n") if self.repo else (128, "")
        elif cmd[1] == "check-ignore":
            codigo, salida = (0 if self.ignora and self.repo else (1 if self.repo else 128)), ""
        else:
            codigo, salida = (0 if self.versionado else 1) if self.repo else 128, ""
        return subprocess.CompletedProcess(cmd, codigo, stdout=salida, stderr="")


@pytest.fixture()
def carpeta(tmp_path):
    """Una carpeta de proyecto de mentira, sin `.git` ni `.gitignore`."""
    c = tmp_path / "proyecto zip"
    c.mkdir()
    return c


def _con_git(monkeypatch, **kw):
    git = GitFalso(**kw)
    monkeypatch.setattr(cm.subprocess, "run", git)
    return git


# ---------------------------------------------------------------- con repositorio: igual de estricta que siempre
@pytest.mark.parametrize("ignora, versionado, esperado", [(True, False, True), (False, False, False), (True, True, False), (False, True, False)])
def test_con_repositorio_git_decide_y_el_gitignore_de_texto_no_cuenta(carpeta, monkeypatch, ignora, versionado, esperado):
    (carpeta / ".gitignore").write_text(".env\n", encoding="utf-8")          # un .gitignore perfecto no salva lo que Git dice que está mal
    git = _con_git(monkeypatch, repo=True, ignora=ignora, versionado=versionado)
    assert cm.env_ignorado_y_no_versionado(carpeta) is esperado
    assert "check-ignore" in git.llamadas and "ls-files" in git.llamadas
    if not esperado:
        assert cm.evaluar_env(carpeta)[1] == cm.MENSAJE_ENV_CON_GIT           # el mensaje de siempre, solo cuando de verdad hay repositorio


def test_una_carpeta_git_que_falla_no_abre_la_puerta_a_la_comprobacion_de_texto(carpeta, monkeypatch):
    (carpeta / ".git").mkdir()
    (carpeta / ".gitignore").write_text(".env\n", encoding="utf-8")
    _con_git(monkeypatch, repo=False)                                           # Git responde 128 (por ejemplo, propiedad dudosa de la carpeta) pero el `.git` está en el disco
    assert cm.env_ignorado_y_no_versionado(carpeta) is False and cm.evaluar_env(carpeta)[1] == cm.MENSAJE_ENV_CON_GIT


def test_un_proyecto_dentro_de_otro_repositorio_usa_la_comprobacion_estricta(tmp_path, monkeypatch):
    padre = tmp_path / "repositorio ajeno"
    (padre / ".git").mkdir(parents=True)
    hijo = padre / "proyecto"
    hijo.mkdir()
    (hijo / ".gitignore").write_text(".env\n", encoding="utf-8")
    _con_git(monkeypatch, repo=True, ignora=False)
    assert cm.env_ignorado_y_no_versionado(hijo) is False
    _con_git(monkeypatch, repo=True, ignora=True)
    assert cm.env_ignorado_y_no_versionado(hijo) is True


# ---------------------------------------------------------------- sin repositorio: solo vale un .gitignore que ignore .env de verdad
CASOS = [(".env\n", True), ("/.env\n", True), (".env*\n", True), ("*.env\n", True), ("**/.env\n", True), (".*\n", True), ("*\n!.gitignore\n", True), ("# comentario\n.env\n", True),
         (".env\n!.env\n.env\n", True), ("!.env\n.env\n", True), (".*\n!.env.example\n", True),
         ("", False), (".env.example\n", False), (".env/\n", False), ("# .env\n", False), ("docs/.env\n", False), ("*.example\n", False), (".env\n!.env\n", False),
         (".env\n!.env*\n", False), ("*\n!.env\n", False)]
SOLO_TEXTO = [("﻿.env\n", True), (".env\r\n", True), (".env\r\n!.env\r\n", False)]      # el BOM y los saltos de Windows se tratan como en un archivo normal


@pytest.mark.parametrize("texto, esperado", CASOS + SOLO_TEXTO)
def test_el_gitignore_ignora_env_solo_si_la_ultima_regla_que_coincide_lo_ignora(texto, esperado):
    assert cm.gitignore_ignora_env(texto) is esperado


def test_el_evaluador_de_texto_coincide_con_git_cuando_git_esta_instalado(tmp_path):
    """Con Git de verdad (si está): cada caso de la tabla da lo mismo que `git check-ignore`; sin Git, la tabla de arriba ya fija lo esperado y esta comparación simplemente no corre."""
    if shutil.which("git") is None:
        return
    for i, (texto, esperado) in enumerate(CASOS):
        repo = tmp_path / f"repo{i}"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        (repo / ".gitignore").write_text(texto, encoding="utf-8", newline="\n")
        (repo / ".env").write_text("X=1\n", encoding="utf-8")
        git_dice = subprocess.run(["git", "check-ignore", "-q", ".env"], cwd=repo, capture_output=True).returncode == 0
        assert git_dice is esperado and cm.gitignore_ignora_env(texto) is esperado, f"caso {texto!r}: git dice {git_dice}"


def test_el_gitignore_real_del_proyecto_ignora_env_y_por_eso_sirve_en_el_zip():
    assert cm.gitignore_ignora_env((ROOT / ".gitignore").read_text(encoding="utf-8")) is True


def test_sin_repositorio_y_con_gitignore_bueno_se_acepta_y_se_avisa(carpeta, monkeypatch, caplog):
    (carpeta / ".gitignore").write_text(".env\nlogs/\n", encoding="utf-8")
    _con_git(monkeypatch, repo=False)
    with caplog.at_level(logging.INFO):
        assert cm.env_ignorado_y_no_versionado(carpeta) is True
    assert "no es un repositorio de Git" in caplog.text and "no se versionará" in caplog.text


def test_con_repositorio_correcto_no_hay_aviso_de_repositorio_ausente(carpeta, monkeypatch, caplog):
    _con_git(monkeypatch, repo=True, ignora=True, versionado=False)
    with caplog.at_level(logging.INFO):
        assert cm.env_ignorado_y_no_versionado(carpeta) is True
    assert "no es un repositorio" not in caplog.text


@pytest.mark.parametrize("contenido, pista", [(None, "no tiene .gitignore"), (".env.example\n", "no deja ignorado"), (".env\n!.env\n", "no deja ignorado"), ("# .env\n", "no deja ignorado")])
def test_sin_repositorio_se_rechaza_con_un_mensaje_que_dice_que_hacer_y_no_habla_de_versionar(carpeta, monkeypatch, contenido, pista):
    if contenido is not None:
        (carpeta / ".gitignore").write_text(contenido, encoding="utf-8")
    _con_git(monkeypatch, repo=False)
    ok, mensaje = cm.evaluar_env(carpeta)
    assert ok is False and pista in mensaje and "no es un repositorio de Git" in mensaje and "ignorado" in mensaje
    assert "versionado" not in mensaje and "traceback" not in mensaje.lower()


def test_sin_el_programa_git_y_sin_repositorio_se_acepta_por_el_gitignore(carpeta, monkeypatch):
    (carpeta / ".gitignore").write_text(".env\n", encoding="utf-8")
    _con_git(monkeypatch, ausente=True)
    assert cm.evaluar_env(carpeta)[0] is True
    (carpeta / ".gitignore").write_text("", encoding="utf-8")
    assert cm.evaluar_env(carpeta)[0] is False


def test_sin_el_programa_git_pero_con_una_carpeta_git_se_rechaza_con_un_mensaje_claro_y_sin_traceback(carpeta, monkeypatch):
    (carpeta / ".git").mkdir()
    (carpeta / ".gitignore").write_text(".env\n", encoding="utf-8")
    _con_git(monkeypatch, ausente=True)
    ok, mensaje = cm.evaluar_env(carpeta)
    assert ok is False and "git no está instalado" in mensaje and "instale Git" in mensaje
    with pytest.raises(cm.ConfiguracionError, match="instale Git"):
        cm.exigir_env_protegido(carpeta)


# ---------------------------------------------------------------- los tres flujos usan la misma comprobación
class LlegoALaClave(Exception):
    """La guardia pasó y el flujo llegó a pedir la contraseña del administrador (no se escribe nada ni se conecta)."""


def _pedir_clave(_):
    raise LlegoALaClave


def _sin_conexion(*a, **k):
    raise AssertionError("no debe conectarse a MySQL antes de pasar la guardia")


def _flujos(ruta_env):
    cfg = {"almacenamiento": {"base": "sismo_cali", "base_prueba": "sismo_cali_prueba"}}
    base = dict(solo_verificar=False, rotar=False, usuario_admin="root")
    return {"configurar": lambda: cm.configurar(cfg, argparse.Namespace(**base), _sin_conexion, _sin_conexion, _pedir_clave, ruta_env),
            "configurar_docker": lambda: cm.configurar_docker(cfg, argparse.Namespace(origen="localhost", **base), _sin_conexion, _pedir_clave, ruta_env),
            "configurar_lectura": lambda: cm.configurar_lectura(cfg, argparse.Namespace(origen=None, **base), _sin_conexion, _pedir_clave, ruta_env)}


@pytest.mark.parametrize("flujo", ["configurar", "configurar_docker", "configurar_lectura"])
def test_los_tres_flujos_aceptan_el_zip_con_gitignore_bueno_y_lo_rechazan_sin_el(carpeta, monkeypatch, flujo):
    ruta_env = carpeta / ".env"
    _con_git(monkeypatch, repo=False)
    with pytest.raises(cm.ConfiguracionError, match="no tiene .gitignore"):
        _flujos(ruta_env)[flujo]()
    (carpeta / ".gitignore").write_text(".env\n", encoding="utf-8")
    with pytest.raises(LlegoALaClave):
        _flujos(ruta_env)[flujo]()
    assert not ruta_env.exists()                                                # la guardia no escribe nada por sí sola
