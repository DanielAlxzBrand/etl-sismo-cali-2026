# Gestión de credenciales, claves de API y tokens

**Fecha:** 2026-11-12 · **Ítem del checklist:** 2.3 «Aseguramos la gestión segura de credenciales, claves de API y tokens de acceso.» · **Alcance:** qué credenciales necesita hoy el proyecto, dónde viven, qué nunca se versiona, cómo lo comprobamos y qué hacemos si algo se filtra.

**Etiquetas de evidencia:** [Evidencia en el repo: ruta] · [Fuente externa: URL y fecha de consulta] · [Criterio aplicado: descripción] · [Hipótesis de diseño: criterio y experimento, no ejecutado].

## 1. Qué credenciales requiere hoy el proyecto
- **Ninguna es obligatoria.** Las tres fuentes usadas (capa ArcGIS, CSV de estrato y polígonos WFS) se consultan sin token ni cuenta. [Evidencia en el repo: `docs/bronze/catalogo_fuentes_metadatos.md`, campo «Autenticación» de cada fuente]
- **Única variable que el código lee:** `HTTP_USER_AGENT` (opcional; si falta se usa un User-Agent genérico). No es un secreto, pero se trata como configuración local. [Evidencia en el repo: `src/common.py`, función `user_agent`; `.env.example`]
- El archivo `.env` local existe y está vacío (0 bytes). [Evidencia en el repo: `docs/proyecto/entorno.md`]
- **Sobre `SOCRATA_APP_TOKEN`:** el ejemplo anterior de `.env.example` declaraba ese nombre, pero ningún código lo lee (la capa se consulta directamente por ArcGIS, no por Socrata). Lo retiramos para que el ejemplo solo prometa lo que el código usa (decisión D34). [Evidencia en el repo: `docs/DECISIONES.md`]

## 2. Variables previstas (no usadas todavía)
| variable | fase | para qué | estado |
|---|---|---|---|
| `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE` | F3 | conectar con MySQL 8.0 local | **prevista, no usada todavía** |
| claves propias de Airflow (clave Fernet, secreto JWT y contraseña del administrador; nombres que F4 confirmará) | F4 | operar Airflow en Docker | **prevista, no usada todavía** |

Reglas para ellas: se agregan a `.env.example` (solo el nombre, sin valor) **en la fase en que el código las lea**; los valores los genera y guarda el equipo en su `.env`; la contraseña de MySQL nunca se pide por chat ni se escribe en un documento. No reutilizamos ninguna credencial del material de clase de Airflow. [Criterio aplicado: decisiones D19 y D21]

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
- **Rotación:** cada credencial se cambia al terminar la Entrega 3 y cada vez que salga alguien del equipo con acceso a ella. [Hipótesis de diseño: criterio de rotación propuesto; no hay credenciales activas hoy que rotar]
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
| Escáner de secretos | busca patrones, parámetros sensibles, URLs con credenciales y cadenas de alta entropía en el árbol, el historial de git, notebooks, logs y un zip; reporta archivo, línea y patrón, nunca el valor | `scripts/escanear_secretos.py`; `tests/test_secretos.py`; `docs/evidencias/api/EV-019_escaner_secretos.txt` |
| API sin secretos | la capa de servicio no autentica ni usa tokens; está enlazada a 127.0.0.1 (D29) | `src/api/`; `docs/api/arquitectura.md` |

## 8. Cómo usar el escáner
```powershell
.\.venv\Scripts\python.exe scripts\escanear_secretos.py
.\.venv\Scripts\python.exe scripts\escanear_secretos.py --zip ruta\al\archivo.zip
```
Imprime una línea por hallazgo (`archivo:línea: patrón`) y `hallazgos: N`; termina con código distinto de cero si N > 0. `.env` queda fuera del recorrido a propósito (es donde van los secretos); su control es que git no lo versione.

**Límites del escáner:** puede dar falsos positivos (cadenas largas que no son secretos) y falsos negativos (un secreto con formato que no conocemos). Por eso es una red de seguridad y no sustituye la regla principal: los secretos nunca se escriben fuera de `.env`.

## 9. Estado del ítem 2.3 y qué se revalida
Estado: **Cumple** para lo que el proyecto usa hoy (ningún secreto obligatorio, controles activos y verificados). Se **revalida en F3** con las variables `MYSQL_*` y en **F8** con el escáner sobre el zip final de entrega.

## Cómo lo defendemos
- **Qué afirmamos:** hoy el proyecto no necesita credenciales; las que vendrán (MySQL, Airflow) tienen lugar, regla y controles definidos; el repositorio, su historial, los notebooks, los logs y un zip de prueba no contienen secretos según el escáner. [Evidencia en el repo: `docs/evidencias/api/EV-019_escaner_secretos.txt`]
- **Con qué evidencia:** `scripts/escanear_secretos.py` y sus diez pruebas (un secreto sembrado por tipo), el enmascarado del registro probado y `.env` fuera de `git ls-files`.
- **Qué NO afirmamos:** que el escáner encuentre todos los secretos posibles ni que no exista una filtración en servicios de terceros; no revisamos las cuentas de los integrantes.
- **Pregunta más probable:** «¿Y si filtran la contraseña de MySQL?» **Respuesta:** la revocamos primero (cambiamos la contraseña del usuario en MySQL), la guardamos nueva solo en `.env`, ejecutamos el escáner sobre árbol e historial y registramos el incidente; no reescribimos el historial sin decisión del equipo.
