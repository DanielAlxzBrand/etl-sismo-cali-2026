# Guía de instalación del proyecto

**Componente:** Servicios locales · **Ítems del checklist:** 7.1 (documentación y código ejecutable), 4.1 y 4.2 (almacén relacional), 5.4 (orquestación) · **Decisiones:** [D91 a D94](../DECISIONES.md)

Esta guía explica cómo ejecutar el proyecto en un equipo nuevo con Windows 11. La escribimos porque hasta ahora solo funcionaba en el equipo donde se desarrolló: un tercero que recibe el zip no tiene la carpeta de Airflow,
ni su archivo de configuración, ni el nombre exacto de la carpeta del proyecto, y las otras dos personas del grupo tienen un Python más reciente que el que usamos. Cada paso se probó en una ejecución real y los tiempos
y consumos de memoria son de **una sola máquina**, no una garantía.

## 1. Qué modo elegir
| | **Modo mínimo** | **Modo completo** |
|---|---|---|
| Qué se ejecuta | el pipeline (Bronze, Silver, Gold), la API y el panel, con SQLite | lo del mínimo, más MySQL, Airflow y phpMyAdmin |
| Qué se instala | Python 3.13 y `requirements.txt` | además MySQL 8, Docker Desktop con WSL2 y las imágenes de Docker |
| Contraseñas | ninguna | la de `root` de MySQL (la teclea la persona) y las que genera el proyecto en `.env` |
| Guía | [modo_minimo.md](modo_minimo.md) | [modo_completo.md](modo_completo.md) |
| Sirve para | reproducir las cifras, mirar el panel y correr las pruebas | ver la carga relacional, el DAG programado y las tablas en el navegador |

Si solo se quiere reproducir el análisis, el modo mínimo basta: el modo completo agrega servicios que no cambian ninguna cifra.

## 2. Requisitos
| Requisito | Para qué | Cómo comprobarlo |
|---|---|---|
| Windows 11 | es el sistema donde se probó todo; en otros no lo probamos | — |
| **Python 3.13**, instalado **en paralelo** | es la única versión soportada: las versiones de `requirements.txt` (por ejemplo pandas 3.0.6 y numpy 2.5.4) se fijaron con ella y con otra las salidas pueden cambiar | `py -0p` debe listar `3.13` |
| Git (opcional) | clonar el repositorio; con el zip no hace falta, pero varias pruebas lo usan en repositorios temporales y, si falta, se omiten 10 con su motivo visible (ver la sección 3.1) | `git --version` |
| MySQL 8.0 o superior (solo modo completo) | la carga relacional | el servicio `MySQL80` en ejecución |
| Docker Desktop con WSL2 (solo modo completo) | Airflow y phpMyAdmin | `docker version` y `docker compose version` |
| Memoria | ver la sección 4 | — |

**Python 3.13 en paralelo.** Si el equipo ya tiene una versión más nueva (por ejemplo 3.14), no hay que desinstalarla: se instala la 3.13 desde python.org marcando «py launcher» y se usa siempre con `py -3.13`.
Lo hacemos así porque `py -3.13` elige la versión sin tocar el `PATH` ni el resto de programas que usen la otra. Esto no prueba que el proyecto funcione con 3.14: no lo probamos.

**Ruta de la carpeta.** Debe tener menos de unos 120 caracteres: el archivo más largo del repositorio tiene 130 caracteres de ruta relativa y Windows corta las rutas completas en 260. Con una ruta más larga,
`git clone` o la descompresión terminan con «Filename too long» (lo vimos en [EV-083](../evidencias/servicios/EV-083_suite_sin_utf8_antes.txt)). Si no queda más remedio, se puede activar `git config --global core.longpaths true`
antes de clonar. Los espacios y las tildes en el nombre de la carpeta no dan problema (probamos con «Prueba con espacios y tildes ñ»).

## 3. Comprobar el entorno antes de empezar
```powershell
py -3.13 scripts\preparar_entorno.py                  # diagnóstico de solo lectura, modo mínimo
py -3.13 scripts\preparar_entorno.py --modo completo  # además MySQL, Docker y los puertos de Airflow y phpMyAdmin
py -3.13 scripts\preparar_entorno.py --instalar       # crea .venv e instala requirements.txt (pide confirmación)
```
El script imprime ✓ o ✗ por cada cosa y, si falta algo, la acción sugerida. Sin `--instalar` no escribe nada y nunca muestra un valor del `.env`, solo los nombres de variables que faltan.
Se puede ejecutar con cualquier Python porque solo usa la biblioteca estándar y `python-dotenv`; si todavía no hay entorno, usar `--instalar` ya lo crea.

