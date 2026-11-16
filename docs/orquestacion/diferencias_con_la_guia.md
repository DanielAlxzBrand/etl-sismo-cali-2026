# Diferencias con la guía de Airflow

> **Procedimiento basado en la guía de Airflow de la asignatura (artículo de Juan Manuel Núñez Velasco).** Citamos los pasos por número y parafraseamos; la guía es la fuente de verdad y solo nos apartamos de ella en lo que se lista aquí.

**Regla.** Airflow se implementa como en la guía: mismos pasos, orden, comandos, estructura, nombres de archivos, imagen, volúmenes y forma de ejecutar y comprobar. Los pasos 1 a 12 (instalación de WSL2 y Docker) ya los hizo el equipo. Solo se permiten las diferencias DF-1 a DF-12. Si la guía falla o es ambigua, lo registramos como hallazgo **H-n**, aplicamos la corrección mínima y seguimos.

## 1. Diferencias permitidas (DF)
| DF | Paso de la guía | Qué cambia | Por qué es inevitable | Evidencia de que es necesaria |
|---|---|---|---|---|
| DF-1 | 13 y 18 | `../medallon` pasa a `../etl_sismo_cali_2026` en el volumen; la ruta interna sigue siendo `/opt/airflow/medallon`; el volumen es de solo lectura (`:ro`) | la carpeta hermana real se llama `etl_sismo_cali_2026`; el modo de solo lectura es decisión del equipo (el repositorio no se escribe nunca) | D58; carpeta real del proyecto |
| DF-2 | 21 | `validar_bronze` crea una copia de trabajo mínima en el contenedor (`src`, `config`, `data` y `docs/silver/hallazgos_eda.md`), única por ejecución y fuera del volumen; cada tarea compara lo que produce con lo versionado (CSV y JSON byte a byte, `etl_sismo.db` tabla a tabla) y falla si difiere; la copia se elimina al terminar o si una tarea falla | el pipeline escribe en `data/` y en `docs/silver`, que son la línea base del proyecto | [EV-035](../evidencias/orquestacion/EV-035_estabilidad_pipeline.txt): la base SQLite no es idéntica byte a byte entre ejecuciones y `run_transform` regenera documentos; D58 y D59 |
| DF-3 | 20 y 21 | `dag_id` `medallon_etl_sismo`, archivo `medallon_etl_dag.py` y cuerpos de las cuatro tareas con nuestros módulos: `validar_bronze` = `src.common.read_manifest` + `verify_files` (8 líneas con sha256, sin descargar); `transformar_a_silver` = `run_transform()`; `integrar_a_gold` = `run_gold()`; `cargar_datawarehouse` = `load_to_sqlite()` y luego `relacional.cargar(conn, "mysql")` | el ejemplo de la guía es de estudiantes; nuestros datos y módulos son otros | nombres leídos del código real: `src/common.py`, `src/transform/integrate.py`, `src/transform/build_gold.py`, `src/load/load_database.py`, `src/load/relacional.py` y `conexion.py`; Bronze es inmutable (`save_bronze` en modo `xb`) |
| DF-4 | 21 | la tarea de carga usa `MYSQL_HOST=host.docker.internal` y un usuario propio de Docker; las credenciales se leen en memoria del `.env` montado y viajan por `os.environ` de la tarea | `config.yaml` trae el host 127.0.0.1 (en el contenedor sería el propio contenedor) y el usuario del proyecto solo existe para `localhost` (D46) | D60; `config/config.yaml` y `scripts/mysql/configurar_mysql.py` |
| DF-5 | 16 (ausente) | `requirements-airflow.txt` con pandas, numpy, PyYAML, python-dotenv, requests, shapely, PyMySQL y cryptography, con las versiones del `.venv` | la guía no trae el contenido del paso 16; con otras versiones las salidas cambian | H-1 y D56; EV-035 |
| DF-6 | 17 | `COPY` y `RUN` en líneas distintas; se comprueba la variable `AIRFLOW_VERSION` de la imagen y, si no existe, se declara con `ARG` | en el documento se perdió el salto de línea y el `RUN` usa una variable no declarada | H-3 y H-4 |
| DF-7 | 21 | se reconstruyen saltos de línea e indentación del código; `start_date` con zona America/Bogota | el código del documento llegó unido y es inválido tal cual | H-5; `tests/test_dag_estatico.py` |
| DF-8 | 15, 29 y 31 | la contraseña de la interfaz no queda en el valor por defecto (si el compose permite fijarla por `.env`, se genera con `secrets` y se guarda solo allí); puertos publicados solo en 127.0.0.1; `airflow-medallon/.env` solo con `AIRFLOW_UID` y, si hace falta, la variable de la contraseña | las reglas de secretos del proyecto no admiten contraseñas por defecto | H-11; [gestión de credenciales](../seguridad/gestion_credenciales.md) |
| DF-9 | 40 | se valida primero con `schedule=None` (34 a 37) y luego se programa `"0 6 * * *"` en America/Bogota con `catchup=False`; complemento `airflow dags unpause`; para obtener una ejecución programada real se usa un cron temporal cercano | el ítem 5.4 pide «flujos programados» y la guía no activa el DAG | H-12; D64 |
| DF-10 | 35 y 36 | el DAG lee `dag_run.conf` y, solo si trae `fallo_inducido` con el nombre de una tarea, esa tarea falla antes de producir salidas | los pasos 35 y 36 describen un fallo y hay que poder provocarlo sin cambiar el código | `tests/test_dag_estatico.py` |
| DF-11 | (empaquetado) | copia versionada del DAG en `dags/` y carpeta `orquestacion/` con Dockerfile, requisitos y el diff del compose; `sincronizar_dag.py` los compara | el DAG vivo está fuera del repositorio y el paquete debe incluirlo | `scripts/make_dist.py` prevé `dags/` y `orquestacion/` |
| DF-12 | 18 y 19 | edición del compose: volumen y `build: .`; se decide qué hacer con la línea `image:` | la guía no lo dice | H-7 |

