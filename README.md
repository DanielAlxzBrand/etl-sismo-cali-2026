# ETL medallion del sismo M7.4 del 10 de agosto de 2026

**Autores:** Diego Fernando Gordillo Londoño, Jhoan Sebastián Castellanos Mayor y Daniel Alexander Brand García.
**Curso:** ETL · **Universidad:** Universidad Autónoma de Occidente (UAO).
**Entorno:** Python 3.13.0 en Windows (PowerShell).

Este repositorio contiene un pipeline ETL con arquitectura medallion (Bronze → Silver → Gold → Validación) que integra una API y un archivo tabular para estudiar, con un indicador satelital, el cambio visible en las construcciones de 7 comunas de Cali tras el sismo. Este documento explica el proyecto de principio a fin: el contexto, las fuentes, qué hace cada capa, cómo leer los resultados, cómo reproducirlos y qué no se puede concluir.

## 1. Título, autores y entorno
Ver el encabezado. Todo el código usa `pathlib` para las rutas y se probó en Windows con PowerShell; los comandos de este documento están escritos para PowerShell.

## 2. Contexto del problema
**El evento.** El 10-08-2026 a las 12:34:28 UTC (07:34:28 hora de Colombia) ocurrió un sismo de magnitud Mww 7,4 (identificador USGS `us6000tjl2`), con epicentro "4 km SSW of San José del Palmar" (Chocó), en 4,8601° N y 76,2558° O. La profundidad vigente en el catálogo USGS al 15-oct-2026 es de 116,13 km (registro actualizado el 2026-10-12); esta cifra ha tenido revisiones. Fuente: USGS FDSN Event, `https://earthquake.usgs.gov/fdsnws/event/1/` (muestra en `docs/bronze/muestras/v10_usgs_11.csv`, consulta del 15-oct-2026).

**Por qué importa Cali.** Cali fue una de las ciudades con mayor nivel de afectación. Las cifras oficiales cambian con el tiempo: el Avance 1 usó el corte del 18 de agosto de la Alcaldía (878 edificaciones verificadas de 5.545 reportes ciudadanos; 24 colapsos totales, 127 parciales y 192 con daño estructural), y reportes posteriores hablan de miles de predios evaluados. Por eso en este proyecto cada cifra lleva su fecha de corte. Según la Alcaldía (El País Cali, 11-oct-2026), las zonas más golpeadas fueron Cuarto de Legua, La Flora, comunas 19, 17 y 2.

**Lo que decía el Avance 1.** Había un patrón visible a simple vista: barrios como Capri, Guadalupe, Pampalinda, Tequendama, San Fernando y Cuarto de Legua, de estratos 3 a 5 y con construcciones antiguas, aparecían muy afectados. La hipótesis era que el daño lo explican mejor los factores geotécnicos y constructivos de cada zona que el estrato socioeconómico, pero **no estaba comprobada** (`docs/proyecto/comprension_proyecto1.md`).

## 3. Pregunta de negocio y alcance
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

## 4. Mapa del flujo
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

## 5. Fuentes de datos
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

## 6. Capa Bronze
**Qué guardamos.** La respuesta cruda de cada petición, byte a byte: 3 páginas de la API (2.000, 2.000, 1.146 filas; 4,4 MB en total), los conteos oficiales de la capa antes y después de descargar (5.146 y 5.146), el metadato de la capa (`capa_meta.json`: campos, fecha de edición y extensión), el CSV original (16.030 bytes) y los polígonos (1.850.751 bytes).

**Por qué es inmutable.** Si Bronze cambiara, no podríamos demostrar de dónde salió cada cifra. Los archivos se abren en modo exclusivo (`"xb"`): un archivo existente nunca se sobrescribe. No se renombran columnas, no se parsean fechas, no se corrigen tipos ni se eliminan filas.

**El manifiesto.** `data/bronze/manifest.jsonl` tiene una línea por archivo con `source_id`, `url`, `params`, `fetched_at_utc`, `http_status`, `rows`, `bytes`, `sha256` y `path`. Nunca incluye tokens. Se verifica en PowerShell comparando el hash de cada archivo con el del manifiesto (debe imprimir `True` en las 8 líneas):
```powershell
Get-Content data\bronze\manifest.jsonl | ForEach-Object { $m = $_ | ConvertFrom-Json; $h = (Get-FileHash $m.path -Algorithm SHA256).Hash.ToLower(); "{0}  {1}" -f ($h -eq $m.sha256), $m.path }
```
**Repetir sin duplicar.** Si Bronze ya existe, `python main.py --stage extract` verifica los sha256 y escribe "ya existe, sha256 coincide": no crea archivos ni agrega líneas al manifiesto. **Refresco.** `python main.py --stage extract --refresh` (necesita red) crea un snapshot nuevo `snap_<fecha UTC>` sin tocar el anterior. Una extracción se considera completa solo si existe el conteo posterior; las páginas se leen con `resultOffset` y orden estable por `OBJECTID`.

