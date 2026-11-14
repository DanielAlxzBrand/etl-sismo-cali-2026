# Gestión de credenciales, claves de API y tokens

**Fecha:** 2026-11-13 (actualizado con la orquestación; versión inicial 2026-11-12) · **Ítem del checklist:** 2.3 «Aseguramos la gestión segura de credenciales, claves de API y tokens de acceso.» · **Alcance:** qué credenciales necesita hoy el proyecto, dónde viven, qué nunca se versiona, cómo lo comprobamos y qué hacemos si algo se filtra.

**Etiquetas de evidencia:** [Evidencia en el repo: ruta] · [Fuente externa: URL y fecha de consulta] · [Criterio aplicado: descripción] · [Hipótesis de diseño: criterio y experimento, no ejecutado].

## 1. Qué credenciales requiere hoy el proyecto
- **Las fuentes no exigen credenciales.** Las tres fuentes usadas (capa ArcGIS, CSV de estrato y polígonos WFS) se consultan sin token ni cuenta. La única credencial del proyecto es la del usuario de MySQL de la carga relacional (sección 2). [Evidencia en el repo: `docs/bronze/catalogo_fuentes_metadatos.md`, campo «Autenticación» de cada fuente]
- **Variables que el código lee:** `HTTP_USER_AGENT` (opcional; si falta se usa un User-Agent genérico; no es un secreto, pero se trata como configuración local) y las `MYSQL_*` de la carga relacional (la contraseña sí es un secreto). [Evidencia en el repo: `src/common.py`, función `user_agent`; `.env.example`]
- El archivo `.env` es local y no se versiona. Antes de la carga relacional estaba vacío; ahora lo completa `scripts/mysql/configurar_mysql.py` con las variables `MYSQL_*`. [Evidencia en el repo: `docs/proyecto/entorno.md`, `docs/almacenamiento/mysql_configuracion.md`]
- **Sobre `SOCRATA_APP_TOKEN`:** el ejemplo anterior de `.env.example` declaraba ese nombre, pero ningún código lo lee (la capa se consulta directamente por ArcGIS, no por Socrata). Lo retiramos para que el ejemplo solo prometa lo que el código usa (decisión D34). [Evidencia en el repo: `docs/DECISIONES.md`]

## 2. Variables de MySQL y variables previstas
| variable | componente | para qué | estado |
|---|---|---|---|
| `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`, `MYSQL_DATABASE_PRUEBA` | Carga relacional | conectar con MySQL 8.0 local (base real y base de prueba); solo `MYSQL_PASSWORD` es secreta | **en uso**: las lee `src/load/conexion.py`; sus nombres están en `.env.example` |
| `MYSQL_DOCKER_USER`, `MYSQL_DOCKER_PASSWORD`, `MYSQL_DOCKER_ORIGEN` | Orquestación | usuario de MySQL con permisos mínimos para la tarea de carga del DAG en Docker; solo la contraseña es secreta | **en uso**: las lee la tarea `cargar_datawarehouse` del DAG desde el `.env` montado en solo lectura; nombres en `.env.example` |
| `_AIRFLOW_WWW_USER_PASSWORD` y `AIRFLOW_UID` | Orquestación | contraseña de la interfaz de Airflow y usuario del contenedor; solo la contraseña es secreta | **en uso**, únicamente en `airflow-medallon/.env` (fuera del repositorio); nombres en `orquestacion/airflow-env.nombres.txt` |
| clave Fernet y secreto JWT de Airflow | Orquestación | cifrar conexiones y firmar tokens de la API interna | **no usadas con valor propio**: el compose oficial deja la Fernet vacía y trae un secreto JWT de ejemplo; el riesgo se mitiga publicando los puertos solo en 127.0.0.1 y no guardando conexiones ni variables en Airflow (hallazgos H-17 y H-18 de `docs/orquestacion/diferencias_con_la_guia.md`) |

Reglas para las nuevas variables: se agregan a `.env.example` (solo el nombre, sin valor) **cuando el código las lea**; los valores los genera y guarda el equipo en su `.env`; la contraseña de MySQL nunca se pide por chat ni se escribe en un documento. No reutilizamos ninguna credencial del material de clase de Airflow. [Criterio aplicado: decisiones D19 y D21]

