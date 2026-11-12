# Registro de cambios de la retroalimentación del avance 2

**Fecha:** 2026-11-11 · **Texto recibido:** [retroalimentacion_avance_2.txt](retroalimentacion_avance_2.txt) · **Regla:** ningún dato, KPI, umbral, regla de Silver ni columna cambió; solo documentación, textos de notebooks, `scripts/make_dist.py`, `.gitignore` y pruebas nuevas.

## Cambios por observación

| # | observación del profesor | qué hicimos | archivos modificados | evidencia | fecha |
|---|---|---|---|---|---|
| 1 | «profundizar la revisión de los códigos de barrio que presentan diferencias en la validación semántica» | Fichas de los 7 códigos «NO coincide», del 1920 y de las 2 construcciones sin comuna ni barrio, con nombres normalizados, similitud recalculada, polígonos donde caen los centroides, barrios parecidos del CSV y categoría numérica (a)-(d); la revisión visual queda «pendiente». Enlace en el README y decisión registrada. Sin columna nueva (habría cambiado los sha256 de Silver y Gold). | `docs/revision_codigos_barrio.md` (nuevo), `scripts/make_readme.py` (→ `README.md`), `docs/DECISIONES.md` | Resumen de la revisión: (a) 4 códigos, 244 construcciones; (b) 2 códigos, 73; (c) 1 código, 16; (d) 6 sin pareja. Total de las 333 = 244 + 73 + 16. `pytest`: `test_revision_de_codigos_cubre_los_casos_pedidos` pasa. sha256 de `data/silver` y `data/gold` idénticos. | 2026-11-11 |
| 2 | «mantener explícita la diferencia temporal entre los datos de estratificación de 2015 y la información de edificaciones de 2026» | Recuadro «Alcance temporal» (fechas leídas de `config/config.yaml`) en el README y en `docs/KPIs.md`; recordatorio de una línea en la sección de resultados del README y en `docs/comprension_proyecto1.md`; aviso en la prosa de apertura de las celdas 0 y última del notebook 04 y de la celda de alcance del notebook 05. | `scripts/make_readme.py`, `README.md`, `docs/KPIs.md`, `docs/comprension_proyecto1.md`, `notebooks/04_gold_kpis.ipynb`, `notebooks/05_validacion_evidencias.ipynb` | `pytest`: `test_encabezados_de_alcance_en_readme_y_kpis` y `test_recuadro_temporal_usa_las_fechas_de_config` pasan. | 2026-11-11 |
| 3 | «continuar diferenciando los indicadores derivados de imágenes satelitales de las evaluaciones estructurales» | Tabla «Indicador satelital frente a evaluación estructural» (README y `docs/KPIs.md`) con las cifras reportadas por la prensa (3.403 predios; 1.078 rojo, 1.272 amarillo, 1.053 verde) y la aclaración de unidad y de fuente; vocabulario «construcciones con cambio satelital severo (severo estricto, proxy de daño)» y después «severo estricto»; dos entradas nuevas en el glosario. No se renombró ninguna columna. | `scripts/make_readme.py`, `README.md`, `docs/KPIs.md`, `docs/comprension_proyecto1.md`, `docs/DECISIONES.md`, `docs/hallazgos_eda.md`, `docs/verificacion_entrega.md`, notebooks 04 y 05 | `pytest`: `test_tabla_satelital_frente_a_estructural_con_cifras_reportadas` pasa. Búsqueda de «daño severo», «edificios dañados» y «daño estructural»: solo quedan citas literales y descripciones del Proyecto 1 (las cifras de la Alcaldía en el Avance 1, el título, el objetivo y la variable del Proyecto 1, y los nombres de la capa y de las columnas). | 2026-11-11 |
| 4 | «delimitar claramente la población analizada para evitar generalizaciones sobre la totalidad de edificaciones de Cali» | Recuadro «Población analizada» con cifras leídas de `gold_final.csv` y `quality_report.json` (5.146 construcciones, 4.711 con datos, 7 comunas, 52 códigos de barrio), en el README, en `docs/KPIs.md` (integra la antigua «advertencia obligatoria») y en la prosa de los notebooks. Revisión de las frases que generalizaban (lista abajo). | `scripts/make_readme.py`, `README.md`, `docs/KPIs.md`, `docs/hallazgos_eda.md`, `docs/DECISIONES.md`, notebooks 04 y 05 | `pytest`: `test_recuadro_de_poblacion_coincide_con_gold` pasa (compara el README y `docs/KPIs.md` con `gold_final.csv`). | 2026-11-11 |
| 5 | «excluir el entorno virtual del archivo comprimido» | `scripts/make_dist.py` descarta cualquier carpeta con `pyvenv.cfg`, además de `.venv*`, `venv`, `env` y `site-packages`, y recorre el árbol sin entrar a esas carpetas. La verificación del zip falla ante `pyvenv.cfg`, `site-packages`, `.venv`, `venv/`, `env/`, `Scripts/`, cachés, `.env`, `.git/`, `dist/` y registros `.log`. `.gitignore` incorpora `.pytest_cache/`. No se generó ningún zip nuevo. | `scripts/make_dist.py`, `.gitignore`, `tests/test_empaquetado_y_revision.py` (nuevo) | Prueba en una carpeta temporal fuera del repo con entornos llamados `.venv_test`, `venv`, `env`, `mi_entorno` y `otro/entorno_x`: ninguno entra al zip. Simulacro sobre el repo real: 90 archivos, 0 prohibidos, `.venv/` fuera. `pytest`: 3 pruebas nuevas de empaquetado pasan. | 2026-11-11 |

