# 5. MVP y criterios de aceptación

**Ítem del checklist (1.5):** «Establecimos criterios verificables de aceptación para las funcionalidades esenciales del producto mínimo viable (MVP).» · **Fecha de verificación:** 2026-11-12 · Índice: [indice.md](indice.md)

> **Etiquetas de evidencia.** [Evidencia en el repo: `ruta`] = existe en el repositorio; [Fuente externa: URL y fecha de consulta]; [Criterio aplicado: descripción] = regla o decisión nuestra, explicada; [Hipótesis de diseño: criterio y experimento de validación propuesto, no ejecutado] = hipótesis de diseño con su experimento, sin ejecutar. Las cifras se leen de `data/silver`, `data/gold` y `config/config.yaml`.

> **Cómo se formalizaron.** Los criterios de pipeline y calidad se formalizan sobre pruebas y umbrales que ya existían (`config/config.yaml`, `tests/`). Los de API, MySQL, Airflow y dashboard son criterios de diseño de la Entrega 3: aún no se pueden ejecutar y figuran como «no verificado aún» con su fase de verificación; todos se cierran en F8.

## 1. Definición del MVP de la Entrega 3
El MVP es el conjunto mínimo que permite repetir y consultar el análisis de punta a punta: **pipeline reproducible, Gold con KPI e incertidumbre, API de solo lectura, almacenamiento relacional con historial, un DAG de orquestación, un dashboard sobre la API y verificación automática.** [Criterio aplicado: definición del equipo; sustituye la anterior, que excluía API, dashboard y orquestación] [Evidencia en el repo: `docs/entrega_3/decisiones_tecnicas.md`]

Quedan **fuera** del MVP: pruebas con usuarios reales (hecho externo, F6), modelos de aprendizaje automático (el proyecto no entrena modelos), Power BI como evidencia y cualquier despliegue en la nube.

## 2. Funcionalidades esenciales (FE1 a FE8) e historias de usuario
Los roles de las historias son un diseño nuestro: no hubo usuarios. [Hipótesis de diseño: criterio y experimento de validación propuesto, no ejecutado] Experimento: las sesiones de F6.

| ID | funcionalidad esencial | historia de usuario (quién, qué, para qué) | capacidad |
|---|---|---|---|
| FE1 | Extracción y Bronze inmutable | Como integrante del equipo, quiero extraer y conservar las fuentes sin modificar, para demostrar de dónde sale cada cifra. | [Evidencia en el repo: `src/extract/`; `data/bronze/manifest.jsonl`] |
| FE2 | Limpieza, integración y calidad (Silver) | Como analista, quiero limpiar y unir las fuentes con reglas que citen un hallazgo y conservar lo que no cruza, para no perder construcciones ni ocultar problemas. | [Evidencia en el repo: `src/transform/`; `docs/reglas_silver.md`; `data/silver/`] |
| FE3 | Gold con KPI e incertidumbre | Como lector del usuario objetivo institucional, quiero tasas con intervalo, porcentaje sin datos y límites, para no leer más certeza de la que hay. | [Evidencia en el repo: `src/transform/build_gold.py`; `data/gold/`; `docs/KPIs.md`] |
| FE4 | API de solo lectura (F2) | Como desarrollador del dashboard, quiero consultar Gold por endpoints, para no leer la base directamente ni poder modificarla. | en construcción |
| FE5 | Almacenamiento relacional con historial (F3) | Como analista, quiero los resultados en MySQL con claves e historial de cargas, para consultarlos con SQL y auditar cada carga. | en construcción |
| FE6 | Orquestación programada (F4) | Como integrante del equipo, quiero un DAG de Airflow con dependencias y reintentos, para repetir el pipeline sin duplicar resultados. | en construcción |
| FE7 | Dashboard sobre la API (F5) | Como usuario objetivo institucional, quiero ver K1 a K6 con sus límites, para decidir dónde mirar primero. | en construcción |
| FE8 | Verificación, reproducibilidad y empaquetado | Como evaluador, quiero pruebas automáticas, ejecución en un clon limpio y un zip sin entorno virtual, para reproducir el análisis. | [Evidencia en el repo: `tests/`; `scripts/make_dist.py`; `docs/entrega_3/evidencias/`] |

## 3. Criterios de aceptación
21 de 29 criterios cumplen hoy; 8 están «no verificado aún» y se verifican en F2, F3, F4 o F5. Un criterio solo se marca «cumple» si el comando o la lectura se hizo el 2026-11-12.

