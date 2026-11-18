# ADR-015: Silver valida la calidad con 18 reglas ligadas a hallazgos, un reporte y umbrales en la configuración

**Estado:** Vigente (implementada). **Fecha de la decisión:** 2026-10-15. **D de origen:** sección «Otras decisiones de Silver», D-FUENTES. **Propietario técnico:** Daniel Alexander Brand García. **Revisión:** Jhoan Sebastián Castellanos Mayor, 2026-11-18.

## Contexto
Silver recibe una capa satelital de 5.146 construcciones con defectos conocidos (`COMUNA` y `BARRIO` en blanco, geometrías idénticas, construcciones sin datos satelitales) y un CSV de estrato con filas resumen y una moda «NR» que no es un estrato. Había que decidir qué se corrige, qué solo se marca, qué hace parar el pipeline y dónde queda constancia de la calidad.

Este diseño no tiene un D propio en `docs/DECISIONES.md`. Lo reconstruimos desde la sección «Otras decisiones de Silver», desde el criterio G5 de D-FUENTES (cobertura de la llave de 0,80 o más sobre una prueba de 500 filas) y desde `docs/silver/reglas_silver.md`. El diseño del reporte `quality_report.json` y el de los demás umbrales de `config/config.yaml` no tienen decisión registrada.

## Decisión
- Silver aplica 18 reglas (R01 a R18), cada una ligada a uno o más hallazgos (H#) de `docs/silver/hallazgos_eda.md`. R01 a R10 están en `clean_api.py`, R11 a R15 en `clean_excel.py` y R16 a R18 en `integrate.py`, y cada ejecución escribe `docs/silver/reglas_silver.md` con sus filas afectadas y su justificación.
- Las reglas corrigen sin imputar (R02 pasa el texto vacío a nulo), marcan sin borrar (R03 marca `geom_duplicada`; R05 deja `sin_datos`, que no se trata como «sin daño») y conservan lo que no cruza (R16 hace un LEFT JOIN y guarda los huérfanos en `silver_orphans_left.csv` y `silver_orphans_right.csv`). R01 fija `OBJECTID` como identificador único y no deduplica por la combinación de las columnas `COMUNA`, `BARRIO`, `MANZANA`, `TERRENO`, `COND`, `EDIFPRED` y `PREDIO` de Bronze, que se repite en 3.719 filas porque un predio tiene varias construcciones.
- Cada ejecución escribe `data/silver/quality_report.json`, sin marcas de tiempo, con las coberturas, los huérfanos con su causa, los nulos antes y después y las 18 reglas aplicadas. La API lo lee para `/calidad`.
- Los umbrales están en `config/config.yaml`: `join_coverage_min` 0,80, `gold_min_rows` 200, `min_edificios_por_barrio` 10, `silver.muestra_baja_severos` 30 y, en `llave`, `similitud_nombre_min` 0,85, `confianza_alta` 0,90 y `confianza_media` 0,80.
- Silver se detiene, con una excepción o una aserción, si aparece una etiqueta de `Estado_Estructural` que no conoce, si `OBJECTID` o el código de barrio del CSV dejan de ser únicos, si el CSV no se lee como UTF-8 o si hay nombres con codificación dañada (sección 9 del documento de arquitectura).
- Todo lo demás se registra y no detiene Silver. La cobertura de la llave queda en `resultado_umbral`, con un aviso si es menor que el umbral más 0,05; los huérfanos, las geometrías duplicadas y una `llave_confianza` distinta de `alta` salen como avisos. Gold sí se detiene, con una aserción, si queda con menos de `gold_min_rows` filas.

## Consecuencias
### Positivas
- Cada defecto tiene una regla con nombre, un hallazgo que la justifica y un conteo de filas afectadas.
- Nada se descarta en silencio: las 6 construcciones sin llave y los 295 barrios del CSV sin construcciones se guardan en archivos aparte.
- `quality_report.json` y los demás archivos de Silver se escriben de forma determinista y entran en la comparación byte a byte con lo versionado.

### Negativas
- No hay una decisión registrada para este diseño: no sabemos qué alternativas se miraron al elegir las reglas, el reporte ni los umbrales.
- `min_edificios_por_barrio` (10) no tiene decisión registrada en `docs/DECISIONES.md`: solo aparece en `config/config.yaml` y en la fórmula de K4 de `docs/gold/KPIs.md`. Tampoco la tienen `confianza_alta` (0,90), `confianza_media` (0,80) y `gold_min_rows` (200), y el 0,85 de `similitud_nombre_min` aparece en las decisiones como resultado, sin la razón de elegirlo.
- El 0,80 de la cobertura viene del criterio G5, evaluado sobre 500 filas como aceptación de la fuente; que Silver lo aplique a las 5.146 construcciones no está registrado como decisión.
- La cobertura de la llave no detiene Silver: si bajara de 0,80, el pipeline terminaría con `resultado_umbral` en «no pasa» y solo la prueba `test_cobertura_join_supera_umbral` fallaría después.
- No hay una validación explícita de columnas ni una prueba que simule un cambio de esquema de la fuente (sección 9 del documento de arquitectura).
- Las 18 reglas están repartidas en tres archivos de código: cambiar una regla cambia `reglas_silver.md`, `quality_report.json` y las entradas de Gold (ver ADR-014).

## Alternativas consideradas entonces
No se registraron alternativas.

## Alternativas que hoy descartamos y por qué
Razonamiento actual del equipo, no registrado en su momento.
- **Validar la calidad solo con pruebas de Gold.** Gold lee únicamente `silver_integrated.csv` (ADR-014): ahí no están las 23 filas resumen del CSV ni los 295 barrios sin construcciones, y los 6 huérfanos a la izquierda llegan con `cruza_llave` falso pero sin su causa, que solo está en la columna `causa` de `silver_orphans_left.csv`. Una prueba de Gold no podría contarlos ni explicarlos.
- **Una herramienta externa de calidad de datos.** `requirements.txt` fija 26 paquetes con `==` y ninguno es de ese tipo; sumar una obligaría a fijar su versión (D81, ADR-007). Las 18 reglas dependen de hallazgos propios de estas fuentes y no evaluamos ninguna herramienta en concreto, así que no afirmamos qué cubriría.
