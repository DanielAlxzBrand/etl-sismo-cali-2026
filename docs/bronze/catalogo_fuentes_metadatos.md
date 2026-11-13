# Catálogo de fuentes y metadatos

**Archivo generado** por `scripts/make_catalogo_fuentes.py` a partir de `data/bronze/manifest.jsonl`, `config/config.yaml`, la capa de metadatos guardada en Bronze, `data/silver/quality_report.json`, `docs/KPIs.md` y `docs/muestras/`. No contiene fechas de ejecución: dos corridas dan el mismo archivo. Se sirve en `GET /fuentes` como `docs/entrega_3/catalogo_fuentes.json`.

> Proxy satelital, no evaluación estructural. Alcance: 7 comunas con polígonos de afectación preliminar; estrato 2015.

## Fuentes

| id | rol | publicador | formato | licencia | filas (snapshot) |
|---|---|---|---|---|---|
| `edificaciones` | principal | Capa catalogada en datos.gov.co (5vy8-gpw8); servicio ArcGIS FeatureServer | JSON (geometría de polígonos, EPSG:4326) | CC BY 4.0 (metadata.custom_fields.Common Core.License del catalogo datos.gov.co, 5vy8-gpw8); el servicio ArcGIS trae copyrightText vacio | 5146 |
| `estrato_barrio` | principal | DAPM Cali (datos.cali.gov.co); catálogo datos.gov.co 6esn-pmy5 | CSV UTF-8 | Licencia Creative Commons Attribution Share-Alike | 369 |
| `poligonos_barrios` | auxiliar (validación de la llave) | DAPM Cali (IDESC, GeoServer) | GeoJSON (EPSG:4326) | no declarada en el servicio | 342 |
| `usgs` | contexto | U.S. Geological Survey | CSV | no declarada en esta verificación | — |
| `atc20_prensa` | contexto | El País Cali (reportando a la Alcaldía) | artículo | no aplica (cifras de prensa) | — |

### `edificaciones` · Impacto Satelital en Edificaciones por Terremoto, Cali 2026

- **Rol:** principal. **Uso en el pipeline:** Bronze → Silver (silver_construcciones) → base de todos los KPI de Gold.
- **URL:** https://services3.arcgis.com/Hf3YbZrlZ0OA2COM/arcgis/rest/services/Impacto_Satelital_en_Edificaciones_por_Terremoto_Cali_2026/FeatureServer/0
- **Protocolo:** ArcGIS REST (FeatureServer, consulta con paginación por resultOffset). **Autenticación:** ninguna (consulta pública sin token). **Límites y paginación:** maxRecordCount 2000; 3 páginas de 2000, 2000, 1146 filas.
- **Cobertura temporal:** imágenes pre 2026-03-22 y post 2026-08-11; capa editada el 2026-09-02. **Cobertura espacial:** construcciones dentro de los polígonos de afectación preliminar; 7 comunas de Cali (no es toda la ciudad). **Granularidad:** una fila por construcción (huella catastral).
- **Fechas:** imagen_pre = 2026-03-22; imagen_post = 2026-08-11; edicion_capa = 2026-09-02; consulta_utc = 2026-10-16T00:10:25Z. **Licencia:** CC BY 4.0 (metadata.custom_fields.Common Core.License del catalogo datos.gov.co, 5vy8-gpw8); el servicio ArcGIS trae copyrightText vacio.
- **Llave de unión:** codigo_barrio = int(COMUNA)*100 + int(BARRIO) (texto).
- **Snapshot:** `data/bronze/api/edificaciones/snap_20261016T001024Z` · extracción UTC 2026-10-16T00:10:25Z · 5146 filas de datos, 4600141 bytes · 6 archivo(s):
  - `data/bronze/api/edificaciones/snap_20261016T001024Z/page_0001.json` · filas 2000 · 1774634 bytes · sha256 `92dfda868878fed44148bbeeb446b13f6bcf88a62dcc33aaab8afd45f717e4af`
  - `data/bronze/api/edificaciones/snap_20261016T001024Z/page_0002.json` · filas 2000 · 1752478 bytes · sha256 `6b2a4849e95d8da1f04f7641cbc90b98aa4372cad9cbab02230bab8babe25729`
  - `data/bronze/api/edificaciones/snap_20261016T001024Z/page_0003.json` · filas 1146 · 1055160 bytes · sha256 `ac23590d1a6713e37f711473d999a9fd10eec024076b58bb63fa48f2e7524f51`
  - `data/bronze/api/edificaciones/snap_20261016T001024Z/capa_meta.json` · filas 20 · 17507 bytes · sha256 `c5e4f42587756d609a8f143d5b49bfc6a4fd051fef1f5d35e22f72cd34ee52df`
  - `data/bronze/api/edificaciones/snap_20261016T001024Z/count_antes.json` · filas 5146 · 181 bytes · sha256 `c20dec67463cb2026f1f47b9949fe1272a30e944e2958a1538f59138effb8f59`
  - `data/bronze/api/edificaciones/snap_20261016T001024Z/count_despues.json` · filas 5146 · 181 bytes · sha256 `c20dec67463cb2026f1f47b9949fe1272a30e944e2958a1538f59138effb8f59`

