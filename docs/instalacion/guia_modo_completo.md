# Guía del modo completo: MySQL, Airflow y phpMyAdmin desde el zip

**Componente:** Servicios locales · **Requisitos:** el [modo mínimo](modo_minimo.md) funcionando, MySQL 8.0 o superior, Docker Desktop con WSL2 y la contraseña de `root` de MySQL · **Estado:** borrador; los bloques «Qué debe verse» marcados «no probado» se llenan con la prueba desde un zip nuevo

Esta guía lleva, paso a paso, a una persona que recibe el zip hasta tener tres cosas funcionando en su equipo: las cuentas de MySQL, Airflow ejecutando el DAG de las 06:00 y phpMyAdmin mirando las siete tablas. La escribimos porque quien la probó
por primera vez, desde el zip y en otra carpeta, tropezó con seis cosas que ningún documento decía (están en la [sección 10](#10-si-algo-falla)). [modo_completo.md](modo_completo.md) sigue siendo la referencia corta de los mismos pasos; esta guía agrega para qué sirve cada comando,
lo que debe verse al ejecutarlo y qué hacer cuando no se ve.

## Cómo leer esta guía
- Todos los comandos son de **PowerShell** y cada uno está en su propio bloque. Antes de cada comando hay una línea **«Para qué sirve»**; debajo, un bloque **«Qué debe verse»** con lo que imprime.
- Cada bloque «Qué debe verse» dice si es **(visto)**, porque lo copiamos de una ejecución real desde un zip nuevo en otra carpeta, o **(no probado)**. Nada se afirma sin haberlo ejecutado. Los comandos que no imprimen nada (cambiar de carpeta, copiar al portapapeles) llevan el bloque `(sin salida)`, también marcado.
- Lo que cambia de un equipo a otro está enmascarado con marcadores fijos: `<usuario>` (el nombre de usuario de Windows), `<ruta>` (una carpeta de su equipo), `<ID>` (un identificador que genera el programa), `<PID>` (un número de proceso), `<hash>` (una huella)
  y `<contraseña>` (cualquier contraseña o clave: nunca se imprime). Debajo de cada bloque «visto» una línea **Varía:** dice qué partes cambian en su equipo (tiempos, identificadores, fechas) y otra **Tiempo:** cuánto tardó.
- Donde un comando trae `<ID>` o `<carpeta del proyecto>`, la guía dice **«Reemplace»** y por qué valor.
- Donde dice **código de salida** se refiere a `$LASTEXITCODE` justo después del comando; `0` significa que terminó bien.
- Esta guía trae **33 comandos**: **0** con su salida vista y **33** sin probar.

## 0. Antes de empezar
**Requisito previo: el zip descomprimido y el entorno creado.** Descomprima el zip en una carpeta **nueva**, de ruta corta (menos de unos 120 caracteres), **fuera de cualquier repositorio de Git** y **fuera de carpetas sincronizadas con OneDrive** (la sincronización puede bloquear o demorar archivos mientras Docker los monta; es una
precaución **deducida**, no la probamos). Después cree el entorno virtual siguiendo el [modo mínimo, paso 3](modo_minimo.md#3-crear-el-entorno-e-instalar) y compruebe que quedó completo:

**Para qué sirve:** comprobar que los paquetes del entorno no tienen conflictos antes de usar los scripts.
```powershell
.\.venv\Scripts\python.exe -m pip check
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

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
Los pasos 1 a 9 se hacen desde la raíz del proyecto, salvo donde dice que se entre a la carpeta de Airflow.

**Qué conserva y qué borra cada comando de apagado**
| Comando | Detiene los contenedores | Borra los contenedores | Borra los volúmenes (la base de metadatos de Airflow) |
|---|---|---|---|
| `docker compose stop` | sí | no | no |
| `docker compose down` | sí | sí | **no** |
| `docker compose down -v` | sí | sí | **sí: pierde el historial de ejecuciones y las contraseñas de esa instalación de Airflow** |

### La contraseña de `root` se teclea solo cuando el script la pide
Los tres comandos de la sección 3 abren una línea que dice **«Contraseña del administrador de MySQL (root); no se muestra al escribir:»**. Ahí, y solo ahí, se escribe la contraseña de la cuenta `root` de MySQL (no la palabra `root`) y se presiona Enter;
al teclear no aparece nada, ni siquiera asteriscos. Si se escribe `root` en el indicador de PowerShell, antes de que el script pida nada, PowerShell contesta que no conoce ese comando; no pasó nada y se vuelve a ejecutar el comando de la guía.

**Qué debe verse si se teclea `root` en el indicador de PowerShell (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

### Contraseñas copiadas al portapapeles
Las secciones 6 y 8 copian una contraseña al portapapeles para pegarla en una página sin mostrarla. Apenas la pegue, **limpie el portapapeles** con el comando que sigue a cada copia (`Set-Clipboard -Value $null`).

## 1. Revisar el `.gitignore` y el `.env` (sin Git)
El zip **no trae `.git`**. No hace falta `git init`: los scripts que guardan contraseñas aceptan una carpeta sin repositorio si el `.gitignore` ignora `.env`, y lo dicen en una línea. El `.gitignore` del zip ya trae esa línea; compruebe que siga ahí.

**Para qué sirve:** comprobar que el `.gitignore` ignora `.env`, que es lo que protege las contraseñas si alguien usa Git más adelante en esta carpeta.
```powershell
Select-String -Path .gitignore -Pattern '^\.env$'
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

## 2. Comprobar que no hay nada levantado y que el equipo está listo
Antes de seguir no debe haber contenedores de pruebas anteriores (Airflow, phpMyAdmin) ni paneles conectados a MySQL, para no confundir lo que se ve con lo de otra prueba.

**Para qué sirve:** ver qué contenedores están en marcha; con todo apagado la lista está vacía.
```powershell
docker ps
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

**Para qué sirve:** diagnosticar el equipo para el modo completo (`--modo completo` suma MySQL, Docker y los puertos de Airflow y phpMyAdmin a lo que mira el modo mínimo); lo que falte trae su acción sugerida.
```powershell
py -3.13 scripts\preparar_entorno.py --modo completo
```
Debe mostrar ✓ en MySQL, Docker y los cuatro puertos.

**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

## 3. Las tres cuentas de MySQL
> **Estos tres comandos cambian las contraseñas de `sismo_etl`, `sismo_airflow` y `sismo_lectura`.** Si usted ya tenía esas cuentas con un `.env` de otra carpeta, ese `.env` deja de servir; vea la [sección 11](#11-si-quiere-volver-a-usar-un-env-anterior).
> Cada comando pide la contraseña de `root` **una vez** (tres comandos, tres veces). El script nunca imprime ninguna contraseña: solo los **nombres** de las variables que escribe en `.env`.

**Para qué sirve:** crear la cuenta del proyecto (`sismo_etl`) y las dos bases, y guardar su contraseña en `.env`.
```powershell
.\.venv\Scripts\python.exe scripts\mysql\configurar_mysql.py
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

**Para qué sirve:** crear la cuenta que usa el DAG de Airflow (`sismo_airflow`), con el origen `localhost` porque Docker Desktop hace llegar al MySQL del equipo las conexiones de los contenedores como si vinieran de este mismo equipo (lo medimos en [EV-040](../evidencias/orquestacion/EV-040_origen_mysql_desde_docker.txt) en una máquina con Windows; en otro sistema el origen puede ser otro).
```powershell
.\.venv\Scripts\python.exe scripts\mysql\configurar_mysql.py --usuario-docker --origen localhost
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

**Para qué sirve:** crear la cuenta de solo lectura (`sismo_lectura`) con la que se entra a phpMyAdmin.
```powershell
.\.venv\Scripts\python.exe scripts\mysql\configurar_mysql.py --usuario-lectura
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

**Para qué sirve:** comprobar las credenciales de `.env` sin cambiar nada (no pide la contraseña de `root`).
```powershell
.\.venv\Scripts\python.exe scripts\mysql\configurar_mysql.py --solo-verificar
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

## 4. La carpeta de Airflow
Airflow vive en una carpeta **hermana** del proyecto que genera `preparar_airflow.py` (no se versiona ni es un requisito previo). Primero se mira, sin escribir nada.

**Para qué sirve:** ver qué falta antes de preparar la carpeta de Airflow, sin escribir nada.
```powershell
.\.venv\Scripts\python.exe scripts\orquestacion\preparar_airflow.py --verificar
```
Antes de preparar, algunas líneas salen con ✗ (falta la carpeta, el `.env` de Airflow…): es lo esperado.

**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

**Elija un nombre de proyecto de Compose.** Sin opción, Compose usa el nombre de la carpeta de Airflow (`airflow-medallon`) y, con él, el **mismo volumen de Postgres** para cualquier zip que se descomprima junto a una carpeta con ese nombre. Si ese volumen viene de otra instalación,
tiene otra contraseña y el servidor de Airflow queda «unhealthy» (sección 10, error 4). Con `--nombre-compose` el volumen es otro y no se toca el viejo. Use minúsculas, dígitos, guion y guion bajo (por ejemplo `airflow-zip`).

**Para qué sirve:** crear la carpeta de Airflow con su compose, su DAG y su `.env` (con contraseñas aleatorias que nunca se imprimen), usando un nombre de proyecto propio.
```powershell
.\.venv\Scripts\python.exe scripts\orquestacion\preparar_airflow.py --nombre-compose airflow-zip
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

**Para qué sirve:** comprobar que la carpeta de Airflow quedó completa y que el `.env` del proyecto trae lo que necesita la tarea de carga.
```powershell
.\.venv\Scripts\python.exe scripts\orquestacion\preparar_airflow.py --verificar
```
Ahora todas las líneas deben salir con ✓.

**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

## 5. Construir y levantar
Los comandos de `docker compose` de Airflow **se ejecutan en la carpeta de Airflow**, no en la del proyecto (error 2 de la sección 10).

**Para qué sirve:** entrar a la carpeta de Airflow, donde está su compose.
```powershell
Set-Location ..\airflow-medallon
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

**Para qué sirve:** construir la imagen de Airflow con las dependencias del pipeline.
```powershell
docker compose build
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

**Para qué sirve:** preparar la base de metadatos de Airflow (en Postgres) y crear el usuario de la interfaz; termina solo.
```powershell
docker compose up airflow-init
```
**Cuidado con el código de salida.** Leímos el comando de `airflow-init` en `orquestacion/docker-compose.yaml`: crea las carpetas, ejecuta `airflow version` (la imagen migra la base y crea el usuario de la interfaz porque el compose activa `_AIRFLOW_DB_MIGRATE` y `_AIRFLOW_WWW_USER_CREATE`; **deducido** del compose, se confirma en la prueba), genera la configuración y cambia el dueño de las carpetas compartidas.
El script **no usa `set -e` y su último comando es un `ls`**, así que termina con `Exited (0)` aunque un paso anterior haya fallado; así pasó cuando la contraseña de Postgres era la equivocada (error 4). Por eso **`Exited (0)` no garantiza una base correcta**: la señal fiable es `docker compose ps -a` con todo «(healthy)», más abajo.

**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

**Para qué sirve:** arrancar todos los contenedores de Airflow en segundo plano.
```powershell
docker compose up -d
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

**Para qué sirve:** ver el estado de cada contenedor; es **la señal fiable** de que Airflow quedó sano.
```powershell
docker compose ps -a
```
Cuando todo está sano: `airflow-apiserver`, `airflow-scheduler`, `airflow-dag-processor`, `airflow-triggerer` y `airflow-worker` en «Up … (healthy)»; `airflow-init` en «Exited (0)»; `postgres` y `redis` «(healthy)». Si el servidor de Airflow sale «unhealthy», vea el error 4.

**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

**Para qué sirve:** comprobar que la interfaz responde (es la misma dirección que usa el compose para su prueba de salud: `/api/v2/monitor/health`).
```powershell
(Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8080/api/v2/monitor/health).StatusCode
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

## 6. La interfaz de Airflow y su contraseña
La interfaz está en `http://127.0.0.1:8080` (o el puerto que eligió con `--puerto`). El usuario es **`airflow`** y la contraseña está en la variable `_AIRFLOW_WWW_USER_PASSWORD` del `.env` de la **carpeta de Airflow**. Para pegarla sin mostrarla en pantalla, cópiela al portapapeles
y péguela en el formulario con Ctrl+V.

**Para qué sirve:** copiar al portapapeles la contraseña de la interfaz sin mostrarla.
```powershell
(Select-String -Path .env -Pattern '^_AIRFLOW_WWW_USER_PASSWORD=').Line.Split('=', 2)[1] | Set-Clipboard
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

**Para qué sirve:** vaciar el portapapeles apenas haya pegado la contraseña.
```powershell
Set-Clipboard -Value $null
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

## 7. El DAG: activar, disparar y leer las cuatro tareas
El DAG se llama `medallon_etl_sismo`, corre todos los días a las 06:00 (hora de Bogotá) y tiene cuatro tareas en este orden: `validar_bronze`, `transformar_a_silver`, `integrar_a_gold` y `cargar_datawarehouse`. **Nace en pausa** (el compose lo configura así), por eso hay que activarlo.

**Para qué sirve:** comprobar que Airflow leyó el DAG sin errores de importación.
```powershell
docker compose exec airflow-scheduler airflow dags list-import-errors
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

**Para qué sirve:** activar el DAG para que se ejecute a su hora.
```powershell
docker compose exec airflow-scheduler airflow dags unpause medallon_etl_sismo
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

**Para qué sirve:** disparar una ejecución ahora, sin esperar a las 06:00.
```powershell
docker compose exec airflow-scheduler airflow dags trigger medallon_etl_sismo
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

**Para qué sirve:** ver el estado de las ejecuciones del DAG y su identificador.
```powershell
docker compose exec airflow-scheduler airflow dags list-runs medallon_etl_sismo
```
Repítalo cada pocos segundos hasta que la ejecución diga `success`.

**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

**Para qué sirve:** ver el estado de cada una de las cuatro tareas de una ejecución (el subcomando `tasks states-for-dag-run` es **deducido** de la ayuda de Airflow; se confirma en la prueba).
```powershell
docker compose exec airflow-scheduler airflow tasks states-for-dag-run medallon_etl_sismo <ID>
```
**Reemplace `<ID>`** por el identificador de la ejecución que mostró el comando anterior. Debe mostrar las cuatro tareas en `success`.

**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

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

**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

**Para qué sirve:** levantar phpMyAdmin en el puerto 8081 (solo en este equipo).
```powershell
docker compose -f servicios\phpmyadmin\docker-compose.yaml up -d
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

**Para qué sirve:** comprobar que el contenedor de phpMyAdmin está en marcha.
```powershell
docker compose -f servicios\phpmyadmin\docker-compose.yaml ps
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

La página está en `http://127.0.0.1:8081`. El usuario es **`sismo_lectura`** y la contraseña es la variable `MYSQL_LECTURA_PASSWORD` del `.env` **del proyecto**. Cópiela sin mostrarla.

**Para qué sirve:** copiar al portapapeles la contraseña de `sismo_lectura` sin mostrarla.
```powershell
(Select-String -Path .env -Pattern '^MYSQL_LECTURA_PASSWORD=').Line.Split('=', 2)[1] | Set-Clipboard
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

**Para qué sirve:** vaciar el portapapeles apenas haya pegado la contraseña.
```powershell
Set-Clipboard -Value $null
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

**Qué se ve en la página (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```
Al entrar, en la base `sismo_cali` aparecen las siete tablas: `barrio_estrato`, `comuna`, `construccion`, `corrida`, `corrida_archivo`, `kpi` y `kpi_sensibilidad`, con sus filas.

**Pruebe que no se puede escribir.** En la pestaña **SQL** de la base `sismo_cali`, escriba `INSERT INTO corrida (id) VALUES (999999);` y pulse «Continuar». MySQL debe rechazarlo con el error **#1142**; los conteos no cambian.

**Qué se ve al rechazar el `INSERT` (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

> **Captura opcional (aún no incluida):** las siete tablas de `sismo_cali` en phpMyAdmin, recortada, sin nombre de usuario ni claves. Si existe, se agrega aquí como «imagen existente».

## 9. Apagar
Primero phpMyAdmin (desde la raíz del proyecto).

**Para qué sirve:** detener y eliminar el contenedor de phpMyAdmin.
```powershell
docker compose -f servicios\phpmyadmin\docker-compose.yaml down
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

Después Airflow (desde la carpeta de Airflow). `down` conserva los volúmenes: al volver a levantar con `docker compose up -d` el DAG, sus ejecuciones y sus contraseñas siguen ahí.

**Para qué sirve:** volver a la carpeta de Airflow, donde está su compose.
```powershell
Set-Location ..\airflow-medallon
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

**Para qué sirve:** detener y eliminar los contenedores de Airflow, conservando el volumen de Postgres.
```powershell
docker compose down
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

**Para qué sirve:** confirmar que no queda ningún contenedor en marcha.
```powershell
docker ps
```
Con todo apagado, la lista debe estar vacía.

**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

> **No use `docker compose down -v` por costumbre.** Borra el volumen de Postgres, es decir, todas las ejecuciones y las contraseñas de esa instalación de Airflow, y no hay cómo recuperarlas. Úselo solo si quiere empezar esa instalación de cero, nunca sobre un volumen de otra prueba que no sea suyo.

## 10. Si algo falla
Cada fila dice cómo se supo: **(visto)** si alguien lo reprodujo en una ejecución real; **(deducido)** si lo concluimos leyendo el código y no lo hemos visto.

| N.º | Qué se ve | Causa | Qué hacer | Cómo se supo |
|---|---|---|---|---|
| 1 | `configurar_mysql.py` termina con «.env no está ignorado por git o está versionado» (antes de esta guía, también sin `.git`) | la comprobación exigía Git; el zip no trae `.git` | con la versión actual el mensaje, sin repositorio, es «esta carpeta no es un repositorio de Git … su .gitignore no deja ignorado el archivo .env»: restaure la línea `.env` del `.gitignore` (está en el zip); `git init` ya no hace falta | (visto) |
| 2 | `docker compose build` dice «no configuration file provided» | se ejecutó en la carpeta del proyecto | `Set-Location ..\airflow-medallon` y repetir | (visto) |
| 3 | `airflow-init` imprime muchas líneas «chown … Read-only file system» sobre `.venv` y termina con «Exited (0)» | el comando del compose oficial recorría el proyecto montado en solo lectura; el contenedor seguía y terminaba bien | corregido en el compose (el `chown` salta `/opt/airflow/medallon`); con un compose anterior es ruido sin consecuencias | (visto) |
| 4 | `airflow-apiserver` queda «unhealthy» y su registro dice «password authentication failed for user airflow»; `airflow-init` salió con «Exited (0)» | existe un volumen de Postgres de otra instalación (mismo nombre de proyecto de Compose) con otra contraseña | `preparar_airflow.py` avisa antes con una línea «!»; use `--nombre-compose <otro nombre>` y levante de nuevo; **no** borre el volumen viejo sin estar seguro de que no sirve | (visto) |
| 5 | no sé qué contraseña pedir en la interfaz de Airflow | la contraseña está en el `.env` de la carpeta de Airflow, no en el del proyecto | variable `_AIRFLOW_WWW_USER_PASSWORD`; usuario `airflow`; cópiela con el comando de la sección 6 | (visto) |
| 6 | al teclear `root` en el indicador de PowerShell, PowerShell dice que no reconoce `root` como nombre de un comando | la contraseña de `root` se teclea solo cuando el script la pide | ejecute de nuevo el comando de la guía y espere la línea «Contraseña del administrador de MySQL (root)…» | (visto) |
| 7 | «el programa git no está instalado» con una carpeta `.git` presente | `escanear_secretos.py` y `configurar_mysql.py` necesitan Git si hay un repositorio | instale Git o descomprima el zip fuera del repositorio | (deducido) |
| 8 | `docker: error during connect` o «Docker está instalado pero no responde» | Docker Desktop apagado o arrancando | encienda Docker Desktop y espere «Engine running» | (deducido) |

## 11. Si quiere volver a usar un `.env` anterior
Las contraseñas de MySQL viven en MySQL y en los archivos `.env`; **cada cuenta tiene una sola contraseña vigente**. Después de la sección 3, el `.env` de cualquier otra carpeta (el de su proyecto anterior, por ejemplo) tiene contraseñas viejas y ya no entra a MySQL.
Para resincronizar, elija **una** carpeta como la que manda y haga ahí los pasos; las demás dejan de servir hasta que repita el proceso en ellas.

**Qué debe verse al comprobar un `.env` anterior (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```
Pasos (no probados): (1) en la carpeta que manda, `.\.venv\Scripts\python.exe scripts\mysql\configurar_mysql.py --rotar` y los dos comandos de la sección 3 con `--rotar`; (2) apague phpMyAdmin y Airflow (sección 9) y levántelos de nuevo para que lean el `.env` nuevo.

## 12. Qué no demuestra esta guía
- Que funcione en un equipo distinto de aquel donde se probó, con otra versión de Docker Desktop o de MySQL, o con menos de 8 GB de memoria.
- Que el DAG funcione a las 06:00 sin que nadie lo vea: se probó disparándolo a mano.
- Que sirva dentro de otro repositorio de Git (limitación deducida: descomprima fuera de cualquier repositorio).
- Nada sobre la calidad de los datos: solo que las siete tablas se cargan y que la cuenta de lectura no puede escribir.