## 7. Capa Silver
Silver solo lee Bronze y escribe tablas limpias. Cada regla cita el hallazgo del análisis exploratorio (`docs/silver/hallazgos_eda.md`, H1-H18) que la justifica; sin hallazgo no hay regla. Las 18 reglas (R01-R18, `docs/silver/reglas_silver.md`), agrupadas por tema, con su hallazgo y las filas que afectan:

- **Identificadores y duplicados.** (R01, H1, 0 filas) Identificador = OBJECTID (único); la llave catastral se repite por predio con varias construcciones y no se deduplica. (R03, H2, 18 filas) Bandera para las construcciones con geometría idéntica a otra; se conservan las filas. (R11, H6, 23 filas) Filas 'Comuna N' y 'Otros' (código '-') se separan; no entran al JOIN.
- **Nulos.** (R02, H4, 4 filas) Texto vacío o solo espacios pasa a nulo; no se imputa. (R05, H9, H12, 435 filas) 'Sin datos satelitales' queda como clase propia (no es 'sin daño'); sale del denominador. (R06, H10, 4.711 filas) Banderas D7; nulas (no falsas) cuando no hay datos satelitales. (R14, H8, 6 filas) estrato = moda solo si es 1-6; 'NR' queda nulo y no se convierte en estrato.
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

**Revisión de los códigos con diferencias.** Revisamos uno por uno los 7 códigos sin nombre validado, el código 1920 y las 2 construcciones sin comuna ni barrio, sin cambiar ninguna columna ni cifra: [docs/silver/revision_codigos_barrio.md](docs/silver/revision_codigos_barrio.md). La revisión visual en el mapa sigue pendiente.

## 8. Capa Gold
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

## 9. Cómo leer los resultados
- **(a) Tasa de severos estrictos.** Es k / n, con k = construcciones con cambio satelital severo (severo estricto, proxy de daño: clase "Alta probabilidad de escombros") y n = construcciones **con datos satelitales** del grupo. Las "Sin datos satelitales" salen del denominador y se reportan aparte; nunca se tratan como "sin daño".
- **(b) Intervalo de Wilson.** Una tasa calculada sobre una muestra es incierta; el intervalo de Wilson al 95 % da el rango de valores compatibles con lo observado. Ejemplo real (K1, estrato 1): 20 severas de 302 = 6,62 %, intervalo 4,33 % – 10,01 %. Con pocos casos el intervalo es ancho; con muchos, angosto.
- **(c) Cotas por "sin datos satelitales".** Para cada grupo, la cota inferior supone que todas las construcciones sin datos no son severas, y la superior que todas lo son: `k/(n + sin datos)` y `(k + sin datos)/(n + sin datos)`. Son extremos poco realistas, pero muestran cuánto podría mover el resultado la falta de datos. El estrato 2 es especial: 27,0 % de sus construcciones no tiene datos, y su cota va de 2,4 % a 29,4 %. Si las cotas de dos grupos se solapan, el orden entre ellos no es identificable.
- **(d) Muestra baja.** Un grupo tiene muestra baja si tiene menos de 30 severos; sus tasas son inestables y se marcan.
- **(e) Intervalo de Newcombe de la diferencia (K2).** K2 compara los estratos 3-5 con los 1-2 y reporta la diferencia de tasas con un intervalo de Newcombe. Si el intervalo incluye 0 (aquí −2,36 a +2,55 puntos porcentuales), los datos son compatibles con que no haya diferencia, y la redacción permitida es "con este proxy y esta muestra no se detecta diferencia"; nunca "el estrato no influye".
- **(f) Mantel-Haenszel.** Calcula una razón de tasas ajustada por comuna, para quitar el efecto de la ubicación. Aquí **no es interpretable**: solo la Comuna 18 tiene construcciones con datos en ambos grupos (44 expuestas y 52 de referencia), y el valor (1,970) descansa en esas 96 construcciones. Es una señal de que estrato y ubicación están confundidos, no un resultado.
- **(g) K3, K4 y K5.** *K3 (concentración):* qué porcentaje de las construcciones severas está en los 10 barrios con más severos. *K4 (Spearman):* correlación de rangos entre el estrato moda de un barrio y su tasa de severos, para barrios con al menos 10 construcciones con datos; es descriptiva, a nivel de barrio. *K5 (calidad del JOIN):* las tres coberturas de la sección 7.