| columna usada | tipo | significado |
|---|---|---|
| `OBJECTID` | entero (identificador) | identificador de la construcción (se conserva como objectid) |
| `COMUNA` | texto | código catastral de la comuna (2 dígitos, texto); entra a la llave del JOIN |
| `BARRIO` | texto | código catastral del barrio dentro de la comuna (2 dígitos, texto); entra a la llave del JOIN |
| `NPISOS` | decimal | número de pisos declarado en la capa |
| `Indice_Escombros` | decimal | índice continuo de cambio de textura entre las imágenes pre y post; nulo si no hay datos satelitales |
| `Estado_Estructural` | texto | etiqueta de clase de la capa (se agrupa en cuatro clases estables); no es una evaluación estructural |

Columnas de la capa que el pipeline no usa: `OBJECTID_1`, `DEPAPRED`, `MUNIPRED`, `TIPO_AVALU`, `SECTOR`, `MANZANA`, `TERRENO`, `COND`, `EDIFPRED`, `PREDIO`, `NUMEPRED`, `ID_PREDIO`, `Shape__Area`, `Shape__Length`.

- **Calidad:** construcciones = 5146; sin_datos_satelitales = 435; pct_sin_datos = 0.084532; geom_duplicada_filas = 18; nulos_antes_bronze = {"COMUNA": 2, "BARRIO": 2, "NPISOS": 11, "Indice_Escombros": 435}.
- **Riesgos y limitaciones:**
  - Proxy satelital: no es una evaluación estructural ni inspección en sitio.
  - Solo incluye construcciones dentro de polígonos de afectación preliminar: la tasa es condicional a esa zona.
  - El servicio no declara licencia (copyrightText vacío); la licencia se toma del catálogo.
  - Las imágenes pre y post están separadas unos 4,5 meses y no hay grupo de control.

### `estrato_barrio` · Estratificación socioeconómica según estrato, por barrio en Cali 2015

- **Rol:** principal. **Uso en el pipeline:** Bronze → Silver (silver_estrato_barrio) → estrato moda por barrio.
- **URL:** https://datos.cali.gov.co/dataset/c6421d6b-2f7c-4a28-b126-fb60192e6302/resource/f492c39c-d980-4a97-9eaa-f00dc17e451a/download/estratificaci_n_socioecon_mica_seg_n_estrato__por_barrio_en_cali_2015.csv
- **Protocolo:** HTTP GET de un archivo. **Autenticación:** ninguna (requiere un User-Agent). **Límites y paginación:** archivo único, sin paginación.
- **Cobertura temporal:** año 2015 (estrato por lados de manzana). **Cobertura espacial:** Cali; 346 barrios y 23 filas resumen (comunas y «Otros»). **Granularidad:** una fila por barrio.
- **Fechas:** datos = 2015; consulta_utc = 2026-10-16T00:10:28Z. **Licencia:** Licencia Creative Commons Attribution Share-Alike.
- **Llave de unión:** Código único del barrio (codigo_barrio).
- **Snapshot:** `data/bronze/tabular/estrato_barrio/snap_20261016T001028Z` · extracción UTC 2026-10-16T00:10:28Z · 1 archivo(s):
  - `data/bronze/tabular/estrato_barrio/snap_20261016T001028Z/estratificaci_n_socioecon_mica_seg_n_estrato__por_barrio_en_cali_2015.csv` · filas 369 · 16030 bytes · sha256 `c16b209e4f20bd0983e0c44c6ad109f151e41c30c23f7708143094746136a089`

