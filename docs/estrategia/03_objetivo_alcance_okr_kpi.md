# 3. Objetivo, alcance, OKR y KPI

**Ítem del checklist (1.3):** «Definimos el objetivo, alcance, los OKRs y los KPIs (métricas de valor) para evaluar el desempeño y el impacto del proyecto.» · **Fecha:** 2026-11-12 · Índice: [indice.md](indice.md)

> **Etiquetas de evidencia.** [Evidencia en el repo: `ruta`] = existe en el repositorio; [Fuente externa: URL y fecha de consulta]; [Criterio aplicado: descripción] = regla o decisión nuestra, explicada; [Hipótesis de diseño: criterio y experimento de validación propuesto, no ejecutado] = hipótesis de diseño con su experimento, sin ejecutar. Las cifras se leen de `data/silver`, `data/gold` y `config/config.yaml`.

## 1. Objetivo y alcance
**Objetivo del Proyecto 1 (Avance 1).** «Evidenciar, con datos reales, si la severidad del daño estructural en Cali se explica mejor por la vulnerabilidad geotécnica/constructiva de cada zona que por su nivel socioeconómico.» [Evidencia en el repo: `docs/proyecto/referencias/contexto_y_problema.pdf, p. 5`]

**Objetivo general del proyecto.** Entregar un servicio de análisis reproducible de impacto sísmico por zonas, con incertidumbre explícita: un pipeline ETL medallion que integra una capa satelital de construcciones con el estrato por barrio de 2015, calcula indicadores con intervalos y los expone mediante una API de solo lectura, un almacenamiento relacional con historial, una orquestación programada y un dashboard. [Evidencia en el repo: `README.md §1 y §3`; `docs/proyecto/decisiones_tecnicas.md`] La API ya existe; el almacenamiento relacional, la orquestación y el dashboard están **en construcción**.

**Objetivos específicos** [Evidencia en el repo: `README.md §4 a §10`]
1. Extraer la capa satelital (API ArcGIS), el CSV de estrato y los polígonos de barrios y conservar lo descargado sin modificar, con manifiesto y sha256.
2. Limpiar, normalizar, tratar nulos y duplicados e integrar las fuentes por código de barrio, conservando los registros sin pareja.
3. Calcular K1 a K6 con intervalos, cotas por falta de datos y seis escenarios de sensibilidad.
4. Verificar con pruebas automáticas, recálculo independiente y documentación (hecho).
5. Exponer los resultados por una API de solo lectura, cargarlos a un almacén relacional con historial, orquestar el flujo y mostrarlo en un dashboard (la API ya existe; el almacén relacional, la orquestación y el dashboard están en construcción).

**Alcance, población analizada.** 5.146 construcciones (4.711 con datos satelitales) de 7 comunas (03, 09, 10, 17, 18, 19 y 20), en 52 códigos de barrio, dentro de los polígonos de afectación preliminar del visor de emergencia del IGAC según la descripción del dataset. [Evidencia en el repo: `docs/gold/KPIs.md «Población analizada»`; `data/gold/gold_final.csv`]
**Alcance temporal.** Estrato de 2015 (DAPM Cali, lados de manzana) frente a imágenes del 2026-03-22 y del 2026-08-11 y capa editada el 2026-09-02: unos once años de distancia. Los resultados por estrato describen el estrato de 2015 asignado al barrio, no el vigente. [Evidencia en el repo: `docs/gold/KPIs.md «Alcance temporal»`; `config/config.yaml (fechas)`]
**Fuera del alcance.** Las comunas ausentes (incluida la Comuna 2) y la zona rural; el daño interno y cualquier evaluación estructural; causalidad; amenaza sísmica oficial; antigüedad constructiva; el seguimiento de verificación de la Alcaldía; modelos de aprendizaje automático. [Evidencia en el repo: `README.md §11 y §17`; `docs/gold/KPIs.md «Qué NO se puede concluir»`]

