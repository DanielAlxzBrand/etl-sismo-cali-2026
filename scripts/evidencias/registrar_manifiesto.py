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


CARPETA_PANEL = "docs/evidencias/panel"
FECHA_PANEL = "2026-11-14"
FILAS_PANEL = {
    "EV-051": ("3.1", "Instalación de Streamlit 1.67.0 en el `.venv` con restricciones: solo paquetes añadidos, ninguno cambió de versión, `pip check` limpio y línea base reproducible", "archivo", "`pip install streamlit -c restricciones.txt`; `pip freeze`; `pip check`", "EV-051_instalacion_streamlit.txt"),
    "EV-052": ("3.1, 5.3", "Ejecución real con el lanzador: salud de la API y del panel, ocho páginas con el cliente real y cierre limpio sin procesos huérfanos", "archivo", "`python scripts/evidencias/evidencia_panel_ejecucion.py`", "EV-052_ejecucion_real.txt"),
    "EV-053": ("5.3", "Equivalencia SQLite frente a MySQL: 12 de 12 respuestas que consume el panel y 8 de 8 páginas con contenido idéntico", "archivo", "`python scripts/evidencias/evidencia_panel_almacenes.py`", "EV-053_equivalencia_almacenes.txt"),
    "EV-054": ("3.1", "Registro de las capturas automatizadas del navegador de las ocho páginas del panel", "archivo", "`python scripts/evidencias/evidencia_capturas_panel.py`", "EV-054_capturas_panel.txt"),
    "EV-054b": ("3.1", "Captura automatizada del navegador de la página Respuesta", "imagen", "`python scripts/evidencias/evidencia_capturas_panel.py`", "EV-054_captura_respuesta.png"),
    "EV-054c": ("3.1", "Captura automatizada del navegador de la página Estratos (K1)", "imagen", "`python scripts/evidencias/evidencia_capturas_panel.py`", "EV-054_captura_estratos.png"),
    "EV-054d": ("3.1", "Captura automatizada del navegador de la página Comunas (K6)", "imagen", "`python scripts/evidencias/evidencia_capturas_panel.py`", "EV-054_captura_comunas.png"),
    "EV-054e": ("3.1", "Captura automatizada del navegador de la página Sensibilidades (S0 a S5)", "imagen", "`python scripts/evidencias/evidencia_capturas_panel.py`", "EV-054_captura_sensibilidades.png"),
    "EV-054f": ("3.1", "Captura automatizada del navegador de la página Concentración (K3 y K4)", "imagen", "`python scripts/evidencias/evidencia_capturas_panel.py`", "EV-054_captura_concentracion.png"),
    "EV-054g": ("3.1", "Captura automatizada del navegador de la página Calidad de la llave", "imagen", "`python scripts/evidencias/evidencia_capturas_panel.py`", "EV-054_captura_calidad.png"),
    "EV-054h": ("3.1", "Captura automatizada del navegador de la página Construcciones", "imagen", "`python scripts/evidencias/evidencia_capturas_panel.py`", "EV-054_captura_construcciones.png"),
    "EV-054i": ("3.1", "Captura automatizada del navegador de la página Fuentes y sistema", "imagen", "`python scripts/evidencias/evidencia_capturas_panel.py`", "EV-054_captura_fuentes.png"),
    "EV-055": ("3.2", "Mediciones locales de una máquina: latencia del cliente por ruta y tiempo de renderizado por página, con SQLite y MySQL", "archivo", "`python scripts/evidencias/evidencia_panel_almacenes.py`", "EV-055_mediciones_panel.txt"),
    "EV-055b": ("3.2", "Datos de las mediciones de EV-055", "archivo", "mismo comando que EV-055", "EV-055_mediciones_panel.csv"),
    "EV-056": ("2.3", "Comprobación canario con las contraseñas de MySQL, del usuario de Docker y de la interfaz de Airflow tras agregar el panel", "archivo", "`python scripts/evidencias/evidencia_canario_orquestacion.py --tema panel --sin-imagen`", "EV-056_canario_panel.txt"),
    "EV-057": ("3.1", "Relaciones de contraste calculadas de la paleta del panel", "archivo", "`python scripts/panel/contraste.py --evidencia`", "EV-057_contrastes.txt"),
    "EV-058": ("3.2", "Imagen renderizada con las latencias del cliente del panel por ruta y almacenamiento (a partir de EV-055b)", "imagen", "`python scripts/evidencias/make_imagenes_panel.py`", "EV-058_latencias_cliente.png"),
    "EV-059": ("5.3", "Imagen renderizada con la cobertura de las pruebas por módulo del panel", "imagen", "`python scripts/evidencias/make_imagenes_panel.py`", "EV-059_cobertura_panel.png"),
    "EV-060": ("3.1, 3.2", "Imagen renderizada con los componentes del panel por página y tipo (a partir del registro de componentes)", "imagen", "`python scripts/evidencias/make_imagenes_panel.py`", "EV-060_trazabilidad_componentes.png"),
    "EV-061": ("5.3", "Las 616 pruebas del proyecto pasan en un clon limpio del commit, `data/` del clon es idéntico al del árbol de trabajo y el escáner no halla secretos", "archivo", "`python scripts/evidencias/evidencia_pruebas_clon.py --nombre EV-061_pruebas_clon.txt` (el archivo se movió a la carpeta del panel)", "EV-061_pruebas_clon.txt"),
}


