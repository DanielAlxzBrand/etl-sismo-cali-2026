# Errores comunes al instalar y ejecutar

**Componente:** Servicios locales · **Decisiones:** [D91 a D94](../DECISIONES.md)

Esta tabla reúne los fallos que encontramos al preparar el proyecto en otro equipo o que esperamos que aparezcan en los de las otras personas del grupo. La armamos porque casi todos tienen una causa conocida y
una solución de una línea, y porque «no funciona» sin el mensaje no sirve para ayudar. Los marcados con (visto) los reprodujimos nosotros; los demás los deducimos de cómo funcionan Windows, Docker y MySQL y **no los probamos**.

## 1. Instalación y Python
| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| `py -3.13` dice «No suitable Python runtime found» | Python 3.13 no está instalado, o se instaló sin el lanzador `py` | Instalar Python 3.13 desde python.org **en paralelo** marcando «py launcher»; comprobar con `py -0p` |
| El proyecto «funciona raro» o `pip` falla con paquetes de otra versión | se creó el entorno con `py -3` o `python`, que toman la versión más nueva (por ejemplo 3.14) y no la 3.13 | Borrar `.venv` y crearlo con `py -3.13 -m venv .venv`; `py -3.13 scripts\preparar_entorno.py` lo detecta |
| `pip install` termina con «No matching distribution found» para numpy o pandas | Python distinto de 3.13 (numpy 2.5.4 exige 3.12 o más; otras versiones no se probaron) | Usar un entorno de Python 3.13 |
| `.\.venv\Scripts\Activate.ps1 : ... no se puede cargar porque la ejecución de scripts está deshabilitada` | la política de ejecución de PowerShell (`ExecutionPolicy`) bloquea los scripts | No activar el entorno: usar `.\.venv\Scripts\python.exe` como en esta guía; o, solo para esa ventana, `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` |
| `git clone` o la descompresión terminan con «Filename too long» (visto) | la ruta completa pasa de 260 caracteres; el archivo más largo del repositorio tiene 130 de ruta relativa | Usar una carpeta de ruta corta (menos de unos 120 caracteres) o `git config --global core.longpaths true` antes de clonar |
| La instalación tarda mucho o se corta | conexión lenta o inestable | Repetir `pip install -r requirements.txt`: reutiliza lo ya descargado. Tardó unos 290 s en nuestra máquina |

## 2. Consola, codificación y rutas
| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| `UnicodeEncodeError` o letras raras (`Ã³`, `�`) al imprimir | la consola usa cp1252 u otra codificación y no UTF-8 (visto en una prueba que leía la salida de otro proceso) | Los scripts nuevos reemplazan lo que no cabe; para el resto, `$env:PYTHONUTF8 = "1"` en esa ventana antes de ejecutar |
| Una prueba falla solo en otro equipo con `TypeError: argument of type 'NoneType'` (visto) | lectura de un subproceso con una codificación distinta de la que escribió | Ya corregido en `tests/` (D92); si reaparece en otra prueba, avisar con el nombre de la prueba |
| Un comando falla con rutas que tienen espacios | falta entrecomillar la ruta | Entre comillas dobles: `cd "C:\carpeta con espacios\proyecto"`; los scripts del proyecto sí las admiten (probado con «Prueba con espacios y tildes ñ») |

## 3. Puertos y servicios
| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| El panel o la API dicen que el puerto está ocupado | otro programa usa el 8000 o el 8501 | El lanzador del panel elige otro libre y lo imprime; para ver quién usa uno: `Get-NetTCPConnection -LocalPort 8501` |
| `preparar_airflow.py` dice «el puerto 8080 está ocupado; pruebe con --puerto 8082» | otro programa (o un Airflow que ya está encendido) usa el 8080 | Repetir con `--puerto 8082`, o apagar lo que lo usa |
| phpMyAdmin no abre en `127.0.0.1:8081` | el 8081 está ocupado o el contenedor no arrancó | `$env:PMA_PUERTO = "8091"` y volver a levantarlo; `docker compose -f servicios\phpmyadmin\docker-compose.yaml ps` |
| `docker: error during connect` o «Docker está instalado pero no responde» | Docker Desktop está apagado, en pausa o arrancando | Encender Docker Desktop y esperar a que diga «Engine running»; `docker version` debe responder |
| `docker compose` no existe | Docker Desktop antiguo | Actualizar Docker Desktop |
| La interfaz de Airflow tarda o los contenedores se reinician | falta de memoria | Ver la [advertencia para 8 GB](README.md#4-tiempos-y-memoria-medidos): apagar el panel, limitar WSL2 con `.wslconfig` |
| El DAG falla en `cargar_datawarehouse` al conectar | MySQL apagado, o falta la cuenta `sismo_airflow`, o el origen no coincide | Iniciar `MySQL80`; ejecutar `configurar_mysql.py --usuario-docker --origen localhost`; `preparar_airflow.py --verificar` dice qué variables faltan (solo nombres) |

## 4. MySQL y contraseñas
| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| `configurar_mysql.py` dice «el servicio MySQL no responde en el puerto indicado» | el servicio `MySQL80` está detenido | Iniciarlo: `Start-Service MySQL80` en PowerShell de administrador, o desde «Servicios» de Windows |
| «autenticación fallida (usuario o contraseña incorrectos)» | se tecleó mal la contraseña de `root` | Repetir el comando y teclearla de nuevo (no se muestra al escribir). Si no se conoce, la tiene que restablecer quien administra MySQL: **el proyecto no la guarda ni la recupera** |
| «permisos insuficientes para esta operación» | el usuario indicado con `--usuario-admin` no puede crear usuarios | Usar `root` u otro administrador |
| «`.env` no está ignorado por git o está versionado» | falta `.gitignore` o el archivo se agregó a Git | Corregir `.gitignore` y quitar `.env` del índice con `git rm --cached .env` antes de repetir |
| phpMyAdmin dice «Access denied» | usuario o contraseña mal tecleados, o la cuenta `sismo_lectura` no existe | Verificar con `configurar_mysql.py --usuario-lectura --solo-verificar`; la contraseña es la variable `MYSQL_LECTURA_PASSWORD` del `.env` |
| `docker compose` avisa «Falta FERNET_KEY» o «Falta PROYECTO_NOMBRE» | el `.env` de Airflow existe pero es de antes de este compose | `preparar_airflow.py --completar` agrega las variables que faltan sin cambiar las demás |
| `PROYECTO_NOMBRE no coincide con la carpeta del proyecto` | se renombró la carpeta del proyecto después de preparar Airflow | `preparar_airflow.py --regenerar` (reescribe el `.env` de Airflow con valores nuevos) o editar esa variable |

## 5. Alcance y límites
- **Qué afirmamos:** cada fila dice qué vimos o qué esperamos; los que no marcan «(visto)» son suposiciones razonadas.
- **Qué NO demuestra:** que estos sean todos los errores posibles ni que las soluciones funcionen en todos los equipos.
