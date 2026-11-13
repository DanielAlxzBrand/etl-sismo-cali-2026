# Guía de evidencias para la plantilla del checklist

**Fecha:** 2026-11-12 · **Política (D35):** el equipo **no graba video**. Para cada ítem del checklist se presentan **archivos adjuntables** (salidas registradas, JSON, XML de pruebas, documentos e imágenes renderizadas) y, **de forma opcional**, capturas de pantalla. Las capturas automatizadas del navegador (rotuladas) y las salidas registradas son evidencia suficiente; una captura manual complementa, no condiciona el cierre de un ítem.

**Rótulos.** Una captura que tome el equipo se rotula «captura tomada por el equipo» con la fecha. La captura de `/docs` incluida en el repositorio (EV-017) se rotula «captura automatizada del navegador». Las imágenes generadas desde salidas reales (EV-021 a EV-024 y los diagramas de `docs/estrategia/img/`) se rotulan «imagen generada a partir de la salida registrada; no es una captura de pantalla».

**Cómo se lee cada ficha.** (a) archivo principal para adjuntar a la plantilla; (b) archivos de apoyo; (c) texto sugerido para la columna «Evidencia / observaciones»; (d) captura opcional, con comando probado; (e) cómo validar la evidencia con un comando de solo lectura. Las rutas son relativas a la raíz del repositorio. El índice de todas las evidencias con su sha256 está en `docs/evidencias/manifiesto.md`.

**Alcance de los resultados.** Proxy satelital, no evaluación estructural; 7 comunas de Cali con polígonos de afectación preliminar; estrato de 2015. No se generaliza a Cali.

**Comandos de PowerShell.** Todos se ejecutan en la raíz del repositorio con el entorno activado (`.\.venv\Scripts\Activate.ps1`) y no modifican nada. Para comprobar que no cambió nada: `git status --short` no debe imprimir nada.

## Índice
Fichas de los ítems 1.1 a 1.5 (Estrategia), 2.1 a 2.3 (API, fuentes y credenciales) y 4.1 a 4.3 (Carga relacional). Las de Pruebas y orquestación, Panel, Usuarios, UX y finanzas, Documentación y demostración y Cierre y paquete se agregan en cada componente con esta misma estructura.

---

## Estrategia · Problema, diseño estratégico y stakeholders (sección 1 del checklist)

### Ítem 1.1 · Data Thinking, insights y problema central
- **(a) Archivo principal:** `docs/estrategia/01_data_thinking.md` (Markdown). Demuestra: marco de cinco etapas con tabla de equivalencia, 11 insights con dato y fuente, problema central y pregunta vigente. **No demuestra:** investigación con usuarios ni que el marco sea el del curso (se adoptó a posteriori).
- **(b) Apoyo:** `docs/evidencias/estrategia/EV-011_cifras_verificadas.txt`, `EV-012_fuentes_externas.txt`, `docs/proyecto/decisiones_tecnicas.md` (decisión i).
- **(c) Texto sugerido:** «Marco de Data Thinking (cinco etapas, mapeo a posteriori), 11 insights con dato y fuente, problema central y pregunta vigente; sin investigación con usuarios: `docs/estrategia/01_data_thinking.md`.»
- **(d) Captura opcional:** editor con `01_data_thinking.md` en la tabla de insights (§3). Nombre: `captura_1.1_insights.png`. Comando probado: `.\.venv\Scripts\python.exe -m pytest tests/test_estrategia.py -q -p no:cacheprovider`.
- **(e) Validar:** el comando anterior debe terminar en `9 passed`; las cifras se comprueban con `EV-011`.

