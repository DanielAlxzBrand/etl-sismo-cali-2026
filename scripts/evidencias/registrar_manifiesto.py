"""Agrega al manifiesto de evidencias las filas de la capa de servicio (EV-013 a EV-026) y del almacenamiento relacional (EV-027 a EV-034) con su sha256 calculado de cada archivo.

Idempotente: si un id ya está en el manifiesto, lo reemplaza. Solo escribe docs/evidencias/manifiesto.md.
Uso: .\\.venv\\Scripts\\python.exe scripts\\evidencias\\registrar_manifiesto.py
"""
import hashlib
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from src.logger import get_logger  # noqa: E402

log = get_logger(__name__)
MANIFIESTO = REPO / "docs" / "evidencias" / "manifiesto.md"
CARPETA = "docs/evidencias/api"
FECHA = "2026-11-12"
FILAS = {
    "EV-013": ("2.1", "fastapi, uvicorn y httpx instalados en el .venv, `pip check` sin conflictos y rueda de pydantic-core para Python 3.13", "archivo",
               "`<VENV>\\Scripts\\python.exe -c \"import fastapi, uvicorn, httpx\"`; `pip check`", "EV-013_instalacion_paquetes.txt"),
    "EV-014": ("2.1, 2.2, 2.3", "Todas las pruebas (incluidas test_api, test_catalogo, test_secretos y test_evidencias) pasan en un clon temporal", "archivo",
               "`<VENV>\\Scripts\\python.exe -m pytest -q -p no:cacheprovider --junitxml` en un clon temporal", "EV-014_pytest.txt"),
    "EV-025": ("2.1, 2.2, 2.3", "Informe JUnit de las pruebas de EV-014 (sin el atributo hostname)", "archivo", "mismo comando que EV-014", "junit_api.xml"),
    "EV-015": ("2.1", "Los sha256 de todo data/ y de la base son idénticos tras clonar, tras las pruebas y tras consultar el servidor real", "archivo",
               "sha256 de cada archivo de `data/` en el clon en tres momentos", "EV-015_sin_escritura_hashes.txt"),
    "EV-016": ("2.1, 2.2", "El servicio arranca en 127.0.0.1, cada ruta responde, se cierra de forma ordenada y se exporta /openapi.json", "archivo",
               "`uvicorn src.api.app:app --host 127.0.0.1 --port <libre>` y GET a cada ruta", "EV-016_respuestas_api.txt"),
    "EV-026": ("2.1, 2.2", "Esquema OpenAPI completo del servicio (11 rutas, solo GET)", "archivo", "`GET /openapi.json`", "openapi.json"),
    "EV-017": ("2.1", "Captura automatizada del navegador sin ventana de la documentación /docs (no es una captura manual)", "imagen",
               "`msedge.exe --headless=new --screenshot` sobre `/docs`", "EV-017_docs_navegador.png"),
    "EV-018": ("2.1", "Mediana y percentil 95 de la latencia por endpoint: 50 repeticiones tras 5 de calentamiento contra el servidor real (medición local de una máquina)", "archivo",
               "solicitudes GET con httpx contra el servicio en 127.0.0.1", "EV-018_latencia_api.csv"),
    "EV-019": ("2.3", "El escáner no halla secretos en el clon, su historial ni un zip de prueba armado con make_dist.py", "archivo",
               "`scripts/escanear_secretos.py --zip <zip temporal>`", "EV-019_escaner_secretos.txt"),
    "EV-020": ("2.1", "requirements.txt está completo: un entorno virtual nuevo instala y recolecta las pruebas", "archivo",
               "`python -m venv <TEMP>`; `pip install -r requirements.txt`; `pytest --collect-only`", "EV-020_requirements_entorno_nuevo.txt"),
    "EV-021": ("2.1", "Imagen renderizada con las latencias de EV-018", "imagen", "matplotlib sobre EV-018", "EV-021_latencias.png"),
    "EV-022": ("2.1", "Imagen renderizada con los sha256 de EV-015", "imagen", "matplotlib sobre EV-015", "EV-022_hashes_antes_despues.png"),
    "EV-023": ("2.1, 2.2, 2.3", "Imagen renderizada con el resultado de EV-014", "imagen", "matplotlib sobre EV-014", "EV-023_pytest.png"),
    "EV-024": ("2.3", "Imagen renderizada con el resultado de EV-019", "imagen", "matplotlib sobre EV-019", "EV-024_escaner.png"),
    "EV-016b": ("2.1, 2.2", "Respuesta real de la ruta calidad (apoyo de EV-016)", "archivo", "GET a la ruta con el servicio en 127.0.0.1", "respuestas_api/calidad.json"),
    "EV-016c": ("2.1, 2.2", "Respuesta real de la ruta composicion (apoyo de EV-016)", "archivo", "GET a la ruta con el servicio en 127.0.0.1", "respuestas_api/composicion.json"),
    "EV-016d": ("2.1, 2.2", "Respuesta real de la ruta comunas (apoyo de EV-016)", "archivo", "GET a la ruta con el servicio en 127.0.0.1", "respuestas_api/comunas.json"),
    "EV-016e": ("2.1, 2.2", "Respuesta real de la ruta construcciones (apoyo de EV-016)", "archivo", "GET a la ruta con el servicio en 127.0.0.1", "respuestas_api/construcciones.json"),
    "EV-016f": ("2.1, 2.2", "Respuesta real de la ruta fuentes (apoyo de EV-016)", "archivo", "GET a la ruta con el servicio en 127.0.0.1", "respuestas_api/fuentes.json"),
    "EV-016g": ("2.1, 2.2", "Respuesta real de la ruta health (apoyo de EV-016)", "archivo", "GET a la ruta con el servicio en 127.0.0.1", "respuestas_api/health.json"),
    "EV-016h": ("2.1, 2.2", "Respuesta real de la ruta kpis (apoyo de EV-016)", "archivo", "GET a la ruta con el servicio en 127.0.0.1", "respuestas_api/kpis.json"),
    "EV-016i": ("2.1, 2.2", "Respuesta real de la ruta kpis K1 (apoyo de EV-016)", "archivo", "GET a la ruta con el servicio en 127.0.0.1", "respuestas_api/kpis_K1.json"),
    "EV-016j": ("2.1, 2.2", "Respuesta real de la ruta kpis sensibilidad (apoyo de EV-016)", "archivo", "GET a la ruta con el servicio en 127.0.0.1", "respuestas_api/kpis_sensibilidad.json"),
    "EV-016k": ("2.1, 2.2", "Respuesta real de la ruta llave revision (apoyo de EV-016)", "archivo", "GET a la ruta con el servicio en 127.0.0.1", "respuestas_api/llave_revision.json"),
    "EV-016l": ("2.1, 2.2", "Respuesta real de la ruta metadata (apoyo de EV-016)", "archivo", "GET a la ruta con el servicio en 127.0.0.1", "respuestas_api/metadata.json"),
    "EV-017b": ("2.1", "Registro de la captura automatizada del navegador de EV-017", "archivo", "`msedge.exe --headless=new --screenshot` sobre `/docs`", "EV-017_docs_navegador.txt"),
}

