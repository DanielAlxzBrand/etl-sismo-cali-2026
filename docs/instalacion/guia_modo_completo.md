# Guía del modo completo: MySQL, Airflow y phpMyAdmin desde el zip

**Componente:** Servicios locales · **Requisitos:** el [modo mínimo](modo_minimo.md) funcionando, MySQL 8.0 o superior, Docker Desktop con WSL2 y la contraseña de `root` de MySQL · **Estado:** probada desde un zip nuevo el 2026-11-16 (la sección 11 la probó Daniel en su proyecto real; el reinicio de los servicios de su paso 2 no se probó) · **Evidencia:** [EV-100](../evidencias/modo_completo/EV-100_guia_seguida_desde_un_zip_nuevo.txt) y [EV-106](../evidencias/modo_completo/EV-106_resincronizar_un_env_anterior.txt)

Esta guía lleva, paso a paso, a una persona que recibe el zip hasta tener tres cosas funcionando en su equipo: las cuentas de MySQL, Airflow ejecutando el DAG de las 06:00 y phpMyAdmin mirando las siete tablas. La escribimos porque quien la probó
por primera vez, desde el zip y en otra carpeta, tropezó con seis cosas que ningún documento decía (están en la [sección 10](#10-si-algo-falla)). [modo_completo.md](modo_completo.md) sigue siendo la referencia corta de los mismos pasos; esta guía agrega para qué sirve cada comando,
lo que debe verse al ejecutarlo y qué hacer cuando no se ve.

## Cómo leer esta guía
- Todos los comandos son de **PowerShell** y cada uno está en su propio bloque. Antes de cada comando ponemos una línea **«Para qué sirve»** y, debajo, un bloque **«Qué debe verse»** con lo que imprime.
- Cada bloque «Qué debe verse» dice si es **(visto)**, porque lo copiamos de una ejecución real desde un zip nuevo en otra carpeta, o **(no probado)**. No afirmamos nada que no hayamos ejecutado. Los comandos que no imprimen nada (cambiar de carpeta, copiar al portapapeles) llevan el bloque `(sin salida)`, también marcado.
- Lo que cambia de un equipo a otro está enmascarado con marcadores fijos: `<usuario>` (el nombre de usuario de Windows), `<ruta>` (una carpeta de su equipo), `<ID>` (un identificador que genera el programa), `<PID>` (un número de proceso), `<hash>` (una huella)
  y `<contraseña>` (cualquier contraseña o clave: nunca se imprime). Debajo de cada bloque «visto» una línea **Varía:** dice qué partes cambian en su equipo (tiempos, identificadores, fechas) y otra **Tiempo:** cuánto tardó.
- **El nombre del proyecto de Compose que sale en las salidas (`airflow-zip`) es el nombre de ejemplo de esta guía.** En las capturas reales fue `airflow-zip`, `airflow-zip2` o `airflow-zip3` según la pasada, y se muestra siempre como `airflow-zip`; el suyo es el que elija con `--nombre-compose`.
- Las salidas «visto» salen de una prueba real desde un zip nuevo: [EV-100](../evidencias/modo_completo/EV-100_guia_seguida_desde_un_zip_nuevo.txt) (transcripción completa) y [EV-101](../evidencias/modo_completo/EV-101_hallazgo_4_y_df20_antes_y_despues.txt) (el hallazgo del volumen de Postgres, antes y después).
- Donde un comando trae `<ID>` o `<carpeta del proyecto>`, la guía dice **«Reemplace»** y por qué valor.
- Donde dice **código de salida** se refiere a `$LASTEXITCODE` justo después del comando; `0` significa que terminó bien.
- Esta guía trae **33 comandos**: **33** con su salida vista y **0** sin probar. Aparte hay dos salidas sin comando propio, vistas por Daniel y no por una ejecución nuestra: la de teclear `root` en el indicador y la de comprobar un `.env` anterior (sección 11).

## 0. Antes de empezar
**Requisito previo: el zip descomprimido y el entorno creado.** Descomprima el zip en una carpeta **nueva**, de ruta corta (menos de unos 120 caracteres), **fuera de cualquier repositorio de Git** y **fuera de carpetas sincronizadas con OneDrive** (la sincronización puede bloquear o demorar archivos mientras Docker los monta; es una
precaución **deducida**, no la probamos). Después cree el entorno virtual siguiendo el [modo mínimo, paso 3](modo_minimo.md#3-crear-el-entorno-e-instalar) y compruebe que quedó completo:

**Para qué sirve:** comprobar que los paquetes del entorno no tienen conflictos antes de usar los scripts.
```powershell
.\.venv\Scripts\python.exe -m pip check
```
**Qué debe verse (visto):**
```text
No broken requirements found.
```
**Varía:** nada: el mensaje es fijo.
**Tiempo:** 1,4 s.

| Hace falta | Para qué | Cómo se comprueba |
|---|---|---|
| El proyecto descomprimido fuera de cualquier repositorio de Git | si estuviera dentro de otro repositorio, la comprobación de `.env` sigue lo que diga ese repositorio y la base guardaría el commit de ese repositorio (limitación **deducida**: no la probamos) | que ninguna carpeta por encima tenga `.git` |
| El entorno virtual del proyecto (`.venv`) | todos los scripts se ejecutan con `.\.venv\Scripts\python.exe` | `pip check` (arriba) |
| MySQL 8.0 o superior con el servicio `MySQL80` activo y la contraseña de `root` | las tres cuentas del proyecto | sección 2 |
| Docker Desktop encendido, con WSL2 | Airflow y phpMyAdmin | sección 2 |
| Los puertos 3306, 8000, 8501, 8080 y 8081 libres | MySQL, API, panel, Airflow y phpMyAdmin | sección 2 |
| Memoria: Airflow en reposo ocupa unos 2 GB (1.970 MiB medidos) | con 8 GB de RAM apague el panel y el navegador antes de levantar Airflow; detalles en la [advertencia para 8 GB](README.md#4-tiempos-y-memoria-medidos) | — |

**Si falta MySQL 8 o Docker Desktop con WSL2.** El repositorio **no trae pasos para instalarlos** (solo los requisitos de arriba y, en [errores comunes](errores_comunes.md), qué hacer si Docker no responde): instálelos desde las páginas oficiales de MySQL y de Docker y vuelva a la sección 2. No probamos instalarlos.

**Orden de los pasos:** requisito previo (zip descomprimido y entorno) → revisar el `.gitignore` y el `.env` (1) → comprobar que no hay nada levantado y que el equipo está listo (2) → cuentas de MySQL (3) → carpeta de Airflow (4) → construir y levantar (5) → contraseña de la interfaz (6) → DAG (7) → phpMyAdmin (8) → apagar (9).
Los pasos 1 a 9 se hacen desde la raíz del proyecto, salvo donde decimos que hay que entrar a la carpeta de Airflow.

**Qué conserva y qué borra cada comando de apagado**
| Comando | Detiene los contenedores | Borra los contenedores | Borra los volúmenes (la base de metadatos de Airflow) |
|---|---|---|---|
| `docker compose stop` | sí | no | no |
| `docker compose down` | sí | sí | **no** |
| `docker compose down -v` | sí | sí | **sí: pierde el historial de ejecuciones y las contraseñas de esa instalación de Airflow** |

### La contraseña de `root` se teclea solo cuando el script la pide
Los tres comandos de la sección 3 abren una línea que dice **«Contraseña del administrador de MySQL (root); no se muestra al escribir:»**. Ahí, y solo ahí, se escribe la contraseña de la cuenta `root` de MySQL (no la palabra `root`) y se presiona Enter;
al teclear no aparece nada, ni siquiera asteriscos. Si se escribe `root` en el indicador de PowerShell, antes de que el script pida nada, PowerShell contesta que no conoce ese comando; no pasó nada y se vuelve a ejecutar el comando de la guía.

**Qué debe verse si se teclea `root` en el indicador de PowerShell (visto):**
```text
root : El término 'root' no se reconoce como nombre de un cmdlet, función, archivo de script o programa ejecutable. Compruebe si escribió correctamente el nombre
o, si incluyó una ruta de acceso, compruebe que dicha ruta es correcta e inténtelo de nuevo.
En línea: 1 Carácter: 1
+ root
+ ~~~~
    + CategoryInfo          : ObjectNotFound: (root:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
```
**Varía:** el idioma del mensaje. Lo vio Daniel el 2026-11-15 al seguir la guía desde un zip en otra carpeta; **no es una ejecución nuestra**.
**Tiempo:** instantáneo (no cronometrado).

### Contraseñas copiadas al portapapeles
Las secciones 6 y 8 copian una contraseña al portapapeles para pegarla en una página sin mostrarla. Apenas la pegue, **limpie el portapapeles** con el comando que sigue a cada copia (`Set-Clipboard -Value $null`).

## 1. Revisar el `.gitignore` y el `.env` (sin Git)
El zip **no trae `.git`**. No hace falta `git init`: los scripts que guardan contraseñas aceptan una carpeta sin repositorio si el `.gitignore` ignora `.env`, y lo dicen en una línea. El `.gitignore` del zip ya trae esa línea; compruebe que siga ahí.

**Para qué sirve:** comprobar que el `.gitignore` ignora `.env`, que es lo que protege las contraseñas si alguien usa Git más adelante en esta carpeta.
```powershell
Select-String -Path .gitignore -Pattern '^\.env$'
```
**Qué debe verse (visto):**
```text
<ruta>\etl_zip\.gitignore:1:.env
```
**Varía:** la ruta antes de `.gitignore` es la carpeta donde descomprimió el zip.
**Tiempo:** menos de 1 s.

## 2. Comprobar que no hay nada levantado y que el equipo está listo
Antes de seguir no debe haber contenedores de pruebas anteriores (Airflow, phpMyAdmin) ni paneles conectados a MySQL, para no confundir lo que se ve con lo de otra prueba.

**Para qué sirve:** ver qué contenedores están en marcha; con todo apagado la lista está vacía.
```powershell
docker ps
```
**Qué debe verse (visto):**
```text
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
```
**Varía:** si hay contenedores de otras pruebas, aparecen como filas debajo del encabezado.
**Tiempo:** 0,2 s.

**Para qué sirve:** diagnosticar el equipo para el modo completo (`--modo completo` suma MySQL, Docker y los puertos de Airflow y phpMyAdmin a lo que mira el modo mínimo); lo que falte trae su acción sugerida.
```powershell
py -3.13 scripts\preparar_entorno.py --modo completo
```
Debe mostrar ✓ en MySQL, Docker y los cuatro puertos. Todavía no existe el `.env` del proyecto (las cuentas se crean en la sección 3), así que esa línea sale con ✗ y el código de salida es 1: es lo esperado en este punto. Al terminar la sección 3 el diagnóstico debe quedar con todo ✓.

**Qué debe verse (visto):**
```text
✓ Python 3.13: encontrado (también hay 3.11: no se usa)
✓ Entorno virtual .venv: Python 3.13
✓ Requisitos instalados: 25 paquetes con versión exacta y `pip check` sin conflictos
✗ .env del proyecto: no existe (solo lo necesita el modo completo)
    → Copie .env.example a .env y cree las cuentas con scripts\mysql\configurar_mysql.py (ver docs/instalacion/).
✓ MySQL: responde en 127.0.0.1:3306
✓ Docker: Docker 29.9.3 y Compose 5.7.0
✓ Puerto 8000 (API): libre
✓ Puerto 8501 (panel): libre
✓ Puerto 8080 (Airflow): libre
✓ Puerto 8081 (phpMyAdmin): libre

Modo completo: falta lo marcado con ✗; siga las acciones sugeridas y vuelva a ejecutar.
```
**Varía:** las versiones de Python, Docker y Compose; y las líneas con ✗ o ✓ según el equipo. Aquí falta el `.env` del proyecto (todavía no hay cuentas), por eso hay un ✗ y el código de salida es 1: es lo esperado en este punto.
**Tiempo:** 3 s.

## 3. Las tres cuentas de MySQL
> **Estos tres comandos cambian las contraseñas de `sismo_etl`, `sismo_airflow` y `sismo_lectura`.** Si usted ya tenía esas cuentas con un `.env` de otra carpeta, ese `.env` deja de servir; vea la [sección 11](#11-si-quiere-volver-a-usar-un-env-anterior).
> Cada comando pide la contraseña de `root` **una vez** (tres comandos, tres veces). El script nunca imprime ninguna contraseña: solo los **nombres** de las variables que escribe en `.env`.

**Para qué sirve:** crear la cuenta del proyecto (`sismo_etl`) y las dos bases, y guardar su contraseña en `.env`.
```powershell
.\.venv\Scripts\python.exe scripts\mysql\configurar_mysql.py
```
**Qué debe verse (visto):**
```text
2026-11-16 11:02:49 INFO etl.__main__ esta carpeta no es un repositorio de Git (por ejemplo, viene de un zip); su .gitignore ignora .env, así que no se versionará si más adelante se usa Git
Contraseña del administrador de MySQL (root); no se muestra al escribir:
2026-11-16 11:12:48 INFO etl.__main__ servidor MySQL 8.0.45; lower_case_table_names=1; character_set_server=utf8mb4
2026-11-16 11:12:49 INFO etl.__main__ variables escritas en .env: MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE, MYSQL_DATABASE_PRUEBA
2026-11-16 11:12:49 INFO etl.__main__ Listo
```
**Varía:** la hora y la versión de MySQL; el aviso de Git y la línea de la contraseña pueden salir en otro orden. Solo se imprimen los nombres de las variables, nunca los valores.
**Tiempo:** 1 s desde que se teclea la contraseña de `root`.

**Para qué sirve:** crear la cuenta que usa el DAG de Airflow (`sismo_airflow`), con el origen `localhost` porque Docker Desktop hace llegar al MySQL del equipo las conexiones de los contenedores como si vinieran de este mismo equipo (lo medimos en [EV-040](../evidencias/orquestacion/EV-040_origen_mysql_desde_docker.txt) en una máquina con Windows; en otro sistema el origen puede ser otro).
```powershell
.\.venv\Scripts\python.exe scripts\mysql\configurar_mysql.py --usuario-docker --origen localhost
```
**Qué debe verse (visto):**
```text
2026-11-16 11:13:04 INFO etl.__main__ esta carpeta no es un repositorio de Git (por ejemplo, viene de un zip); su .gitignore ignora .env, así que no se versionará si más adelante se usa Git
Contraseña del administrador de MySQL (root); no se muestra al escribir:
2026-11-16 11:14:50 INFO etl.__main__ servidor MySQL 8.0.45; lower_case_table_names=1; character_set_server=utf8mb4
2026-11-16 11:14:50 INFO etl.__main__ variables escritas en .env: MYSQL_DOCKER_USER, MYSQL_DOCKER_PASSWORD, MYSQL_DOCKER_ORIGEN
2026-11-16 11:14:50 INFO etl.__main__ Listo
```
**Varía:** la hora y la versión de MySQL; el aviso de Git y la línea de la contraseña pueden salir en otro orden.
**Tiempo:** menos de 1 s desde que se teclea la contraseña de `root`.

**Para qué sirve:** crear la cuenta de solo lectura (`sismo_lectura`) con la que se entra a phpMyAdmin.
```powershell
.\.venv\Scripts\python.exe scripts\mysql\configurar_mysql.py --usuario-lectura
```
**Qué debe verse (visto):**
```text
2026-11-16 11:14:56 INFO etl.__main__ esta carpeta no es un repositorio de Git (por ejemplo, viene de un zip); su .gitignore ignora .env, así que no se versionará si más adelante se usa Git
Contraseña del administrador de MySQL (root); no se muestra al escribir:
2026-11-16 11:15:08 INFO etl.__main__ servidor MySQL 8.0.45; lower_case_table_names=1; character_set_server=utf8mb4
2026-11-16 11:15:08 INFO etl.__main__ variables escritas en .env: MYSQL_LECTURA_USER, MYSQL_LECTURA_PASSWORD
2026-11-16 11:15:08 INFO etl.__main__ Listo
```
**Varía:** la hora y la versión de MySQL; el aviso de Git y la línea de la contraseña pueden salir en otro orden.
**Tiempo:** menos de 1 s desde que se teclea la contraseña de `root`.

**Para qué sirve:** comprobar las credenciales de `.env` sin cambiar nada (no pide la contraseña de `root`).
```powershell
.\.venv\Scripts\python.exe scripts\mysql\configurar_mysql.py --solo-verificar
```
**Qué debe verse (visto):**
```text
2026-11-16 14:32:42 INFO etl.__main__ verificación correcta: las credenciales de .env funcionan y los privilegios son los esperados
2026-11-16 14:32:42 INFO etl.__main__ Listo
```
**Varía:** la fecha y la hora. Con credenciales que no sirven imprime en su lugar «ERROR … las credenciales de .env no son válidas» y sale con 1 (sección 11). Lo vio Daniel en su proyecto real el 2026-11-16 ([EV-106](../evidencias/modo_completo/EV-106_resincronizar_un_env_anterior.txt)); la primera versión de este bloque decía «(sin salida)» por un error de captura (DEF-023).
**Tiempo:** menos de 1 s.

## 4. La carpeta de Airflow
Airflow vive en una carpeta **hermana** del proyecto que genera `preparar_airflow.py` (no se versiona ni es un requisito previo). Primero se mira, sin escribir nada.

**Para qué sirve:** ver qué falta antes de preparar la carpeta de Airflow, sin escribir nada.
```powershell
.\.venv\Scripts\python.exe scripts\orquestacion\preparar_airflow.py --verificar
```
Antes de preparar, algunas líneas salen con ✗ (falta la carpeta, el `.env` de Airflow…): es lo esperado. Si ya existe un volumen de Postgres con el nombre de proyecto por defecto, sale además una línea con «!» que avisa del riesgo (error 4 de la sección 10).

**Qué debe verse (visto):**
```text
✓ la carpeta de Airflow es hermana del proyecto
✗ faltan las carpetas dags, logs, plugins, config
✗ distintos o ausentes: docker-compose.yaml, Dockerfile, requirements-airflow.txt
✗ el DAG de la carpeta de Airflow falta o es distinto del del proyecto
✗ al `.env` de Airflow le faltan: AIRFLOW_UID, _AIRFLOW_WWW_USER_PASSWORD, FERNET_KEY, POSTGRES_PASSWORD, AIRFLOW__API_AUTH__JWT_SECRET, PROYECTO_NOMBRE, AIRFLOW_PUERTO (use --completar)
✓ nombre de proyecto de Compose: airflow-medallon (el de la carpeta de Airflow, por defecto)
✓ `.env` del proyecto con las variables MYSQL_DOCKER_* de la carga
✓ Docker 29.9.3 y Compose 5.7.0
! ya existe el volumen airflow-medallon_postgres-db-volume (creado 2026-11-13 22:03) y se va a crear un `.env` nuevo con una contraseña de Postgres nueva: si es de otra instalación, el apiserver quedará «unhealthy» con «password authentication failed for user airflow». Para empezar con una base nueva sin tocar ese volumen, repita con --nombre-compose <otro nombre>; borrarlo (docker compose down -v) elimina esa instalación de Airflow
✓ puerto 8080 libre
```
**Varía:** la versión de Docker, la fecha del volumen de Postgres y qué líneas salen con ✗; la línea con «!» solo sale si ya existe un volumen con ese nombre de proyecto.
**Tiempo:** 1,1 s.

**Elija un nombre de proyecto de Compose.** Sin opción, Compose usa el nombre de la carpeta de Airflow (`airflow-medallon`) y, con él, el **mismo volumen de Postgres** para cualquier zip que se descomprima junto a una carpeta con ese nombre. Si ese volumen viene de otra instalación,
tiene otra contraseña y el servidor de Airflow queda «unhealthy» (sección 10, error 4). Con `--nombre-compose` el volumen es otro y no se toca el viejo. Use minúsculas, dígitos, guion y guion bajo (por ejemplo `airflow-zip`).

**Para qué sirve:** crear la carpeta de Airflow con su compose, su DAG y su `.env` (con contraseñas aleatorias que nunca se imprimen), usando un nombre de proyecto propio.
```powershell
.\.venv\Scripts\python.exe scripts\orquestacion\preparar_airflow.py --nombre-compose airflow-zip
```
**Qué debe verse (visto):**
```text
✓ Docker 29.9.3 y Compose 5.7.0
✓ carpetas creadas: dags, logs, plugins, config; copiados: docker-compose.yaml, Dockerfile, requirements-airflow.txt, dags/medallon_etl_dag.py
✓ `.env` de Airflow: creado
✓ nombre de proyecto de Compose: airflow-zip (guardado en el `.env` de Airflow)
Siguientes pasos (PowerShell):
  cd "<ruta>\airflow-medallon"
  docker compose build
  docker compose up airflow-init
  docker compose up -d
Interfaz: http://127.0.0.1:8080 · usuario: airflow · contraseña: la variable _AIRFLOW_WWW_USER_PASSWORD de airflow-medallon\.env (no se imprime aquí)
Activar y disparar el DAG:  docker compose exec airflow-scheduler airflow dags unpause medallon_etl_sismo
Para apagar:  docker compose down
```
**Varía:** la versión de Docker y la ruta del `cd` (la carpeta hermana del proyecto).
**Tiempo:** 1 s.

**Para qué sirve:** comprobar que la carpeta de Airflow quedó completa y que el `.env` del proyecto trae lo que necesita la tarea de carga.
```powershell
.\.venv\Scripts\python.exe scripts\orquestacion\preparar_airflow.py --verificar
```
Ahora todas las líneas deben salir con ✓.

**Qué debe verse (visto):**
```text
✓ la carpeta de Airflow es hermana del proyecto
✓ carpetas dags, logs, plugins y config presentes
✓ compose, Dockerfile y requisitos iguales a los del proyecto
✓ DAG igual al del proyecto (sha256)
✓ `.env` de Airflow con sus 7 variables
✓ PROYECTO_NOMBRE coincide con la carpeta del proyecto
✓ nombre de proyecto de Compose: airflow-zip (guardado en el `.env` de Airflow)
✓ `.env` del proyecto con las variables MYSQL_DOCKER_* de la carga
✓ Docker 29.9.3 y Compose 5.7.0
✓ puerto 8080 libre
```
**Varía:** la versión de Docker.
**Tiempo:** 0,9 s.

## 5. Construir y levantar
Los comandos de `docker compose` de Airflow **se ejecutan en la carpeta de Airflow**, no en la del proyecto (error 2 de la sección 10).

**Para qué sirve:** entrar a la carpeta de Airflow, donde está su compose.
```powershell
Set-Location ..\airflow-medallon
```
**Qué debe verse (visto):**
```text
(sin salida)
```

**Para qué sirve:** construir la imagen de Airflow con las dependencias del pipeline.
```powershell
docker compose build
```
**Qué debe verse (visto):**
```text
 Image airflow-zip-airflow-triggerer Building
 Image airflow-zip-airflow-worker Building
 Image airflow-zip-airflow-apiserver Building
 Image airflow-zip-airflow-init Building
 Image airflow-zip-airflow-dag-processor Building
 Image airflow-zip-airflow-scheduler Building
#1 [internal] load local bake definitions
#1 reading from stdin 4.31kB 0.1s done
#1 DONE 0.1s

#2 [airflow-worker internal] load build definition from Dockerfile
#2 transferring dockerfile: 239B 0.0s done
[… 104 líneas más (las líneas 13 a 116; la captura completa de 130 está en EV-107) …]
#18 [airflow-worker] resolving provenance for metadata file
#18 DONE 0.2s

#19 [airflow-apiserver] resolving provenance for metadata file
#19 DONE 0.3s

#20 [airflow-dag-processor] resolving provenance for metadata file
#20 DONE 0.0s
 Image airflow-zip-airflow-triggerer Built
 Image airflow-zip-airflow-worker Built
 Image airflow-zip-airflow-apiserver Built
 Image airflow-zip-airflow-dag-processor Built
 Image airflow-zip-airflow-init Built
 Image airflow-zip-airflow-scheduler Built
```
**Varía:** la lista de pasos de BuildKit y sus tiempos. Se capturó con `docker compose build` y las salidas estándar y de errores juntas (`cmd /c "… > archivo 2>&1"`), sin consola interactiva (en PowerShell se dibuja un progreso en vivo); las 6 líneas `Image … Building` del principio y las 6 `Built` del final salen por la salida de errores y antes faltaban en este bloque (DEF-025). **Enmascarado:** el nombre del proyecto de Compose se muestra como `airflow-zip`, el nombre de ejemplo de esta guía (en la captura fue `airflow-zip3`; el suyo es el que elija con `--nombre-compose`) y los resúmenes de imagen (`sha256`) como `<hash>`. **Abreviado:** se omiten las líneas 13 a 116 de la captura de 130; la captura completa está en [EV-107](../evidencias/modo_completo/EV-107_recaptura_de_airflow_init_con_2_y_1.txt).
**Tiempo:** 12,2 s con las capas en caché; desde cero será más y no se midió.

**Para qué sirve:** preparar la base de metadatos de Airflow (en Postgres) y crear el usuario de la interfaz; termina solo.
```powershell
docker compose up airflow-init
```
**Cuidado con el código de salida.** Leímos el comando de `airflow-init` en `orquestacion/docker-compose.yaml`: crea las carpetas, ejecuta `airflow version` (la imagen migra la base y crea el usuario de la interfaz porque el compose activa `_AIRFLOW_DB_MIGRATE` y `_AIRFLOW_WWW_USER_CREATE`; en la prueba el registro mostró «Performing upgrade to the metadata database»), genera la configuración y cambia el dueño de las carpetas compartidas.
El script **no usa `set -e` y su último comando es un `ls`**, así que, como en el compose oficial, un paso anterior podía fallar y el contenedor terminaba igual con `Exited (0)`: así pasó cuando la contraseña de Postgres era la equivocada (error 4). Como `set -e` no habría bastado (el propio `airflow version` sale con 0 aunque la migración falle), el compose de esta versión añade una comprobación con `/entrypoint airflow db check` (DF-20; se ejecuta siempre a través de `/entrypoint`, porque el `airflow` suelto no encuentra su módulo con el usuario `root` del contenedor): si no se conecta a la base, el contenedor `airflow-init` termina con código 1 y los demás servicios no arrancan. Aun así, **no confíe en el código de salida de `docker compose up airflow-init`: no es una señal fiable** (en nuestra prueba con el volumen viejo terminó con 0 aunque el contenedor quedó en `Exited (1)`), y **`Exited (0)` no garantiza una base correcta** (una migración que falle con la base alcanzable no se detecta). La señal fiable es `docker compose ps -a` con todo «(healthy)» y el código de salida de `docker compose up -d` (0), más abajo.

**Qué debe verse (visto):**
```text
 Network airflow-zip_default Creating
 Volume airflow-zip_postgres-db-volume Creating
 Volume airflow-zip_postgres-db-volume Creating
 Network airflow-zip_default Creating
 Volume airflow-zip_postgres-db-volume Created
 Volume airflow-zip_postgres-db-volume Created
 Network airflow-zip_default Created
 Network airflow-zip_default Created
 Container airflow-zip-postgres-1 Creating
 Container airflow-zip-redis-1 Creating
 Container airflow-zip-redis-1 Created
 Container airflow-zip-postgres-1 Created
 Container airflow-zip-airflow-init-1 Creating
 Container airflow-zip-airflow-init-1 Created
Attaching to airflow-init-1
 Container airflow-zip-postgres-1 Starting
 Container airflow-zip-redis-1 Starting
 Container airflow-zip-postgres-1 Started
 Container airflow-zip-postgres-1 Waiting
 Container airflow-zip-redis-1 Started
 Container airflow-zip-redis-1 Waiting
 Container airflow-zip-postgres-1 Healthy
 Container airflow-zip-redis-1 Healthy
 Container airflow-zip-airflow-init-1 Starting
 Container airflow-zip-airflow-init-1 Started
airflow-init-1  |
airflow-init-1  | Creating missing opt dirs if missing:
airflow-init-1  |
airflow-init-1  |
airflow-init-1  | Airflow version:
airflow-init-1  | The container is run as root user. For security, consider using a regular user account.
airflow-init-1  | 2026-11-16T19:57:48.586914Z [info     ] Performing upgrade to the metadata database [airflow.cli.commands.db_command] loc=db_command.py:134 url=<contraseña>
[… 611 líneas más …]
airflow-init-1  | drwxrwxr-x 1 airflow root 4096 Nov 16 19:57 ..
airflow-init-1  | drwxrwxr-x 1 airflow root 4096 Nov 16 17:14 dag_id=medallon_etl_sismo
airflow-init-1  | drwxrwxr-x 1 airflow root 4096 Nov 16 16:17 dag_processor
airflow-init-1  |
airflow-init-1  | /opt/airflow/plugins:
airflow-init-1  | total 4
airflow-init-1  | drwxrwxrwx 1 airflow root 4096 Nov 16 16:15 .
airflow-init-1  | drwxrwxr-x 1 airflow root 4096 Nov 16 19:57 ..

airflow-init-1 exited with code 0
```
**Varía:** las horas, los identificadores y el orden de las líneas de Airflow; el número de líneas (unas 650); la dirección de la base, que Airflow imprime con la clave ya tapada, aparece aquí como `<contraseña>`. Se capturó con `docker compose up airflow-init` y las salidas estándar y de errores juntas (`cmd /c "… > archivo 2>&1"`) sobre un volumen nuevo, por eso empieza con las líneas de progreso de Compose del primer arranque (`Network`, `Volume` y `Container` con `Creating`, `Created`, `Starting`, `Started`, `Waiting`, `Healthy`); en PowerShell interactivo Docker dibuja ese progreso en vivo. El nombre del proyecto de Compose es el que se elige con `--nombre-compose` (en la captura fue otro; aquí se muestra `airflow-zip`). Se abrevió: faltan las líneas de en medio. La captura anterior, hecha sin `2>&1`, perdía 27 líneas que Compose y el contenedor escriben por la salida de errores (24 de progreso de Compose y 3 avisos del contenedor, como «The container is run as root user…»). Debe verse «Checking the connection to the metadata database:» seguido de «Connection successful.» y ninguna línea «Read-only file system»; sobre su código de salida, vea la advertencia de arriba.
**Tiempo:** 59,6 s con un volumen de Postgres nuevo (primer arranque).

**Para qué sirve:** arrancar todos los contenedores de Airflow en segundo plano.
```powershell
docker compose up -d
```
**Qué debe verse (visto):**
```text
 Container airflow-zip-postgres-1 Running
 Container airflow-zip-redis-1 Running
 Container airflow-zip-airflow-scheduler-1 Creating
 Container airflow-zip-airflow-dag-processor-1 Creating
 Container airflow-zip-airflow-triggerer-1 Creating
 Container airflow-zip-airflow-apiserver-1 Creating
 Container airflow-zip-airflow-scheduler-1 Created
 Container airflow-zip-airflow-dag-processor-1 Created
 Container airflow-zip-airflow-triggerer-1 Created
 Container airflow-zip-airflow-apiserver-1 Created
 Container airflow-zip-airflow-worker-1 Creating
 Container airflow-zip-airflow-worker-1 Created
 Container airflow-zip-postgres-1 Waiting
 Container airflow-zip-redis-1 Waiting
 Container airflow-zip-redis-1 Healthy
 Container airflow-zip-postgres-1 Healthy
 Container airflow-zip-airflow-init-1 Starting
 Container airflow-zip-airflow-init-1 Started
 Container airflow-zip-airflow-init-1 Waiting
 Container airflow-zip-airflow-init-1 Exited
 Container airflow-zip-airflow-apiserver-1 Starting
 Container airflow-zip-airflow-dag-processor-1 Starting
 Container airflow-zip-airflow-scheduler-1 Starting
 Container airflow-zip-airflow-triggerer-1 Starting
 Container airflow-zip-airflow-apiserver-1 Started
 Container airflow-zip-airflow-apiserver-1 Waiting
 Container airflow-zip-airflow-dag-processor-1 Started
 Container airflow-zip-airflow-scheduler-1 Started
 Container airflow-zip-airflow-triggerer-1 Started
 Container airflow-zip-airflow-apiserver-1 Healthy
 Container airflow-zip-airflow-worker-1 Starting
 Container airflow-zip-airflow-worker-1 Started
```
**Varía:** el orden de las líneas. El nombre del proyecto de Compose es el que se elige con `--nombre-compose` (en la prueba fue otro; aquí se muestra `airflow-zip`, el de esta guía).
**Tiempo:** 77,3 s hasta que el servidor de Airflow quedó sano.

**Para qué sirve:** ver el estado de cada contenedor; es **la señal fiable** de que Airflow quedó sano.
```powershell
docker compose ps -a
```
Cuando todo está sano: `airflow-apiserver`, `airflow-scheduler`, `airflow-dag-processor`, `airflow-triggerer` y `airflow-worker` en «Up … (healthy)»; `airflow-init` en «Exited (0)»; `postgres` y `redis` «(healthy)». Si el servidor de Airflow sale «unhealthy», vea el error 4.

**Qué debe verse (visto):**
```text
NAME                                   IMAGE                                                                                        COMMAND                  SERVICE                 CREATED         STATUS                          PORTS
airflow-zip-airflow-apiserver-1       airflow-zip-airflow-apiserver                                                               "/usr/bin/dumb-init …"   airflow-apiserver       2 minutes ago   Up About a minute (healthy)     127.0.0.1:8080->8080/tcp
airflow-zip-airflow-dag-processor-1   airflow-zip-airflow-dag-processor                                                           "/usr/bin/dumb-init …"   airflow-dag-processor   2 minutes ago   Up About a minute (healthy)     8080/tcp
airflow-zip-airflow-init-1            airflow-zip-airflow-init                                                                    "/bin/bash -c 'if [[…"   airflow-init            3 minutes ago   Exited (0) About a minute ago
airflow-zip-airflow-scheduler-1       airflow-zip-airflow-scheduler                                                               "/usr/bin/dumb-init …"   airflow-scheduler       2 minutes ago   Up About a minute (healthy)     8080/tcp
airflow-zip-airflow-triggerer-1       airflow-zip-airflow-triggerer                                                               "/usr/bin/dumb-init …"   airflow-triggerer       2 minutes ago   Up About a minute (healthy)     8080/tcp
airflow-zip-airflow-worker-1          airflow-zip-airflow-worker                                                                  "/usr/bin/dumb-init …"   airflow-worker          2 minutes ago   Up 45 seconds (healthy)         8080/tcp
airflow-zip-postgres-1                postgres:16          "docker-entrypoint.s…"   postgres                3 minutes ago   Up 3 minutes (healthy)          5432/tcp
airflow-zip-redis-1                   redis:7.2-bookworm   "docker-entrypoint.s…"   redis                   3 minutes ago   Up 3 minutes (healthy)          6379/tcp
```
**Varía:** los nombres, los tiempos de «CREATED» y «STATUS». El nombre del proyecto de Compose es el que se elige con `--nombre-compose` (en la prueba fue otro; aquí se muestra `airflow-zip`, el de esta guía). Se hizo unos 45 s después de `docker compose up -d`.
**Tiempo:** 0,6 s.

**Para qué sirve:** comprobar que la interfaz responde (es la misma dirección que usa el compose para su prueba de salud: `/api/v2/monitor/health`).
```powershell
(Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8080/api/v2/monitor/health).StatusCode
```
**Qué debe verse (visto):**
```text
200
```
**Varía:** nada: es el código HTTP.
**Tiempo:** 0,2 s.

## 6. La interfaz de Airflow y su contraseña
La interfaz está en `http://127.0.0.1:8080` (o el puerto que eligió con `--puerto`). El usuario es **`airflow`** y la contraseña está en la variable `_AIRFLOW_WWW_USER_PASSWORD` del `.env` de la **carpeta de Airflow**. Para pegarla sin mostrarla en pantalla, cópiela al portapapeles
y péguela en el formulario con Ctrl+V.

**Para qué sirve:** copiar al portapapeles la contraseña de la interfaz sin mostrarla.
```powershell
(Select-String -Path .env -Pattern '^_AIRFLOW_WWW_USER_PASSWORD=').Line.Split('=', 2)[1] | Set-Clipboard
```
**Qué debe verse (visto):**
```text
(sin salida)
```

**Para qué sirve:** vaciar el portapapeles apenas haya pegado la contraseña.
```powershell
Set-Clipboard -Value $null
```
**Qué debe verse (visto):**
```text
(sin salida)
```

## 7. El DAG: activar, disparar y leer las cuatro tareas
El DAG se llama `medallon_etl_sismo`, corre todos los días a las 06:00 (hora de Bogotá) y tiene cuatro tareas en este orden: `validar_bronze`, `transformar_a_silver`, `integrar_a_gold` y `cargar_datawarehouse`. **Nace en pausa** (el compose lo configura así), por eso hay que activarlo.

**Para qué sirve:** comprobar que Airflow leyó el DAG sin errores de importación.
```powershell
docker compose exec airflow-scheduler airflow dags list-import-errors
```
**Qué debe verse (visto):**
```text
No data found
```
**Varía:** nada.
**Tiempo:** 4,2 s.

**Para qué sirve:** activar el DAG para que se ejecute a su hora.
```powershell
docker compose exec airflow-scheduler airflow dags unpause medallon_etl_sismo
```
**Qué debe verse (visto):**
```text
dag_id             | is_paused
===================+==========
medallon_etl_sismo | True
```
**Varía:** la tabla imprime `True` aunque el DAG queda activo (comprobado con `airflow dags list`, que mostró `False` en la columna de pausa); no se tomó por un error.
**Tiempo:** 4,1 s.

**Para qué sirve:** disparar una ejecución ahora, sin esperar a las 06:00.
```powershell
docker compose exec airflow-scheduler airflow dags trigger medallon_etl_sismo
```
**Qué debe verse (visto):**
```text
2026-11-16T16:18:51.218038Z [info     ] creating dag run               [airflow.serialization.definitions.dag] loc=dag.py:615 logical_date=None partition_key=None run_after=datetime.datetime(2026, 11, 16, 16, 18, 51, 184161, tzinfo=Timezone('UTC')) run_id=<ID>
     |                    |                        |                     |                   |          | last_scheduling_decisio |              |          |            |        |
conf | dag_id             | dag_run_id             | data_interval_start | data_interval_end | end_date | n                       | logical_date | run_type | start_date | state  | triggering_user_name
=====+====================+========================+=====================+===================+==========+=========================+==============+==========+============+========+=====================
{}   | medallon_etl_sismo | <ID> | None                | None              | None     | None                    | None         | manual   | None       | queued | airflow
     |                    |      |                     |                   |          |                         |              |          |            |        |
```
**Varía:** el identificador de la ejecución y la hora; la tabla se parte en líneas según el ancho de la consola.
**Tiempo:** 4,7 s.

**Para qué sirve:** ver el estado de las ejecuciones del DAG y su identificador.
```powershell
docker compose exec airflow-scheduler airflow dags list-runs medallon_etl_sismo
```
Repítalo cada pocos segundos hasta que la ejecución diga `success`.

**Qué debe verse (visto):**
```text
dag_id             | run_id                               | state   | run_after                        | logical_date              | start_date                       | end_date
===================+======================================+=========+==================================+===========================+==================================+=================================
medallon_etl_sismo | <ID> | success | 2026-11-16T16: |                           | 2026-11-16T16:18:52.300187+00:00 | 2026-11-16T16:19:04.878922+00:00
                   |                                      |         |                                  |                           |                                  |
medallon_etl_sismo | scheduled__2026-11-16T11:00:00+00:00 | success | 2026-11-16T11:00:00+00:00        | 2026-11-16T11:00:00+00:00 | 2026-11-16T16:18:47.483307+00:00 | 2026-11-16T16:19:04.896181+00:00
```
**Varía:** los identificadores y las horas. Salen dos ejecuciones: la que usted disparó y la programada de las 06:00 de hoy, que Airflow lanzó sola al activar el DAG. Los números de líneas dependen del ancho de la consola.
**Tiempo:** 4 s por consulta; la ejecución completa tardó unos 13 s (de `start_date` a `end_date`).

**Para qué sirve:** ver el estado de cada una de las cuatro tareas de una ejecución (el subcomando `tasks states-for-dag-run` es **deducido** de la ayuda de Airflow; se confirma en la prueba).
```powershell
docker compose exec airflow-scheduler airflow tasks states-for-dag-run medallon_etl_sismo <ID>
```
**Reemplace `<ID>`** por el identificador de la ejecución que mostró el comando anterior. Debe mostrar las cuatro tareas en `success`.

**Qué debe verse (visto):**
```text
dag_id             | logical_date | task_id              | state   | start_date                       | end_date
===================+==============+======================+=========+==================================+=================================
medallon_etl_sismo |              | validar_bronze       | success | 2026-11-16T16:18:52.778161+00:00 | 2026-11-16T16:18:55.827005+00:00
medallon_etl_sismo |              | transformar_a_silver | success | 2026-11-16T16:18:56.012170+00:00 | 2026-11-16T16:18:58.891568+00:00
medallon_etl_sismo |              | integrar_a_gold      | success | 2026-11-16T16:18:59.748331+00:00 | 2026-11-16T16:19:01.641074+00:00
medallon_etl_sismo |              | cargar_datawarehouse | success | 2026-11-16T16:19:02.550478+00:00 | 2026-11-16T16:19:04.809056+00:00
```
**Varía:** las horas de inicio y fin de cada tarea. Las cuatro deben estar en `success`.
**Tiempo:** 3,8 s; las cuatro tareas juntas duraron unos 12 s.

**En la interfaz:** entre a `http://127.0.0.1:8080`, abra el DAG `medallon_etl_sismo` en la lista, pulse el interruptor para activarlo (si no lo hizo por terminal), pulse el botón de disparar (▶) y abra la ejecución: la cuadrícula muestra las cuatro tareas en verde. Con un clic en una tarea y «Logs»
se lee su registro. La [documentación de operación](../orquestacion/operacion.md) dice que los registros no contienen contraseñas porque la tarea de carga no las imprime; esa afirmación **no está probada todavía**: la prueba desde el zip pasa el escáner de secretos, con el canario, sobre los registros de Airflow.

> **Captura opcional (aún no incluida):** la cuadrícula del DAG con las cuatro tareas en verde, recortada, sin nombre de usuario ni claves. Si existe, se agrega aquí como «imagen existente».

## 8. phpMyAdmin (solo lectura)
Desde la **raíz del proyecto** (no desde la carpeta de Airflow).

**Para qué sirve:** volver a la carpeta del proyecto, donde está el compose de phpMyAdmin.
```powershell
Set-Location ..\<carpeta del proyecto>
```
**Reemplace `<carpeta del proyecto>`** por el nombre de la carpeta donde descomprimió el zip.

**Qué debe verse (visto):**
```text
(sin salida)
```

**Para qué sirve:** levantar phpMyAdmin en el puerto 8081 (solo en este equipo).
```powershell
docker compose -f servicios\phpmyadmin\docker-compose.yaml up -d
```
**Qué debe verse (visto):**
```text
 Network sismo-phpmyadmin_default Creating
 Network sismo-phpmyadmin_default Creating
 Network sismo-phpmyadmin_default Created
 Network sismo-phpmyadmin_default Created
 Container sismo-phpmyadmin-phpmyadmin-1 Creating
 Container sismo-phpmyadmin-phpmyadmin-1 Created
 Container sismo-phpmyadmin-phpmyadmin-1 Starting
 Container sismo-phpmyadmin-phpmyadmin-1 Started
```
**Varía:** los nombres de la red y del contenedor y el orden de las líneas.
**Tiempo:** 1 s.

**Para qué sirve:** comprobar que el contenedor de phpMyAdmin está en marcha.
```powershell
docker compose -f servicios\phpmyadmin\docker-compose.yaml ps
```
**Qué debe verse (visto):**
```text
NAME                            IMAGE                                                                                      COMMAND                  SERVICE      CREATED        STATUS                  PORTS
sismo-phpmyadmin-phpmyadmin-1   phpmyadmin:5.2.3   "/docker-entrypoint.…"   phpmyadmin   1 second ago   Up Less than a second   127.0.0.1:8081->80/tcp
```
**Varía:** la columna «CREATED».
**Tiempo:** 0,5 s.

La página está en `http://127.0.0.1:8081`. El usuario es **`sismo_lectura`** y la contraseña es la variable `MYSQL_LECTURA_PASSWORD` del `.env` **del proyecto**. Cópiela sin mostrarla.

**Para qué sirve:** copiar al portapapeles la contraseña de `sismo_lectura` sin mostrarla.
```powershell
(Select-String -Path .env -Pattern '^MYSQL_LECTURA_PASSWORD=').Line.Split('=', 2)[1] | Set-Clipboard
```
**Qué debe verse (visto):**
```text
(sin salida)
```

**Para qué sirve:** vaciar el portapapeles apenas haya pegado la contraseña.
```powershell
Set-Clipboard -Value $null
```
**Qué debe verse (visto):**
```text
(sin salida)
```

Al entrar, en la base `sismo_cali` aparecen las siete tablas, con sus filas (la interfaz salió en inglés):

**Qué se ve en la página (visto):**
```text
Table              Rows   Type    Collation
barrio_estrato      346   InnoDB  utf8mb4_0900_ai_ci
comuna               27   InnoDB  utf8mb4_0900_ai_ci
construccion      5,146   InnoDB  utf8mb4_0900_ai_ci
corrida               1   InnoDB  utf8mb4_0900_ai_ci
corrida_archivo       5   InnoDB  utf8mb4_0900_ai_ci
kpi                  23   InnoDB  utf8mb4_0900_ai_ci
kpi_sensibilidad    107   InnoDB  utf8mb4_0900_ai_ci
7 tables          5,655   InnoDB  utf8mb4_0900_ai_ci
```
**Varía:** el tamaño y el idioma de la interfaz. Las filas que muestra phpMyAdmin para InnoDB son una estimación; aquí coincidieron con los conteos de [EV-085](../evidencias/servicios/EV-085_phpmyadmin_en_vivo.txt) y con los archivos de Gold.
**Tiempo:** no cronometrado (se mira en el navegador).

**Pruebe que no se puede escribir.** En la pestaña **SQL** de la base `sismo_cali`, escriba `INSERT INTO corrida (id) VALUES (999999);` y pulse «Go» («Continuar» si la interfaz está en español). MySQL debe rechazarlo con el error **#1142**; los conteos no cambian.

**Qué se ve al rechazar el `INSERT` (visto):**
```text
#1142 - INSERT command denied to user 'sismo_lectura'@'localhost' for table 'corrida'
```
**Varía:** el idioma del mensaje; el usuario y la tabla son los de esta prueba.
**Tiempo:** no cronometrado (instantáneo).

> **Captura opcional (aún no incluida):** las siete tablas de `sismo_cali` en phpMyAdmin, recortada, sin nombre de usuario ni claves. Existe una tomada en la prueba; se agrega al PDF como «imagen existente».

## 9. Apagar
Primero phpMyAdmin (desde la raíz del proyecto).

**Para qué sirve:** detener y eliminar el contenedor de phpMyAdmin.
```powershell
docker compose -f servicios\phpmyadmin\docker-compose.yaml down
```
**Qué debe verse (visto):**
```text
 Container sismo-phpmyadmin-phpmyadmin-1 Stopping
 Container sismo-phpmyadmin-phpmyadmin-1 Stopped
 Container sismo-phpmyadmin-phpmyadmin-1 Removing
 Container sismo-phpmyadmin-phpmyadmin-1 Removed
 Network sismo-phpmyadmin_default Removing
 Network sismo-phpmyadmin_default Removed
```
**Varía:** el orden de las líneas.
**Tiempo:** 2,1 s.

Después Airflow (desde la carpeta de Airflow). `down` conserva los volúmenes: al volver a levantar con `docker compose up -d` el DAG, sus ejecuciones y sus contraseñas siguen ahí.

**Para qué sirve:** volver a la carpeta de Airflow, donde está su compose.
```powershell
Set-Location ..\airflow-medallon
```
**Qué debe verse (visto):**
```text
(sin salida)
```

**Para qué sirve:** detener y eliminar los contenedores de Airflow, conservando el volumen de Postgres.
```powershell
docker compose down
```
**Qué debe verse (visto):**
```text
 Container airflow-zip-airflow-scheduler-1 Stopping
 Container airflow-zip-airflow-triggerer-1 Stopping
 Container airflow-zip-airflow-worker-1 Stopping
 Container airflow-zip-airflow-dag-processor-1 Stopping
 Container airflow-zip-airflow-scheduler-1 Stopped
 Container airflow-zip-airflow-scheduler-1 Removing
 Container airflow-zip-airflow-triggerer-1 Stopped
 Container airflow-zip-airflow-triggerer-1 Removing
 Container airflow-zip-airflow-scheduler-1 Removed
 Container airflow-zip-airflow-triggerer-1 Removed
 Container airflow-zip-airflow-worker-1 Stopped
 Container airflow-zip-airflow-worker-1 Removing
 Container airflow-zip-airflow-dag-processor-1 Stopped
 Container airflow-zip-airflow-dag-processor-1 Removing
 Container airflow-zip-airflow-worker-1 Removed
 Container airflow-zip-airflow-apiserver-1 Stopping
 Container airflow-zip-airflow-dag-processor-1 Removed
 Container airflow-zip-airflow-apiserver-1 Stopped
 Container airflow-zip-airflow-apiserver-1 Removing
 Container airflow-zip-airflow-apiserver-1 Removed
 Container airflow-zip-airflow-init-1 Stopping
 Container airflow-zip-airflow-init-1 Stopped
 Container airflow-zip-airflow-init-1 Removing
 Container airflow-zip-airflow-init-1 Removed
 Container airflow-zip-postgres-1 Stopping
 Container airflow-zip-redis-1 Stopping
 Container airflow-zip-redis-1 Stopped
 Container airflow-zip-redis-1 Removing
 Container airflow-zip-redis-1 Removed
 Container airflow-zip-postgres-1 Stopped
 Container airflow-zip-postgres-1 Removing
 Container airflow-zip-postgres-1 Removed
 Network airflow-zip_default Removing
 Network airflow-zip_default Removed
```
**Varía:** el orden de las líneas. El nombre del proyecto de Compose es el que se elige con `--nombre-compose` (en la prueba fue otro; aquí se muestra `airflow-zip`, el de esta guía).
**Tiempo:** unos 7 s.

**Para qué sirve:** confirmar que no queda ningún contenedor en marcha.
```powershell
docker ps
```
Con todo apagado, la lista debe estar vacía.

**Qué debe verse (visto):**
```text
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
```
**Varía:** las filas de contenedores de otras pruebas, si las hubiera.
**Tiempo:** 0,2 s.

> **No use `docker compose down -v` por costumbre.** Borra el volumen de Postgres, es decir, todas las ejecuciones y las contraseñas de esa instalación de Airflow, y no hay cómo recuperarlas. Úselo solo si quiere empezar esa instalación de cero, nunca sobre un volumen de otra prueba que no sea suyo.

## 10. Si algo falla
Cada fila dice cómo se supo: **(visto)** si alguien lo reprodujo en una ejecución real; **(deducido)** si lo concluimos leyendo el código y no lo hemos visto.

| N.º | Qué se ve | Causa | Qué hacer | Cómo se supo |
|---|---|---|---|---|
| 1 | `configurar_mysql.py` termina con «.env no está ignorado por git o está versionado» (antes de esta guía, también sin `.git`) | la comprobación exigía Git; el zip no trae `.git` | con la versión actual el mensaje, sin repositorio, es «esta carpeta no es un repositorio de Git … su .gitignore no deja ignorado el archivo .env»: restaure la línea `.env` del `.gitignore` (está en el zip); `git init` ya no hace falta | (visto) |
| 2 | `docker compose build` dice «no configuration file provided» | se ejecutó en la carpeta del proyecto | `Set-Location ..\airflow-medallon` y repetir | (visto) |
| 3 | `airflow-init` imprime muchas líneas «chown … Read-only file system» sobre `.venv` y termina con «Exited (0)» | el comando del compose oficial recorría el proyecto montado en solo lectura; el contenedor seguía y terminaba bien | corregido en el compose (el `chown` salta `/opt/airflow/medallon`); con un compose anterior es ruido sin consecuencias | (visto) |
| 4 | **Antes** (compose sellado): `airflow-apiserver` queda «unhealthy» y su registro dice «password authentication failed for user airflow»; `airflow-init` salió con «Exited (0)». **Ahora**: `airflow-init` imprime «ERROR: could not connect to the metadata database», sale con «Exited (1)» y `docker compose up -d` termina con código 1 con los demás servicios «not started: condition "service_completed_successfully"» | existe un volumen de Postgres de otra instalación (mismo nombre de proyecto de Compose) con otra contraseña | `preparar_airflow.py` avisa antes con una línea «!»; use `--nombre-compose <otro nombre>` y levante de nuevo; **no** borre el volumen viejo sin estar seguro de que no sirve | (visto) |
| 5 | no sé qué contraseña pedir en la interfaz de Airflow | la contraseña está en el `.env` de la carpeta de Airflow, no en el del proyecto | variable `_AIRFLOW_WWW_USER_PASSWORD`; usuario `airflow`; cópiela con el comando de la sección 6 | (visto) |
| 6 | al teclear `root` en el indicador de PowerShell, PowerShell dice que no reconoce `root` como nombre de un comando | la contraseña de `root` se teclea solo cuando el script la pide | ejecute de nuevo el comando de la guía y espere la línea «Contraseña del administrador de MySQL (root)…» | (visto) |
| 7 | «el programa git no está instalado» con una carpeta `.git` presente | `escanear_secretos.py` y `configurar_mysql.py` necesitan Git si hay un repositorio | instale Git o descomprima el zip fuera del repositorio | (deducido) |
| 8 | `docker: error during connect` o «Docker está instalado pero no responde» | Docker Desktop apagado o arrancando | encienda Docker Desktop y espere «Engine running» | (deducido) |

## 11. Si quiere volver a usar un `.env` anterior
Las contraseñas de MySQL viven en MySQL y en los archivos `.env`; **cada cuenta tiene una sola contraseña vigente**. Después de la sección 3, el `.env` de cualquier otra carpeta (el de su proyecto anterior, por ejemplo) tiene contraseñas viejas y ya no entra a MySQL.
Para resincronizar, elija **una** carpeta como la que manda y haga ahí los pasos; las demás dejan de servir hasta que repita el proceso en ellas.

**Qué debe verse al comprobar un `.env` anterior (visto):**
```text
2026-11-16 14:28:08 ERROR etl.__main__ las credenciales de .env no son válidas (ejecuta el script sin --solo-verificar)
```
**Varía:** la fecha y la hora. El código de salida de ese comando es 1 (`$LASTEXITCODE`) y no pide la contraseña de `root` ni imprime ninguna clave. **Lo vio Daniel el 2026-11-16 en su proyecto real, en su propia terminal; no es una ejecución nuestra** ([EV-106](../evidencias/modo_completo/EV-106_resincronizar_un_env_anterior.txt)).
**Tiempo:** menos de 1 s.

Pasos (vistos por Daniel el 2026-11-16, en la carpeta que manda, con la contraseña de `root` tecleada por él en cada uno): (1) `.\.venv\Scripts\python.exe scripts\mysql\configurar_mysql.py --rotar`, luego `.\.venv\Scripts\python.exe scripts\mysql\configurar_mysql.py --usuario-docker --origen localhost --rotar` y `.\.venv\Scripts\python.exe scripts\mysql\configurar_mysql.py --usuario-lectura --rotar`; cada uno imprime el indicador de `root`, la versión de MySQL, la línea «variables escritas en .env» con solo los nombres y «Listo». Después, `.\.venv\Scripts\python.exe scripts\mysql\configurar_mysql.py --solo-verificar` imprime «verificación correcta» y sale con 0 (el bloque de la sección 3). (2) Apague phpMyAdmin y Airflow (sección 9) y levántelos de nuevo para que lean el `.env` nuevo: **este segundo paso no se probó**.

## 12. Qué no demuestra esta guía
- Que funcione en un equipo distinto de aquel donde se probó, con otra versión de Docker Desktop o de MySQL, o con menos de 8 GB de memoria.
- Que el DAG funcione a las 06:00 sin que nadie lo vea: se probó disparándolo a mano.
- Que sirva dentro de otro repositorio de Git (limitación deducida: descomprima fuera de cualquier repositorio).
- Nada sobre la calidad de los datos: solo que las siete tablas se cargan y que la cuenta de lectura no puede escribir.