### Ítem 1.2 · Mapeo de stakeholders y tipología
- **(a) Archivo principal:** `docs/estrategia/02_stakeholders.md` (Markdown) con la imagen `docs/estrategia/img/matriz_poder_interes.png`. Demuestra: 11 stakeholders con rúbrica R1 reproducible y matriz poder-interés. **No demuestra:** contacto con ningún stakeholder (el campo dice «Ninguno»).
- **(b) Apoyo:** `tests/test_estrategia.py` (la prueba recalcula poder, interés y cuadrante).
- **(c) Texto sugerido:** «Mapa de 11 stakeholders con rúbrica R1 y matriz poder-interés basada en fuentes públicas; sin contacto con stakeholders: `docs/estrategia/02_stakeholders.md`.»
- **(d) Captura opcional:** la imagen de la matriz junto a la tabla de puntajes. Nombre: `captura_1.2_matriz.png`.
- **(e) Validar:** `.\.venv\Scripts\python.exe -m pytest tests/test_estrategia.py::test_rubrica_r1_y_matriz_poder_interes_son_consistentes -q -p no:cacheprovider`.

### Ítem 1.3 · Objetivo, alcance, OKR y KPI
- **(a) Archivo principal:** `docs/estrategia/03_objetivo_alcance_okr_kpi.md` (Markdown). Demuestra: objetivo, alcance, OKR con su estado real, K1 a K6, métricas de valor y trazabilidad. **No demuestra:** impacto en usuarios (no se mide); KR2, KR3 y KR5 quedan sin cubrir.
- **(b) Apoyo:** `docs/gold/KPIs.md`, `data/gold/kpis_gold.csv`, `docs/evidencias/estrategia/EV-011_cifras_verificadas.txt`, `docs/evidencias/api/EV-018_latencia_api.csv` (latencia de la API, medición local).
- **(c) Texto sugerido:** «Objetivo, alcance, OKR del Avance 1 con su estado, K1 a K6, métricas de valor y trazabilidad OKR → KPI → evidencia: `docs/estrategia/03_objetivo_alcance_okr_kpi.md`.»
- **(d) Captura opcional:** la tabla de trazabilidad (§4). Nombre: `captura_1.3_trazabilidad.png`.
- **(e) Validar:** `.\.venv\Scripts\python.exe -m pytest tests/test_estrategia.py::test_cifras_de_1_3_y_1_5_coinciden_con_las_salidas -q -p no:cacheprovider`.

### Ítem 1.4 · Canvas, Data Innovation Board y propuesta de valor
- **(a) Archivo principal:** `docs/estrategia/04_canvas_data_innovation_board.md` con la imagen `docs/estrategia/img/canvas_modelo_negocio.png`. Demuestra: nueve bloques, mapa de valor y diez hipótesis con experimento propuesto. **No demuestra:** que las hipótesis estén validadas ni cifras de mercado (ingresos y costos «no estimado»).
- **(b) Apoyo:** `docs/estrategia/indice.md`.
- **(c) Texto sugerido:** «Canvas, propuesta de valor y Data Innovation Board como ejercicio de diseño con hipótesis sin validar y sin cifras de mercado: `docs/estrategia/04_canvas_data_innovation_board.md`.»
- **(d) Captura opcional:** el aviso inicial y la imagen del Canvas visibles. Nombre: `captura_1.4_canvas.png`.
- **(e) Validar:** `.\.venv\Scripts\python.exe -m pytest tests/test_estrategia.py::test_1_4_declara_hipotesis_sin_validar_y_no_estimado -q -p no:cacheprovider`.