CARPETA_END = "docs/evidencias/endurecimiento"
FECHA_END = "2026-11-14"
FILAS_END = {
    "EV-062": ("5.6, 7.1", "Instalación desde cero con Python 3.13 (`pip check` limpio, `pip freeze` frente al del `.venv`, rechazo esperado con Python 3.11) y suite completa en un clon con ese entorno", "archivo",
               "`python -m venv <VENV>`; `pip install -r requirements.txt`; `python -m pytest -q -p no:cacheprovider` en un clon del commit", "EV-062_instalacion_desde_cero.txt"),
    "EV-063": ("1.5, 5.1, 5.2, 5.5, 5.6", "Tabla de mutaciones en clones: requisitos, tabla de criterios del MVP, textos y notas del panel y cifras de los documentos de estado; todas detectadas por alguna prueba", "archivo",
               "mutación de un archivo en un clon temporal y `python -m pytest -q -p no:cacheprovider` sobre las pruebas guardianas", "EV-063_mutaciones.txt"),
    "EV-064": ("5.4", "Airflow en vivo: interfaz en 127.0.0.1:8080, DAG sin errores de importación, ejecución manual por la línea de comandos con las cuatro tareas en éxito, `data/` y MySQL sin cambios", "archivo",
               "`docker compose up -d`; `airflow dags list`; `airflow dags list-import-errors`; `airflow dags trigger medallon_etl_sismo`; `docker compose down`", "EV-064_airflow_en_vivo.txt"),
}


CARPETA_USU = "docs/evidencias/usuarios"
FECHA_USU = "2026-11-14"
FILAS_USU = {
    "EV-065": ("5.6", "Las pruebas de regresión de DEF-015 y DEF-016 pasan con la corrección y fallan sin ella (reintroducción en una copia temporal)", "archivo",
               "`python scripts/evidencias/evidencia_regresiones_nuevas.py`", "EV-065_regresiones_def015_def016.txt"),
}

_PAGINAS = (("respuesta", "Respuesta"), ("estratos", "Estratos (K1)"), ("comunas", "Comunas (K6)"), ("sensibilidades", "Sensibilidades (S0 a S5)"),
            ("concentracion", "Concentración (K3 y K4)"), ("calidad", "Calidad de la llave"), ("construcciones", "Construcciones"), ("fuentes", "Fuentes y sistema"))
