# Decisiones técnicas del proyecto

**Fecha:** 2026-11-12 · **Alcance:** decisiones que condicionan los componentes API, fuentes y credenciales, Carga relacional, Pruebas y orquestación, Panel, Usuarios, UX y finanzas, Documentación y demostración y Cierre y paquete del checklist de Data Thinking. Cada una tiene opción recomendada, respaldo, criterios y qué hacemos si la recomendada resulta inviable. Los registros formales están en `docs/DECISIONES.md` (D17 en adelante). La fecha límite y la rúbrica del proyecto no constan; no las suponemos.

**Etiquetas de evidencia:** [Evidencia en el repo: ruta] · [Fuente externa: URL y fecha de consulta] · [Criterio aplicado: descripción] · [Hipótesis de diseño: criterio y experimento de validación propuesto, no ejecutado].

**Criterios comunes:** compatibilidad con Windows y Python 3.13, dependencias mínimas, reproducibilidad en una máquina limpia, tiempo, riesgo de romper el pipeline, valor frente al checklist.

## Resumen
| # | decisión | recomendada | respaldo | componente |
|---|---|---|---|---|
| a | API | FastAPI de solo lectura sobre Gold | servidor con la biblioteca estándar | API, fuentes y credenciales |
| b | Almacenamiento | mantener SQLite y agregar MySQL 8.0 local (SQL explícito, PyMySQL) | almacén relacional en un archivo SQLite con matiz | Carga relacional |
| c | Dashboard | Streamlit sobre la API | página HTML estática con Plotly | Panel |
| d | Orquestación | Airflow 3.x con Docker Compose (variante ligera, ejecutor local) sobre WSL2 | Docker Engine dentro de WSL2; luego pip con restricciones; luego validación estática | Pruebas y orquestación |
| e | MLOps y LLMOps | prácticas equivalentes de DataOps; el resto N/A justificado | — | Pruebas y orquestación |
| f | Integración | pruebas en proceso (API, interfaz, almacén) y humo de solo lectura | pruebas contra SQLite en memoria | Panel |
| g | Línea base | rama, etiquetas, clon temporal, pruebas de huellas, `.gitattributes` | copia de respaldo de `data/` fuera del repo | todas |
| h | Dependencias por componente | API, fuentes y credenciales: fastapi, uvicorn, httpx · Carga relacional: pymysql, cryptography · Panel: streamlit | — | API, fuentes y credenciales, Carga relacional, Panel |
| i | Marco de Data Thinking | las cinco etapas de d.school, adaptadas a datos | — | Estrategia |
| j | Palabra «IA» en los documentos | permitida como concepto técnico; prohibidos los rastros de elaboración | — | todas |

---

## (a) API de solo lectura con FastAPI sobre Gold
- **Recomendada:** servicio FastAPI que lee Gold desde el almacén (SQLite o MySQL, ver b) y no tiene ningún endpoint que escriba. Endpoints previstos para API, fuentes y credenciales: `GET /health`; `GET /metadata` (fuentes, fechas de corte y de imágenes, población analizada y alcance temporal); `GET /kpis` (filtro por `kpi_id`); `GET /kpis/sensibilidad`; `GET /comunas`; `GET /construcciones` (paginado; filtros por comuna, estrato y severo estricto); `GET /calidad` (resumen de `quality_report.json`); `GET /llave/revision` (códigos con diferencias en la validación semántica). Un solo comando de arranque. La API abre la base en modo de solo lectura y una prueba comprueba que los hashes de `data/` y de la base no cambian.
- **Respaldo:** servidor con `http.server` de la biblioteca estándar y respuestas JSON; sin OpenAPI, con los mismos endpoints.
- **Por qué:** solo lectura protege la línea base; FastAPI genera el esquema OpenAPI como evidencia; se prueba sin red con el cliente de pruebas de FastAPI. FastAPI 0.116.2, Uvicorn 0.35.0 y httpx 0.28.1 ya corren con Python 3.13.0 en este equipo (en el Python global). [Evidencia en el repo: `docs/proyecto/entorno.md`]
- **Si resulta inviable** (incompatibilidad o error de instalación): el respaldo, y el ítem 2.1 queda «Cumple con matiz» declarando que no hay esquema OpenAPI.

