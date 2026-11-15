# Modo completo: MySQL, panel con MySQL, Airflow y phpMyAdmin

**Componente:** Servicios locales · **Requisitos:** el [modo mínimo](modo_minimo.md) funcionando, MySQL 8.0 o superior y Docker Desktop con WSL2 · **Decisiones:** [D91 a D94](../DECISIONES.md)

Este modo suma los servicios que el proyecto usa para la carga relacional y la orquestación. Lo dejamos aparte porque necesita contraseñas y programas que el modo mínimo no pide, y porque cada pieza se puede
levantar por separado. Los comandos son de PowerShell, desde la raíz del proyecto. **Ninguna contraseña pasa por esta guía ni por el equipo que escribió el código:** la de `root` de MySQL la teclea la persona que
la conoce, y las demás las genera el proyecto con `secrets` y quedan solo en archivos `.env`, que Git ignora.

## 1. Comprobar el equipo
```powershell
py -3.13 scripts\preparar_entorno.py --modo completo
```
Debe mostrar ✓ en MySQL, Docker y los puertos 8000, 8501, 8080 y 8081. Lo que falte trae su acción sugerida.

## 2. MySQL: las tres cuentas
Con el servicio **MySQL80** activo, se crean las bases `sismo_cali` y `sismo_cali_prueba` y tres cuentas, cada una con el mínimo privilegio que necesita (D46, D60 y D91). Cada comando pide la contraseña de
`root` con el teclado, sin mostrarla; no se pasa por argumento, variable de entorno ni archivo.

| Comando | Crea | Para qué | Privilegios |
|---|---|---|---|
| `.\.venv\Scripts\python.exe scripts\mysql\configurar_mysql.py` | `sismo_etl`@`localhost` y las dos bases | la carga y la API con `--almacenamiento mysql` | lectura y escritura solo sobre las dos bases del proyecto |
| `.\.venv\Scripts\python.exe scripts\mysql\configurar_mysql.py --usuario-docker --origen localhost` | `sismo_airflow`@`localhost` | la tarea de carga del DAG | `SELECT`, `INSERT`, `CREATE`, `INDEX` y `REFERENCES` solo sobre `sismo_cali` |
| `.\.venv\Scripts\python.exe scripts\mysql\configurar_mysql.py --usuario-lectura` | `sismo_lectura`@`localhost` | mirar los datos en phpMyAdmin | solo `SELECT` sobre `sismo_cali` |

El origen es `localhost` porque Docker Desktop entrega al MySQL del anfitrión las conexiones de los contenedores como si vinieran de este mismo equipo (lo medimos en [EV-040](../evidencias/orquestacion/EV-040_origen_mysql_desde_docker.txt) y lo decidimos en D65);
en otro sistema (por ejemplo Docker en Linux nativo) el origen puede ser otro y hay que volver a medirlo. Ningún usuario se crea con `%`. Los tres comandos son idempotentes: si el `.env` ya tiene las credenciales, no
cambian nada ni piden la contraseña de `root`; `--rotar` cambia la contraseña y `--solo-verificar` comprueba sin modificar. Los valores quedan en `.env` (variables `MYSQL_*`, `MYSQL_DOCKER_*` y `MYSQL_LECTURA_*`); los comandos
solo imprimen los nombres. Detalle en la [configuración de MySQL](../almacenamiento/mysql_configuracion.md).

Para cargar los resultados a MySQL y servirlos desde la API:
```powershell
.\.venv\Scripts\python.exe scripts\cargar_mysql.py --destino mysql
.\.venv\Scripts\python.exe scripts\panel\ejecutar_panel.py --almacenamiento mysql
```

## 3. Airflow desde el zip
Esta parte es la que antes no se podía hacer con solo el zip: faltaban la carpeta de Airflow, el compose original, su `.env` y el nombre exacto de la carpeta del proyecto. Ahora el compose adaptado viene dentro del repositorio
(`orquestacion/docker-compose.yaml`, con el aviso de la licencia Apache 2.0 y de dónde sale) y un script prepara todo.

