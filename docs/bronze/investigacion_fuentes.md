# Investigación de fuentes — Avance 2 ETL (UAO) · Sismo 10-ago-2026

**Fecha de consulta:** 15-oct-2026 · **Etiquetas:** `[CONFIRMADO url]` visto en respuesta real o documentación oficial · `[INFERIDO]` razonable, no visto · `[NO VERIFICADO]` no se pudo acceder. Todo `[INFERIDO]`/`[NO VERIFICADO]` está convertido en una tarea **V#** (sección 8) que se resuelve en la verificación previa de las fuentes.

**Limitación de herramienta:** `web_fetch` descarta los parámetros de consulta de URLs no escritas literalmente por el usuario, y `datos.cali.gov.co` y `cali.gov.co` bloquean el fetch por detección de bots. Por eso **no se obtuvo muestra de filas** de la API principal (Socrata) ni de SGC ArcGIS; sí se obtuvo de USGS y de RUD.

---

## 1. Evento confirmado

| Campo | Valor | Etiqueta |
|---|---|---|
| ID USGS | `us6000tjl2` | [CONFIRMADO earthquake.usgs.gov/fdsnws/event/1/query?format=csv&starttime=2026-08-10…] |
| Fecha/hora | 2026-08-10 12:34:28 UTC = 07:34 hora Colombia | [CONFIRMADO USGS CSV; https://www2.sgc.gov.co/Noticias/Paginas/SGC-actualiza-la-informacion-sobre-el-sismo-ocurrido-en-San-Jose-del-Palmar-Choco.aspx] |
| Magnitud | Mww 7,4 | [CONFIRMADO USGS CSV; SGC] |
| Epicentro | 4,8601° N, 76,2558° O ("4 km SSW of San José del Palmar", Chocó). Primeras versiones: 4,8436° N, 76,2422° O | [CONFIRMADO USGS CSV; https://kohrco.com/casos/sismo-choco-2026] |
| Profundidad | 116,13 km (USGS hoy, actualizado 2026-10-12); 110,3 km (versión previa USGS); 103 km (SGC) | [CONFIRMADO]. Hay revisiones: usar el valor vigente de USGS y registrar la fecha de consulta |
| Intensidad máx. SGC | 7 ("daño severo") | [CONFIRMADO SGC] |
| Nacional | 331 fallecidos en 16 departamentos (UNGRD, corte 10-sep); RUD: 409 municipios y 364.670 familias (17-sep) | [CONFIRMADO https://www.elespectador.com/salud/de-la-emergencia-del-terremoto-a-una-propuesta-epidemiologica-para-cuidar-mejor-a-cali/ ; https://datosdelterremoto.org/data/public/rud.json] |
| Cali (cifras que cambian) | 878 verificadas/5.545 reportes (24 total, 127 parcial, 192 estructural) → 920/7.797 (18-ago; 24/177/197) → 998/8.030 (20-ago; 24/177/221) → 1.335 visitas (30-ago; 398 parcial) → 506 parcial (reporte 40, 8-sep) → 3.403 predios ATC-20: 1.078 rojo, 1.272 amarillo, 1.053 verde (~22-sep) → ~14.400 reportes, ~5.000 visitados en fase 1 (11-oct) | [CONFIRMADO El País Cali: …alcaldia-de-cali-desmiente-que-el-censo…, …alcaldia-de-cali-entrega-balance-de-gestion-tras-el-sismo…, …tras-el-sismo-cali-evalua-miles-de-estructuras…; Pulzo; cali.gov.co/boletines/publicaciones/193673] |
| Zonas más golpeadas según Alcaldía (11-oct) | Cuarto de Legua, La Flora, comunas 19, 17 y 2 | [CONFIRMADO El País Cali, 11-oct-2026] |

**Conclusión:** el evento existe y coincide con el Avance 1. Los conteos de Cali **no son estables**: los tempranos mezclan "reportados" (46 colapsos totales, 14-ago) con "verificados" (24). Cada KPI debe llevar su fecha de corte.

**Hallazgo clave:** no se encontró una tabla oficial descargable de daño por barrio/comuna. El Repositorio Oficial (https://www.cali.gov.co/gobierno/publicaciones/193607/terremoto-de-cali-repositorio-oficial-de-informacion/) publica boletines y balances (web). El fetch fue bloqueado, así que **solo se vio el snippet** [NO VERIFICADO si ofrece descargas].

---

## 2. Fichas de fuentes

### F1 · Socrata SODA — "Impacto Satelital en Edificaciones por Terremoto. Cali 2026" (datos.gov.co `5vy8-gpw8`) — **API PRINCIPAL**
- **URL:** https://www.datos.gov.co/dataset/Impacto-Satelital-en-Edificaciones-por-Terremoto-C/5vy8-gpw8 [CONFIRMADO, página pública]. Endpoint API previsto: `https://www.datos.gov.co/resource/5vy8-gpw8.json` [INFERIDO, patrón Socrata; no abierto].
- **Metodología:** GEOBIA; geometrías de la capa oficial "Construcciones" (Geoportal Catastral Cali, 2024); diferencial de textura (desv. estándar focal, banda roja) entre imagen pre (Vantor, 30 cm, 22-mar-2026) y post (Planet SkySat, 50 cm, 11-ago-2026); **acotado por spatial join a los polígonos de afectación preliminar del visor IGAC** [CONFIRMADO, descripción del dataset]. No reemplaza inspección de ingeniería [CONFIRMADO].
- **Formatos:** CSV, XML, XLSX [CONFIRMADO, `distribution` del dataset].
- **Auth/límites:** datasets públicos de Socrata no exigen token; hay throttling sin app token y `$limit` por página con tope alto (típico 50.000) [INFERIDO]. Paginación `$limit/$offset/$order` [INFERIDO].
- **Columnas, tipos, llave, volumen, cobertura, licencia, última actualización:** [NO VERIFICADO] (V1–V3, V7). Publicado hace ~42 días [CONFIRMADO, metadato de búsqueda].
- **Sesgo a registrar:** como solo incluye edificaciones dentro de polígonos de afectación preliminar, la "tasa de daño" es **condicional a estar en zona de afectación**, no una prevalencia de toda la ciudad.
- **Muestra:** ninguna (limitación de herramienta).

### F2 · CSV — "Estratificación socioeconómica según estrato, por barrio en Cali 2015" (datos.gov.co `6esn-pmy5`) — **CSV PRINCIPAL**
- **URL:** https://www.datos.gov.co/dataset/Estratificaci-n-socioecon-mica-seg-n-estrato-por-b/6esn-pmy5 [CONFIRMADO]. Espejo: https://datos.cali.gov.co/dataset/estratificacion-socioeconomica-segun-estrato-por-barrio-en-cali-2015 [CONFIRMADO en resultado de búsqueda; fetch bloqueado por bots].
- **Contenido:** "Distribución de lados de manzana, según estrato por barrio, año 2015"; distribución `text/csv` [CONFIRMADO]. Publicador: DAPM Cali. Última actualización: 8-jul-2019 [CONFIRMADO]. Licencia: CC Attribution Share-Alike [CONFIRMADO en datos.cali.gov.co].
- **Cobertura:** Cali; 335 barrios en 6 estratos según DAPM (15 de estrato 6, 36 de 5, 33 de 4, 117 de 3, 88 de 2, 46 de 1) [CONFIRMADO https://www.elpais.com.co/cali/cuantos-barrios-tiene-cali-lista-completa-organizada-por-estratos-sociales-2414.html].
- **Columnas esperadas:** Barrio, Estrato 1…6, Total, Estrato moda [INFERIDO, por analogía con el CSV por comunas]. [NO VERIFICADO] (V4).
- **Vigencia:** datos de 2015; hay una capa de estrato urbano actualizada en jun-2025 solo como servicio WMS [CONFIRMADO https://datos.cali.gov.co/dataset/estrato-urbano-expansion]. Riesgo de desfase temporal.

### F3 · CSV respaldo — "Área barrios de Cali 2015" (`wpm5-26dr`) y "Estratificación por comunas 2015"
- `wpm5-26dr`: barrio, área, perímetro, **estrato moda 2015**; CSV; última actualización 27-nov-2018; licencia CC0 [CONFIRMADO https://www.datos.gov.co/dataset/-rea-barrios-de-Cali-2015/wpm5-26dr ; http://datos.cali.gov.co/dataset/area-barrios-de-cali-2015].
- Comunas: columnas `Comuna, Estrato 1…Estrato 6, Total, Estrato moda` [CONFIRMADO diccionario en https://datos.cali.gov.co/dataset/estratificacion-socioeconomica-urbana-por-comunas-en-cali-ano-2015/resource/88f7450b-59d7-42f5-aaa3-010dbca9976b]. Solo 22 filas (sirve para llave por comuna).
- Acceso programático desde `requests`: [NO VERIFICADO] (el fetch fue bloqueado por detección de bots) → V8.

### F4 · USGS FDSN Event — **solo contexto del evento**
- **Docs:** https://earthquake.usgs.gov/fdsnws/event/1/ [CONFIRMADO]. Formatos `csv/geojson/xml/text/kml`; `limit` 1–20.000; superar 20.000 devuelve HTTP 400 [CONFIRMADO]. `count` disponible. Sin autenticación [CONFIRMADO: ambas consultas respondieron].
- **Conteo real** (2026-08-10 a 08-31, lat 3,0–5,5, lon −77,5 a −75,0, M≥2,5): **11** [CONFIRMADO https://earthquake.usgs.gov/fdsnws/event/1/count?...].
- **Muestra real (CSV, 22 columnas: `time,latitude,longitude,depth,mag,magType,nst,gap,dmin,rms,net,id,updated,place,type,horizontalError,depthError,magError,magNst,status,locationSource,magSource`):**

| time (UTC) | lat | lon | depth km | mag | place | id |
|---|---|---|---|---|---|---|
| 2026-08-10T12:34:28Z | 4,8601 | −76,2558 | 116,13 | 7,4 mww | 4 km SSW of San José del Palmar | us6000tjl2 |
| 2026-08-10T13:18:09Z | 4,8770 | −76,3246 | 91,13 | 5,0 mb | 10 km WSW of San José del Palmar | us6000tjm4 |
| 2026-08-10T15:01:31Z | 4,9924 | −76,3671 | 97,87 | 4,3 mb | 18 km NW of San José del Palmar | us6000tjms |
| 2026-08-11T15:43:41Z | 4,9121 | −76,3300 | 101,65 | 4,1 mb | 10 km W of San José del Palmar | us6000tjzx |
| 2026-08-29T10:50:23Z | 4,5132 | −76,7395 | 60,64 | 4,5 mb | 18 km SW of Sipí | us7000tcth |

- **Limitación decisiva:** 11 filas y sin llave hacia barrio/municipio (solo `place` en texto). Descartada como fuente del JOIN. El feed continuo `…/earthquakes/feed/v1.0/csv.php` cubre una ventana móvil (≤30 días); el evento tiene 66 días [INFERIDO por aritmética de fechas]; no se usa.

### F5 · SGC ArcGIS REST — Mapa de Intensidades Evaluadas (**respaldo/Plan B**)
- Raíz: https://srvags.sgc.gov.co/arcgis/rest/services?f=pjson responde, ArcGIS 10.91, con carpetas `eval_int`, `Mapa_Intensidad_Maxima_Observada_Colombia`, `Zonas_amenaza_Sismica_NR10`, `Zonificacion_Sismica_Intensidad_Esperada`, `catalogo_sismos`, `PortalSismos`, `SIMMA`, entre otras [CONFIRMADO].
- Capa `eval_int/mapa_eval_int/FeatureServer/0` ("FRSN.EVAL_INT_CAPA_INT"): puntos; `MaxRecordCount` 1000; **`Supports Pagination: false`**; formatos JSON/GeoJSON; consultas avanzadas, estadísticas y orden permitidos; extent en EPSG:4326; sin token [CONFIRMADO https://srvags.sgc.gov.co/arcgis/rest/services/eval_int/mapa_eval_int/FeatureServer/0].
- **Campos:** `OBJECTID, INTENSIDAD (smallint 2–8), ID_SISMO (str 50), X, Y, SITIO (str 250), ID_CENTRO_POBLADO (double), FECHA_ACTUALIZACION, INICIADOR` [CONFIRMADO].
- **Filas del evento, ID_SISMO del 10-ago, presencia de Cali, equivalencia ID_CENTRO_POBLADO↔DIVIPOLA:** [NO VERIFICADO] (V9).
- Granularidad: por sitio/centro poblado, **no por barrio**: sirve a escala municipal.

### F6 · Otras rutas candidatas del usuario
- `https://services1.arcgis.com/Og2nrTKe5bptW02d/arcgis/rest/services/MAPAGEOLOGIA/FeatureServer/1/query`: capa "Fallas"; formulario de consulta con filtro espacial (`geometry`, `spatialRel`) y salida JSON/GeoJSON/PBF [CONFIRMADO]. Geología a escala nacional; sin llave a barrio. **Descartada** como fuente del JOIN; posible contexto geotécnico futuro.
- `https://srvags.sgc.gov.co/arcgis/rest/services/SIMMA/Capas_Generales/MapServer`: grillas, áreas de estudio, **Municipios (capa 5)**, Departamentos, Límite Nacional; `MaxRecordCount` 1000; CRS 4686 [CONFIRMADO]. No es amenaza por barrio. Útil solo como polígonos municipales del Plan B (campos [NO VERIFICADO], V9).

### F7 · Socrata `hbdu-4927` — **DESCARTADA**
- `https://www.datos.gov.co/api/views/hbdu-4927` devuelve `assetType: federated_href`, `columns: []`, "Portal de Datos Abiertos // SGC", licencia CC BY 4.0, `Last Update` 2025-09-30: es un **enlace** al portal ArcGIS Hub del SGC [CONFIRMADO].
- `https://www.datos.gov.co/resource/hbdu-4927.json` devuelve **HTTP 400** [CONFIRMADO]. No contiene filas.

### F8 · RUD (UNGRD) vía monitor "Datos del terremoto" — **Plan B, tabla izquierda**
- `https://datosdelterremoto.org/data/public/rud.json` abre sin autenticación; datos derivados CC BY 4.0; fuente original https://rud.gestiondelriesgo.gov.co/ (no abierta) [CONFIRMADO]. Es un **archivo JSON estático** de un monitor de un solo mantenedor, no la API oficial de UNGRD.
- Estructura: `generado, fuente, serie[], municipios[], detalle_diario{fecha:[…]}`. En `municipios`: `departamento, municipio, familias, personas, viv_destruidas, viv_averiadas, nohabitables, habitables, poblacion_2026, tasa_pct, delta_familias, nuevo`. **Sin código DIVIPOLA** en esas filas [CONFIRMADO].
- **409 municipios** en la última captura; capturas diarias del 16-ago al 17-sep, luego cerrada [CONFIRMADO].
- **Muestra real (5 de 409):**

| departamento | municipio | familias | personas | viv_destruidas | viv_averiadas | poblacion_2026 | tasa_pct |
|---|---|---|---|---|---|---|---|
| RISARALDA | PEREIRA | 47.211 | 110.882 | 4.341 | 0 | 487.820 | 22,73 |
| VALLE DEL CAUCA | CALI | 45.138 | 97.337 | 879 | 16.357 | 2.269.983 | 4,288 |
| VALLE DEL CAUCA | BUENAVENTURA | 31.654 | 67.590 | 1.782 | 16.613 | 335.217 | 20,16 |
| QUINDÍO | ARMENIA | 21.935 | 41.197 | 1.147 | 2.476 | 307.103 | 13,41 |
| CHOCÓ | QUIBDÓ | 14.889 | 34.608 | 1.202 | 8.296 | 143.332 | 24,15 |

- **Hallazgos de calidad:** nombres repetidos entre departamentos (LA UNIÓN, ARGELIA, BOLÍVAR, CÓRDOBA, SAN LUIS, GRANADA, VENECIA, CABRERA, ARMENIA, BALBOA, EL TAMBO, SUCRE…) → la llave exige departamento+municipio; ceros que pueden significar "no reportado" (Pereira `viv_averiadas = 0`); registro **declarativo**, no daño verificado [CONFIRMADO].
- `crosscheck.csv` del mismo sitio tiene solo 7 filas [CONFIRMADO]: inservible para el JOIN.

### F9 · DIVIPOLA (Plan B, tabla derecha)
- Dataset Socrata "DIVIPOLA - Códigos municipios" (`gdxc-w37w`, 1.122 filas según nota de terceros) [INFERIDO; no abierto]. DANE publica `Listados_DIVIPOLA.xlsx` (hojas Departamentos y Municipios) vía https://geoportal.dane.gov.co/servicios/descarga-y-metadatos/datos-geoestadisticos/?cod=112 [CONFIRMADO en https://www.dane.gov.co/files/pqr/Respuesta-202510034970.pdf; el archivo no fue descargado].
- Código: 2 dígitos departamento, 5 dígitos municipio [CONFIRMADO https://epiverse-trace.r-universe.dev/ColOpenData/doc/manual.html]. Riesgo: ceros a la izquierda → leer como `str`.

### F10 · Polígonos de barrios (auxiliar de llave espacial, Plan A)
- "Barrios de Santiago de Cali": WMS + capa descargable RAR; actualizado 19-ene-2026 [CONFIRMADO https://datos.cali.gov.co/es/dataset/servicio-wms-barrios-de-cali ].
- GeoServer IDESC (WFS) con capa `idesc:mc_barrios` [CONFIRMADO en https://directory.spatineo.com/service/15905/; host `idesc.cali.gov.co:8080` — disponibilidad actual [NO VERIFICADO]].
- ArcGIS Server de IDESC: https://geoportal.cali.gov.co/agserver/rest/services/IDESC lista servicios (`cali_cifras_2014_2015`, `sisben`, etc.) [CONFIRMADO]; **no se identificó** un servicio de barrios [NO VERIFICADO]. CRS de IDESC: 102796 (MAGNA Cali), no 4326 [CONFIRMADO en geoportal.cali.gov.co/agserver/…/IDESC/movilidad/FeatureServer].

### F11 · Descartadas
- Copernicus EMSR916 / ICube-SERTIT: solo 21 + 94 edificios clasificados en zonas parciales de Cali, sin edificios en común; SERTIT es de uso no comercial [CONFIRMADO https://datosdelterremoto.org/municipio/cali/].
- Repositorio Oficial de la Alcaldía: boletines web; fetch bloqueado [NO VERIFICADO] como fuente estructurada.

---

## 3. Matriz de decisión (0–3)

Ponderación: **llave de JOIN ×2** y **relevancia ×2** (máx. 24). Relevancia medida contra la pregunta refinada (Cali, estrato vs daño). Volumen: ideal 1.000–100.000 filas; las tablas dimensión (barrios) están exentas por diseño, pero se puntúan igual para no ocultar el hecho.

### 3.1 APIs

| Fuente | Acceso sin auth | Estabilidad y docs | Tabular legible | Volumen | Llave JOIN (×2) | Relevancia (×2) | **Total** |
|---|---|---|---|---|---|---|---|
| **F1 Socrata 5vy8** | 2 | 2 | 2 | 2 | 1→2 | 3→6 | **16** |
| F5 SGC eval_int | 3 | 2 | 3 | 1 | 2→4 | 1→2 | **15** |
| F8 RUD JSON | 3 | 1 | 3 | 2 | 1→2 | 1→2 | **13** |
| F4 USGS FDSN | 3 | 3 | 3 | 0 | 0→0 | 1→2 | **11** |
| F7 hbdu-4927 | 0 | 1 | 0 | 0 | 0 | 0 | **1** |

**Evidencia:** F1 acceso 2 (página pública confirmada, `/resource` no abierto); estabilidad 2 (portal MinTIC, publicado hace ~42 días); tabular 2 (CSV/XLSX/XML confirmados, columnas no vistas); volumen 2 (edificaciones dentro de polígonos de afectación [INFERIDO] 1.000–100.000); llave 1 (barrio no confirmado; puede requerir paso espacial); relevancia 3 (única fuente a nivel de edificio en Cali). F5 acceso 3 (metadatos de capa sin token); estabilidad 2 (sin paginación); tabular 3 (campos vistos); volumen 1 (no se conoce el número de filas del evento); llave 2 (`ID_CENTRO_POBLADO` [INFERIDO] → DIVIPOLA); relevancia 1 (no discrimina dentro de Cali). F8 estabilidad 1 (un solo mantenedor, captura cerrada); llave 1 (nombres duplicados sin código). F4 volumen 0 (11 filas), llave 0.

**Sensibilidad:** la diferencia F1–F5 es de 1 punto y F1 contiene tres puntajes sin evidencia directa. **La elección de F1 es condicional a los criterios de aceptación de las fuentes** (sección 6.3).

### 3.2 CSV/Excel

| Fuente | Acceso | Estabilidad | Tabular | Volumen | Llave (×2) | Relevancia (×2) | **Total** |
|---|---|---|---|---|---|---|---|
| **F2 Estrato por barrio 2015 (6esn-pmy5)** | 3 | 2 | 2 | 1 | 2→4 | 3→6 | **18** |
| F3a Área barrios 2015 (wpm5-26dr) | 3 | 2 | 2 | 1 | 2→4 | 2→4 | **16** |
| F3b Estrato por comuna 2015 | 2 | 2 | 3 | 0 | 2→4 | 2→4 | **15** |
| F9 DIVIPOLA (Plan B) | 2 | 3 | 3 | 3 | 3→6 | 1→2 | **19** (solo sirve a Plan B) |

---

## 4. Selección

| Rol | Fuente | Razón |
|---|---|---|
| **API principal** | F1 Socrata `5vy8-gpw8` | Única fuente abierta a nivel de edificio en Cali; permite agregar a barrio y cruzar con estrato (KR1, KR4). |
| **CSV principal** | F2 `6esn-pmy5` | Mismo origen institucional (DAPM Cali) que los barrios; estrato por barrio y nombres de barrio como llave. |
| **Respaldo CSV** | F3a `wpm5-26dr`; si falla el nivel barrio, F3b (comuna) | Estrato moda por barrio con CSV confirmado; comuna da cobertura aunque se pierda granularidad. |
| **Respaldo API (Plan B)** | F8 RUD JSON + F5 SGC ArcGIS + F9 DIVIPOLA | Única combinación con muestra confirmada (RUD), cumple ≥200 filas (409). Cambia la escala a municipio. |
| **Auxiliar de llave** | F10 polígonos de barrios | Solo si F1 no trae barrio/comuna. |
| **Contexto** | F4 USGS | Ficha del evento en README; no entra al JOIN. |

---

## 5. Pregunta de negocio del ETL
Ver `comprension_proyecto1.md`. Plan B la reformula así: *¿cómo se distribuye el daño declarado (RUD) frente a población e intensidad SGC en los 409 municipios con registro, y qué posición ocupa Cali?*

---

## 6. Viabilidad del JOIN

### 6.1 Plan A (Cali)
- **Izquierda:** edificaciones evaluadas (F1), una fila por edificación, con barrio asignado.
- **Derecha:** estrato por barrio (F2), una fila por barrio.
- **Llave:** `barrio_norm` = mayúsculas, sin tildes ni puntuación, espacios colapsados, alias de prefijos ("URB.", "BARRIO", numerales). Si F1 no trae barrio, `barrio_norm` se obtiene por **punto-en-polígono** de la geometría de F1 con los polígonos F10.
- **Tipo:** `LEFT JOIN` (se preservan las edificaciones sin estrato como huérfanos medibles).
- **Cobertura esperada** (todo [INFERIDO]): asignación edificación→barrio ≥95 % (solo falla en bordes); coincidencia de nombre barrio↔estrato 85–95 % tras alias (ambas capas son de DAPM, pero 2015 vs 2024–26 puede diferir en barrios nuevos o renombrados). **Meta ≥80 % de la izquierda.**
- **Gold ≥200 filas:** se cumple a nivel edificación si F1 tiene ≥200 edificaciones (probable, [NO VERIFICADO]). A nivel barrio puede quedar entre 50 y 200: el Gold se publica a **grano edificación**; los KPI se agregan por barrio y estrato.
- **Server-side ArcGIS:** `geometry + spatialRel` resuelve punto-en-polígono sin geopandas, pero es **una consulta por punto**. Con miles de edificaciones es lento y frágil. Se prefiere descargar los polígonos una vez (≈335) y resolver localmente con `shapely`.
- **Riesgos:** (1) F1 no trae barrio ni geometría usable; (2) estrato 2015 vs realidad actual; (3) la variable de daño es proxy satelital (no ATC-20); (4) sesgo de selección: solo edificaciones dentro de polígonos de afectación; (5) falacia ecológica (se asigna el estrato moda del barrio al edificio); (6) `datos.cali.gov.co` bloquea bots (usar el espejo `datos.gov.co`); (7) CRS distinto (102796 vs 4326).

### 6.2 Plan B (municipal)
- **Izquierda:** RUD, 409 municipios. **Derecha 1:** DIVIPOLA por (`departamento_norm`, `municipio_norm`) → código de 5 dígitos. **Derecha 2:** SGC eval_int agregado por municipio (máx. y media de `INTENSIDAD`; municipio = primeros 5 dígitos de `ID_CENTRO_POBLADO` [INFERIDO], o punto-en-municipio con SIMMA capa 5 en servidor).
- **Cobertura esperada:** RUD↔DIVIPOLA ≥97 % [INFERIDO; los nombres RUD son oficiales en mayúsculas, con casos tipo "PIENDAMÓ - TUNÍA", "BOGOTÁ, D.C."]; municipio↔intensidad SGC **[NO VERIFICADO]**, el mayor riesgo; si <80 %, reportar Gold con intensidad nula y documentar.
- **Gold:** 409 filas (≥200 ✓). **Limitación:** no contesta la pregunta del estrato; contesta daño declarado vs intensidad vs población, con Cali como caso.

### 6.3 Criterios de aceptación de las fuentes (se evalúan en la verificación previa de las fuentes, sin preguntas abiertas)
| Criterio | Condición | Si falla |
|---|---|---|
| G1 | `/resource/5vy8-gpw8.json` responde 200 sin token y `count(*)` ≥ 200 | Plan B |
| G2 | F1 tiene campo `barrio`/`comuna` **o** geometría/lat-lon utilizable | Plan B |
| G3 | CSV de estrato descarga y trae ≥250 barrios con columna de estrato | usar F3a; si falla F3a, usar F3b (comuna) solo si G2 trae comuna; si no, Plan B |
| G4 | Si G2 se cumple solo por geometría: polígonos de barrios obtenibles (F10) | usar comuna (F3b) si hay polígonos de comuna; si no, Plan B |
| G5 | Cobertura del JOIN de prueba ≥80 % sobre una muestra de 500 filas | agregar alias (máx. 20 reglas, documentadas); si persiste, Plan B |

---

## 7. Decisiones de diseño

| # | Decisión | Alternativas | Razón | Riesgo |
|---|---|---|---|---|
| D1 | Escala principal: edificio→barrio en Cali | Municipal (RUD); comuna (22 filas) | Alineada con el Proyecto 1; el grano edificación da >200 filas | Depende de campos no verificados (V1, V7) |
| D2 | API: Socrata `5vy8-gpw8` | USGS; SGC eval_int; RUD JSON | Relevancia y grano; USGS solo trae 11 filas | Sin muestra; criterios G1/G2 |
| D3 | CSV: estrato por barrio (F2) | Comuna; estrato moda | Mantiene el barrio como llave | Datos de 2015 |
| D4 | Llave: `barrio_norm`; espacial solo si falta | Código de barrio; comuna | Un nombre normalizado es explicable a nivel estudiante | Alias y barrios nuevos |
| D5 | Punto-en-polígono local con `shapely` | `geopandas`; consulta ArcGIS por punto; `within_polygon` de Socrata | Una dependencia liviana; evita miles de peticiones | Instalación en Windows; plan: ray casting en Python puro |
| D6 | Bronze = respuestas crudas por página + manifiesto (url, parámetros, UTC, status, filas, sha256); sin sobrescribir | Un solo CSV consolidado | Trazabilidad e idempotencia | Más archivos |
| D7 | Variable de daño: umbral de "severo" definido tras el EDA de Bronze y documentado | Fijar el umbral a priori | No se conoce el dominio de la columna | Discrecionalidad; se justifica en DECISIONES.md |
| D8 | USGS solo en README/contexto | Incluirlo en el JOIN | Sin llave espacial a barrio | Ninguno |
| D9 | Plan B se activa por los criterios de aceptación, no por preferencia | Decidirlo a mano | Evita arrastrar una fuente no accesible | Cambio de pregunta de negocio |
| D10 | Salida: CSV en `data/` + SQLite | Solo CSV | Permite recalcular KPI con SQL de forma independiente | Más código |

**Supuestos de stack ajustados (declarados):** además de pandas, requests, openpyxl, pyyaml, sqlite3, matplotlib y pytest se autorizan: `python-dotenv` (lectura de `.env`), `tzdata` (zona America/Bogota en Windows), `shapely` (solo si la llave es espacial), y `jupyter/nbconvert/ipykernel` como infraestructura de notebooks. `geopandas` no se usa. Voz de los notebooks: primera persona plural.

---

## 8. Verificaciones pendientes (la verificación previa de las fuentes)

| ID | Pendiente | Etiqueta actual |
|---|---|---|
| V1 | `GET /resource/5vy8-gpw8.json?$limit=5` sin token; columnas, tipos, dominio de la clase de daño | [NO VERIFICADO] |
| V2 | `count(*)`, tope de `$limit`, throttling con/sin app token | [INFERIDO] |
| V3 | `/api/views/5vy8-gpw8.json`: `rowsUpdatedAt`, licencia, columnas | [NO VERIFICADO] |
| V4 | CSV de `6esn-pmy5`: URL de descarga, columnas, nº de barrios, codificación | [INFERIDO] |
| V5 | Descarga de `wpm5-26dr` y del CSV por comunas | [INFERIDO] |
| V6 | Polígonos de barrios (WFS `idesc:mc_barrios`, ArcGIS o RAR): URL viva, campos, CRS | [NO VERIFICADO] |
| V7 | Formato de geometría y CRS de F1; ¿trae barrio/comuna? | [NO VERIFICADO] |
| V8 | `requests` con `User-Agent` contra `datos.cali.gov.co` y el espejo `datos.gov.co` | [NO VERIFICADO] |
| V9 | SGC eval_int: `count`, valores distintos de `ID_SISMO`, evento del 10-ago, puntos de Cali, `ID_CENTRO_POBLADO`↔DIVIPOLA; campos de SIMMA capa 5 | [NO VERIFICADO] |
| V10 | Repetir conteo USGS (=11) y registrar profundidad vigente de `us6000tjl2` | [CONFIRMADO hoy; re-chequear] |
| V11 | `rud.json` accesible desde la máquina del equipo; sha256 y nº de municipios | [CONFIRMADO desde la herramienta; re-chequear] |
| V12 | DIVIPOLA (`gdxc-w37w` o `Listados_DIVIPOLA.xlsx`): URL, hojas, ceros a la izquierda | [INFERIDO] |
| V13 | Instalación de `shapely` y `tzdata` en el equipo | [NO VERIFICADO] |
| V14 | Fecha de corte exacta del Avance 1 (878/5.545) | [INFERIDO: ~17–18 ago] |

---

## 9. URLs consultadas (literales)
**Evento:** https://cnnespanol.cnn.com/2026/08/10/colombia/terremoto-sismo-san-jose-choco-orix · https://www2.sgc.gov.co/Noticias/Paginas/SGC-actualiza-la-informacion-sobre-el-sismo-ocurrido-en-San-Jose-del-Palmar-Choco.aspx · https://kohrco.com/casos/sismo-choco-2026 · https://earthquaketrack.com/quakes/2026-08-10-12-34-28-utc-7-4-110 · https://en.wikipedia.org/wiki/List_of_earthquakes_in_2026 · https://www.dallasnews.com/espanol/al-dia/noticias/article/sismo-colombia-epicentro-san-jose-palmar-choco-22381947.php
**USGS:** https://earthquake.usgs.gov/fdsnws/event/1/ · …/count?starttime=2026-08-10T00:00:00&endtime=2026-08-31T23:59:59&minlatitude=3.0&maxlatitude=5.5&minlongitude=-77.5&maxlongitude=-75.0&minmagnitude=2.5 · …/query?format=csv&(mismos parámetros)
**Daños Cali:** https://www.elpais.com.co/cali/terremoto-en-cali-en-vivo-autoridades-suspenden-el-pico-y-placa-debido-a-la-emergencia-1007.html · https://www.elpais.com.co/cali/alcaldia-de-cali-desmiente-que-el-censo-de-damnificados-por-el-terremoto-excluya-a-familias-por-su-estrato-1913.html · https://www.elpais.com.co/cali/alcaldia-de-cali-entrega-balance-de-gestion-tras-el-sismo-mas-de-3400-edificaciones-evaluadas-y-45000-familias-damnificadas-2338.html · https://www.elpais.com.co/cali/tras-el-sismo-cali-evalua-miles-de-estructuras-y-alista-la-reconstruccion-el-plan-es-que-de-aqui-a-diciembre-se-coloque-el-primer-ladrillo-1159.html · https://www.cali.gov.co/boletines/publicaciones/193673/cifras-y-datos-actualizados-del-terremoto-en-cali/ · https://www.cali.gov.co/gobierno/publicaciones/193607/terremoto-de-cali-repositorio-oficial-de-informacion/ (bloqueada)
**datos.gov.co / datos.cali.gov.co:** https://www.datos.gov.co/dataset/Impacto-Satelital-en-Edificaciones-por-Terremoto-C/5vy8-gpw8 · https://www.datos.gov.co/dataset/Estratificaci-n-socioecon-mica-seg-n-estrato-por-b/6esn-pmy5 · https://www.datos.gov.co/dataset/-rea-barrios-de-Cali-2015/wpm5-26dr · https://www.datos.gov.co/api/views/hbdu-4927 · https://www.datos.gov.co/resource/hbdu-4927.json (400) · https://datos.cali.gov.co/es/dataset/servicio-wms-barrios-de-cali · https://datos.cali.gov.co/dataset/estrato-urbano-expansion
**SGC / ArcGIS:** https://srvags.sgc.gov.co/arcgis/rest/services?f=pjson · https://srvags.sgc.gov.co/arcgis/rest/services/eval_int/mapa_eval_int/FeatureServer/0 · …/FeatureServer/0/query · https://services1.arcgis.com/Og2nrTKe5bptW02d/arcgis/rest/services/MAPAGEOLOGIA/FeatureServer/1/query · https://srvags.sgc.gov.co/arcgis/rest/services/SIMMA/Capas_Generales/MapServer · https://geoportal.cali.gov.co/agserver/rest/services/IDESC · https://directory.spatineo.com/service/15905/
**RUD / DIVIPOLA:** https://datosdelterremoto.org/municipio/cali/ · https://datosdelterremoto.org/data/public/rud.json · https://datosdelterremoto.org/data/public/crosscheck.csv · https://www.dane.gov.co/files/pqr/Respuesta-202510034970.pdf · https://epiverse-trace.r-universe.dev/ColOpenData/doc/manual.html
