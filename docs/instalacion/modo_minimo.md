# Modo mínimo: pipeline, API y panel con SQLite

**Componente:** Servicios locales · **Requisitos:** [Python 3.13 en paralelo](README.md#2-requisitos) y nada más · **Decisión:** [D93](../DECISIONES.md)

Este modo reproduce todo el análisis sin MySQL ni Docker. Lo separamos del completo porque la mayoría de las personas que reciben el proyecto solo quieren ver las cifras y el panel, y porque con SQLite
no hay contraseñas ni servicios que configurar. Todos los comandos son de PowerShell y se ejecutan en la raíz del proyecto (la carpeta que contiene `main.py`); usamos `.\.venv\Scripts\python.exe` en lugar de activar el
entorno porque así no depende de la política de ejecución de scripts de PowerShell.

## 1. Obtener el proyecto
- **Con el zip:** descomprimirlo en una carpeta de ruta corta (ver [la nota de rutas largas](README.md#2-requisitos)). El nombre de la carpeta es libre.
- **Con Git:** `git clone <dirección del repositorio> sismo` y entrar a esa carpeta.

## 2. Comprobar el equipo
```powershell
py -3.13 scripts\preparar_entorno.py
```
Si falta Python 3.13 imprime cómo instalarlo en paralelo. **Lo que debe decir depende del momento:** ahora, sin el entorno virtual, tiene que terminar con «Modo minimo: falta lo marcado con ✗» y código 1, con la línea de Python 3.13 en ✓ y las acciones sugeridas para el entorno y los requisitos (es lo esperado, no un error). Después del paso 3, al volver a ejecutarlo, debe terminar con «Modo minimo: todo lo necesario está listo» y código 0. Lo medimos desde un zip en una carpeta con espacios y tildes, siguiendo la guía de las sesiones: tardó menos de 1 s la primera vez y unos 3 s la segunda.

## 3. Crear el entorno e instalar
```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
```
`pip check` debe decir «No broken requirements found». En una máquina de desarrollo la instalación tardó unos 290 s (ver [tiempos](README.md#4-tiempos-y-memoria-medidos)).
Si PowerShell no deja activar el entorno (`Activate.ps1` está bloqueado por la política de ejecución) no hace falta activarlo con esta guía; ver [errores comunes](errores_comunes.md).
Con `py -3.13 scripts\preparar_entorno.py --instalar` se hacen estos dos pasos pidiendo confirmación.

## 4. Reproducir el pipeline
```powershell
.\.venv\Scripts\python.exe main.py --stage all
```
Con Bronze presente en `data/bronze` no necesita red: verifica los ocho sha256 del manifiesto, regenera Silver y Gold y deja las mismas cifras (5.146 construcciones, 346 barrios, 23 indicadores).
Para comprobar que los archivos son idénticos a los versionados se compara su sha256, como explica la [sección 12 del README](../../README.md#12-cómo-reproducir). Aunque los datos sean los mismos, `git status`
puede mostrar `data/gold/etl_sismo.db` como modificado: SQLite no escribe el archivo igual byte a byte en cada carga y lo que importa es el contenido de las tablas (D59).

## 5. API y panel
```powershell
.\.venv\Scripts\python.exe scripts\panel\ejecutar_panel.py
```
Arranca la API en `http://127.0.0.1:8000` y el panel en `http://127.0.0.1:8501` (si un puerto está ocupado elige otro libre y lo imprime) y los cierra a los dos con `Ctrl+C`. **El panel es la dirección que se abre en el navegador (`:8501`).** La API no tiene página en la raíz: `http://127.0.0.1:8000/` responde «404 No se encontró», que es lo normal; para comprobarla se abre `http://127.0.0.1:8000/health` (debe decir `"estado":"ok"`) o su documentación en `http://127.0.0.1:8000/docs`.
Para solo comprobar que arrancan: `.\.venv\Scripts\python.exe scripts\panel\ejecutar_panel.py --verificar` (imprime las dos direcciones y termina). Más detalle en la [guía de uso del panel](../panel/guia_de_uso.md).

## 6. Pruebas
```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```
Todas deben pasar; el número vigente y el resultado de cada una están en el [informe de pruebas](../validacion/informe_pruebas.md). Tardan unos 3 minutos y no necesitan red, MySQL ni Docker.

## 7. Cómo saber que el modo mínimo funciona
| Comprobación | Resultado esperado |
|---|---|
| `py -3.13 scripts\preparar_entorno.py` | todo con ✓ en el modo mínimo |
| `.\.venv\Scripts\python.exe main.py --stage all` | termina sin errores y repite las cifras de la sección 4 |
| `.\.venv\Scripts\python.exe scripts\panel\ejecutar_panel.py --verificar` | imprime la dirección de la API y la del panel y termina con código 0 |
| `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider` | todas las pruebas pasan |

## 8. Alcance y límites
- **Qué afirmamos:** estos pasos se ejecutaron con Python 3.13 en una carpeta con espacios y tildes, sin variables de UTF-8 y con el entorno creado desde cero: la prueba que fallaba por la codificación pasó ([EV-084](../evidencias/servicios/EV-084_suite_sin_utf8_despues.txt)) y la suite completa pasó en un clon equivalente (EV-089).
- **Qué NO demuestra:** que funcione con otra versión de Python, en una máquina de 8 GB o sin los datos de Bronze que vienen en el zip.