CARPETA_ALMACEN = "docs/evidencias/almacenamiento"
FECHA_ALMACEN = "2026-11-13"
CARPETA_ORQ = "docs/evidencias/orquestacion"
FECHA_ORQ = "2026-11-13"
FILAS_ORQ = {
    "EV-035": ("5.4", "Estabilidad del pipeline antes de orquestarlo: dos ejecuciones en un clon reproducen los CSV y JSON versionados byte a byte y la base tabla a tabla (pandas 3.0.6)", "archivo", "`python scripts/evidencias/evidencia_estabilidad.py`", "EV-035_estabilidad_pipeline.txt"),
    "EV-036": ("5.6", "Cada prueba de regresión falla sin la corrección que protege (defecto reintroducido en una copia temporal)", "archivo", "`python scripts/validacion/verificar_regresiones.py --evidencia`", "EV-036_regresiones_sin_correccion.txt"),
    "EV-037": ("5.4", "Pasos 13 a 19 de la guía de Airflow: carpeta, compose 3.3.2, `.env`, Dockerfile, volumen de solo lectura y `build: .`", "archivo", "`curl.exe -LfO <compose 3.3.2>`; edición del compose y del `.env`; `docker run --rm --entrypoint printenv apache/airflow:3.3.2 AIRFLOW_VERSION`", "EV-037_pasos_13_a_19.txt"),
    "EV-038": ("5.4", "Pasos 27 a 30: construcción de la imagen, inicialización, arranque de los 7 contenedores y `docker ps`", "archivo", "`docker compose build`; `docker compose up airflow-init`; `docker compose up -d`; `docker ps`", "EV-038_pasos_27_a_30.txt"),
    "EV-039": ("5.4", "Pasos 31 a 33: interfaz en 127.0.0.1:8080, `dags list`, `list-import-errors` y contenido de `dags/`", "archivo", "`curl http://localhost:8080`; `docker compose exec airflow-scheduler airflow dags list`", "EV-039_pasos_31_a_33.txt"),
    "EV-040": ("5.4, 4.1", "Origen con el que MySQL ve la conexión desde el contenedor (`localhost`) y privilegios mínimos del usuario de Docker", "archivo", "`docker compose exec -T airflow-worker python -` (usuario inexistente a host.docker.internal:3306)", "EV-040_origen_mysql_desde_docker.txt"),
    "EV-041": ("5.4, 5.5", "Pasos 34 y 37: ejecuciones manuales del DAG y repetición, con las salidas comparadas con las versionadas del repositorio", "archivo", "`airflow dags trigger / unpause / list-runs`; `airflow tasks states-for-dag-run`", "EV-041_ejecucion_manual.txt"),
    "EV-042": ("5.4, 5.6", "Pasos 35 y 36: fallo inducido en una tarea, registros de la tarea fallida, copia de trabajo eliminada y recuperación con una ejecución sana", "archivo", "`airflow dags trigger medallon_etl_sismo --conf fallo_inducido`; registros de la tarea", "EV-042_fallo_inducido_y_recuperacion.txt"),
    "EV-043": ("5.4", "Paso 40: programación `0 6 * * *` en hora de Bogotá, ejecución disparada por el planificador y restauración del cron definitivo", "archivo", "`airflow dags unpause / details / list-runs`", "EV-043_programacion.txt"),
    "EV-044": ("5.4", "Pasos 41 a 43: reinicio de un servicio, registros, detener y volver a levantar conservando el volumen y la programación", "archivo", "`docker compose restart / logs / down / up -d`", "EV-044_operacion.txt"),
    "EV-044b": ("5.4, 5.5", "Estados y tiempos de las 4 tareas en las 7 ejecuciones del DAG (28 filas) exportados de Airflow", "archivo", "`airflow tasks states-for-dag-run -o json` por ejecución", "EV-044_estados_tareas.csv"),
    "EV-045": ("5.4", "Imagen renderizada con los estados y duraciones de las tareas en cada ejecución (a partir de EV-044b)", "imagen", "`python scripts/evidencias/make_imagenes_orquestacion.py`", "EV-045_estados_de_tareas.png"),
    "EV-046": ("5.5", "Imagen renderizada con las salidas del DAG frente a las versionadas (sha256 y contenido de la base)", "imagen", "`python scripts/evidencias/make_imagenes_orquestacion.py`", "EV-046_esperado_frente_a_obtenido.png"),
    "EV-047": ("5.4", "Imagen renderizada con las ejecuciones disparadas por el planificador (a partir de EV-044b)", "imagen", "`python scripts/evidencias/make_imagenes_orquestacion.py`", "EV-047_ejecucion_programada.png"),
    "EV-048": ("5.1, 5.2", "Imagen renderizada con la cobertura de líneas por módulo (a partir de `docs/validacion/cobertura_pruebas.csv`)", "imagen", "`python scripts/evidencias/make_imagenes_orquestacion.py`", "EV-048_cobertura_por_modulo.png"),
    "EV-049": ("2.3", "Comprobación canario con las contraseñas de MySQL, del usuario de Docker y de la interfaz de Airflow en el árbol, los registros, el historial, la carpeta de Airflow, la imagen y un zip de prueba", "archivo", "`python scripts/evidencias/evidencia_canario_orquestacion.py`", "EV-049_canario_orquestacion.txt"),
    "EV-050": ("5.1, 5.6", "Las 316 pruebas pasan en un clon limpio del commit, `data/` del clon es idéntico al del árbol de trabajo y el escáner no halla secretos", "archivo", "`python scripts/evidencias/evidencia_pruebas_clon.py --nombre EV-050_pruebas_clon.txt` (el archivo se movió a la carpeta de orquestación)", "EV-050_pruebas_clon.txt"),
}


