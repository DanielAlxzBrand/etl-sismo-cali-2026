# Operación de Airflow

> **Procedimiento basado en la guía de Airflow de la asignatura (artículo de Juan Manuel Núñez Velasco).** Los comandos son los de los pasos 27 a 43 y se ejecutan en PowerShell desde la carpeta `airflow-medallon`, junto al proyecto.

## Antes de empezar
1. Docker Desktop en marcha (no pausado): `docker info` debe responder.
2. MySQL80 activo y, para la carga relacional, el usuario de Docker creado con `scripts/mysql/configurar_mysql.py --usuario-docker --origen <PATRÓN>` ([configuración de MySQL](../almacenamiento/mysql_configuracion.md)).
3. El DAG sincronizado: `.\.venv\Scripts\python.exe scripts\orquestacion\sincronizar_dag.py` (desde la raíz del proyecto) y `--verificar`.

## Levantar y parar
```powershell
docker compose build
docker compose up airflow-init
docker compose up -d
docker ps
docker compose down
```
La interfaz está en `http://localhost:8080` (puerto publicado solo en 127.0.0.1). Para volver a levantar después de `down`: `docker compose up -d`.

## Comprobar y ejecutar el DAG
```powershell
docker compose exec airflow-scheduler airflow dags list
docker compose exec airflow-scheduler airflow dags list-import-errors
docker compose exec airflow-scheduler ls /opt/airflow/dags
docker compose exec airflow-scheduler airflow dags trigger medallon_etl_sismo
docker compose exec airflow-scheduler airflow dags list-runs medallon_etl_sismo
docker compose exec airflow-scheduler airflow dags unpause medallon_etl_sismo
```
Para provocar un fallo controlado (pasos 35 y 36): `airflow dags trigger medallon_etl_sismo --conf '{"fallo_inducido":"integrar_a_gold"}'`; la tarea indicada falla antes de producir salidas y las siguientes no se ejecutan.

## Registros
```powershell
docker compose logs airflow-scheduler
docker compose logs -f airflow-scheduler
docker compose restart airflow-scheduler
```
Los registros de cada tarea están en la interfaz (Tarea → Logs) y en `airflow-medallon\logs`. No contienen contraseñas: la tarea de carga no las imprime.

## Solución de problemas
| Síntoma | Causa probable | Qué hacemos |
|---|---|---|
| `docker info` dice que Docker Desktop está en pausa | pausa manual | reanudar Docker Desktop |
| El DAG no aparece | error de importación | `airflow dags list-import-errors` |
| `validar_bronze` falla | Bronze o manifiesto distintos de lo versionado | revisar `git status` del proyecto y `data/bronze` |
| `transformar_a_silver` o `integrar_a_gold` fallan con «Salida distinta de la versionada» | cambió una dependencia o un dato | no se modifica el repositorio: comparar versiones de `orquestacion/requirements-airflow.txt` con el `.venv` (D56) |
| `cargar_datawarehouse` falla al conectar | el origen del usuario de Docker no coincide con el del contenedor, o MySQL no escucha | repetir la configuración con el origen correcto; verificar la regla de entrada del cortafuegos |
| Falta de memoria | recursos de WSL2 | crear `%USERPROFILE%\.wslconfig` con `[wsl2]`, `memory=8GB` y `swap=2GB`; `wsl --shutdown` |
| La interfaz no carga | puerto 8080 ocupado | `Get-NetTCPConnection -LocalPort 8080` |

## Programación
Con el DAG programado (`0 6 * * *` en America/Bogota) y activo (`airflow dags unpause`), el planificador lo ejecuta a las 06:00 hora de Bogotá con el equipo y Docker encendidos; con `catchup=False` no recupera los días en que estuvo apagado.
