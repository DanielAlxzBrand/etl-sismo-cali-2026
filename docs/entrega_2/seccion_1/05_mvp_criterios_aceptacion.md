# 5. MVP y criterios de aceptación

**Ítem del checklist:** «Establecimos criterios verificables de aceptación para las funcionalidades esenciales del producto mínimo viable (MVP).» · **Fecha de verificación:** 2026-11-11 · Índice: [indice.md](indice.md)

> **Cómo leer las etiquetas.** [Evidencia en el repo: `ruta`] = existe en el repositorio; [Fuente externa: URL y fecha de consulta]; [Hipótesis del equipo, por validar] = juicio nuestro, por validar. Los resultados de la tabla se leyeron de los archivos o salen de comandos ejecutados el 2026-11-11 que no modifican nada; las filas que dependen de una salida guardada lo dicen.

## 1. Definición del MVP (supuesto S3)
El MVP es el pipeline reproducible con Gold, KPI con incertidumbre y su verificación. Esa definición es nuestra y la formalizamos después de construir el pipeline: los criterios se redactaron a partir de pruebas y umbrales que ya existían. [Hipótesis del equipo, por validar] [Evidencia en el repo: `docs/enunciado_flujo.png`; `docs/verificacion_entrega.md`]

| incluye | queda fuera | razón |
|---|---|---|
| Extracción a Bronze con manifiesto y sha256 | Dashboard o interfaz | El enunciado del avance pide Bronze, Silver, Gold y validación; no se pidió interfaz. [Evidencia en el repo: `docs/verificacion_entrega.md`] |
| Silver con reglas trazables a hallazgos y JOIN con huérfanos | API | Sin interfaz que la consuma. |
| Gold con K1 a K6 y sensibilidades | Orquestación (flujos programados) | El pipeline se ejecuta por etapas con `main.py`; no hay ejecución programada. [Evidencia en el repo: `main.py`] |
| Carga a SQLite y CSV | Carga a un motor distinto de SQLite | SQLite permite el recálculo independiente con SQL y no necesita servidor. [Evidencia en el repo: `docs/DECISIONES.md (D10)`] |
| Pruebas, recálculo independiente y documentación | Pruebas con usuarios | No hubo usuarios. |
| Empaquetado sin entorno virtual | Modelos de aprendizaje automático | No se entrenan modelos. |

## 2. Funcionalidades esenciales e historias de usuario
Los roles de las historias son hipotéticos: no hubo usuarios. [Hipótesis del equipo, por validar]

| ID | funcionalidad esencial | historia de usuario (quién, qué, para qué) | capacidad (ruta) |
|---|---|---|---|
| F1 | Extracción reproducible | Como integrante del equipo, quiero extraer y conservar las fuentes sin modificar, para poder demostrar de dónde sale cada cifra. | [Evidencia en el repo: `src/extract/`; `data/bronze/manifest.jsonl`] |
| F2 | Limpieza e integración con trazabilidad | Como analista, quiero limpiar y unir las fuentes con reglas que cite un hallazgo y conservar lo que no cruza, para no perder construcciones ni ocultar problemas. | [Evidencia en el repo: `src/transform/`; `docs/reglas_silver.md`; `data/silver/`] |
| F3 | Gold con KPI e incertidumbre | Como lector de la entidad destino, quiero tasas con intervalo, porcentaje sin datos y límites, para no leer más certeza de la que hay. | [Evidencia en el repo: `src/transform/build_gold.py`; `data/gold/`; `docs/KPIs.md`] |
| F4 | Verificación automática | Como evaluador, quiero pruebas y un recálculo independiente, para confiar en que el pipeline hace lo documentado. | [Evidencia en el repo: `tests/`; `notebooks/04_gold_kpis.ipynb`] |
| F5 | Documentación y reproducibilidad | Como tercero, quiero instrucciones y cifras que coincidan con las salidas, para reproducir el análisis. | [Evidencia en el repo: `README.md`; `docs/`] |
| F6 | Empaquetado sin entorno virtual | Como evaluador, quiero un archivo con solo el código, las dependencias y los datos necesarios, para ejecutarlo sin el entorno del equipo. | [Evidencia en el repo: `scripts/make_dist.py`] |

## 3. Criterios de aceptación
19 de 19 criterios cumplen; los demás, si los hay, aparecen como «no cumple». Un criterio solo se marca «cumple» si el comando o la lectura se hizo el 2026-11-11.