| columna usada | tipo | significado |
|---|---|---|
| `Código único` | entero (con guiones como nulo) | ver columnas de silver_estrato_barrio |
| `Barrio` | texto | ver columnas de silver_estrato_barrio |
| `Lados de manzana por estrato 1` | entero (con guiones como nulo) | ver columnas de silver_estrato_barrio |
| `Lados de manzana por estrato 2` | entero (con guiones como nulo) | ver columnas de silver_estrato_barrio |
| `Lados de manzana por estrato 3` | entero (con guiones como nulo) | ver columnas de silver_estrato_barrio |
| `Lados de manzana por estrato 4` | entero (con guiones como nulo) | ver columnas de silver_estrato_barrio |
| `Lados de manzana por estrato 5` | entero (con guiones como nulo) | ver columnas de silver_estrato_barrio |
| `Lados de manzana por estrato 6` | entero (con guiones como nulo) | ver columnas de silver_estrato_barrio |
| `Sin vivienda` | entero (con guiones como nulo) | ver columnas de silver_estrato_barrio |
| `Estrato moda` | entero (con guiones como nulo) | ver columnas de silver_estrato_barrio |

- **Calidad:** filas_entrada = 369; filas_resumen_separadas = 23; filas_salida = 346; cobertura_estrato_valido = 0.998445.
- **Riesgos y limitaciones:**
  - Estrato de 2015: desfase temporal frente a las imágenes de 2026.
  - Estrato asignado por barrio (moda), no por predio: falacia ecológica.
  - Los códigos de barrio de 2026 están renumerados respecto de 2015 (ver docs/revision_codigos_barrio.md).

### `poligonos_barrios` · Polígonos de barrios y sectores (WFS dapm:pdt_dpa_barrios_sectores)

- **Rol:** auxiliar (validación de la llave). **Uso en el pipeline:** solo valida la llave (coincide_poligono, nombre_validado).
- **URL:** https://ws-idesc.cali.gov.co/geoserver/dapm/ows
- **Protocolo:** OGC WFS 1.0.0 GetFeature. **Autenticación:** ninguna. **Límites y paginación:** una sola respuesta.
- **Cobertura temporal:** polígonos vigentes en 2026 (acuerdo DIVIPOLA). **Cobertura espacial:** Cali. **Granularidad:** una fila por barrio o sector.
- **Fechas:** consulta_utc = 2026-10-16T00:10:31Z. **Licencia:** no declarada en el servicio.
- **Llave de unión:** centroide de la construcción dentro del polígono (no entra al JOIN).
- **Snapshot:** `data/bronze/geo/poligonos_barrios/snap_20261016T001031Z` · extracción UTC 2026-10-16T00:10:31Z · 1 archivo(s):
  - `data/bronze/geo/poligonos_barrios/snap_20261016T001031Z/barrios.geojson` · filas 342 · 1850751 bytes · sha256 `8e74f06308568e2ccbe90f54c5bef0611c15072765a255fa6bd5bc12babe6ad1`

| columna usada | tipo | significado |
|---|---|---|
| `barcodigo` | texto | código del polígono 2026 |
| `barnombre` | texto | nombre del barrio o sector |
| `geometry` | polígono | límite; se ubica el centroide de cada construcción |

- **Calidad:** pct_coincide_poligono = 0.914269; pct_nombre_validado = 0.935214.
- **Riesgos y limitaciones:**
  - Los códigos de 2026 difieren de los de 2015 en parte de los barrios.
  - El servicio es de un tercero y puede cambiar.

### `usgs` · USGS FDSN Event (catálogo de sismos)