### 3.1 Pruebas omitidas esperadas
La suite completa no omite ninguna prueba en un clon con Git instalado. En el zip descomprimido hay dos casos que medimos armando el zip con `make_dist.empaquetar`, descomprimiéndolo en una carpeta temporal sin `.git` y corriendo las pruebas que usan git (misma máquina, con y sin git en el `PATH`):
| Dónde se ejecuta | Omitidas | Cuáles y por qué |
|---|---|---|
| clon con Git | 0 | — |
| zip descomprimido, con Git instalado | **1** | `test_sin_hallazgos_en_el_historial_de_git`: el zip no trae el historial, así que no hay nada que revisar; se omite con su motivo a la vista en lugar de pasar vacía |
| zip descomprimido, sin Git (o clon sin Git) | **10** | la anterior, 8 que arman un repositorio temporal para comprobar el `.gitignore` y el escáner de secretos y necesitan el binario `git` (`test_env_no_esta_versionado`, `test_el_env_real_esta_ignorado_y_no_versionado`, 5 de `tests/test_configurar_mysql.py` y 1 de `tests/test_canario_extra.py`) y la que arma el zip y corre las demás (`test_las_pruebas_que_usan_git_pasan_en_el_zip_descomprimido_sin_git_y_omiten_solo_una`), que también necesita el binario |
Ninguna de las demás pruebas usa git. Las tres cifras se midieron de nuevo con la suite actual (1007 pruebas) en [EV-096](../evidencias/auditoria/EV-096_independencia_repetida_y_omisiones.txt): 0, 1 y 10; `tests/test_independencia_del_repositorio.py` comprueba que este documento y el motivo de la omisión dicen el mismo número. Esto no demuestra que la suite pase en otro equipo, solo cuántas pruebas se omiten por no tener historial o binario de git y por qué.

## 4. Tiempos y memoria medidos
Todas las cifras son de una máquina de desarrollo con Windows 11 y 15,7 GB de RAM; **en otro equipo cambiarán**.

| Qué | Valor | Origen |
|---|---|---|
| Crear el entorno e instalar `requirements.txt` desde cero | 288 y 290 s (unos 5 minutos) | [EV-083](../evidencias/servicios/EV-083_suite_sin_utf8_antes.txt) y [EV-062](../evidencias/endurecimiento/EV-062_instalacion_desde_cero.txt); depende de la conexión |
| Pipeline completo (`main.py --stage all`) | 3,4 s y 148 MB de pico | [recursos_medidos.csv](../finanzas/recursos_medidos.csv) |
| Suite de pruebas (sin cobertura), solo el proceso de `pytest` | 227 s (unos 4 minutos) y un pico de **286 MiB**, con 959 pruebas | [recursos_medidos.csv](../finanzas/recursos_medidos.csv) (fila `memoria_pico_suite_de_pruebas`) |
| Suite de pruebas, `pytest` y todos los procesos que arranca (medida con `scripts/evidencias/medir_memoria_suite.py`) | 323 s y un pico máximo de **319 MiB**, con 1007 pruebas | [EV-097](../evidencias/auditoria/EV-097_memoria_de_la_suite.txt) |
| API y panel en reposo (sin ninguna página abierta) | unos 160 MiB entre los procesos de Python del lanzador | [recursos_medidos.csv](../finanzas/recursos_medidos.csv) (fila `memoria_api_mas_panel_en_reposo`) |
| Airflow en reposo (seis contenedores) | 1.970 MiB | [recursos_medidos.csv](../finanzas/recursos_medidos.csv) (fila `memoria_en_reposo_total_contenedores_de_airflow`) |
| phpMyAdmin en reposo | 33 MiB | [recursos_medidos.csv](../finanzas/recursos_medidos.csv) (fila `memoria_en_reposo_phpmyadmin`) |

**Dos picos de memoria de la suite, y cuál usamos.** Los 286 MiB miran solo al proceso de `pytest`; los 319 MiB son el mayor pico entre `pytest` y los procesos que las pruebas arrancan (la API y el panel de las pruebas de integración), con otra cantidad de pruebas y otro método, así que no se restan ni se comparan. **Para planear la memoria de un equipo usamos los 319 MiB**, porque es lo que una persona que corre la suite necesita de verdad; los 286 MiB quedan como referencia de la medición anterior.

