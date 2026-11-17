# Guía de evidencias para la plantilla del checklist

**Fecha:** 2026-11-15 (actualizada en la auditoría intermedia; versión inicial 2026-11-12) · **Política (D35):** el equipo **no graba video**. Para cada ítem del checklist se presentan **archivos adjuntables** (salidas registradas, JSON, XML de pruebas, documentos e imágenes renderizadas) y, **de forma opcional**, capturas de pantalla. Las capturas automatizadas del navegador (rotuladas) y las salidas registradas son evidencia suficiente; una captura manual complementa, no condiciona el cierre de un ítem.

**Rótulos.** Una captura que tome el equipo se rotula «captura tomada por el equipo» con la fecha. La captura de `/docs` incluida en el repositorio (EV-017) y las del panel (EV-054) se rotulan «captura automatizada del navegador». Las imágenes generadas desde salidas reales (EV-021 a EV-024, EV-045 a EV-048, EV-058 a EV-060, los diagramas de `docs/orquestacion/img/` y `docs/panel/img/` y los de `docs/estrategia/img/`) se rotulan «imagen generada a partir de la salida registrada; no es una captura de pantalla».

**Cómo se lee cada ficha.** (a) archivo principal para adjuntar a la plantilla; (b) archivos de apoyo; (c) texto sugerido para la columna «Evidencia / observaciones»; (d) captura opcional, con comando probado; (e) cómo validar la evidencia con un comando de solo lectura. Las rutas son relativas a la raíz del repositorio. El índice de todas las evidencias con su sha256 está en `docs/evidencias/manifiesto.md`.

**Numeración.** EV-086 es un número no usado: no hay ninguna evidencia registrada con ese identificador ni fila en el manifiesto, y la numeración salta de EV-085 a EV-087 (ningún archivo del proyecto lo cita).

**Alcance de los resultados.** Proxy satelital, no evaluación estructural; 7 comunas de Cali con polígonos de afectación preliminar; estrato de 2015. No se generaliza a Cali.

**Comandos de PowerShell.** Todos se ejecutan en la raíz del repositorio con el entorno activado (`.\.venv\Scripts\Activate.ps1`) y no modifican nada. Para comprobar que no cambió nada: `git status --short` no debe imprimir nada.