FILAS_ALMACEN = {
    "EV-027": ("4.1", "PyMySQL y cryptography instalados en el .venv, con `pip check` sin conflictos y ruedas para Python 3.13", "archivo", "`python scripts/evidencias/evidencia_conector.py` (pip install pymysql cryptography; pip check)", "EV-027_conector_mysql.txt"),
    "EV-028": ("4.1, 4.2", "Batería en vivo sobre la base de prueba de MySQL 8.0.45: privilegios mínimos, esquema desde cero, carga conciliada al 100 %, idempotencia, historial, reversión, violaciones de integridad rechazadas y API idéntica a SQLite (26 de 26)", "archivo",
              "`python scripts/mysql/verificar_mysql.py --evidencia`", "EV-028_verificacion_mysql.txt"),
    "EV-029": ("4.1, 4.2", "Carga real a `sismo_cali`: 100 % de conciliación con los archivos de origen, segunda carga «ya cargada», 0 filas huérfanas y cifras iguales a gold_final.csv", "archivo", "`python scripts/evidencias/evidencia_carga_real.py`", "EV-029_carga_real_mysql.txt"),
    "EV-030": ("4.3", "Medición de la carga fila a fila frente a lotes de 500, 1000 y 2000 (mediana, p95 y filas por segundo; 1 calentamiento y 5 repeticiones) y lote elegido", "archivo", "`python scripts/mysql/benchmark_lotes.py --evidencia --fijar`", "EV-030_benchmark_lotes.txt"),
    "EV-030b": ("4.3", "Datos de la medición de lotes de EV-030", "archivo", "mismo comando que EV-030", "EV-030_benchmark_lotes.csv"),
    "EV-030c": ("4.3", "Gráfico renderizado con las medianas de EV-030", "imagen", "matplotlib sobre EV-030", "EV-030_benchmark_lotes.png"),
    "EV-031": ("4.2", "Respaldo lógico en CSV con manifiesto sha256 de la base real, restauración en la base de prueba y huellas de filas iguales en las 7 tablas", "archivo", "`python scripts/mysql/respaldar_restaurar.py --evidencia`", "EV-031_respaldo_restauracion.txt"),
    "EV-032": ("4.1", "La API sirve las mismas respuestas desde MySQL que desde SQLite (17 rutas con servidores reales en 127.0.0.1), solo acepta GET y no cambia data/; con latencias", "archivo", "`python scripts/evidencias/evidencia_api_mysql.py`", "EV-032_api_mysql_vs_sqlite.txt"),
    "EV-032b": ("4.1", "Datos de latencia por ruta y almacén de EV-032 (50 repeticiones tras 5 de calentamiento)", "archivo", "mismo comando que EV-032", "EV-032_latencia_api_mysql_vs_sqlite.csv"),
    "EV-032c": ("4.1", "Gráfico renderizado con las latencias de EV-032", "imagen", "matplotlib sobre EV-032", "EV-032_latencia_api_mysql_vs_sqlite.png"),
    "EV-033": ("2.3", "Comprobación canario: la contraseña real de MySQL no aparece en el árbol, los registros, el historial de git ni un zip de prueba; `.env` ignorado y no versionado", "archivo", "`python scripts/evidencias/evidencia_canario.py`", "EV-033_canario_credenciales.txt"),
    "EV-034": ("4.1, 4.2, 4.3", "Las pruebas (199) pasan en un clon limpio, `data/` del clon es idéntico al del árbol de trabajo y el escáner no halla secretos", "archivo", "`python scripts/evidencias/evidencia_pruebas_clon.py`", "EV-034_pruebas_clon.txt"),
}


