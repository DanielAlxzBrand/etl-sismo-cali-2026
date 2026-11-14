# Guía de implementación de Airflow: pasos 13 a 44

> **Procedimiento basado en la guía de Airflow de la asignatura (artículo de Juan Manuel Núñez Velasco).** Los pasos se citan por su número y se parafrasean. Los pasos 1 a 12 (instalación de WSL2 y Docker Desktop) ya los hizo el equipo y no se repiten. En la guía falta el paso 16 y están repetidos el 28 y el 41 (H-1 y H-2 de [diferencias_con_la_guia.md](diferencias_con_la_guia.md)).

**Estado.** Cada paso queda con su estado final («tal cual» o «con diferencia DF-n», más los hallazgos H-n) y su evidencia. Las ejecuciones se hacen desde `..\airflow-medallon` como indica la guía.

| Paso | Qué hace (paráfrasis) | Estado | Diferencia | Evidencia |
|---|---|---|---|---|
| 13 | Crear la carpeta `airflow-medallon` junto al proyecto, con `dags`, `logs`, `plugins` y `config` | ejecutado: tal cual | — | [EV-037](../evidencias/orquestacion/EV-037_pasos_13_a_19.txt) |
| 14 | Descargar el `docker-compose.yaml` de Airflow 3.3.2 con `curl.exe -LfO` | ejecutado: tal cual | — | [EV-037](../evidencias/orquestacion/EV-037_pasos_13_a_19.txt) |
| 15 | Crear `.env` con `AIRFLOW_UID` | ejecutado: con diferencia | DF-8 (contraseña de la interfaz en `.env`, no la de ejemplo); H-6 (CRLF) | [EV-037](../evidencias/orquestacion/EV-037_pasos_13_a_19.txt) |
| 16 | (ausente en la guía) contenido de `requirements-airflow.txt` | ejecutado: con diferencia | DF-5 (H-1) | [EV-037](../evidencias/orquestacion/EV-037_pasos_13_a_19.txt) |
| 17 | Dockerfile sobre `apache/airflow:3.3.2` que instala los requisitos | ejecutado: con diferencia | DF-6 (H-3, H-4) | [EV-037](../evidencias/orquestacion/EV-037_pasos_13_a_19.txt) |
| 18 | Montar el proyecto en el contenedor (`/opt/airflow/medallon`) | ejecutado: con diferencia | DF-1 (solo lectura, H-8) | [EV-037](../evidencias/orquestacion/EV-037_pasos_13_a_19.txt), [EV-039](../evidencias/orquestacion/EV-039_pasos_31_a_33.txt) |
| 19 | Que Docker construya nuestra imagen (`build: .`) | ejecutado: con diferencia | DF-12 (línea `image:` comentada, H-7) | [EV-037](../evidencias/orquestacion/EV-037_pasos_13_a_19.txt) |
| 20 | Crear `dags/medallon_etl_dag.py` | ejecutado: con diferencia | DF-3, DF-11 | [EV-039](../evidencias/orquestacion/EV-039_pasos_31_a_33.txt) |
| 21 | Código del DAG: cuatro tareas con sus dependencias | ejecutado: con diferencia | DF-2, DF-3, DF-4, DF-7, DF-9 y DF-10 (H-5, H-14, H-15) | [EV-039](../evidencias/orquestacion/EV-039_pasos_31_a_33.txt), [EV-041](../evidencias/orquestacion/EV-041_ejecucion_manual.txt) |
| 22 | Entender el DAG | lectura; reflejado en el DAG | — | `tests/test_dag_estatico.py` |
| 23 | `schedule=None`: ejecución manual | ejecutado: tal cual (valor inicial) | DF-9 después, en el paso 40 | [EV-041](../evidencias/orquestacion/EV-041_ejecucion_manual.txt) |
| 24 | `catchup=False` | ejecutado: tal cual | — | [EV-043](../evidencias/orquestacion/EV-043_programacion.txt) |
| 25 | `@task` convierte una función en tarea | ejecutado: tal cual | — | [EV-039](../evidencias/orquestacion/EV-039_pasos_31_a_33.txt) |
| 26 | Dependencias con `>>` | ejecutado: tal cual | — | [EV-041](../evidencias/orquestacion/EV-041_ejecucion_manual.txt) |
| 27 | `docker compose build` | ejecutado: tal cual | H-16 (aviso de pip, sin efecto) | [EV-038](../evidencias/orquestacion/EV-038_pasos_27_a_30.txt) |
| 28 | `docker compose up airflow-init` (salida con código 0) | ejecutado: tal cual | — | [EV-038](../evidencias/orquestacion/EV-038_pasos_27_a_30.txt) |
| 29 | `docker compose up -d` | ejecutado: con diferencia | DF-8 (puertos en 127.0.0.1); H-17 y H-18 | [EV-038](../evidencias/orquestacion/EV-038_pasos_27_a_30.txt) |
| 30 | `docker ps` | ejecutado: tal cual | — | [EV-038](../evidencias/orquestacion/EV-038_pasos_27_a_30.txt) |
| 31 | Abrir la interfaz en `http://localhost:8080` | ejecutado: con diferencia | DF-8 (HTTP 200 y estado de salud; la contraseña no se imprime) | [EV-039](../evidencias/orquestacion/EV-039_pasos_31_a_33.txt) |
| 32 | `airflow dags list` y `list-import-errors` | ejecutado: tal cual | H-12 (el DAG nace pausado) | [EV-039](../evidencias/orquestacion/EV-039_pasos_31_a_33.txt) |
| 33 | `ls /opt/airflow/dags` dentro del contenedor | ejecutado: tal cual | — | [EV-039](../evidencias/orquestacion/EV-039_pasos_31_a_33.txt) |
| 34 | Ejecutar el DAG (Trigger DAG) | ejecutado: con diferencia | DF-9 (`airflow dags unpause` antes; con el DAG pausado la ejecución queda en `queued`) | [EV-041](../evidencias/orquestacion/EV-041_ejecucion_manual.txt) |
| 35 | Qué pasa si una tarea falla | ejecutado: con diferencia | DF-10 (fallo inducido por `dag_run.conf`) | [EV-042](../evidencias/orquestacion/EV-042_fallo_inducido_y_recuperacion.txt) |
| 36 | Revisar los registros de una tarea | ejecutado: con diferencia | DF-10 | [EV-042](../evidencias/orquestacion/EV-042_fallo_inducido_y_recuperacion.txt) |
| 37 | `airflow dags trigger` y `list-runs` desde la terminal | ejecutado: tal cual | — | [EV-041](../evidencias/orquestacion/EV-041_ejecucion_manual.txt) |
| 38 | Diferencia entre el entorno de VS Code y el de Docker | lectura; nuestras pruebas del DAG son estáticas | — | `tests/test_dag_estatico.py` |
| 39 | No instalar Airflow en el entorno virtual de Windows | cumplido: no hay Airflow en el `.venv` | — | `requirements.txt` |
| 40 | Programar el pipeline (`@daily` o cron) | ejecutado: con diferencia | DF-9 (`0 6 * * *` en America/Bogota; cron temporal para una ejecución programada real) | [EV-043](../evidencias/orquestacion/EV-043_programacion.txt) |
| 41 | `docker compose down` y volver a levantar | ejecutado: tal cual | — | [EV-044](../evidencias/orquestacion/EV-044_operacion.txt) |
| 42 | `docker compose restart airflow-scheduler` | ejecutado: tal cual | — | [EV-044](../evidencias/orquestacion/EV-044_operacion.txt) |
| 43 | `docker compose logs` (y `-f` del scheduler) | ejecutado: tal cual | H-10 (ejecutor del compose oficial) | [EV-044](../evidencias/orquestacion/EV-044_operacion.txt) |
| 44 | Arquitectura completa obtenida | ejecutado: 7 contenedores en `healthy` y diagrama generado | — | [EV-038](../evidencias/orquestacion/EV-038_pasos_27_a_30.txt); [arquitectura_orquestacion.png](img/arquitectura_orquestacion.png) |

Los 32 números de paso de la guía (13 a 44; el 16 falta y el 28 y el 41 se repiten) quedaron ejecutados o cumplidos: 15 «tal cual», 13 «con diferencia» de la lista cerrada DF-1 a DF-12 y 4 de lectura, cumplimiento o comprobación final (22, 38, 39 y 44). Detalle de cada diferencia en [diferencias_con_la_guia.md](diferencias_con_la_guia.md); cómo operar el sistema, en [operacion.md](operacion.md).