- **Rol:** contexto. **Uso en el pipeline:** solo contexto del evento (id us6000tjl2, magnitud 7.4); no entra al pipeline ni a Bronze (muestra en docs/muestras/v10_usgs_11.csv).
- **URL:** https://earthquake.usgs.gov/fdsnws/event/1/query
- **Protocolo:** HTTP GET (FDSN). **Autenticación:** ninguna. **Límites y paginación:** limit 1 a 20.000.
- **Cobertura temporal:** evento del 2026-08-10. **Cobertura espacial:** ventana de consulta cercana a Cali. **Granularidad:** un evento por fila.
- **Fechas:** consulta = 2026-10-15. **Licencia:** no declarada en esta verificación.
- **Llave de unión:** ninguna.

- **Calidad:** eventos_en_la_muestra = 11.
- **Riesgos y limitaciones:**
  - Sin llave a barrio o municipio: descartada como fuente del JOIN.

### `atc20_prensa` · Evaluación estructural ATC-20 de la Alcaldía (cifras de prensa)

- **Rol:** contexto. **Uso en el pipeline:** solo contexto; no se compara ni se mezcla con cifras de Gold.
- **URL:** https://www.elpais.com.co/cali/alcaldia-de-cali-entrega-balance-de-gestion-tras-el-sismo-mas-de-3400-edificaciones-evaluadas-y-45000-familias-damnificadas-2338.html
- **Protocolo:** página web. **Autenticación:** ninguna. **Límites y paginación:** no aplica.
- **Cobertura temporal:** publicado el 23-sep-2026. **Cobertura espacial:** Cali (distribución por comuna desconocida). **Granularidad:** predio.
- **Fechas:** consulta = 2026-10-15. **Licencia:** no aplica (cifras de prensa).
- **Llave de unión:** ninguna.

- **Calidad:** cifras = "3.403 predios: 1".
- **Riesgos y limitaciones:**
  - Cifras de prensa, no recotejadas con una fuente oficial descargable.
  - La unidad (predios) no es la nuestra (construcciones).

## Fuentes descartadas

| id | fuente | motivo | evidencia |
|---|---|---|---|
| `sgc_eval_int` | SGC · Mapa de Intensidades Evaluadas (ArcGIS REST) | Granularidad por sitio o centro poblado, no por barrio; ningún ID_SISMO identificable como el evento (V9). | docs/investigacion_fuentes.md §2 F5; verificacion_fuentes.md V9 |
| `sgc_municipios` | SGC · SIMMA Capas Generales, Municipios | Solo polígonos municipales para el Plan B; no es amenaza por barrio. | docs/investigacion_fuentes.md §2 F6 |
| `area_barrios` | Área barrios de Cali 2015 (CSV, respaldo) | Solo estrato moda por barrio; respaldo del CSV principal, no se usa en el JOIN. | docs/investigacion_fuentes.md §2 F3; V5 |
| `estrato_comunas` | Estratificación por comunas 2015 (CSV) | Solo 22 filas; sirve para una llave por comuna, no por barrio. | docs/investigacion_fuentes.md §2 F3; V5 |
| `rud` | RUD (UNGRD) vía monitor «Datos del terremoto» | Archivo JSON estático de un monitor de un solo mantenedor, registro declarativo, sin código DIVIPOLA; Plan B municipal. | docs/investigacion_fuentes.md §2 F8; V11 |
| `divipola` | DIVIPOLA (Socrata gdxc-w37w) | Códigos municipales; solo útiles en el Plan B municipal. | docs/investigacion_fuentes.md §2 F9; V12 |
| `socrata_hbdu_4927` | Socrata hbdu-4927 (portal SGC) | Es un enlace federado sin filas; la API devuelve HTTP 400. | docs/investigacion_fuentes.md §2 F7 |
| `mapageologia` | ArcGIS MAPAGEOLOGIA (fallas) | Geología a escala nacional, sin llave a barrio. | docs/investigacion_fuentes.md §2 F6 |
| `copernicus_emsr916` | Copernicus EMSR916 / ICube-SERTIT | Solo 21 y 94 edificios en zonas parciales de Cali, sin edificios en común; uso no comercial. | docs/investigacion_fuentes.md §2 F11 |

## Diccionario de metadatos por capa

### Bronze

Bytes crudos de cada fuente con manifiesto de sha256; nunca se sobrescriben.

