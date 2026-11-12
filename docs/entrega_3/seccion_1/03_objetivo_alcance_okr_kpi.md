# 3. Objetivo, alcance, OKR y KPI

**Ítem del checklist:** «Definimos el objetivo, alcance, los OKRs y los KPIs (métricas de valor) para evaluar el desempeño y el impacto del proyecto.» · **Fecha:** 2026-11-11 · Índice: [indice.md](indice.md)

> **Cómo leer las etiquetas.** [Evidencia en el repo: `ruta`] = existe en el repositorio; [Fuente externa: URL y fecha de consulta]; [Hipótesis del equipo, por validar] = juicio nuestro por validar. Las cifras se leen de `data/gold/*.csv`, `data/silver/quality_report.json` y `config/config.yaml`.

## 1. Objetivo y alcance
**Objetivo del Proyecto 1 (Avance 1).** «Evidenciar, con datos reales, si la severidad del daño estructural en Cali se explica mejor por la vulnerabilidad geotécnica/constructiva de cada zona que por su nivel socioeconómico.» [Evidencia en el repo: `docs/referencias/avance_1_contexto_y_problema.pdf, p. 5`]

**Objetivo general del Avance 2.** Construir un pipeline ETL reproducible con arquitectura medallion que integre una capa satelital de construcciones con el estrato por barrio de 2015, y calcule indicadores con incertidumbre para responder, con este proxy y esta muestra, si el cambio satelital severo varía entre estratos. [Evidencia en el repo: `README.md §1 y §3`; `docs/comprension_proyecto1.md «Qué hereda este Avance 2»`]

**Objetivos específicos.** [Evidencia en el repo: `README.md §4 a §10`]
1. Extraer la capa satelital (API ArcGIS), el CSV de estrato y los polígonos de barrios, y conservar lo descargado sin modificar, con manifiesto y sha256.
2. Limpiar, normalizar tipos, tratar nulos y duplicados e integrar las fuentes por código de barrio, conservando los registros sin pareja.
3. Calcular los indicadores K1 a K6 con intervalos, cotas por falta de datos y seis escenarios de sensibilidad.
4. Verificar el resultado con pruebas automáticas, recálculo independiente y documentación.

**Alcance dentro.** 5.146 construcciones (4.711 con datos satelitales) de 7 comunas (03, 09, 10, 17, 18, 19 y 20), en 52 códigos de barrio, dentro de los polígonos de afectación preliminar del visor de emergencia del IGAC según la descripción del dataset. [Evidencia en el repo: `docs/KPIs.md «Población analizada»`; `data/gold/gold_final.csv`]

**Alcance temporal.** Estrato de 2015 (DAPM Cali, lados de manzana) frente a imágenes del 2026-03-22 y del 2026-08-11 y capa editada el 2026-09-02: unos once años de distancia. Los resultados por estrato describen el estrato de 2015 asignado al barrio, no el vigente. [Evidencia en el repo: `docs/KPIs.md «Alcance temporal»`; `config/config.yaml (fechas)`]

**Alcance fuera.** Las comunas ausentes (incluida la Comuna 2) y la zona rural; el daño interno y cualquier evaluación estructural; causalidad; amenaza sísmica oficial; antigüedad constructiva; el seguimiento de verificación de la Alcaldía; interfaz, API y orquestación. [Evidencia en el repo: `README.md §11 y §17`; `docs/KPIs.md «Qué NO se puede concluir»`]

## 2. OKR
**Objetivo (Avance 1).** «Evidenciar, con datos reales, si la severidad del daño estructural en Cali se explica mejor por la vulnerabilidad geotécnica/constructiva de cada zona que por su nivel socioeconómico.» [Evidencia en el repo: `docs/referencias/avance_1_contexto_y_problema.pdf, p. 5`]