### Ítem 1.5 · MVP y criterios de aceptación
- **(a) Archivo principal:** `docs/estrategia/05_mvp_criterios_aceptacion.md` (Markdown). Demuestra: MVP con ocho funcionalidades (FE1 a FE8) y 29 criterios; 25 ejecutados con fecha y 4 «no verificado aún» (Airflow y dashboard). **No demuestra:** los criterios pendientes.
- **(b) Apoyo:** `docs/evidencias/estrategia/EV-009_determinismo_clon.txt` (dos corridas en un clon con los mismos sha256), `docs/evidencias/api/EV-014_pytest.txt`, `EV-016_respuestas_api.txt` y `EV-015_sin_escritura_hashes.txt` (criterios de la API).
- **(c) Texto sugerido:** «MVP del proyecto y 29 criterios de aceptación (23 verificados con su evidencia; 6 se verifican en Carga relacional, Pruebas y orquestación y Panel): `docs/estrategia/05_mvp_criterios_aceptacion.md`.»
- **(d) Captura opcional:** la tabla de criterios con la columna de estado visible. Nombre: `captura_1.5_criterios.png`.
- **(e) Validar:** `.\.venv\Scripts\python.exe -m pytest tests/test_estrategia.py::test_1_5_tiene_al_menos_24_criterios_y_no_marca_cumple_sin_verificar -q -p no:cacheprovider`.

---

## API, fuentes y credenciales · Backend y captura de datos (sección 2 del checklist)

### Ítem 2.1 · Arquitectura de backend, APIs y servicios
- **(a) Archivo principal:** `docs/api/arquitectura.md` (Markdown) con su diagrama `docs/api/img/arquitectura_backend.png`. Demuestra: capas, módulos, contratos, errores, seguridad y límites de una API de solo lectura con 11 rutas GET. **No demuestra:** que la API sea apta para exponerse en red (no tiene autenticación; uso local en 127.0.0.1) ni que MySQL, Airflow o el dashboard existan (están en construcción).
- **(b) Apoyo:**
  - `docs/evidencias/api/openapi.json` (EV-026; esquema completo del servicio).
  - `docs/evidencias/api/respuestas_api/` y `EV-016_respuestas_api.txt` (respuesta real de cada ruta, errores 404, 422 y 405, y cierre ordenado).
  - `docs/evidencias/api/junit_api.xml` (EV-025) y `EV-014_pytest.txt` (pruebas en un clon temporal; las de la API están en `tests/test_api.py`).
  - `docs/evidencias/api/EV-015_sin_escritura_hashes.txt` (sha256 de `data/` y de la base idénticos tras clonar, tras las pruebas y tras consultar el servidor real).
  - `docs/evidencias/api/EV-017_docs_navegador.png` («captura automatizada del navegador» de `/docs`).
  - `docs/evidencias/api/EV-018_latencia_api.csv` y `EV-021_latencias.png` (tabla y gráfico de latencias; mediciones locales de una máquina).
  - `docs/evidencias/api/EV-013_instalacion_paquetes.txt` y `EV-020_requirements_entorno_nuevo.txt` (versiones instaladas y entorno nuevo con `requirements.txt`).
  - `docs/validacion/verificacion_servicios.md` (subcriterios y estado).
- **(c) Texto sugerido:** «API de solo lectura (FastAPI, 11 rutas GET, errores uniformes y esquema OpenAPI), con pruebas contra las salidas y sha256 de `data/` y de la base idénticos antes y después de consultar: `docs/api/arquitectura.md` y `docs/evidencias/api/`.»
- **(d) Captura opcional** (la toma el equipo; se rotula «captura tomada por el equipo»):
  - `GET /health`: PowerShell, primero `.\.venv\Scripts\python.exe -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000` en una terminal y, en otra, `Invoke-RestMethod http://127.0.0.1:8000/health | ConvertTo-Json -Depth 5`. Debe verse `estado` «ok», `base_disponible` verdadero y las filas por tabla (5146, 5146, 23 y 107). Nombre: `captura_2.1_health.png`.
  - `/docs` en el navegador con las rutas desplegadas. Nombre: `captura_2.1_docs.png`.
  - `/kpis`: `(Invoke-RestMethod "http://127.0.0.1:8000/kpis?kpi_id=K1") | Select-Object kpi_id, grupo, valor, numerador, denominador | Format-Table` (los paréntesis hacen que PowerShell recorra la lista). Nombre: `captura_2.1_kpis.png`.
  - Resultado de pytest: `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider`, con la línea final «passed». Nombre: `captura_2.1_pytest.png`.
  - Para cerrar el servicio: Ctrl+C en la terminal 1.
