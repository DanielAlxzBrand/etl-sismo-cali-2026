"""Guardián del escáner de secretos (`scripts/escanear_secretos.py`) cuando la carpeta NO es un repositorio de Git (por ejemplo, el zip), y del módulo compartido `scripts/gitignore_env.py`.

Por qué existe: sin `.git` el escáner no comprobaba nada del `.env` (un `.gitignore` sin la línea `.env` pasaba en silencio) y terminaba en «hallazgos: 0» sin decir que no había revisado ningún historial; con `.git` pero sin
el programa git caía con un traceback. Ahora, sin repositorio, si existe un `.env` el `.gitignore` debe ignorarlo de forma efectiva; el historial no revisado se dice; y sin el programa git (con `.git` presente) hay un
mensaje claro y código 2. La regla de «ignora `.env`» vive en un solo módulo que usan este escáner y `configurar_mysql.py`, y que viaja en el zip.
Qué NO demuestra: que el escáner encuentre todo secreto posible (eso lo vigilan las pruebas de patrones y del canario) ni nada sobre historiales de otros repositorios.
"""
import shutil
import subprocess
import sys

import pytest

from src.common import ROOT
from test_configurar_mysql import cm, esc
from test_env_sin_repositorio import GitFalso


@pytest.fixture()
def carpeta(tmp_path):
    c = tmp_path / "proyecto zip"
    c.mkdir()
    return c


def _con_git(monkeypatch, **kw):
    git = GitFalso(**kw)
    monkeypatch.setattr(esc.subprocess, "run", git)
    return git


# ---------------------------------------------------------------- sin repositorio: el .gitignore decide si hay un .env
def test_sin_repositorio_un_env_con_gitignore_que_lo_ignora_no_da_hallazgo(carpeta, monkeypatch):
    (carpeta / ".env").write_text("HTTP_USER_AGENT=Equipo\n", encoding="utf-8")
    (carpeta / ".gitignore").write_text(".env\n", encoding="utf-8")
    _con_git(monkeypatch, repo=False)
    assert esc.estado_de_env(carpeta) == []


@pytest.mark.parametrize("contenido", [None, "", ".env.example\n", ".env\n!.env\n", "# .env\n", ".env/\n"], ids=["sin .gitignore", "vacío", "solo .env.example", "reincorporado con !", "comentado", "solo carpeta"])
def test_sin_repositorio_un_env_sin_gitignore_efectivo_es_un_hallazgo(carpeta, monkeypatch, contenido):
    (carpeta / ".env").write_text("HTTP_USER_AGENT=Equipo\n", encoding="utf-8")
    if contenido is not None:
        (carpeta / ".gitignore").write_text(contenido, encoding="utf-8")
    _con_git(monkeypatch, repo=False)
    assert esc.estado_de_env(carpeta) == [(".env", 0, "env_no_ignorado")]


def test_sin_repositorio_y_sin_env_no_hay_nada_que_proteger(carpeta, monkeypatch):
    _con_git(monkeypatch, repo=False)
    assert esc.estado_de_env(carpeta) == []                                       # ni siquiera hace falta un .gitignore: no hay secreto en la carpeta


@pytest.mark.parametrize("ignora, versionado, esperado", [(True, False, []), (False, False, [(".env", 0, "env_no_ignorado")]), (True, True, [(".env", 0, "env_versionado")]),
                                                           (False, True, [(".env", 0, "env_no_ignorado"), (".env", 0, "env_versionado")])])
def test_con_repositorio_decide_git_y_el_gitignore_de_texto_no_cuenta(carpeta, monkeypatch, ignora, versionado, esperado):
    (carpeta / ".env").write_text("X=1\n", encoding="utf-8")
    (carpeta / ".gitignore").write_text(".env\n", encoding="utf-8")                # perfecto en texto: no salva lo que Git dice que está mal
    _con_git(monkeypatch, repo=True, ignora=ignora, versionado=versionado)
    assert esc.estado_de_env(carpeta) == esperado


# ---------------------------------------------------------------- el aviso de historial no revisado y el código de salida
def test_sin_repositorio_se_dice_que_el_historial_no_se_revisa_y_el_codigo_de_salida_no_cambia(carpeta, monkeypatch, capsys):
    (carpeta / ".gitignore").write_text(".env\n", encoding="utf-8")
    _con_git(monkeypatch, repo=False)
    codigo = esc.main(["--raiz", str(carpeta)])
    salida = capsys.readouterr().out.splitlines()
    assert codigo == 0 and "historial de git: no revisado (esta carpeta no es un repositorio de Git)" in salida and salida[-1] == "hallazgos: 0"


def test_el_aviso_no_sale_si_se_pidio_omitir_el_historial_ni_si_hay_repositorio_propio(carpeta, monkeypatch, capsys):
    _con_git(monkeypatch, repo=False)
    assert esc.main(["--raiz", str(carpeta), "--sin-historial"]) == 0
    assert "historial de git" not in capsys.readouterr().out
    (carpeta / ".git").mkdir()
    _con_git(monkeypatch, repo=True)
    assert esc.main(["--raiz", str(carpeta)]) == 0 and "no revisado" not in capsys.readouterr().out


def test_con_un_hallazgo_el_aviso_sale_y_el_codigo_sigue_siendo_1(carpeta, monkeypatch, capsys):
    (carpeta / ".env").write_text("X=1\n", encoding="utf-8")                        # sin .gitignore
    _con_git(monkeypatch, repo=False)
    codigo = esc.main(["--raiz", str(carpeta)])
    salida = capsys.readouterr().out
    assert codigo == 1 and ".env:0: env_no_ignorado" in salida and "historial de git: no revisado" in salida