## 2. OKR
**Objetivo (Avance 1).** «Evidenciar, con datos reales, si la severidad del daño estructural en Cali se explica mejor por la vulnerabilidad geotécnica/constructiva de cada zona que por su nivel socioeconómico.» [Evidencia en el repo: `docs/proyecto/referencias/contexto_y_problema.pdf, p. 5`]

| KR | redacción del Avance 1 | KPI operativo del Avance 1 | meta o umbral del Avance 1 | fuente prevista | estado en este avance (tabla de alcance del README) |
|---|---|---|---|---|---|
| KR1 | «Identificar las zonas con mayor concentración de daño severo» | N.º de colapsos totales/parciales por barrio y comuna, sobre el total de reportes verificados a la fecha de corte | Cobertura de al menos el 90% de los puntos verificados oficialmente, geolocalizados y clasificados | Repositorio Oficial — Alcaldía de Cali | **parcial**: K3 y K6; solo 7 comunas |
| KR2 | «Contrastar el daño con el nivel de amenaza sísmica oficial» | % de edificaciones dañadas ubicadas en zonas de amenaza sísmica alta, según el mapa oficial de la Alcaldía de Cali / DAGMA | Establecer con claridad si la correlación es alta, media o baja frente al mapa de amenaza | Datos Abiertos Cali — Mapa de amenaza sísmica | **no cubierto**: no se usó amenaza sísmica oficial; trabajo futuro |
| KR3 | «Explorar, de forma cualitativa, la relación entre antigüedad constructiva y severidad del daño» | N.º de casos documentados en fuentes periodísticas técnicas verificadas que asocian antigüedad de la construcción con severidad del daño | Contrastar cualitativamente en al menos 3 fuentes periodísticas independientes si existe un patrón consistente (limitación: no se dispone de fuente cuantitativa abierta por edificación) | Prensa especializada y verificada | **fuera de alcance**: cualitativo, no es ETL |
| KR4 | «Establecer si el estrato socioeconómico explica o no el patrón de daño» | % de colapsos por estrato socioeconómico (1 a 6) | Confirmar o descartar la hipótesis de que el daño depende principalmente del estrato | Datos Abiertos Cali / DANE — Estratificación | **cubierto con el proxy satelital**: K1 y K2 |
| KR5 | «Medir el avance de verificación oficial de los reportes ciudadanos» | % de reportes ciudadanos verificados técnicamente vs. pendientes | Seguimiento periódico del avance de verificación mientras la Alcaldía actualiza el repositorio | Repositorio Oficial — Alcaldía de Cali | **fuera de alcance**: seguimiento, no es ETL |

Fuente de la redacción: [Evidencia en el repo: `docs/proyecto/referencias/contexto_y_problema.pdf, p. 5-6`]. Fuente del estado: [Evidencia en el repo: `README.md §3`]. Los KPI del Avance 1 (conteos de colapsos por barrio, porcentaje de reportes verificados) no son los K1 a K6: son medidas sobre datos oficiales por punto que no tenemos. K1 a K6 son tasas de severo estricto sobre un proxy satelital.

**Justificación del estado**
- **KR1** (parcial). Medimos concentración con el proxy satelital (K3, K6), no con conteos de colapsos totales o parciales. Solo 7 comunas.
- **KR2** (no cubierto). No usamos el mapa de amenaza sísmica oficial; queda como trabajo futuro.
- **KR3** (fuera de alcance). Es cualitativo y no es una tarea de ETL; no se hizo la revisión de 3 fuentes periodísticas.
- **KR4** (cubierto con el proxy satelital). Cubierto con el proxy (K1, K2): con este proxy y esta muestra no se detecta diferencia entre los estratos 3-5 y 1-2 (diferencia +0,49 pp, Newcombe [−2,36; +2,55]).
- **KR5** (fuera de alcance). Es seguimiento de un proceso de la Alcaldía y no es tarea de ETL; no lo medimos.