## (b) Almacenamiento: SQLite y MySQL 8.0 local
- **Recomendada:** mantener `data/gold/etl_sismo.db` (SQLite, recálculo independiente con SQL) y agregar un almacén MySQL 8.0 local con **SQL explícito, sin ORM**. Conector PyMySQL con `cryptography` para la autenticación `caching_sha2_password` de MySQL 8. Modelo relacional con claves primarias y foráneas, tabla de historial de cargas, carga por lotes e idempotencia (Carga relacional). El almacén nuevo no modifica `etl_sismo.db` ni los CSV.
- **Versiones reales (consultadas el 2026-11-12 con `pip index versions` y `pip download --only-binary --python-version 3.13 --platform win_amd64`, sin instalar):** PyMySQL 1.2.4 (rueda `py3-none-any`) y cryptography 50.0.2 (rueda `cp311-abi3-win_amd64`, utilizable en Python 3.13). El servidor instalado es MySQL Server 8.0.45 con el servicio `MySQL80` en ejecución y el puerto 3306 aceptando conexiones TCP. [Evidencia en el repo: `docs/proyecto/entorno.md`; `docs/evidencias/estrategia/EV-012_fuentes_externas.txt`]
- **Credenciales:** variables de entorno `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD` y `MYSQL_DATABASE` en `.env` (en `.env.example` solo los nombres). El usuario y la base los crea el equipo ejecutando un script SQL que generará la carga relacional; las contraseñas nunca se piden por chat ni se guardan en el repositorio.
- **Respaldo:** el mismo modelo relacional en un archivo SQLite con `PRAGMA foreign_keys=ON`; el ítem 4.1 queda «Cumple con matiz» porque SQLite no figura en la lista del checklist.
- **Por qué:** sin instalaciones de servidor (MySQL ya está), cumple el checklist, integridad real y DDL versionado; el riesgo de romper el pipeline es nulo porque es una carga posterior a Gold.
- **Si resulta inviable** (sin acceso al servicio o sin cuenta): respaldo y matiz declarado. Las pruebas contra MySQL llevan un marcador y quedan fuera de la ejecución por defecto, sin pruebas saltadas.

## (c) Dashboard con Streamlit sobre la API
- **Recomendada:** Streamlit que consume solo la API (cliente HTTP propio); **la interfaz no lee la base directamente**. Vistas mínimas: resumen y alcance (recuadros temporal y de población), K1 por estrato con intervalos, K6 por comuna, sensibilidades, calidad de la llave y descarga de tablas. Pruebas sin navegador con `streamlit.testing.v1.AppTest`.
- **Respaldo:** una página HTML estática generada con Plotly a partir de las respuestas de la API.
- **Por qué:** se ejecuta por script con `pip` y un comando; Streamlit 1.58.0 ya corre aquí. **Power BI se descarta como evidencia**: no está instalado, no se puede ejecutar por script y el repositorio debe ejecutarse en una máquina limpia (si el equipo lo usa como extra, no cuenta como evidencia).
- **Si resulta inviable:** el respaldo.

## (d) Orquestación con Airflow 3.x en Windows
> **Actualización del 2026-11-13.** Esta sección conserva el plan de partida. Lo implementado sigue el artículo de Airflow acreditado en el README (sección 20) y difiere de este plan: el compose oficial con **CeleryExecutor** (Postgres y Redis; los 7,6 GB de memoria disponibles para Docker lo permitieron), un DAG `medallon_etl_sismo` con **cuatro tareas** (no cinco) y **sin reintentos** (la guía no los incluye) y los secretos de la interfaz en `airflow-medallon/.env`. Ver `docs/orquestacion/` y las decisiones D56 a D66 de `docs/DECISIONES.md`.

**Evidencia de partida.** Windows con 15,7 GB de RAM en total y **3,7 GB libres** en la revisión; hipervisor presente; WSL con versión predeterminada 2 y **sin distribución**; Docker **no instalado**. [Evidencia en el repo: `docs/proyecto/entorno.md`] El material de clase usa Docker Compose con la imagen `apache/airflow:3.3.2`, el compose oficial y un DAG de cinco tareas con cron horario; no impone un ejecutor concreto. [Criterio aplicado: resumen del laboratorio de clase, material fuera del repositorio]

