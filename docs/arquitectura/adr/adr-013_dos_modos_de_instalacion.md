# ADR-013: Dos modos de instalación y Python 3.13 solo en paralelo

**Estado:** Vigente (implementada). **Fecha de la decisión:** 2026-11-15. **D de origen:** D93. **Propietario técnico:** Daniel Alexander Brand García. **Revisión:** Jhoan Sebastián Castellanos Mayor, 2026-11-18.

## Contexto
Reproducir las cifras no requiere MySQL ni Docker, pero el proyecto también incluye la carga relacional, Airflow y phpMyAdmin. Las otras dos personas del equipo tienen una versión de Python más nueva que la 3.13 con la que se fijaron las salidas, y necesitaban saber qué les faltaba antes de ejecutar.

## Decisión
La guía `docs/instalacion/` separa el **modo mínimo** (pipeline, API y panel con SQLite, sin MySQL ni Docker) del **modo completo** (además MySQL con sus tres cuentas, Airflow y phpMyAdmin). Python 3.13 es la única versión soportada y se instala en paralelo, usándola con `py -3.13` aunque el equipo tenga una más nueva. `scripts/preparar_entorno.py` diagnostica el equipo en solo lectura y solo con `--instalar` y confirmación crea el entorno.

## Consecuencias
### Positivas
- Quien solo quiere ver las cifras necesita únicamente Python 3.13: el modo mínimo corre con unos 160 MiB para la API y el panel.
- El diagnóstico dice qué falta y qué acción corresponde, y nunca imprime valores del `.env`.
- Los dos modos se probaron: el mínimo en un clon nuevo con espacios y ñ en la ruta (EV-113) y el completo desde un zip nuevo (EV-100).

### Negativas
- Hay dos caminos que documentar y mantener.
- Solo probamos en Windows 11 con PowerShell; en otros sistemas no sabemos qué ocurre.
- Con 8 GB de RAM no conviene encender todo a la vez, y esa configuración no está probada.

## Alternativas consideradas entonces
Registradas en `docs/DECISIONES.md`:
- un solo modo con todo (exigiría docker y mysql a quien solo quiere ver las cifras) (D93)
- soportar python 3.14 (no se probó) (D93)
- instalar o desinstalar python desde el script (D93)

## Alternativas que hoy descartamos y por qué
Razonamiento actual del equipo, no registrado en su momento.
- **Empaquetar todo en contenedores, incluido el pipeline.** Airflow ya ocupa unos 1.970 MiB en reposo con siete contenedores; sumar la API y el panel solo para ver cifras que se obtienen con 160 MiB y un comando sería un costo sin beneficio medible.
- **Un instalador que cree todo, incluidas las cuentas de MySQL.** Las contraseñas de administrador deben teclearlas quienes las conocen; un instalador automático tendría que guardarlas o pedirlas por argumento, lo que descartamos en el diseño de la seguridad (ADR-011).
