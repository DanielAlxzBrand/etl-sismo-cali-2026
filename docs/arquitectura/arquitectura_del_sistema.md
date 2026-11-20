# Arquitectura del sistema ETL del sismo de Cali

## 1. Portada y metadatos
| Campo | Valor |
|---|---|
| Título | Arquitectura del sistema ETL medallion del sismo M7.4 de Cali (10 de agosto de 2026) |
| Versión y fecha | 0.2, 2026-11-18 |
| Autor y owner técnico | Daniel Alexander Brand García |
| Revisión de la documentación | Jhoan Sebastián Castellanos Mayor, 2026-11-18 |
| Aprobadores | Daniel Alexander Brand García, Jhoan Sebastián Castellanos Mayor y Diego Fernando Gordillo Londoño; la aprobación se registra al pasar el estado a Aprobado |
| Estado | Revisado |
| Repositorio | aún no está publicado; cuando se publique, esta tabla enlazará a sus issues (ver el [README](../../README.md#19-contacto-y-responsables)) |
| Registros de decisión | los 15 ADR de [adr/](adr/), listados en la sección 10; las decisiones completas están en [docs/DECISIONES.md](../DECISIONES.md) (D1 a D110) |

Este documento describe cómo está construido el sistema hoy y por qué lo construimos así. Lo escribimos como estudiantes que hicimos el proyecto: donde algo no existe decimos «no lo hicimos» o «no aplica» y damos la razón, y no rellenamos con contenido genérico. Para cada cifra o afirmación indicamos de dónde sale (un archivo, una evidencia o una decisión del repositorio), y varias cifras las comparan pruebas automáticas con lo medido. Lo que no pudimos verificar, o depende de la máquina de quien lo ejecute, lo marcamos como límite.

## 2. Resumen ejecutivo
**Propósito.** Un pipeline ETL con capas Bronze, Silver y Gold que integra una capa satelital de impacto en construcciones y el estrato socioeconómico por barrio, calcula indicadores con intervalos de confianza y los entrega por una API de solo lectura, un panel y dos bases de datos, con orquestación en Airflow.

**Problema que resuelve.** Después del sismo del 10 de agosto de 2026 circulan cifras oficiales distintas y con fechas de corte distintas. Quisimos medir, con datos abiertos y con la incertidumbre explícita, si la proporción de construcciones con cambio satelital severo cambia entre los estratos 1 a 6 del barrio o se concentra por zona. El resultado y sus límites están en [docs/gold/resultados.md](../gold/resultados.md).

**Alcance.**
- Entra: 5.146 construcciones de 7 comunas de Cali, el estrato de 2015 por barrio, seis indicadores (K1 a K6) con seis escenarios de sensibilidad, una API, un panel, dos almacenes (SQLite y MySQL) y un DAG de cuatro tareas.
- No entra: una evaluación estructural de los predios, la Comuna 2 ni las demás comunas ausentes, modelos predictivos, despliegue en la nube y pruebas con personas usuarias (aún sin sesiones reales).

**Características principales.**
- Bronze inmutable con manifiesto de sha256 y una línea base de nueve archivos que se compara byte a byte.
- Idempotencia: repetir la extracción o la carga no duplica nada.
- API de solo lectura (11 rutas GET) y panel de 8 páginas que solo habla con la API.
- Mínimo privilegio: tres cuentas de MySQL y un repositorio montado en solo lectura en Airflow.
- Cifras de los documentos vigiladas por pruebas: **1467 pruebas** automáticas.

## 3. Contexto y drivers
**Objetivos.** Entregar un análisis reproducible de impacto sísmico por zonas, con incertidumbre explícita, y que se pueda repetir de punta a punta ([docs/estrategia/03_objetivo_alcance_okr_kpi.md](../estrategia/03_objetivo_alcance_okr_kpi.md) y [05_mvp_criterios_aceptacion.md](../estrategia/05_mvp_criterios_aceptacion.md)).

**Stakeholders reales** (mapeo completo en [02_stakeholders.md](../estrategia/02_stakeholders.md)):
| Stakeholder | Relación con el sistema |
|---|---|
| Habitantes de las zonas afectadas | usuarios objetivo del análisis; necesitan entender qué se mide y con qué incertidumbre |
| Entidad de gestión del riesgo del municipio | segundo grupo de usuarios objetivo; podría usar el análisis para priorizar estudios |
| Alcaldía de Cali (evaluaciones estructurales) | produce las evaluaciones por predio; sus cifras son contexto y no se mezclan con las nuestras |
| DAPM de Cali, IDESC y Fondo Adaptación | publican las fuentes que usamos (estrato, polígonos y capa satelital) |
| Comunidad académica | tercer grupo de usuarios objetivo |
| Equipo del proyecto | construye y mantiene el sistema |

No hubo sesiones con personas usuarias que probaran el sistema (ver la sección 17).

**Restricciones.**
- Frescura: no hay requisito de frescura. Los datos son una captura única descargada el 2026-10-15 (hora de Bogotá); la capa se editó por última vez el 2026-09-02.
- Presupuesto: el repositorio no define ninguno. El costo es tiempo del equipo y una máquina local; los precios son parámetros vacíos ([docs/finanzas/estructura_costos.md](../finanzas/estructura_costos.md)).
- Regulaciones: en ninguna capa hay nombres, documentos ni datos de contacto de personas; Bronze trae columnas catastrales con identificadores de predio, que Silver descarta (regla R10), y Gold conserva las coordenadas del centroide de cada construcción (el detalle está en la sección 12). No hacemos afirmaciones jurídicas; lo que cada publicador declara sobre licencias está en [docs/bronze/atribucion_y_terminos_de_datos.md](../bronze/atribucion_y_terminos_de_datos.md).
- Entorno: Windows 11 con PowerShell y Python 3.13; en otros sistemas no lo probamos.

**Volumen actual (medido).**
| Qué | Valor | Origen |
|---|---|---|
| Construcciones | 5.146 (4.711 con datos satelitales) | `data/gold/gold_final.csv` |
| Barrios en el CSV de estrato | 346, más 23 filas resumen | `data/silver/silver_estrato_barrio.csv` |
| Archivos de Bronze | 8 líneas de manifiesto | `data/bronze/manifest.jsonl` |
| Tamaño de `data/` | 10,6 MB | [recursos_medidos.csv](../finanzas/recursos_medidos.csv), 2026-11-14 |
| Base SQLite | 1,6 MB | el mismo archivo |
| Filas en MySQL | 5.655 en 7 tablas | [EV-102](../evidencias/modo_completo/EV-102_capturas_de_daniel.txt) |

**Nota sobre las filas de MySQL.** Las 5.655 filas en 7 tablas son las 5.622 filas de datos (`barrio_estrato` 346, `construccion` 5.146, `kpi` 23 y `kpi_sensibilidad` 107) más 27 de `comuna`, 1 de `corrida` y 5 de `corrida_archivo`. Los 5 archivos de corrida son las entradas de la carga relacional, `silver_estrato_barrio.csv`, `gold_final.csv`, `kpis_gold.csv`, `kpis_sensibilidad.csv` y `quality_report.json`, y no archivos de Bronze. La tabla `comuna` es un catálogo: se llena con las comunas de los 346 barrios del CSV de estrato, que cubre toda Cali, y con las de las construcciones; por eso tiene 27 filas aunque el análisis use 7 comunas (03, 09, 10, 17, 18, 19 y 20), que están contenidas en esas 27. Los códigos son 01 a 22, 51, 52, 53, 54 y 56; el repositorio no documenta qué son los códigos 51 a 56, y el nombre de cada fila lo genera el código («Comuna 51»), no una fuente oficial.

**Proyección a 12 o 24 meses.** No proyectada: la fuente es una captura única del evento, no crece sola, y no tenemos una segunda fuente que cambie con el tiempo. Si la fuente se refresca, `--refresh` crea un snapshot nuevo del mismo tamaño aproximado.

**Requisitos no funcionales prioritarios** (prioridad del equipo, derivada de las decisiones registradas): reproducibilidad de las cifras, trazabilidad de cada cifra hasta un archivo con sha256, honestidad sobre los límites del análisis, mínimo privilegio en los accesos, y que quien solo quiere ver las cifras no necesite Docker ni MySQL.

## 4. Objetivos y no objetivos
### Objetivos
1. Extraer la capa satelital, el CSV de estrato y los polígonos de barrios, y conservarlos sin modificar.
2. Limpiar, tipar e integrar por código de barrio, conservando los registros sin pareja.
3. Calcular K1 a K6 con intervalos, cotas por falta de datos y seis escenarios de sensibilidad.
4. Entregar los resultados por una API de solo lectura, un panel y dos almacenes con historial.
5. Orquestar el pipeline con un DAG que no pueda alterar la línea base.
6. Poder repetirlo todo en otra máquina con la guía de instalación.

### No objetivos
Cada uno es una decisión de alcance, con su razón.
| No lo hicimos | Razón |
|---|---|
| Carga incremental | la fuente es una captura única; una carga completa de unas 5.600 filas tarda menos de un segundo ([ADR-004](adr/adr-004_historial_por_corrida_idempotente.md)) |
| Dimensiones de cambio lento (SCD) | no llegan cambios que registrar; cada corrida es una copia completa |
| Despliegue en la nube | todo corre en una máquina local y el panel no está desplegado; los precios de nube no existen en el proyecto |
| Infraestructura como código con Terraform | no hay nada que aprovisionar; el compose y el Dockerfile declaran lo que sí se levanta |
| Integración continua | no hay repositorio remoto publicado; el procedimiento de entrega es manual (sección 14) |
| Alertas externas (Slack, PagerDuty, Prometheus) | no hay un servicio desplegado que alguien deba vigilar |
| Modelos predictivos | el proyecto calcula indicadores estadísticos; no entrena modelos |
| Evaluación estructural de predios | nuestro indicador es un proxy satelital y no se mezcla con las inspecciones de la Alcaldía |

## 5. Principios arquitectónicos
Solo los que de verdad aplicamos, cada uno con el lugar donde se ve.
| Principio | Cómo lo aplicamos |
|---|---|
| Separación de capas | Bronze guarda lo descargado, Silver limpia y une, y Gold lee solo `silver_integrated.csv`, nunca Bronze ([ADR-014](adr/adr-014_gold_lee_solo_silver.md)) |
| Bronze inmutable | archivos abiertos en modo exclusivo y manifiesto con sha256 ([ADR-001](adr/adr-001_bronze_crudo_inmutable.md)) |
| Idempotencia | repetir `--stage extract` verifica y no descarga; repetir una carga responde `ya_cargada` ([ADR-004](adr/adr-004_historial_por_corrida_idempotente.md)) |
| Reproducibilidad | versiones exactas y nueve archivos de línea base comparados byte a byte ([ADR-007](adr/adr-007_reproducibilidad_de_versiones.md)) |
| Contratos con pruebas | esquemas SQL con prueba de paridad, modelos pydantic de la API y guardianes de las cifras de los documentos ([ADR-008](adr/adr-008_pruebas_sin_servidor_y_regresion.md)) |
| Mínimo privilegio | tres cuentas de MySQL, API de solo lectura y repositorio montado en solo lectura ([ADR-010](adr/adr-010_api_de_solo_lectura_local.md), [ADR-011](adr/adr-011_cuentas_de_mysql_minimo_privilegio.md)) |
| Falla temprano y a la vista | `validar_bronze` detiene el DAG si un sha256 no coincide; cada tarea compara su salida con lo versionado ([ADR-006](adr/adr-006_copia_de_trabajo_y_comparacion.md)); si Airflow cambia su compose, el generador falla en lugar de escribir otra cosa |
| Declarar los límites | cada documento de análisis dice qué afirma y qué no demuestra, y los recuadros de alcance acompañan a cada resultado |

Infraestructura declarada: el `Dockerfile` y los compose de `orquestacion/` y `servicios/` describen lo que se levanta en Docker. No usamos IaC de nube porque no hay nube.

## 6. Vista de alto nivel
### Diagrama de contexto
```
 FUENTES EXTERNAS (solo lectura, por HTTPS)

 +-----------------+      +-----------------+      +-----------------+
 | Capa ArcGIS     |      | CSV de estrato  |      | Poligonos WFS   |
 | Fondo Adaptacion|      | DAPM Cali       |      | IDESC           |
 +--------+--------+      +--------+--------+      +--------+--------+
          |                        |                        |
          +------------------------+------------------------+
                                   |
                                   v
 +-------------------------------------------------------------------+
 |             SISTEMA ETL DEL SISMO DE CALI (una maquina)           |
 |  pipeline medallon, dos almacenes, API de solo lectura, panel     |
 |  y orquestacion con Airflow                                       |
 +-------------------------------------------------------------------+
          ^                        |                        |
          |                        v                        v
 +-----------------+      +-----------------+      +-----------------+
 | Equipo del      |      | Persona que     |      | Quien administra|
 | proyecto        |      | consulta        |      | MySQL           |
 | ejecuta y       |      | lee el panel o  |      | teclea la clave |
 | revisa          |      | la API          |      | de root         |
 +-----------------+      +-----------------+      +-----------------+
```

### Diagrama de contenedores
```
 +----------------------------------+
 | Fuentes externas (HTTPS)         |
 +----------------+-----------------+
                  | descarga: main.py --stage extract
                  v
 MAQUINA LOCAL (Windows 11)

 [Pipeline] ------------> [Archivos de data/] --------------> [SQLite]
 main.py                  Bronze, Silver y Gold               etl_sismo.db
     ^                             |                             |
     | copia, solo lectura         | carga relacional            | lee, por omision
     |                             v                             v
 [Airflow] --- carga ---------->[MySQL] ------ lee ------->   [API] <-- HTTP GET --  [Panel]
 DAG, :8080                     sismo_cali                    :8000                  :8501
                                   ^
                                   | SELECT, cuenta de solo lectura
                                   |
                             [phpMyAdmin]
                               :8081
```

### Cajas del diagrama de contenedores
| Caja | Qué es |
|---|---|
| Pipeline | `main.py` con las etapas `extract`, `transform` y `gold`; la última también carga `etl_sismo.db` |
| Archivos de data/ | `data/bronze/`, `data/silver/` y `data/gold/`, versionados en Git |
| SQLite | `data/gold/etl_sismo.db`, almacén de referencia con 4 tablas |
| MySQL | base `sismo_cali`, almacén relacional con historial en 7 tablas |
| API | servicio FastAPI de solo lectura con 11 rutas GET, en el puerto 8000 |
| Panel | aplicación Streamlit de 8 páginas, en el puerto 8501, que solo habla con la API |
| Airflow | DAG `medallon_etl_sismo` en Docker (siete contenedores), interfaz en el puerto 8080 |
| phpMyAdmin | visor de MySQL con una cuenta de solo `SELECT`, en el puerto 8081 |

**Flujos principales.** El pipeline descarga y transforma hasta dejar los archivos de `data/`; la carga escribe SQLite y, aparte, MySQL; la API lee de uno de los dos almacenes y el panel lee de la API; Airflow ejecuta una copia del pipeline y la compara con lo versionado; phpMyAdmin solo mira MySQL.

**Límites del sistema.** Lo que levanta el proyecto publica solo en `127.0.0.1`: la API, el panel, la interfaz de Airflow (y Flower, si se activa) y phpMyAdmin. Lo comprueban las pruebas de la configuración y de los compose y las evidencias en vivo [EV-016](../evidencias/api/EV-016_respuestas_api.txt), [EV-064](../evidencias/endurecimiento/EV-064_airflow_en_vivo.txt), [EV-085](../evidencias/servicios/EV-085_phpmyadmin_en_vivo.txt) y [EV-102](../evidencias/modo_completo/EV-102_capturas_de_daniel.txt); no hay una comprobación de sockets en escucha. El servicio MySQL es del equipo y el proyecto no lo configura: no sabemos en qué interfaces escucha. Lo que sí acotamos es quién puede iniciar sesión: ninguna cuenta tiene origen `%` (D46, D60 y D65). No hay autenticación en la API porque el servicio no sale del equipo. Las fuentes se consultan por HTTPS y nada se envía a un tercero.

## 7. Arquitectura de datos
### Modelo de capas y su justificación
| Capa | Granularidad | Qué hace | Salida |
|---|---|---|---|
| Bronze | una respuesta cruda por petición, una línea de manifiesto por archivo | guarda lo descargado sin tocarlo | `data/bronze/` y `manifest.jsonl` |
| Silver | una fila por construcción (`OBJECTID`) y una por barrio del CSV | limpia, tipa, calcula la llave, une y valida con 18 reglas (R01 a R18) | cinco tablas y `quality_report.json` |
| Gold | una fila por construcción en `gold_final.csv`; una fila por grupo en los indicadores | calcula K1 a K6 y los escenarios S0 a S5 | `gold_final.csv`, `kpis_gold.csv`, `kpis_sensibilidad.csv` y `etl_sismo.db` |

Separamos en capas para poder demostrar de dónde sale cada cifra: lo descargado no cambia, lo limpio se puede regenerar desde lo descargado, y los indicadores se regeneran desde lo limpio. Gold lee solo Silver; el paso espacial que necesita la validación de la llave vive en Silver para que Gold no lea Bronze.

### Estrategia de modelado
- **Gold:** una tabla ancha por construcción (`gold_final`), con la llave, el estrato, las banderas de daño y los datos de validación; los indicadores van aparte en dos tablas pequeñas.
- **SQLite:** cuatro tablas, `silver_integrated`, `gold_final`, `kpis_gold` y `kpis_sensibilidad`, con el mismo contenido que los CSV.
- **MySQL:** modelo relacional de siete tablas con claves primarias y foráneas y restricciones: `corrida`, `corrida_archivo`, `comuna`, `barrio_estrato`, `construccion`, `kpi` y `kpi_sensibilidad` ([docs/almacenamiento/modelo_datos.md](../almacenamiento/modelo_datos.md)).

### Estrategia de carga
Cada ejecución regenera Silver y Gold completos desde Bronze y reemplaza las tablas de `etl_sismo.db`. En MySQL cada carga con una entrada distinta es una corrida completa; repetir la misma entrada responde `ya_cargada` sin escribir ([ADR-004](adr/adr-004_historial_por_corrida_idempotente.md)). No hay carga incremental ni SCD.

### Particionamiento, clustering, índices y ordenamiento
No hay particionamiento ni clustering: con 5.146 construcciones no los necesitamos. Lo que sí existe: 8 índices secundarios en el esquema de MySQL (`src/load/sql/esquema_mysql.sql`) y el orden estable por `OBJECTID` en la extracción y en `gold_final.csv`.

### Historial y datos tardíos
El historial es la suma de corridas en MySQL y los snapshots inmutables de Bronze (`snap_<fecha UTC>`). Los datos tardíos no aplican: no hay un flujo de datos que llegue después. `python main.py --stage extract --refresh` crea un snapshot nuevo sin tocar el anterior, y después hay que regenerar Silver y Gold; los resultados pueden cambiar si la fuente cambió.

### Contratos de datos
| Contrato | Dónde vive | Calidad y frescura |
|---|---|---|
| Respuestas de la API | modelos pydantic en `src/api/esquemas.py` | pruebas de estructura y de coincidencia con las salidas |
| Esquemas SQL | `src/load/sql/esquema_mysql.sql` y `esquema_sqlite.sql` | prueba de paridad entre los dos y con el diccionario |
| Reporte de calidad de Silver | `data/silver/quality_report.json` y los umbrales de `config/config.yaml` | cobertura de la llave (se registra, no detiene), mínimo de filas de Gold (detiene), indicadores en rango |
| Salidas del pipeline | los nueve archivos de la línea base con sha256 | `tests/test_pipeline_reproducible.py` |

Responsable de mantenerlos: Daniel Alexander Brand García. No hay un acuerdo de nivel de servicio de frescura; la fecha de corte (la de la última edición de la capa, 2026-09-02) la entrega `/health`.

### Linaje
El manifiesto de Bronze liga cada archivo con su URL, su fecha y su sha256. Cada regla de Silver cita el hallazgo del análisis exploratorio que la justifica. La trazabilidad por ítem enlaza archivos, pruebas y evidencias en [docs/checklist/trazabilidad.md](../checklist/trazabilidad.md), y la línea base de nueve archivos detecta cualquier cambio que altere una salida.

### Catálogo de datos
El catálogo de fuentes (`docs/bronze/catalogo_fuentes.json` y [catalogo_fuentes_metadatos.md](../bronze/catalogo_fuentes_metadatos.md)) se genera desde el manifiesto; el diccionario de columnas de Gold está en [docs/gold/KPIs.md](../gold/KPIs.md) y el de MySQL se genera del SQL. No usamos una herramienta de catálogo de datos.

## 8. Componentes y responsabilidades
La columna Responsable es la persona que se encarga de mantenerlo de aquí en adelante, por acuerdo del equipo; no describe quién lo construyó.
| Componente | Responsabilidad | Tecnología | Responsable |
|---|---|---|---|
| Extracción | descargar las tres fuentes, guardar Bronze y su manifiesto, verificar sha256 | `requests`, `src/extract/` | Daniel Alexander Brand García |
| Orquestación | ejecutar el pipeline programado sobre una copia y compararlo con lo versionado | Airflow 3.3.2, Docker Compose, `dags/` y `orquestacion/` | Daniel Alexander Brand García |
| Transformación | limpiar, calcular la llave, unir y calcular los indicadores | `pandas`, `numpy`, `shapely`, `src/transform/` | Daniel Alexander Brand García |
| Calidad | reglas de Silver, reporte de calidad, pruebas, matriz de casos y registro de defectos | `pytest`, `coverage`, `quality_report.json` | Daniel Alexander Brand García |
| Almacenamiento | SQLite de referencia y MySQL relacional con historial | SQLite, MySQL 8.0, `pymysql`, `src/load/` | Daniel Alexander Brand García |
| Serving | API de solo lectura y panel | FastAPI, uvicorn, Streamlit, `src/api/` y `src/panel/` | Daniel Alexander Brand García |
| Observabilidad | registro de ejecución, `/health`, `/calidad` e interfaz de Airflow | `logging`, `src/logger.py` | Daniel Alexander Brand García |
| Pruebas con personas usuarias | protocolo, guion, análisis de sesiones (aún sin sesiones reales) | `docs/usuarios/` y `scripts/usuarios/` | Diego Fernando Gordillo Londoño |
| Documentación y demostración | mantener la documentación y el guion y la grabación de la demostración | Markdown en `docs/` | Jhoan Sebastián Castellanos Mayor |

## 9. Flujos detallados
### Flujo de datos
```
 ArcGIS --+                                  +--> gold_final.csv ---------+
 CSV -----+--> BRONZE --> SILVER --> GOLD ---+--> kpis_gold.csv           +--> etl_sismo.db (SQLite)
 WFS -----+    (crudo)    (limpio    (K1 a K6)+--> kpis_sensibilidad.csv   |
                          y unido)                                        +--> MySQL (una corrida)
                             |
                             +--> huerfanos (izquierda y derecha) y quality_report.json
```

### Secuencia del camino feliz del DAG
```
 Planificador      Trabajador (copia de trabajo)     Repositorio (solo lectura)        MySQL
      |                      |                                |                          |
      | 06:00 Bogota         |                                |                          |
      |--------------------->| validar_bronze                 |                          |
      |                      |--- copia src, config, data --->|                          |
      |                      |--- compara manifiesto -------->|                          |
      |                      |    verifica 8 sha256           |                          |
      |--------------------->| transformar_a_silver           |                          |
      |                      |    run_transform en la copia   |                          |
      |                      |--- compara 6 archivos Silver ->|                          |
      |--------------------->| integrar_a_gold                |                          |
      |                      |    run_gold en la copia        |                          |
      |                      |--- compara 3 archivos Gold --->|                          |
      |--------------------->| cargar_datawarehouse           |                          |
      |                      |    load_to_sqlite en la copia  |                          |
      |                      |--- compara 4 tablas ---------->|                          |
      |                      |--- carga relacional (cuenta sismo_airflow) -------------->|
      |                      |<------------------ ya_cargada o una corrida nueva -------|
      |                      |    borra la copia de trabajo   |                          |
      |<---- 4 tareas en success                              |                          |
```

### Secuencia del camino de fallo y la recuperación
```
 Disparo manual con el parametro fallo_inducido (falla la tercera tarea)
 Planificador      Trabajador (copia de trabajo)     Repositorio (solo lectura)        MySQL
      |                      |                                |                          |
      |--------------------->| validar_bronze: success        |                          |
      |--------------------->| transformar_a_silver: success  |                          |
      |--------------------->| integrar_a_gold                |                          |
      |                      |    lee fallo_inducido y lanza RuntimeError                |
      |                      |    ANTES de producir salidas   |                          |
      |                      |    borra la copia de trabajo   |                          |
      |<---- integrar_a_gold: failed                          |                          |
      |      cargar_datawarehouse: upstream_failed (no se ejecuta)                       |
      |      ejecucion: failed; repositorio y MySQL sin cambios                          |
      |                                                                                  |
 Nuevo disparo, sin parametro (recuperacion)                                             |
      |--------------------->| las 4 tareas en success                                   |
      |                      |--- carga relacional ------------------------------------>|
      |                      |<-------------------------------------- ya_cargada -------|
```
La evidencia de este camino es [EV-042](../evidencias/orquestacion/EV-042_fallo_inducido_y_recuperacion.txt): `integrar_a_gold` falla en 0,2 s, `cargar_datawarehouse` queda `upstream_failed`, no quedan copias de trabajo y MySQL conserva la misma única corrida.

### Backfill
No hay. Hay una sola captura de la fuente, con su fecha. El DAG usa `catchup=False`, así que no recupera ejecuciones que ocurrieron con el equipo apagado; un refresco crea un snapshot nuevo y no reescribe el pasado.

### Cambios de esquema de la fuente, tal como se manejan hoy
No hay una validación explícita de columnas ni una prueba que simule ese cambio, y no podemos afirmar qué mensaje daría una columna que falte o cambie de nombre. Lo que sí existe: la extracción guarda el metadato de la capa (`capa_meta.json`, con sus campos) y los conteos antes y después de descargar, y las pruebas de Bronze comprueban que las páginas sumen el conteo oficial. Silver se detiene si aparece una etiqueta de `Estado_Estructural` que no conoce, si `OBJECTID` o el código de barrio dejan de ser únicos, si el CSV no se lee como UTF-8 o si hay nombres con codificación dañada. Como Bronze es inmutable y todo se calcula sobre el snapshot versionado, la fuente solo puede afectar al proyecto con `--refresh`.

## 10. Decisiones y ADR
Cada ADR vive en su archivo, con Contexto, Decisión, Consecuencias, las alternativas que se registraron entonces, las que hoy descartamos y su número D de origen. Los separamos a propósito: lo registrado en [DECISIONES.md](../DECISIONES.md) es lo que de verdad se consideró entonces; lo demás es razonamiento actual, rotulado como tal.
| ADR | Decisión | D de origen |
|---|---|---|
| [ADR-001](adr/adr-001_bronze_crudo_inmutable.md) | Bronze guarda lo descargado sin tocarlo | D6 |
| [ADR-002](adr/adr-002_llave_codigo_catastral.md) | La llave del JOIN es el código catastral, no el nombre del barrio | D4, D-FUENTES, sección «Llave del JOIN» |
| [ADR-003](adr/adr-003_almacenamiento_dual_sin_orm.md) | SQLite como almacén de referencia, MySQL como almacén relacional y SQL explícito sin ORM | D10, D19, D40, D41 |
| [ADR-004](adr/adr-004_historial_por_corrida_idempotente.md) | Cada carga a MySQL es una corrida completa, con clave determinista y una sola transacción | D43, D44, D45, D53 |
| [ADR-005](adr/adr-005_orquestacion_con_airflow.md) | Airflow en Docker orquesta el pipeline con cuatro tareas | D21, D57, D64, D92 |
| [ADR-006](adr/adr-006_copia_de_trabajo_y_comparacion.md) | El DAG trabaja sobre una copia y compara lo que produce con lo versionado | D58, D59 |
| [ADR-007](adr/adr-007_reproducibilidad_de_versiones.md) | Versiones exactas, pandas fijado en 3.0.6 y Python 3.13 como única versión soportada | D56, D81 |
| [ADR-008](adr/adr-008_pruebas_sin_servidor_y_regresion.md) | Pruebas sin servidor, casos generados y regresión por reintroducción | D49, D61, D62, D63 |
| [ADR-009](adr/adr-009_fuentes_por_criterios_de_aceptacion.md) | Las fuentes se aceptan por criterios verificados, sin bajar ningún umbral | D2, D9, D-FUENTES |
| [ADR-010](adr/adr-010_api_de_solo_lectura_local.md) | La API es de solo lectura, la fuerza la conexión y escucha solo en 127.0.0.1 | D18, D27, D28, D29, D52, D54 |
| [ADR-011](adr/adr-011_cuentas_de_mysql_minimo_privilegio.md) | Tres cuentas de MySQL con el mínimo privilegio y ningún origen abierto | D46, D60, D65, D67, D91 |
| [ADR-012](adr/adr-012_panel_solo_sobre_la_api.md) | El panel Streamlit solo habla con la API | D20, D69, D70 |
| [ADR-013](adr/adr-013_dos_modos_de_instalacion.md) | Dos modos de instalación y Python 3.13 solo en paralelo | D93 |
| [ADR-014](adr/adr-014_gold_lee_solo_silver.md) | Gold lee solo Silver y el paso espacial vive en Silver | D5, sección «Diseño», sección «Otras decisiones de Silver» |
| [ADR-015](adr/adr-015_calidad_de_datos_en_silver.md) | Silver valida la calidad con 18 reglas ligadas a hallazgos, un reporte y umbrales en la configuración | sección «Otras decisiones de Silver», D-FUENTES |

La separación de capas (Gold solo desde Silver) tiene su [ADR-014](adr/adr-014_gold_lee_solo_silver.md): DECISIONES.md la registró como una decisión de diseño sin alternativas, así que ese ADR dice «No se registraron alternativas.» y sus alternativas de hoy están rotuladas como razonamiento actual. D21 y D5 quedaron marcadas como modificadas en [D106](../DECISIONES.md): D21 planeó una variante de Airflow que no implementamos y D5 decía que `shapely` ya no se usaba, cuando la regla R09 de Silver sí lo usa.

La validación de la calidad en Silver (las 18 reglas, el reporte `quality_report.json` y los umbrales de `config/config.yaml`) tiene su [ADR-015](adr/adr-015_calidad_de_datos_en_silver.md): no tiene un D propio en DECISIONES.md, así que ese ADR lo dice, cita la sección «Otras decisiones de Silver» y el criterio G5 de D-FUENTES, dice «No se registraron alternativas.» y sus alternativas de hoy son razonamiento actual. También deja escrito lo que el repositorio no respalda, como que `min_edificios_por_barrio` no tiene decisión registrada.

## 11. Requisitos no funcionales
### Disponibilidad y resiliencia
- **SLA y SLO:** no los definimos. No hay un servicio desplegado ni personas usuarias que dependan de él; ponerles un número sería inventarlo.
- **Reintentos reales:** la descarga hace hasta 3 intentos por petición (reintenta si falla la conexión o la respuesta es 5xx), con una pausa de 0,5 s, 1 s y 1,5 s después de cada intento fallido, y espera como máximo 30 s por intento a que el servidor conteste (`timeout_s` de `config/config.yaml`, sección `http`, que acota la conexión y la espera de datos, no el tiempo total); el cliente del panel reintenta una vez un error de conexión; el DAG no tiene reintentos de tareas.
- **Circuit breakers:** no hay.
- **Idempotencia:** ver la sección 5.
- **Recuperación:** un fallo en el DAG se recupera volviendo a lanzarlo; una carga a MySQL ocurre en una sola transacción, así que no queda a medias.
- **Recuperación ante desastres:** no hay un plan formal. Lo que existe: los datos y las salidas están en Git, y `scripts/mysql/respaldar_restaurar.py` exporta cada tabla de MySQL a CSV con manifiesto sha256, restaura en la base de prueba y concilia ([EV-031](../evidencias/almacenamiento/EV-031_respaldo_restauracion.txt)): 5.655 filas en 7 tablas con huellas iguales tras restaurar.

### Rendimiento y escalabilidad
Mediciones locales de una máquina, con fecha ([EV-113](../evidencias/readme/EV-113_primera_vez_y_suite_en_clon_y_zip.txt) y [recursos_medidos.csv](../finanzas/recursos_medidos.csv)):
| Qué | Valor | Fecha |
|---|---|---|
| Pipeline completo | 2,9 s y 148 MB de pico (mediana de 3) | 2026-11-16 |
| Carga a MySQL de 5.622 filas de datos (las cuatro tablas de datos), fila a fila frente a lotes de 2.000 | 2,415 s frente a 0,715 s | 2026-11-14 |
| Latencia de la API, mediana por ruta (12 rutas, cliente del panel, [EV-055](../evidencias/panel/EV-055_mediciones_panel.txt)) | SQLite de 3,6 a 13,9 ms; MySQL de 4,8 a 126,9 ms | 2026-11-14 |
| Memoria en reposo de la API y el panel | unos 160 MiB | 2026-11-15 |
| Memoria en reposo de Airflow (siete contenedores) | 1.970 MiB | 2026-11-14 |

**Cuellos de botella medidos:** Airflow es lo que más memoria usa, por mucho; en las rutas que consultan el almacén, MySQL tiene una mediana de medianas de 88,2 ms frente a 6,1 ms con SQLite ([EV-032](../evidencias/almacenamiento/EV-032_api_mysql_vs_sqlite.txt)); `/fuentes` y `/calidad`, que no lo consultan, responden en pocos milisegundos con ambos, lo que sugiere que la diferencia viene de abrir una conexión nueva por solicitud. No aislamos ese costo con una medición propia.
**Estrategia de escalado:** no medimos más datos, más personas usuarias a la vez ni otro motor, y no prometemos cómo escala.
**Optimizaciones aplicadas:** carga por lotes de 2.000 filas, 8 índices secundarios en MySQL, caché del panel de 300 s, paginación de la API (50 por omisión, 200 como máximo) y extracción que no vuelve a descargar si Bronze existe.

### Costo
El modelo de costos tiene siete categorías y fórmulas con símbolos; los precios son parámetros vacíos en `config/parametros_costos.yaml`, y el análisis dice «costo no calculado: faltan parámetros» ([D84](../DECISIONES.md)). Los drivers son tiempo del equipo, cómputo y almacenamiento locales, y mantenimiento ante cambios de fuentes. Control: todo corre en una máquina local, así que no hay un gasto recurrente que controlar; no inventamos ninguna cifra monetaria.

### Mantenibilidad y evolución
- **Versionado:** Git con etiquetas por componente y commits en español; versiones exactas de las dependencias.
- **Impacto de un cambio:** una prueba compara en una copia los nueve archivos de la línea base con lo regenerado; después se busca el archivo cambiado en la trazabilidad para saber qué ítems, pruebas y evidencias lo citan.
- **Cambios de esquema:** ver la sección 9.
- **Deuda técnica conocida y reconocida:** el DAG sin reintentos; Airflow pesado para cuatro tareas; sin validación explícita de columnas de la fuente; dependencias transitivas sin fijar; dos almacenes que mantener sincronizados; el panel sin desplegar.

## 12. Seguridad y cumplimiento
- **Clasificación de datos:** datos abiertos. En ninguna capa hay nombres, documentos ni datos de contacto de personas. Trabajamos con huellas de construcciones y con el estrato por barrio: en Bronze vienen las columnas catastrales que publica la fuente, entre ellas identificadores de predio (`PREDIO`, `NUMEPRED` e `ID_PREDIO`); Silver los descarta (regla R10) y Gold conserva las coordenadas del centroide de cada construcción. Una huella identifica un lugar y no a quien vive allí; no evaluamos si, cruzada con otras fuentes, podría asociarse a una persona. Los secretos son las contraseñas de las tres cuentas de MySQL y los de Airflow: la clave Fernet, el secreto JWT y las contraseñas de la interfaz y de Postgres. El compose adaptado no trae ninguno escrito: los exige desde el `.env` de Airflow.
- **Controles de acceso:** tres cuentas de MySQL con el mínimo privilegio y ningún origen `%` (ver [ADR-011](adr/adr-011_cuentas_de_mysql_minimo_privilegio.md)); API y panel de solo lectura publicados solo en `127.0.0.1`. No hay IAM ni RBAC de nube porque no hay nube.
- **Cifrado:** en tránsito, las fuentes se descargan por HTTPS; lo que levanta el proyecto (API, panel, phpMyAdmin y Airflow) se publica solo en loopback y sin TLS. Las conexiones a MySQL (desde el pipeline y la API, y desde los contenedores por `host.docker.internal`) no usan TLS configurado por el proyecto; no medimos si el servidor lo negocia. En reposo no ciframos nada (CSV, SQLite, MySQL ni `.env`). Es una decisión de alcance: los datos son abiertos, sin nombres ni datos de contacto de personas, y todo corre en una máquina local; si el proyecto se despliega, hay que reconsiderarla.
- **Auditoría y registro de accesos:** la API registra cada solicitud (método, ruta, estado y duración) en el registro de ejecución; la interfaz de Airflow guarda un registro de auditoría de las acciones. No configuramos el registro de consultas de MySQL.
- **Cumplimiento regulatorio:** la clasificación de datos de arriba explica qué hay y qué no hay en cada capa, y no hacemos afirmaciones jurídicas. Las licencias de las fuentes se describen tal como las declara cada publicador, y el estrato de 2015 se trata con la condición más restrictiva por prudencia ([atribución](../bronze/atribucion_y_terminos_de_datos.md)).
- **Gestión de secretos:** los generan al azar `scripts/mysql/configurar_mysql.py` y `scripts/orquestacion/preparar_airflow.py` y los escriben solo en archivos `.env` que Git ignora. Los scripts que los crean imprimen los nombres de las variables y no sus valores, y el registro de ejecución oculta tokens, cabeceras de autenticación y valores de `.env`; pruebas y el escáner comprueban que no aparezcan. Quien necesita la contraseña de la interfaz de Airflow la lee de su `.env`. `scripts/escanear_secretos.py` revisa el árbol, el historial, los notebooks, los registros y el zip, y con `--canario-env` busca los valores reales sin imprimirlos ([política](../seguridad/gestion_credenciales.md)).
- **Límite conocido:** el origen `localhost` de una cuenta no acota por sí solo quién puede conectarse; la protección real es el mínimo privilegio más la contraseña aleatoria (D67).

## 13. Observabilidad
- **Qué se monitorea:** el estado y la duración de cada tarea del DAG, la salud del servicio (`/health`), la calidad de los datos (`/calidad` y `quality_report.json`) y el registro de cada ejecución.
- **Registro:** consola y un archivo por día en `logs/`, con el formato `fecha hora NIVEL módulo mensaje`; un filtro oculta tokens, cabeceras de autenticación y valores de `.env`. No hay rotación ni borrado automático.
- **Trazabilidad y linaje:** ver la sección 7.
- **Alertas:** no hay. Decidimos no incluir Slack, PagerDuty ni Prometheus porque no hay un servicio desplegado que alguien deba vigilar.
- **Tableros:** la interfaz de Airflow, `/health` y el panel.
- **Deriva de datos:** no la monitoreamos; los datos son una captura estática. **Deriva de esquema:** solo lo que detiene Silver (sección 9); no hay una comparación del esquema de la fuente entre descargas.

## 14. Despliegue y operaciones
- **Entornos:** uno solo, el local; no hay staging ni producción.
- **CI/CD:** no hay. No existe un repositorio remoto publicado. El procedimiento manual que repetimos: las pruebas completas en un clon y en el zip, `python scripts\make_dist.py` arma el zip por lista de inclusión, `python scripts\orquestacion\sincronizar_dag.py --verificar` comprueba que el DAG versionado y el de Airflow son idénticos, `python scripts\escanear_secretos.py` debe terminar en `hallazgos: 0`, y las etiquetas de Git por componente marcan cada cierre.
- **Estrategia de despliegue:** no aplica; no desplegamos en ningún servidor.
- **Ramas:** el trabajo vive en la rama `desarrollo`; la rama `master` conserva un punto anterior y no se ha vuelto a integrar. No hay rama `main`.
- **Configuración por entorno:** `config/config.yaml` y las variables de `.env` (12 nombres en `.env.example`, nunca valores).
- **Runbooks:** [guía de instalación](../instalacion/README.md), [modo mínimo](../instalacion/modo_minimo.md), [modo completo paso a paso](../instalacion/guia_modo_completo.md), [errores comunes](../instalacion/errores_comunes.md) y [operación de Airflow](../orquestacion/operacion.md).
- **Responsables y guardia:** responsables por componente en la sección 8; no hay guardia ni on-call.

## 15. Trade-offs
| Decisión difícil | Qué ganamos | Qué sacrificamos | Por qué esta opción |
|---|---|---|---|
| Airflow para cuatro tareas ([ADR-005](adr/adr-005_orquestacion_con_airflow.md)) | estados por tarea, programación y un DAG que se puede inspeccionar | 1.970 MiB en reposo y un modo completo pesado | el ítem de orquestación pide un DAG; lo compensamos con el modo mínimo, sin Docker |
| Corridas completas en vez de cambios ([ADR-004](adr/adr-004_historial_por_corrida_idempotente.md)) | comparar corridas con consultas simples y una carga idempotente | espacio que crece de forma lineal | con unas 5.600 filas por corrida y una fuente que no cambia, el espacio es irrelevante |
| Comparar byte a byte con la línea base ([ADR-006](adr/adr-006_copia_de_trabajo_y_comparacion.md) y [ADR-007](adr/adr-007_reproducibilidad_de_versiones.md)) | demostrar que Airflow y el entorno no cambian las cifras | rigidez: una versión de pandas distinta rompe la comparación | preferimos ver el fallo que aceptar una diferencia que no explicamos |
| SQL explícito sin ORM ([ADR-003](adr/adr-003_almacenamiento_dual_sin_orm.md)) | siete tablas que se leen completas y menos dependencias | más SQL escrito a mano | el esquema es pequeño y la revisión completa es más valiosa que la comodidad |
| API sin autenticación ([ADR-010](adr/adr-010_api_de_solo_lectura_local.md)) | un servicio simple y sin secretos | no puede salir del equipo | es local y de una persona a la vez; si se despliega hay que decidir de nuevo |
| Una conexión por solicitud a MySQL ([ADR-010](adr/adr-010_api_de_solo_lectura_local.md)) | sin estado de conexiones que caduquen | unos 80 ms más por consulta con MySQL (88,2 ms frente a 6,1 ms, EV-032) | el servicio es local y de un solo usuario |
| Proxy satelital con 7 comunas ([ADR-009](adr/adr-009_fuentes_por_criterios_de_aceptacion.md)) | la única fuente abierta a nivel de construcción | no es una evaluación estructural y no cubre toda Cali | lo declaramos en cada resultado y no extrapolamos |
| Documentación vigilada por pruebas ([ADR-008](adr/adr-008_pruebas_sin_servidor_y_regresion.md)) | cifras que no se desactualizan en silencio | más pruebas que mantener (**1467 pruebas** en total) | una cifra vieja ya se coló una vez en un documento y la prueba la detectó |

## 16. Riesgos y mitigaciones
La probabilidad y el impacto son juicio del equipo, sin cifras; se basan en las limitaciones, defectos y riesgos registrados.
| Riesgo | Tipo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|
| La fuente ArcGIS cambia o desaparece | técnico | media | baja | Bronze versionado con sha256; solo `--refresh` toca la fuente |
| Se lee el proxy satelital como una evaluación estructural | negocio | media | alta | recuadros de alcance en cada resultado y la tabla de diferencias con las evaluaciones de la Alcaldía |
| El estrato es de 2015 y las imágenes de 2026 | negocio | alta | media | regla de lectura declarada: describe el estrato de 2015 asignado al barrio |
| Otra versión de pandas cambia las cifras | técnico | media | media | versión fijada y prueba byte a byte de la línea base ([ADR-007](adr/adr-007_reproducibilidad_de_versiones.md)) |
| Airflow pesa demasiado en una máquina con poca memoria | técnico | media | media | el modo mínimo no lo necesita; con 8 GB no lo probamos |
| Una credencial local se filtra | técnico | baja | media | `.env` ignorado, escáner, canario y mínimo privilegio; el límite de D67 está declarado |
| Los dos almacenes divergen | técnico | baja | media | conciliación al cargar y prueba de equivalencia de la API |
| El DAG pierde una ejecución con el equipo apagado | técnico | media | baja | `catchup=False` es una decisión (D64); las salidas son estáticas |
| Una cifra de un documento queda desactualizada | técnico | media | media | pruebas que comparan cada cifra con lo medido; ya detectaron un informe de pruebas atrasado |
| La licencia del estrato es contradictoria (dos portales declaran licencias distintas) | negocio | media | media | se trata con la condición más restrictiva; descripción en el documento de atribución |
| Una dependencia transitiva cambia entre instalaciones | técnico | baja | baja | las pruebas de reproducibilidad detectarían un cambio que afecte las salidas |
| Falta feedback de personas usuarias | negocio | alta | media | material de sesiones preparado; hoja de ruta de la sección 17 |
| Todos los commits del historial son de la misma persona: el conocimiento técnico está concentrado en ella | organizativo | alta | alta | la documentación (README, este documento y los ADR), las guías de instalación y las pruebas que vigilan lo decidido; la ejecución desde cero en otros equipos está pendiente de comprobar |

## 17. Hoja de ruta técnica
**Madurez actual:** MVP académico, ejecutable en local, sin despliegue ni integración continua, aún sin sesiones reales con personas usuarias.

**Limitaciones conocidas:** las de [docs/gold/resultados.md](../gold/resultados.md) (proxy satelital, 7 comunas, estrato de 2015, estratos con muestra baja) y las de la sección 11 (deuda técnica).

**Propuesta del equipo, no compromiso:**
| Plazo | Mejora propuesta |
|---|---|
| Corto | publicar el repositorio y enlazar sus issues desde el README; comprobar la ejecución desde cero en otros equipos; hacer las sesiones con personas usuarias; aprobar el documento y los ADR entre los tres autores, pasando el estado de Revisado a Aprobado; grabar la demostración |
| Medio | ampliar la cobertura a la Comuna 2 y a las demás comunas ausentes; repetir el análisis con un estrato actualizado; agregar una validación explícita de las columnas de la fuente; evaluar reintentos de tareas en el DAG |
| Largo | incorporar la amenaza sísmica oficial; comparar el proxy con las inspecciones de la Alcaldía; si el sistema se despliega, agregar autenticación, integración continua y alertas |

**Posibles cambios de arquitectura futuros:** autenticación en la API si sale de `127.0.0.1`; un conjunto de conexiones si crece el uso; carga incremental solo si aparece una fuente que cambie; sustituir el compose por infraestructura como código si se despliega.

### Evidencias de pruebas, retroalimentación recibida y feedback de personas usuarias
- **Evidencias de pruebas técnicas:** [informe de pruebas](../validacion/informe_pruebas.md), [matriz de casos](../validacion/matriz_casos_prueba.md) (179 casos), [registro de defectos](../validacion/registro_defectos.md) (25 defectos; para 15 se demostró que su prueba de regresión falla sin la corrección y para los otros 10 no se demostró (DEF-003, DEF-006, DEF-009, DEF-010, DEF-011, DEF-014 y DEF-022 a DEF-025), con el motivo de cada uno en el registro), las mutaciones de [EV-103](../evidencias/modo_completo/EV-103_mutaciones_modo_completo.txt) (132 en total), la suite en un clon y en un zip ([EV-113](../evidencias/readme/EV-113_primera_vez_y_suite_en_clon_y_zip.txt)); la cobertura de `src/` es de 78 % de las líneas, medida con la suite completa y sin red ([EV-114](../evidencias/readme/EV-114_cobertura_de_src_repetida.txt)); es una cota inferior, porque `clean_api.py` e `integrate.py` se ejecutan en subprocesos que la medición no sigue y `extract_api.py` necesita red; la misma suite, la cobertura, el informe y el escáner de secretos sobre un commit posterior ([EV-116](../evidencias/arquitectura/EV-116_suite_en_clon_y_zip_cobertura_y_escaner_del_commit_final.txt)); las mutaciones de las pruebas de este documento y de sus ADR ([EV-115](../evidencias/arquitectura/EV-115_mutaciones_de_las_pruebas_de_arquitectura.txt)): 188 de 188 detectadas; y el PDF del documento y de los ADR, con la comprobación de sus marcadores, enlaces y fechas ([EV-117](../evidencias/arquitectura/EV-117_pdf_del_documento_de_arquitectura.txt)).
- **Retroalimentación recibida sobre la entrega anterior:** el texto está en [retroalimentacion_recibida.txt](../retroalimentacion/retroalimentacion_recibida.txt) y no se edita. Trae aspectos positivos y cinco observaciones por mejorar; cada una está atendida en [registro_de_cambios.md](../retroalimentacion/registro_de_cambios.md), con qué hicimos, qué archivos cambiaron y su evidencia. Atenderlas no cambió ningún dato, indicador, umbral, regla de Silver ni columna.
- **Feedback de personas usuarias:** **no existe todavía y sigue pendiente.** La retroalimentación recibida sobre la entrega anterior no es feedback de personas usuarias. El protocolo, el guion, el consentimiento y el análisis (probado solo con datos sintéticos rotulados) están en [docs/usuarios/](../usuarios/README.md); cuando haya sesiones reales, sus resultados se registran ahí y este apartado se actualiza.

## 18. Glosario y referencias
### Glosario
| Término | Significado |
|---|---|
| Medallion | organización por capas: Bronze crudo, Silver limpio, Gold listo para análisis |
| Construcción | huella catastral de una edificación; no es un edificio completo ni un predio |
| Proxy satelital | medida indirecta del daño: cambio de textura entre dos imágenes sobre la huella; no es una inspección |
| Severo estricto | construcción con la clase «Alta probabilidad de escombros»; el indicador principal |
| Estrato moda | el estrato con más lados de manzana en un barrio; se asigna a todas sus construcciones |
| Llave | `int(COMUNA) * 100 + int(BARRIO)` como texto; une las construcciones con el CSV de estrato |
| Huérfano | fila que no encuentra pareja en el JOIN; se conserva en un archivo aparte |
| Línea base | los nueve archivos de Silver y Gold cuyos sha256 se comprueban |
| Snapshot | copia fechada (UTC) de lo descargado; no se sobrescribe |
| Corrida | una carga completa a MySQL, identificada por una clave determinista |
| Idempotente | que repetir la operación con la misma entrada no cambia nada |
| DAG | grafo de tareas de Airflow que se ejecutan en orden y sin ciclos |
| Copia de trabajo | carpeta temporal del contenedor donde el DAG produce sus salidas para compararlas |
| ADR | registro de una decisión de arquitectura con su contexto, consecuencias y alternativas |

El glosario del análisis (Wilson, Newcombe, Mantel-Haenszel, K1 a K6) está en [docs/gold/resultados.md](../gold/resultados.md).

### Referencias
- Decisiones: [docs/DECISIONES.md](../DECISIONES.md) y los 15 ADR de la sección 10.
- Diagramas: los de las secciones 6 y 9 de este documento, en texto.
- Documentación por componente: [API](../api/arquitectura.md), [panel](../panel/arquitectura_panel.md), [orquestación](../orquestacion/README.md), [modelo de datos](../almacenamiento/modelo_datos.md) y [seguridad](../seguridad/gestion_credenciales.md).
- Documentación de las herramientas (páginas principales; no las verificamos con una consulta de hoy): Apache Airflow (https://airflow.apache.org/docs/), FastAPI (https://fastapi.tiangolo.com/), Streamlit (https://docs.streamlit.io/), pandas (https://pandas.pydata.org/docs/), pytest (https://docs.pytest.org/) y MySQL 8.0 (https://dev.mysql.com/doc/refman/8.0/en/).

### Crédito del método de orquestación
Orquestación: el DAG y el compose de Airflow siguen el artículo de Juan Manuel Núñez Velasco, «Apache Airflow en Windows con WSL2 y Docker: tutorial paso a paso para orquestar un pipeline ETL 2026», con las diferencias documentadas en [docs/orquestacion/diferencias_con_la_guia.md](../orquestacion/diferencias_con_la_guia.md).