- **(e) Validar:** `.\.venv\Scripts\python.exe -m pytest tests/test_api.py -q -p no:cacheprovider` (debe terminar en `17 passed`) y `Get-FileHash -Algorithm SHA256 data\gold\etl_sismo.db` antes y después de consultar la API (el valor no cambia).

### Ítem 2.2 · Fuentes de datos y metadatos
- **(a) Archivo principal:** `docs/bronze/catalogo_fuentes_metadatos.md` (Markdown) y su versión `docs/bronze/catalogo_fuentes.json`. Demuestra: 3 fuentes usadas, 2 de contexto y 9 descartadas, con publicador, URL, protocolo, formato, autenticación, límites, columnas, cobertura, fechas, licencia, snapshot con sha256 y diccionario por capa. **No demuestra:** una revisión jurídica de las licencias (se toman de los catálogos consultados) ni que las cifras de prensa de la evaluación ATC-20 sean oficiales (no se recotejaron).
- **(b) Apoyo:**
  - `docs/evidencias/api/respuestas_api/fuentes.json` (respuesta real de `/fuentes`) y `metadata.json` (respuesta de `/metadata`).
  - `docs/evidencias/api/EV-014_pytest.txt` y `junit_api.xml` (prueba `test_catalogo`).
  - `data/bronze/manifest.jsonl` (origen de las huellas).
- **(c) Texto sugerido:** «Catálogo de fuentes y metadatos generado desde el manifiesto de Bronze, con licencias, fechas, snapshots (sha256) y diccionario por capa; coincide con el manifiesto según prueba automática: `docs/bronze/catalogo_fuentes_metadatos.md`.»
- **(d) Captura opcional:** el catálogo abierto en la ficha de `edificaciones` con el snapshot y su sha256 visibles. Nombre: `captura_2.2_catalogo.png`.
- **(e) Validar:** `.\.venv\Scripts\python.exe -m pytest tests/test_catalogo.py -q -p no:cacheprovider` (debe terminar en `5 passed`); `.\.venv\Scripts\python.exe scripts\make_catalogo_fuentes.py` y luego `git status --short` no debe mostrar cambios en el catálogo.

### Ítem 2.3 · Credenciales, claves y tokens
- **(a) Archivo principal:** `docs/seguridad/gestion_credenciales.md` (Markdown). Demuestra: qué se requiere hoy (ninguna credencial obligatoria), variables previstas (`MYSQL_*` en Carga relacional y claves de Airflow en Pruebas y orquestación, «previstas, no usadas todavía»), dónde se guardan, rotación, revocación y respuesta ante una filtración. **No demuestra:** que no exista una filtración en servicios de terceros ni que el escáner encuentre todos los secretos posibles. Estado: Cumple; se revalida con las variables `MYSQL_*` (Carga relacional) y con el escáner sobre el zip final (Cierre y paquete).
- **(b) Apoyo:**
  - `docs/evidencias/api/EV-019_escaner_secretos.txt` y `EV-024_escaner.png` (escáner sobre el clon, su historial de git y un zip de prueba: `hallazgos: 0`).
  - `.env.example` (solo `HTTP_USER_AGENT`, la única variable que el código lee).
  - `tests/test_secretos.py` y `docs/evidencias/api/junit_api.xml` (detección de un secreto sembrado por tipo, `.env` fuera de `git ls-files`, `make_dist` sin `.env`).
  - `tests/test_logger.py` y la prueba `test_el_registro_enmascara_un_token_de_prueba` (enmascarado del registro).