- `data/bronze/api/edificaciones/snap_20261016T001024Z/count_antes.json` · 5146 filas · 181 bytes · sha256 `c20dec67463cb2026f1f47b9949fe1272a30e944e2958a1538f59138effb8f59`
- `data/bronze/api/edificaciones/snap_20261016T001024Z/capa_meta.json` · 20 filas · 17507 bytes · sha256 `c5e4f42587756d609a8f143d5b49bfc6a4fd051fef1f5d35e22f72cd34ee52df`
- `data/bronze/api/edificaciones/snap_20261016T001024Z/page_0001.json` · 2000 filas · 1774634 bytes · sha256 `92dfda868878fed44148bbeeb446b13f6bcf88a62dcc33aaab8afd45f717e4af`
- `data/bronze/api/edificaciones/snap_20261016T001024Z/page_0002.json` · 2000 filas · 1752478 bytes · sha256 `6b2a4849e95d8da1f04f7641cbc90b98aa4372cad9cbab02230bab8babe25729`
- `data/bronze/api/edificaciones/snap_20261016T001024Z/page_0003.json` · 1146 filas · 1055160 bytes · sha256 `ac23590d1a6713e37f711473d999a9fd10eec024076b58bb63fa48f2e7524f51`
- `data/bronze/api/edificaciones/snap_20261016T001024Z/count_despues.json` · 5146 filas · 181 bytes · sha256 `c20dec67463cb2026f1f47b9949fe1272a30e944e2958a1538f59138effb8f59`
- `data/bronze/tabular/estrato_barrio/snap_20261016T001028Z/estratificaci_n_socioecon_mica_seg_n_estrato__por_barrio_en_cali_2015.csv` · 369 filas · 16030 bytes · sha256 `c16b209e4f20bd0983e0c44c6ad109f151e41c30c23f7708143094746136a089`
- `data/bronze/geo/poligonos_barrios/snap_20261016T001031Z/barrios.geojson` · 342 filas · 1850751 bytes · sha256 `8e74f06308568e2ccbe90f54c5bef0611c15072765a255fa6bd5bc12babe6ad1`

### Silver

Datos limpios, tipificados e integrados; cada regla de limpieza está en docs/reglas_silver.md.

- `data/silver/silver_construcciones.csv` · 5146 filas · 794579 bytes · sha256 `85ea33ebe99c9fb6087bb7eaf88fee42f6ba55b9a254348f7e9d9fee571d5c9b`

| columna | tipo | descripción |
|---|---|---|
| `objectid` | entero | identificador de la construcción (único) |
| `comuna` | texto | códigos catastrales de 2 dígitos (texto; nulos si venían en blanco) |
| `barrio` | texto | códigos catastrales de 2 dígitos (texto; nulos si venían en blanco) |
| `codigo_barrio` | texto | llave `int(comuna)*100 + int(barrio)` (texto) |
| `npisos` | decimal | número de pisos (entero nullable) y bandera de 0 pisos |
| `npisos_cero` | lógico (con nulos) | número de pisos (entero nullable) y bandera de 0 pisos |
| `indice_escombros` | decimal | índice continuo de cambio de textura (nulo si sin datos) |
| `estado_estructural` | texto | etiqueta original y clase (`escombros`, `techo`, `sin_cambio`, `sin_datos`) |
| `clase_dano` | texto | etiqueta original y clase (`escombros`, `techo`, `sin_cambio`, `sin_datos`) |
| `sin_datos` | lógico | sin datos satelitales |
| `severo_estricto` | lógico (con nulos) | banderas D7; **nulas** (no falsas) si `sin_datos` |
| `dano_visible` | lógico (con nulos) | banderas D7; **nulas** (no falsas) si `sin_datos` |
| `geom_duplicada` | lógico | comparte geometría idéntica con otra construcción (18 filas, 9 pares) |
| `lon` | decimal | centroide a 7 decimales (EPSG:4326) |
| `lat` | decimal | centroide a 7 decimales (EPSG:4326) |
| `codigo_poligono` | texto | polígono WFS 2026 donde cae el centroide y si su código coincide con `codigo_barrio` |
| `nombre_poligono` | texto | polígono WFS 2026 donde cae el centroide y si su código coincide con `codigo_barrio` |
| `coincide_poligono` | lógico (con nulos) | polígono WFS 2026 donde cae el centroide y si su código coincide con `codigo_barrio` |

