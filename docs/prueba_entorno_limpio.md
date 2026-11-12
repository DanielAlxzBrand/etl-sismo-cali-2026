# Prueba en entorno limpio

**Objetivo:** comprobar que un tercero puede instalar y ejecutar el pipeline desde una copia limpia del repositorio, sin `.env`, sin el venv del equipo y reutilizando Bronze (sin red para extraer).

**Equipo:** Windows 11, PowerShell, Python 3.13.0. **Copia:** `%TEMP%\avance2_limpio` (fuera del repositorio), creada con `robocopy` excluyendo `.venv*`, `dist`, `__pycache__`, `.ipynb_checkpoints`, `.pytest_cache` y `.env` (80 archivos; `.env` presente en la copia: False).

## Comandos
```powershell
robocopy <repo> $env:TEMP\avance2_limpio /E /XD .venv .venv_test dist __pycache__ .ipynb_checkpoints .pytest_cache /XF .env
cd $env:TEMP\avance2_limpio
py -3 -m venv .venv_test
.\.venv_test\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
python main.py --stage all
Get-FileHash -Algorithm SHA256 data\silver\*.csv, data\silver\quality_report.json, data\gold\*.csv
```

## Salida (resumen)
- `pip install -r requirements.txt`: terminó sin error.
- `pytest -q`: `26 passed in 5.35s` (0 fallos, 0 errores, sin pruebas saltadas).
- `python main.py --stage all`: código de salida 0. `extract` reportó "ya existe, sha256 coincide" para las tres fuentes (reutiliza Bronze con manifiesto + sha256; no necesita red); `transform`: construcciones=5146, barrios=346, cobertura de llave 99,8834 % (pasa), huérfanos izquierda 6 y derecha 295, llave_confianza alta; `gold`: 5146 filas, 6 indicadores, 107 filas de sensibilidades; `load`: 4 tablas en SQLite.

## sha256 en la copia limpia (primeros 16 caracteres) — idénticos a los del repositorio de trabajo
| archivo | sha256 |
|---|---|
| silver_construcciones.csv | 85EA33EBE99C9FB6 |
| silver_estrato_barrio.csv | 0815BE18476695F1 |
| silver_integrated.csv | BC1D1C6BD4BB3F62 |
| silver_orphans_left.csv | 04BC074BF0332EAE |
| silver_orphans_right.csv | DA95C33F59F5112A |
| quality_report.json | FA66F7F26FF6B6DA |
| gold_final.csv | 496AB49EB76ADA32 |
| kpis_gold.csv | 6DB3DBEEEFFBBF5C |
| kpis_sensibilidad.csv | 0CF75F2D2FABCB56 |

**Alcance de la prueba:** no probó la descarga desde las fuentes (`--stage extract --refresh`), que necesita red y depende del servicio ArcGIS de un tercero.