## 10. Resultados
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

## 11. Limitaciones y alcance
1. El proxy mide **cambio visible desde satélite**, no daño interno ni el de construcciones de varios pisos sin cambio visible; no sustituye la inspección ATC-20.
2. Solo hay **7 comunas** (03, 09, 10, 17, 18, 19, 20); la **Comuna 2 no está**. Las tasas describen esta muestra; no se extrapolan a las construcciones de Cali ni a la ciudad. La Alcaldía de Cali mencionó la Comuna 2 entre las de mayor pérdida de daños (El País Cali, 11-oct-2026: https://www.elpais.com.co/cali/tras-el-sismo-cali-evalua-miles-de-estructuras-y-alista-la-reconstruccion-el-plan-es-que-de-aqui-a-diciembre-se-coloque-el-primer-ladrillo-1159.html); esa comuna no está en la capa satelital.
3. **E2 tiene ≈ 27 % sin datos** y la falta de datos no es aleatoria; sus cotas (2,4 %-29,4 % de severos) no permiten ordenar E2 frente a otros estratos.
4. **Estratos con muestra baja** (k < 30): E1, E2, E6 y el grupo 1-2 de K2 (23 severos); también C09, C17, C18 y C20 en K6.
5. El estrato es de **2015, por lados de manzana, asignado a todo el barrio** (falacia ecológica); 1.480 construcciones están en barrios con pureza de estrato < 0,8.
6. `dano_visible` es de **baja confianza** (22,5 % de las construcciones con datos son "techo"; imágenes separadas ≈ 4,5 meses y sin grupo de control).
7. **Asociación no es causa.** Con este proxy y esta muestra no se detecta diferencia entre estratos, y eso no equivale a decir que el estrato no influye.
8. El grupo de estratos 1-2 está formado, casi por completo, por la Comuna 20 (342 construcciones, 20 severos) y la Comuna 18 (52, 3); K2 compara en la práctica la Comuna 20 con el resto de la muestra, y la razón ajustada por comuna solo puede usar la Comuna 18.

Además: la capa viene de un servicio ArcGIS Online de un tercero y puede cambiar; la **reproducibilidad la garantiza el snapshot de Bronze con su manifiesto y sha256**, no el servicio. El estrato es de **2015** y se mide en **lados de manzana**, no por construcción.

## 12. Cómo reproducir
1. **Entorno** (PowerShell, en la raíz del repositorio):
```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```
Debe terminar sin errores (Python 3.13.0).
2. **Variables:** el pipeline no necesita tokens; `HTTP_USER_AGENT` es opcional. Las variables `MYSQL_*` solo se usan en la carga relacional y las crea `scripts/mysql/configurar_mysql.py` (sección 19); `.env` nunca se versiona.
3. **Pipeline completo:** `python main.py --stage all`. Con Bronze presente no necesita red. Al terminar el registro muestra, entre otras líneas, `Salida: construcciones=5.146 barrios=346 integrado=5.146 | cobertura de llave=99.8834% (pasa)` y `Salida: gold_final=5.146 filas | kpis_gold=23 filas (6 indicadores) | sensibilidades=107 filas`. Ejecutarlo dos veces seguidas deja los mismos sha256 en `data/silver` y `data/gold`:
```powershell
Get-FileHash -Algorithm SHA256 data\silver\*.csv, data\silver\quality_report.json, data\gold\*.csv
```
   **Qué puede mostrar Git después de ejecutarlo.** Aunque los datos sean los mismos, `git status` puede listar dos cambios: `data/gold/etl_sismo.db` (SQLite no escribe el archivo igual byte a byte en cada carga: cambian los bytes, no las tablas) y una línea de `docs/silver/reglas_silver.md` (la regla R10 cita una ruta antigua que el pipeline vuelve a escribir). Lo comprobamos en un clon: los CSV de Silver y de Gold conservan sus sha256, así que no hay pérdida de datos. Para volver a lo versionado: `git checkout -- data/gold/etl_sismo.db docs/silver/reglas_silver.md`. No corregimos esa ruta porque cambiaría `quality_report.json` y con él la línea base (D81).
4. **Pruebas:** `pytest -q` → `711 passed`.
5. **Notebooks** (cada uno se ejecuta de arriba a abajo sin errores):
```powershell
jupyter nbconvert --to notebook --execute --inplace notebooks\05_validacion_evidencias.ipynb
```
6. **Verificar Bronze:** el comando de la sección 6 debe imprimir `True` en las 8 líneas.
7. **Refresco (solo con red):** `python main.py --stage extract --refresh` crea un snapshot nuevo; después `python main.py --stage transform` y `--stage gold` regeneran Silver y Gold (los resultados pueden cambiar si la fuente cambió).

**Registro de ejecución (logs).** Cada ejecución escribe en consola y en `logs\etl_AAAAMMDD.log`, con el formato `fecha hora NIVEL módulo mensaje`. Cada etapa registra su inicio, su fin con la duración, y las filas de entrada y salida. Las advertencias de calidad usan `WARNING` (construcciones sin llave, geometrías duplicadas, grupos con muestra baja); `ERROR` solo aparece si algo falla. Un filtro oculta tokens, cabeceras de autenticación y valores de `.env`. Se leen con `Get-Content logs\etl_*.log -Tail 20` y `Select-String " WARNING " logs\*.log`. El formato, el nivel y la carpeta se configuran en la sección `logging` de `config/config.yaml`. Los logs no entran en Silver, Gold ni Bronze, por lo que no alteran los sha256.

## 13. Estructura del repositorio
- `main.py`: puerta de entrada: `--stage extract|transform|gold|all` y `--refresh`
- `requirements.txt`: dependencias con versión exacta (Python 3.13)
- `pytest.ini`: configuración de las pruebas (carpeta de pruebas y ruta de importación)
- `.env.example`: nombres de variables sin valores (`HTTP_USER_AGENT` y las `MYSQL_*` de la carga relacional)
- `.gitignore`: lo que git no versiona (`.env`, entornos virtuales, `dist/`, registros)
- `.gitattributes`: fija los bytes de `data/` y los saltos de línea
- `config/`: parámetros en `config.yaml`: URL de las fuentes, umbrales, fechas, rutas, registro de ejecución y capa de servicio
- `data/bronze/`: respuestas crudas, CSV original, polígonos y `manifest.jsonl`
- `data/silver/`: tablas limpias, huérfanos y `quality_report.json`
- `data/gold/`: `gold_final.csv`, `kpis_gold.csv`, `kpis_sensibilidad.csv`, `etl_sismo.db`
- `notebooks/`: cinco notebooks ejecutados (conexión, EDA, Silver, Gold y validación)
- `dags/`: DAG de Airflow `medallon_etl_dag.py` (copia versionada del DAG vivo de `airflow-medallon`)
- `orquestacion/`: Dockerfile, requisitos de la imagen de Airflow y hash del DAG
- `src/`: código por capas (ver `src/README.md`): `extract/`, `transform/`, `load/` (SQLite y carga relacional), `api/`, `panel/` (interfaz Streamlit de solo lectura), `common.py` y `logger.py`
- `tests/`: 711 pruebas automáticas
- `scripts/`: generadores y utilidades (ver `scripts/README.md`): README, catálogo de fuentes, modelo de datos, carga relacional, `mysql/` (configuración y verificación en vivo), matriz de casos de prueba e informe de pruebas, orquestación (`orquestacion/`), escáner de secretos, empaquetado y `evidencias/`
- `docs/README.md`: índice de la documentación por capas y tabla «dónde está cada cosa»
- `docs/DECISIONES.md`: decisiones con alternativas, razón y riesgo
- `docs/proyecto/`: contexto, entorno, decisiones técnicas y referencias (documento de contexto y problema, imagen del enunciado)
- `docs/estrategia/`: Data Thinking, stakeholders, objetivo y OKR, Canvas y MVP con criterios de aceptación
- `docs/bronze/`: investigación y verificación de fuentes, catálogo de fuentes y metadatos, y muestras de las fuentes
- `docs/silver/`: hallazgos del análisis exploratorio, reglas de limpieza, validación de la llave y revisión de códigos de barrio
- `docs/gold/`: definición de cada KPI y diccionario de columnas de Gold
- `docs/api/`: arquitectura del backend y de la API de solo lectura, con su diagrama
- `docs/orquestacion/`: pruebas y orquestación: diferencias con la guía de Airflow, guía de implementación, prácticas de producción y operación
- `docs/panel/`: panel: guía de uso, arquitectura con su diagrama, trazabilidad de la interfaz, pruebas y accesibilidad
- `docs/almacenamiento/`: almacenamiento relacional: modelo de datos con su diagrama, configuración de MySQL y carga y verificación
- `docs/seguridad/`: política de credenciales, claves y tokens
- `docs/validacion/`: verificaciones: contra el enunciado, de los servicios, en entorno limpio y del registro de ejecución
- `docs/checklist/`: estado de los 30 ítems del checklist y guía de evidencias por ítem (`docs/checklist/guia_de_evidencias.md`)
- `docs/evidencias/`: manifiesto de evidencias y salidas registradas por tema
- `docs/retroalimentacion/`: retroalimentación del profesor y cómo la atendimos
- `logs/`: archivos de registro diarios (se crean al ejecutar; no se versionan)

## 14. Pruebas y validación
Hay **711 pruebas** automáticas, sin red:
- `tests/test_api.py` (17): API de solo lectura: estructura, validación, coincidencia con las salidas, solo GET y sin escritura en `data/` ni en la base.
- `tests/test_canario_extra.py` (5): comprobación canario con archivos `.env` extra: detecta contraseñas de otra carpeta sin imprimirlas.
- `tests/test_carga_relacional.py` (54): esquema relacional (paridad, diccionario al día), conversión estricta, carga con conciliación al 100 %, idempotencia, historial, reversión, integridad referencial y equivalencia de la API entre SQLite y el almacén relacional (sin servidor MySQL).
- `tests/test_carga_sqlite.py` (5): carga a SQLite en una carpeta temporal: contenido igual al de la base versionada, repetida, con una fila y con un CSV ausente.
- `tests/test_casos_limite.py` (19): casos límite: un solo registro, entrada vacía y extremos de paginación.
- `tests/test_catalogo.py` (5): el catálogo de fuentes coincide con el manifiesto, es determinista y `/fuentes` lo devuelve igual.
- `tests/test_cifras_de_estado.py` (12): .
- `tests/test_configurar_mysql.py` (25): configuración de MySQL con conexiones simuladas (privilegios, contraseñas que nunca llegan a `.env` ni a SQL, rotación), `.env` atómico, enmascarado del registro y comprobación canario del escáner.
- `tests/test_dag_estatico.py` (24): DAG y imagen de Airflow analizados con `ast`: tareas, dependencias, repositorio de solo lectura, fallo inducido, secretos, requisitos y hash.
- `tests/test_decisiones.py` (4): la cabecera de las decisiones y el índice de la documentación coinciden con la última decisión registrada.
- `tests/test_dist.py` (19): el empaquetado detecta entornos virtuales por su contenido, aunque no tengan `pyvenv.cfg`.
- `tests/test_empaquetado_y_revision.py` (5): el empaquetado excluye entornos virtuales con cualquier nombre; la revisión de códigos de barrio cubre los casos pedidos y suma las construcciones sin nombre validado.
- `tests/test_entorno_de_pruebas.py` (4): configuración de pytest, extensiones de las pruebas y versión de pandas de la línea base.
- `tests/test_estrategia.py` (29): documentos de estrategia y estado del checklist: existencia, términos prohibidos, cifras, criterios con componente de la lista cerrada y pruebas negativas.
- `tests/test_evidencias.py` (4): el saneamiento de evidencias sustituye rutas, usuario y equipo, y las evidencias guardadas no llevan datos del equipo.
- `tests/test_extract.py` (6): manifiesto, sha256, filas y páginas de Bronze (sin red).
- `tests/test_informe_pruebas.py` (6): lectura de JUnit, resultado por caso y recálculo independiente de K1 para el informe de pruebas.
- `tests/test_kpis.py` (6): regresión numérica de los KPI, Newcombe, Mantel-Haenszel y regresión del defecto.
- `tests/test_logger.py` (2): enmascarado de secretos y nombre de los loggers.
- `tests/test_matriz_casos.py` (7): la matriz de casos de prueba apunta a pruebas existentes y está al día con su definición.
- `tests/test_panel_cliente.py` (29): cliente HTTP del panel: solo GET, errores traducidos al español, un reintento de conexión y caché que no guarda fallos.
- `tests/test_panel_formato_redaccion.py` (47): formato de cifras del panel (miles, coma decimal, signo menos y half-up) y regla de redacción de conclusiones con valores sintéticos.
- `tests/test_panel_humo_extremo_a_extremo.py` (5): humo de solo lectura: API real en un subproceso, cliente HTTP real y las ocho páginas.
- `tests/test_panel_integracion.py` (11): los valores que muestra el panel coinciden con las salidas del pipeline, leídas y recalculadas en la prueba.
- `tests/test_panel_lanzador.py` (19): lanzador del panel con subprocesos simulados: comandos, entorno, puertos, códigos de salida y cierre garantizado.
- `tests/test_panel_paginas.py` (134): las ocho páginas con `AppTest` sobre la API real en memoria, alcance visible y resiliencia ante cada fallo de la API.
- `tests/test_panel_registro_y_aislamiento.py` (39): registro de componentes (rutas, campos y KPI existen) y aislamiento del panel por análisis estático: solo la API, solo GET y sin cifras escritas a mano.
- `tests/test_panel_tema.py` (10): relación de contraste WCAG de la paleta del panel.
- `tests/test_panel_textos.py` (54): .
- `tests/test_pipeline_reproducible.py` (4): el pipeline regenerado en una copia reproduce byte a byte los nueve archivos de la línea base.
- `tests/test_quality.py` (4): campos del reporte, cobertura frente al umbral, mínimo de filas de Gold, KPI en rango.
- `tests/test_readme_cifras.py` (13): las cifras de este README coinciden con los archivos de salida; recuadros de alcance, población e indicador satelital.
- `tests/test_requisitos.py` (14): .
- `tests/test_respaldo_y_medicion.py` (12): respaldo lógico con manifiesto sha256, restauración con conciliación, reglas de la medición de lotes y límites de los scripts en vivo.
- `tests/test_secretos.py` (10): escáner de secretos (un secreto sembrado por tipo), `.env` fuera de git, enmascarado del registro y zip sin `.env`.
- `tests/test_transform.py` (7): llaves, `normalize_key`, duplicados, tipos, zona horaria, vectores de Wilson.
- `tests/test_usuario_docker.py` (41): usuario de MySQL para Docker: origen validado (sin `%`), permisos mínimos sobre la base real, contraseñas solo en `.env` e idempotencia, con conexiones simuladas.

Además: (1) el **recálculo independiente de los KPI con SQL** sobre SQLite (notebook 04, diferencia máxima inferior a 1e-9), con implementaciones independientes de Wilson, Newcombe, Mantel-Haenszel y Spearman; (2) la **regresión del defecto de Mantel-Haenszel**: ese recálculo detectó que se contaban construcciones sin datos satelitales en los tamaños de grupo; se corrigió y una prueba fija el comportamiento (`docs/DECISIONES.md`); (3) las verificaciones en `docs/validacion/` (`verificacion_entrega.md`, `verificacion_servicios.md`, `prueba_entorno_limpio.md`, `verificacion_logging.md` y los hashes de antes y después del registro) y las salidas registradas en `docs/evidencias/`.

## 15. Decisiones principales y trazabilidad
El detalle, con alternativas, razón y riesgo de cada decisión, está en [docs/DECISIONES.md](docs/DECISIONES.md).

| id | decisión | razón |
|---|---|---|
| D1 | Escala principal construcción→barrio en la capa satelital | Alineada con Proyecto 1; grano construcción da >200 filas |
| D2 | API de edificaciones (originalmente Socrata `5vy8-gpw8`) | Relevancia y grano |
| D3 | CSV: estrato por barrio (ficha 2) | Mantiene el barrio como llave |
| D4 | Llave: `barrio_norm`; espacial solo si falta | Explicable |
| D5 | Punto-en-polígono local con `shapely` | Dependencia liviana |
| D6 | Bronze = respuestas crudas por página + manifiesto; sin sobrescribir | Trazabilidad e idempotencia |
| D7 | Umbral de "severo" definido tras el EDA de Bronze | Dominio no conocido |
| D8 | USGS solo contexto (README) | Sin llave a barrio |
| D9 | Plan B por criterio de aceptación, no por preferencia | Evita arrastrar fuente inaccesible |
| D10 | Salida CSV + SQLite | Recalcular KPI con SQL |

Decisiones de las fuentes: el plan elegido es el de las construcciones de la capa satelital, en 7 comunas de Cali (la verificación previa de las fuentes cumplió los criterios de acceso, columnas, cobertura y volumen); el endpoint Socrata no es tabular y se usa el FeatureServer enlazado; la llave es el código catastral y no un nombre; el indicador principal es `severo_estricto` y `dano_visible` queda como sensibilidad de baja confianza.

**Cómo leer los identificadores:** `H#` = hallazgo del análisis exploratorio (`docs/silver/hallazgos_eda.md`); `R##` = regla de Silver (`docs/silver/reglas_silver.md`); `K#` = indicador de Gold (`docs/gold/KPIs.md`); `S#` = escenario de sensibilidad; `V#` = verificación de una fuente (`docs/bronze/verificacion_fuentes.md`); `D#` = decisión (`docs/DECISIONES.md`).

## 16. Glosario
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

## 17. Trabajo futuro y atribución
**Trabajo futuro.** Incorporar la amenaza sísmica oficial para cubrir KR2; ampliar la cobertura a la Comuna 2 y a las demás comunas ausentes; comparar el proxy satelital con las inspecciones ATC-20 de la Alcaldía; repetir el análisis con un estrato actualizado (el de 2015 puede estar desfasado).

**Atribución.** Capa de impacto satelital: Fondo Adaptación, catálogo datos.gov.co `5vy8-gpw8` (CC BY 4.0 según el catálogo; consulta del 15-oct-2026). Estratificación por barrio 2015: DAPM Cali, datos.cali.gov.co (consulta del 15-oct-2026). Polígonos de barrios: IDESC / DAPM Cali (consulta del 15-oct-2026). Evento: USGS `us6000tjl2` (consulta del 15-oct-2026). Contexto externo: El País Cali, 11-oct-2026.

## 18. Capa de servicio (API de solo lectura)
Además de los archivos, el repositorio expone los resultados de Gold por una API local de **solo lectura** (`src/api/`). No escribe en `data/` ni en la base, no recalcula indicadores y entrega un proxy satelital, no una evaluación estructural. Tiene **11 rutas GET**: `/calidad`, `/composicion`, `/comunas`, `/construcciones`, `/fuentes`, `/health`, `/kpis`, `/kpis/sensibilidad`, `/kpis/{kpi_id}`, `/llave/revision`, `/metadata`.

**Ejecución** (PowerShell, en la raíz del repositorio, con el entorno activado):
```powershell
python -m pip install -r requirements.txt
python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000
```
Después se abre `http://127.0.0.1:8000/docs` (documentación automática) o `http://127.0.0.1:8000/health`. El servicio queda enlazado a `127.0.0.1`: no es accesible desde otros equipos.

| endpoint | qué entrega |
|---|---|
| `/health` | estado del servicio, fecha de corte y filas por tabla |
| `/metadata` | fuentes, fechas, población analizada (7 comunas), alcance temporal (estrato 2015) y licencias |
| `/fuentes` | catálogo de fuentes y metadatos |
| `/kpis`, `/kpis/{kpi_id}` | filas de `kpis_gold.csv` tal como están (filtros `kpi_id` y `grupo`) |
| `/kpis/sensibilidad` | filas de `kpis_sensibilidad.csv` (filtro `escenario`, S0 a S5) |
| `/comunas` | K6 por comuna |
| `/composicion` | construcciones con datos y severos por comuna y grupo de estrato |
| `/construcciones` | construcciones paginadas (`limit` por defecto 50 y máximo 200) con filtros por comuna, estrato y severo estricto |
| `/calidad` | coberturas y confianza de la llave |
| `/llave/revision` | códigos de barrio con nombre no validado |

Los errores usan siempre `{"error": {"codigo", "mensaje", "detalle"}}`. Documentación: [arquitectura del backend](docs/api/arquitectura.md), [catálogo de fuentes y metadatos](docs/bronze/catalogo_fuentes_metadatos.md) y [política de credenciales](docs/seguridad/gestion_credenciales.md). Para buscar secretos: `python scripts/escanear_secretos.py` (termina en `hallazgos: 0`).

## 19. Almacenamiento relacional (MySQL)
Además de `etl_sismo.db` (SQLite), los resultados se pueden cargar a **MySQL 8.0** con un esquema de siete tablas con claves primarias y foráneas, restricciones de validación e **historial**: cada carga distinta es una *corrida* completa y las anteriores no se tocan. La carga lee solo `data/` (5.146 construcciones, 346 barrios y los indicadores), es **idempotente** (la misma entrada responde «ya cargada»), se hace en **una transacción** (si algo falla no queda nada a medias) y usa **lotes** cuyo tamaño se decide por medición. Las construcciones sin cruce con el CSV de estrato se conservan con el enlace al barrio nulo. Los datos siguen siendo un proxy satelital sobre construcciones de siete comunas, sin generalizar a toda Cali.

**Verificación en vivo** (MySQL 8.0.45, 2026-11-13): la batería de la base de prueba pasa 26 de 26 comprobaciones, la carga real concilia al 100 % con Gold, la API sirve lo mismo desde MySQL y SQLite y el lote de 2000 filas es 3,4 veces más rápido que insertar fila a fila (tiempos de un equipo, no de un despliegue). Las evidencias están en `docs/evidencias/almacenamiento/`.

**Primera vez** (PowerShell, en la raíz, con el servicio MySQL80 activo). Quien conoce la contraseña del administrador de MySQL la escribe cuando el script la pide (no se ve); el script crea las bases `sismo_cali` y `sismo_cali_prueba`, el usuario `sismo_etl` con privilegios mínimos y guarda sus credenciales solo en `.env`:
```powershell
.\.venv\Scripts\python.exe scripts\mysql\configurar_mysql.py
```
**Cargar y verificar:**
```powershell
.\.venv\Scripts\python.exe scripts\cargar_mysql.py --destino mysql
.\.venv\Scripts\python.exe scripts\mysql\verificar_mysql.py
```
La verificación en vivo corre solo sobre la base de prueba. Para servir la API desde MySQL se cambia `api.almacenamiento` a `mysql` en `config/config.yaml`. Las pruebas automáticas no necesitan MySQL. La contraseña no se escribe en ningún archivo del repositorio, notebook ni registro; el escáner la busca activamente (`python scripts/escanear_secretos.py --canario-env`).

Documentación: [modelo de datos](docs/almacenamiento/modelo_datos.md), [configuración de MySQL](docs/almacenamiento/mysql_configuracion.md), [carga y verificación](docs/almacenamiento/carga_y_verificacion.md) y [gestión de credenciales](docs/seguridad/gestion_credenciales.md).

## 20. Pruebas y orquestación
El pipeline se orquesta con **Apache Airflow en Docker**, siguiendo la guía de Airflow de la asignatura (artículo de Juan Manuel Núñez Velasco) con unas pocas diferencias documentadas. El DAG `medallon_etl_sismo` (`dags/medallon_etl_dag.py`) tiene cuatro tareas, `validar_bronze → transformar_a_silver → integrar_a_gold → cargar_datawarehouse`, y trabaja sobre una **copia de trabajo** dentro del contenedor: el repositorio se monta en solo lectura y cada tarea compara lo que produce con los archivos versionados (CSV y JSON byte a byte, `etl_sismo.db` tabla a tabla), así que ni los datos ni las salidas pueden alterarse. La carga a MySQL usa un usuario propio de Docker con permisos mínimos sobre la base real. Para reproducir los archivos de la línea base hay que usar **pandas 3.0.6** (con otra versión cambian celdas del decimal 12; ver D56).

Hay 711 pruebas automáticas, una **matriz de casos** por función crítica generada desde una única definición (`python scripts/make_matriz_casos.py`), un **informe de pruebas** con resultado esperado y obtenido por caso y cobertura por módulo (`python scripts/informe_pruebas.py`) y un **registro de defectos** cuyas pruebas de regresión fallan sin su corrección.
```powershell
.\.venv\Scripts\python.exe scripts\informe_pruebas.py
.\.venv\Scripts\python.exe scripts\orquestacion\sincronizar_dag.py --verificar
```
Documentación: [orquestación](docs/orquestacion/README.md), [diferencias con la guía](docs/orquestacion/diferencias_con_la_guia.md), [matriz de casos](docs/validacion/matriz_casos_prueba.md), [informe de pruebas](docs/validacion/informe_pruebas.md) y [registro de defectos](docs/validacion/registro_defectos.md).

## 21. Panel (interfaz de solo lectura)
El **panel** (`src/panel/`) es una interfaz Streamlit que muestra los resultados de Gold hablando **solo con la API** por HTTP (solo GET): no abre bases ni archivos de datos, no lee `.env` ni maneja credenciales. Tiene ocho páginas (Respuesta, Estratos, Comunas, Sensibilidades, Concentración, Calidad de la llave, Construcciones y Fuentes y sistema); todas muestran el recuadro de alcance (cambio satelital severo como proxy de daño, tasas condicionales a la muestra, estrato de 2015 por lados de manzana) y las conclusiones se redactan con la regla de `docs/gold/KPIs.md`.

Se ejecuta con un solo comando (arranca la API y el panel en 127.0.0.1 y cierra los dos con Ctrl+C):
```powershell
.\.venv\Scripts\python.exe scripts\panel\ejecutar_panel.py
```
Por separado: `python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000` y `python -m streamlit run src/panel/app.py`. Con `--almacenamiento mysql` la API sirve desde MySQL. El panel no está desplegado: se ejecuta en local.

Documentación: [guía de uso](docs/panel/guia_de_uso.md), [arquitectura](docs/panel/arquitectura_panel.md), [trazabilidad de la interfaz](docs/panel/trazabilidad_ui.md), [pruebas](docs/panel/pruebas_panel.md) y [accesibilidad y respuesta](docs/panel/accesibilidad_y_respuesta.md).

## 22. Componentes en construcción
Quedan en construcción, y se documentarán en `docs/` cuando existan: los materiales de **usuarios y UX** y el análisis de **costos y finanzas**. El índice de la documentación, con la carpeta prevista para cada uno, está en [docs/README.md](docs/README.md).
