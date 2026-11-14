# Configuración de MySQL para el proyecto

**Componente:** Carga relacional · **Script:** `scripts/mysql/configurar_mysql.py` · **Ítems del checklist:** 4.1 (almacén relacional) y 2.3 (credenciales)

Este documento explica qué hace el script que prepara MySQL, cómo se ejecuta, qué permisos recibe el usuario del proyecto y por qué. Lo ejecuta una persona del equipo en su propio equipo, porque la contraseña del administrador de MySQL solo la conoce el equipo y no pasa por ningún archivo, argumento ni herramienta del repositorio.

## 1. Qué crea
| Objeto | Nombre | Para qué |
|---|---|---|
| Base de datos | `sismo_cali` | datos reales de la carga relacional |
| Base de datos | `sismo_cali_prueba` | verificaciones que reconstruyen tablas (esquema desde cero, fallos inyectados, restauración); nunca se usan en la base real |
| Usuario | `sismo_etl`@`localhost` | único usuario del proyecto; solo acepta conexiones desde este equipo |
| Variables en `.env` | `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`, `MYSQL_DATABASE_PRUEBA` | las lee `src/load/conexion.py`; los valores no se versionan |

Las bases se crean con `utf8mb4` y el cotejamiento `utf8mb4_0900_ai_ci`, igual que las tablas de `src/load/sql/esquema_mysql.sql`.

## 2. Cómo ejecutarlo
Con el servicio **MySQL80** activo, en una terminal PowerShell nueva, en la raíz del proyecto:

```powershell
.\.venv\Scripts\python.exe scripts\mysql\configurar_mysql.py
```

1. El script pide la contraseña del administrador (`root` por defecto; otro usuario con `--usuario-admin`). Se escribe sin que se vea: usa `getpass`.
2. Comprueba que el servidor sea MySQL 8.0 o superior y registra la versión y el juego de caracteres.
3. Crea las dos bases y el usuario con una contraseña de 32 caracteres generada con `secrets` (mayúsculas, minúsculas, dígitos y símbolos seguros para `.env` y para SQL).
4. Abre una conexión **con el usuario nuevo** y revisa con `SHOW GRANTS` que sus permisos sean exactamente los de la sección 3.
5. Solo si esa verificación pasa, escribe las variables en `.env` de forma atómica (archivo temporal y reemplazo), conservando las demás líneas. Si algo falla antes, `.env` queda como estaba.
6. Imprime los **nombres** de las variables escritas y termina con «Listo». Nunca imprime valores.

El script es idempotente: si el usuario ya existe y las credenciales de `.env` funcionan, no cambia nada y ni siquiera pide la contraseña del administrador. Con `--solo-verificar` comprueba las credenciales de `.env` sin modificar nada.

## 3. Privilegios del usuario y por qué
```sql
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, INDEX, REFERENCES ON `sismo_cali`.*        TO 'sismo_etl'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, INDEX, REFERENCES ON `sismo_cali_prueba`.* TO 'sismo_etl'@'localhost';
```
| Privilegio | Por qué lo necesitamos |
|---|---|
| `SELECT` | leer para conciliar y para que la API sirva los datos (con sesión de solo lectura) |
| `INSERT` | cargar las corridas |
| `UPDATE`, `DELETE` | mantenimiento y pruebas en la base de prueba; la carga normal no actualiza ni borra |
| `CREATE`, `ALTER`, `INDEX`, `REFERENCES` | crear el esquema con sus índices y claves foráneas |
| `DROP` | reconstruir la base de prueba desde cero en cada verificación |

Lo que **no** recibe, y el script lo comprueba: privilegios globales (`*.*` solo con `USAGE`), `GRANT OPTION`, permisos sobre otras bases y ningún usuario con host `'%'`. No usa `LOAD DATA LOCAL`: la conexión se abre con `local_infile` desactivado.

Límite que aceptamos: con `DROP` el usuario podría borrar las dos bases del proyecto. Lo cubre el respaldo lógico (`scripts/mysql/respaldar_restaurar.py`) y que el usuario no existe fuera de este equipo.

## 4. La contraseña del administrador
- Se pide solo con `getpass`: no se acepta por argumento, variable de entorno ni archivo.
- No se guarda, no se registra y no se envía a ninguna herramienta del repositorio; el script la descarta en cuanto abre la conexión.
- Quienes colaboran con el código del proyecto nunca la ven ni la reciben: si necesitamos que alguien ejecute el script, lo hace quien la conoce, en su terminal.