## 3. KPI
### 3.1 KPI del fenómeno (K1 a K6)
`data/gold/kpis_gold.csv` tiene 23 filas con 6 indicadores; `data/gold/kpis_sensibilidad.csv` repite K1, K2 y K6 en seis escenarios (107 filas). Denominador de toda tasa: construcciones con datos satelitales. La decisión que cada KPI informa es una apreciación nuestra. [Criterio aplicado: apreciación del equipo]

| KPI | definición y fórmula | fuente de datos | umbral o meta | valor actual (leído de los archivos) | decisión que informa | límite de interpretación |
|---|---|---|---|---|---|---|
| K1 | Tasa de severo estricto por estrato: k/n con IC de Wilson al 95 %, % sin datos y cotas extremas | `data/silver/silver_integrated.csv` → `data/gold/kpis_gold.csv` | Muestra baja si k < 30 | E1 20/302 = 6,62 %; E2 3/92 = 3,26 %; E3 74/1.173 = 6,31 %; E4 145/2.095 = 6,92 %; E5 53/1.031 = 5,14 %; E6 0/11 = 0,00 % | Si el cambio satelital severo difiere visiblemente entre estratos | E1, E2 y E6 con muestra baja; E2 con 27,0 % sin datos |
| K2 | Estratos 3-5 frente a 1-2: razón, diferencia con intervalo de Newcombe y razón de Mantel-Haenszel ajustada por comuna | ídem | Si el intervalo incluye 0, solo se dice «con este proxy y esta muestra no se detecta diferencia» | 3-5: 6,33 %; 1-2: 5,84 %; razón 1,084; diferencia +0,49 pp [−2,36; +2,55]; razón MH 1,970 | Si hay una brecha entre estratos que justifique mirar más | La razón MH no es interpretable (una sola comuna con ambos grupos) |
| K3 | Concentración: severos en los 10 barrios con más severos / severos con barrio | ídem | Sin umbral | 167/295 = 56,6 %; esos barrios reúnen 48,7 % de las construcciones con datos | Dónde mirar primero | Más construcciones no es mayor riesgo |
| K4 | Spearman entre estrato moda del barrio y tasa de severos (barrios con al menos 10 construcciones con datos) | ídem | Sin umbral | rho = 0,035; n = 45 barrios; p de permutación = 0,8218 | Si hay relación monótona a nivel de barrio | Descriptivo; falacia ecológica |
| K5 | Calidad del JOIN: cobertura de llave, cobertura de estrato válido, nombre validado | `data/silver/quality_report.json` | Cobertura de llave ≥ 0,80 | 99,883 %; 99,845 %; 93,52 % | Si la integración es confiable | El nombre validado no prueba que el barrio asignado sea el correcto |
| K6 | Tasa por comuna con Wilson, % sin datos y muestra baja | ídem | Muestra baja si k < 30 | C03 39/550 = 7,09 %; C09 7/184 = 3,80 %; C10 35/541 = 6,47 %; C17 4/87 = 4,60 %; C18 8/96 = 8,33 %; C19 182/2.909 = 6,26 %; C20 20/342 = 5,85 % | Si la concentración es por zona | Solo 7 comunas; estrato y ubicación mezclados |

Fuentes de las definiciones: [Evidencia en el repo: `docs/gold/KPIs.md`; `src/transform/build_gold.py`].

### 3.2 KPI de desempeño del proyecto
Miden la calidad de nuestro trabajo; no miden impacto en usuarios, porque no los hay medidos. [Criterio aplicado: definición del equipo]