| ID | funcionalidad | criterio verificable | cómo se verifica | evidencia | resultado actual | estado | fase de verificación | fecha de verificación |
|---|---|---|---|---|---|---|---|---|
| AC01 | FE1 | Dado el manifiesto de Bronze, cuando se recalcula el sha256 de cada archivo, entonces coincide | `python -m pytest -q -p no:cacheprovider tests/test_extract.py` y sha256 de cada ruta del manifiesto | [Evidencia en el repo: `data/bronze/manifest.jsonl`] | 8 de 8; test_extract: 6 passed | **cumple** | F1 | 2026-11-12 |
| AC02 | FE1 | Dado un clon temporal, cuando se ejecuta el pipeline completo dos veces, entonces Bronze sigue coincidiendo con el manifiesto | Clon con `git clone` y `main.py --stage all` dos veces (la extracción verifica el snapshot y no descarga) | [Evidencia en el repo: `docs/entrega_3/evidencias/f1/EV-010_bronze_manifiesto.txt`] | antes 8 de 8; después 8 de 8 | **cumple** | F1 | 2026-11-12 |
| AC03 | FE1 | Cuando se suman las filas de las páginas de la API, entonces igualan el conteo oficial antes y después | `tests/test_extract.py::test_paginas_suman_el_conteo_oficial` | [Evidencia en el repo: `tests/test_extract.py`] | pasa (incluida en test_extract) | **cumple** | F1 | 2026-11-12 |
| AC04 | FE2 | Cuando se une construcciones con el CSV por código de barrio, entonces la cobertura de llave es al menos el umbral | `tests/test_quality.py::test_cobertura_join_supera_umbral` | [Evidencia en el repo: `data/silver/quality_report.json`; `config/config.yaml`] | 99,883 % (umbral 0,80); pasa | **cumple** | F1 | 2026-11-12 |
| AC05 | FE2 | Dado `docs/reglas_silver.md`, entonces cada regla cita un hallazgo y todos existen en `docs/hallazgos_eda.md` | Cruce de ambas tablas | [Evidencia en el repo: `docs/reglas_silver.md`; `docs/hallazgos_eda.md`] | 18 reglas; 0 sin hallazgo; 0 inexistentes | **cumple** | F1 | 2026-11-12 |
| AC06 | FE2 | Cuando una construcción no tiene pareja en el JOIN, entonces se conserva en el archivo de huérfanos | Conteo de `silver_orphans_left.csv` y `quality_report.json` | [Evidencia en el repo: `data/silver/silver_orphans_left.csv`] | 6 construcciones sin llave; 295 barrios del CSV sin construcciones | **cumple** | F1 | 2026-11-12 |
| AC07 | FE2 | Cuando una construcción no tiene datos satelitales, entonces `severo_estricto` es nulo y sale del denominador | Cruce de `severo_estricto` nulo con `sin_datos` | [Evidencia en el repo: `data/gold/gold_final.csv`; `docs/DECISIONES.md (D7)`] | 435 sin datos + 4.711 con datos = 5.146; coincidencia exacta: sí | **cumple** | F1 | 2026-11-12 |
| AC08 | FE3 | Cuando se genera Gold, entonces tiene al menos el mínimo de filas y cero duplicados por `objectid` | `tests/test_quality.py::test_gold_minimo_de_filas_y_sin_duplicados` | [Evidencia en el repo: `data/gold/gold_final.csv`] | 5.146 filas (mínimo 200); 0 duplicados | **cumple** | F1 | 2026-11-12 |
| AC09 | FE3 | Cuando se lee `kpis_gold.csv`, entonces están K1 a K6 | `tests/test_quality.py::test_kpis_presentes_y_en_rango` | [Evidencia en el repo: `data/gold/kpis_gold.csv`] | 23 filas; K1, K2, K3, K4, K5, K6 | **cumple** | F1 | 2026-11-12 |
| AC10 | FE3 | Cuando un KPI trae intervalo, entonces 0 ≤ límite inferior ≤ tasa ≤ límite superior ≤ 1 | Recorrido de `kpis_gold.csv` y `kpis_sensibilidad.csv` | [Evidencia en el repo: `data/gold/kpis_gold.csv`; `data/gold/kpis_sensibilidad.csv`] | 15 de 15 y 87 de 87; incumplen 0 | **cumple** | F1 | 2026-11-12 |
| AC11 | FE3 | Cuando se lee la fecha de corte de cada KPI, entonces es la fecha de edición de la capa configurada | `tests/test_quality.py::test_kpis_presentes_y_en_rango` | [Evidencia en el repo: `data/gold/kpis_gold.csv`; `config/config.yaml`] | 23 de 23 filas con 2026-09-02: sí | **cumple** | F1 | 2026-11-12 |
| AC12 | FE3 | Cuando se carga Gold a SQLite, entonces cada tabla tiene las mismas filas que su CSV | Conteo de filas de cada tabla de `etl_sismo.db` (lectura) | [Evidencia en el repo: `data/gold/etl_sismo.db`] | gold_final 5.146; kpis_gold 23; kpis_sensibilidad 107; silver_integrated 5.146 | **cumple** | F1 | 2026-11-12 |
| AC13 | FE3 | Cuando se recalculan los KPI con SQL independiente, entonces coinciden con `kpis_gold.csv` | Salida guardada del notebook 04 §6 (no se reejecuta en el árbol: regenera la base) | [Evidencia en el repo: `notebooks/04_gold_kpis.ipynb`] | «todo dentro de 1e-9: True» en la salida guardada: sí | **cumple** | F1 | 2026-11-12 |
| AC14 | FE8 | Dado un clon temporal, cuando se ejecuta `main.py --stage all` dos veces, entonces los 9 archivos de Silver y Gold son idénticos entre sí y con la línea base | Clon temporal, dos ejecuciones y comparación de sha256 (determinismo directo) | [Evidencia en el repo: `docs/entrega_3/evidencias/f1/EV-009_determinismo_clon.txt`] | corrida 1: 9 de 9; corrida 2: 9 de 9; corridas iguales entre sí: sí | **cumple** | F1 | 2026-11-12 |
| AC15 | FE8 | Cuando se corren todas las pruebas, entonces pasan, sin saltadas | `python -m pytest -q -p no:cacheprovider` | [Evidencia en el repo: `tests/`] | 55 passed in 12.39s | **cumple** | F1 | 2026-11-12 |
| AC16 | FE8 | Cuando se corren las pruebas, entonces no cambia ningún archivo de Silver ni de Gold | sha256 de los 9 archivos antes y después de `pytest` | [Evidencia en el repo: `docs/entrega_3/evidencias/f1/EV-007_hashes_linea_base.txt`] | 9 de 9 idénticos a la línea base antes y después | **cumple** | F1 | 2026-11-12 |
| AC17 | FE8 | Cuando se compara el README con las salidas, entonces las cifras coinciden | `python -m pytest -q -p no:cacheprovider tests/test_readme_cifras.py` | [Evidencia en el repo: `README.md`; `tests/test_readme_cifras.py`] | 12 passed | **cumple** | F1 | 2026-11-12 |
| AC18 | FE8 | Cuando se leen las rutas citadas en el README, entonces todas existen | `tests/test_readme_cifras.py::test_rutas_citadas_en_readme_existen` | [Evidencia en el repo: `README.md`] | pasa (incluida en el archivo anterior) | **cumple** | F1 | 2026-11-12 |
| AC19 | FE8 | Cuando se arma el zip, entonces no contiene entorno virtual, cachés, `.env`, `.git/` ni `dist/` | `scripts/make_dist.py` en una carpeta temporal fuera del repo y su verificación posterior | [Evidencia en el repo: `scripts/make_dist.py`] | 0 entradas prohibidas en 115; `dist/` sin cambios: ['avance2_etl_20261016.zip'] | **cumple** | F1 | 2026-11-12 |
| AC20 | FE8 | Dado un entorno virtual sin `pyvenv.cfg` (con `bin/python` o `Scripts/python.exe`), cuando se arma el zip, entonces no entra | `python -m pytest -q -p no:cacheprovider tests/test_dist.py` | [Evidencia en el repo: `tests/test_dist.py`] | 4 passed | **cumple** | F1 | 2026-11-12 |
| AC21 | FE8 | Dado un clon con `core.autocrlf` verdadero y otro con falso, cuando se verifican `data/` y las pruebas, entonces los sha256 y las pruebas coinciden | Clon a carpeta temporal y verificación (hecha en F0) | [Evidencia en el repo: `docs/entrega_3/evidencias/f0/EV-003_clon_limpio.txt`] | ambos clones: Bronze 8 de 8, línea base 9 de 9 y pruebas en verde (EV-003, 2026-11-12) | **cumple** | F0 | 2026-11-12 |
| AC22 | FE4 | Dado el servicio en marcha, cuando se pide `GET /health`, entonces responde 200 y publica el esquema OpenAPI | prueba de la API con el cliente de pruebas (se crea en F2) y arranque con un comando | se define en F2 | no verificado aún | **no verificado aún (F2)** | F2 | — |
| AC23 | FE4 | Dado cualquier endpoint, cuando se consulta, entonces no escribe: los sha256 de `data/` y de la base no cambian | Hashes antes y después de ejercer todos los endpoints | se define en F2 | no verificado aún | **no verificado aún (F2)** | F2 | — |
| AC24 | FE5 | Cuando se carga a MySQL, entonces cada tabla tiene las mismas filas que Gold y las claves foráneas están activas | Prueba de integración con marcador `mysql` y conteos | se define en F3 | no verificado aún | **no verificado aún (F3)** | F3 | — |
| AC25 | FE5 | Cuando se repite la carga, entonces no se duplican filas y el historial suma una fila por carga | Prueba de idempotencia e historial | se define en F3 | no verificado aún | **no verificado aún (F3)** | F3 | — |
| AC26 | FE6 | Dado el DAG, cuando se importa, entonces no hay errores y tiene las cinco tareas con sus dependencias (P1) | `DagBag` y `airflow dags list-import-errors` | se define en F4 | no verificado aún | **no verificado aún (F4)** | F4 | — |
| AC27 | FE6 | Cuando se ejecuta de forma manual y programada y luego se repite una corrida, entonces Gold se valida y no se duplica nada (P2, P3 y P5) | `airflow dags test`, observación del programador y comparación de hashes | se define en F4 | no verificado aún | **no verificado aún (F4)** | F4 | — |
| AC28 | FE7 | Cuando se abre el dashboard, entonces muestra K1 a K6 con los recuadros de alcance y no lee la base directamente | prueba de la interfaz con `AppTest` (se crea en F5) | se define en F5 | no verificado aún | **no verificado aún (F5)** | F5 | — |
| AC29 | FE7 | Cuando se recorre interfaz → API → almacén, entonces la prueba de humo de solo lectura pasa | prueba de humo de extremo a extremo de solo lectura (se crea en F5) | se define en F5 | no verificado aún | **no verificado aún (F5)** | F5 | — |