| KR | redacción del Avance 1 | KPI operativo del Avance 1 | meta o umbral del Avance 1 | fuente prevista | estado en este avance (tabla de alcance del README) |
|---|---|---|---|---|---|
| KR1 | «Identificar las zonas con mayor concentración de daño severo» | N.º de colapsos totales/parciales por barrio y comuna, sobre el total de reportes verificados a la fecha de corte | Cobertura de al menos el 90% de los puntos verificados oficialmente, geolocalizados y clasificados | Repositorio Oficial — Alcaldía de Cali | **parcial**: K3 y K6; solo 7 comunas |
| KR2 | «Contrastar el daño con el nivel de amenaza sísmica oficial» | % de edificaciones dañadas ubicadas en zonas de amenaza sísmica alta, según el mapa oficial de la Alcaldía de Cali / DAGMA | Establecer con claridad si la correlación es alta, media o baja frente al mapa de amenaza | Datos Abiertos Cali — Mapa de amenaza sísmica | **no cubierto**: no se usó amenaza sísmica oficial; trabajo futuro |
| KR3 | «Explorar, de forma cualitativa, la relación entre antigüedad constructiva y severidad del daño» | N.º de casos documentados en fuentes periodísticas técnicas verificadas que asocian antigüedad de la construcción con severidad del daño | Contrastar cualitativamente en al menos 3 fuentes periodísticas independientes si existe un patrón consistente (limitación: no se dispone de fuente cuantitativa abierta por edificación) | Prensa especializada y verificada | **fuera de alcance**: cualitativo, no es ETL |
| KR4 | «Establecer si el estrato socioeconómico explica o no el patrón de daño» | % de colapsos por estrato socioeconómico (1 a 6) | Confirmar o descartar la hipótesis de que el daño depende principalmente del estrato | Datos Abiertos Cali / DANE — Estratificación | **cubierto con el proxy satelital**: K1 y K2 |
| KR5 | «Medir el avance de verificación oficial de los reportes ciudadanos» | % de reportes ciudadanos verificados técnicamente vs. pendientes | Seguimiento periódico del avance de verificación mientras la Alcaldía actualiza el repositorio | Repositorio Oficial — Alcaldía de Cali | **fuera de alcance**: seguimiento, no es ETL |

Fuente de la redacción: [Evidencia en el repo: `docs/referencias/avance_1_contexto_y_problema.pdf, p. 5-6`]. Fuente del estado: [Evidencia en el repo: `README.md §3`].

**Justificación del estado**
- **KR1** (parcial). Medimos concentración con el proxy satelital (K3, K6), no con conteos de colapsos totales o parciales; la meta del Avance 1 (90 % de los puntos verificados) no se evaluó porque no encontramos una tabla oficial descargable de daño por barrio, solo boletines. Solo 7 comunas.
- **KR2** (no cubierto). No usamos el mapa de amenaza sísmica oficial; queda como trabajo futuro.
- **KR3** (fuera de alcance). Es cualitativo y no es una tarea de ETL; no se hizo la revisión de las 3 fuentes periodísticas.
- **KR4** (cubierto con el proxy satelital). Cubierto con el proxy satelital (K1, K2): con este proxy y esta muestra no se detecta diferencia entre los estratos 3-5 y 1-2 (diferencia +0,49 pp, Newcombe [−2,36; +2,55]).
- **KR5** (fuera de alcance). Es seguimiento de un proceso de la Alcaldía y no es tarea de ETL; no lo medimos.

Los KPI del Avance 1 (conteos de colapsos por barrio, porcentaje de reportes verificados) no son los K1 a K6: son medidas sobre datos oficiales por punto que no tenemos. K1 a K6 son tasas de severo estricto sobre una proxy satelital. Esa diferencia se mantiene explícita en la tabla de trazabilidad.

## 3. KPI
### 3.1 KPI del fenómeno (K1 a K6)
`data/gold/kpis_gold.csv` tiene 23 filas con 6 indicadores; `data/gold/kpis_sensibilidad.csv` repite K1, K2 y K6 en seis escenarios (107 filas). Denominador de toda tasa: construcciones con datos satelitales. La decisión que cada KPI informa es nuestra apreciación. [Hipótesis del equipo, por validar]