**Advertencia para 8 GB de RAM.** Con 8 GB no conviene encender todo a la vez: Windows y el navegador ya usan buena parte, WSL2 reserva por defecto la mitad de la memoria para Docker y Airflow ocupa cerca de 2 GB
en reposo (más al ejecutar el DAG). Lo que hacemos en ese caso es trabajar por tramos: el modo mínimo en reposo usa unos 160 MiB entre API y panel (abrir páginas lo aumenta) y la suite pide unos 320 MiB con sus procesos hijos; para Airflow se apaga el panel (`Ctrl+C`), se levanta Airflow y se
baja con `docker compose down` antes de volver al panel; y se limita WSL2 creando `%USERPROFILE%\.wslconfig` con `[wsl2]`, `memory=4GB` y `swap=2GB`, y luego `wsl --shutdown`. Esto no está probado en una máquina de 8 GB.

## 5. Documentos de esta carpeta
| Documento | Qué contiene |
|---|---|
| [modo_minimo.md](modo_minimo.md) | los pasos del modo mínimo y cómo comprobar que funciona |
| [modo_completo.md](modo_completo.md) | MySQL (las tres cuentas), panel con MySQL, Airflow desde el zip y phpMyAdmin, con su comprobación |
| [errores_comunes.md](errores_comunes.md) | tabla de síntomas, causas y qué hacer |
| [../usuarios/guia_simulacion/README.md](../usuarios/guia_simulacion/README.md) | la instalación del modo mínimo contada para quien lo hace por primera vez, desde el zip, con los tiempos medidos siguiéndola como tercero ([EV-098](../evidencias/simulacion/EV-098_guia_seguida_como_tercero.txt)) |
| [../orquestacion/operacion.md](../orquestacion/operacion.md) | sección «Desde el zip» y «Operación en otra máquina» de Airflow |
| [../almacenamiento/phpmyadmin.md](../almacenamiento/phpmyadmin.md) | phpMyAdmin de solo lectura: cómo arrancarlo y qué mirar |

## 5.1 Scripts de verificación en vivo y su última ejecución real
Los pasos que dieron las evidencias de los servicios quedaron como scripts en `scripts/evidencias/`, para que el equipo pueda repetirlos. **En la auditoría intermedia se ejecutaron de verdad dos** (`evidencia_independencia.py`, EV-096, y `medir_memoria_suite.py`, EV-097) y **los dos que necesitan Docker solo se validaron de forma estática** (compilan, tienen su documentación, no traen rutas locales ni imprimen credenciales; `tests/test_scripts_de_evidencia.py`) porque Docker estaba apagado. La última ejecución real de cada uno es:

| Script | Qué verifica | Última ejecución real |
|---|---|---|
| `evidencia_phpmyadmin.py` | phpMyAdmin con la cuenta `sismo_lectura`: siete tablas, conteos iguales a Gold y escrituras rechazadas | [EV-085](../evidencias/servicios/EV-085_phpmyadmin_en_vivo.txt) |
| `evidencia_airflow_desde_zip.py` | Airflow desde el zip descomprimido en una carpeta de otro nombre, con las cuatro tareas del DAG | [EV-087](../evidencias/servicios/EV-087_airflow_desde_el_zip.txt) |
| `evidencia_independencia.py` | clon y zip en una carpeta sin hermanas: suite, `main.py`, hashes, panel y scripts de servicios | [EV-096](../evidencias/auditoria/EV-096_independencia_repetida_y_omisiones.txt) (con esta versión del script; antes, EV-090) |
| `medir_memoria_suite.py` | pico de memoria del proceso de pytest | [EV-097](../evidencias/auditoria/EV-097_memoria_de_la_suite.txt) (con esta versión del script; antes, la fila `memoria_pico_suite_de_pruebas` de [recursos_medidos.csv](../finanzas/recursos_medidos.csv)) |

Si un equipo vuelve a ejecutar alguno y el resultado difiere, se registra como una evidencia nueva; las anteriores no se editan.

## 6. Alcance y límites
- **Qué afirmamos:** los pasos de esta guía se ejecutaron en una máquina con Windows 11 (instalación en una carpeta con espacios y tildes, suite completa sin variables de UTF-8, Airflow construido desde el zip descomprimido en otra carpeta y phpMyAdmin en vivo).
- **Qué NO demuestra:** que funcione en una máquina limpia de verdad (la nuestra ya tenía Docker, MySQL y las imágenes descargadas), en una de 8 GB, con una versión de Python distinta de la 3.13 ni en otro sistema operativo.
  Las otras dos personas del grupo son quienes lo comprobarán en sus equipos.