## Traslados de archivos

Cada traslado se hizo copiando, comparando el sha256 de origen y destino y solo después eliminando el original del repo. Las rutas con `<padre>` están fuera del repositorio.

| origen | destino | sha256 | nota |
|---|---|---|---|
| `Retroalimentacion.txt` | `<padre>/guia_equipo/seguimiento/originales/Retroalimentacion_avance_2.txt` | `22a726e5dfb10b72a661dc17170425da9375fb33da271462b86d0eae40162feb` | copia verificada por sha256 |
| `_Checklist-Proyecto_DataThinking.docx` | `<padre>/guia_equipo/seguimiento/originales/Checklist_Proyecto_DataThinking_plantilla.docx` | `57551e6bdd1930e4748c32ff089fd62e8c396ed6fdc15c6f4f04527cffa63465` | copia verificada por sha256 |
| `Retroalimentacion.txt` | `docs/avance_2/retroalimentacion_avance_2.txt` | `22a726e5dfb10b72a661dc17170425da9375fb33da271462b86d0eae40162feb` | copia verificada por sha256 |
| `<padre>/reparticion.pdf` | `<padre>/guia_equipo/seguimiento/originales/reparticion.pdf` | `6a32deefaae4bc9f737bf6f904a995024c832513ecb93bcead50e9c9aa02b172` | el original ya no estaba en la raiz del repo; se copio desde <padre>/ (no se elimina nada del padre) |
| `<padre>/guia_equipo/pdf/Guia_ETL_Equipo.pdf` | `<padre>/guia_equipo/guias_estudio/Guia_ETL_Equipo.pdf` | `e9a241172a0fdf9b2a55c81c64aa8535b9f03d71cbc8f842ae90c9d7d796fb35` | el PDF ya no estaba en el repo; se copio desde <padre>/guia_equipo/pdf/ (original intacto) |
| `docs/guia_uso_guion_gold_6min.pdf` | `<padre>/guia_equipo/guias_estudio/guia_uso_guion_gold_6min.pdf` | `550fdf4d7b8c9d5e4bbf765f460a7f6e85b573087267615b823e457c6d68541c` | copia verificada por sha256 |
| `docs/guia_uso_guion_gold_6min_v2.pdf` | `<padre>/guia_equipo/guias_estudio/guia_uso_guion_gold_6min_v2.pdf` | `839eea37038d6d94dc27656b252593c843f3abe598a49f45b30be226e8e088ff` | copia verificada por sha256 |
| `docs/guia_uso_guion_gold_10min_v3.pdf` | `<padre>/guia_equipo/guias_estudio/guia_uso_guion_gold_10min_v3.pdf` | `bfededb351f96edcf7caa3e3419b243a7dcd36963408c9514f94cf875fd205dd` | copia verificada por sha256 |
| `Avance 1 Proyecto ETL 2026 (1).pdf` | `docs/referencias/avance_1_contexto_y_problema.pdf` | `2adf74e511134f58f3115c3e0046a9a2f5777460a3a7e737d4c2f4ed6ff44592` | traslado dentro del repo |