1. **Preparar la carpeta de Airflow.** Queda junto a la del proyecto (una carpeta hermana, porque el compose monta `../<nombre del proyecto>`):
```powershell
.\.venv\Scripts\python.exe scripts\orquestacion\preparar_airflow.py                 # carpeta airflow-medallon, puerto 8080
.\.venv\Scripts\python.exe scripts\orquestacion\preparar_airflow.py --puerto 8082   # si el 8080 está ocupado
.\.venv\Scripts\python.exe scripts\orquestacion\preparar_airflow.py --verificar     # solo mira (no escribe nada)
```
   El script detecta el nombre de la carpeta del proyecto, crea `dags`, `logs`, `plugins` y `config`, copia el compose, el Dockerfile y `requirements-airflow.txt`, copia el DAG comprobando su sha256 y escribe el `.env`
   de Airflow **solo si no existe** (contraseña de la interfaz y `FERNET_KEY` aleatorias, `AIRFLOW_UID`, `PROYECTO_NOMBRE` y `AIRFLOW_PUERTO`). Si el `.env` ya existe no lo toca (con `--completar` agrega solo lo que falte;
   con `--regenerar` lo reescribe con valores nuevos). Nunca imprime un valor. Comprueba también que Docker responde, que el puerto está libre y que el `.env` del proyecto tiene las variables `MYSQL_DOCKER_*`.
2. **Construir y levantar** (desde la carpeta de Airflow, que el script indica; tarda ⟦BUILD_TIEMPO⟧):
```powershell
docker compose build
docker compose up airflow-init
docker compose up -d
```
3. **Comprobar:**
```powershell
docker compose ps
docker compose exec airflow-scheduler airflow dags list
docker compose exec airflow-scheduler airflow dags list-import-errors     # debe decir «No data found»
docker compose exec airflow-scheduler airflow dags unpause medallon_etl_sismo
docker compose exec airflow-scheduler airflow dags trigger medallon_etl_sismo
docker compose exec airflow-scheduler airflow dags list-runs medallon_etl_sismo
```
   La interfaz queda en `http://127.0.0.1:8080` (o el puerto elegido), con el usuario `airflow` y la contraseña de la variable `_AIRFLOW_WWW_USER_PASSWORD` del `.env` de Airflow. Las cuatro tareas del DAG
   (`validar_bronze`, `transformar_a_silver`, `integrar_a_gold`, `cargar_datawarehouse`) deben terminar en éxito en unos ⟦DAG_TIEMPO⟧ y, como la corrida ya estaba cargada, la carga dice «ya cargada» sin duplicar filas.
4. **Apagar:** `docker compose down` (conserva los volúmenes) o `docker compose down -v` (los borra).

Más sobre operación, registros y problemas en [operacion.md](../orquestacion/operacion.md#desde-el-zip).

## 4. phpMyAdmin (solo lectura)
```powershell
docker compose -f servicios\phpmyadmin\docker-compose.yaml up -d      # http://127.0.0.1:8081
docker compose -f servicios\phpmyadmin\docker-compose.yaml down
```
Se entra tecleando `sismo_lectura` y su contraseña (la variable `MYSQL_LECTURA_PASSWORD` del `.env`) en el formulario: el compose no guarda ningún usuario ni contraseña. Con esa cuenta MySQL rechaza cualquier escritura.
Qué mirar y qué no hace, en [phpmyadmin.md](../almacenamiento/phpmyadmin.md). Con otro puerto: `$env:PMA_PUERTO = "8091"` antes de levantarlo.

## 5. Cómo saber que el modo completo funciona
| Comprobación | Resultado esperado |
|---|---|
| `py -3.13 scripts\preparar_entorno.py --modo completo` | todo con ✓ |
| `.\.venv\Scripts\python.exe scripts\mysql\configurar_mysql.py --solo-verificar` | verificación correcta de los permisos de `sismo_etl` |
| `.\.venv\Scripts\python.exe scripts\mysql\verificar_mysql.py` | la batería sobre la base de prueba termina sin fallos |
| `.\.venv\Scripts\python.exe scripts\orquestacion\preparar_airflow.py --verificar` | todo con ✓ |
| `docker compose exec airflow-scheduler airflow dags list-import-errors` | «No data found» |
| una ejecución del DAG | las cuatro tareas en éxito |
| `http://127.0.0.1:8081` con `sismo_lectura` | se ven las siete tablas de `sismo_cali`; un `INSERT` o un `DROP` es rechazado por MySQL |

## 6. Alcance y límites
- **Qué afirmamos:** el modo completo se verificó en una máquina de desarrollo: Airflow se construyó y ejecutó con las cuatro tareas en éxito desde un zip descomprimido en una carpeta de otro nombre ([EV-087](../evidencias/servicios/EV-087_airflow_desde_el_zip.txt)),
  y phpMyAdmin mostró las tablas con la cuenta de solo lectura y rechazó una escritura ([EV-085](../evidencias/servicios/EV-085_phpmyadmin_en_vivo.txt)).
- **Qué NO demuestra:** que funcione en una máquina limpia de verdad (en la nuestra ya estaban Docker, MySQL y las imágenes), con 8 GB de RAM, con otro origen de conexión a MySQL (Docker en Linux nativo) ni que el DAG se ejecute a las 06:00 con el equipo apagado.