- **(c) Texto sugerido:** «Política de credenciales y escáner de secretos sobre árbol, historial, notebooks, logs y zip, sin hallazgos; `.env` fuera de git y `.env.example` sin valores: `docs/seguridad/gestion_credenciales.md`.»
- **(d) Captura opcional:** PowerShell con `.\.venv\Scripts\python.exe scripts\escanear_secretos.py`, que debe terminar en `hallazgos: 0` sin mostrar ningún valor. Nombre: `captura_2.3_escaner.png`.
- **(e) Validar:** `.\.venv\Scripts\python.exe scripts\escanear_secretos.py` (termina en `hallazgos: 0`) y `.\.venv\Scripts\python.exe -m pytest tests/test_secretos.py -q -p no:cacheprovider` (debe terminar en `10 passed`).

---

## Carga relacional · Almacenamiento y carga (sección 4 del checklist)

### Ítem 4.1 · Carga al almacenamiento destino (MySQL)
- **(a) Archivo principal:** `docs/almacenamiento/carga_y_verificacion.md` (Markdown), con `docs/almacenamiento/modelo_datos.md` y su diagrama `docs/almacenamiento/img/modelo_er.png`. Demuestra: esquema de siete tablas con claves y restricciones, carga por lotes con historial desde los CSV de Silver y Gold y conciliación al 100 %. **No demuestra:** uso con varios usuarios a la vez ni rendimiento en otro equipo.
- **(b) Apoyo:**
  - `docs/evidencias/almacenamiento/EV-028_verificacion_mysql.txt` (batería en vivo sobre la base de prueba: 26 de 26 comprobaciones).
  - `docs/evidencias/almacenamiento/EV-029_carga_real_mysql.txt` (carga real a `sismo_cali`: conciliación, idempotencia, integridad y cifras iguales a Gold).
  - `docs/evidencias/almacenamiento/EV-032_api_mysql_vs_sqlite.txt`, `EV-032_latencia_api_mysql_vs_sqlite.csv` y `EV-032_latencia_api_mysql_vs_sqlite.png` (la API sirve lo mismo desde MySQL que desde SQLite, con sus latencias).
  - `docs/evidencias/almacenamiento/EV-027_conector_mysql.txt` (versiones de PyMySQL y `cryptography`).
  - `tests/test_carga_relacional.py` (54 pruebas sin servidor MySQL).
  - `docs/almacenamiento/mysql_configuracion.md` (cómo se crean las bases y el usuario).
- **(c) Texto sugerido:** «Almacén relacional en MySQL 8.0 con siete tablas, claves primarias y foráneas, restricciones de validación y carga por lotes; la carga real concilia al 100 % con Gold y la API sirve las mismas respuestas desde MySQL y SQLite: `docs/almacenamiento/carga_y_verificacion.md` y `docs/evidencias/almacenamiento/EV-029_carga_real_mysql.txt`.»
- **(d) Captura opcional** (la toma el equipo; se rotula «captura tomada por el equipo»): PowerShell con `.\.venv\Scripts\python.exe scripts\mysql\verificar_mysql.py`, que debe terminar en «26 de 26 comprobaciones correctas» y no mostrar ninguna contraseña. Nombre: `captura_4.1_verificacion.png`.
- **(e) Validar:** `.\.venv\Scripts\python.exe scripts\mysql\verificar_mysql.py` (código de salida 0) y `.\.venv\Scripts\python.exe -m pytest tests/test_carga_relacional.py -q -p no:cacheprovider` (debe terminar en `54 passed`).