Eliminados del repo tras verificar los sha256: `Retroalimentacion.txt` (raíz del repo); `_Checklist-Proyecto_DataThinking.docx` (raíz del repo); `Avance 1 Proyecto ETL 2026 (1).pdf` (raíz del repo, trasladado a `docs/referencias/`); las tres guías de uso del guion de Gold (PDF) de la carpeta docs.

Además, fuera del repo y sin tocar los originales: `<padre>/guia_equipo/entregas/entrega_1/` guarda el zip de la entrega anterior (`avance2_etl_20261016.zip`, con su `sha256.txt` y `diferencias_zip_vs_repo.txt`) y el documento de la primera entrega; `<padre>/guia_equipo/seguimiento/originales/` guarda las copias de solo lectura de la retroalimentación y del checklist (con `sha256.txt`). El checklist rellenado se generará después en `docs/entrega_3/`.

## Frases que generalizaban sobre Cali (antes → después)

| dónde | antes | después |
|---|---|---|
| README, introducción | «estudiar el daño estructural de Cali tras el sismo» | «estudiar, con un indicador satelital, el cambio visible en las construcciones de 7 comunas de Cali tras el sismo» |
| README (pregunta de negocio) | «En las construcciones de Cali evaluadas por satélite tras el sismo, ¿la proporción con daño severo cambia…» | «En las construcciones evaluadas por satélite en 7 comunas de Cali tras el sismo, ¿la proporción con cambio satelital severo (severo estricto, proxy de daño) cambia…» |
| `docs/comprension_proyecto1.md` (pregunta refinada) | «En las edificaciones de Cali evaluadas por satélite tras el sismo, ¿la proporción con daño severo cambia…» | «En las construcciones evaluadas por satélite en 7 comunas de Cali tras el sismo, ¿la proporción con cambio satelital severo (severo estricto, proxy de daño) cambia…» |
| `docs/KPIs.md` y README (limitaciones), notebook 05 | «Las tasas no son prevalencias de Cali.» | «Las tasas describen esta muestra; no se extrapolan a las construcciones de Cali ni a la ciudad.» |
| notebook 04, lista de limitaciones | «no es prevalencia de Cali.» | «las tasas no se extrapolan a las construcciones de Cali.» |
| notebook 05, composición de estratos | «no está repartido por toda la ciudad» | «no está repartido por todas las comunas de la muestra» |
| `docs/hallazgos_eda.md`, H15 | «(no es prevalencia de Cali)» y «15 comunas sin ninguna edificación» | «las tasas no se extrapolan a las construcciones de Cali» y «15 comunas sin ninguna construcción» |
| `docs/DECISIONES.md`, plan elegido | «Plan elegido: A (edificaciones de Cali + estrato por barrio)» | «(construcciones de la capa satelital, en 7 comunas de Cali, + estrato por barrio)» |
| `docs/DECISIONES.md`, D1 | «Escala principal edificio→barrio en Cali» | «Escala principal construcción→barrio en la capa satelital» |
| README, decisiones de las fuentes | «el plan elegido es el de las construcciones de Cali» | «el plan elegido es el de las construcciones de la capa satelital, en 7 comunas de Cali» |
| README y `docs/KPIs.md`, K3 y K1 | «daño severo», «edificios de varios pisos» | «cambio satelital severo (severo estricto, proxy de daño)», «construcciones de varios pisos» |

Se conservaron sin cambio los nombres propios, las URL, los títulos de las fuentes («Impacto Satelital en Edificaciones por Terremoto. Cali 2026»), las citas de la Alcaldía y los enunciados del Proyecto 1.

## Alternativas aplicadas y observaciones