### Credenciales de MySQL: cómo se crean y se usan
- **Quién las crea:** `scripts/mysql/configurar_mysql.py`, que ejecuta una persona del equipo en su terminal. Pide la contraseña del administrador con `getpass` (sin eco; nunca por argumento, variable de entorno ni archivo; no se guarda ni se registra) y crea el usuario `sismo_etl`@`localhost` con una contraseña aleatoria de 32 caracteres generada con `secrets`. [Evidencia en el repo: `scripts/mysql/configurar_mysql.py`; `tests/test_configurar_mysql.py`]
- **Dónde queda:** solo en `.env`, que se escribe de forma atómica y **después** de comprobar que el usuario nuevo se conecta y tiene los privilegios esperados. El script imprime nombres de variables, nunca valores.
- **Cómo se pasa a SQL:** la contraseña viaja como parámetro de la sentencia (`CREATE USER ... IDENTIFIED BY %s`), nunca dentro del texto SQL.
- **Privilegios:** solo las dos bases del proyecto, sin privilegios globales ni `GRANT OPTION`, y sin usuarios con host `'%'` (D46).
- **Rotación:** `configurar_mysql.py --rotar` cambia la contraseña con `ALTER USER`, verifica la conexión y actualiza `.env`.
- **Quién no la ve:** quienes colaboran con el código del proyecto nunca reciben ni leen la contraseña de administrador ni la del usuario; la genera y la guarda el propio script.

### Credenciales del DAG de Airflow (usuario de MySQL para Docker)
- **Variables:** `MYSQL_DOCKER_USER`, `MYSQL_DOCKER_PASSWORD` y `MYSQL_DOCKER_ORIGEN` (nombres en `.env.example`, sin valores). Las crea `scripts/mysql/configurar_mysql.py --usuario-docker --origen <PATRÓN>`: usuario `sismo_airflow` con permisos solo sobre `sismo_cali` (`SELECT`, `INSERT`, `CREATE`, `INDEX`, `REFERENCES`), sin `GRANT OPTION`, sin privilegios globales y sin origen `%` (D60). La contraseña aleatoria de 32 caracteres solo se escribe en `.env` después de comprobar los permisos.
- **Uso:** la tarea de carga del DAG lee esas variables en memoria del `.env` del proyecto (montado en solo lectura) y las pasa por `os.environ` de la tarea; nunca se copian a la copia de trabajo, a la imagen, al compose, a `airflow-medallon/.env` ni a los registros.
- **Origen del usuario:** `sismo_airflow`@`localhost`. Docker Desktop entrega al servidor MySQL del anfitrión la conexión desde el contenedor a través del bucle local, de modo que MySQL la ve como `localhost` y no con la IP de la red de Docker (evidencia [EV-040](../evidencias/orquestacion/EV-040_origen_mysql_desde_docker.txt); decisión D65). El usuario sigue sin poder entrar desde ningún otro origen y nunca se creó con `%`.
- **Contraseña de la interfaz de Airflow:** no se dejó la de la guía ni la del compose; se generó con `secrets` (variable `_AIRFLOW_WWW_USER_PASSWORD`) y vive solo en `airflow-medallon/.env`, que no se versiona ni se copia a ninguna imagen. La interfaz solo escucha en 127.0.0.1:8080.
- **Lo que el equipo no vio:** ni la contraseña de administrador de MySQL (la teclea la persona en `getpass`), ni la del usuario de Docker, ni la de la interfaz; los scripts imprimen nombres, nunca valores.
- **Límite de la protección (D67):** el origen `localhost` no acota por sí solo quién puede conectarse. La protección real de `sismo_airflow` es el mínimo privilegio (solo `sismo_cali`, sin `UPDATE`, `DELETE` ni `ALTER`) más la contraseña aleatoria; cualquier proceso local que tenga esa contraseña puede conectarse, igual que con `sismo_etl`.
- **Rotación y revocación:** `configurar_mysql.py --usuario-docker --origen <PATRÓN> --rotar` cambia la contraseña con `ALTER USER`; para revocar, el administrador ejecuta `DROP USER 'sismo_airflow'@'<PATRÓN>';` (documentado, no ejecutado por ningún script).
- **Comprobación:** `escanear_secretos.py --canario-env --env-extra ..\airflow-medallon\.env` busca también los valores sensibles del `.env` de Airflow en el árbol, el historial y un zip sin imprimirlos; `--solo-canario` permite revisar una carpeta ajena (como `airflow-medallon`) sin los patrones de contraseñas por defecto del compose oficial.

