# Guía del modo completo: MySQL, Airflow y phpMyAdmin desde el zip

**Componente:** Servicios locales · **Requisitos:** el [modo mínimo](modo_minimo.md) funcionando, MySQL 8.0 o superior, Docker Desktop con WSL2 y la contraseña de `root` de MySQL · **Estado:** borrador; los bloques «Qué debe verse» marcados «no probado» se llenan con la prueba desde un zip nuevo

Esta guía lleva, paso a paso, a una persona que recibe el zip hasta tener tres cosas funcionando en su equipo: las cuentas de MySQL, Airflow ejecutando el DAG de las 06:00 y phpMyAdmin mirando las siete tablas. La escribimos porque quien la probó
por primera vez, desde el zip y en otra carpeta, tropezó con seis cosas que ningún documento decía (están en la [sección 10](#10-si-algo-falla)). [modo_completo.md](modo_completo.md) sigue siendo la referencia corta de los mismos pasos; esta guía agrega lo que debe verse en cada
comando y qué hacer cuando no se ve.

## Cómo leer esta guía
- Todos los comandos son de **PowerShell** y cada uno está en su propio bloque. Debajo de cada comando hay un bloque **«Qué debe verse»** con lo que imprime.
- Cada bloque «Qué debe verse» dice si es **(visto)**, porque lo copiamos de una ejecución real desde un zip nuevo en otra carpeta, o **(no probado)**. Nada se afirma sin haberlo ejecutado.
- Lo que cambia de un equipo a otro está enmascarado con marcadores fijos: `<usuario>` (el nombre de usuario de Windows), `<ruta>` (una carpeta de su equipo), `<ID>` (un identificador que genera el programa), `<PID>` (un número de proceso), `<hash>` (una huella)
  y `<contraseña>` (cualquier contraseña o clave: nunca se imprime). Debajo de cada bloque «visto» una línea **Varía:** dice qué partes cambian en su equipo (tiempos, identificadores, fechas).
- Donde dice **código de salida** se refiere a `$LASTEXITCODE` justo después del comando; `0` significa que terminó bien.

## 0. Antes de empezar
| Hace falta | Para qué | Cómo se comprueba |
|---|---|---|
| El proyecto descomprimido en una carpeta de ruta corta, **fuera de cualquier repositorio de Git** | los comandos usan la carpeta tal como está; dentro de otro repositorio, la comprobación de `.env` sigue lo que diga ese repositorio y la base guardaría el commit de ese repositorio (limitación **deducida**: no la probamos) | que ninguna carpeta por encima tenga `.git` |
| El entorno virtual del proyecto (`.venv`) | todos los scripts se ejecutan con `.\.venv\Scripts\python.exe` | [modo mínimo, paso 3](modo_minimo.md#3-crear-el-entorno-e-instalar) |
| MySQL 8.0 o superior con el servicio `MySQL80` activo y la contraseña de `root` | las tres cuentas del proyecto | sección 1 |
| Docker Desktop encendido (WSL2) | Airflow y phpMyAdmin | `docker version` |
| Los puertos 3306, 8000, 8501, 8080 y 8081 | MySQL, API, panel, Airflow y phpMyAdmin | sección 1 |

**Orden de los pasos:** comprobar que no hay nada levantado (1) → descomprimir y revisar `.env` (2) → cuentas de MySQL (3) → carpeta de Airflow (4) → construir y levantar (5) → contraseña de la interfaz (6) → DAG (7) → phpMyAdmin (8) → apagar (9).
Los pasos 3 a 9 se hacen siempre desde la raíz del proyecto, salvo donde dice que se entre a la carpeta de Airflow.

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

## 1. Comprobar que no hay nada levantado y que el equipo está listo
Antes de empezar no debe haber contenedores de pruebas anteriores (Airflow, phpMyAdmin) ni paneles conectados a MySQL, para no confundir lo que se ve con lo de otra prueba.

```powershell
docker ps
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

```powershell
py -3.13 scripts\preparar_entorno.py --modo completo
```
Debe mostrar ✓ en MySQL, Docker y los cuatro puertos; lo que falte trae su acción sugerida.

**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

## 2. El zip: descomprimir y revisar el `.env` sin Git
Descomprima el zip en una carpeta de ruta corta y entre a ella; cree el entorno con el [modo mínimo](modo_minimo.md#3-crear-el-entorno-e-instalar).

```powershell
.\.venv\Scripts\python.exe -m pip check
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

El zip **no trae `.git`**. No hace falta `git init`: los scripts que guardan contraseñas aceptan una carpeta sin repositorio si el `.gitignore` ignora `.env` y lo dicen en una línea. El `.gitignore` del zip ya trae esa línea; compruebe que siga ahí.

```powershell
Select-String -Path .gitignore -Pattern '^\.env$'
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

## 3. Las tres cuentas de MySQL
> **Estos tres comandos cambian las contraseñas de `sismo_etl`, `sismo_airflow` y `sismo_lectura`.** Si usted ya tenía esas cuentas con un `.env` de otra carpeta, ese `.env` deja de servir; vea la [sección 11](#11-si-quiere-volver-a-usar-un-env-anterior).
> Cada comando pide la contraseña de `root` **una vez** (tres comandos, tres veces). El script nunca imprime ninguna contraseña: solo los **nombres** de las variables que escribe en `.env`.

La cuenta del proyecto (`sismo_etl`) y las dos bases:
```powershell
.\.venv\Scripts\python.exe scripts\mysql\configurar_mysql.py
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

La cuenta de Airflow (`sismo_airflow`), con el origen `localhost` porque Docker Desktop hace llegar al MySQL del equipo las conexiones de los contenedores como si vinieran de este mismo equipo:
```powershell
.\.venv\Scripts\python.exe scripts\mysql\configurar_mysql.py --usuario-docker --origen localhost
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

La cuenta de solo lectura (`sismo_lectura`), para phpMyAdmin:
```powershell
.\.venv\Scripts\python.exe scripts\mysql\configurar_mysql.py --usuario-lectura
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

Para comprobar las credenciales sin cambiar nada (no pide la contraseña de `root`):
```powershell
.\.venv\Scripts\python.exe scripts\mysql\configurar_mysql.py --solo-verificar
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

## 4. La carpeta de Airflow
Airflow vive en una carpeta **hermana** del proyecto que genera `preparar_airflow.py` (no se versiona ni es un requisito previo). Primero se mira, sin escribir nada:

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

```powershell
.\.venv\Scripts\python.exe scripts\orquestacion\preparar_airflow.py --nombre-compose airflow-zip
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

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

```powershell
Set-Location ..\airflow-medallon
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

```powershell
docker compose build
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

```powershell
docker compose up airflow-init
```
Prepara la base de metadatos y el usuario de la interfaz y termina solo. Debe terminar con `airflow-init ... exited with code 0`. Ya no debe imprimir líneas «Read-only file system» sobre el `.venv` del proyecto (error 3 de la sección 10).

**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

```powershell
docker compose up -d
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

```powershell
docker compose ps -a
```
Cuando todo está sano: `airflow-apiserver`, `airflow-scheduler`, `airflow-dag-processor`, `airflow-triggerer` y `airflow-worker` en «Up … (healthy)»; `airflow-init` en «Exited (0)»; `postgres` y `redis` «(healthy)». Si el servidor de Airflow sale «unhealthy», vea el error 4.

**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

```powershell
(Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8080/api/v2/monitor/health).StatusCode
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

## 6. La interfaz de Airflow y su contraseña
La interfaz está en `http://127.0.0.1:8080` (o el puerto que eligió con `--puerto`). El usuario es **`airflow`** y la contraseña está en la variable `_AIRFLOW_WWW_USER_PASSWORD` del `.env` de la **carpeta de Airflow**. Para pegarla sin mostrarla en pantalla, cópiela al portapapeles
y péguela en el formulario con Ctrl+V:

```powershell
(Select-String -Path .env -Pattern '^_AIRFLOW_WWW_USER_PASSWORD=').Line.Split('=', 2)[1] | Set-Clipboard
```
No imprime nada. **Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

## 7. El DAG: activar, disparar y leer las cuatro tareas
El DAG se llama `medallon_etl_sismo`, corre todos los días a las 06:00 (hora de Bogotá) y tiene cuatro tareas en este orden: `validar_bronze`, `transformar_a_silver`, `integrar_a_gold` y `cargar_datawarehouse`. Nace en pausa.

```powershell
docker compose exec airflow-scheduler airflow dags list-import-errors
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

```powershell
docker compose exec airflow-scheduler airflow dags unpause medallon_etl_sismo
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

```powershell
docker compose exec airflow-scheduler airflow dags trigger medallon_etl_sismo
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

```powershell
docker compose exec airflow-scheduler airflow dags list-runs medallon_etl_sismo
```
Repítalo cada pocos segundos hasta que la ejecución diga `success`.

**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

```powershell
docker compose exec airflow-scheduler airflow tasks states-for-dag-run medallon_etl_sismo <ID>
```
Use como `<ID>` el identificador de la ejecución que mostró el comando anterior. Debe mostrar las cuatro tareas en `success`.

**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

**En la interfaz:** entre a `http://127.0.0.1:8080`, abra el DAG `medallon_etl_sismo` en la lista, pulse el interruptor para activarlo (si no lo hizo por terminal), pulse el botón de disparar (▶) y abra la ejecución: la cuadrícula muestra las cuatro tareas en verde. Con un clic en una tarea y «Logs»
se lee su registro. Ninguna tarea imprime contraseñas.

## 8. phpMyAdmin (solo lectura)
Desde la **raíz del proyecto** (no desde la carpeta de Airflow):

```powershell
Set-Location ..\<carpeta del proyecto>
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

```powershell
docker compose -f servicios\phpmyadmin\docker-compose.yaml up -d
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

```powershell
docker compose -f servicios\phpmyadmin\docker-compose.yaml ps
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

La página está en `http://127.0.0.1:8081`. El usuario es **`sismo_lectura`** y la contraseña es la variable `MYSQL_LECTURA_PASSWORD` del `.env` **del proyecto**. Cópiela sin mostrarla:

```powershell
(Select-String -Path .env -Pattern '^MYSQL_LECTURA_PASSWORD=').Line.Split('=', 2)[1] | Set-Clipboard
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

## 9. Apagar
Primero phpMyAdmin (desde la raíz del proyecto):

```powershell
docker compose -f servicios\phpmyadmin\docker-compose.yaml down
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

Después Airflow (desde la carpeta de Airflow). `down` conserva los volúmenes: al volver a levantar con `docker compose up -d` el DAG, sus ejecuciones y sus contraseñas siguen ahí.

```powershell
Set-Location ..\airflow-medallon
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

```powershell
docker compose down
```
**Qué debe verse (no probado):**
```text
<pendiente: se copia de la prueba desde el zip>
```

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
| 4 | `airflow-apiserver` queda «unhealthy» y su registro dice «password authentication failed for user airflow» | existe un volumen de Postgres de otra instalación (mismo nombre de proyecto de Compose) con otra contraseña | `preparar_airflow.py` avisa antes con una línea «!»; use `--nombre-compose <otro nombre>` y levante de nuevo; **no** borre el volumen viejo sin estar seguro de que no sirve | (visto) |
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