- El paso de crear el repositorio git estaba pendiente al cerrar esta etapa (el directorio no era un repositorio); se ejecuta en el ajuste E de los ajustes menores posteriores (última sección).
- La solicitud hablaba de cinco mejoras y numeraba cuatro; la quinta (excluir el entorno virtual del zip) está en la retroalimentación y es la de la fila 5.
- `Guia_ETL_Equipo.pdf` y `reparticion.pdf` ya no estaban en la raíz del repo al empezar. Se copiaron desde la carpeta padre (`reparticion.pdf`) y desde `<padre>/guia_equipo/pdf/` (la guía), sin eliminar esos originales.
- El zip anterior (87 entradas) coincide con el repo en 86 archivos; solo `data/gold/etl_sismo.db` difiere (la base se regeneró después del empaquetado). Contiene la base de datos y 4 entradas de `data/gold`.
- Al reejecutar los notebooks 04 y 05 las salidas numéricas son idénticas. Cambian solo: los tiempos de duración del registro; las frases de vocabulario corregidas (limitaciones y respuesta a la pregunta de negocio); el total de pruebas (32 → 40); y la última celda del notebook 05, que lee el registro del día y ahora muestra el de 2026-11-11 (11 líneas, 0 errores) en lugar del de 2026-10-16.
- La ruta histórica `tests/test_quality.p` de `docs/DECISIONES.md` (línea 50) es una cita literal de un error ya corregido; no es un enlace.
- La clasificación de los códigos de barrio usa solo evidencia numérica; la revisión visual en el mapa y los campos pendientes de la declaración de uso siguen en manos del equipo.

## Verificación

| comprobación | comando | resultado |
|---|---|---|
| sha256 de Silver, Gold y `quality_report.json` | suma sha256 de `data/silver/*.csv`, `quality_report.json` y `data/gold/*.csv` antes y después | idénticos |
| manifiesto de Bronze | sha256 de cada archivo listado en `data/bronze/manifest.jsonl` | 8 líneas, 8 coinciden |
| pruebas | `python -m pytest -q -p no:cacheprovider` | 40 passed (32 originales + 8 nuevas) |
| notebooks | `jupyter nbconvert --to notebook --execute --inplace` sobre 04 y 05 | sin errores; diferencias solo las descritas arriba |
| términos prohibidos | búsqueda en el repo (sin `.venv*`, `data/bronze`, binarios) | solo la lista de cadenas prohibidas de `tests/test_readme_cifras.py` |
| rutas citadas | comprobación de existencia de cada ruta citada en README y `docs/` | sin rutas rotas (salvo la cita histórica anterior) |

## Ajustes menores posteriores (2026-11-11)

| ajuste | qué hicimos | evidencia |
|---|---|---|
| A. Redondeo | `scripts/make_readme.py` formatea todas las cifras con una sola función (`redondear`, half-up sobre el valor decimal escrito). Única cifra del README que cambió: cobertura de estrato válido, de «99,844 %» a «99,845 %» (línea 121; la 208 ya decía 99,845 %). «99,844» no aparece en `docs/`, en los notebooks ni en las pruebas. | `tests/test_readme_cifras.py`: todas las apariciones coinciden entre sí y con `quality_report.json` redondeado a 3 decimales |
| B. Lectura de las 333 | Párrafo nuevo en la sección de validación de la llave del README, con cifras leídas de `silver_integrated.csv` y de `docs/revision_codigos_barrio.md`: 244 (73,3 %), 73 (21,9 %) y 16 (4,8 %); 98,27 % si se aceptaran las de la primera categoría; se conserva 93,52 %. | prueba: a + b + c = construcciones sin nombre validado de Silver (333) |
| C. Vocabulario | `docs/comprension_proyecto1.md` distingue el objetivo y la variable del Proyecto 1 (evaluación estructural) del proxy satelital. | revisión de texto |
| D. Empaquetado | `scripts/make_dist.py` descarta también carpetas con `site-packages`, `conda-meta`, `python.exe`, `Scripts/python*` o `bin/python*` aunque no tengan `pyvenv.cfg`, y su verificación del zip falla ante esas cadenas. La primera versión de la detección siempre daba verdadero; la prueba lo detectó y se corrigió. | `tests/test_dist.py` (3 pruebas); zip de prueba en carpeta temporal: 0 entornos simulados dentro |
| E. Repositorio git | `git init` en la raíz, revisión de los archivos antes de confirmar, commit «Estado inicial de la segunda entrega» y etiqueta `base-segunda-entrega`. | `git log -1` y `git tag` |

Los sha256 de `data/silver`, `data/gold` y `quality_report.json` no cambiaron. Pruebas: 45 passed.