## 2. Hallazgos de la guía y de la preparación (H-n)
| H | Paso | Qué encontramos | Corrección mínima aplicada |
|---|---|---|---|
| H-1 | 16 | falta el paso (contenido de `requirements-airflow.txt`) | DF-5: versiones del `.venv` |
| H-2 | 28 y 41 | los pasos están repetidos con el mismo texto | se ejecutan una vez; sin efecto |
| H-3 | 17 | `COPY … /requirements-airflow.txtRUN pip install …` unidos en una línea | DF-6: líneas separadas |
| H-4 | 17 | `${AIRFLOW_VERSION}` sin `ARG` ni `ENV` en el Dockerfile | DF-6: se comprueba la imagen base y, si hace falta, se declara |
| H-5 | 21 | código sin saltos de línea (`from pathlib import Pathimport pandas as pd…`, `@task` y `def` pegados, `import … \` partido) | DF-7: se reconstruye sin cambiar nombres, orden ni mensajes |
| H-6 | 15 | `Out-File -Encoding ascii` escribe saltos CRLF y `AIRFLOW_UID=50000` no tiene efecto en Windows con WSL2 | se registra el efecto al ejecutar; sin cambio de contenido |
| H-7 | 19 | `build: .` sin decir qué hacer con la línea `image:` del compose | DF-12: se decide al leer el compose descargado |
| H-8 | 18 | el volumen se agrega a un bloque «similar a» el de la guía, que en el compose oficial aplica a todos los servicios, y monta la carpeta completa del proyecto | DF-1: solo lectura |
| H-9 | 22 | el texto trae avisos de la página de origen (suscripción) | se ignoran |
| H-10 | 30 | el ejecutor no se declara (la lista de servicios implica Celery, Redis y Postgres) | se usa el del compose oficial sin cambios |
| H-11 | 31 | no da usuario ni contraseña de la interfaz | DF-8 |
| H-12 | 40 | el cron corre en UTC, `start_date` no tiene zona y no se dice activar el DAG (nace pausado en el compose oficial) | DF-9 |
| H-13 | (entorno) | el `.venv` había pasado a pandas 3.1.1 y las salidas ya no se reproducían ([EV-035](../evidencias/orquestacion/EV-035_estabilidad_pipeline.txt), DEF-011) | se restauró pandas 3.0.6 y se fijó en los requisitos (D56) |
| H-14 | 21 | `run_transform` lee `docs/silver/hallazgos_eda.md`; una copia sin ese archivo falla (DEF-012) | la copia de trabajo incluye ese único archivo de `docs/silver` |
| H-15 | 21 | para importar `src` solo desde la copia, la copia se crea antes de validar el manifiesto; la validación comprueba además que el manifiesto de la copia sea idéntico al del repositorio | `validar_bronze` copia, compara el manifiesto y verifica los 8 sha256 |
| H-16 | 27 | `apache-airflow-providers-mysql 6.6.2` (ya incluido en la imagen base) pide `pymysql<1.2` y el proyecto usa 1.2.4: pip lo avisa y no impide la instalación ([EV-038](../evidencias/orquestacion/EV-038_pasos_27_a_30.txt)) | no se cambia la versión: el DAG no usa el proveedor de MySQL de Airflow, se conecta con `src.load.conexion` (PyMySQL 1.2.4) |
| H-17 | 29 | el compose oficial usa `${FERNET_KEY}` sin valor por defecto y Compose avisa de una cadena vacía en cada comando | se deja así: no se guardan conexiones ni variables en Airflow (las credenciales se leen del `.env` del proyecto en memoria); ver `docs/seguridad/gestion_credenciales.md` |
| H-18 | 18 y 29 | el compose oficial trae un secreto JWT y una contraseña de Postgres de ejemplo | se mitiga publicando solo el 8080 y solo en 127.0.0.1 (Postgres y Redis no se publican); no se cambian para no apartarse del compose oficial (DF-8 solo cubre la contraseña de la interfaz) |

## 3. Extras opcionales que no incluimos
Reintentos, tareas adicionales, ejecutor local, carga de ejemplos y las pruebas P1 a P5 del laboratorio de clase no están en la guía y no se implementan.

## 4. Qué decidiría un posible conflicto
El ítem 5.4 dice «flujos programados (DAGs de Airflow)». La guía llega a `schedule=None` y solo propone programar en el paso 40; por eso aplicamos ese paso (DF-9).

## 5. Diferencias nuevas al incluir el compose adaptado (DF-13 a DF-19)
Hasta ahora el compose se descargaba y se editaba a mano (pasos 14, 18 y 19 de la guía, DF-12). Para que quien reciba el zip pueda levantar Airflow sin ese procedimiento, el compose adaptado viaja dentro del repositorio (D92) y lo genera
`scripts/orquestacion/generar_compose.py` desde el oficial de Airflow 3.3.2 (se comprueba su sha256, `99da85d87016…`, el mismo de [EV-037](../evidencias/orquestacion/EV-037_pasos_13_a_19.txt)). Cada cambio es un reemplazo exacto sobre el texto
oficial y el diff completo está en `orquestacion/docker-compose.diff` (con la contraseña de ejemplo del oficial oculta: lo dice su primera línea). Estas diferencias se suman a la lista cerrada de la sección 1:

| DF | Paso de la guía | Qué cambia | Por qué es necesario |
|---|---|---|---|
| DF-13 | 18 | el volumen del proyecto pasa de `../etl_sismo_cali_2026` a `../${PROYECTO_NOMBRE}` (obligatoria, de solo lectura); la ruta interna sigue siendo `/opt/airflow/medallon` | el nombre de la carpeta del proyecto ya no es fijo: quien descomprime el zip puede llamarla como quiera (`preparar_airflow.py` lo detecta y lo escribe en el `.env` de Airflow) |
| DF-14 | 29 y 31 | el puerto de la interfaz pasa de `127.0.0.1:8080:8080` a `127.0.0.1:${AIRFLOW_PUERTO:-8080}:8080` y el de Flower (servicio opcional) de `5555:5555` a `127.0.0.1:5555:5555` | si el 8080 está ocupado el script acepta otro puerto; y Flower, que el compose oficial publica en todas las interfaces, queda solo en este equipo |
| DF-15 | 15 y 29 | `AIRFLOW__CORE__FERNET_KEY` pasa de `${FERNET_KEY}` (en blanco con un aviso en cada comando, H-17) a `${FERNET_KEY:?…}`: el compose se niega a arrancar si el `.env` de Airflow no la trae | `preparar_airflow.py` genera una clave Fernet aleatoria y la escribe solo en ese `.env`; así Airflow nunca cifra con una clave vacía |
| DF-16 | 15 y 31 | `_AIRFLOW_WWW_USER_PASSWORD` pasa de `${…:-airflow}` (contraseña por defecto) a `${…:?…}` (obligatoria) | completa DF-8: la interfaz no puede quedar con la contraseña de ejemplo ni siquiera si se olvida el `.env` |
| DF-17 | 18 | las imágenes `postgres:16` y `redis:7.2-bookworm` conservan su etiqueta y se fijan además por su resumen (`@sha256:…`) | una etiqueta de Docker se reconstruye con el tiempo; con el resumen todos los equipos usan la misma imagen que probamos |
| DF-18 | 18 y 29 | la contraseña de Postgres (`POSTGRES_PASSWORD` y las dos URL de conexión) y el secreto JWT (`AIRFLOW__API_AUTH__JWT_SECRET`) pasan de valores de ejemplo escritos en el compose a `${…:?…}` obligatorios; `preparar_airflow.py` los genera aleatorios y distintos entre sí y los escribe solo en el `.env` de Airflow | el compose entregado no puede llevar contraseñas escritas (el escáner de secretos las marca como URL con credenciales) y deja de aplicarse H-18: ya no hay credenciales de ejemplo, ni siquiera en Postgres, que no se publica |
| DF-19 | 19 y 27 | en `airflow-init`, el `chown -R "${AIRFLOW_UID:-50000}:0" /opt/airflow/` del oficial pasa a `find /opt/airflow -path /opt/airflow/medallon -prune -o -exec chown -h "${AIRFLOW_UID:-50000}:0" {} +` | con DF-13 el proyecto está montado en `/opt/airflow/medallon` en solo lectura; el `chown -R` recorría su `.venv` y dejaba una línea «Read-only file system» por archivo (visto al probar el zip). El nuevo comando salta ese montaje, sigue cambiando el dueño del resto de `/opt/airflow` y el `chown` siguiente de `logs`, `dags`, `plugins` y `config` queda igual |

Lo que **no** cambia: Redis no lleva contraseña en el oficial y se deja igual. H-18 (valores de ejemplo de Postgres y del JWT) queda superado por DF-18. La imagen de Airflow sigue siendo `apache/airflow:3.3.2` (resumen
`sha256:e9982ad3f49a60418622e1baf80c34b0daf3fa5091a336cb5ee61f0cdd189371`, comprobado el 2026-11-14), construida con el Dockerfile de `orquestacion/` como en el paso 17. El `orquestacion/README.md` dice «El compose completo no se
redistribuye»: era cierto antes de D92 y ya no lo es; ese texto se corrige en la revisión final de la documentación.

Qué NO demuestra: que el compose adaptado funcione con otra versión de Airflow; si Airflow cambia su compose, el generador falla en lugar de escribir otra cosa.
