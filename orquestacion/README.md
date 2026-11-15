# Carpeta `orquestacion/`

> **Procedimiento basado en la guía de Airflow de la asignatura (artículo de Juan Manuel Núñez Velasco).**

Archivos con los que `scripts/orquestacion/preparar_airflow.py` arma la carpeta de Airflow (`airflow-medallon`, junto al proyecto) para construir la imagen y levantar el DAG. Esa carpeta **se genera**: no es un requisito previo ni se versiona. La documentación completa está en [docs/orquestacion/](../docs/orquestacion/README.md) y la guía de instalación, en [docs/instalacion/](../docs/instalacion/README.md).

| Archivo | Para qué sirve | Paso de la guía |
|---|---|---|
| `docker-compose.yaml` | compose adaptado del oficial de Airflow 3.3.2 (D91 y D92): monta el proyecto en solo lectura, no trae contraseñas y lee todo del `.env` de Airflow; **viaja en el repositorio y en el zip** | 19 |
| `docker-compose.diff` | diferencias entre el compose oficial y el adaptado, para revisarlas | 19 |
| `Dockerfile` | imagen sobre `apache/airflow:3.3.2` con las dependencias del pipeline | 17 |
| `requirements-airflow.txt` | dependencias con las mismas versiones que el `.venv` (pandas 3.0.6 para reproducir la línea base) | 16 (ausente en la guía) |
| `airflow-env.nombres.txt` | **solo los nombres** de las siete variables del `.env` de Airflow que escribe `preparar_airflow.py` (sin valores); una prueba lo compara con el script | — |
| `dag.sha256` | sha256 del DAG versionado (`dags/medallon_etl_dag.py`); una prueba lo exige | — |
| `README.md` | este archivo | — |

En `airflow-medallon/.env` solo van variables de Airflow (el usuario de ejecución, la contraseña de la interfaz, la clave Fernet, la contraseña de Postgres, el secreto del API, el nombre del proyecto y el puerto); **nunca** las contraseñas de MySQL, que viven solo en el `.env` del proyecto. Ese `.env` lo escribe `preparar_airflow.py` con valores aleatorios solo si no existe, y no imprime ningún valor.

```powershell
# desde la raíz del proyecto
.\.venv\Scripts\python.exe scripts\orquestacion\preparar_airflow.py --verificar  # solo mira: dice qué falta, no escribe nada
.\.venv\Scripts\python.exe scripts\orquestacion\preparar_airflow.py              # genera ..\airflow-medallon con estos archivos y el DAG
.\.venv\Scripts\python.exe scripts\orquestacion\sincronizar_dag.py --verificar   # compara los sha256 del DAG en ambas carpetas
.\.venv\Scripts\python.exe scripts\orquestacion\sincronizar_dag.py --registrar   # anota el sha256 tras editar el DAG
```
