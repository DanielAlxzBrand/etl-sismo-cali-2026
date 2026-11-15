# Verificación de la sección 2 del checklist: backend, fuentes y credenciales (ítems 2.1, 2.2 y 2.3)

**Fecha:** 2026-11-12 · **Componente:** API, fuentes y credenciales · **Regla de estado:** *Cumple*: evidencia concreta y reproducible para todos los subcriterios y límites declarados. *Cumple con matiz*: entregable central verificado y algún subcriterio depende de un hecho externo o de una componente posterior. Nunca «cumple» lo que requiera un evento que no ocurrió.

**Etiquetas de evidencia:** [Evidencia en el repo: ruta] · [Fuente externa: URL y fecha de consulta] · [Criterio aplicado: descripción] · [Hipótesis de diseño: criterio y experimento, no ejecutado].

> **Alcance de los resultados.** Proxy satelital, no evaluación estructural; 7 comunas de Cali con polígonos de afectación preliminar; estrato de 2015. No se generaliza a Cali.

## Auditoría previa (qué había antes de la capa de servicio)
| aspecto | hallazgo | evidencia |
|---|---|---|
| Pipeline por etapas | `main.py --stage extract\|transform\|gold\|all`; módulos con una responsabilidad cada uno (`extract`, `transform`, `load`) | `main.py:24-26`; `src/` |
| Configuración | URL, umbrales, fechas, rutas y registro en un solo archivo; sin secretos | `config/config.yaml` |
| Manejo de errores y reintentos | `http_get` reintenta con espera creciente (`retries`, `request_delay_s`); `load_database` registra y relanza los errores | `src/extract/extract_api.py:20-32`; `src/load/load_database.py` |
| Idempotencia | Bronze se escribe en modo `xb` (nunca sobrescribe) y un refresco crea otro snapshot; el determinismo se comprobó en un clon (9 de 9 archivos iguales en dos corridas) | `src/common.py` (`save_bronze`); `docs/evidencias/estrategia/EV-009_determinismo_clon.txt` |
| Registro de ejecución | `logs/etl_AAAAMMDD.log` con enmascarado de secretos | `src/logger.py:13-29` |
| Consumo de la API ArcGIS | paginación por `resultOffset` con orden estable por `OBJECTID` y recuento antes y después (5.146 filas en 3 páginas) | `src/extract/extract_api.py:64-81`; `docs/bronze/muestras/v2_limites_arcgis.txt` |
| Fuentes y metadatos | manifiesto con sha256, filas y bytes; metadatos de la capa guardados en Bronze; investigación y verificación de fuentes; muestras | `data/bronze/manifest.jsonl`; `docs/bronze/investigacion_fuentes.md`; `docs/bronze/verificacion_fuentes.md`; `docs/bronze/muestras/` |
| Secretos | `.env` ignorado por git y vacío; `.env.example` con dos nombres (uno sin uso); `make_dist.py` excluye `.env`; notebooks sin credenciales | `.gitignore`; `scripts/make_dist.py:16`; escáner sobre notebooks (0 hallazgos) |
| Historial de git y zip anterior | sin secretos en las líneas añadidas del historial y en el zip de un empaquetado anterior (solo lectura) | `docs/evidencias/api/EV-019_escaner_secretos.txt` |
| Brecha principal | el proyecto consumía una API pero **no exponía servicios**; no había catálogo de fuentes unificado ni política de credenciales ni escáner | — |

---

## Ítem 2.1 · «Diseñamos e implementamos la arquitectura de Backend, APIs y servicios para el procesamiento de datos.»

**(a) Subcriterios**
1. Arquitectura por capas diseñada y documentada.
2. API implementada con endpoints tipados y validación de parámetros.
3. Errores uniformes y sin fuga de información.
4. Los resultados de la API coinciden con las salidas de Gold y de calidad.
5. Solo lectura: no escribe en `data/` ni en la base.
6. Servicios de procesamiento (pipeline, carga, orquestación) identificados y su estado declarado.
7. Observabilidad (registro de solicitudes).

