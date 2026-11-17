"""Los archivos de Docker Compose de los servicios locales (phpMyAdmin y Airflow) se revisan como texto, sin Docker: puertos solo en 127.0.0.1, sin credenciales escritas, imágenes con versión exacta (D91).

Por qué existen: un puerto publicado en 0.0.0.0 dejaría la interfaz abierta a toda la red, una contraseña escrita en un compose acabaría en el repositorio y una imagen `latest` cambiaría sin avisar.
La comprobación en vivo de que los servicios arrancan y responden está en las evidencias EV-085 y EV-087; aquí solo se vigila que nadie deshaga lo decidido.
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


# ---------------------------------------------------------------- Airflow (compose adaptado)
AIRFLOW = ROOT / "orquestacion" / "docker-compose.yaml"
# Ningún valor de ejemplo del compose oficial se conserva (DF-18): ni la contraseña de Postgres ni el secreto JWT ni las de la interfaz y Fernet.
EJEMPLOS_DEL_OFICIAL = set()


def _servicios():
    return _cargar(AIRFLOW)[1]["services"]


def test_airflow_publica_todos_sus_puertos_solo_en_127_0_0_1_y_el_de_la_interfaz_es_parametrizable():
    puertos = {n: s["ports"] for n, s in _servicios().items() if "ports" in s}
    assert puertos == {"airflow-apiserver": ["127.0.0.1:${AIRFLOW_PUERTO:-8080}:8080"], "flower": ["127.0.0.1:5555:5555"]}, "solo la interfaz y Flower (opcional) publican un puerto"
    assert all(p.startswith("127.0.0.1:") and "0.0.0.0" not in p for lista in puertos.values() for p in lista)


def test_airflow_monta_el_proyecto_en_solo_lectura_y_con_el_nombre_de_la_carpeta_parametrizado():
    comun = _cargar(AIRFLOW)[1]["x-airflow-common"]
    montajes = [v for v in comun["volumes"] if "/opt/airflow/medallon" in v]
    assert len(montajes) == 1 and montajes[0].endswith(":/opt/airflow/medallon:ro")
    assert montajes[0].startswith("../${PROYECTO_NOMBRE:?") and "etl_sismo_cali_2026" not in AIRFLOW.read_text(encoding="utf-8")   # el nombre de la carpeta ya no es fijo


def test_airflow_no_trae_ninguna_contrasena_ni_clave_escrita_y_exige_las_del_env():
    texto, c = _cargar(AIRFLOW)
    entorno = c["x-airflow-common"]["environment"]
    assert entorno["AIRFLOW__CORE__FERNET_KEY"].startswith("${FERNET_KEY:?")
    assert c["services"]["airflow-init"]["environment"]["_AIRFLOW_WWW_USER_PASSWORD"].startswith("${_AIRFLOW_WWW_USER_PASSWORD:?")
    assert c["services"]["postgres"]["environment"]["POSTGRES_PASSWORD"].startswith("${POSTGRES_PASSWORD:?")
    assert entorno["AIRFLOW__API_AUTH__JWT_SECRET"].startswith("${AIRFLOW__API_AUTH__JWT_SECRET:?")
    assert "${POSTGRES_PASSWORD:?" in entorno["AIRFLOW__DATABASE__SQL_ALCHEMY_CONN"] and "${POSTGRES_PASSWORD:?" in entorno["AIRFLOW__CELERY__RESULT_BACKEND"]
    literales = set()
    for linea in _lineas_sin_comentarios(texto).splitlines():
        m = re.match(r"\s*([A-Za-z_]\w*)\s*:\s*(\S+)\s*$", linea)
        if m and re.search(r"(?i)password|secret|fernet|key", m.group(1)) and not m.group(2).startswith("${"):
            literales.add(m.group(2).strip("'\""))
    assert literales <= EJEMPLOS_DEL_OFICIAL, f"valores escritos en el compose: {len(literales)}"


def test_airflow_usa_versiones_exactas_y_no_latest():
    texto = AIRFLOW.read_text(encoding="utf-8")
    servicios = _servicios()
    assert servicios["postgres"]["image"].startswith("postgres:16@sha256:") and servicios["redis"]["image"].startswith("redis:7.2-bookworm@sha256:")
    assert all(HEX64.search(servicios[n]["image"]) for n in ("postgres", "redis"))
    assert "latest" not in _lineas_sin_comentarios(texto).lower()
    assert "# image: ${AIRFLOW_IMAGE_NAME:-apache/airflow:3.3.2}" in texto and _cargar(AIRFLOW)[1]["x-airflow-common"]["build"] == "."
    assert (ROOT / "orquestacion" / "Dockerfile").read_text(encoding="utf-8").splitlines()[0] == "FROM apache/airflow:3.3.2"


def test_airflow_conserva_el_aviso_de_licencia_y_dice_de_donde_sale_y_que_cambio():
    texto = AIRFLOW.read_text(encoding="utf-8")
    assert "Licensed to the Apache Software Foundation" in texto and "Apache License, Version 2.0" in texto
    assert "AVISO DE ORIGEN Y DE CAMBIOS" in texto and "docker-compose.yaml oficial de Apache Airflow 3.3.2" in texto and "generar_compose.py" in texto


def _generador():
    import importlib.util
    espec = importlib.util.spec_from_file_location("generar_compose_prueba", ROOT / "scripts" / "orquestacion" / "generar_compose.py")
    modulo = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(modulo)
    return modulo


def test_el_generador_aplica_cada_cambio_una_sola_vez_y_falla_si_el_oficial_cambia():
    g = _generador()
    oficial = "# under the License.\n#\n" + "".join(ancla for ancla, _ in g.REEMPLAZOS)
    adaptado = g.adaptar(oficial)
    assert all(nuevo in adaptado for _, nuevo in g.REEMPLAZOS) and "AVISO DE ORIGEN" in adaptado
    for ancla, _ in g.REEMPLAZOS:
        with pytest.raises(g.ComposeError):
            g.adaptar(oficial.replace(ancla, ""))                 # un ancla que ya no está
        with pytest.raises(g.ComposeError):
            g.adaptar(oficial + ancla)                            # un ancla repetida
    assert len(g.SHA256_OFICIAL) == 64 and g.URL_OFICIAL.startswith("https://airflow.apache.org/docs/apache-airflow/3.3.2/")


def test_el_diff_del_repositorio_resume_los_cambios_y_no_contiene_contrasenas_ni_urls_con_credenciales():
    diff = (ROOT / "orquestacion" / "docker-compose.diff").read_text(encoding="utf-8")
    for pieza in ("+  build: .", "-  image: ${AIRFLOW_IMAGE_NAME:-apache/airflow:3.3.2}", "${FERNET_KEY:?", "../${PROYECTO_NOMBRE:?", '+      - "127.0.0.1:${AIRFLOW_PUERTO:-8080}:8080"',
                  "${_AIRFLOW_WWW_USER_PASSWORD:?", "${POSTGRES_PASSWORD:?", "${AIRFLOW__API_AUTH__JWT_SECRET:?", '+      - "127.0.0.1:5555:5555"', "+    image: postgres:16@sha256:", "+    image: redis:7.2-bookworm@sha256:"):
        assert pieza in diff, pieza
    # el ejemplo del oficial va oculto para que el escáner de secretos no lo tome por una URL con credenciales
    assert "<ejemplo del oficial>" in diff and not re.search(r"[a-z][a-z0-9+.-]*://[^/\s:@'\"]+:[^/\s@'\"]{3,}@", diff)


# --- el documento de credenciales dice lo que el compose hace con la clave Fernet y el secreto JWT ---
FILA_FERNET_JWT = re.compile(r"(?m)^\| clave Fernet y secreto JWT de Airflow \|.*$")


def fila_de_fernet_y_jwt_correcta(doc, compose, preparar):
    """Lista de problemas de la fila del documento de credenciales sobre la clave Fernet y el secreto JWT, frente al compose y al script que los genera."""
    fila = FILA_FERNET_JWT.search(doc)
    if not fila:
        return ["falta la fila de la clave Fernet y el secreto JWT"]
    errores = []
    if "${FERNET_KEY:?" not in compose or "AIRFLOW__API_AUTH__JWT_SECRET:?" not in compose:
        errores.append("el compose ya no exige la clave Fernet o el secreto JWT")
    if "FERNET_KEY" not in preparar or "AIRFLOW__API_AUTH__JWT_SECRET" not in preparar:
        errores.append("el script de preparación ya no genera la clave Fernet o el secreto JWT")
    for falso in ("deja la Fernet vacía", "trae un secreto JWT de ejemplo", "no usadas con valor propio"):
        if falso in fila.group(0):
            errores.append(f"la fila dice «{falso}»")
    for cierto in ("obligatorias", "se niega a arrancar", "DF-15", "DF-18", ".env"):
        if cierto not in fila.group(0):
            errores.append(f"la fila no dice «{cierto}»")
    return errores


def test_la_fila_de_fernet_y_jwt_del_documento_de_credenciales_dice_lo_que_hace_el_compose():
    doc = (ROOT / "docs" / "seguridad" / "gestion_credenciales.md").read_text(encoding="utf-8")
    compose = (ROOT / "orquestacion" / "docker-compose.yaml").read_text(encoding="utf-8")
    preparar = (ROOT / "scripts" / "orquestacion" / "preparar_airflow.py").read_text(encoding="utf-8")
    assert fila_de_fernet_y_jwt_correcta(doc, compose, preparar) == []


def test_una_fila_desactualizada_de_fernet_y_jwt_se_detecta():
    doc = (ROOT / "docs" / "seguridad" / "gestion_credenciales.md").read_text(encoding="utf-8")
    compose = (ROOT / "orquestacion" / "docker-compose.yaml").read_text(encoding="utf-8")
    preparar = (ROOT / "scripts" / "orquestacion" / "preparar_airflow.py").read_text(encoding="utf-8")
    vieja = doc.replace("**con valor propio y obligatorias**", "**no usadas con valor propio**: el compose oficial deja la Fernet vacía y trae un secreto JWT de ejemplo")
    assert fila_de_fernet_y_jwt_correcta(vieja, compose, preparar), "la fila antigua"
    assert fila_de_fernet_y_jwt_correcta(doc, compose.replace("${FERNET_KEY:?", "${FERNET_KEY:-"), preparar), "el compose deja de exigir la clave"
    assert fila_de_fernet_y_jwt_correcta(doc, compose, preparar.replace("FERNET_KEY", "OTRA")), "el script deja de generarla"