## Índice
Fichas de los ítems 1.1 a 1.5 (Estrategia), 2.1 a 2.3 (API, fuentes y credenciales), 3.1, 3.2 y 5.3 (Panel), 3.3 y 6.1 a 6.4 (Usuarios, UX y finanzas), 4.1 a 4.3 (Carga relacional) y 5.1, 5.2, 5.4, 5.5 y 5.6 (Pruebas y orquestación). Las fichas de los ítems 6.5 y 7.1 a 7.5 (Documentación y demostración, y Cierre y paquete) se escribieron en la auditoría intermedia y dicen el estado real de cada uno; ninguno está en «Cumple».

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
- **(a) Archivo principal:** `docs/estrategia/05_mvp_criterios_aceptacion.md` (Markdown). Demuestra: MVP con ocho funcionalidades (FE1 a FE8) y 29 criterios, todos ejecutados con fecha. AC26 se ajustó a las cuatro tareas de la guía (D66). **No demuestra:** el uso por personas reales del dashboard.
- **(b) Apoyo:** `docs/evidencias/estrategia/EV-009_determinismo_clon.txt` (dos corridas en un clon con los mismos sha256), `docs/evidencias/api/EV-014_pytest.txt`, `EV-016_respuestas_api.txt` y `EV-015_sin_escritura_hashes.txt` (criterios de la API).
- **(c) Texto sugerido:** «MVP del proyecto y 29 criterios de aceptación (los 29 verificados con su evidencia; AC26 con la interpretación de D66): `docs/estrategia/05_mvp_criterios_aceptacion.md`.»
- **(d) Captura opcional:** la tabla de criterios con la columna de estado visible. Nombre: `captura_1.5_criterios.png`.
- **(e) Validar:** `.\.venv\Scripts\python.exe -m pytest tests/test_estrategia.py::test_1_5_tiene_al_menos_24_criterios_y_cada_estado_es_coherente -q -p no:cacheprovider`.

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
- **(a) Archivo principal:** `docs/seguridad/gestion_credenciales.md` (Markdown). Demuestra: qué se requiere hoy (ninguna credencial obligatoria), variables en uso (`MYSQL_*`, `MYSQL_DOCKER_*` y la contraseña de la interfaz de Airflow, solo en su `.env`), dónde se guardan, rotación, revocación y respuesta ante una filtración. **No demuestra:** que no exista una filtración en servicios de terceros ni que el escáner encuentre todos los secretos posibles. Estado: Cumple; revalidado con las variables `MYSQL_*` (Carga relacional), con las del usuario de Docker y de Airflow (Pruebas y orquestación, EV-049), con el panel, que no maneja credenciales (EV-056) y, al final, con el escáner sobre el zip final (Cierre y paquete).
- **(b) Apoyo:**
  - `docs/evidencias/api/EV-019_escaner_secretos.txt` y `EV-024_escaner.png` (escáner sobre el clon, su historial de git y un zip de prueba: `hallazgos: 0`).
  - `.env.example` (solo `HTTP_USER_AGENT`, la única variable que el código lee).
  - `tests/test_secretos.py` y `docs/evidencias/api/junit_api.xml` (detección de un secreto sembrado por tipo, `.env` fuera de `git ls-files`, `make_dist` sin `.env`).
  - `tests/test_logger.py` y la prueba `test_el_registro_enmascara_un_token_de_prueba` (enmascarado del registro).
  - `docs/evidencias/orquestacion/EV-049_canario_orquestacion.txt` (las contraseñas de MySQL, del usuario de Docker y de la interfaz de Airflow no aparecen en el árbol, los registros, el historial, `airflow-medallon`, la imagen ni un zip de prueba: 0 hallazgos).
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
  - `docs/almacenamiento/phpmyadmin.md` y `docs/evidencias/servicios/EV-085_phpmyadmin_en_vivo.txt` con sus ocho capturas automatizadas (phpMyAdmin con la cuenta de solo lectura: tablas, claves foráneas, conteos iguales a Gold y escrituras rechazadas con el error #1142).
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
  - `docs/evidencias/servicios/EV-085_captura_relaciones_construccion.png` (las tres claves foráneas de `construccion` con `RESTRICT`, vistas en phpMyAdmin).
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

## Panel · Interfaz y consumo de la API (ítems 3.1, 3.2 y 5.3 del checklist)

### Ítem 3.1 · Componentes de interfaz y dashboards
- **(a) Archivo principal:** `docs/panel/guia_de_uso.md` (Markdown), con `docs/panel/arquitectura_panel.md` y `docs/panel/trazabilidad_ui.md`. Demuestra: un panel de ocho páginas que muestra K1 a K6, las sensibilidades, la calidad de la llave, las construcciones y las fuentes, con el recuadro de alcance en todas, intervalos y conclusiones generadas con la regla del proyecto. **No demuestra:** usabilidad con personas ni un despliegue (el panel se ejecuta en local).
- **(b) Apoyo:**
  - `docs/evidencias/panel/EV-054_captura_respuesta.png`, `EV-054_captura_estratos.png`, `EV-054_captura_comunas.png`, `EV-054_captura_sensibilidades.png`, `EV-054_captura_concentracion.png`, `EV-054_captura_calidad.png`, `EV-054_captura_construcciones.png` y `EV-054_captura_fuentes.png` (capturas automatizadas del navegador) y `EV-054_capturas_panel.txt` (registro).
  - `docs/evidencias/panel/EV-052_ejecucion_real.txt` (ejecución con el lanzador, salud, ocho páginas y cierre limpio).
  - `docs/panel/img/arquitectura_panel.png` y `docs/evidencias/panel/EV-060_trazabilidad_componentes.png` (imágenes generadas a partir de la salida registrada; no son capturas de pantalla).
  - `docs/evidencias/panel/EV-057_contrastes.txt` (contrastes calculados).
- **(c) Texto sugerido:** «Panel Streamlit de solo lectura con ocho páginas (K1 a K6, sensibilidades, calidad, construcciones y fuentes), alcance visible en todas y conclusiones generadas con la regla del proyecto; se ejecuta con un comando: `docs/panel/guia_de_uso.md` y capturas en `docs/evidencias/panel/`.»
- **(d) Captura opcional** (la toma el equipo; se rotula «captura tomada por el equipo»): el navegador en la dirección que imprime `.\.venv\Scripts\python.exe scripts\panel\ejecutar_panel.py`, con la página Respuesta. Nombre: `captura_3.1_panel.png`.
- **(e) Validar:** `.\.venv\Scripts\python.exe scripts\panel\ejecutar_panel.py --verificar` (código de salida 0) y `.\.venv\Scripts\python.exe -m pytest tests/test_panel_paginas.py -q -p no:cacheprovider`.

### Ítem 3.2 · Integración del frontend con la API
- **(a) Archivo principal:** `docs/panel/arquitectura_panel.md` (Markdown). Demuestra: un cliente HTTP único y de solo lectura, páginas modulares, errores de la API traducidos a avisos claros y un registro de componentes con su ruta, su campo y su archivo de salida. **No demuestra:** rendimiento con muchas personas a la vez.
- **(b) Apoyo:**
  - `docs/panel/trazabilidad_ui.md` (generado desde el registro).
  - `tests/test_panel_registro_y_aislamiento.py` (análisis estático: solo la API, solo GET, sin recursos externos ni cifras escritas a mano) y `tests/test_panel_cliente.py`.
  - `docs/evidencias/panel/EV-055_mediciones_panel.txt` y `EV-055_mediciones_panel.csv` (mediciones locales) y `EV-058_latencias_cliente.png` (imagen generada a partir de la salida registrada).
  - `docs/evidencias/panel/EV-056_canario_panel.txt` (el panel no maneja credenciales).
- **(c) Texto sugerido:** «El panel consume únicamente la API por HTTP (solo GET) con un cliente propio, de forma modular y con errores traducidos a avisos; ninguna cifra se escribe a mano: `docs/panel/arquitectura_panel.md` y `docs/panel/trazabilidad_ui.md`.»
- **(d) Captura opcional:** la página «Fuentes y sistema» con el almacenamiento activo visible. Nombre: `captura_3.2_integracion.png`.
- **(e) Validar:** `.\.venv\Scripts\python.exe -m pytest tests/test_panel_registro_y_aislamiento.py tests/test_panel_cliente.py -q -p no:cacheprovider`.

### Ítem 5.3 · Integración entre interfaz, lógica y almacenamiento
- **(a) Archivo principal:** `docs/panel/pruebas_panel.md` (Markdown). Demuestra: pruebas de cada página con `AppTest`, integración del panel con la API real sobre una copia de la base, humo de extremo a extremo de solo lectura y equivalencia de los datos entre SQLite y MySQL. **No demuestra:** pruebas en un navegador por personas.
- **(b) Apoyo:**
  - `tests/test_panel_paginas.py`, `tests/test_panel_integracion.py` y `tests/test_panel_humo_extremo_a_extremo.py`.
  - `docs/evidencias/panel/EV-053_equivalencia_almacenes.txt` (12 de 12 respuestas y 8 de 8 páginas idénticas con SQLite y con MySQL).
  - `docs/evidencias/panel/EV-052_ejecucion_real.txt` y `docs/evidencias/panel/EV-059_cobertura_panel.png` (imagen generada a partir de la salida registrada).
- **(c) Texto sugerido:** «Pruebas de integración interfaz-API-almacenamiento: los valores del panel coinciden con las salidas del pipeline, el humo de extremo a extremo de solo lectura pasa y los datos son idénticos con SQLite y MySQL: `docs/panel/pruebas_panel.md`.»
- **(d) Captura opcional:** PowerShell con `.\.venv\Scripts\python.exe -m pytest tests/test_panel_humo_extremo_a_extremo.py -q -p no:cacheprovider`, que debe terminar en `5 passed`. Nombre: `captura_5.3_humo.png`.
- **(e) Validar:** `.\.venv\Scripts\python.exe -m pytest tests/test_panel_paginas.py tests/test_panel_integracion.py tests/test_panel_humo_extremo_a_extremo.py -q -p no:cacheprovider` y, con MySQL, `.\.venv\Scripts\python.exe scripts\evidencias\evidencia_panel_almacenes.py`.

---

## Usuarios, UX y finanzas · Evaluación, sesiones y costos (ítems 3.3 y 6.1 a 6.4 del checklist)

### Ítem 3.3 · Usabilidad, capacidad de respuesta y coherencia visual
- **(a) Archivo principal:** `docs/usuarios/evaluacion_heuristica.md` (Markdown). Demuestra: evaluación heurística interna con las diez heurísticas de Nielsen sobre las ocho páginas, 14 hallazgos con severidad 0 a 4 y captura, fortalezas, matriz heurística × página y la reevaluación tras corregir 8 hallazgos (iteración técnica). **No demuestra:** que personas reales entiendan el panel ni que los cambios mejoren su experiencia; la severidad de después es una estimación nuestra.
- **(b) Apoyo:**
  - `docs/evidencias/usuarios/EV-066_capturas_anchos.txt` (24 capturas automatizadas en 1400, 1024 y 390 px, con desbordamiento y texto recortado), `EV-069_capturas_390_barra_cerrada.txt` (8 capturas más a 390 px).
  - `docs/evidencias/usuarios/EV-067_mediciones_anchos.txt` y su `.csv` (tiempo de dibujo medido en el navegador; medición local de una máquina) y `EV-068_contraste_texto.txt` (contraste calculado, sin declarar un nivel).
  - `docs/evidencias/ajustes_ux/`: EV-073 a EV-076 (antes de los ajustes y verificación del contraste de 1,0, que era una etiqueta oculta), EV-077 a EV-079 (24 capturas, tiempos con su variabilidad y contrastes después), EV-080 (F-11 evaluado y aplazado), EV-081 (mutaciones, todas detectadas) y EV-082 (suite en un clon con el entorno nuevo).
- **(c) Texto sugerido:** «Evaluación heurística interna del panel con 14 hallazgos priorizados, 8 corregidos y reevaluados con capturas antes y después en tres anchos, tiempos de dibujo medidos y contraste calculado; las sesiones con personas usuarias están preparadas y pendientes: `docs/usuarios/evaluacion_heuristica.md`.»
- **(d) Captura opcional:** la página «Respuesta» a 1024 px después de los ajustes, con las tarjetas completas (F-01): `docs/evidencias/ajustes_ux/EV-077_captura_respuesta_1024.png`. Nombre sugerido: `captura_3.3_respuesta_1024.png`.
- **(e) Validar:** `.\.venv\Scripts\python.exe -m pytest tests/test_usuarios_estructura.py -q -p no:cacheprovider`.

### Ítems 6.1, 6.2 y 6.3 · Sesiones, métricas y fricciones (pendientes por un hecho externo)
- **(a) Archivo principal:** `docs/usuarios/README.md` (índice) con `protocolo_sesiones.md`, `guion_sesion.md`, `consentimiento.md` e `instrumentos.md`. Demuestra: material preparado para 2 o 3 sesiones reales (seis tareas con criterio de éxito, consentimiento, SUS y CSAT), un script de análisis probado y un registro de las 14 fricciones de la evaluación heurística con su decisión. **No demuestra:** que se haya hecho alguna sesión; `docs/usuarios/sesiones_reales/` solo tiene plantillas y los ítems siguen «Pendiente (hecho externo)».
- **(b) Apoyo:**
  - `scripts/usuarios/analizar_sesiones.py` y `tests/test_usuarios.py` (SUS con vectores conocidos, cero sesiones, rechazo de filas simuladas, n pequeño y Wilson).
  - `docs/usuarios/simulacion/` y `docs/usuarios/resultados_simulacion.md`: **datos sintéticos rotulados, no son personas; no cuentan**.
  - `docs/usuarios/registro_de_friccion.md` (14 fricciones de la evaluación heurística, con su decisión) y `trazabilidad_de_cambios.md` (llena con los ajustes de la iteración técnica; ninguno viene de sesiones con personas).
- **(c) Texto sugerido:** «Material de las sesiones con personas usuarias preparado y script de análisis probado con datos sintéticos; las sesiones reales aún no se han realizado: `docs/usuarios/README.md`.»
- **(d) Captura opcional:** ninguna: no hay sesiones que capturar.
- **(e) Validar:** `.\.venv\Scripts\python.exe -m pytest tests/test_usuarios.py tests/test_usuarios_estructura.py -q -p no:cacheprovider` y `.\.venv\Scripts\python.exe scripts\usuarios\analizar_sesiones.py` (debe decir «No hay sesiones reales»).

### Ítem 6.4 · Finanzas y costos
- **(a) Archivo principal:** `docs/finanzas/estructura_costos.md` (Markdown). Demuestra: siete categorías de costo, su relación con el Canvas, el consumo medido y las fórmulas con precios como parámetros vacíos. **No demuestra:** cuánto cuesta operar el panel (ningún precio tiene valor) ni la sostenibilidad del proyecto.
- **(b) Apoyo:**
  - `docs/finanzas/recursos_medidos.csv` (EV-070) y `config/parametros_costos.yaml`.
  - `scripts/finanzas/costos.py` y `tests/test_finanzas.py`.
- **(c) Texto sugerido:** «Estructura de costos por categorías, consumo de recursos medido y fórmulas de costo por ejecución con los precios como parámetros vacíos (sin cifras monetarias): `docs/finanzas/estructura_costos.md`.»
- **(d) Captura opcional:** PowerShell con `.\.venv\Scripts\python.exe scripts\finanzas\costos.py`, que debe terminar en «costo no calculado: faltan parámetros». Nombre: `captura_6.4_costos.png`.
- **(e) Validar:** `.\.venv\Scripts\python.exe -m pytest tests/test_finanzas.py tests/test_usuarios_estructura.py -q -p no:cacheprovider`.

---

## Pruebas y orquestación · Pruebas, Airflow y defectos (sección 5 del checklist)

### Ítem 5.1 · Casos de prueba por función crítica
- **(a) Archivo principal:** `docs/validacion/matriz_casos_prueba.md` (Markdown, con su `.csv`). Demuestra: 27 funciones críticas con 179 casos (78 correctos, 61 incorrectos y 40 límite), cada uno con su resultado esperado y la prueba que lo ejecuta, generados desde una única definición. **No demuestra:** que no existan fallos fuera de los casos definidos.
- **(b) Apoyo:**
  - `docs/validacion/informe_pruebas.md` y `informe_pruebas.csv` (resultado de cada caso en la última ejecución: 1252 de 1252).
  - `tests/test_matriz_casos.py` (cada función crítica tiene casos y cada prueba citada existe).
  - `docs/evidencias/orquestacion/EV-048_cobertura_por_modulo.png` (imagen generada a partir de la salida registrada; no es una captura de pantalla).
  - `docs/evidencias/orquestacion/EV-050_pruebas_clon.txt` (las pruebas de ese momento pasan en un clon limpio) y `docs/evidencias/usuarios/EV-072_suite_en_entorno_nuevo.txt` (en su momento pasaron 822 pruebas en un entorno nuevo con Python 3.13, creado según `docs/evidencias/endurecimiento/EV-062_instalacion_desde_cero.txt`); la repetición más reciente, en un clon sin variables de UTF-8, es `docs/evidencias/servicios/EV-089_suite_final_sin_utf8.txt`.
- **(c) Texto sugerido:** «Matriz de 179 casos de prueba para 27 funciones críticas, cada uno con su resultado esperado y su prueba automática en verde: `docs/validacion/matriz_casos_prueba.md`.»
- **(d) Captura opcional:** PowerShell con `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider`, que debe terminar en `1252 passed`. Nombre: `captura_5.1_pytest.png`.
- **(e) Validar:** `.\.venv\Scripts\python.exe -m pytest tests/test_matriz_casos.py -q -p no:cacheprovider` y `.\.venv\Scripts\python.exe scripts\make_matriz_casos.py` (regenera la matriz; `git status --short` no debe mostrar cambios).

### Ítem 5.2 · Datos correctos, incorrectos y casos límite
- **(a) Archivo principal:** `docs/validacion/informe_pruebas.md` (Markdown, generado). Demuestra: cada caso etiquetado como correcto, incorrecto o límite con su resultado obtenido; las salidas reales se reproducen byte a byte. **No demuestra:** datos de otras fuentes ni de otros sismos.
- **(b) Apoyo:**
  - `docs/validacion/matriz_casos_prueba.md` (tipo de cada caso).
  - `tests/test_casos_limite.py`, `tests/test_carga_relacional.py` y `tests/test_usuario_docker.py` (entradas inválidas y valores en el borde).
  - `docs/evidencias/orquestacion/EV-035_estabilidad_pipeline.txt` (las nueve salidas se regeneran idénticas).
- **(c) Texto sugerido:** «Probamos datos correctos, incorrectos y límite en cada función crítica (78, 61 y 40 casos) y la reproducción byte a byte de las salidas: `docs/validacion/informe_pruebas.md`.»
- **(d) Captura opcional:** el informe con la columna de tipo visible. Nombre: `captura_5.2_informe.png`.
- **(e) Validar:** `.\.venv\Scripts\python.exe -m pytest tests/test_casos_limite.py tests/test_carga_relacional.py tests/test_pipeline_reproducible.py -q -p no:cacheprovider`.

### Ítem 5.4 · MLOps y orquestación con Airflow
- **(a) Archivo principal:** `docs/orquestacion/guia_de_implementacion.md` (Markdown), con `docs/orquestacion/diferencias_con_la_guia.md`, `docs/orquestacion/mlops_y_produccion.md` y el diagrama `docs/orquestacion/img/arquitectura_orquestacion.png`. Demuestra: el DAG `medallon_etl_sismo` con cuatro tareas en Airflow 3.3.2 con Docker, ejecutado de forma manual (con repetición y fallo inducido) y programado (`0 6 * * *`, hora de Bogotá). **No demuestra:** que se ejecute con el equipo apagado ni un despliegue en la nube; LLMOps no aplica (D22).
- **(b) Apoyo:**
  - `docs/evidencias/orquestacion/EV-037_pasos_13_a_19.txt`, `EV-038_pasos_27_a_30.txt` y `EV-039_pasos_31_a_33.txt` (carpeta, compose, imagen, contenedores sanos, interfaz y DAG sin errores de importación).
  - `docs/evidencias/orquestacion/EV-040_origen_mysql_desde_docker.txt` (origen con el que MySQL ve la conexión y privilegios mínimos).
  - `docs/evidencias/orquestacion/EV-041_ejecucion_manual.txt` y `EV-042_fallo_inducido_y_recuperacion.txt`.
  - `docs/evidencias/orquestacion/EV-043_programacion.txt` y `EV-044_operacion.txt` (con `EV-044_estados_tareas.csv`).
  - `docs/evidencias/orquestacion/EV-045_estados_de_tareas.png`, `EV-046_esperado_frente_a_obtenido.png` y `EV-047_ejecucion_programada.png` (imágenes generadas a partir de la salida registrada; no son capturas de pantalla).
  - `docs/evidencias/servicios/EV-087_airflow_desde_el_zip.txt` (Airflow construido y ejecutado desde el zip, en una carpeta de otro nombre y con el puerto 8082: interfaz, `list-import-errors` sin datos y las cuatro tareas en éxito) y `docs/orquestacion/operacion.md` (secciones «Desde el zip» y «Operación en otra máquina»).
  - `dags/medallon_etl_dag.py`, `orquestacion/` y `tests/test_dag_estatico.py` (24 pruebas estáticas), `tests/test_servicios_compose.py` y `tests/test_preparar_airflow.py` (compose adaptado y preparación de la carpeta de Airflow).
- **(c) Texto sugerido:** «DAG de Airflow 3.3.2 en Docker con cuatro tareas (Bronze, Silver, Gold y carga a MySQL), ejecutado de forma manual y programada, con fallo inducido y recuperación; las salidas coinciden con las versionadas: `docs/orquestacion/guia_de_implementacion.md` y `docs/evidencias/orquestacion/EV-043_programacion.txt`.»
- **(d) Captura opcional** (la toma el equipo; se rotula «captura tomada por el equipo»): la interfaz de Airflow en `http://localhost:8080` con el DAG y sus ejecuciones, sin mostrar la contraseña. Nombre: `captura_5.4_airflow.png`.
- **(e) Validar:** `.\.venv\Scripts\python.exe -m pytest tests/test_dag_estatico.py -q -p no:cacheprovider` y, con Docker Desktop en marcha, `docker compose ps` y `docker compose exec airflow-scheduler airflow dags list-import-errors` desde la carpeta `airflow-medallon`.

### Ítem 5.5 · Resultado esperado, obtenido y evidencia por prueba
- **(a) Archivo principal:** `docs/validacion/informe_pruebas.md` (Markdown, con `informe_pruebas.csv`). Demuestra: por cada caso, el resultado esperado, el obtenido, su duración y la prueba; la cobertura por módulo (74,2 % de 6.137 líneas) y las métricas de validación del análisis (K1 recalculado con SQL y una fórmula propia, diferencia máxima de 4,82e-13). **No demuestra:** métricas de modelos, porque no se entrenan (N/A justificado, D22).
- **(b) Apoyo:**
  - `docs/validacion/cobertura_pruebas.csv` y `docs/evidencias/orquestacion/EV-048_cobertura_por_modulo.png`.
  - `docs/evidencias/orquestacion/EV-046_esperado_frente_a_obtenido.png` y `EV-041_ejecucion_manual.txt` (esperado frente a obtenido en el DAG).
  - `scripts/informe_pruebas.py` y `tests/test_informe_pruebas.py`.
- **(c) Texto sugerido:** «Informe generado desde la salida de `pytest` con resultado esperado, obtenido y evidencia por caso, cobertura por módulo y métricas de validación del análisis; sin modelos que validar: `docs/validacion/informe_pruebas.md`.»
- **(d) Captura opcional:** PowerShell con `.\.venv\Scripts\python.exe scripts\informe_pruebas.py`, que debe terminar en «0 fallan, 0 casos sin resultado». Nombre: `captura_5.5_informe.png`.
- **(e) Validar:** `.\.venv\Scripts\python.exe scripts\informe_pruebas.py` y `.\.venv\Scripts\python.exe -m pytest tests/test_informe_pruebas.py -q -p no:cacheprovider`.

### Ítem 5.6 · Corrección de errores y repetición de las pruebas
- **(a) Archivo principal:** `docs/validacion/registro_defectos.md` (Markdown). Demuestra: 25 defectos con fecha, dónde se detectaron, causa, corrección con su commit y prueba de regresión, y la verificación de que la prueba falla sin la corrección. **No demuestra:** que el registro sea exhaustivo antes del 2026-10-15.
- **(b) Apoyo:**
  - `docs/evidencias/orquestacion/EV-036_regresiones_sin_correccion.txt` (nueve reintroducciones en una copia temporal: fallan sin la corrección y pasan con ella) y `docs/evidencias/usuarios/EV-065_regresiones_def015_def016.txt` (dos más, DEF-015 y DEF-016) y `docs/evidencias/modo_completo/EV-104_regresiones_def017_a_def021.txt` (cinco más, DEF-017 a DEF-021).
  - `docs/evidencias/orquestacion/EV-035_estabilidad_pipeline.txt` y `EV-042_fallo_inducido_y_recuperacion.txt` (DEF-011 y DEF-013).
  - `scripts/validacion/verificar_regresiones.py`.
  - `docs/evidencias/orquestacion/EV-050_pruebas_clon.txt` (repetición de todas las pruebas en un clon limpio, en su momento) y EV-072 (en su momento pasaron 822 pruebas en un entorno nuevo con Python 3.13, EV-062).
- **(c) Texto sugerido:** «Registro de 25 defectos corregidos, cada uno con su prueba de regresión que falla sin la corrección y pasa con ella, y repetición de todas las pruebas: `docs/validacion/registro_defectos.md` y `docs/evidencias/orquestacion/EV-036_regresiones_sin_correccion.txt`.»
- **(d) Captura opcional:** PowerShell con `.\.venv\Scripts\python.exe scripts\validacion\verificar_regresiones.py`, con cada defecto «falla sin la corrección». Nombre: `captura_5.6_regresiones.png`.
- **(e) Validar:** `.\.venv\Scripts\python.exe scripts\validacion\verificar_regresiones.py` (código de salida 0) y `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider`.

---

## Documentación y demostración, y Cierre y paquete · Ítems 6.5 y 7.1 a 7.5 (con su estado real)
Estas seis fichas se escribieron en la auditoría intermedia. Ninguna de las seis está en «Cumple»: cada una dice qué hay y qué falta. La tabla ítem → requisito → archivos → pruebas → evidencias → comando de los 30 ítems está en [trazabilidad.md](trazabilidad.md) y se comprueba con `python scripts/validar_checklist.py --item N`.

### Ítem 6.5 · Retroalimentación y verificación de los ajustes (Pendiente por un hecho externo)
- **(a) Archivo principal:** `docs/usuarios/trazabilidad_de_cambios.md` (Markdown). Demuestra: la tabla fricción → cambio → commit → captura antes y después → prueba está llena con los 8 ajustes de la iteración técnica (D87 a D90). **No demuestra:** que alguien haya dado retroalimentación ni que los ajustes se hayan verificado con personas: salen de una evaluación heurística interna. Estado: Pendiente (hecho externo).
- **(b) Apoyo:** `tests/test_usuarios_estructura.py` (el estado no marca como cumplido lo que depende de sesiones reales), `tests/test_panel_ajustes.py` (cada ajuste falla si el defecto vuelve) y EV-073 a EV-082 (capturas y mediciones antes y después de los ajustes; son iteración técnica y no cuentan para este ítem).
- **(c) Texto sugerido:** «Los ajustes al panel salen de una evaluación heurística interna; la retroalimentación de personas usuarias y la verificación posterior están pendientes de las sesiones reales: `docs/usuarios/trazabilidad_de_cambios.md`.»
- **(d) Captura opcional:** ninguna: no hay sesiones que capturar.
- **(e) Validar:** `.\.venv\Scripts\python.exe scripts\validar_checklist.py --item 6.5`.

### Ítem 7.1 · Documentación completa y código ejecutable (En curso)
- **(a) Archivo principal:** `docs/instalacion/README.md` (guía con modo mínimo y modo completo) y `README.md`. Demuestra: el proyecto se instala y pasa su suite en un clon y en el zip descomprimido, en una carpeta sin ninguna otra carpeta del equipo y con una ruta con espacios y tildes; `requirements.txt` tiene todas las versiones exactas; el zip se arma por lista de inclusión sin `.env`. **No demuestra:** la publicación del repositorio en GitHub, el paquete final de Cierre y paquete ni que las otras dos personas del grupo lo hayan probado en sus equipos. Estado: En curso.
- **(b) Apoyo:** EV-049, EV-062, EV-083, EV-084, EV-087, EV-089 y EV-090 (instalación desde cero, suite sin variables de UTF-8, Airflow desde el zip y los experimentos de independencia); EV-001, EV-002, EV-003 y EV-006 (línea base protegida y estado del entorno); `tests/test_dist.py`, `tests/test_empaquetado_y_revision.py`, `tests/test_independencia_del_repositorio.py`, `tests/test_portabilidad.py`, `tests/test_preparar_entorno.py`, `tests/test_requisitos.py` y `tests/test_servicios_estructura.py`.
- **(c) Texto sugerido:** «Código y documentación ejecutables desde un clon limpio y desde el zip, con guía de instalación; falta publicar el repositorio y que las otras dos personas lo prueben: `docs/instalacion/README.md`.»
- **(d) Captura opcional:** ninguna.
- **(e) Validar:** `.\.venv\Scripts\python.exe scripts\validar_checklist.py --item 7.1 --ejecutar`.

### Ítem 7.2 · README con problema, funcionalidades, instalación, arquitectura y ejecución (En curso)
- **(a) Archivo principal:** `README.md` (escrito a mano desde D105; el análisis está en `docs/gold/resultados.md`). Demuestra: descripción y alcance (sección 1), arquitectura con los dos diagramas aportados (4), requisitos y primera vez (7), ejecución (8), datos y contratos (9) y pruebas (10), con las cifras leídas de los archivos de salida. **No demuestra:** que sirva en otro equipo, que sus tiempos valgan en otra máquina ni que exista el documento de arquitectura completo (7.3), que el README todavía no enlaza. Estado: En curso.
- **(b) Apoyo:** `tests/test_readme_cifras.py` (las cifras del README coinciden con lo medido), `tests/test_resultados_cifras.py` (las del análisis coinciden con las salidas), `tests/test_readme_guardiana.py` (forma y redacción del README) y `tests/test_estrategia.py::test_ningun_estado_supera_su_evidencia` (el ítem no puede pasar a «Cumple» sin el diagrama y la sección).
- **(c) Texto sugerido:** «README con descripción, arquitectura con diagrama, primera vez, instalación y ejecución; falta enlazar el documento de arquitectura completo (7.3): `README.md`.»
- **(d) Captura opcional:** ninguna.
- **(e) Validar:** `.\.venv\Scripts\python.exe scripts\validar_checklist.py --item 7.2 --ejecutar`.

### Ítem 7.3 · Arquitectura, evidencias de pruebas y feedback del usuario (En curso)
- **(a) Archivo principal:** `docs/api/arquitectura.md` y `docs/panel/arquitectura_panel.md` (arquitectura por componente, con diagrama) y `docs/validacion/informe_pruebas.md` (evidencia de pruebas técnicas). **No demuestra:** un documento de la arquitectura del sistema completo ni el feedback recibido de personas usuarias, que depende de sesiones reales. Estado: En curso.
- **(b) Apoyo:** `docs/orquestacion/guia_de_implementacion.md`, `tests/test_informe_pruebas.py` y `tests/test_matriz_casos.py`.
- **(c) Texto sugerido:** «Arquitectura documentada por componente y evidencias de pruebas técnicas; falta el documento del sistema completo y el feedback de personas usuarias: `docs/api/arquitectura.md`.»
- **(d) Captura opcional:** ninguna.
- **(e) Validar:** `.\.venv\Scripts\python.exe scripts\validar_checklist.py --item 7.3 --ejecutar`.

### Ítem 7.4 · Cambios e iteraciones tras las sesiones con usuarios (Pendiente por un hecho externo)
- **(a) Archivo principal:** `docs/usuarios/trazabilidad_de_cambios.md`. Demuestra: la estructura para registrar cada cambio con su commit y su verificación. **No demuestra:** iteraciones tras sesiones con personas: no hubo sesiones; los cambios registrados son de la evaluación heurística interna. Estado: Pendiente (hecho externo).
- **(b) Apoyo:** `docs/retroalimentacion/registro_de_cambios.md` (cambios atendidos de la retroalimentación recibida, que no es una sesión con usuarios) y `tests/test_usuarios_estructura.py`.
- **(c) Texto sugerido:** «Aún no hay iteraciones tras sesiones con personas; la tabla de cambios está lista y hoy solo trae ajustes de una evaluación heurística interna: `docs/usuarios/trazabilidad_de_cambios.md`.»
- **(d) Captura opcional:** ninguna.
- **(e) Validar:** `.\.venv\Scripts\python.exe scripts\validar_checklist.py --item 7.4`.

### Ítem 7.5 · Demostración de extremo a extremo (No iniciado)
- **(a) Archivo principal:** ninguno: en el repositorio no existe un guion de demostración ni un ensayo. Estado: No iniciado.
- **(b) Apoyo:** `tests/test_estrategia.py::test_ningun_estado_supera_su_evidencia` impide subir el estado sin que aparezca un guion de demostración en `docs/`.
- **(c) Texto sugerido:** «La demostración de extremo a extremo todavía no se ha preparado.»
- **(d) Captura opcional:** ninguna.
- **(e) Validar:** `.\.venv\Scripts\python.exe scripts\validar_checklist.py --item 7.5` (muestra que no hay archivos).

## Cómo se produjeron las evidencias de la capa de servicio
`scripts/evidencias/evidencias_api.py` clona el commit a una carpeta temporal fuera del repositorio, ejecuta ahí las pruebas, el servicio, el navegador sin ventana, el escáner y el entorno nuevo, y guarda las salidas **saneadas** (sin rutas de usuario, usuario ni equipo: se sustituyen por `<REPO>`, `<CLON>`, `<TEMP>`, `<VENV>`, `<USUARIO>` y `<EQUIPO>`) en `docs/evidencias/api/`. `scripts/evidencias/registrar_manifiesto.py` calcula el sha256 de cada archivo y lo registra en el manifiesto. Una prueba (`tests/test_evidencias.py`) verifica que ninguna evidencia guardada lleva datos del equipo.

## Componentes en construcción
Documentación y demostración y Cierre y paquete siguen en construcción; sus fichas se actualizan con la misma estructura cuando cambie el estado de un ítem.
