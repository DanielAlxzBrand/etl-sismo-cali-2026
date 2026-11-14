# Guía de implementación de Airflow: pasos 13 a 44

> **Procedimiento basado en la guía de Airflow de la asignatura (artículo de Juan Manuel Núñez Velasco).** Los pasos se citan por su número y se parafrasean. Los pasos 1 a 12 (instalación de WSL2 y Docker Desktop) ya los hizo el equipo y no se repiten. En la guía falta el paso 16 y están repetidos el 28 y el 41 (H-1 y H-2 de [diferencias_con_la_guia.md](diferencias_con_la_guia.md)).

**Estado.** «Preparado» significa que el código o el archivo ya existe y se prueba sin Docker; «por ejecutar» significa que el paso se hace con Docker en marcha. Cada paso ejecutado se registra aquí con su estado final («tal cual» o «con diferencia DF-n») y su evidencia. Las ejecuciones se hacen desde `..\airflow-medallon` como indica la guía.

| Paso | Qué hace (paráfrasis) | Estado | Diferencia | Evidencia |
|---|---|---|---|---|
| 13 | Crear la carpeta `airflow-medallon` junto al proyecto, con `dags`, `logs`, `plugins` y `config` | por ejecutar | — | |
| 14 | Descargar el `docker-compose.yaml` de Airflow 3.3.2 con `curl.exe -LfO` | por ejecutar | — | |
| 15 | Crear `.env` con `AIRFLOW_UID` | por ejecutar | DF-8 si el compose permite fijar la contraseña de la interfaz | |
| 16 | (ausente en la guía) contenido de `requirements-airflow.txt` | preparado: `orquestacion/requirements-airflow.txt` | DF-5 | `tests/test_dag_estatico.py` |
| 17 | Dockerfile sobre `apache/airflow:3.3.2` que instala los requisitos | preparado: `orquestacion/Dockerfile` | DF-6 | `tests/test_dag_estatico.py` |
| 18 | Montar el proyecto en el contenedor (`/opt/airflow/medallon`) | por ejecutar | DF-1 | |
| 19 | Que Docker construya nuestra imagen (`build: .`) | por ejecutar | DF-12 | |
| 20 | Crear `dags/medallon_etl_dag.py` | preparado: `dags/medallon_etl_dag.py` y `scripts/orquestacion/sincronizar_dag.py` | DF-3 | |
| 21 | Código del DAG: cuatro tareas con sus dependencias | preparado | DF-2, DF-3, DF-4, DF-7, DF-9 y DF-10 | `tests/test_dag_estatico.py` |
| 22 | Entender el DAG | lectura; reflejado en el DAG | — | |
| 23 | `schedule=None`: ejecución manual | preparado (valor inicial) | DF-9 | |
| 24 | `catchup=False` | preparado | — | |
| 25 | `@task` convierte una función en tarea | preparado | — | |
| 26 | Dependencias con `>>` | preparado | — | |
| 27 | `docker compose build` | por ejecutar | — | |
| 28 | `docker compose up airflow-init` (salida con código 0) | por ejecutar | — | |
| 29 | `docker compose up -d` | por ejecutar | DF-8 (puertos en 127.0.0.1) | |
| 30 | `docker ps` | por ejecutar | — | |
| 31 | Abrir la interfaz en `http://localhost:8080` | por ejecutar | DF-8 | |
| 32 | `airflow dags list` y `list-import-errors` | por ejecutar | — | |
| 33 | `ls /opt/airflow/dags` dentro del contenedor | por ejecutar | — | |
| 34 | Ejecutar el DAG (Trigger DAG) | por ejecutar | — | |
| 35 | Qué pasa si una tarea falla | por ejecutar | DF-10 | |
| 36 | Revisar los registros de una tarea | por ejecutar | DF-10 | |
| 37 | `airflow dags trigger` y `list-runs` desde la terminal | por ejecutar | — | |
| 38 | Diferencia entre el entorno de VS Code y el de Docker | lectura; nuestras pruebas del DAG son estáticas | — | `tests/test_dag_estatico.py` |
| 39 | No instalar Airflow en el entorno virtual de Windows | cumplido: no hay Airflow en el `.venv` | — | `requirements.txt` |
| 40 | Programar el pipeline (`@daily` o cron) | por ejecutar | DF-9 | |
| 41 | `docker compose down` y volver a levantar | por ejecutar | — | |
| 42 | `docker compose restart airflow-scheduler` | por ejecutar | — | |
| 43 | `docker compose logs` (y `-f` del scheduler) | por ejecutar | — | |
| 44 | Arquitectura completa obtenida | diagrama en [mlops_y_produccion.md](mlops_y_produccion.md) (se genera al terminar) | — | |

Los pasos «por ejecutar» pasan a «tal cual» o «con diferencia DF-n» con su evidencia en `docs/evidencias/orquestacion/` cuando se ejecutan con Docker en marcha.
