# Scripts (`scripts/`)

Utilidades que generan documentos, empaquetan o comprueban el repositorio. Ninguno modifica `data/`; se ejecutan con el intérprete del `.venv` desde la raíz del repositorio.

| script | qué hace |
|---|---|
| `make_readme.py` | genera `README.md` leyendo los archivos de salida y la documentación (las cifras salen de los archivos, no se escriben a mano) |
| `make_catalogo_fuentes.py` | genera el catálogo de fuentes y metadatos (`docs/bronze/catalogo_fuentes_metadatos.md` y `.json`) desde el manifiesto de Bronze; es determinista |
| `escanear_secretos.py` | busca secretos en el árbol, el historial de git, los notebooks, los logs y un zip; reporta archivo, línea y patrón, nunca el valor |
| `make_dist.py` | empaqueta el proyecto en `dist/etl_sismo_<fecha>.zip` por **lista de inclusión** (ver abajo) y verifica el zip |
| `evidencias/` | produce las evidencias en un clon temporal con saneamiento de rutas y datos del equipo: `evidencias_api.py` (corrida completa), `registrar_manifiesto.py` (sha256 en el manifiesto), `integrar_latencias.py` (latencias en los documentos), `make_diagrama_arquitectura.py` (diagrama) y `saneamiento.py` |

Para comprobar el proyecto: `python -m pytest -q -p no:cacheprovider` y `python scripts/escanear_secretos.py`.

## Qué entra y qué no en el zip (`make_dist.py`)
- **Entra:** `README.md`, `main.py`, `requirements.txt`, `pytest.ini`, `.env.example`, `.gitignore`, `.gitattributes`, `DECLARACION_USO_IA.md` y las carpetas `config/`, `src/`, `scripts/`, `tests/`, `notebooks/`, `docs/`, `data/` (incluida `data/gold/etl_sismo.db`) y `dags/` (solo si existe). De `docs/` solo entran los PDF de `docs/proyecto/referencias/` y `docs/retroalimentacion/`.
- **No entra:** cualquier otro archivo o carpeta de la raíz (notas, borradores), el `.env` real, `logs/`, `dist/`, `.git/`, las notas y la configuración local de herramientas de edición, cachés (`__pycache__`, `.pytest_cache`, `.ipynb_checkpoints`, `*.pyc`) y los entornos virtuales (`.venv*`, `venv/`, `env/` y toda carpeta con `pyvenv.cfg`, `site-packages`, `conda-meta`, `python.exe` o `bin/python`, tengan el nombre que tengan).
- **Verificación:** si el zip tiene entradas prohibidas, un primer nivel fuera de la lista, PDF de `docs/` no permitidos o no trae `requirements.txt`, el script falla con un mensaje claro; si pesa más de 50 MB, avisa.
- **Carpeta nueva del proyecto:** hay que agregarla a `RAIZ_CARPETAS` en `make_dist.py` y a las pruebas de `tests/test_dist.py` (decisión D38).