**(b) Evidencia existente.** Pipeline y módulos (`main.py`, `src/`); registro (`src/logger.py`); determinismo (EV-009).
**(c) Brecha.** Sin capa de servicio, sin API, sin documento de arquitectura.
**(d) Decisiones.** D18, D26, D27, D28, D29, D30 y D33.
**(e) Acción realizada.** `src/api/` (`app.py`, `esquemas.py`, `repositorio.py`, `errores.py`), parámetros bajo `api` en `config/config.yaml`, 17 pruebas en `tests/test_api.py`, `docs/api/arquitectura.md` y su diagrama, e instalación de `fastapi`, `uvicorn` y `httpx` en el `.venv`.
**(f) Evidencia producida.** EV-013 (instalación y versiones), EV-014 (pytest y junit), EV-015 (sin escritura), EV-016 (respuestas reales y OpenAPI), EV-017 (captura automatizada de `/docs`), EV-018 (latencia), EV-020 (entorno nuevo con `requirements.txt`) y el diagrama `docs/api/img/arquitectura_backend.png`.

**(g) Estado final: Cumple.**
| subcriterio | estado | justificación |
|---|---|---|
| 1 | Cumple | `arquitectura.md` con capas, módulos, flujo, contratos, seguridad y límites |
| 2 | Cumple | 11 rutas GET con modelos pydantic; 422 con detalle por campo |
| 3 | Cumple | `{"error": {"codigo", "mensaje", "detalle"}}` en 404, 405, 422, 503 y 500; el 500 no trae trazas ni rutas |
| 4 | Cumple | pruebas comparan con los CSV (tolerancia 1e-9) y con pandas |
| 5 | Cumple | `mode=ro` (un INSERT falla), solo GET y sha256 de `data/` y de la base iguales antes y después (EV-015) |
| 6 | Cumple | el pipeline y su determinismo están probados; la carga a MySQL (Carga relacional) y Airflow (Pruebas y orquestación) cierran otros ítems y se declaran «en construcción» |
| 7 | Cumple | cada solicitud se registra (método, ruta, estado y duración) |

**Límites declarados:** sin autenticación (uso local en 127.0.0.1); proxy satelital, no evaluación estructural.
**(h) Cómo validar.** `.\.venv\Scripts\python.exe -m pytest tests/test_api.py -q -p no:cacheprovider`; `.\.venv\Scripts\python.exe -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000` y abrir `http://127.0.0.1:8000/health` y `/docs` (captura opcional; ver `evidencias/guia_de_evidencias.md`).

---

## Ítem 2.2 · «Definimos las fuentes de datos y sus metadatos»

**(a) Subcriterios**
1. Cada fuente tiene publicador, URL, protocolo, formato, autenticación, límites y paginación.
2. Columnas usadas con tipo y significado; cobertura temporal y espacial; granularidad.
3. Fechas (imágenes, edición de la capa y consulta) y licencia (o «no declarada en el servicio»).
4. Snapshot trazable: ruta, filas, bytes, sha256 y fecha UTC, coincidente con el manifiesto.
5. Fuentes de contexto y descartadas con su motivo; las cifras de prensa marcadas como no recotejadas.
6. Diccionario de metadatos por capa (Bronze, Silver, Gold).
7. Catálogo determinista y servido por la API.

**(b) Evidencia existente.** `manifest.jsonl`, metadatos de la capa en Bronze, `docs/bronze/investigacion_fuentes.md`, `docs/bronze/verificacion_fuentes.md`, `docs/bronze/muestras/`, `docs/gold/KPIs.md` (diccionario de Gold).
**(c) Brecha.** La información estaba dispersa en cuatro documentos; no había un catálogo único ni verificable contra el manifiesto.
**(d) Decisiones.** D26 (`/fuentes`) y D31.
**(e) Acción realizada.** `scripts/make_catalogo_fuentes.py` genera `catalogo_fuentes_metadatos.md` y `catalogo_fuentes.json`; endpoints `/fuentes` y `/metadata`; `tests/test_catalogo.py`.
**(f) Evidencia producida.** El catálogo, EV-016 (respuesta de `/fuentes` y `/metadata`) y EV-014 (pruebas).