_CMD_ANCHOS = "`python scripts/evidencias/evidencia_capturas_anchos.py`"
_CMD_MOVIL = "`python scripts/evidencias/evidencia_capturas_movil.py`"
FILAS_USU.update({
    "EV-066": ("3.3", "Capturas automatizadas, desbordamiento horizontal y texto recortado de las ocho páginas del panel en tres anchos (1400, 1024 y 390 px)", "archivo", _CMD_ANCHOS, "EV-066_capturas_anchos.txt"),
    "EV-067": ("3.3", "Tiempo hasta que cada página termina de dibujarse en tres anchos, medido en el navegador (medición local de una máquina)", "archivo", _CMD_ANCHOS, "EV-067_mediciones_anchos.txt"),
    "EV-067b": ("3.3", "Datos de los tiempos de EV-067 (una carga de calentamiento y cinco medidas por página y ancho)", "archivo", _CMD_ANCHOS, "EV-067_mediciones_anchos.csv"),
    "EV-068": ("3.3", "Contraste calculado del texto secundario y de los rótulos del panel (valores calculados, sin declarar un nivel de conformidad)", "archivo", _CMD_ANCHOS, "EV-068_contraste_texto.txt"),
    "EV-068b": ("3.3", "Detalle por página y ancho de los contrastes de EV-068", "archivo", _CMD_ANCHOS, "EV-068_contraste_texto.csv"),
    "EV-069": ("3.3", "Capturas a 390 px con la barra lateral cerrada, desbordamiento y texto recortado", "archivo", _CMD_MOVIL, "EV-069_capturas_390_barra_cerrada.txt"),
    "EV-072": ("5.6", "Las 822 pruebas pasan en un clon con el entorno nuevo de Python 3.13 (el de EV-062) en el commit del componente de usuarios, con `data/` idéntico y el escáner de secretos sin hallazgos", "archivo",
               "`python -m pytest -q -p no:cacheprovider` en un clon temporal con el intérprete del entorno nuevo", "EV-072_suite_en_entorno_nuevo.txt"),
    "EV-071": ("1.5, 3.3, 6.4", "Tabla de mutaciones de las pruebas guardianas de usuarios y finanzas (sesiones reales, precios, parámetros sin fuente, estado del checklist, fórmula SUS, hallazgos y capturas)", "archivo",
               "mutación de un archivo en un clon y `python -m pytest -q -p no:cacheprovider tests/test_usuarios.py tests/test_usuarios_estructura.py tests/test_finanzas.py`", "EV-071_mutaciones_usuarios.txt"),
})
for _i, (_ancho, (_pid, _titulo)) in enumerate((a, p) for a in (1400, 1024, 390) for p in _PAGINAS):
    FILAS_USU[f"EV-066{'bcdefghijklmnopqrstuvwxy'[_i]}"] = ("3.3", f"Captura automatizada del navegador de la página {_titulo} a {_ancho} px", "imagen", _CMD_ANCHOS, f"EV-066_captura_{_pid}_{_ancho}.png")
for _i, (_pid, _titulo) in enumerate(_PAGINAS):
    FILAS_USU[f"EV-069{'bcdefghi'[_i]}"] = ("3.3", f"Captura automatizada del navegador de la página {_titulo} a 390 px con la barra lateral cerrada", "imagen", _CMD_MOVIL, f"EV-069_captura_{_pid}_390_barra_cerrada.png")
