# Código del proyecto (`src/`)

El código está organizado por capas del ETL medallion y por la capa de servicio. Cada paquete importa solo hacia abajo (el panel solo importa `logger` y su propio paquete y habla con la API por HTTP): `extract` escribe Bronze, `transform` lee Bronze y escribe Silver y Gold, `load` copia Silver y Gold a la base, y `api` lee la base sin escribir nada.

| módulo | qué hace | capa |
|---|---|---|
| `common.py` | rutas, lectura de `config/config.yaml`, sha256 y manifiesto de Bronze | transversal |
| `logger.py` | registro de ejecución en consola y en `logs/`, con enmascarado de secretos | transversal |
| `extract/extract_api.py` | descarga paginada de la capa ArcGIS y de los polígonos de barrios (WFS) | Bronze |
| `extract/extract_excel.py` | descarga y lectura del archivo tabular (CSV o Excel) | Bronze |
| `transform/clean_api.py` | limpieza de las construcciones (tipos, bandera de duplicados, llave, clase de daño) | Silver |
| `transform/clean_excel.py` | limpieza del CSV de estrato por barrio | Silver |
| `transform/keys.py` | construcción de la llave del JOIN y normalización de nombres | Silver |
| `transform/integrate.py` | JOIN, huérfanos, validación de la llave, reporte de calidad y documentos generados de Silver | Silver |
| `transform/build_gold.py` | Gold: KPI, intervalos de Wilson y Newcombe, sensibilidades | Gold |
| `load/load_database.py` | carga de Silver y Gold a `data/gold/etl_sismo.db` (SQLite) | almacenamiento |
| `load/esquema.py` y `load/sql/` | esquema relacional en dos archivos (MySQL y SQLite), lectura, aplicación y análisis para el diccionario de datos | almacenamiento |
| `load/relacional.py` | carga por lotes con historial: conversión estricta, clave de corrida determinista, una transacción por carga | almacenamiento |
| `load/conexion.py` | conexiones a MySQL (la contraseña solo viene de `.env`) y a SQLite con claves foráneas | almacenamiento |
| `load/conciliacion.py` | conciliación de una corrida contra los archivos de origen (conteos, huellas y cada valor), integridad referencial y equivalencia de endpoints | almacenamiento |
| `api/` | API de solo lectura: `app.py` (rutas), `esquemas.py` (respuestas), `repositorio.py` (acceso a datos en solo lectura, con `RepositorioSqlite` y `RepositorioRelacional`) y `errores.py` (errores uniformes) | servicio |
| `panel/` | panel de solo lectura (Streamlit): `app.py` (navegación), `registro.py` (páginas y componentes), `cliente_api.py` (único acceso a datos, solo GET), `formato.py`, `redaccion.py`, `componentes.py`, `tema.py`, `configuracion.py` y `paginas/` (una por página) | interfaz |

La orquestación con Airflow vive fuera de `src/`: `dags/medallon_etl_dag.py` importa `src` solo dentro de sus tareas y desde una copia de trabajo, y el repositorio nunca se escribe (ver `docs/orquestacion/`). La carga relacional (`load/relacional.py`) es independiente de las etapas del pipeline: se ejecuta con `scripts/cargar_mysql.py`. El componente en construcción (el panel) se agregará como paquetes nuevos sin cambiar los existentes; la capa de servicio separa el contrato de los endpoints del almacenamiento mediante la interfaz `RepositorioGold` y elige el almacén con `api.almacenamiento` de `config/config.yaml`.