- `data/silver/silver_estrato_barrio.csv` · 346 filas · 18030 bytes · sha256 `0815be18476695f160b3002f40c84b29afd7a69ccddc6cba5a6b99bad87a346b`

| columna | tipo | descripción |
|---|---|---|
| `codigo_barrio` | entero | código del barrio (llave del JOIN) |
| `barrio` | texto | nombre del barrio en el CSV 2015 |
| `lados_e1` | entero | lados de manzana de estrato 1 |
| `lados_e2` | entero | lados de manzana de estrato 2 |
| `lados_e3` | entero | lados de manzana de estrato 3 |
| `lados_e4` | entero | lados de manzana de estrato 4 |
| `lados_e5` | entero | lados de manzana de estrato 5 |
| `lados_e6` | entero | lados de manzana de estrato 6 |
| `sin_vivienda` | entero | lados de manzana sin vivienda |
| `lados_total` | entero | suma de los lados de manzana por estrato (1 a 6) |
| `estrato_moda_original` | texto | estrato moda tal como viene en el CSV |
| `estrato` | decimal | estrato moda validado (1 a 6; nulo si NR) |
| `pureza_estrato` | decimal | max(lados 1..6)/suma(lados 1..6), sin «Sin vivienda» |

- `data/silver/silver_integrated.csv` · 5146 filas · 1048708 bytes · sha256 `bc1d1c6bd4bb3f6278a423751e63323b69ebc583f82a3f5f2b1b0d491d09ae4d`

| columna | tipo | descripción |
|---|---|---|
| `objectid` | entero | identificador de la construcción (único) |
| `comuna` | texto | códigos catastrales de 2 dígitos (texto; nulos si venían en blanco) |
| `barrio` | texto | códigos catastrales de 2 dígitos (texto; nulos si venían en blanco) |
| `codigo_barrio` | texto | llave `int(comuna)*100 + int(barrio)` (texto) |
| `nombre_barrio_csv` | texto | nombre del barrio en el CSV de estrato 2015 (nulo si no cruza) |
| `cruza_llave` | lógico | la llave existe en el CSV de estrato |
| `estrato` | decimal | estrato moda del barrio (1-6; nulo si NR o sin llave) |
| `pureza_estrato` | decimal | max(lados 1..6)/suma(lados 1..6) del barrio, sin "Sin vivienda" |
| `n_con_datos_estrato` | decimal | conteos por estrato (construcciones con datos) y bandera k < 30 |
| `n_severos_estrato` | decimal | conteos por estrato (construcciones con datos) y bandera k < 30 |
| `muestra_baja` | lógico (con nulos) | conteos por estrato (construcciones con datos) y bandera k < 30 |
| `npisos` | decimal | número de pisos (entero nullable) y bandera de 0 pisos |
| `npisos_cero` | lógico (con nulos) | número de pisos (entero nullable) y bandera de 0 pisos |
| `indice_escombros` | decimal | índice continuo de cambio de textura (nulo si sin datos) |
| `estado_estructural` | texto | etiqueta original y clase (`escombros`, `techo`, `sin_cambio`, `sin_datos`) |
| `clase_dano` | texto | etiqueta original y clase (`escombros`, `techo`, `sin_cambio`, `sin_datos`) |
| `sin_datos` | lógico | sin datos satelitales |
| `severo_estricto` | lógico (con nulos) | banderas D7; **nulas** (no falsas) si `sin_datos` |
| `dano_visible` | lógico (con nulos) | banderas D7; **nulas** (no falsas) si `sin_datos` |
| `geom_duplicada` | lógico | comparte geometría idéntica con otra construcción (18 filas, 9 pares) |
| `lon` | decimal | centroide a 7 decimales (EPSG:4326) |
| `lat` | decimal | centroide a 7 decimales (EPSG:4326) |
| `codigo_poligono` | texto | polígono WFS 2026 donde cae el centroide y si su código coincide con `codigo_barrio` |
| `nombre_poligono` | texto | polígono WFS 2026 donde cae el centroide y si su código coincide con `codigo_barrio` |
| `coincide_poligono` | lógico (con nulos) | polígono WFS 2026 donde cae el centroide y si su código coincide con `codigo_barrio` |
| `nombre_validado` | lógico (con nulos) | el nombre CSV 2015 coincide (similitud ≥ 0,85) con el polígono dominante del código |