**Decisión.**
- **Prerrequisito común:** WSL2. **Vía principal:** Docker Desktop (motor WSL2) con **Docker Compose** y la imagen oficial de Airflow (se parte de `apache/airflow:3.3.2`, la del laboratorio; Pruebas y orquestación confirma versión de Airflow y de Python con `airflow version`). La documentación oficial de Airflow presenta el compose como la vía de desarrollo local y declara compatibilidad con Python 3.13 desde Airflow 3.1.0. [Fuente externa: https://airflow.apache.org/docs/apache-airflow/3.3.1/howto/docker-compose/index.html y https://airflow.apache.org/docs/apache-airflow/3.1.1/start.html, consultadas el 2026-11-12] `pip index versions apache-airflow --python-version 3.13` lista 3.4.0, 3.3.2 y 3.1.x. [Evidencia en el repo: `docs/evidencias/estrategia/EV-012_fuentes_externas.txt`]
- **Variante ligera (la que adoptamos):** **ejecutor local en lugar de Celery**, sin Redis, sin worker de Celery y sin Flower; servicios: Postgres, servidor de API, programador y procesador de DAG (más el servicio de inicialización). **Razón:** la memoria libre (3,7 GB) es inferior a los 4 GB que el propio script de inicialización del compose de clase usa como mínimo, y el laboratorio no exige Celery; la rúbrica evalúa DAG, dependencias, disparador horario, validaciones, reintentos, logs e idempotencia. [Criterio aplicado: comparación del laboratorio con el entorno]
- **Licencia de Docker Desktop:** la página oficial indica que es gratuito para educación, uso personal, código abierto no comercial y pequeñas empresas (menos de 250 empleados y menos de 10 millones de dólares de ingresos); el acuerdo de licencia es el que rige, y se revisa al instalar. [Fuente externa: https://docs.docker.com/subscription-billing/desktop-license/, consultada el 2026-11-12] Es un proyecto de estudiantes de la UAO.
- **Secretos:** los del ejemplo de clase **no se reutilizan**. Las claves de Airflow (Fernet, JWT) y la contraseña del administrador se generan por el equipo y se leen de variables de entorno desde un `.env` fuera de git (en el repo solo `.env.example` con nombres).
- **Qué va en el repositorio (Pruebas y orquestación):** una carpeta llamada `orquestacion` con el compose ligero, el DAG `pipeline_sismo` (cinco tareas: verificación de Bronze de las tres fuentes en tareas independientes, Silver, Gold, carga y validación), su README y la prueba estática del DAG. Airflow **nunca** entra en `requirements.txt` ni en el `.venv`.

**Procedimiento de instalación para el equipo (PowerShell como administrador; puede pedir reinicio).**
1. `wsl --install -d Ubuntu` (crea el usuario de Linux; reiniciar si lo pide).
2. Limitar WSL2 para proteger el equipo: crear `%UserProfile%\.wslconfig` con `[wsl2]`, `memory=6GB` y `processors=4`; luego `wsl --shutdown`.
3. `winget install -e --id Docker.DockerDesktop`; abrir Docker Desktop, aceptar la licencia y activar el motor WSL2.
4. Comprobar: `docker --version` y `docker compose version`.
5. En Pruebas y orquestación: `docker compose -f orquestacion/docker-compose.yaml up airflow-init` y luego `up -d`; interfaz en `http://localhost:8080`.

**Qué se prueba en Pruebas y orquestación.** Correspondencia con las cinco pruebas del laboratorio: P1 DAG sin errores de importación y con cinco tareas (`DagBag` y `airflow dags list-import-errors`); P2 ejecución manual con Gold validado; P3 ejecución disparada por el programador con cron horario y zona `America/Bogota` documentada; P4 fallo inducido con reintento visible; P5 segunda ejecución sin duplicados y con hashes iguales. Todo sobre un clon temporal del proyecto.

**Respaldos, en orden.** (1) Docker Engine dentro de WSL2 Ubuntu, si la licencia de Docker Desktop no encajara (fuente de licencia de Docker Engine no consultada en esta ejecución). (2) Airflow con `pip` y el archivo de restricciones del release dentro de WSL2 Ubuntu (`pip install "apache-airflow==<versión>" --constraint <archivo de restricciones oficial>`; Pruebas y orquestación fija la versión). (3) Último recurso: validación estática del DAG por AST (identificador, tareas, dependencias, programación) y estado **«Cumple con matiz»** declarando que no se ejecutó `DagBag`.
**Si la recomendada resulta inviable:** pasar al respaldo siguiente y registrarlo en `docs/DECISIONES.md`.

## (e) MLOps y LLMOps
El proyecto **no entrena modelos**: usa estadística descriptiva e inferencial sobre un proxy satelital (intervalos de Wilson y de Newcombe, razón de Mantel-Haenszel, Spearman con permutación). [Evidencia en el repo: `docs/gold/KPIs.md`]
- **Prácticas equivalentes que sí aplicamos:** versionado de datos con manifiesto de Bronze y sha256 de Silver y Gold; versionado de código con ramas y etiquetas; reproducibilidad (dependencias fijadas, clon limpio y ejecución del pipeline en un clon temporal); **métricas por corrida** (filas de entrada y salida, cobertura de llave, duración por etapa, en el registro de ejecución); **cuadro de calidad como puerta de salida** (`validate`: cobertura de llave, filas de Gold, intervalos válidos, hashes) y una ficha del análisis con propósito, datos, límites y uso previsto (Pruebas y orquestación).
- **N/A justificado:** registro de modelos y métricas de rendimiento de modelos (no hay modelos) y todo LLMOps (no hay modelos de lenguaje).
- **Respaldo:** si el matiz no basta, se mantiene la ficha del análisis y se declara la parte de modelos como N/A. El ítem 5.4 queda «Cumple con matiz» por esta razón.

## (f) Pruebas de integración interfaz–lógica–almacenamiento
- **Recomendada:** (1) API ↔ almacén con el cliente de pruebas sobre una copia de solo lectura; (2) interfaz ↔ API con `AppTest` y un cliente que apunta a la API en proceso; (3) carga ↔ MySQL con el marcador `mysql`; (4) humo de extremo a extremo de solo lectura (almacén → API → interfaz) y una prueba de contrato contra el esquema OpenAPI. Ninguna escribe en `data/` y ninguna usa red externa.
- **Respaldo:** las mismas pruebas contra un SQLite en memoria cargado con Gold.
- **Por qué:** rápidas, sin servicios, verificables en un clon limpio. **Si resulta inviable:** el respaldo.

## (g) Protección de la línea base durante el desarrollo
Rama de trabajo `desarrollo` con etiquetas en los puntos seguros; `.gitattributes` que fija los bytes de `data/`; el pipeline y los notebooks se ejecutan **solo en un clon temporal** fuera del repositorio y se comparan sus sha256 con la línea base; una prueba de huellas de Bronze en las pruebas existentes. **Respaldo:** copia de `data/` fuera del repositorio con su `sha256.txt`. **Reversa:** `git restore data/`. [Evidencia en el repo: `docs/DECISIONES.md` (D12, D14, D15)]

## (h) Dependencias por componente
- API, fuentes y credenciales: `fastapi`, `uvicorn`, `httpx`. Carga relacional: `pymysql`, `cryptography`. Panel: `streamlit`. **Sin SQLAlchemy** (SQL explícito; esto sustituye lo que decía `entorno.md` para la API y la carga relacional).
- `python-docx` solo en un entorno aparte (no en el `.venv` del proyecto). Airflow, nunca en `requirements.txt` ni en el `.venv`.
- Versiones: se fijan en cada componente tras instalarlas en un entorno limpio y probarlas. Disponibles el 2026-11-12 para Python 3.13: fastapi 0.162.5, uvicorn 0.54.0, httpx 0.28.1, streamlit 1.67.0, pymysql 1.2.4, cryptography 50.0.2 (instaladas hoy en el Python global: fastapi 0.116.2, uvicorn 0.35.0, httpx 0.28.1, streamlit 1.58.0). **Si una versión nueva rompe:** se fija la última que pasa las pruebas.

## (i) Marco de Data Thinking para el ítem 1.1
En la carpeta de material de clase no hay vocabulario de Data Thinking: contiene el laboratorio de Airflow y una exposición sobre series de tiempo, sin relación. [Criterio aplicado: lectura del material de clase] Adoptamos un marco público reconocido: **las cinco etapas de Design Thinking de la d.school de Stanford** (empatizar, definir, idear, prototipar y evaluar), adaptadas a datos. [Fuente externa: https://dschool.stanford.edu/resources/design-thinking-bootleg, consultada el 2026-11-12] El mapeo del proyecto a estas etapas se hace **a posteriori**: el proyecto no se planificó con ellas.

## (j) La palabra «IA» en los documentos
La sigla (inteligencia artificial, IA, AI) puede aparecer como concepto técnico en los documentos del producto: enfoques futuros, ética y la redacción literal del checklist (D17). Las pruebas vigilan que no aparezcan nombres de herramientas, no la sigla. En cada revisión se clasifica cada coincidencia de la sigla en concepto técnico o cita literal del checklist, y se exige cero de cualquier otra.