| ID | funcionalidad | criterio verificable | umbral | cómo se verifica | evidencia | resultado actual | estado | fecha de verificación |
|---|---|---|---|---|---|---|---|---|
| AC01 | F1 | Dado el manifiesto de Bronze, cuando se recalcula el sha256 de cada archivo listado, entonces coincide con el manifiesto | 8 de 8 | sha256 de cada ruta del manifiesto; `python -m pytest -q -p no:cacheprovider tests/test_extract.py` | [Evidencia en el repo: `data/bronze/manifest.jsonl`] | 8 de 8 coinciden; test_extract: 6 passed | **cumple** | 2026-11-11 |
| AC02 | F1 | Cuando se suman las filas de las páginas de la API, entonces igualan el conteo oficial de la capa antes y después de la descarga | igualdad | `tests/test_extract.py::test_paginas_suman_el_conteo_oficial` | [Evidencia en el repo: `tests/test_extract.py`] | pasa (incluida en los 6 de test_extract) | **cumple** | 2026-11-11 |
| AC03 | F2 | Cuando se une construcciones con el CSV por código de barrio, entonces la cobertura de llave es al menos el umbral | ≥ 0,80 | `tests/test_quality.py::test_cobertura_join_supera_umbral` | [Evidencia en el repo: `data/silver/quality_report.json`; `config/config.yaml`] | 99,883 %; resultado: pasa | **cumple** | 2026-11-11 |
| AC04 | F2 | Dado `docs/reglas_silver.md`, entonces cada regla cita al menos un hallazgo y todos los hallazgos citados existen en `docs/hallazgos_eda.md` | 18 de 18; 0 inexistentes | Lectura de ambas tablas y cruce de los H# | [Evidencia en el repo: `docs/reglas_silver.md`; `docs/hallazgos_eda.md`] | 18 reglas; 0 sin hallazgo; 0 hallazgos inexistentes | **cumple** | 2026-11-11 |
| AC05 | F2 | Cuando una construcción no tiene pareja en el JOIN, entonces se conserva en el archivo de huérfanos | 6 a la izquierda | Conteo de filas de `silver_orphans_left.csv` y `quality_report.json` | [Evidencia en el repo: `data/silver/silver_orphans_left.csv`; `data/silver/quality_report.json`] | 6 construcciones sin llave conservadas; 295 barrios del CSV sin construcciones | **cumple** | 2026-11-11 |
| AC06 | F2 | Cuando una construcción no tiene datos satelitales, entonces `severo_estricto` es nulo (no falso) y sale del denominador | nulo si y solo si `sin_datos` | Cruce de `severo_estricto` nulo con `sin_datos` en `gold_final.csv` | [Evidencia en el repo: `data/gold/gold_final.csv`; `docs/DECISIONES.md (D7)`] | 435 sin datos y 4.711 con datos suman 5.146 = 5.146; coincidencia exacta: sí | **cumple** | 2026-11-11 |
| AC07 | F3 | Cuando se genera Gold, entonces tiene al menos el mínimo de filas y cero duplicados por `objectid` | ≥ 200 filas; 0 duplicados | `tests/test_quality.py::test_gold_minimo_de_filas_y_sin_duplicados` | [Evidencia en el repo: `data/gold/gold_final.csv`] | 5.146 filas; 0 duplicados | **cumple** | 2026-11-11 |
| AC08 | F3 | Cuando se lee `kpis_gold.csv`, entonces están los seis indicadores K1 a K6 | K1 a K6 | `tests/test_quality.py::test_kpis_presentes_y_en_rango` | [Evidencia en el repo: `data/gold/kpis_gold.csv`] | 23 filas; indicadores K1, K2, K3, K4, K5, K6 | **cumple** | 2026-11-11 |
| AC09 | F3 | Cuando un KPI trae intervalo, entonces 0 ≤ límite inferior ≤ tasa ≤ límite superior ≤ 1 | sin excepciones | Recorrido de `kpis_gold.csv` y `kpis_sensibilidad.csv` (tasas con intervalo) | [Evidencia en el repo: `data/gold/kpis_gold.csv`; `data/gold/kpis_sensibilidad.csv`] | 15 de 15 en kpis_gold; 87 de 87 en sensibilidades; incumplen: 0 | **cumple** | 2026-11-11 |
| AC10 | F3 | Cuando se lee la fecha de corte de cada KPI, entonces es la fecha de edición de la capa configurada y no la de hoy | 2026-09-02 | `tests/test_quality.py::test_kpis_presentes_y_en_rango` | [Evidencia en el repo: `data/gold/kpis_gold.csv`; `config/config.yaml`] | 23 de 23 filas con fecha_corte = 2026-09-02: sí | **cumple** | 2026-11-11 |
| AC11 | F3 | Cuando se carga Gold a SQLite, entonces cada tabla tiene las mismas filas que su CSV | igualdad de filas | Conteo de filas de cada tabla de `etl_sismo.db` (lectura) | [Evidencia en el repo: `data/gold/etl_sismo.db`] | gold_final 5.146; kpis_gold 23; kpis_sensibilidad 107; silver_integrated 5.146 | **cumple** | 2026-11-11 |
| AC12 | F3 | Cuando se recalculan los KPI con SQL independiente, entonces coinciden con `kpis_gold.csv` | diferencia máxima < 1e-9 | Salida guardada del notebook 04 §6 (no se reejecutó hoy: regenera la base) | [Evidencia en el repo: `notebooks/04_gold_kpis.ipynb`] | «todo dentro de 1e-9: True» en la salida guardada: sí | **cumple** | 2026-11-11 |
| AC13 | F4 | Cuando se corren todas las pruebas, entonces pasan, sin saltadas | todas | `python -m pytest -q -p no:cacheprovider` | [Evidencia en el repo: `tests/`] | 50 passed in 1.99s (el README cuenta 45 pruebas de nivel de módulo; las 5 de `tests/test_entrega_seccion_1.py` están en una clase y no entran en ese conteo) | **cumple** | 2026-11-11 |
| AC14 | F4 | Cuando se corren las pruebas, entonces no cambia ningún archivo de Silver ni de Gold | sha256 idénticos | sha256 de los 9 archivos antes y después de `pytest` | [Evidencia en el repo: `data/silver/`; `data/gold/`] | 9 de 9 idénticos a la línea base (prefijos de 8 caracteres) antes y después | **cumple** | 2026-11-11 |
| AC15 | F5 | Cuando se compara el README con las salidas, entonces las cifras coinciden | todas las pruebas del archivo | `python -m pytest -q -p no:cacheprovider tests/test_readme_cifras.py` | [Evidencia en el repo: `README.md`; `tests/test_readme_cifras.py`] | 12 passed | **cumple** | 2026-11-11 |
| AC16 | F5 | Cuando se leen las rutas citadas en el README, entonces todas existen | 0 rotas | `tests/test_readme_cifras.py::test_rutas_citadas_en_readme_existen` | [Evidencia en el repo: `README.md`] | pasa (incluida en el archivo anterior) | **cumple** | 2026-11-11 |
| AC17 | F5 | Cuando se regeneran Silver y Gold, entonces los archivos de salida son idénticos a los de la ejecución anterior | 9 de 9 idénticos | Comparación de sha256 del zip entregado el 16-oct (`dist/`, no versionado) con los archivos regenerados después; copia limpia (`docs/prueba_entorno_limpio.md`). No se reejecutó hoy para no regenerar la base. | [Evidencia en el repo: `docs/prueba_entorno_limpio.md`] | 9 de 9 idénticos; Silver regenerado el 2026-10-16 15:15, zip creado el 2026-10-16 14:56 | **cumple** | 2026-11-11 |
| AC18 | F6 | Cuando se arma el zip, entonces no contiene entorno virtual, cachés, `.env`, `.git/` ni `dist/` | 0 entradas prohibidas | `scripts/make_dist.py` en una carpeta temporal fuera del repo y su verificación posterior | [Evidencia en el repo: `scripts/make_dist.py`] | 0 entradas prohibidas en 101 entradas; `dist/` sin cambios: ['avance2_etl_20261016.zip'] | **cumple** | 2026-11-11 |
| AC19 | F6 | Dado un entorno virtual sin `pyvenv.cfg` (con `bin/python` o `Scripts/python.exe`), cuando se arma el zip, entonces no entra | no entra | `python -m pytest -q -p no:cacheprovider tests/test_dist.py` | [Evidencia en el repo: `tests/test_dist.py`] | 3 passed | **cumple** | 2026-11-11 |