**(g) Estado final: Cumple.**
| subcriterio | estado | justificación |
|---|---|---|
| 1 | Cumple | tres fuentes usadas, dos de contexto; la autenticación y los límites de cada una se leen de la configuración y los metadatos |
| 2 | Cumple | columnas de la capa con el tipo que reporta el servicio; las del CSV desde su encabezado |
| 3 | Cumple | licencia de la capa tomada del catálogo (el servicio trae `copyrightText` vacío); la de los polígonos se declara «no declarada en el servicio» |
| 4 | Cumple | la prueba compara sha256, filas y bytes de los 8 registros del manifiesto |
| 5 | Cumple | nueve fuentes descartadas con motivo y sección de `docs/bronze/investigacion_fuentes.md`; ATC-20 como «cifras de prensa, no recotejadas» |
| 6 | Cumple | el diccionario de `gold_final` se lee de `docs/gold/KPIs.md`; las demás columnas tienen descripción propia |
| 7 | Cumple | dos generaciones son idénticas y `/fuentes` devuelve el mismo JSON |

**Límites declarados:** las licencias son las de los catálogos consultados (no es una revisión jurídica); no volvimos a consultar los servicios al cerrar la capa de servicio (la fecha de consulta es la del snapshot, 2026-10-16); las cifras de la evaluación ATC-20 vienen de prensa y no las recotejamos.
**(h) Cómo validar.** `.\.venv\Scripts\python.exe scripts\make_catalogo_fuentes.py` (los archivos no deben cambiar: `git status`), `pytest tests/test_catalogo.py` y `GET /fuentes`.

---

## Ítem 2.3 · «Aseguramos la gestión segura de credenciales, claves de API y tokens de acceso.»

**(a) Subcriterios**
1. Política documentada: qué se requiere hoy, variables previstas, dónde se guardan y qué nunca va al repositorio.
2. `.env` fuera de git y `.env.example` solo con nombres de variables que el código lee.
3. Ningún secreto en el árbol de trabajo, el historial, los notebooks, los logs ni un zip.
4. Enmascarado de secretos en el registro y `.env` excluido del zip.
5. Procedimientos de rotación, revocación y respuesta ante filtración.
6. Un escáner que reporte archivo, línea y patrón, nunca el valor, y que se pruebe con secretos sembrados.

**(b) Evidencia existente.** `.gitignore`, `src/logger.py`, `scripts/make_dist.py`, `.env.example` (con un nombre sin uso).
**(c) Brecha.** Sin política escrita ni escáner; `.env.example` listaba una variable que el código no lee.
**(d) Decisiones.** D32 y D34.
**(e) Acción realizada.** `docs/seguridad/gestion_credenciales.md`, `scripts/escanear_secretos.py`, `tests/test_secretos.py` (10 pruebas) y `.env.example` con solo `HTTP_USER_AGENT`.
**(f) Evidencia producida.** EV-019 (escáner sobre el clon, su historial y un zip armado con `make_dist.py` en carpeta temporal: 0 hallazgos) y EV-014.

**(g) Estado final: Cumple.** *Nota:* se revalida con las variables `MYSQL_*` (Carga relacional) y con el escáner sobre el zip final (Cierre y paquete).
| subcriterio | estado | justificación |
|---|---|---|
| 1 | Cumple | documento con las nueve secciones; variables `MYSQL_*` y claves de Airflow como «previstas, no usadas todavía» |
| 2 | Cumple | `.env` no está en `git ls-files`; el ejemplo solo trae `HTTP_USER_AGENT` |
| 3 | Cumple | 0 hallazgos en árbol, historial, notebooks, logs y zip (incluido el zip de un empaquetado anterior, solo lectura) |
| 4 | Cumple | pruebas del enmascarado y de `make_dist` |
| 5 | Cumple | sección 5 y 6 del documento: revocar primero, no reescribir el historial sin decisión del equipo |
| 6 | Cumple | detecta un secreto sembrado de cada uno de doce tipos; no se detecta a sí mismo ni a las pruebas |

