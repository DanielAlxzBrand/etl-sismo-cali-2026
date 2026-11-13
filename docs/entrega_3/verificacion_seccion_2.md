# Verificación de la sección 2 del checklist: backend, fuentes y credenciales (ítems 2.1, 2.2 y 2.3)

**Fecha:** 2026-11-12 · **Fase:** F2 · **Regla de estado:** *Cumple*: evidencia concreta y reproducible para todos los subcriterios y límites declarados. *Cumple con matiz*: entregable central verificado y algún subcriterio depende de un hecho externo o de una fase posterior. Nunca «cumple» lo que requiera un evento que no ocurrió.

**Etiquetas de evidencia:** [Evidencia en el repo: ruta] · [Fuente externa: URL y fecha de consulta] · [Criterio aplicado: descripción] · [Hipótesis de diseño: criterio y experimento, no ejecutado].

> **Alcance de los resultados.** Proxy satelital, no evaluación estructural; 7 comunas de Cali con polígonos de afectación preliminar; estrato de 2015. No se generaliza a Cali.

## Auditoría previa (qué había antes de F2)
| aspecto | hallazgo | evidencia |
|---|---|---|
| Pipeline por etapas | `main.py --stage extract\|transform\|gold\|all`; módulos con una responsabilidad cada uno (`extract`, `transform`, `load`) | `main.py:24-26`; `src/` |
| Configuración | URL, umbrales, fechas, rutas y registro en un solo archivo; sin secretos | `config/config.yaml` |
| Manejo de errores y reintentos | `http_get` reintenta con espera creciente (`retries`, `request_delay_s`); `load_database` registra y relanza los errores | `src/extract/extract_api.py:20-32`; `src/load/load_database.py` |
| Idempotencia | Bronze se escribe en modo `xb` (nunca sobrescribe) y un refresco crea otro snapshot; el determinismo se comprobó en un clon (9 de 9 archivos iguales en dos corridas) | `src/common.py` (`save_bronze`); `docs/entrega_3/evidencias/f1/EV-009_determinismo_clon.txt` |
| Registro de ejecución | `logs/etl_AAAAMMDD.log` con enmascarado de secretos | `src/logger.py:13-29` |
| Consumo de la API ArcGIS | paginación por `resultOffset` con orden estable por `OBJECTID` y recuento antes y después (5.146 filas en 3 páginas) | `src/extract/extract_api.py:64-81`; `docs/muestras/v2_limites_arcgis.txt` |
| Fuentes y metadatos | manifiesto con sha256, filas y bytes; metadatos de la capa guardados en Bronze; investigación y verificación de fuentes; muestras | `data/bronze/manifest.jsonl`; `docs/investigacion_fuentes.md`; `docs/verificacion_fuentes.md`; `docs/muestras/` |
| Secretos | `.env` ignorado por git y vacío; `.env.example` con dos nombres (uno sin uso); `make_dist.py` excluye `.env`; notebooks sin credenciales | `.gitignore`; `scripts/make_dist.py:16`; escáner sobre notebooks (0 hallazgos) |
| Historial de git y zip entregado | sin secretos en las líneas añadidas de los 14 commits y en el zip de `guia_equipo\entregas\entrega_1\` (solo lectura) | `docs/entrega_3/evidencias/f2/EV-019_escaner_secretos.txt` |
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
**(d) Decisiones.** D-E3-08, D-E3-16, D-E3-17, D-E3-18, D-E3-19, D-E3-20 y D-E3-23.
**(e) Acción realizada.** `src/api/` (`app.py`, `esquemas.py`, `repositorio.py`, `errores.py`), parámetros bajo `api` en `config/config.yaml`, 17 pruebas en `tests/test_api.py`, `docs/entrega_3/arquitectura.md` y su diagrama, e instalación de `fastapi`, `uvicorn` y `httpx` en el `.venv`.
**(f) Evidencia producida.** EV-013 (instalación y versiones), EV-014 (pytest y junit), EV-015 (sin escritura), EV-016 (respuestas reales y OpenAPI), EV-017 (captura automatizada de `/docs`), EV-018 (latencia), EV-020 (entorno nuevo con `requirements.txt`) y el diagrama `docs/entrega_3/img/arquitectura_backend.png`.

**(g) Estado final: Cumple.**
| subcriterio | estado | justificación |
|---|---|---|
| 1 | Cumple | `arquitectura.md` con capas, módulos, flujo, contratos, seguridad y límites |
| 2 | Cumple | 11 rutas GET con modelos pydantic; 422 con detalle por campo |
| 3 | Cumple | `{"error": {"codigo", "mensaje", "detalle"}}` en 404, 405, 422, 503 y 500; el 500 no trae trazas ni rutas |
| 4 | Cumple | pruebas comparan con los CSV (tolerancia 1e-9) y con pandas |
| 5 | Cumple | `mode=ro` (un INSERT falla), solo GET y sha256 de `data/` y de la base iguales antes y después (EV-015) |
| 6 | Cumple | el pipeline y su determinismo están probados; la carga a MySQL (F3) y Airflow (F4) cierran otros ítems y se declaran «en construcción» |
| 7 | Cumple | cada solicitud se registra (método, ruta, estado y duración) |

**Límites declarados:** sin autenticación (uso local en 127.0.0.1); proxy satelital, no evaluación estructural.
**(h) Cómo validar.** `.\.venv\Scripts\python.exe -m pytest tests/test_api.py -q -p no:cacheprovider`; `.\.venv\Scripts\python.exe -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000` y abrir `http://127.0.0.1:8000/health` y `/docs` (captura que debe tomar el equipo; ver `evidencias/guion_capturas_y_video.md`).

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

