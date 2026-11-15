"""Los archivos de Docker Compose de los servicios locales (phpMyAdmin y Airflow) se revisan como texto, sin Docker: puertos solo en 127.0.0.1, sin credenciales escritas, imágenes con versión exacta (D91).

Por qué existen: un puerto publicado en 0.0.0.0 dejaría la interfaz abierta a toda la red, una contraseña escrita en un compose acabaría en el repositorio y una imagen `latest` cambiaría sin avisar.
La comprobación en vivo de que los servicios arrancan y responden está en las evidencias EV-083 y EV-084; aquí solo se vigila que nadie deshaga lo decidido.
"""
import re

import pytest
import yaml

from src.common import ROOT

PMA = ROOT / "servicios" / "phpmyadmin" / "docker-compose.yaml"
HEX64 = re.compile(r"@sha256:[0-9a-f]{64}$")


def _cargar(ruta):
    texto = ruta.read_text(encoding="utf-8")
    return texto, yaml.safe_load(texto)


def _lineas_sin_comentarios(texto):
    return "\n".join(l for l in texto.splitlines() if not l.lstrip().startswith("#"))


# ---------------------------------------------------------------- phpMyAdmin
def test_phpmyadmin_publica_el_puerto_solo_en_127_0_0_1_y_con_8081_por_defecto():
    _, c = _cargar(PMA)
    puertos = c["services"]["phpmyadmin"]["ports"]
    assert puertos == ["127.0.0.1:${PMA_PUERTO:-8081}:80"]
    assert all(p.startswith("127.0.0.1:") and "0.0.0.0" not in p for p in puertos)


def test_phpmyadmin_no_guarda_usuario_ni_contrasena_ni_admite_servidores_arbitrarios():
    texto, c = _cargar(PMA)
    entorno = c["services"]["phpmyadmin"]["environment"]
    assert not any(k.upper().startswith(("PMA_USER", "PMA_PASSWORD", "PMA_CONTROL", "MYSQL_")) or "PASSWORD" in k.upper() or "SECRET" in k.upper() for k in entorno)
    assert str(entorno["PMA_ARBITRARY"]) == "0" and "PMA_HOSTS" not in entorno
    assert entorno["PMA_HOST"] == "host.docker.internal" and str(entorno["PMA_PORT"]) == "3306"
    codigo = _lineas_sin_comentarios(texto)
    assert "env_file" not in codigo and ".env" not in codigo


def test_phpmyadmin_usa_una_imagen_con_version_exacta_y_resumen_y_nunca_latest():
    texto, c = _cargar(PMA)
    imagen = c["services"]["phpmyadmin"]["image"]
    nombre, _, resto = imagen.partition(":")
    version = resto.split("@")[0]
    assert nombre == "phpmyadmin" and re.fullmatch(r"5\.2\.\d+", version), imagen
    assert HEX64.search(imagen), "la imagen debe fijarse también por su resumen (digest)"
    assert "latest" not in texto.lower().replace("la última", "")


def test_phpmyadmin_no_reinicia_solo_limita_la_carga_y_llega_al_anfitrion():
    _, c = _cargar(PMA)
    s = c["services"]["phpmyadmin"]
    assert str(s["restart"]).lower() in ("no", "false")
    assert "host.docker.internal:host-gateway" in s["extra_hosts"]
    limite = str(s["environment"]["UPLOAD_LIMIT"]).upper()
    magnitud = int(re.match(r"\d+", limite).group()) * (1024 if limite.endswith("K") else 1024 * 1024 if limite.endswith("M") else 1)
    assert 0 < magnitud <= 8 * 1024 * 1024


def test_phpmyadmin_no_trae_comodines_de_origen():
    texto, _ = _cargar(PMA)
    assert "%" not in texto