**Límites declarados:** el escáner puede dar falsos positivos y negativos; `.env` local queda fuera del recorrido (su control es que git no lo versione); no revisamos servicios de terceros ni las cuentas de los integrantes; las credenciales de MySQL y de Airflow aún no existen.
**(h) Cómo validar.** `.\.venv\Scripts\python.exe scripts\escanear_secretos.py` (debe terminar en `hallazgos: 0`) y `pytest tests/test_secretos.py`.

---

## Qué falta del lado del equipo (hechos externos)
- Las capturas de pantalla de API, fuentes y credenciales son **opcionales** y complementarias (D35); la evidencia suficiente son las salidas registradas, y la captura de `/docs` incluida como EV-017 es **automatizada del navegador**. La guía por ítem está en `docs/checklist/guia_de_evidencias.md`.
- Antes de Carga relacional, una cuenta de MySQL local (el script SQL lo entrega Carga relacional).

---

## Cierre de API, fuentes y credenciales (2026-11-12)
- **Estados:** 2.1 Cumple, 2.2 Cumple y 2.3 Cumple (se revalida con las variables `MYSQL_*` (Carga relacional) y con el escáner sobre el zip final (Cierre y paquete)).
- **Pruebas:** 92 en el clon temporal (`EV-014`, `EV-025`); el desglose por archivo está en `README.md` §14.
- **Sin escritura:** sha256 de los 19 archivos de `data/` (incluida la base) idénticos tras clonar, tras las pruebas y tras consultar el servidor real (`EV-015`).
- **Latencia:** medida con el servidor real en 127.0.0.1 (`EV-018`, `EV-021`); son mediciones locales de una máquina.
- **Escáner:** sin hallazgos en el clon, su historial y un zip de prueba (`EV-019`, `EV-024`).
- **Entorno nuevo:** `pip install -r requirements.txt` en un entorno virtual nuevo y `pytest --collect-only` recolectaron las 92 pruebas (`EV-020`).
- **Evidencias saneadas:** sin rutas de usuario, nombre de usuario ni nombre del equipo (marcadores `<REPO>`, `<CLON>`, `<TEMP>`, `<VENV>`, `<USUARIO>` y `<EQUIPO>`; D36).
- **Política de evidencias (D35):** sin video; las capturas de pantalla son opcionales (`evidencias/guia_de_evidencias.md`).

---

## Carga relacional (2026-11-13)
Verificación de los ítems 4.1, 4.2 y 4.3 y revalidación del 2.3 con las variables `MYSQL_*`. Cada subcriterio se cumple por dos vías: **sin servidor** (pruebas automáticas sobre SQLite con el mismo esquema) y **en vivo** (batería, carga real, medición y respaldo sobre MySQL 8.0.45, con el usuario `sismo_etl` creado por el equipo con `scripts/mysql/configurar_mysql.py`). Las evidencias están en `docs/evidencias/almacenamiento/` y se listan en el manifiesto (EV-027 a EV-034).

### Auditoría previa
| aspecto | hallazgo | evidencia |
|---|---|---|
| Almacén existente | `etl_sismo.db` (SQLite) con cuatro tablas sin claves foráneas, sin historial y sin carga por lotes; se reconstruye en cada ejecución | `src/load/load_database.py` |
| Servidor MySQL | MySQL 8.0.45 como servicio `MySQL80` en el puerto 3306; la contraseña del administrador solo la conoce el equipo | `docs/proyecto/entorno.md` |
| Conector | PyMySQL y `cryptography` instalados, `pip check` sin conflictos | EV-027 |
| Credenciales | `.env` vacío; sin variables `MYSQL_*` en el código | `docs/seguridad/gestion_credenciales.md` (versión inicial) |
| Brecha principal | no había esquema relacional, ni historial, ni integridad referencial, ni carga por lotes, ni forma segura de crear el usuario | — |

