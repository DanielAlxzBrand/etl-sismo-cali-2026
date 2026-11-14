# Carpeta `orquestacion/`

> **Procedimiento basado en la guía de Airflow de la asignatura (artículo de Juan Manuel Núñez Velasco).**

Archivos que se copian a la carpeta hermana `airflow-medallon` (junto al proyecto) para construir la imagen de Airflow. La documentación completa está en [docs/orquestacion/](../docs/orquestacion/README.md).

| Archivo | Para qué sirve | Paso de la guía |
|---|---|---|
| `Dockerfile` | imagen sobre `apache/airflow:3.3.2` con las dependencias del pipeline | 17 |
| `requirements-airflow.txt` | dependencias con las mismas versiones que el `.venv` (pandas 3.0.6 para reproducir la línea base) | 16 (ausente en la guía) |
| `dag.sha256` | sha256 del DAG versionado (`dags/medallon_etl_dag.py`); una prueba lo exige | — |

En `airflow-medallon/.env` solo van variables de Airflow (`AIRFLOW_UID` y, si el compose lo exige, la contraseña de la interfaz); **nunca** las contraseñas de MySQL, que viven solo en el `.env` del proyecto. El compose completo no se redistribuye: se guarda aquí el diff frente al descargado de la documentación oficial (`docker-compose.diff`) cuando se ejecuta el paso 19.

```powershell
# desde la raíz del proyecto
.\.venv\Scripts\python.exe scripts\orquestacion\sincronizar_dag.py             # copia el DAG a ..\airflow-medallon\dags
.\.venv\Scripts\python.exe scripts\orquestacion\sincronizar_dag.py --verificar # compara los sha256 de ambos
.\.venv\Scripts\python.exe scripts\orquestacion\sincronizar_dag.py --registrar # anota el sha256 tras editar el DAG
```
