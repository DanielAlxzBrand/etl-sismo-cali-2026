# Entorno de la Entrega 3

**Fecha de la revisión:** 2026-11-12 · Solo lectura: no se instaló nada ni se arrancó ningún servicio, y no se probó ninguna credencial. Los comandos y sus salidas están en `docs/entrega_3/evidencias/f0/EV-006_entorno.txt`. [Evidencia en el repo: `docs/entrega_3/evidencias/f0/EV-006_entorno.txt`]

## 1. Lo que hay
| elemento | estado | detalle |
|---|---|---|
| Python | instalado | 3.13.0; el lanzador `py` también lista 3.11. El `.venv` del proyecto usa 3.13.0. |
| Paquetes del `.venv` | instalados | pandas 3.0.6, numpy 2.5.4, requests 2.34.2, httpx 0.28.1, pytest 9.1.1, shapely 2.2.0, matplotlib 3.11.2, openpyxl 3.1.5, python-dotenv 1.2.4 |
| Solo en el Python global (no en el `.venv` ni en `requirements.txt`) | instalados | fastapi 0.116.2, uvicorn 0.35.0, streamlit 1.58.0, SQLAlchemy 2.0.51 (no se usará), pydantic 2.11.9, plotly 6.8.0, PyMuPDF 1.28.0 (además de pandas 2.2.3 y pytest 8.4.1, con versiones distintas a las del `.venv`) |
| No instalados en ninguno | faltan | PyMySQL (o `mysql-connector-python`), `python-docx` |
| Windows | Windows 10 Home Single Language según el sistema, compilación 26300, 64 bits | Edición Home: no incluye Hyper-V completo, pero WSL2 y Docker Desktop con el motor WSL2 sí funcionan en Home. |
| Virtualización | hipervisor presente | `HypervisorPresent` verdadero; el firmware no reporta los requisitos de Hyper-V porque ya hay un hipervisor en uso. |
| RAM | 15,7 GB en total; 3,7 GB libres en el momento de la revisión | El compose oficial de Airflow advierte con menos de 4 GB disponibles. |
| Disco | 210,9 GB libres en `C:` | Suficiente. |
| WSL | característica presente, versión predeterminada 2; **sin ninguna distribución instalada** | `wsl -l -v` informa que no hay distribuciones. |
| Docker | **no instalado** | `docker --version` no existe. |
| MySQL | servidor **instalado y en ejecución** | Servicio `MySQL80` (inicio automático), MySQL Server 8.0.45, puerto 3306 según `my.ini`; una conexión TCP a `localhost:3306` se acepta (sin autenticación). Cliente `mysql.exe` 8.0.45 presente en `C:\Program Files\MySQL\MySQL Server 8.0\bin`, **fuera de la variable PATH** (`where mysql` no lo encuentra). MySQL Workbench 8.0 instalado. **Usuario, contraseña y base: no verificados.** |
| Node / npm | instalados | 24.14.0 / 11.9.0 (no se necesitan) |
| Navegadores | Chrome 157.0.8103.52 y Edge 157.0.4341.46 | Para las capturas del dashboard. |
| Grabación | OBS Studio 32.2.2 | Para el video de la demostración; ffmpeg no está instalado. |
| Documentos | Word (Office 16) instalado; LibreOffice no | Word sirve para revisar y renderizar el .docx. |
| PowerShell | Windows PowerShell 5.1 | `pwsh` 7 no está instalado; los scripts se escriben para 5.1. |
| Variables en `.env` | ninguna | El archivo existe y está vacío (0 bytes). `.env.example` declara los nombres `SOCRATA_APP_TOKEN` y `HTTP_USER_AGENT`. |
| Puertos de trabajo | 8000, 8501, 8080 y 5432 sin nada escuchando; 3306 ocupado por MySQL | Verificado con pruebas de conexión TCP a `localhost` (sin autenticación). |

## 2. Implicaciones para F2 a F8
| fase | qué falta | vía de instalación y comando exacto | administrador, reinicio o credenciales |
|---|---|---|---|
| F2 | FastAPI, Uvicorn y httpx en el `.venv` (hoy solo en el Python global; SQLAlchemy ya no se usa, ver D-E3-14) | `.\.venv\Scripts\python.exe -m pip install fastapi uvicorn httpx` y añadirlos a `requirements.txt` con versiones fijas | No necesita administrador ni credenciales. |
| F3 | Driver de MySQL; usuario y base de datos de proyecto | `.\.venv\Scripts\python.exe -m pip install pymysql cryptography`. Para crear la base: `$env:Path += ';C:\Program Files\MySQL\MySQL Server 8.0\bin'` y `mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS etl_sismo CHARACTER SET utf8mb4; CREATE USER IF NOT EXISTS 'etl'@'localhost' IDENTIFIED BY '<definir>'; GRANT ALL ON etl_sismo.* TO 'etl'@'localhost';"` | **Credenciales:** hace falta la contraseña del administrador de MySQL local (no consta); la del usuario `etl` se define y se guarda solo en una variable de entorno de sesión. No requiere administrador de Windows ni reinicio. |
| F4 | Distribución de WSL2 para Airflow (o Docker) | `wsl --install -d Ubuntu`; dentro de Ubuntu, un entorno virtual e instalación de Airflow con el archivo de restricciones del release que se fije en F4 (`pip install "apache-airflow==<versión>" --constraint <archivo de restricciones>`). Alternativa: `winget install -e --id Docker.DockerDesktop` y la imagen oficial de Airflow. | **PowerShell como administrador** y **posible reinicio**; hay que crear un usuario y contraseña de Linux (los define el equipo). La instalación necesita red y varios GB de descarga. |
| F4 | `pytest-cov` si se mide cobertura | `.\.venv\Scripts\python.exe -m pip install pytest-cov` | No necesita administrador. |
| F5 | Streamlit y Plotly en el `.venv` | `.\.venv\Scripts\python.exe -m pip install streamlit plotly` y añadirlos a `requirements.txt` | No necesita administrador. |
| F6 | Nada que instalar | Los materiales de usuarios y el análisis de costos son archivos. | Requiere hechos externos (personas), no instalaciones. |
| F7 | Nada obligatorio; OBS ya está instalado | La demostración se graba con OBS (lo hace el equipo). | — |
| F8 | `python-docx` para rellenar el checklist | `.\.venv\Scripts\python.exe -m pip install python-docx` (o el entorno de `guia_equipo`) | No necesita administrador. |

Consideraciones transversales: la RAM libre actual (3,7 GB) queda justa para WSL2 con Airflow; conviene cerrar aplicaciones antes de F4. Todas las instalaciones se hacen solo con aprobación del equipo y nunca sobre el Python global.
