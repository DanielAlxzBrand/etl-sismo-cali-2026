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

## Desde el zip
Esta sección explica cómo levantar Airflow con solo el zip del proyecto, sin la carpeta `airflow-medallon` ni el compose original (D92). La escribimos porque el procedimiento de arriba supone que quien lo ejecuta ya hizo los pasos
13 a 19 de la guía a mano; ahora el compose adaptado viene en `orquestacion/docker-compose.yaml` y un script prepara el resto. Requisitos: [modo mínimo](../instalacion/modo_minimo.md) funcionando, Docker Desktop encendido y, para la carga a MySQL,
las cuentas de la [configuración de MySQL](../almacenamiento/mysql_configuracion.md) (`--usuario-docker --origen localhost`). Desde la raíz del proyecto descomprimido, en PowerShell:

```powershell
.\.venv\Scripts\python.exe scripts\orquestacion\preparar_airflow.py --verificar   # mira sin escribir: dice qué falta
.\.venv\Scripts\python.exe scripts\orquestacion\preparar_airflow.py               # prepara ..\airflow-medallon (carpeta hermana) con el puerto 8080
cd ..\airflow-medallon
docker compose build                    # construye la imagen con las dependencias del pipeline
docker compose up airflow-init          # crea la base de metadatos y el usuario de la interfaz
docker compose up -d
docker compose exec airflow-scheduler airflow dags list-import-errors      # «No data found»
docker compose exec airflow-scheduler airflow dags unpause medallon_etl_sismo
docker compose exec airflow-scheduler airflow dags trigger medallon_etl_sismo
docker compose exec airflow-scheduler airflow dags list-runs medallon_etl_sismo
```
Qué hace `preparar_airflow.py` y qué no está en `docs/instalacion/modo_completo.md`: la carpeta de Airflow tiene que ser **hermana** de la del proyecto porque el compose monta `../<nombre del proyecto>` en solo lectura; el nombre se detecta
solo y queda en la variable `PROYECTO_NOMBRE` del `.env` de Airflow, junto con una contraseña de la interfaz y una `FERNET_KEY` aleatorias que el script nunca imprime. El `.env` se escribe solo si no existe. Los comandos siguen
siendo los de los pasos 27 a 43 de la guía; lo único nuevo es de dónde salen el compose y el `.env`.

**Tiempos medidos** al armar Airflow desde un zip descomprimido en una carpeta de otro nombre (medición de una máquina, con las imágenes base ya descargadas; [EV-087](../evidencias/servicios/EV-087_airflow_desde_el_zip.txt)):

| Paso | Tiempo |
|---|---|
| `preparar_airflow.py` | 0,9 s |
| `docker compose build` | 5,5 s **con la caché de construcción de esta máquina** (desde cero tarda mucho más: no lo medimos) |
| `docker compose up airflow-init` | 47,7 s |
| `docker compose up -d` hasta que la interfaz responde | 106,4 s (el DAG apareció en `dags list` unos 77 s después) |
| una ejecución del DAG (cuatro tareas) | 49,4 s hasta el estado final (61,5 s contando desde el disparo) |

## Operación en otra máquina
Lo que cambia al levantar Airflow en el equipo de otra persona, y qué hacemos en cada caso:
1. **Otro nombre de carpeta.** Se detecta solo al preparar. Si la persona renombra la carpeta del proyecto después, `preparar_airflow.py --verificar` marca «PROYECTO_NOMBRE no coincide»; se corrige con `--regenerar` (reescribe el `.env` de Airflow con valores nuevos) o editando esa variable.
2. **Puerto ocupado.** El script avisa y sugiere otro: `preparar_airflow.py --puerto 8082`. Si ya existe un `.env` con otro `AIRFLOW_PUERTO`, no lo cambia y lo avisa (con `--regenerar` sí).
3. **El `.env` del proyecto no trae `MYSQL_DOCKER_*`.** El script lo dice por nombre y da el comando que las crea; la contraseña de `root` la teclea la persona. Sin esas variables el DAG falla en `cargar_datawarehouse` (las otras tres tareas funcionan).
4. **Memoria.** Airflow ocupa cerca de 1.970 MiB en reposo ([recursos_medidos.csv](../finanzas/recursos_medidos.csv)); con 8 GB de RAM se limita WSL2 con `%USERPROFILE%\.wslconfig` (`[wsl2]`, `memory=4GB`, `swap=2GB`) y se apaga el panel mientras se usa Airflow. Esto no está probado en un equipo de 8 GB.
5. **Un Airflow que ya existe.** Si la persona ya tiene su propia carpeta de Airflow, no hay que tocarla: se prepara otra con `--destino` (hermana del proyecto) y otro `--puerto`, y se usa `-p <nombre>` en `docker compose` para que los contenedores y volúmenes no se mezclen.
6. **Programación a las 06:00.** El DAG está programado a las 06:00 de Bogotá, pero solo corre con el equipo y Docker encendidos y sin recuperar días perdidos (`catchup=False`, D64).
7. **Limpiar.** `docker compose down` apaga y conserva los volúmenes; `docker compose down -v` borra también la base de metadatos de Airflow.

Qué NO demuestra esta sección: que funcione en una máquina limpia de verdad (en la nuestra ya estaban Docker, MySQL y las imágenes base), con 8 GB de RAM, ni que el DAG corra a las 06:00 con el equipo apagado.