CARPETA_UX = "docs/evidencias/ajustes_ux"
_CMD_ANTES = "`python scripts/evidencias/evidencia_capturas_ajustes.py --momento antes`"
_CMD_DESPUES = "`python scripts/evidencias/evidencia_capturas_ajustes.py --momento despues`"
FILAS_UX = {
    "EV-073": ("3.3", "Capturas, desbordamiento y texto recortado de las ocho páginas en tres anchos ANTES de los ajustes de la evaluación heurística", "archivo", _CMD_ANTES, "EV-073_capturas_anchos.txt"),
    "EV-074": ("3.3", "Tiempos de dibujo de las ocho páginas en tres anchos antes de los ajustes (medición local de una máquina)", "archivo", _CMD_ANTES, "EV-074_mediciones_anchos.txt"),
    "EV-074b": ("3.3", "Datos de los tiempos de EV-074", "archivo", _CMD_ANTES, "EV-074_mediciones_anchos.csv"),
    "EV-075": ("3.3", "Contraste calculado del texto del panel antes de los ajustes, midiendo solo texto visible", "archivo", _CMD_ANTES, "EV-075_contraste_texto.txt"),
    "EV-075b": ("3.3", "Detalle por página y ancho de los contrastes de EV-075", "archivo", _CMD_ANTES, "EV-075_contraste_texto.csv"),
    "EV-076": ("3.3", "Verificación del contraste de 1,0 de la evaluación original: era una etiqueta de eje oculta por el propio gráfico (opacidad 0)", "archivo", "`python scripts/evidencias/evidencia_contraste_dudoso.py`", "EV-076_contraste_dudoso.txt"),
    "EV-076b": ("3.3", "Captura del eje de la dispersión de Construcciones a 1024 px que muestra la etiqueta oculta de EV-076", "imagen", "`python scripts/evidencias/evidencia_contraste_dudoso.py`", "EV-076_eje_construcciones_1024.png"),
    "EV-077": ("3.3", "Capturas, desbordamiento y texto recortado de las ocho páginas en tres anchos DESPUÉS de los ajustes", "archivo", _CMD_DESPUES, "EV-077_capturas_anchos.txt"),
    "EV-078": ("3.3", "Tiempos de dibujo de las ocho páginas en tres anchos después de los ajustes (medición local de una máquina, con variabilidad)", "archivo", _CMD_DESPUES, "EV-078_mediciones_anchos.txt"),
    "EV-078b": ("3.3", "Datos de los tiempos de EV-078", "archivo", _CMD_DESPUES, "EV-078_mediciones_anchos.csv"),
    "EV-079": ("3.3", "Contraste calculado del texto del panel después de los ajustes (valores calculados, sin declarar un nivel de conformidad)", "archivo", _CMD_DESPUES, "EV-079_contraste_texto.txt"),
    "EV-079b": ("3.3", "Detalle por página y ancho de los contrastes de EV-079", "archivo", _CMD_DESPUES, "EV-079_contraste_texto.csv"),
    "EV-080": ("3.3", "Evaluación de F-11: los controles en inglés de Streamlit 1.67.0 no se pueden traducir ni ocultar de forma limpia (parámetros, texto en el front y prueba en vivo)", "archivo", "`python scripts/evidencias/evidencia_streamlit_controles.py`", "EV-080_controles_de_streamlit.txt"),
    "EV-081": ("3.3, 5.6", "Tabla de mutaciones de las pruebas de los ajustes del panel (glosario, barra lateral, tarjetas, contraste, coordenadas, barras, aviso de tabla ancha, pie de intervalos): todas detectadas", "archivo",
               "mutación de un archivo en un clon y `python -m pytest -q -p no:cacheprovider tests/test_panel_ajustes.py`", "EV-081_mutaciones_ajustes.txt"),
    "EV-082": ("5.6", "Las pruebas del proyecto pasan en un clon con el entorno nuevo de Python 3.13 en el commit del componente de ajustes del panel, con `data/` idéntico y el escáner de secretos sin hallazgos", "archivo",
               "`python -m pytest -q -p no:cacheprovider` en un clon temporal con el intérprete del entorno nuevo", "EV-082_suite_en_entorno_nuevo.txt"),
}
for _momento, _ev, _cmd in (("antes", "EV-073", _CMD_ANTES), ("despues", "EV-077", _CMD_DESPUES)):
    for _i, (_ancho, (_pid, _titulo)) in enumerate((a, p) for a in (1400, 1024, 390) for p in _PAGINAS):
        FILAS_UX[f"{_ev}{'bcdefghijklmnopqrstuvwxy'[_i]}"] = ("3.3", f"Captura automatizada del navegador de la página {_titulo} a {_ancho} px ({'antes' if _momento == 'antes' else 'después'} de los ajustes)", "imagen", _cmd, f"{_ev}_captura_{_pid}_{_ancho}.png")
