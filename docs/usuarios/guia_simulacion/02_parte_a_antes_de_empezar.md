{{para: todos}}
{{sin-salto}}
# Parte A · Antes de empezar

Esta parte lleva su equipo desde el zip hasta el proyecto funcionando. Tarda unos 30 minutos y casi todos son de espera, así que conviene hacerla **días antes de su sesión**. Todos los comandos son de PowerShell. Lo que falle aquí **no es una fricción del panel**: no se anota como tal.

## A1. Qué necesita su equipo
{{incluir: docs/instalacion/README.md#2-requisitos | filas: Windows 11; Python 3.13; Git}}

Además de lo anterior, necesita:
| Qué | Cuánto o cómo | Origen |
|---|---|---|
| Memoria (RAM) | 8 GB o más. El panel en reposo ocupa unos 160 MiB y la suite de pruebas llegó a 319 MiB como mayor pico entre `pytest` y sus procesos hijos, sin contar Windows ni el navegador | `docs/instalacion/README.md`, sección 4 |
| Espacio libre | unos 700 MB: el zip pesa 21,3 MB, el proyecto descomprimido 34 MB y el entorno virtual 632 MB | los medimos nosotros en la prueba de esta guía |
| Navegador | Edge o Chrome | — |
| Internet | solo mientras se instalan los paquetes del paso A5 | `pip` los descarga |
| Carpeta | nueva, de ruta corta y **fuera de OneDrive** (su ruta no debe pasar por una carpeta llamada OneDrive) | los archivos sincronizados se bloquean y se retrasan |

Para saber qué versiones de Python tiene instaladas:
```powershell
py -0p
```
Debe listar `3.13`. Si no la lista, instale Python 3.13 desde python.org **en paralelo**, marcando «py launcher»; no desinstale la versión que ya tenga.

## A2. Verifique el zip
Quien le mandó el zip le mandó también su **sha256**. Compárelo con el que calcula su equipo:
```powershell
Get-FileHash -Algorithm SHA256 "<ruta del zip>"
```
Las dos cadenas deben ser idénticas; `Get-FileHash` las escribe en mayúsculas y quien manda el zip puede escribirlas en minúsculas, así que **compárelas sin distinguir mayúsculas de minúsculas**. Si no coinciden, **no descomprima** el zip y pida que se lo manden de nuevo: el archivo llegó incompleto o cambiado.

## A3. Descomprima el zip
```powershell
Expand-Archive -Path "<ruta del zip>" -DestinationPath "<carpeta del proyecto>"
cd "<carpeta del proyecto>"
```
Use una carpeta nueva. En nuestra prueba tardó 18,5 s. A partir de aquí todos los comandos se escriben **dentro de esa carpeta**, la que contiene `main.py`. Si el nombre tiene espacios, déjelo entre comillas dobles.

## A4. Compruebe el equipo
{{incluir: docs/instalacion/modo_minimo.md#2-comprobar-el-equipo}}

## A5. Cree el entorno e instale los paquetes
{{incluir: docs/instalacion/modo_minimo.md#3-crear-el-entorno-e-instalar}}

Tiempos que medimos para esta guía, desde un zip en una carpeta con espacios y tildes, en un equipo con Windows 11 y 15,7 GB de RAM: descomprimir 18,5 s, crear el entorno 14,7 s, instalar los paquetes 275,2 s (unos 5 minutos) y `pip check` 5,9 s. **En su equipo cambiarán**, sobre todo la instalación, que depende de su conexión.

## A6. Compruebe que todo funciona (cinco comandos)
Ejecútelos en este orden. Después de cada uno escriba `$LASTEXITCODE`: debe decir `0`.
| Nº | Comando | Qué debe pasar | Tiempo medido |
|---|---|---|---|
| 1 | `py -3.13 scripts\preparar_entorno.py` | termina con «Modo minimo: todo lo necesario está listo» | 2,8 s |
| 2 | `.\.venv\Scripts\python.exe main.py --stage all` | termina sin errores; con los datos que trae el zip no necesita internet | 8,4 s |
| 3 | el de la comprobación de huellas, justo abajo | nueve líneas que dicen «igual» | 0,2 s |
| 4 | `.\.venv\Scripts\python.exe scripts\panel\ejecutar_panel.py --verificar` | imprime la dirección de la API y la del panel y termina | 7,4 s |
| 5 | `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider` | todas las pruebas pasan, una se omite (la del historial de Git: el zip no trae `.git`) y termina sin fallos | 212,3 s (unos 3,5 minutos) |

**Comando 3: comprobación de huellas.** Compara los nueve archivos que genera el pipeline con las huellas que trae el proyecto. Si alguno dice «DISTINTO», no siga y avise.
```powershell
Get-Content docs\validacion\sha256_despues_logging.txt | ForEach-Object { $h, $r = $_ -split ' \*', 2; $r = $r -replace '/', '\'; if ((Get-FileHash -Algorithm SHA256 $r).Hash.ToLower() -eq $h) { "igual    $r" } else { "DISTINTO $r" } }
```
El comando 5 es el más largo y el que menos hace falta para la sesión: córralo si tiene tiempo, porque comprueba todo el proyecto. Con Git instalado se omite esa una; **sin Git se omiten 10**, con su motivo a la vista: es lo esperado (`docs/instalacion/README.md`, sección 3.1).

## A7. Si algo falla
Busque su síntoma en estas tablas. Lo marcado con «(visto)» lo reprodujimos nosotros; lo demás lo deducimos de cómo funciona Windows y **no lo probamos**.

### Instalación y Python
{{incluir: docs/instalacion/errores_comunes.md#1-instalación-y-python}}

### Consola, codificación y rutas
{{incluir: docs/instalacion/errores_comunes.md#2-consola-codificación-y-rutas}}

### Puertos
{{incluir: docs/instalacion/errores_comunes.md#3-puertos-y-servicios | filas: El panel o la API dicen que el puerto está ocupado}}

Si el síntoma no está en las tablas, copie el mensaje de error completo y **recorte la captura** para que no se vea el nombre de su usuario de Windows en la ruta que aparece antes del cursor: ese nombre no debe llegar al proyecto.
