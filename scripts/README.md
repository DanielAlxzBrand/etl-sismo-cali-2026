# Scripts (`scripts/`)

Utilidades que generan documentos, empaquetan o comprueban el repositorio. Ninguno modifica `data/`; se ejecutan con el intérprete del `.venv` desde la raíz del repositorio.

| script | qué hace |
|---|---|
| `make_readme.py` | genera `README.md` leyendo los archivos de salida y la documentación (las cifras salen de los archivos, no se escriben a mano) |
| `make_catalogo_fuentes.py` | genera el catálogo de fuentes y metadatos (`docs/bronze/catalogo_fuentes_metadatos.md` y `.json`) desde el manifiesto de Bronze; es determinista |
| `escanear_secretos.py` | busca secretos en el árbol, el historial de git, los notebooks, los logs y un zip; reporta archivo, línea y patrón, nunca el valor |
| `make_dist.py` | empaqueta el proyecto en `dist/` sin entornos virtuales, cachés ni `.env`, y verifica el zip |
| `evidencias/` | produce las evidencias en un clon temporal con saneamiento de rutas y datos del equipo: `evidencias_api.py` (corrida completa), `registrar_manifiesto.py` (sha256 en el manifiesto), `integrar_latencias.py` (latencias en los documentos), `make_diagrama_arquitectura.py` (diagrama) y `saneamiento.py` |

Para comprobar el proyecto: `python -m pytest -q -p no:cacheprovider` y `python scripts/escanear_secretos.py`.
