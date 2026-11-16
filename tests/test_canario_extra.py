"""Comprobación canario con archivos .env extra: busca contraseñas de otra carpeta de trabajo sin imprimirlas."""
import shutil
import subprocess

import pytest

from test_configurar_mysql import esc

VALOR = "Extra-" + "Canario-" + "Prueba-4d7e1c9a"   # valor inventado para sembrar


def _carpeta(tmp_path, nombre, contenido_env):
    c = tmp_path / nombre
    c.mkdir()
    (c / ".env").write_text(contenido_env, encoding="utf-8")
    (c / ".gitignore").write_text(".env\n", encoding="utf-8")      # una carpeta de trabajo protegida: sin repositorio, el escáner exige que el .gitignore ignore el .env que existe
    return c


def test_los_canarios_de_un_env_extra_se_suman_y_se_nombran_por_su_carpeta(tmp_path):
    repo = _carpeta(tmp_path, "proyecto", "MYSQL_" + "PASS" + "WORD=Valor-Del-Proyecto-123\n")
    otra = _carpeta(tmp_path, "airflow", "AIRFLOW_" + "WWW_USER_" + f"PASSWORD={VALOR}\nAIRFLOW_UID=50000\n")
    can = esc.canarios(repo, [otra / ".env"])
    assert sorted(can) == ["AIRFLOW_WWW_USER_PASSWORD@airflow", "MYSQL_PASSWORD"]
    assert "AIRFLOW_UID@airflow" not in can   # no es sensible
    assert list(esc.canarios(repo, [tmp_path / "no_existe.env"])) == ["MYSQL_PASSWORD"]


def test_detecta_la_contrasena_del_env_extra_en_el_arbol_sin_imprimirla(tmp_path, capsys):
    repo = _carpeta(tmp_path, "proyecto", "HTTP_USER_AGENT=Equipo\n")
    otra = _carpeta(tmp_path, "airflow", "AIRFLOW_" + "WWW_USER_" + f"PASSWORD={VALOR}\n")
    (repo / "notas.txt").write_text(f"copiada por error: {VALOR}\n", encoding="utf-8")
    codigo = esc.main(["--raiz", str(repo), "--env-extra", str(otra / ".env"), "--sin-historial"])
    salida = capsys.readouterr().out
    assert codigo == 1 and VALOR not in salida and "canario:AIRFLOW_WWW_USER_PASSWORD@airflow" in salida and "notas.txt" in salida


def test_sin_la_contrasena_en_el_arbol_no_hay_hallazgos(tmp_path):
    repo = _carpeta(tmp_path, "proyecto", "HTTP_USER_AGENT=Equipo\n")
    otra = _carpeta(tmp_path, "airflow", "AIRFLOW_" + "WWW_USER_" + f"PASSWORD={VALOR}\n")
    (repo / "limpio.txt").write_text("nada sensible\n", encoding="utf-8")
    assert esc.main(["--raiz", str(repo), "--env-extra", str(otra / ".env"), "--sin-historial"]) == 0


def test_solo_canario_omite_los_patrones_de_secretos(tmp_path, capsys):
    repo = _carpeta(tmp_path, "ajena", "AIRFLOW_UID=50000\n")
    (repo / "compose.txt").write_text("ENV " + "pass" + "word = 'valorporomision123'\n", encoding="utf-8")   # un patrón conocido que el escáner normal sí marca
    assert esc.main(["--raiz", str(repo), "--sin-historial"]) == 1
    capsys.readouterr()
    assert esc.main(["--raiz", str(repo), "--solo-canario", "--sin-historial"]) == 0


def test_el_historial_tambien_se_revisa_con_el_env_extra(tmp_path, capsys):
    repo = _carpeta(tmp_path, "proyecto", "HTTP_USER_AGENT=Equipo\n")
    otra = _carpeta(tmp_path, "airflow", "AIRFLOW_" + "WWW_USER_" + f"PASSWORD={VALOR}\n")
    if shutil.which("git") is None:
        pytest.skip("falta el binario git en el equipo")
    for orden in (["git", "init", "-q"], ["git", "config", "user.email", "prueba@ejemplo.invalid"], ["git", "config", "user.name", "Prueba"]):
        subprocess.run(orden, cwd=repo, check=True)
    (repo / ".gitignore").write_text(".env\n", encoding="utf-8")
    (repo / "viejo.txt").write_text(f"valor: {VALOR}\n", encoding="utf-8")
    subprocess.run(["git", "add", ".gitignore", "viejo.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "inicio"], cwd=repo, check=True)
    (repo / "viejo.txt").unlink()
    subprocess.run(["git", "commit", "-q", "-am", "se quita"], cwd=repo, check=True)
    assert esc.main(["--raiz", str(repo), "--env-extra", str(otra / ".env"), "--solo-canario"]) == 1
    salida = capsys.readouterr().out
    assert VALOR not in salida and "historial:" in salida