## 3. Dónde se guardan y qué nunca va al repositorio
- **Se guardan en:** el archivo `.env` de cada integrante, fuera de git (`.gitignore` lo excluye). En el repositorio solo está `.env.example`, con **nombres** de variables y sin valores.
- **Nunca van a:** `config/config.yaml` (solo parámetros no secretos), notebooks (ni en celdas ni en salidas), logs, mensajes de commit, capturas de pantalla ni URLs que lleven el token en la consulta. Las respuestas de la API que mostramos nunca incluyen secretos: no existen en la capa de servicio.
- **Manifiesto de Bronze:** el campo `params` «nunca incluye tokens» (regla de `save_bronze`). [Evidencia en el repo: `src/common.py`]

## 4. Si una fuente exige un token
1. Pedirlo con una cuenta propia del equipo (no la de otra persona).
2. Guardarlo en `.env` con un nombre explícito (por ejemplo `FUENTE_X_TOKEN`) y agregar solo el nombre a `.env.example`.
3. Leerlo con `os.getenv` en el código; nunca ponerlo en la URL de `config.yaml` ni en `params` del manifiesto.
4. Enviarlo en una cabecera, no en la URL, para que no quede en registros.
5. Ejecutar `python scripts/escanear_secretos.py` antes de guardar cambios.

## 5. Rotación y revocación
- **Rotación:** cada credencial se cambia al terminar el proyecto y cada vez que salga alguien del equipo con acceso a ella. [Hipótesis de diseño: criterio de rotación propuesto; no hay credenciales activas hoy que rotar]
- **Revocación:** quien detecte una filtración revoca primero la credencial en el servicio que la emitió.

## 6. Si se filtra un secreto
1. **Revocar primero** la credencial en el servicio emisor (el secreto filtrado ya no es confiable aunque se borre).
2. Generar una nueva y guardarla solo en `.env`.
3. Eliminar el secreto de los archivos actuales y ejecutar el escáner (árbol e historial).
4. **No reescribir el historial de git sin una decisión del equipo:** se registra en `docs/DECISIONES.md` quién decide y por qué.
5. Anotar el incidente (qué, cuándo, qué se revocó) sin escribir el valor.