## 5. Rotación
```powershell
.\.venv\Scripts\python.exe scripts\mysql\configurar_mysql.py --rotar
```
Pide de nuevo la contraseña del administrador, cambia la del usuario con `ALTER USER`, verifica la conexión con la nueva y actualiza `.env`. La rotamos al terminar el proyecto y cuando salga una persona con acceso al `.env`.

## 5 bis. Usuario para el DAG de Airflow en Docker
El DAG de [orquestación](../orquestacion/README.md) corre dentro de un contenedor, y MySQL ve esa conexión como proveniente de otro origen que `localhost`. Por eso existe un segundo usuario, `sismo_airflow`, que se crea con el mismo script y **nunca con `%`**:

```powershell
.\.venv\Scripts\python.exe scripts\mysql\configurar_mysql.py --usuario-docker --origen <PATRÓN>
```
- **Origen (`<PATRÓN>`):** una IP privada exacta, un nombre exacto o una red con máscara privada de al menos 16 bits (por ejemplo `192.168.65.0/255.255.255.0`). El script rechaza vacío, `%`, `_`, comodines, IP públicas, `0.0.0.0`, loopback y máscaras más anchas que 16 bits.
- **Permisos:** solo sobre `sismo_cali`: `SELECT` (leer la corrida), `INSERT` (cargarla) y `CREATE`, `INDEX` y `REFERENCES` (el esquema se aplica con `CREATE TABLE IF NOT EXISTS`, con sus índices y claves foráneas). Sin `UPDATE`, `DELETE`, `DROP` ni `ALTER`, sin `GRANT OPTION` y sin privilegios globales: el DAG no modifica ni borra datos.
- **Credenciales:** contraseña aleatoria de 32 caracteres que solo se guarda en `.env` (`MYSQL_DOCKER_USER`, `MYSQL_DOCKER_PASSWORD` y `MYSQL_DOCKER_ORIGEN`; el script imprime nombres, nunca valores). La contraseña del administrador se pide con `getpass`, como siempre.
- **Verificación:** este usuario no puede probarse desde Windows (su origen es el contenedor); `--solo-verificar` inspecciona sus permisos con la cuenta de administrador y el `.env` solo se escribe después de comprobarlos. Es idempotente y admite `--rotar`.
- **Uso en el DAG:** la tarea de carga lee esas variables del `.env` del proyecto (montado en solo lectura) en memoria y las pasa por `os.environ` de la tarea; nunca se copian a la copia de trabajo, a la imagen, al compose ni a los registros.

## 6. Si algo falla
| Síntoma | Causa probable | Qué hacemos |
|---|---|---|
| «el servicio MySQL no responde» | MySQL80 detenido o puerto distinto | iniciar el servicio (`Get-Service MySQL80`) o corregir `almacenamiento.puerto` en `config/config.yaml` |
| «autenticación fallida» | contraseña del administrador incorrecta | volver a ejecutar el script y escribirla de nuevo |
| «permisos insuficientes» | el administrador indicado no puede crear usuarios | usar otro administrador con `--usuario-admin` |
| «se necesita MySQL 8.0 o superior» | servidor anterior | instalar 8.0 (ver `docs/proyecto/entorno.md`) |
| «.env no está ignorado por git» | falta la regla en `.gitignore` | corregir `.gitignore` antes de guardar credenciales |
| `--solo-verificar` falla | `.env` sin credenciales o contraseña cambiada | ejecutar sin `--solo-verificar` o con `--rotar` |

## 7. Revocar el acceso (documentado, no ejecutado)
Si hay que retirar el usuario del proyecto, el administrador ejecuta en su cliente de MySQL:

```sql
DROP USER 'sismo_etl'@'localhost';
-- opcional, solo si también se descartan los datos:
-- DROP DATABASE sismo_cali_prueba;
-- DROP DATABASE sismo_cali;
```
Después se borran las variables `MYSQL_*` del `.env`. Estas sentencias no las ejecuta ningún script del repositorio.

## 8. Regla de oro
**La contraseña de MySQL no viaja por chat, no entra al repositorio y no se escribe en notebooks, registros ni capturas.** Vive en un solo lugar, `.env`, y el escáner de secretos la busca activamente en el árbol, el historial y el zip (`escanear_secretos.py --canario-env`) sin imprimirla. Ver [gestión de credenciales](../seguridad/gestion_credenciales.md).