def test_el_canario_sigue_funcionando_sin_repositorio(carpeta, monkeypatch, capsys):
    valor = "Canario-" + "Ficticio-" + "7f3a9c21d4"
    (carpeta / ".env").write_text("MYSQL_" + "PASS" + f"WORD={valor}\n", encoding="utf-8")
    (carpeta / ".gitignore").write_text(".env\n", encoding="utf-8")
    (carpeta / "notas.txt").write_text(f"se coló: {valor}\n", encoding="utf-8")
    _con_git(monkeypatch, repo=False)
    codigo = esc.main(["--raiz", str(carpeta), "--canario-env"])
    salida = capsys.readouterr().out
    assert codigo == 1 and valor not in salida and "notas.txt:1: canario:MYSQL_PASSWORD" in salida


# ---------------------------------------------------------------- con .git pero sin el programa git: mensaje claro y código 2
def test_con_git_en_disco_y_sin_el_programa_hay_un_mensaje_claro_y_codigo_2_sin_traceback(carpeta, monkeypatch, capsys):
    (carpeta / ".git").mkdir()
    _con_git(monkeypatch, ausente=True)
    codigo = esc.main(["--raiz", str(carpeta)])
    captura = capsys.readouterr()
    assert codigo == 2 and "instale Git" in captura.err and "git no está instalado" in captura.err and "hallazgos" not in captura.out


def test_el_codigo_2_tambien_sale_con_sin_historial_porque_el_estado_de_env_necesita_git(carpeta, monkeypatch, capsys):
    (carpeta / ".git").mkdir()
    _con_git(monkeypatch, ausente=True)
    assert esc.main(["--raiz", str(carpeta), "--sin-historial"]) == 2
    assert "instale Git" in capsys.readouterr().err


def test_sin_historial_y_solo_canario_no_necesitan_git_aunque_haya_una_carpeta_git(carpeta, monkeypatch, capsys):
    (carpeta / ".git").mkdir()
    _con_git(monkeypatch, ausente=True)
    assert esc.main(["--raiz", str(carpeta), "--sin-historial", "--solo-canario"]) == 0
    assert "instale Git" not in capsys.readouterr().err


def test_sin_el_programa_git_y_sin_carpeta_git_el_escaner_funciona_como_en_un_zip_sin_git(carpeta, monkeypatch, capsys):
    (carpeta / ".gitignore").write_text(".env\n", encoding="utf-8")
    (carpeta / ".env").write_text("X=1\n", encoding="utf-8")
    _con_git(monkeypatch, ausente=True)
    assert esc.main(["--raiz", str(carpeta)]) == 0
    assert "historial de git: no revisado" in capsys.readouterr().out


# ---------------------------------------------------------------- el módulo compartido: una sola copia, dentro del zip y suficiente
def test_la_regla_de_gitignore_vive_en_un_solo_modulo_y_los_dos_scripts_la_usan():
    definiciones = [p for p in (ROOT / "scripts").rglob("*.py") if "def gitignore_ignora_env" in p.read_text(encoding="utf-8")]
    assert [p.relative_to(ROOT).as_posix() for p in definiciones] == ["scripts/gitignore_env.py"]
    assert cm.gitignore_ignora_env is esc.gitignore_env.gitignore_ignora_env          # configurar_mysql sigue exponiendo el mismo nombre
    assert "gitignore_env" in (ROOT / "scripts" / "mysql" / "configurar_mysql.py").read_text(encoding="utf-8")


def test_el_modulo_compartido_viaja_en_el_zip():
    import importlib.util
    espec = importlib.util.spec_from_file_location("make_dist_gitignore", ROOT / "scripts" / "make_dist.py")
    md = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(md)
    viajan = {p.relative_to(ROOT).as_posix() for p in md.listar(ROOT)}
    assert {"scripts/gitignore_env.py", "scripts/escanear_secretos.py", "scripts/mysql/configurar_mysql.py"} <= viajan


def test_el_escaner_solo_necesita_su_carpeta_y_el_modulo_compartido_para_arrancar(tmp_path):
    """Como en el zip: copia únicamente `escanear_secretos.py` y `gitignore_env.py` y lo ejecuta sobre una carpeta sin `.git`; sin el módulo compartido no arranca (por eso tiene que viajar)."""
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    shutil.copy2(ROOT / "scripts" / "escanear_secretos.py", scripts)
    proyecto = tmp_path / "proyecto sin git"
    proyecto.mkdir()
    (proyecto / ".gitignore").write_text(".env\n", encoding="utf-8")
    (proyecto / ".env").write_text("HTTP_USER_AGENT=Equipo\n", encoding="utf-8")
    orden = [sys.executable, "-I", str(scripts / "escanear_secretos.py"), "--raiz", str(proyecto), "--sin-historial"]
    sin_modulo = subprocess.run(orden, capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert sin_modulo.returncode != 0 and "gitignore_env" in sin_modulo.stderr
    shutil.copy2(ROOT / "scripts" / "gitignore_env.py", scripts)
    con_modulo = subprocess.run(orden, capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert con_modulo.returncode == 0 and "hallazgos: 0" in con_modulo.stdout
    (proyecto / ".gitignore").write_text("", encoding="utf-8")
    sin_regla = subprocess.run(orden, capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert sin_regla.returncode == 1 and ".env:0: env_no_ignorado" in sin_regla.stdout