- `data/silver/silver_orphans_left.csv` · 6 filas · 597 bytes · sha256 `04bc074bf0332eae832bff81a8be4cc3dc60857bd5398851989444a5aa00b126`

| columna | tipo | descripción |
|---|---|---|
| `objectid` | entero | identificador de la construcción |
| `comuna` | decimal | código de comuna |
| `barrio` | decimal | código de barrio |
| `codigo_barrio` | decimal | llave construida |
| `codigo_poligono` | entero | código del polígono 2026 donde cae el centroide |
| `nombre_poligono` | texto | nombre del polígono |
| `clase_dano` | texto | clase de la capa |
| `causa` | texto | motivo por el que la construcción no cruza con el CSV |

- `data/silver/silver_orphans_right.csv` · 295 filas · 15289 bytes · sha256 `da95c33f59f5112afb1952ab9a1824a0a791726292d7a164350ad78aa9c4c05a`

| columna | tipo | descripción |
|---|---|---|
| `codigo_barrio` | entero | código del barrio (llave del JOIN) |
| `barrio` | texto | nombre del barrio en el CSV 2015 |
| `lados_e1` | entero | lados de manzana de estrato 1 |
| `lados_e2` | entero | lados de manzana de estrato 2 |
| `lados_e3` | entero | lados de manzana de estrato 3 |
| `lados_e4` | entero | lados de manzana de estrato 4 |
| `lados_e5` | entero | lados de manzana de estrato 5 |
| `lados_e6` | entero | lados de manzana de estrato 6 |
| `sin_vivienda` | entero | lados de manzana sin vivienda |
| `lados_total` | entero | suma de los lados de manzana por estrato (1 a 6) |
| `estrato_moda_original` | texto | estrato moda tal como viene en el CSV |
| `estrato` | decimal | estrato moda validado (1 a 6; nulo si NR) |
| `pureza_estrato` | decimal | max(lados 1..6)/suma(lados 1..6), sin «Sin vivienda» |

- `data/silver/quality_report.json` · — filas · 13253 bytes · sha256 `fa66f7f26ff6b6da5255dd364228afab650a540f9cd60e1f509d8c93e84c1120`

### Gold

Tablas finales para análisis y servicio; diccionario de gold_final leído de docs/KPIs.md.

- `data/gold/gold_final.csv` · 5146 filas · 1074233 bytes · sha256 `496ab49eb76ada329df916266befd327febfd8f6333636e9e37fbed234cbc7a9`

| columna | tipo | descripción |
|---|---|---|
| `objectid` | entero | identificador de la construcción (único) |
| `comuna` | texto | códigos catastrales de 2 dígitos (texto; nulos si venían en blanco) |
| `barrio` | texto | códigos catastrales de 2 dígitos (texto; nulos si venían en blanco) |
| `codigo_barrio` | texto | llave `int(comuna)*100 + int(barrio)` (texto) |
| `nombre_barrio_csv` | texto | nombre del barrio en el CSV de estrato 2015 (nulo si no cruza) |
| `cruza_llave` | lógico | la llave existe en el CSV de estrato |
| `estrato` | decimal | estrato moda del barrio (1-6; nulo si NR o sin llave) |
| `pureza_estrato` | decimal | max(lados 1..6)/suma(lados 1..6) del barrio, sin "Sin vivienda" |
| `n_con_datos_estrato` | decimal | conteos por estrato (construcciones con datos) y bandera k < 30 |
| `n_severos_estrato` | decimal | conteos por estrato (construcciones con datos) y bandera k < 30 |
| `muestra_baja` | lógico (con nulos) | conteos por estrato (construcciones con datos) y bandera k < 30 |
| `npisos` | decimal | número de pisos (entero nullable) y bandera de 0 pisos |
| `npisos_cero` | lógico (con nulos) | número de pisos (entero nullable) y bandera de 0 pisos |
| `indice_escombros` | decimal | índice continuo de cambio de textura (nulo si sin datos) |
| `estado_estructural` | texto | etiqueta original y clase (`escombros`, `techo`, `sin_cambio`, `sin_datos`) |
| `clase_dano` | texto | etiqueta original y clase (`escombros`, `techo`, `sin_cambio`, `sin_datos`) |
| `sin_datos` | lógico | sin datos satelitales |
| `severo_estricto` | lógico (con nulos) | banderas D7; **nulas** (no falsas) si `sin_datos` |
| `dano_visible` | lógico (con nulos) | banderas D7; **nulas** (no falsas) si `sin_datos` |
| `geom_duplicada` | lógico | comparte geometría idéntica con otra construcción (18 filas, 9 pares) |
| `lon` | decimal | centroide a 7 decimales (EPSG:4326) |
| `lat` | decimal | centroide a 7 decimales (EPSG:4326) |
| `codigo_poligono` | texto | polígono WFS 2026 donde cae el centroide y si su código coincide con `codigo_barrio` |
| `nombre_poligono` | texto | polígono WFS 2026 donde cae el centroide y si su código coincide con `codigo_barrio` |
| `coincide_poligono` | lógico (con nulos) | polígono WFS 2026 donde cae el centroide y si su código coincide con `codigo_barrio` |
| `nombre_validado` | lógico (con nulos) | el nombre CSV 2015 coincide (similitud ≥ 0,85) con el polígono dominante del código |