### Ítem 4.1 · «Cargamos los datos procesados en el sistema de almacenamiento destino (PostgreSQL, MySQL, Data Warehouse o Data Lake).»
**(a) Subcriterios**
1. Esquema relacional (tablas, tipos, claves e índices) definido para MySQL 8.0 y documentado con diccionario de datos y diagrama entidad-relación.
2. Carga de las construcciones de Gold, el estrato por barrio de Silver y los indicadores sin modificar el pipeline ni `data/`.
3. Conciliación contra las entradas: conteos, huellas de los archivos y ida y vuelta de cada valor, al 100 %.
4. Configuración segura: usuario con privilegios mínimos, dos bases (real y de prueba) y credenciales solo en `.env`.
5. La API sirve las mismas respuestas desde el almacén relacional que desde SQLite.

**(b) Evidencia existente.** `src/load/load_database.py` (SQLite), EV-027.
**(c) Brecha.** Todo lo anterior salvo el conector.
**(d) Decisiones.** D40, D41, D42, D46, D49, D51, D52 y D54.
**(e) Acción realizada.** `src/load/sql/esquema_mysql.sql` y `esquema_sqlite.sql`, `src/load/esquema.py`, `relacional.py`, `conexion.py`, `conciliacion.py`, `scripts/cargar_mysql.py`, `scripts/mysql/` (configuración, verificación, medición y respaldo), `RepositorioRelacional` en `src/api/`, `docs/almacenamiento/`.
**(f) Evidencia producida.** `docs/almacenamiento/modelo_datos.md` e `img/modelo_er.png` (generados del esquema); `tests/test_carga_relacional.py`; EV-028 (batería en vivo, 26 de 26), EV-029 (carga real a `sismo_cali`) y EV-032 (API sobre MySQL).

**(g) Estado final: Cumple.**
| subcriterio | estado | justificación |
|---|---|---|
| 1 | Cumple | siete tablas con comentario en cada columna; una prueba compara el diccionario con el esquema y otra la paridad de los dos archivos SQL; en MySQL el esquema creado desde cero tiene 7 tablas, 92 columnas, InnoDB con `utf8mb4_0900_ai_ci`, 8 claves foráneas y 14 restricciones `CHECK` (EV-028) |
| 2 | Cumple | la carga real tardó 1,17 s y cargó 346 barrios, 5.146 construcciones, 23 indicadores y 107 filas de sensibilidad (EV-029); los 19 archivos de `data/` conservan su sha256 (EV-032 y prueba de la carga) |
| 3 | Cumple | 145.247 valores comparados y 0 diferencias en la base de prueba (EV-028); en la base real, 100 % en las cuatro tablas, huellas de los 5 archivos de entrada iguales y cifras (5.146 construcciones, 296 severas, 435 sin datos satelitales, 6 sin cruce) iguales a `gold_final.csv` (EV-029) |
| 4 | Cumple | `SHOW GRANTS`: solo `sismo_cali` y `sismo_cali_prueba`, sin privilegios globales ni `GRANT OPTION` (EV-028); `.env` ignorado y sin valores en ningún otro lugar (EV-033) |
| 5 | Cumple | 17 de 17 rutas idénticas entre MySQL y SQLite con servidores reales (EV-032) y en la batería (EV-028) |

**Cómo validar.** `pytest tests/test_carga_relacional.py` y `.\.venv\Scripts\python.exe scripts\mysql\verificar_mysql.py --evidencia`.

### Ítem 4.2 · «Garantizamos la persistencia histórica e integridad referencial de los datos guardados.»
**(a) Subcriterios**
1. Persistencia histórica: cada carga distinta es una corrida completa y las anteriores quedan intactas.
2. Integridad referencial: claves primarias y foráneas con `ON DELETE RESTRICT`, restricciones `CHECK` y ninguna fila huérfana; las construcciones sin cruce de barrio se conservan con el enlace nulo.
3. Idempotencia: la misma entrada no duplica datos (clave de corrida determinista).
4. Atomicidad: una carga es una transacción; ante un fallo no queda nada a medias.
5. Las violaciones de integridad se rechazan con su código de error y no dejan filas.
6. Respaldo y restauración lógicos que concilian tabla por tabla.