## 4. Criterios que no cumplimos o no aplican
| criterio | estado | motivo |
|---|---|---|
| Dashboard, API, frontend | no aplica | Fuera del MVP (S3); el enunciado del avance no los pide. |
| Orquestación con flujos programados | no aplica | Fuera del MVP; no existe. |
| Carga a PostgreSQL, MySQL o un almacén distinto de SQLite | no aplica | Decisión D10: SQLite. [Evidencia en el repo: `docs/DECISIONES.md`] |
| Pruebas con usuarios | no aplica | No hubo usuarios ni stakeholders contactados. |
| Prueba de instalación en entorno limpio con el código final | no cumple (pendiente) | `docs/prueba_entorno_limpio.md` se ejecutó con 26 pruebas, antes de los cambios posteriores; hay que repetirla. [Evidencia en el repo: `docs/prueba_entorno_limpio.md`; `docs/verificacion_entrega.md`] |
| Zip de `dist/` con el código actual | no cumple (pendiente) | `dist/avance2_etl_20261016.zip` es anterior a los cambios del avance; hay que regenerarlo. [Evidencia en el repo: `docs/verificacion_entrega.md`] |
| Prueba automática de la lectura de archivos Excel | no cumple | No está en `tests/`; está documentada solo como comprobación manual. [Evidencia en el repo: `docs/verificacion_entrega.md`] |
| Meta del Avance 1 de cobertura del 90 % de los puntos verificados (KR1) | no evaluado | No tenemos la fuente por punto. [Evidencia en el repo: `docs/entrega_2/seccion_1/03_objetivo_alcance_okr_kpi.md §2`] |
| Revisión visual de los códigos de barrio sobre el mapa | pendiente | Es un juicio del equipo. [Evidencia en el repo: `docs/revision_codigos_barrio.md`] |
| Reejecución de las etapas el 2026-11-11 | no ejecutada | Regenera Gold y la base; el criterio AC17 se verificó por comparación de sha256. |