### Ítem 4.2 · Persistencia histórica e integridad referencial
- **(a) Archivo principal:** `docs/almacenamiento/modelo_datos.md` (Markdown). Demuestra: claves primarias y foráneas con `ON DELETE RESTRICT`, restricciones `CHECK`, historial por corrida e idempotencia por clave determinista. **No demuestra:** que no exista corrupción por fallos del servidor (el motor InnoDB es transaccional, pero no lo probamos).
- **(b) Apoyo:**
  - `docs/evidencias/almacenamiento/EV-028_verificacion_mysql.txt` (historial con corrida nueva, reversión ante un fallo inyectado y violaciones de integridad rechazadas con su código de error).
  - `docs/evidencias/almacenamiento/EV-029_carga_real_mysql.txt` (idempotencia y 0 filas huérfanas en la base real).
  - `docs/evidencias/almacenamiento/EV-031_respaldo_restauracion.txt` (respaldo en CSV con sha256, restauración y conciliación por huella de filas).
  - `tests/test_carga_relacional.py` y `tests/test_respaldo_y_medicion.py`.
- **(c) Texto sugerido:** «Cada carga distinta es una corrida completa con todas sus filas; la misma entrada no duplica nada, un fallo revierte todo y la base rechaza las filas que violan claves o restricciones: `docs/almacenamiento/modelo_datos.md` y `docs/evidencias/almacenamiento/EV-028_verificacion_mysql.txt`.»
- **(d) Captura opcional:** el resultado de `.\.venv\Scripts\python.exe scripts\mysql\respaldar_restaurar.py`, con la tabla de huellas «igual» en las siete tablas. Nombre: `captura_4.2_respaldo.png`.
- **(e) Validar:** `.\.venv\Scripts\python.exe -m pytest tests/test_carga_relacional.py tests/test_respaldo_y_medicion.py -q -p no:cacheprovider` y, con MySQL, `scripts\mysql\verificar_mysql.py` y `scripts\mysql\respaldar_restaurar.py`.

### Ítem 4.3 · Rendimiento del cargue
- **(a) Archivo principal:** `docs/evidencias/almacenamiento/EV-030_benchmark_lotes.txt` (informe con la tabla de medianas, p95 y filas por segundo). Demuestra: la carga fila a fila frente a lotes de 500, 1000 y 2000 (1 calentamiento y 5 repeticiones), la elección del lote 2000 (D53) y que la carga repetida no recarga nada. **No demuestra:** los mismos tiempos en otro equipo; son mediciones locales.
- **(b) Apoyo:**
  - `docs/evidencias/almacenamiento/EV-030_benchmark_lotes.csv` y `EV-030_benchmark_lotes.png` (datos y gráfico).
  - `config/config.yaml` (`almacenamiento.lote`).
  - `docs/DECISIONES.md` (D47 y D53).
- **(c) Texto sugerido:** «Carga por lotes medida con tres tamaños frente a fila a fila (3,4 veces más rápido con el lote elegido), con mediana, p95 y filas por segundo: `docs/evidencias/almacenamiento/EV-030_benchmark_lotes.txt`.»
- **(d) Captura opcional:** la tabla impresa por `.\.venv\Scripts\python.exe scripts\mysql\benchmark_lotes.py`. Nombre: `captura_4.3_lotes.png`.
- **(e) Validar:** `.\.venv\Scripts\python.exe scripts\mysql\benchmark_lotes.py` (imprime la tabla y el lote propuesto; sin `--fijar` no cambia `config.yaml`).

---

## Cómo se produjeron las evidencias de la capa de servicio
`scripts/evidencias/evidencias_api.py` clona el commit a una carpeta temporal fuera del repositorio, ejecuta ahí las pruebas, el servicio, el navegador sin ventana, el escáner y el entorno nuevo, y guarda las salidas **saneadas** (sin rutas de usuario, usuario ni equipo: se sustituyen por `<REPO>`, `<CLON>`, `<TEMP>`, `<VENV>`, `<USUARIO>` y `<EQUIPO>`) en `docs/evidencias/api/`. `scripts/evidencias/registrar_manifiesto.py` calcula el sha256 de cada archivo y lo registra en el manifiesto. Una prueba (`tests/test_evidencias.py`) verifica que ninguna evidencia guardada lleva datos del equipo.

## Componentes en construcción
Se agregan en cada componente con la misma estructura de fichas.