def fila(ev, item, que, tipo, cmd, archivo, carpeta, fecha):
    p = REPO / carpeta / archivo
    return f"| {ev} |", f"| {ev} | {item} | {que} | {tipo} | {cmd} | {fecha} | {carpeta}/{archivo} | {hashlib.sha256(p.read_bytes()).hexdigest()} |"


def main():
    lineas = [l for l in MANIFIESTO.read_text(encoding="utf-8").split("\n")]
    nuevas = []
    for ev, (item, que, tipo, cmd, archivo) in FILAS.items():
        p = REPO / CARPETA / archivo
        if not p.exists():
            log.warning("falta %s; no se registra %s", archivo, ev)
            continue
        nuevas.append(fila(ev, item, que, tipo, cmd, archivo, CARPETA, FECHA))
    for ev, (item, que, tipo, cmd, archivo) in FILAS_ALMACEN.items():
        if not (REPO / CARPETA_ALMACEN / archivo).exists():
            log.warning("falta %s; no se registra %s", archivo, ev)
            continue
        nuevas.append(fila(ev, item, que, tipo, cmd, archivo, CARPETA_ALMACEN, FECHA_ALMACEN))
    for ev, (item, que, tipo, cmd, archivo) in FILAS_ORQ.items():
        if not (REPO / CARPETA_ORQ / archivo).exists():
            log.warning("falta %s; no se registra %s", archivo, ev)
            continue
        nuevas.append(fila(ev, item, que, tipo, cmd, archivo, CARPETA_ORQ, FECHA_ORQ))
    ids = {pref for pref, _ in nuevas}
    lineas = [l for l in lineas if not any(l.startswith(i) for i in ids)]
    ultima = max(i for i, l in enumerate(lineas) if l.startswith("| EV-"))   # las filas nuevas van al final de la tabla, antes de la convención
    lineas[ultima + 1:ultima + 1] = [fila for _, fila in nuevas]
    MANIFIESTO.write_text("\n".join(lineas) + "\n", encoding="utf-8", newline="\n")
    log.info("manifiesto: %s filas registradas (capa de servicio y almacenamiento relacional)", len(nuevas))


if __name__ == "__main__":
    main()