| KPI | definición y fórmula | fuente | umbral o meta | valor actual | decisión que informa | límite |
|---|---|---|---|---|---|---|
| P1 Cobertura de llave | construcciones con llave en el CSV / construcciones | `data/silver/quality_report.json` | ≥ 0,80 (`config/config.yaml`, `thresholds.join_coverage_min`) | 99,883 % (5.140 de 5.146); resultado: pasa | Si se integra sin perder construcciones | No mide si el barrio asignado es correcto |
| P2 Cobertura de estrato válido | construcciones con llave y estrato moda de 1 a 6 / construcciones | ídem | Sin umbral definido | 99,845 % (5.138) | Cuántas construcciones entran a los KPI por estrato | Excluye los barrios con estrato moda NR |
| P3 Nombre validado | construcciones en códigos cuyo nombre 2015 coincide (similitud ≥ 0,85) con el polígono 2026 | ídem | `llave_confianza`: alta ≥ 0,90 | 93,52 % (4.807 de 5.140); confianza alta | Si la llave es confiable | 244 de las 333 no validadas son diferencias de escritura |
| P4 Filas de Gold | filas de `gold_final.csv`, sin duplicados por `objectid` | `data/gold/gold_final.csv` | ≥ 200 (`thresholds.gold_min_rows`) | 5.146 filas; duplicados 0 | Si hay muestra suficiente | No mide la calidad de las filas |
| P5 Pruebas en verde | pruebas automáticas que pasan / pruebas | `tests/` | Todas | 1330 passed in 343.0s (verificado el 2026-11-16) | Si el pipeline hace lo documentado | Que pasen no garantiza que los datos sean ciertos |
| P6 Determinismo | archivos de Silver y Gold con sha256 idéntico entre dos ejecuciones | clon temporal | 100 % | 9 de 9 idénticos entre dos ejecuciones de `main.py --stage all` y con la línea base | Si un tercero reproduce los resultados | Medido en un clon temporal, no en el árbol de trabajo |
| P7 Empaquetado sin entorno virtual | entradas prohibidas en el zip | `scripts/make_dist.py`, `tests/test_dist.py` | 0 | 0 entradas prohibidas en el zip de prueba (carpeta temporal) | Si se puede entregar sin el entorno | El zip real de `dist/` es anterior a los cambios |

### 3.3 Métricas de valor (impacto)
Son métricas de valor del proyecto como servicio de análisis; el impacto sobre decisiones reales no se mide porque no hay usuarios. [Criterio aplicado: definición del equipo]

| métrica | fórmula | fuente | valor actual | límite |
|---|---|---|---|---|
| V1 Construcciones con dato satelital utilizable | construcciones con `sin_datos = false` / construcciones | `data/gold/gold_final.csv` | 91,5 % (4.711 de 5.146) | Mide disponibilidad, no exactitud del proxy |
| V2 Cobertura de la llave | construcciones con llave / construcciones | `data/silver/quality_report.json` | 99,883 % | Ver P1 |
| V3 Reproducibilidad | diferencias de sha256 entre dos corridas | clon temporal | 0 diferencias de 9 archivos | Solo Silver y Gold |
| V4 Componentes del proyecto | latencia de la API; tiempo de carga al almacén; tasa de éxito del DAG; tiempo de carga del dashboard | pruebas de cada componente; `docs/evidencias/api/EV-018_latencia_api.csv`, `docs/evidencias/almacenamiento/EV-030_benchmark_lotes.csv`, `docs/evidencias/almacenamiento/EV-032_latencia_api_mysql_vs_sqlite.csv` | latencia de la API: mediana entre 3,2 y 11,0 ms por ruta y percentil 95 de hasta 12,2 ms (50 repeticiones tras 5 de calentamiento, servidor real en 127.0.0.1; medición local de una máquina, EV-018); tiempo de carga al almacén: mediana de 715,0 ms para 5622 filas con lote de 2000 frente a 2415,0 ms fila a fila (5 repeticiones tras 1 de calentamiento, EV-030); API sobre MySQL: mediana de las medianas de 88,2 ms frente a 6,1 ms con SQLite (EV-032); el resto se mide cuando existan los componentes en construcción | Medición local, no representa un despliegue; sin valor para los componentes que aún no existen |