| KPI | definición y fórmula | fuente de datos | umbral o meta | valor actual (leído de los archivos) | decisión que informa | límite de interpretación |
|---|---|---|---|---|---|---|
| K1 | Tasa de severo estricto por estrato: k/n con IC de Wilson al 95 %, % sin datos y cotas extremas | `data/silver/silver_integrated.csv` → `data/gold/kpis_gold.csv` | Muestra baja si k < 30 | E1 20/302 = 6,62 %; E2 3/92 = 3,26 %; E3 74/1.173 = 6,31 %; E4 145/2.095 = 6,92 %; E5 53/1.031 = 5,14 %; E6 0/11 = 0,00 % | Si el cambio satelital severo difiere visiblemente entre estratos | E1, E2 y E6 con muestra baja; E2 con 27,0 % sin datos |
| K2 | Estratos 3-5 frente a 1-2: razón, diferencia con intervalo de Newcombe y razón de Mantel-Haenszel ajustada por comuna | ídem | Regla: si el intervalo incluye 0, solo se dice «con este proxy y esta muestra no se detecta diferencia» | 3-5: 6,33 %; 1-2: 5,84 %; razón 1,084; diferencia +0,49 pp [−2,36; +2,55]; razón MH 1,970 | Si hay una brecha entre estratos que justifique mirar más | La razón MH no es interpretable (una sola comuna con ambos grupos); no significa que el estrato no influya |
| K3 | Concentración: severos en los 10 barrios con más severos / severos con barrio | ídem | Sin umbral | 167/295 = 56,6 %; esos barrios reúnen 48,7 % de las construcciones con datos | Dónde mirar primero para estudios adicionales | Más construcciones no es mayor riesgo |
| K4 | Spearman entre estrato moda del barrio y tasa de severos del barrio (barrios con al menos 10 construcciones con datos) | ídem | Sin umbral | rho = 0,035; n = 45 barrios; p de permutación = 0,8218 | Si hay relación monótona a nivel de barrio | Descriptivo; falacia ecológica |
| K5 | Calidad del JOIN: cobertura de llave, cobertura de estrato válido, nombre validado | `data/silver/quality_report.json` | Cobertura de llave ≥ 0,80 | 99,883 %; 99,845 %; 93,52 % | Si la integración es confiable | El nombre validado no prueba que el barrio asignado sea el correcto |
| K6 | Tasa por comuna con Wilson, % sin datos y muestra baja | ídem | Muestra baja si k < 30 | C03 39/550 = 7,09 %; C09 7/184 = 3,80 %; C10 35/541 = 6,47 %; C17 4/87 = 4,60 %; C18 8/96 = 8,33 %; C19 182/2.909 = 6,26 %; C20 20/342 = 5,85 % | Si la concentración es por zona | Solo 7 comunas; estrato y ubicación mezclados |

Fuentes de las definiciones: [Evidencia en el repo: `docs/KPIs.md`; `src/transform/build_gold.py`].

### 3.2 KPI de desempeño del proyecto
Son nuestras medidas de calidad del trabajo y no miden el impacto sobre ningún usuario: no tenemos usuarios medidos. [Hipótesis del equipo, por validar]