## 7. Controles técnicos existentes y su evidencia
| control | qué hace | evidencia |
|---|---|---|
| `.gitignore` | excluye `.env`, `logs/*.log`, entornos virtuales y `dist/` | `.gitignore`; `tests/test_secretos.py::test_env_no_esta_versionado` |
| `.env.example` | solo nombres, sin valores; solo variables que el código lee | `.env.example`; D34 |
| Enmascarado del registro | reemplaza por `***` cabeceras de autorización, pares `clave=valor` sensibles y cualquier valor de `.env` | `src/logger.py` (`EnmascararSecretos`); `tests/test_logger.py`; `tests/test_secretos.py::test_el_registro_enmascara_un_token_de_prueba` |
| `make_dist.py` | excluye `.env`, entornos virtuales, cachés y `dist/` del zip | `scripts/make_dist.py`; `tests/test_secretos.py::test_make_dist_excluye_env` |
| `.gitattributes` | fija los bytes de `data/` y los saltos de línea; **no es un control de secretos**: evita que el contenido de datos cambie sin que nos demos cuenta | `.gitattributes`; D12 |
| Comprobación canario | `escanear_secretos.py --canario-env` toma los valores sensibles de `.env` como canarios y los busca en el árbol (incluidos `data/bronze`, registros y evidencias), el historial de git y el zip, e informa archivo y variable, nunca el valor; además avisa si `.env` no está ignorado o está versionado | `scripts/escanear_secretos.py`; `tests/test_configurar_mysql.py` (contraseña sembrada en árbol, historial y zip) |
| Canario con las credenciales de la orquestación | `evidencia_canario_orquestacion.py` busca las tres contraseñas (MySQL, usuario de Docker e interfaz de Airflow) en el árbol, los registros, el historial (67 commits), `airflow-medallon` (109 archivos, 102 registros de tareas, compose y Dockerfile), la imagen (`docker image inspect` y `docker history`) y un zip armado en una carpeta temporal: 0 hallazgos; `airflow-medallon/.env` solo trae variables de Airflow | `scripts/evidencias/evidencia_canario_orquestacion.py`; [EV-049](../evidencias/orquestacion/EV-049_canario_orquestacion.txt); `tests/test_canario_extra.py` |
| Patrón de contraseña literal | el escáner reconoce `MYSQL_PASSWORD=<literal>` (los marcadores como `<definir en .env>` no cuentan) | `scripts/escanear_secretos.py`; `tests/test_configurar_mysql.py` |
| Escáner de secretos | busca patrones, parámetros sensibles, URLs con credenciales y cadenas de alta entropía en el árbol, el historial de git, notebooks, logs y un zip; reporta archivo, línea y patrón, nunca el valor | `scripts/escanear_secretos.py`; `tests/test_secretos.py`; `docs/evidencias/api/EV-019_escaner_secretos.txt` |
| API sin secretos | la capa de servicio no autentica ni usa tokens; está enlazada a 127.0.0.1 (D29) | `src/api/`; `docs/api/arquitectura.md` |

## 8. Cómo usar el escáner
```powershell
.\.venv\Scripts\python.exe scripts\escanear_secretos.py
.\.venv\Scripts\python.exe scripts\escanear_secretos.py --zip ruta\al\archivo.zip
.\.venv\Scripts\python.exe scripts\escanear_secretos.py --canario-env --zip ruta\al\archivo.zip
```
Imprime una línea por hallazgo (`archivo:línea: patrón`) y `hallazgos: N`; termina con código distinto de cero si N > 0. `.env` queda fuera del recorrido a propósito (es donde van los secretos); su control es que git no lo versione.

**Límites del escáner:** puede dar falsos positivos (cadenas largas que no son secretos) y falsos negativos (un secreto con formato que no conocemos). Por eso es una red de seguridad y no sustituye la regla principal: los secretos nunca se escriben fuera de `.env`.

## 9. Estado del ítem 2.3 y qué se revalida
Estado: **Cumple**. Con las variables `MYSQL_*` quedan implementados y probados el alta segura del usuario, el enmascarado del registro y la comprobación canario; la comprobación con la contraseña real dio 0 hallazgos en el árbol, los registros, los 54 commits del historial y un zip de prueba (`docs/evidencias/almacenamiento/EV-033_canario_credenciales.txt`). Se **revalida con el escáner sobre el zip final** (Cierre y paquete).

## Alcance y límites
- **Qué afirmamos:** las fuentes no necesitan credenciales; la de MySQL se crea y se guarda con controles que probamos y las que vendrán (Airflow) tienen lugar, regla y controles definidos; el repositorio, su historial, los notebooks, los logs y un zip de prueba no contienen secretos según el escáner. [Evidencia en el repo: `docs/evidencias/api/EV-019_escaner_secretos.txt`]
- **Con qué evidencia:** `scripts/escanear_secretos.py` y sus pruebas (un secreto sembrado por tipo y la contraseña sembrada en árbol, historial y zip), el enmascarado del registro probado y `.env` fuera de `git ls-files`.
- **Qué NO afirmamos:** que el escáner encuentre todos los secretos posibles ni que no exista una filtración en servicios de terceros; no revisamos las cuentas de los integrantes.

## Preguntas frecuentes
- **«¿Y si filtran la contraseña de MySQL?»** La revocamos primero (cambiamos la contraseña del usuario en MySQL), la guardamos nueva solo en `.env`, ejecutamos el escáner sobre árbol e historial y registramos el incidente; no reescribimos el historial sin decisión del equipo.