CARPETA_SERV = "docs/evidencias/servicios"
FILAS_SERV = {
    "EV-083": ("7.1", "Suite completa en un clon con espacios y tildes en el nombre y sin variables de UTF-8, antes de corregir la portabilidad (1 fallo por codificación y el hallazgo de las rutas largas)", "archivo",
               "`python -m pytest -q -p no:cacheprovider` en un clon temporal con el intérprete del entorno nuevo, sin PYTHONUTF8 ni PYTHONIOENCODING", "EV-083_suite_sin_utf8_antes.txt"),
    "EV-084": ("7.1", "La misma suite después de corregir la portabilidad: la prueba que fallaba por codificación pasa", "archivo", "mismo comando que EV-083", "EV-084_suite_sin_utf8_despues.txt"),
    "EV-085": ("4.1, 4.2", "phpMyAdmin en vivo con la cuenta de solo lectura: siete tablas, claves foráneas, conteos iguales a Gold y escrituras rechazadas por MySQL (#1142)", "archivo",
               "`docker compose -p servicios_prueba_pma -f servicios/phpmyadmin/docker-compose.yaml up -d` y navegador sin ventana por DevTools", "EV-085_phpmyadmin_en_vivo.txt"),
    "EV-087": ("5.4, 7.1", "Airflow construido y ejecutado desde el zip descomprimido en una carpeta de otro nombre: interfaz, DAG sin errores de importación y cuatro tareas en éxito", "archivo",
               "`preparar_airflow.py` y `docker compose -p servicios_prueba` (build, up, dags trigger, down) sobre un zip temporal", "EV-087_airflow_desde_el_zip.txt"),
    "EV-088": ("4.1, 5.6", "Tabla de mutaciones de las pruebas de los servicios locales (puertos, credenciales, privilegios, versiones, canario, `.env` sobrescrito, nombre fijo, zip, codificación): todas detectadas", "archivo",
               "mutación de un archivo en un clon y `python -m pytest -q -p no:cacheprovider` sobre las pruebas de servicios", "EV-088_mutaciones_servicios.txt"),
    "EV-089": ("5.6, 7.1", "Suite completa en verde en un clon con espacios y tildes y sin variables de UTF-8, en el commit del componente de servicios, con `data/` idéntico y el escáner de secretos sin hallazgos", "archivo",
               "`python -m pytest -q -p no:cacheprovider` en un clon temporal con el intérprete del entorno nuevo", "EV-089_suite_final_sin_utf8.txt"),
}
for _i, _n in enumerate(("acceso", "tablas", "estructura_construccion", "relaciones_construccion", "conteos", "tabla_corrida", "insert_rechazado", "drop_rechazado")):
    FILAS_SERV[f"EV-085{'bcdefghi'[_i]}"] = ("4.1, 4.2", f"Captura automatizada del navegador de phpMyAdmin ({_n.replace('_', ' ')})", "imagen", "mismo comando que EV-085", f"EV-085_captura_{_n}.png")
