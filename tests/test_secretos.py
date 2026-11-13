"""Gestión de secretos: escáner, .env fuera de git, enmascarado del registro y exclusión de .env del zip."""
import importlib.util
import logging
import subprocess
import zipfile

from src.common import ROOT
from src.logger import EnmascararSecretos


def _cargar(nombre):
    espec = importlib.util.spec_from_file_location(nombre, ROOT / "scripts" / f"{nombre}.py")
    modulo = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(modulo)
    return modulo


esc = _cargar("escanear_secretos")
make_dist = _cargar("make_dist")
# secretos de prueba construidos por concatenación: ni este archivo ni el escáner se detectan a sí mismos
SEMBRADOS = {
    "clave_aws": "AK" + "IA" + "ABCDEFGHIJKLMNOP",
    "token_github": "gh" + "p_" + "a1B2c3D4e5F6g7H8i9" + "J0k1L2m3N4o5P6q7R8",
    "token_slack": "xo" + "xb-" + "1234567890-abcdefghij",
    "clave_google": "AI" + "za" + "SyA1B2c3D4e5F6g7H8i9" + "J0k1L2m3N4o5P6q",
    "jwt": "ey" + "JhbGciOiJIUzI1NiJ9" + ".ey" + "JzdWIiOiIxMjM0NTY3ODkwIn0" + ".abcdefghijklmnop1234",
    "clave_privada": "-----BEGIN " + "RSA PRIV" + "ATE KEY-----",
    "url_con_credenciales": "https://usuario:" + "clave1234@" + "ejemplo.invalid/ruta",
    "parametro_url_sensible": "https://ejemplo.invalid/datos?app_" + "token=" + "abcdef123456",
    "cabecera_autorizacion": "Authoriz" + "ation: Bearer " + "abcdef1234567890",
    "cabecera_token_app": "X-App-" + "Token: " + "abcdef1234567890",
    "asignacion_literal_sensible": "pass" + "word = '" + "hunter2hunter2'",
    "cadena_de_alta_entropia": "valor = '" + "x7Kd3Vz8Yt2P" + "uNaR4mQwB9" + "eLc5HjS6fGv1Zq0" + "'",
}


def test_sin_hallazgos_en_el_arbol_de_trabajo():
    assert esc.escanear_arbol(ROOT) == []


def test_sin_hallazgos_en_el_historial_de_git():
    assert esc.escanear_historial(ROOT) == []


def test_detecta_un_secreto_sembrado_de_cada_tipo(tmp_path):
    for nombre, texto in SEMBRADOS.items():
        (tmp_path / f"{nombre}.txt").write_text("linea inocente\n" + texto + "\n", encoding="utf-8")
    hallazgos = esc.escanear_arbol(tmp_path)
    detectados = {p for _, _, p in hallazgos}
    assert detectados == set(SEMBRADOS), set(SEMBRADOS) ^ detectados
    assert all(linea == 2 for _, linea, _ in hallazgos)
    assert not any(valor in repr(hallazgos) for valor in SEMBRADOS.values())  # nunca se reporta el valor


def test_detecta_secretos_en_salidas_de_notebooks_y_logs(tmp_path):
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "etl.log").write_text("conexion " + SEMBRADOS["parametro_url_sensible"] + "\n", encoding="utf-8")
    (tmp_path / "cuaderno.ipynb").write_text('{"outputs": [{"text": ["' + SEMBRADOS["cabecera_token_app"] + '"]}]}\n', encoding="utf-8")
    assert {a for a, _, _ in esc.escanear_arbol(tmp_path)} == {"logs/etl.log", "cuaderno.ipynb"}


def test_no_marca_huellas_ni_rutas_ni_urls_largas(tmp_path):
    texto = "sha256 " + "ab12" * 16 + "\ncommit " + "0123456789abcdef" * 2 + "\nhttps://ejemplo.invalid/Impacto_Satelital_en_Edificaciones_2026/FeatureServer/0\n"
    (tmp_path / "huellas.txt").write_text(texto, encoding="utf-8")
    assert esc.escanear_arbol(tmp_path) == []


def test_escanea_el_contenido_de_un_zip_y_el_env_dentro_de_el(tmp_path):
    zip_ruta = tmp_path / "e.zip"
    with zipfile.ZipFile(zip_ruta, "w") as z:
        z.writestr("src/a.py", "x = 1\n")
        z.writestr("config/c.txt", SEMBRADOS["clave_aws"] + "\n")
        z.writestr(".env", "A=1\n")
    assert {(a, p) for a, _, p in esc.escanear_zip(zip_ruta)} == {("zip:config/c.txt", "clave_aws"), ("zip:.env", "archivo_env_en_el_zip")}


def test_el_codigo_de_salida_es_distinto_de_cero_con_hallazgos(tmp_path):
    (tmp_path / "a.txt").write_text(SEMBRADOS["clave_aws"] + "\n", encoding="utf-8")
    assert esc.main(["--raiz", str(tmp_path), "--sin-historial"]) == 1
    vacia = tmp_path / "limpia"
    vacia.mkdir()
    (vacia / "a.txt").write_text("nada\n", encoding="utf-8")
    assert esc.main(["--raiz", str(vacia), "--sin-historial"]) == 0


def test_env_no_esta_versionado():
    r = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    assert ".env" not in r.stdout.splitlines()
    assert ".env.example" in r.stdout.splitlines()


def test_el_registro_enmascara_un_token_de_prueba():
    registro = logging.LogRecord("etl.prueba", logging.INFO, __file__, 1, "app_token=" + "valor-de-prueba-123 y Authorization: Bearer " + "otro-valor-456", (), None)
    EnmascararSecretos().filter(registro)
    texto = registro.getMessage()
    assert "valor-de-prueba-123" not in texto and "otro-valor-456" not in texto and "***" in texto


def test_make_dist_excluye_env(tmp_path):
    raiz = tmp_path / "proyecto"
    for r in ("main.py", "requirements.txt", ".env", ".env.example", "src/a.py"):
        (raiz / r).parent.mkdir(parents=True, exist_ok=True)
        (raiz / r).write_text("x", encoding="utf-8")
    _, nombres = make_dist.empaquetar(raiz, tmp_path / "salida")
    assert ".env" not in nombres and ".env.example" in nombres