**(b) Evidencia existente.** Ninguna sobre historial ni integridad referencial.
**(c) Brecha.** Sin historial, sin claves foráneas, sin carga transaccional, sin respaldo.
**(d) Decisiones.** D43, D44, D45, D48, D51 y D55.
**(e) Acción realizada.** Esquema con claves y restricciones; `cargar` transaccional con gancho de pruebas; `scripts/mysql/respaldar_restaurar.py`.
**(f) Evidencia producida.** `tests/test_carga_relacional.py` y `tests/test_respaldo_y_medicion.py`; EV-028, EV-029 y EV-031.

**(g) Estado final: Cumple.**
| subcriterio | estado | justificación |
|---|---|---|
| 1 | Cumple | una entrada alterada crea la corrida 2 (10.292 construcciones en total), una consulta encuentra la única construcción distinta y la corrida 1 sigue conciliada al 100 % (EV-028) |
| 2 | Cumple | 0 filas huérfanas en las 8 relaciones, en la base de prueba y en la real; las 6 construcciones sin cruce tienen el enlace nulo (EV-028 y EV-029) |
| 3 | Cumple | la segunda carga de la base real responde «ya cargada» y la base sigue con 1 corrida (EV-029) |
| 4 | Cumple | un error inyectado tras insertar las construcciones deja los conteos de todas las tablas iguales (EV-028) |
| 5 | Cumple | clave primaria repetida (1062), estrato 9, latitud fuera de Cali y cruce sin enlace (3819), corrida inexistente y barrio inexistente (1216, familia de 1452) y borrado de una corrida con datos (1217, familia de 1451): todas rechazadas y sin filas nuevas (EV-028; D55) |
| 6 | Cumple | 5.655 filas en 7 tablas respaldadas con manifiesto sha256, restauradas en la base de prueba y con la huella de filas igual en todas las tablas (EV-031) |

**Cómo validar.** `pytest tests/test_carga_relacional.py tests/test_respaldo_y_medicion.py`; en vivo, `verificar_mysql.py` y `respaldar_restaurar.py`.

### Ítem 4.3 · «Optimizamos el rendimiento del cargue (operaciones en lote/batch o estrategias de actualización).»
**(a) Subcriterios**
1. Inserciones por lotes (`executemany`) con tamaño configurable.
2. Medición de al menos tres tamaños de lote frente a la carga fila a fila, con calentamiento y repeticiones.
3. El tamaño elegido sale de la medición y queda en `config/config.yaml`.
4. Estrategia de actualización: la clave de corrida evita recargar lo que no cambió y un cambio genera una corrida nueva, sin actualizar fila a fila.
5. Informe con mediana, percentil 95 y filas por segundo, con la salvedad de que los tiempos dependen del equipo.

**(b) Evidencia existente.** Ninguna (`load_database.py` inserta con `to_sql`).
**(c) Brecha.** No había medición ni parámetro de lote.
**(d) Decisiones.** D44, D47 y D53.
**(e) Acción realizada.** `almacenamiento.lote` en `config/config.yaml`; `scripts/mysql/benchmark_lotes.py` con la regla de elección y sus pruebas.
**(f) Evidencia producida.** EV-030 (tabla, CSV y gráfico) y `tests/test_respaldo_y_medicion.py`.

**(g) Estado final: Cumple.**
| subcriterio | estado | justificación |
|---|---|---|
| 1 | Cumple | `_insertar` divide en lotes del tamaño configurado; las pruebas y la carga real lo usan |
| 2 | Cumple | fila a fila, 500, 1000 y 2000; 1 carga de calentamiento y 5 repeticiones por estrategia (EV-030) |
| 3 | Cumple | medianas de 2,415, 0,787, 0,788 y 0,715 s; el lote 2000 es el más rápido por más de 5 % y queda en `config/config.yaml` (D53) |
| 4 | Cumple | idempotencia e historial probados en vivo (EV-028 y EV-029) |
| 5 | Cumple | EV-030 trae mediana, p95 y filas por segundo (de 2.328 fila a fila a 7.859 con lote de 2000) y la salvedad de que dependen del equipo |

**Cómo validar.** `.\.venv\Scripts\python.exe scripts\mysql\benchmark_lotes.py --evidencia`.

