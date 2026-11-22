# Resultados, lectura y alcance

Este documento reúne el análisis del proyecto: el contexto del evento, la pregunta de negocio, las fuentes, lo que hace cada capa, cómo leer los indicadores, los resultados, las limitaciones y el glosario. Las cifras salen de los archivos de salida (`data/gold/`, `data/silver/quality_report.json` y `data/bronze/manifest.jsonl`) y `tests/test_resultados_cifras.py` comprueba que coincidan. La definición de cada indicador está en [KPIs.md](KPIs.md); el resumen del proyecto y la forma de ejecutarlo, en el [README](../../README.md).

## 1. Contexto del problema
**El evento.** El 10-08-2026 a las 12:34:28 UTC (07:34:28 hora de Colombia) ocurrió un sismo de magnitud Mww 7,4 (identificador USGS `us6000tjl2`), con epicentro "4 km SSW of San José del Palmar" (Chocó), en 4,8601° N y 76,2558° O. La profundidad vigente en el catálogo USGS al 15-oct-2026 es de 116,13 km (registro actualizado el 2026-10-12); esta cifra ha tenido revisiones. Fuente: USGS FDSN Event, `https://earthquake.usgs.gov/fdsnws/event/1/` (muestra en `docs/bronze/muestras/v10_usgs_11.csv`, consulta del 15-oct-2026).

**Por qué importa Cali.** Cali fue una de las ciudades con mayor nivel de afectación. Las cifras oficiales cambian con el tiempo: el Avance 1 usó el corte del 18 de agosto de la Alcaldía (878 edificaciones verificadas de 5.545 reportes ciudadanos; 24 colapsos totales, 127 parciales y 192 con daño estructural), y reportes posteriores hablan de miles de predios evaluados. Por eso en este proyecto cada cifra lleva su fecha de corte. Según la Alcaldía (El País Cali, 11-oct-2026), las zonas más golpeadas fueron Cuarto de Legua, La Flora, comunas 19, 17 y 2.

**Lo que decía el Avance 1.** Había un patrón visible a simple vista: barrios como Capri, Guadalupe, Pampalinda, Tequendama, San Fernando y Cuarto de Legua, de estratos 3 a 5 y con construcciones antiguas, aparecían muy afectados. La hipótesis era que el daño lo explican mejor los factores geotécnicos y constructivos de cada zona que el estrato socioeconómico, pero **no estaba comprobada** (`docs/proyecto/comprension_proyecto1.md`).

## 2. Pregunta de negocio y alcance
> **En las construcciones evaluadas por satélite en 7 comunas de Cali tras el sismo, ¿la proporción con cambio satelital severo (severo estricto, proxy de daño) cambia entre los estratos 1-6 de su barrio, o se concentra por zona?**

Es la porción del Proyecto 1 que se puede medir hoy con datos abiertos estructurados: el estrato es la única variable de control con fuente tabular, y la capa satelital es la única fuente abierta a nivel de construcción. El costo es que el indicador es un proxy satelital y no una evaluación estructural (ATC-20) de la Alcaldía; no los mezclamos (ver la tabla «Indicador satelital frente a evaluación estructural»).

| KR | estado | evidencia |
|---|---|---|
| KR1 concentración de daño severo (proxy satelital) | parcial | K3 y K6; solo 7 comunas |
| KR2 contraste con amenaza sísmica oficial | no cubierto | no se usó amenaza sísmica oficial; trabajo futuro |
| KR3 antigüedad constructiva | fuera de alcance | cualitativo, no es ETL |
| KR4 daño por estrato | cubierto con el proxy satelital | K1 y K2 |
| KR5 avance de verificación | fuera de alcance | seguimiento, no es ETL |

### Alcance temporal
> **Alcance temporal.** El estrato por barrio es de **2015** (DAPM Cali, medido en lados de manzana). Las construcciones se evaluaron con imágenes del **2026-03-22** y del **2026-08-11**, y la capa se editó por última vez el **2026-09-02** (`config/config.yaml`, sección `fechas`). Los polígonos de barrios que usamos para validar son de 2026 y están renumerados respecto a 2015 (H13, H18). Entre el estrato y las imágenes hay unos **once años** de distancia. **Regla de lectura:** los resultados por estrato describen el estrato de 2015 asignado al barrio, no el estrato vigente. Lo que cambió en los barrios entre 2015 y 2026 es **desconocido** para nosotros y no lo estimamos.

### Población analizada
> **Población analizada.** **5.146** construcciones (**4.711** con datos satelitales) de **7 comunas** de Cali (03, 09, 10, 17, 18, 19 y 20), repartidas en **52** códigos de barrio. Criterio de inclusión: la capa solo incluye construcciones dentro de los polígonos de afectación preliminar del visor de emergencia del IGAC, según la descripción del dataset. Quedan fuera las comunas ausentes, entre ellas la **Comuna 2** (la Alcaldía la mencionó entre las de mayor pérdida), y la zona rural. **Regla:** las tasas describen esta muestra; no se extrapolan a las construcciones de Cali ni a la ciudad.

