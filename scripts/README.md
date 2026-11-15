# Scripts (`scripts/`)

Utilidades que generan documentos, empaquetan o comprueban el repositorio. Ninguno modifica `data/`; se ejecutan con el intérprete del `.venv` desde la raíz del repositorio.

| script | qué hace |
|---|---|
| `make_readme.py` | genera `README.md` leyendo los archivos de salida y la documentación (las cifras salen de los archivos, no se escriben a mano) |
| `make_catalogo_fuentes.py` | genera el catálogo de fuentes y metadatos (`docs/bronze/catalogo_fuentes_metadatos.md` y `.json`) desde el manifiesto de Bronze; es determinista |
| `escanear_secretos.py` | busca secretos en el árbol, el historial de git, los notebooks, los logs y un zip; reporta archivo, línea y patrón, nunca el valor |
| `cargar_mysql.py` | carga relacional por lotes con historial a MySQL (o a un SQLite fuera de `data/` para pruebas); idempotente y de una sola transacción |
| `make_modelo_datos.py` | genera `docs/almacenamiento/modelo_datos.md` y el diagrama entidad-relación desde el esquema SQL; con `--verificar` comprueba que no estén desactualizados |
| `mysql/configurar_mysql.py` | lo ejecuta el equipo: crea las bases y el usuario del proyecto con privilegios mínimos (y, con `--usuario-docker --origen`, el usuario para el contenedor de Airflow) y guarda la contraseña generada solo en `.env` (pide la del administrador sin mostrarla) |
| `mysql/verificar_mysql.py` | batería en vivo sobre la base de prueba: esquema desde cero, conciliación, idempotencia, equivalencia con SQLite, reversión e integridad |
| `mysql/benchmark_lotes.py` | mide fila a fila frente a lotes de 500, 1000 y 2000 y propone el tamaño de lote |
| `mysql/respaldar_restaurar.py` | respaldo lógico en CSV con manifiesto sha256, restauración en la base de prueba y conciliación |
| `make_matriz_casos.py` | genera la matriz de casos de prueba (`docs/validacion/matriz_casos_prueba.md` y `.csv`) desde una definición única; con `--verificar` comprueba que esté al día |
| `informe_pruebas.py` | ejecuta pytest con `coverage` y escribe `docs/validacion/informe_pruebas.md` y `.csv` (resultado esperado, obtenido, duración, métricas del análisis y cobertura por módulo) |
| `validacion/verificar_regresiones.py` | reintroduce cada defecto corregido en una copia temporal y comprueba que su prueba de regresión falla sin la corrección |
| `orquestacion/sincronizar_dag.py` | copia `dags/medallon_etl_dag.py` a `airflow-medallon/dags`, compara los sha256 de ambos (`--verificar`) y registra el hash (`--registrar`) |
| `panel/ejecutar_panel.py` | lanzador del panel: arranca la API y Streamlit en 127.0.0.1 (puertos libres si hace falta), espera su salud y los cierra a los dos; `--almacenamiento sqlite` o `mysql`, `--verificar` y `--duracion` |
| `panel/contraste.py` | calcula la relación de contraste WCAG de la paleta del panel (`--evidencia` guarda EV-057) |
| `panel/generar_trazabilidad.py` | genera `docs/panel/trazabilidad_ui.md` desde el registro de componentes; con `--verificar` comprueba que esté al día |
| `panel/make_arquitectura_panel.py` | dibuja `docs/panel/img/arquitectura_panel.png` con matplotlib |
| `contar_estados_checklist.py` | cuenta los 30 ítems del checklist por estado desde su tabla y escribe (`--escribir`) o comprueba (`--verificar`) la línea de conteo de `docs/checklist/estado_checklist.md`; el conteo nunca se escribe a mano (D96) |
| `validar_checklist.py` | comprueba la trazabilidad de un ítem del checklist (`--item 4.2`: archivos, pruebas, evidencias con su sha256 y comando; `--ejecutar` corre solo sus pruebas), de todos (`--todos`) o regenera `docs/checklist/trazabilidad.md` (`--escribir`); la fuente es `docs/checklist/trazabilidad.csv` (D98) |
| `make_dist.py` | empaqueta el proyecto en `dist/etl_sismo_<fecha>.zip` por **lista de inclusión** (ver abajo) y verifica el zip |
| `evidencias/` | produce las evidencias en un clon temporal con saneamiento de rutas y datos del equipo: `evidencia.py` (guardado saneado de las salidas), `evidencia_estabilidad.py` (reproducibilidad del pipeline antes de orquestarlo), `evidencia_conector.py` (instalación del conector MySQL), `evidencias_api.py` (corrida completa), `registrar_manifiesto.py` (sha256 en el manifiesto), `integrar_latencias.py` (latencias en los documentos), `make_diagrama_arquitectura.py` (diagrama), `saneamiento.py` y los cuatro scripts de verificación en vivo: `evidencia_airflow_desde_zip.py` (Airflow como lo levantaría quien recibe el zip), `evidencia_phpmyadmin.py` (phpMyAdmin con la cuenta de solo lectura), `medir_memoria_suite.py` (pico de memoria de la suite) y `evidencia_independencia.py` (el proyecto en una carpeta sin hermanas); necesitan Docker, MySQL o minutos de instalación y la suite no los ejecuta: `tests/test_scripts_de_evidencia.py` solo comprueba su forma |

Para comprobar el proyecto: `python -m pytest -q -p no:cacheprovider` y `python scripts/escanear_secretos.py`.

## Qué entra y qué no en el zip (`make_dist.py`)
- **Entra:** `README.md`, `main.py`, `requirements.txt`, `pytest.ini`, `.env.example`, `.gitignore`, `.gitattributes`, el documento aislado de la raíz (un `.md` con nombre en mayúsculas, que nada enlaza ni cita) y las carpetas `config/`, `src/`, `scripts/`, `tests/`, `notebooks/`, `docs/`, `data/` (incluida `data/gold/etl_sismo.db`), `dags/` y `orquestacion/` (solo si existen). De `docs/` solo entran los PDF de `docs/proyecto/referencias/` y `docs/retroalimentacion/`.
- **No entra:** cualquier otro archivo o carpeta de la raíz (notas, borradores), el `.env` real, `logs/`, `dist/`, `.git/`, las carpetas ocultas, cachés (`__pycache__`, `.pytest_cache`, `.ipynb_checkpoints`, `*.pyc`) y los entornos virtuales (`.venv*`, `venv/`, `env/` y toda carpeta con `pyvenv.cfg`, `site-packages`, `conda-meta`, `python.exe` o `bin/python`, tengan el nombre que tengan).
- **Verificación:** si el zip tiene entradas prohibidas, un primer nivel fuera de la lista, PDF de `docs/` no permitidos o no trae `requirements.txt`, el script falla con un mensaje claro; si pesa más de 50 MB, avisa.
- **Carpeta nueva del proyecto:** hay que agregarla a `RAIZ_CARPETAS` en `make_dist.py` y a las pruebas de `tests/test_dist.py` (decisión D38).