### Revalidación del ítem 2.3 con las variables `MYSQL_*`
Subcriterios nuevos, además de los seis anteriores: 7. la contraseña del usuario del proyecto se crea y se guarda sin que la vea nadie más que `.env`; 8. los valores de `.env` no aparecen en ningún otro lugar.

| subcriterio | estado | justificación |
|---|---|---|
| 1 a 6 | Cumple (sin cambios) | `pytest tests/test_secretos.py`; escáner sin hallazgos |
| 7 | Cumple | `.env` con las seis variables `MYSQL_*` creado por el script (nombres, nunca valores), `--solo-verificar` correcto; `tests/test_configurar_mysql.py` prueba que la contraseña del administrador no llega a `.env`, a SQL ni al registro |
| 8 | Cumple | comprobación canario con la contraseña real: 0 hallazgos en el árbol, 5 registros, 54 commits del historial y un zip de prueba de 194 entradas sin `.env` (EV-033) |

**Estado del 2.3:** Cumple. Queda por repetir la comprobación canario sobre el zip final en Cierre y paquete.

---

## Panel (2026-11-14)
Ítems 3.1, 3.2 y 5.3, y criterios AC28 y AC29 del MVP. El ítem 3.3 (usabilidad, capacidad de respuesta y coherencia visual) **no se cierra aquí**: solo se producen mediciones y verificaciones técnicas reutilizables ([accesibilidad_y_respuesta.md](../panel/accesibilidad_y_respuesta.md)).

### Auditoría previa
| Qué había | Brecha |
|---|---|
| API de solo lectura con 11 rutas GET y errores JSON uniformes; salidas de Gold; decisión D20 (Streamlit sobre la API) | ninguna interfaz, ningún código del panel y Streamlit sin instalar |
| Streamlit no estaba en el entorno | instalarlo sin cambiar pandas, numpy ni shapely ([EV-051](../evidencias/panel/EV-051_instalacion_streamlit.txt)) |
| La API no entrega el umbral de muestra baja, el texto de «qué no se puede concluir» ni el detalle de los barrios de K3 más que en una nota | se resuelve en el panel sin modificar `src/api/` (D78) |