### Indicador satelital frente a evaluación estructural
| aspecto | indicador satelital (este proyecto) | evaluación estructural (ATC-20, Alcaldía de Cali) |
|---|---|---|
| qué es | cambio de textura entre dos imágenes de satélite sobre la huella de la construcción; el severo estricto es la clase "Alta probabilidad de escombros" | inspección técnica en sitio que clasifica el predio con un sticker: rojo (inseguro), amarillo (uso restringido) o verde |
| quién lo produce | Fondo Adaptación (capa catalogada en datos.gov.co, `5vy8-gpw8`) | Alcaldía de Cali |
| cómo se obtiene | análisis de imágenes del 2026-03-22 y 2026-08-11, sin inspección directa | evaluación directa de cada predio |
| qué ve y qué no ve | ve cambio visible desde arriba; no ve daño interno ni daño sin cambio visible, y no da seguridad de uso | evalúa la seguridad de uso del predio; no tenemos sus datos por predio |
| unidad de análisis | construcción (huella catastral) | predio |
| cobertura | 5.146 construcciones de 7 comunas, dentro de los polígonos de afectación preliminar | 3.403 predios caracterizados (no conocemos su distribución por comuna) |
| cifras disponibles | 4.711 con datos satelitales; 296 severos estrictos (6,28 %) | 3.403 predios: 1.078 rojo, 1.272 amarillo y 1.053 verde, publicado por El País Cali el 23-sep-2026 (https://www.elpais.com.co/cali/alcaldia-de-cali-entrega-balance-de-gestion-tras-el-sismo-mas-de-3400-edificaciones-evaluadas-y-45000-familias-damnificadas-2338.html) |
| uso en este proyecto | es la base de todos los KPI de Gold | solo contexto: no se compara ni se mezcla con ninguna cifra de Gold |

Las cifras de la evaluación estructural son cifras reportadas por la prensa citando a la Alcaldía; no las cotejamos con una fuente oficial descargable. La unidad (predios) no es la nuestra (construcciones), por lo que no las comparamos ni las mezclamos con ninguna cifra de Gold.

## 3. Mapa del flujo
```
 API (ArcGIS) ─┐                                                              ┌─ gold_final.csv
               ├─> BRONZE ──> SILVER ──> JOIN por código de barrio ──> GOLD ──┼─ kpis_gold.csv, kpis_sensibilidad.csv
 CSV estrato ──┘  (crudo)    (limpio)   (LEFT, con huérfanos)                  └─ etl_sismo.db (SQLite)
                                          VALIDACIÓN: pruebas, recálculo SQL, evidencias en docs/
```
| capa | entra | qué se hace | sale |
|---|---|---|---|
| **Bronze** | la capa ArcGIS (API), el CSV de estrato y los polígonos de barrios | se guarda tal como llegó, con sha256 y manifiesto | `data/bronze/api/…/page_000N.json`, `data/bronze/tabular/…csv`, `data/bronze/geo/…geojson`, `data/bronze/manifest.jsonl` |
| **Silver** | Bronze (solo lectura) | duplicados, nulos, tipos y formatos, llave, JOIN y validación de calidad | `silver_construcciones.csv`, `silver_estrato_barrio.csv`, `silver_integrated.csv`, `silver_orphans_left.csv`, `silver_orphans_right.csv`, `quality_report.json` |
| **Gold** | `silver_integrated.csv` (nunca Bronze) | indicadores, intervalos, cotas y sensibilidades | `gold_final.csv`, `kpis_gold.csv`, `kpis_sensibilidad.csv`, `etl_sismo.db` |
| **Validación** | todo lo anterior | pruebas, recálculo independiente con SQL, verificación de sha256, notebooks | `docs/`, `notebooks/`, `tests/` |

## 4. Fuentes de datos
Todas se consultaron el 15-oct-2026 (hora de Bogotá). El snapshot de Bronze del manifiesto está en UTC: **2026-10-16 00:10:24 UTC (2026-10-15 19:10:24 hora de Bogotá)**.

### 5.1 Capa de impacto satelital en construcciones (API)
- **Qué es:** "Impacto Satelital en Edificaciones por Terremoto. Cali 2026". Analiza la huella de cada construcción de la capa catastral "Construcciones" (Geoportal Catastral Cali, 2024) y calcula el diferencial de textura entre una imagen anterior (2026-03-22) y una posterior (2026-08-11). Solo incluye construcciones dentro de los polígonos de afectación preliminar del visor de emergencia del IGAC.
- **Quién la publica y cómo se accede:** Fondo Adaptación, catalogada en datos.gov.co (`5vy8-gpw8`, publicada 2026-09-03). El endpoint Socrata del catálogo **no es tabular**: es un enlace federado (`assetType: federated_href`, `columns: []`) y `/resource/5vy8-gpw8.json` responde HTTP 403 ("no row or column access to non-tabular tables"). Por eso usamos el **FeatureServer de ArcGIS** al que enlaza el propio catálogo (`https://services3.arcgis.com/Hf3YbZrlZ0OA2COM/arcgis/rest/services/Impacto_Satelital_en_Edificaciones_por_Terremoto_Cali_2026/FeatureServer/0`): es la misma capa, con paginación (`resultOffset`, máximo 2.000 filas por página) y sin token.
- **Columnas que usamos:** `OBJECTID`, `COMUNA`, `BARRIO` (códigos catastrales de 2 dígitos, no nombres), `NPISOS`, `Indice_Escombros`, `Estado_Estructural` y la geometría (polígonos en EPSG:4326).
- **Última edición:** 2026-09-02 (hora de Bogotá). **Atribución y licencia:** Fondo Adaptación; CC BY 4.0 según los metadatos del catálogo (`https://creativecommons.org/licenses/by/4.0`); licencia no declarada en el servicio ArcGIS (su `copyrightText` está vacío).

### 5.2 Estratificación por barrio 2015 (archivo tabular)
- **Qué es:** "Estratificación socioeconómica según estrato, por barrio en Cali 2015": para cada barrio, el número de lados de manzana en cada estrato (1 a 6), los lados sin vivienda y el estrato moda.
- **Quién la publica y cómo se accede:** Departamento Administrativo de Planeación Municipal (DAPM) de Cali; publicada 2018-10-30, última actualización 2019-07-08. El catálogo de datos.gov.co enlaza al portal datos.cali.gov.co, de donde descargamos el CSV con un `User-Agent` (la descarga directa `rows.csv` de datos.gov.co falla porque es un enlace federado).
- **Columnas:** `Código único` (llave), `Barrio`, `Lados de manzana por estrato 1…6`, `Sin vivienda`, `Estrato moda`. Tiene 369 filas: 346 barrios y 23 filas resumen (22 comunas y "Otros").
- **Por qué CSV y no Excel:** el requisito del curso admite CSV o Excel y esta tabla solo se publica como CSV. El módulo se llama `extract_excel.py` porque su lector (`leer_tabular_raw`) soporta los dos formatos (CSV y `.xlsx` vía `openpyxl`).
- **Licencia:** el CSV figura como Creative Commons Attribution Share-Alike en datos.cali.gov.co y como CC0 en datos.gov.co (`docs/bronze/muestras/v4_ckan_licencia.txt`); atribuimos a DAPM Cali. Gold contiene datos derivados de este CSV (por ejemplo el estrato de cada construcción); los datos derivados se comparten con atribución a DAPM Cali y bajo la misma licencia.

### 5.3 Polígonos de barrios (solo validación)
Servicio WFS del IDESC / DAPM Cali (`https://ws-idesc.cali.gov.co/geoserver/dapm/ows`, capa `dapm:pdt_dpa_barrios_sectores`), pedido en EPSG:4326: 342 polígonos (324 barrios y 18 sectores). Los usamos para comprobar la llave, no para el JOIN. Licencia no verificada.

### 5.4 USGS (solo contexto)
La consulta de USGS devuelve 11 eventos y no trae ninguna llave hacia un barrio o municipio (solo un texto con el lugar), por lo que no puede entrar al JOIN. Solo describimos el evento en este documento. Licencia no verificada.

## 5. Capa Bronze
**Qué guardamos.** La respuesta cruda de cada petición, byte a byte: 3 páginas de la API (2.000, 2.000, 1.146 filas; 4,4 MB en total), los conteos oficiales de la capa antes y después de descargar (5.146 y 5.146), el metadato de la capa (`capa_meta.json`: campos, fecha de edición y extensión), el CSV original (16.030 bytes) y los polígonos (1.850.751 bytes).

**Por qué es inmutable.** Si Bronze cambiara, no podríamos demostrar de dónde salió cada cifra. Los archivos se abren en modo exclusivo (`"xb"`): un archivo existente nunca se sobrescribe. No se renombran columnas, no se parsean fechas, no se corrigen tipos ni se eliminan filas.

**El manifiesto.** `data/bronze/manifest.jsonl` tiene una línea por archivo con `source_id`, `url`, `params`, `fetched_at_utc`, `http_status`, `rows`, `bytes`, `sha256` y `path`. Nunca incluye tokens. Se verifica en PowerShell comparando el hash de cada archivo con el del manifiesto (debe imprimir `True` en las 8 líneas):
```powershell
Get-Content data\bronze\manifest.jsonl | ForEach-Object { $m = $_ | ConvertFrom-Json; $h = (Get-FileHash $m.path -Algorithm SHA256).Hash.ToLower(); "{0}  {1}" -f ($h -eq $m.sha256), $m.path }
```
**Repetir sin duplicar.** Si Bronze ya existe, `python main.py --stage extract` verifica los sha256 y escribe "ya existe, sha256 coincide": no crea archivos ni agrega líneas al manifiesto. **Refresco.** `python main.py --stage extract --refresh` (necesita red) crea un snapshot nuevo `snap_<fecha UTC>` sin tocar el anterior. Una extracción se considera completa solo si existe el conteo posterior; las páginas se leen con `resultOffset` y orden estable por `OBJECTID`.

## 6. Capa Silver
Silver solo lee Bronze y escribe tablas limpias. Cada regla cita el hallazgo del análisis exploratorio (`docs/silver/hallazgos_eda.md`, H1-H18) que la justifica; sin hallazgo no hay regla. Las 18 reglas (R01-R18, `docs/silver/reglas_silver.md`), agrupadas por tema, con su hallazgo y las filas que afectan:

- **Identificadores y duplicados.** (R01, H1, 0 filas) Identificador = OBJECTID (único); la llave catastral se repite por predio con varias construcciones y no se deduplica. (R03, H2, 18 filas) Bandera para las construcciones con geometría idéntica a otra; se conservan las filas. (R11, H6, 23 filas) Filas 'Comuna N' y 'Otros' (código '-') se separan; no entran al JOIN.
- **Nulos.** (R02, H4, 2 filas (4 celdas)) Texto vacío o solo espacios pasa a nulo; no se imputa. (R05, H9, H12, 435 filas) 'Sin datos satelitales' queda como clase propia (no es 'sin daño'); sale del denominador. (R06, H10, 4.711 filas) Banderas D7; nulas (no falsas) cuando no hay datos satelitales. (R14, H8, 6 filas) estrato = moda solo si es 1-6; 'NR' queda nulo y no se convierte en estrato.
- **Tipos y formatos.** (R04, H9, 5.146 filas) Etiqueta de Estado_Estructural a 4 clases estables; Indice_Escombros no se imputa. (R07, H16, 1.234 filas) NPISOS a entero nullable sin imputar; bandera para 0 pisos; no se usa como filtro. (R12, H7, 342 filas) Guion y vacío = 0 lados, coma de miles eliminada, columnas a entero. (R13, H7, 26 filas) strip y espacios internos colapsados; el archivo se lee como UTF-8. (R15, H14, 343 filas) max(lados 1..6)/suma(lados 1..6) sin 'Sin vivienda'; nula si el total es 0.
- **Llave y ubicación espacial.** (R08, H5, 5.144 filas) Llave del JOIN = int(COMUNA)*100 + int(BARRIO) como texto; nula si falta COMUNA o BARRIO. (R09, H13, H18, 5.146 filas) Centroide de la huella (7 decimales) ubicado en los polígonos WFS 2026; solo valida la llave, no entra al JOIN.
- **JOIN y validación.** (R16, H5, H6, 5.140 filas) LEFT JOIN construcciones <- estrato por barrio; huérfanos guardados, no descartados. (R17, H11, 5.138 filas) Conteos por estrato sobre construcciones con datos satelitales y bandera de muestra baja (< 30 severos). (R18, H18, 5.140 filas) Validación semántica de la llave (nombre CSV vs nombre de polígono); no cambia la llave.
- **Columnas descartadas.** (R10, H3, H4, 5.146 filas) Se descartan columnas vacías, en grados o sin uso en Gold; ver docs/silver/hallazgos_eda.md.

### Duplicados: qué encontramos y qué decidimos
- `OBJECTID` es único: **0 duplicados eliminados** por esa llave (se aplica `duplicated(keep="first")` de forma explícita). La llave catastral (comuna, barrio, manzana, terreno, condición, edificio, predio) sí se repite en 3.719 filas porque un predio tiene varias construcciones; **no** se deduplica por ella (0 eliminadas). En el CSV, el código de barrio es único (0 eliminados).
- Hay **18 construcciones con geometría idéntica a otra (9 parejas)**. Las marcamos con `geom_duplicada` y las conservamos: tienen `OBJECTID` distinto y no hay evidencia de doble conteo (H2); eliminarlas sería arbitrario.

### Nulos
Texto vacío o solo espacios pasa a nulo real (`COMUNA` y `BARRIO`: 2 y 2 construcciones, que no se imputan y terminan como huérfanas). `Indice_Escombros` es nulo en 435 construcciones, exactamente las de "Sin datos satelitales": no se imputa y esas construcciones salen del denominador de las tasas. Las banderas `severo_estricto` y `dano_visible` son **nulas, no falsas**, cuando no hay datos. `NPISOS` queda como entero nullable (11 nulos). En el CSV, un guion o un vacío en los lados de manzana vale 0, y el estrato moda `NR` queda como estrato nulo.

### La llave del JOIN
Las construcciones no traen el nombre del barrio, solo `COMUNA` y `BARRIO` (dos dígitos cada uno), y el CSV trae un `Código único`. La llave es `int(COMUNA)*100 + int(BARRIO)` como texto sin ceros a la izquierda. Ejemplo real: una construcción con comuna `19` y barrio `04` tiene la llave `1904`, que en el CSV corresponde a "Urbanización Tequendama" (estrato moda 5). Es un `LEFT JOIN` desde las construcciones, para que ninguna construcción desaparezca aunque no tenga estrato.

### Las tres coberturas
1. **Cobertura de llave: 99,883 %** (5.140 de 5.146): construcciones cuya llave existe en el CSV. Es la que se compara con el umbral (0,80): pasa.
2. **Cobertura de estrato válido: 99,845 %** (5.138): además de existir la llave, el barrio tiene un estrato moda entre 1 y 6 (se excluyen los barrios `NR`).
3. **Nombre validado: 93,521 %** (4.807 de 5.140): el nombre del barrio en el CSV de 2015 coincide (similitud ≥ 0,85) con el del polígono 2026 donde cae la construcción. Es un control de la llave, no un filtro; `llave_confianza` = **alta** (`docs/silver/validacion_llave.md`).

### Huérfanos
Se guardan, no se descartan. A la izquierda (`silver_orphans_left.csv`): 6 construcciones sin llave en el CSV (COMUNA o BARRIO en blanco: 2; código ausente del CSV 2015: 4). A la derecha (`silver_orphans_right.csv`): 295 barrios del CSV sin ninguna construcción, esperable porque la capa solo cubre 7 comunas.

### Por qué los polígonos 2026 no son la llave
El código derivado coincide con el código del polígono 2026 en 91,43 % de las construcciones. La diferencia se debe sobre todo a renumeración de códigos entre 2015 y 2026: entre las construcciones que no coinciden con el polígono, el 95,19 % tiene el nombre validado, es decir, es el mismo barrio con otro código. Por eso la llave es el código catastral que sí existe en el CSV de 2015 y los polígonos solo validan.

**Lectura de las construcciones sin nombre validado.** De las 333 construcciones sin nombre validado, 244 (73,3 %) corresponden a diferencias de escritura (prefijos como «Barrio» o «Sector», abreviaturas), 73 (21,9 %) a nombres ampliados o cambiados y 16 (4,8 %) a un posible cambio de límites (código 2098). Si se aceptaran las de la primera categoría, el porcentaje de nombre validado sería 98,27 %; conservamos 93,52 % porque el umbral de similitud se fijó antes de ver los resultados y no se ajusta a posteriori. La revisión visual de estos códigos sobre el mapa sigue pendiente.

**Revisión de los códigos con diferencias.** Revisamos uno por uno los 7 códigos sin nombre validado, el código 1920 y las 2 construcciones sin comuna ni barrio, sin cambiar ninguna columna ni cifra: [docs/silver/revision_codigos_barrio.md](../silver/revision_codigos_barrio.md). La revisión visual en el mapa sigue pendiente.

## 7. Capa Gold
**`gold_final.csv`** tiene **5.146 filas**, una por construcción (`objectid` único), sin duplicados. **`kpis_gold.csv`** tiene 23 filas con los indicadores K1-K6 (valor, numerador, denominador, grupo, fecha de corte, intervalo de Wilson, cotas por "sin datos", bandera de muestra baja y una nota). **`kpis_sensibilidad.csv`** repite K1, K2 y K6 en seis escenarios (S0-S5, 107 filas). **`etl_sismo.db`** (SQLite) tiene las tablas `gold_final`, `kpis_gold`, `kpis_sensibilidad`, `silver_integrated`.

Diccionario de columnas de `gold_final.csv`:

| columna | descripción |
|---|---|
| `objectid` | identificador de la construcción (único) |
| `comuna`, `barrio` | códigos catastrales de 2 dígitos (texto; nulos si venían en blanco) |
| `codigo_barrio` | llave `int(comuna)*100 + int(barrio)` (texto) |
| `nombre_barrio_csv` | nombre del barrio en el CSV de estrato 2015 (nulo si no cruza) |
| `cruza_llave` | la llave existe en el CSV de estrato |
| `estrato` | estrato moda del barrio (1-6; nulo si NR o sin llave) |
| `pureza_estrato` | max(lados 1..6)/suma(lados 1..6) del barrio, sin "Sin vivienda" |
| `n_con_datos_estrato`, `n_severos_estrato`, `muestra_baja` | conteos por estrato (construcciones con datos) y bandera k < 30 |
| `npisos`, `npisos_cero` | número de pisos (entero nullable) y bandera de 0 pisos |
| `indice_escombros` | índice continuo de cambio de textura (nulo si sin datos) |
| `estado_estructural`, `clase_dano` | etiqueta original y clase (`escombros`, `techo`, `sin_cambio`, `sin_datos`) |
| `sin_datos` | sin datos satelitales |
| `severo_estricto`, `dano_visible` | banderas D7; **nulas** (no falsas) si `sin_datos` |
| `geom_duplicada` | comparte geometría idéntica con otra construcción (18 filas, 9 pares) |
| `lon`, `lat` | centroide a 7 decimales (EPSG:4326) |
| `codigo_poligono`, `nombre_poligono`, `coincide_poligono` | polígono WFS 2026 donde cae el centroide y si su código coincide con `codigo_barrio` |
| `nombre_validado` | el nombre CSV 2015 coincide (similitud ≥ 0,85) con el polígono dominante del código |

Ejemplo de consulta (se ejecuta con `sqlite3` o con `pandas.read_sql_query`); devuelve, por estrato, los severos y las construcciones con datos satelitales:
```sql
SELECT estrato, SUM(severo_estricto) AS severos, COUNT(severo_estricto) AS con_datos
FROM gold_final WHERE estrato IS NOT NULL GROUP BY estrato ORDER BY estrato;
```
Resultado (estrato | severos | con_datos):
```
1 | 20 | 302
2 | 3 | 92
3 | 74 | 1173
4 | 145 | 2095
5 | 53 | 1031
6 | 0 | 11
```

## 8. Cómo leer los resultados
- **(a) Tasa de severos estrictos.** Es k / n, con k = construcciones con cambio satelital severo (severo estricto, proxy de daño: clase "Alta probabilidad de escombros") y n = construcciones **con datos satelitales** del grupo. Las "Sin datos satelitales" salen del denominador y se reportan aparte; nunca se tratan como "sin daño".
- **(b) Intervalo de Wilson.** Una tasa calculada sobre una muestra es incierta; el intervalo de Wilson al 95 % da el rango de valores compatibles con lo observado. Ejemplo real (K1, estrato 1): 20 severas de 302 = 6,62 %, intervalo 4,33 % – 10,01 %. Con pocos casos el intervalo es ancho; con muchos, angosto.
- **(c) Cotas por "sin datos satelitales".** Para cada grupo, la cota inferior supone que todas las construcciones sin datos no son severas, y la superior que todas lo son: `k/(n + sin datos)` y `(k + sin datos)/(n + sin datos)`. Son extremos poco realistas, pero muestran cuánto podría mover el resultado la falta de datos. El estrato 2 es especial: 27,0 % de sus construcciones no tiene datos, y su cota va de 2,4 % a 29,4 %. Si las cotas de dos grupos se solapan, el orden entre ellos no es identificable.
- **(d) Muestra baja.** Un grupo tiene muestra baja si tiene menos de 30 severos; sus tasas son inestables y se marcan.
- **(e) Intervalo de Newcombe de la diferencia (K2).** K2 compara los estratos 3-5 con los 1-2 y reporta la diferencia de tasas con un intervalo de Newcombe. Si el intervalo incluye 0 (aquí −2,36 a +2,55 puntos porcentuales), los datos son compatibles con que no haya diferencia, y la redacción permitida es "con este proxy y esta muestra no se detecta diferencia"; nunca "el estrato no influye".
- **(f) Mantel-Haenszel.** Calcula una razón de tasas ajustada por comuna, para quitar el efecto de la ubicación. Aquí **no es interpretable**: solo la Comuna 18 tiene construcciones con datos en ambos grupos (44 expuestas y 52 de referencia), y el valor (1,970) descansa en esas 96 construcciones. Es una señal de que estrato y ubicación están confundidos, no un resultado.
- **(g) K3, K4 y K5.** *K3 (concentración):* qué porcentaje de las construcciones severas está en los 10 barrios con más severos. *K4 (Spearman):* correlación de rangos entre el estrato moda de un barrio y su tasa de severos, para barrios con al menos 10 construcciones con datos; es descriptiva, a nivel de barrio. *K5 (calidad del JOIN):* las tres coberturas de la sección 6.

## 9. Resultados
> **Recordatorio.** Los resultados por estrato describen el estrato de 2015 asignado al barrio, no el vigente (ver «Alcance temporal»), y las tasas describen las 4.711 construcciones con datos de 7 comunas, no las de Cali (ver «Población analizada»).

### Respuesta a la pregunta de negocio
(a) Con este proxy y esta muestra no se detecta diferencia en la proporción de construcciones con cambio satelital severo (severo estricto, proxy de daño) entre los estratos 3-5 y 1-2 (6,33 % frente a 5,84 %; diferencia +0,49 puntos porcentuales).
(b) Los datos son compatibles con diferencias entre −2,36 y +2,55 puntos porcentuales (intervalo de Newcombe al 95 %).
(c) Esto no equivale a decir que el estrato no influye.
(d) El signo de la diferencia no es estable entre escenarios (negativo en: S3) y la razón ajustada por comuna (1,97) solo usa la Comuna 18 (44 construcciones expuestas y 52 de referencia), por lo que no es interpretable.
(e) Las tasas por comuna oscilan entre 3,80 % (C09) y 8,33 % (C18) (ambas con muestra baja: 7 y 8 severos); todos los intervalos de Wilson comparten un tramo común (5,43 % a 7,20 %).
(f) La Comuna 19 concentra 61,7 % de los severos y 61,8 % de las construcciones con datos (comunas asignadas), así que la concentración se explica por tamaño en esta muestra.

No concluimos causalidad ni validamos o refutamos la hipótesis geotécnica del Avance 1.

### K1 · Tasa por estrato (fecha de corte 2026-09-02)
| estrato | n con datos | severos | tasa | IC 95 % Wilson | % sin datos | cotas por sin datos | muestra baja |
|---|---|---|---|---|---|---|---|
| E1 | 302 | 20 | 6,62 % | 4,33 % – 10,01 % | 10,7 % | 5,9 % – 16,6 % | sí |
| E2 | 92 | 3 | 3,26 % | 1,12 % – 9,15 % | 27,0 % | 2,4 % – 29,4 % | sí |
| E3 | 1.173 | 74 | 6,31 % | 5,05 % – 7,85 % | 8,5 % | 5,8 % – 14,3 % | no |
| E4 | 2.095 | 145 | 6,92 % | 5,91 % – 8,09 % | 7,6 % | 6,4 % – 14,0 % | no |
| E5 | 1.031 | 53 | 5,14 % | 3,95 % – 6,66 % | 7,5 % | 4,8 % – 12,2 % | no |
| E6 | 11 | 0 | 0,00 % | 0,00 % – 25,88 % | 0,0 % | 0,0 % – 0,0 % | sí |

### K2-K5
- Tasa estratos 3-5: 272/4.299 = 6,33 %; estratos 1-2: 23/394 = 5,84 % (muestra baja); razón 1,084; diferencia +0,49 pp, Newcombe [−2,36; +2,55]. E6 queda fuera de K2 (11 construcciones).
- K3: los 10 barrios con más severos reúnen 167 de 295 severos (56,6 %); esos 10 barrios reúnen 48,7 % de las construcciones con datos; concentración de casos no es mayor riesgo.
- K4: Spearman entre estrato moda y tasa por barrio = 0,035 (n = 45 barrios; p de permutación = 0,8218); descriptivo.
- K5 (calidad del JOIN): cobertura de llave 99,883 %; cobertura de estrato válido 99,845 %; nombre validado 93,521 %.

### K6 · Tasa por comuna
| comuna | n con datos | severos | tasa | IC 95 % Wilson | % de los severos | % de las construcciones | muestra baja |
|---|---|---|---|---|---|---|---|
| C03 | 550 | 39 | 7,09 % | 5,23 % – 9,55 % | 13,2 % | 11,7 % | no |
| C09 | 184 | 7 | 3,80 % | 1,85 % – 7,64 % | 2,4 % | 3,9 % | sí |
| C10 | 541 | 35 | 6,47 % | 4,69 % – 8,86 % | 11,9 % | 11,5 % | no |
| C17 | 87 | 4 | 4,60 % | 1,80 % – 11,23 % | 1,4 % | 1,8 % | sí |
| C18 | 96 | 8 | 8,33 % | 4,28 % – 15,59 % | 2,7 % | 2,0 % | sí |
| C19 | 2.909 | 182 | 6,26 % | 5,43 % – 7,20 % | 61,7 % | 61,8 % | no |
| C20 | 342 | 20 | 5,85 % | 3,82 % – 8,86 % | 6,8 % | 7,3 % | sí |

### Sensibilidades S0-S5
Repiten K2 cambiando una decisión cada vez. En todos los escenarios el intervalo de la diferencia incluye 0.

| escenario | qué cambia | tasa 3-5 | tasa 1-2 | diferencia [Newcombe] (pp) | RR Mantel-Haenszel |
|---|---|---|---|---|---|
| S0 | base (todas las construcciones con estrato válido) | 6,33 % | 5,84 % | +0,49 [−2,36; +2,55] | 1,970 |
| S1 | solo `nombre_validado = true` (sensibilidad principal de la llave) | 6,28 % | 6,12 % | +0,17 [−2,81; +2,32] | 2,315 |
| S2 | solo `coincide_poligono = true` (secundaria; no sustituye a S1) | 6,41 % | 6,13 % | +0,28 [−2,96; +2,55] | no calculable |
| S3 | solo `pureza_estrato ≥ 0,8` | 6,64 % | 7,51 % | −0,87 [−4,88; +1,94] | 1,894 |
| S4 | `dano_visible` en lugar de `severo_estricto` (baja confianza) | 28,91 % | 26,90 % | +2,01 [−2,77; +6,37] | 1,397 |
| S5 | sin construcciones con `geom_duplicada` | 6,30 % | 5,88 % | +0,42 [−2,45; +2,50] | 1,894 |

### Composición del grupo de estratos 1-2 (construcciones con datos / severos)
| comuna | 1-2: n / severos | 3-5: n / severos | 6: n / severos |
|---|---|---|---|
| 03 | 0 / 0 | 550 / 39 | 0 / 0 |
| 09 | 0 / 0 | 184 / 7 | 0 / 0 |
| 10 | 0 / 0 | 541 / 35 | 0 / 0 |
| 17 | 0 / 0 | 87 / 4 | 0 / 0 |
| 18 | 52 / 3 | 44 / 5 | 0 / 0 |
| 19 | 0 / 0 | 2893 / 182 | 11 / 0 |
| 20 | 342 / 20 | 0 / 0 | 0 / 0 |

Nota: 5 construcciones con datos satelitales no tienen estrato válido (Comuna 19: 5); por eso la suma de la tabla (4.704) es menor que el total con datos y comuna asignada (4.709).

El grupo de estratos 1-2 está formado, casi por completo, por las Comunas 20 y 18; K2 compara en la práctica la Comuna 20 con el resto de la muestra.

### Interpretación honesta
**Se puede afirmar:** con este proxy y esta muestra no detectamos diferencia entre los estratos 3-5 y 1-2; la proporción de construcciones con cambio visible severo ronda 6,3 % y no varía de forma clara entre estratos ni entre comunas; la concentración de severos en la Comuna 19 coincide con su tamaño. **No se puede afirmar:** que el estrato no influya, que el cambio satelital severo sea mayor o menor en algún estrato, ni nada sobre las causas (geotécnicas o constructivas). El indicador es un proxy que mide cambio visible desde satélite, no una evaluación estructural, la muestra la definieron los polígonos de afectación y el estrato está asignado por barrio.

## 10. Limitaciones y alcance
1. El proxy mide **cambio visible desde satélite**, no daño interno ni el de construcciones de varios pisos sin cambio visible; no sustituye la inspección ATC-20.
2. Solo hay **7 comunas** (03, 09, 10, 17, 18, 19, 20); la **Comuna 2 no está**. Las tasas describen esta muestra; no se extrapolan a las construcciones de Cali ni a la ciudad. La Alcaldía de Cali mencionó la Comuna 2 entre las de mayor pérdida de daños (El País Cali, 11-oct-2026: https://www.elpais.com.co/cali/tras-el-sismo-cali-evalua-miles-de-estructuras-y-alista-la-reconstruccion-el-plan-es-que-de-aqui-a-diciembre-se-coloque-el-primer-ladrillo-1159.html); esa comuna no está en la capa satelital.
3. **E2 tiene ≈ 27 % sin datos** y la falta de datos no es aleatoria; sus cotas (2,4 %-29,4 % de severos) no permiten ordenar E2 frente a otros estratos.
4. **Estratos con muestra baja** (k < 30): E1, E2, E6 y el grupo 1-2 de K2 (23 severos); también C09, C17, C18 y C20 en K6.
5. El estrato es de **2015, por lados de manzana, asignado a todo el barrio** (falacia ecológica); 1.480 construcciones están en barrios con pureza de estrato < 0,8.
6. `dano_visible` es de **baja confianza** (22,5 % de las construcciones con datos son "techo"; imágenes separadas ≈ 4,5 meses y sin grupo de control).
7. **Asociación no es causa.** Con este proxy y esta muestra no se detecta diferencia entre estratos, y eso no equivale a decir que el estrato no influye.
8. El grupo de estratos 1-2 está formado, casi por completo, por la Comuna 20 (342 construcciones, 20 severos) y la Comuna 18 (52, 3); K2 compara en la práctica la Comuna 20 con el resto de la muestra, y la razón ajustada por comuna solo puede usar la Comuna 18.

Además: la capa viene de un servicio ArcGIS Online de un tercero y puede cambiar; la **reproducibilidad la garantiza el snapshot de Bronze con su manifiesto y sha256**, no el servicio. El estrato es de **2015** y se mide en **lados de manzana**, no por construcción.

## 11. Glosario
- **Construcción:** huella catastral de una edificación (una fila de la capa); no es un edificio completo ni un predio.
- **Estrato moda:** el estrato con más lados de manzana en un barrio; se asigna a todas sus construcciones.
- **Lados de manzana:** unidad con la que el DAPM mide el estrato (un lado de manzana tiene un estrato).
- **Proxy satelital:** medida indirecta del daño: cambio de textura entre dos imágenes de satélite sobre la huella de la construcción; no es una inspección técnica ni una evaluación estructural.
- **Evaluación estructural (ATC-20):** inspección técnica en sitio, hecha por la Alcaldía sobre predios, que los clasifica con sticker rojo (inseguro), amarillo (uso restringido) o verde. No es nuestro indicador ni usamos sus datos por predio.
- **Intervalo de Wilson:** rango de valores compatibles con una proporción observada (95 %).
- **Intervalo de Newcombe:** el equivalente para la diferencia entre dos proporciones.
- **Mantel-Haenszel:** razón de tasas ajustada por una variable de estratificación (aquí, la comuna).
- **Spearman:** correlación entre los rangos de dos variables.
- **Huérfano:** fila de una tabla que no encuentra pareja en el JOIN; se conserva en un archivo aparte.
- **Snapshot:** copia fechada (UTC) de lo descargado; no se sobrescribe.
- **Medallion:** organización por capas (Bronze crudo, Silver limpio, Gold listo para análisis).
- **Avance 1:** documento de contexto y problema que dio origen al proyecto (`docs/proyecto/referencias/contexto_y_problema.pdf`).
- **API:** programa que responde consultas por HTTP; aquí entrega los resultados de Gold sin recalcularlos.
- **Endpoint:** una dirección concreta de la API, por ejemplo `/kpis`.
- **Solo lectura:** la API puede entregar los datos, pero no puede cambiarlos; la conexión a la base rechaza cualquier escritura.
- **Catálogo de metadatos:** ficha de cada fuente (publicador, URL, formato, licencia, fechas, columnas y huella del snapshot) generada desde el manifiesto.
- **Escáner de secretos:** script que busca credenciales en el repositorio, su historial y un zip; reporta archivo, línea y patrón, nunca el valor.
- **Corrida:** una carga completa a la base relacional; cada corrida distinta conserva todas sus filas y la historia es la suma de corridas.
- **Idempotente:** que repetir la operación con la misma entrada no cambia nada; la carga repetida responde «ya cargada».
- **Clave foránea:** regla de la base que impide que una fila apunte a otra que no existe.
- **Conciliación:** comparar lo cargado con los archivos de origen (conteos, huellas y cada valor) para demostrar que son iguales.
- **DAG:** grafo de tareas de Airflow que se ejecutan en un orden y sin ciclos; el nuestro tiene cuatro (`validar_bronze`, `transformar_a_silver`, `integrar_a_gold` y `cargar_datawarehouse`).
- **Orquestación:** programar, ejecutar y vigilar las tareas del pipeline con una herramienta (aquí Airflow en Docker) en lugar de lanzarlas a mano.
- **Copia de trabajo:** carpeta temporal dentro del contenedor donde el DAG produce sus salidas para compararlas con las versionadas sin escribir nunca en el repositorio.
- **Panel:** interfaz de usuario del proyecto; consume la API y nunca toca los datos directamente.
- **Streamlit:** biblioteca de Python con la que se escribe el panel como una aplicación web local.
- **AppTest:** herramienta de Streamlit para ejecutar una página en las pruebas, sin navegador, y revisar lo que muestra.
- **Lote (batch):** grupo de filas que se inserta en una sola operación; es más rápido que insertar fila por fila.