## 4. Trazabilidad OKR → KPI → evidencia → verificación
| OKR | meta del Avance 1 / qué logramos | KPI asociado | archivo de evidencia | prueba o comando |
|---|---|---|---|---|
| Objetivo general | Objetivo del Avance 1: **cubierto en parte**; K1, K2, K4 y K6 son lo que logramos | K1, K2, K4, K6 | `data/gold/kpis_gold.csv`, `data/gold/kpis_sensibilidad.csv` | `python -m pytest -q -p no:cacheprovider tests/test_kpis.py`; notebook 04 §6 (recálculo SQL, diferencia máxima inferior a 1e-9) |
| KR1 (parcial) | Meta: Cobertura de al menos el 90% de los puntos verificados oficialmente, geolocalizados y clasificados. Logro: Meta de cobertura del 90 % de los puntos verificados: **no se pudo evaluar con esta capa**, porque no encontramos una tabla oficial descargable de daño por barrio y la capa satelital no es una verificación de puntos. Logramos: K3 y K6 sobre 4.711 construcciones con datos. | K3, K6 | `data/gold/kpis_gold.csv` | `python -m pytest -q -p no:cacheprovider tests/test_kpis.py::test_consistencia_k1_k6_k5_y_rangos` |
| KR2 (no cubierto) | Meta: Establecer con claridad si la correlación es alta, media o baja frente al mapa de amenaza. Logro: No evaluado: no se usó el mapa de amenaza. | ninguno | no hay | no aplica |
| KR3 (fuera de alcance) | Meta: Contrastar cualitativamente en al menos 3 fuentes periodísticas independientes si existe un patrón consistente (limitación: no se dispone de fuente cuantitativa abierta por edificación). Logro: No evaluado: es cualitativo y no se hizo. | ninguno | no hay | no aplica |
| KR4 (cubierto con el proxy satelital) | Meta: Confirmar o descartar la hipótesis de que el daño depende principalmente del estrato. Logro: Logramos K1 y K2 con intervalos; la meta «confirmar o descartar» no se alcanza: el resultado es «con este proxy y esta muestra no se detecta diferencia». | K1, K2 (con S0 a S5), K4 | `data/gold/kpis_gold.csv`, `data/gold/kpis_sensibilidad.csv` | `python -m pytest -q -p no:cacheprovider tests/test_kpis.py::test_k1_recalculado_desde_gold` |
| KR5 (fuera de alcance) | Meta: Seguimiento periódico del avance de verificación mientras la Alcaldía actualiza el repositorio. Logro: No evaluado: seguimiento fuera del ETL. | ninguno | no hay | no aplica |
| Calidad de la integración (sostiene KR1 y KR4) | P1, P2, P3 superan el umbral | K5, P1, P2, P3 | `data/silver/quality_report.json`, `docs/silver/validacion_llave.md` | `tests/test_quality.py::test_cobertura_join_supera_umbral` |
| Reproducibilidad (sostiene todos) | P4 a P7 | P4, P5, P6, P7 | `data/bronze/manifest.jsonl`, `tests/`, `scripts/make_dist.py` | `tests/test_extract.py::test_archivos_existen_y_sha256_coincide`; `tests/test_dist.py` |
| Componentes del proyecto | latencia de la API y tiempo de carga al almacén medidos (EV-018, EV-030 y EV-032); el resto se mide cuando existan los componentes en construcción | V4 | se define en cada componente | pruebas de cada componente |

Estas filas no convierten un KR parcial en cumplido.

## Alcance y límites
- **Qué afirmamos:** definimos objetivo, alcance, OKR del Avance 1 con su estado real, KPI del fenómeno y de desempeño, métricas de valor y una trazabilidad hasta el comando de verificación.
- **Con qué evidencia:** las tablas de este documento, `docs/gold/KPIs.md`, `data/gold/*.csv` y `data/silver/quality_report.json`.
- **Qué NO afirmamos:** que cumplimos los KR2, KR3 y KR5, que la meta del 90 % de puntos verificados se evaluó ni que medimos impacto en usuarios.

## Preguntas frecuentes
- **«¿Cumplieron los OKR del Avance 1?»** Cubrimos KR4 con el proxy, KR1 en parte y no cubrimos KR2, KR3 ni KR5; la tabla de trazabilidad dice qué logramos frente a cada meta y por qué la meta del 90 % no se pudo evaluar.