CARPETA_AUD = "docs/evidencias/auditoria"
FILAS_AUD = {
    "EV-090": ("7.1", "Experimentos de independencia en carpetas sin hermanas: el clon pasa las 964 pruebas y el zip fallaba 2 por no traer .git; 9 de 9 hashes iguales en los dos", "archivo",
               "clon o zip de `make_dist.empaquetar` en una carpeta temporal sin hermanas: entorno nuevo, suite, `main.py`, hashes, panel y scripts de servicios", "EV-090_independencia_clon_y_zip.txt"),
    "EV-091": ("7.1", "Tabla de mutaciones de la prueba guardiana de independencia del repositorio: todas detectadas", "archivo",
               "mutación de un archivo en un clon y `python -m pytest -q -p no:cacheprovider` sobre las pruebas de independencia", "EV-091_mutaciones_independencia.txt"),
    "EV-092": ("7.1, 7.2, 7.5", "Tabla de mutaciones de las pruebas de los estados del checklist y de los scripts de verificación en vivo: todas detectadas", "archivo",
               "mutación de un archivo en un clon y `python -m pytest -q -p no:cacheprovider` sobre las pruebas de estados, scripts e independencia", "EV-092_mutaciones_estados_y_scripts.txt"),
    "EV-093": ("7.1", "Igualdad de código entre la etiqueta inicial de la auditoría y el árbol de trabajo: `src/`, `dags/` y `main.py` sin cambios y los notebooks solo en textos", "archivo",
               "`python scripts/validacion/igualdad_de_codigo.py --base auditoria-inicio --rutas src dags notebooks main.py`", "EV-093_igualdad_de_codigo.txt"),
    "EV-094": ("7.1", "Tabla de mutaciones de las pruebas del criterio de texto, el documento aislado, la figura de stakeholders y la herramienta de igualdad: todas detectadas", "archivo",
               "mutación de un archivo en un clon y `python -m pytest -q -p no:cacheprovider` sobre las pruebas de criterio, empaquetado, estrategia e igualdad", "EV-094_mutaciones_criterio_de_texto.txt"),
    "EV-095": ("7.1", "Tabla de mutaciones de la prueba de coherencia de la trazabilidad del checklist: todas detectadas", "archivo",
               "mutación de un archivo en un clon y `python -m pytest -q -p no:cacheprovider tests/test_trazabilidad.py`", "EV-095_mutaciones_trazabilidad.txt"),
    "EV-096": ("7.1", "Independencia repetida con el script movido (clon y zip sin hermanas) y número exacto de pruebas omitidas: 0 con Git, 1 en el zip y 10 sin el binario git", "archivo",
               "`python scripts/evidencias/evidencia_independencia.py clon|zip` y `python -m pytest -q -rs` con el PATH sin git", "EV-096_independencia_repetida_y_omisiones.txt"),
    "EV-097": ("6.4, 7.1", "Pico de memoria de la suite medido con `scripts/evidencias/medir_memoria_suite.py` en una carpeta temporal", "archivo",
               "`python scripts/evidencias/medir_memoria_suite.py --salida <carpeta temporal>`", "EV-097_memoria_de_la_suite.txt"),
}
CARPETA_FIN = "docs/finanzas"
FILAS_FIN = {
    "EV-070": ("6.4", "Recursos medidos del pipeline (tiempo y memoria de `main.py --stage all`, tamaños, memoria de Airflow en reposo) y mediciones previas reunidas, con su origen y fecha; sin cifras monetarias", "archivo",
               "`python scripts/finanzas/medir_recursos.py --docker`", "recursos_medidos.csv"),
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


CARPETA_SIM = "docs/evidencias/simulacion"
FILAS_SIM = {
    "EV-098": ("6.1", "La guía de simulación seguida como una tercera persona desde el zip, en una carpeta con espacios y tilde: partes A, B y E con los comandos de la guía, tiempos, Ctrl+C, plan B, navegador y análisis de datos sintéticos; ambigüedades halladas y corregidas", "archivo",
               "los comandos de `docs/usuarios/guia_simulacion/` (partes A, B y E) sobre el zip de `make_dist.empaquetar` descomprimido", "EV-098_guia_seguida_como_tercero.txt"),
    "EV-099": ("6.1", "Tabla de mutaciones de las pruebas de la guía de simulación y de su generador de PDF: todas detectadas", "archivo",
               "mutación de un archivo en un clon y `python -m pytest -q -p no:cacheprovider tests/test_guia_simulacion.py`", "EV-099_mutaciones_guia_de_simulacion.txt"),
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
    for ev, (item, que, tipo, cmd, archivo) in FILAS_PANEL.items():
        if not (REPO / CARPETA_PANEL / archivo).exists():
            log.warning("falta %s; no se registra %s", archivo, ev)
            continue
        nuevas.append(fila(ev, item, que, tipo, cmd, archivo, CARPETA_PANEL, FECHA_PANEL))
    for ev, (item, que, tipo, cmd, archivo) in FILAS_END.items():
        if not (REPO / CARPETA_END / archivo).exists():
            log.warning("falta %s; no se registra %s", archivo, ev)
            continue
        nuevas.append(fila(ev, item, que, tipo, cmd, archivo, CARPETA_END, FECHA_END))
    for ev, (item, que, tipo, cmd, archivo) in FILAS_USU.items():
        if not (REPO / CARPETA_USU / archivo).exists():
            log.warning("falta %s; no se registra %s", archivo, ev)
            continue
        nuevas.append(fila(ev, item, que, tipo, cmd, archivo, CARPETA_USU, FECHA_USU))
    for ev, (item, que, tipo, cmd, archivo) in FILAS_UX.items():
        if not (REPO / CARPETA_UX / archivo).exists():
            log.warning("falta %s; no se registra %s", archivo, ev)
            continue
        nuevas.append(fila(ev, item, que, tipo, cmd, archivo, CARPETA_UX, FECHA_USU))
    for ev, (item, que, tipo, cmd, archivo) in FILAS_SERV.items():
        if not (REPO / CARPETA_SERV / archivo).exists():
            log.warning("falta %s; no se registra %s", archivo, ev)
            continue
        nuevas.append(fila(ev, item, que, tipo, cmd, archivo, CARPETA_SERV, "2026-11-15"))
    for ev, (item, que, tipo, cmd, archivo) in FILAS_AUD.items():
        if not (REPO / CARPETA_AUD / archivo).exists():
            log.warning("falta %s; no se registra %s", archivo, ev)
            continue
        nuevas.append(fila(ev, item, que, tipo, cmd, archivo, CARPETA_AUD, "2026-11-15"))
    for ev, (item, que, tipo, cmd, archivo) in FILAS_FIN.items():
        if not (REPO / CARPETA_FIN / archivo).exists():
            log.warning("falta %s; no se registra %s", archivo, ev)
            continue
        nuevas.append(fila(ev, item, que, tipo, cmd, archivo, CARPETA_FIN, FECHA_USU))
    for ev, (item, que, tipo, cmd, archivo) in FILAS_SIM.items():
        if not (REPO / CARPETA_SIM / archivo).exists():
            log.warning("falta %s; no se registra %s", archivo, ev)
            continue
        nuevas.append(fila(ev, item, que, tipo, cmd, archivo, CARPETA_SIM, "2026-11-15"))
    ids ={pref for pref, _ in nuevas}
    lineas = [l for l in lineas if not any(l.startswith(i) for i in ids)]
    ultima = max(i for i, l in enumerate(lineas) if l.startswith("| EV-"))   # las filas nuevas van al final de la tabla, antes de la convención
    lineas[ultima + 1:ultima + 1] = [fila for _, fila in nuevas]
    MANIFIESTO.write_text("\n".join(lineas) + "\n", encoding="utf-8", newline="\n")
    total = sum(1 for linea in lineas if linea.startswith("| EV-"))
    log.info("manifiesto: este script escribió %s filas (las de las evidencias que registra) y la tabla tiene %s en total; las demás son anteriores y no se tocan", len(nuevas), total)


if __name__ == "__main__":
    main()