## 4. Criterios que no cumplimos o no aplican
| criterio | estado | motivo |
|---|---|---|
| Pruebas con usuarios reales | no aplica al MVP | Dependen de un hecho externo; se tratan en F6 y no se simulan. |
| Modelos de aprendizaje automático, registro de modelos y LLMOps | N/A justificado | El proyecto no entrena modelos (`docs/entrega_3/decisiones_tecnicas.md`, decisión e). |
| Prueba de instalación en un entorno virtual nuevo con el código final | no cumple (pendiente) | `docs/prueba_entorno_limpio.md` se ejecutó con 26 pruebas, antes de los cambios posteriores; el clon limpio de F0 usa el `.venv` existente. Se repite en F8. |
| Zip de `dist/` con el código actual | no cumple (pendiente) | `dist/avance2_etl_20261016.zip` es anterior a los cambios; se regenera en F8. |
| Prueba automática de la lectura de archivos Excel | no cumple | No está en `tests/`; consta solo como comprobación manual en `docs/verificacion_entrega.md`. |
| Meta del Avance 1 de cobertura del 90 % de los puntos verificados (KR1) | no evaluado | No tenemos la fuente por punto. |
| Revisión visual de los códigos de barrio sobre el mapa | pendiente | Es un juicio del equipo (`docs/revision_codigos_barrio.md`). |

## Cómo lo defendemos
- **Qué afirmamos:** definimos el MVP de la Entrega 3 con ocho funcionalidades y 29 criterios; 21 se ejecutaron hoy y 8 (API, MySQL, Airflow y dashboard) se verifican en F2 a F5.
- **Con qué evidencia:** los comandos y archivos de la tabla; el determinismo se comprobó en un clon temporal con dos ejecuciones completas.
- **Qué NO afirmamos:** que la API, el almacén relacional, la orquestación o el dashboard funcionen: todavía no existen.
- **La pregunta más probable del profesor:** «¿Por qué los criterios de pipeline parecen escritos después de ver los resultados?».
- **Cómo respondemos:** porque lo son: los formalizamos sobre pruebas y umbrales que ya existían, y lo decimos al inicio; los criterios nuevos se redactaron antes de construir los componentes.