### Subcriterios, decisiones y estado
| # | Ítem | Subcriterio | Brecha | Decisión | Acción | Evidencia producida | Estado | Cómo validar |
|---|---|---|---|---|---|---|---|---|
| 1 | 3.1 | Componentes de interfaz: ocho páginas con métricas, tablas y gráficos con barras de error | no existían | D68, D71 | `src/panel/` con registro único de componentes | [EV-054](../evidencias/panel/EV-054_capturas_panel.txt); [trazabilidad_ui.md](../panel/trazabilidad_ui.md) | Cumple | `python scripts/panel/ejecutar_panel.py` |
| 2 | 3.1 | Visualización fiel y con alcance visible en todas las páginas (K1 a K6, sensibilidades, calidad y fuentes) | no existía | D73, D74, D80 | recuadro de alcance permanente; conclusiones generadas con la regla de `KPIs.md`; ninguna cifra escrita a mano | `tests/test_panel_integracion.py` (valores iguales a las salidas) | Cumple | `pytest tests/test_panel_integracion.py tests/test_panel_paginas.py` |
| 3 | 3.1 | Interacción: filtros que aplica la API, paginación y descarga CSV de lo mostrado | no existía | D75, D76 | página Construcciones | `tests/test_panel_paginas.py::test_construcciones_pagina_filtra_en_la_api_y_ofrece_la_descarga`; capturas | Cumple | abrir la página Construcciones |
| 4 | 3.1 | Ejecución reproducible con un comando y cierre limpio | no existía | D72 | `scripts/panel/ejecutar_panel.py` | [EV-052](../evidencias/panel/EV-052_ejecucion_real.txt) | Cumple | `python scripts/panel/ejecutar_panel.py --verificar` |
| 5 | 3.2 | El frontend consume solo los endpoints de la API, de forma modular | no existía | D69, D70 | cliente HTTP único y solo GET; páginas `render(api)` | análisis estático (`tests/test_panel_registro_y_aislamiento.py`); registro de rutas contra el OpenAPI | Cumple | `pytest tests/test_panel_registro_y_aislamiento.py` |
| 6 | 3.2 | Errores de la API traducidos a avisos claros, sin trazas | no existía | D69, D71 | resultados tipados y marco con degradación | `tests/test_panel_cliente.py`; 5 tipos de fallo en las 8 páginas (`tests/test_panel_paginas.py`) | Cumple | `pytest tests/test_panel_cliente.py tests/test_panel_paginas.py` |
| 7 | 3.2 | Eficiencia: caché con tiempo de vida y mediciones | no existía | D70 | `st.cache_data` que no guarda fallos; mediciones locales | [EV-055](../evidencias/panel/EV-055_mediciones_panel.txt) | Cumple | `python scripts/evidencias/evidencia_panel_almacenes.py` |
| 8 | 5.3 | Pruebas interfaz ↔ lógica con `AppTest` | no existían | D77 | una prueba por página y tipo de fallo | `tests/test_panel_paginas.py` | Cumple | `pytest tests/test_panel_paginas.py` |
| 9 | 5.3 | Integración interfaz ↔ API ↔ almacenamiento con la API real | no existía | D77 | cliente en memoria contra la API real sobre una copia temporal de SQLite en solo lectura | `tests/test_panel_integracion.py` (11 pruebas) | Cumple | `pytest tests/test_panel_integracion.py` |
| 10 | 5.3 | Humo de extremo a extremo de solo lectura (D23 vigente por D67) | no existía | D77 | API real en un subproceso y cliente HTTP real | `tests/test_panel_humo_extremo_a_extremo.py`; [EV-052](../evidencias/panel/EV-052_ejecucion_real.txt) | Cumple | `pytest tests/test_panel_humo_extremo_a_extremo.py` |
| 11 | 5.3 | Equivalencia entre almacenamientos: los datos de cada página son iguales con SQLite y con MySQL | no existía | D77 | dos APIs reales, una por almacén | [EV-053](../evidencias/panel/EV-053_equivalencia_almacenes.txt): 12 de 12 respuestas y 8 de 8 páginas idénticas | Cumple | `python scripts/evidencias/evidencia_panel_almacenes.py` (necesita MySQL) |
| 12 | AC28 | K1 a K6 con alcance visible y sin leer la base | no verificado | D68 | ver subcriterios 2 y 5 | EV-054 y análisis estático | Cumple | ver 2 y 5 |
| 13 | AC29 | Humo de solo lectura interfaz → API → almacén | no verificado | D77 | ver subcriterios 10 y 11 | EV-052 y EV-053 | Cumple | ver 10 y 11 |

### Hallazgos de la API (resueltos sin modificar `src/api/`)
La API no entrega el umbral de muestra baja; no sirve el texto de «qué no se puede concluir» (que hoy lista ocho puntos y no siete); entrega el detalle de los barrios de K3 solo en la nota del KPI; `/composicion` trae los grupos de estrato 1-2, 3-5 y 6; y `/comunas` renombra las columnas de Gold. Detalle y manejo en D78.

### Revalidación del ítem 2.3
El panel no maneja credenciales: no importa módulos de conexión, no lee `.env` y el lanzador no le pasa variables `MYSQL_*` (pruebas de aislamiento y del lanzador). La comprobación canario con las contraseñas de MySQL, del usuario de Docker y de la interfaz de Airflow sobre el árbol, el historial, los registros, la carpeta de Airflow y un zip de prueba dio 0 hallazgos ([EV-056](../evidencias/panel/EV-056_canario_panel.txt)). Estado del 2.3: Cumple.

### Avance de otros ítems
7.2: el README tiene la sección «Panel» (cómo ejecutarlo, páginas, estructura y glosario). 7.3: [arquitectura_panel.md](../panel/arquitectura_panel.md) y la trazabilidad de la interfaz; el feedback de usuarios sigue pendiente (hecho externo).

**Estado final:** 3.1 Cumple, 3.2 Cumple, 5.3 Cumple, AC28 y AC29 cumplen. El 3.3 queda como avance técnico; las sesiones con usuarios están pendientes.