| KPI | definición y fórmula | fuente | umbral o meta | valor actual | decisión que informa | límite |
|---|---|---|---|---|---|---|
| P1 Cobertura de llave | construcciones con llave en el CSV / construcciones | `data/silver/quality_report.json` | ≥ 0,80 (`config/config.yaml`, `thresholds.join_coverage_min`) | 99,883 % (5.140 de 5.146); resultado: pasa | Si se puede integrar sin perder construcciones | No mide si el barrio asignado es correcto |
| P2 Cobertura de estrato válido | construcciones con llave y estrato moda de 1 a 6 / construcciones | ídem | Sin umbral definido | 99,845 % (5.138) | Cuántas construcciones entran a los KPI por estrato | Excluye los barrios con estrato moda NR |
| P3 Nombre validado | construcciones en códigos cuyo nombre 2015 coincide (similitud ≥ 0,85) con el polígono 2026 | ídem | `llave_confianza`: alta ≥ 0,90 | 93,52 % (4.807 de 5.140); confianza alta | Si la llave es confiable | El umbral se fijó antes de ver los resultados; 244 de las 333 no validadas son diferencias de escritura |
| P4 Filas de Gold | filas de `gold_final.csv`, sin duplicados por `objectid` | `data/gold/gold_final.csv` | ≥ 200 (`thresholds.gold_min_rows`) | 5.146 filas; duplicados 0 | Si hay muestra suficiente | No mide la calidad de las filas |
| P5 Pruebas en verde | pruebas automáticas que pasan / pruebas | `tests/` | Todas | 50 passed in 1.99s (verificado el 2026-11-11) | Si el pipeline hace lo documentado | Que pasen no garantiza que los datos sean ciertos |
| P6 Determinismo | archivos de Silver y Gold con sha256 idéntico tras regenerarlos | `docs/prueba_entorno_limpio.md`, `dist/` | 100 % | 9 de 9 idénticos entre el zip del 16-oct y los archivos regenerados el 2026-10-16 15:15 | Si un tercero reproduce los resultados | No se reejecutó hoy para no regenerar la base |
| P7 Empaquetado sin entorno virtual | entradas prohibidas en el zip | `scripts/make_dist.py`, `tests/test_dist.py` | 0 | 0 entradas prohibidas en el zip de prueba (carpeta temporal) | Si se puede entregar sin el entorno | El zip real de `dist/` es anterior a los cambios |

Fuentes: [Evidencia en el repo: `config/config.yaml`; `docs/validacion_llave.md`; `docs/revision_codigos_barrio.md`; `docs/prueba_entorno_limpio.md`; `docs/avance_2/registro_cambios_retroalimentacion.md`].

## 4. Trazabilidad OKR → KPI → evidencia → verificación
| OKR | KPI asociado | archivo de evidencia | prueba o comando de verificación |
|---|---|---|---|
| Objetivo general | K1, K2, K4, K6 | `data/gold/kpis_gold.csv`, `data/gold/kpis_sensibilidad.csv` | `python -m pytest -q -p no:cacheprovider tests/test_kpis.py`; notebook 04 §6 (recálculo SQL, diferencia máxima inferior a 1e-9) |
| KR1 (parcial) | K3, K6 (proxy; no los conteos del Avance 1) | `data/gold/kpis_gold.csv` | `tests/test_kpis.py::test_consistencia_k1_k6_k5_y_rangos` |
| KR2 (no cubierto) | ninguno | no hay | no aplica |
| KR3 (fuera de alcance) | ninguno | no hay | no aplica |
| KR4 (cubierto con el proxy) | K1, K2 (con S0 a S5), K4 | `data/gold/kpis_gold.csv`, `data/gold/kpis_sensibilidad.csv`, `README.md §10` | `tests/test_kpis.py::test_k1_recalculado_desde_gold`; `tests/test_readme_cifras.py` |
| KR5 (fuera de alcance) | ninguno | no hay | no aplica |
| Calidad de la integración (sostiene KR1 y KR4) | K5, P1, P2, P3 | `data/silver/quality_report.json`, `docs/validacion_llave.md` | `tests/test_quality.py::test_cobertura_join_supera_umbral` |
| Reproducibilidad (sostiene todos) | P4, P5, P6, P7 | `data/bronze/manifest.jsonl`, `tests/`, `scripts/make_dist.py` | `tests/test_extract.py::test_archivos_existen_y_sha256_coincide`; `tests/test_dist.py` |

El cumplimiento de cada KR depende del estado de la tabla de la sección 2; estas filas no convierten un KR parcial en cumplido.