**(b) Evidencia existente.** `manifest.jsonl`, metadatos de la capa en Bronze, `docs/investigacion_fuentes.md`, `docs/verificacion_fuentes.md`, `docs/muestras/`, `docs/KPIs.md` (diccionario de Gold).
**(c) Brecha.** La información estaba dispersa en cuatro documentos; no había un catálogo único ni verificable contra el manifiesto.
**(d) Decisiones.** D-E3-16 (`/fuentes`) y D-E3-21.
**(e) Acción realizada.** `scripts/make_catalogo_fuentes.py` genera `catalogo_fuentes_metadatos.md` y `catalogo_fuentes.json`; endpoints `/fuentes` y `/metadata`; `tests/test_catalogo.py`.
**(f) Evidencia producida.** El catálogo, EV-016 (respuesta de `/fuentes` y `/metadata`) y EV-014 (pruebas).

**(g) Estado final: Cumple.**
| subcriterio | estado | justificación |
|---|---|---|
| 1 | Cumple | tres fuentes usadas, dos de contexto; la autenticación y los límites de cada una se leen de la configuración y los metadatos |
| 2 | Cumple | columnas de la capa con el tipo que reporta el servicio; las del CSV desde su encabezado |
| 3 | Cumple | licencia de la capa tomada del catálogo (el servicio trae `copyrightText` vacío); la de los polígonos se declara «no declarada en el servicio» |
| 4 | Cumple | la prueba compara sha256, filas y bytes de los 8 registros del manifiesto |
| 5 | Cumple | nueve fuentes descartadas con motivo y sección de `docs/investigacion_fuentes.md`; ATC-20 como «cifras de prensa, no recotejadas» |
| 6 | Cumple | el diccionario de `gold_final` se lee de `docs/KPIs.md`; las demás columnas tienen descripción propia |
| 7 | Cumple | dos generaciones son idénticas y `/fuentes` devuelve el mismo JSON |

**Límites declarados:** las licencias son las de los catálogos consultados (no es una revisión jurídica); no volvimos a consultar los servicios en F2 (la fecha de consulta es la del snapshot, 2026-10-16); las cifras de la evaluación ATC-20 vienen de prensa y no las recotejamos.
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
**(d) Decisiones.** D-E3-22 y D-E3-24.
**(e) Acción realizada.** `docs/entrega_3/gestion_credenciales.md`, `scripts/escanear_secretos.py`, `tests/test_secretos.py` (10 pruebas) y `.env.example` con solo `HTTP_USER_AGENT`.
**(f) Evidencia producida.** EV-019 (escáner sobre el clon, su historial y un zip armado con `make_dist.py` en carpeta temporal: 0 hallazgos) y EV-014.

**(g) Estado final: Cumple.** *Nota:* se revalida en F3 con las variables `MYSQL_*` y en F8 con el escáner sobre el zip final.
| subcriterio | estado | justificación |
|---|---|---|
| 1 | Cumple | documento con las nueve secciones; variables `MYSQL_*` y claves de Airflow como «previstas, no usadas todavía» |
| 2 | Cumple | `.env` no está en `git ls-files`; el ejemplo solo trae `HTTP_USER_AGENT` |
| 3 | Cumple | 0 hallazgos en árbol, historial, notebooks, logs y zip (incluido el zip entregado en `entrega_1`, solo lectura) |
| 4 | Cumple | pruebas del enmascarado y de `make_dist` |
| 5 | Cumple | sección 5 y 6 del documento: revocar primero, no reescribir el historial sin decisión del equipo |
| 6 | Cumple | detecta un secreto sembrado de cada uno de doce tipos; no se detecta a sí mismo ni a las pruebas |

**Límites declarados:** el escáner puede dar falsos positivos y negativos; `.env` local queda fuera del recorrido (su control es que git no lo versione); no revisamos servicios de terceros ni las cuentas de los integrantes; las credenciales de MySQL y de Airflow aún no existen.
**(h) Cómo validar.** `.\.venv\Scripts\python.exe scripts\escanear_secretos.py` (debe terminar en `hallazgos: 0`) y `pytest tests/test_secretos.py`.

---

## Qué falta del lado del equipo (hechos externos)
- Las **capturas manuales** de F2 (respuesta de `GET /health`, documentación en `/docs`, una consulta a `/kpis`, resultado de pytest y salida del escáner) las toma el equipo; el guion está en `docs/entrega_3/evidencias/guion_capturas_y_video.md`. La captura de `/docs` incluida como EV-017 es **automatizada del navegador**, no una captura manual.
- Antes de F3, una cuenta de MySQL local (el script SQL lo entrega F3).