- `data/gold/kpis_gold.csv` · 23 filas · 8606 bytes · sha256 `6db3dbeeeffbbf5c087c9b71fd5b8c51f280d0a4c8c14b37e084418f9fbf2e4c`

| columna | tipo | descripción |
|---|---|---|
| `kpi_id` | texto | identificador del indicador (K1 a K6) |
| `nombre` | texto | nombre del indicador |
| `valor` | decimal | valor del indicador (tasa, razón o proporción) |
| `numerador` | decimal | numerador (por ejemplo, severos estrictos) |
| `denominador` | decimal | denominador (construcciones con datos satelitales) |
| `grupo` | texto | grupo o corte del indicador |
| `fecha_corte` | texto | fecha de corte de la capa |
| `fuente` | texto | fuente declarada del cálculo |
| `ic95_inf` | decimal | límite inferior del intervalo al 95 % |
| `ic95_sup` | decimal | límite superior del intervalo al 95 % |
| `n_sin_datos` | decimal | construcciones sin datos satelitales |
| `pct_sin_datos` | decimal | proporción sin datos satelitales |
| `muestra_baja` | lógico | verdadero si hay menos de 30 severos |
| `cota_inf` | decimal | cota inferior por «sin datos» |
| `cota_sup` | decimal | cota superior por «sin datos» |
| `nota` | texto | nota del indicador |

- `data/gold/kpis_sensibilidad.csv` · 107 filas · 12942 bytes · sha256 `0cf75f2d2fabcb56f1b6bded38a4afb02d7ede0bf0c6e550b55dd3b8c6aca40e`

| columna | tipo | descripción |
|---|---|---|
| `escenario` | texto | escenario de sensibilidad (S0 a S5) |
| `kpi_id` | texto | indicador |
| `grupo` | texto | grupo o corte |
| `k` | decimal | severos |
| `n` | decimal | construcciones con datos |
| `tasa` | decimal | k / n |
| `ic95_inf` | decimal | límite inferior del intervalo al 95 % |
| `ic95_sup` | decimal | límite superior del intervalo al 95 % |
| `nota` | texto | descripción del escenario |


## Cómo lo defendemos

- **Qué afirmamos:** cada fuente usada tiene su publicador, URL, formato, autenticación, límites, columnas, cobertura, fechas, licencia, snapshot con sha256 y riesgos. [Evidencia en el repo: `docs/entrega_3/catalogo_fuentes.json`]
- **Con qué evidencia:** el catálogo se genera del manifiesto y la prueba `tests/test_catalogo.py` compara sha256, filas y bytes; `GET /fuentes` devuelve el mismo JSON.
- **Qué NO afirmamos:** que las licencias estén verificadas jurídicamente (las tomamos de los catálogos y la fecha de consulta está indicada); que las cifras de prensa sean oficiales.
- **Pregunta probable:** «¿cómo saben que el catálogo coincide con lo descargado?» **Respuesta:** porque se genera desde el manifiesto de Bronze y una prueba compara huellas, filas y bytes.
