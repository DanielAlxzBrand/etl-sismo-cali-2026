# Estructura de costos y finanzas del proyecto

**Ítem del checklist:** 6.4 (estructura de costos por categorías, consumo de recursos medido, fórmulas de costo por ejecución con precios como parámetro y ninguna cifra monetaria inventada) · **Estado:** estructura, fórmulas y mediciones listas; **ningún precio ni tarifa tiene valor**, porque no tenemos una fuente que los respalde.

> **Aviso.** Este documento no contiene ninguna cifra monetaria. Los precios y tarifas son parámetros vacíos en [`config/parametros_costos.yaml`](../../config/parametros_costos.yaml); solo tendrán valor si el equipo los aporta con su fuente y su fecha. Los ingresos siguen «no estimados» (como en el [Canvas](../estrategia/04_canvas_data_innovation_board.md)) y no calculamos un punto de equilibrio.

## 1. Categorías y su relación con el Canvas
El bloque 9 del Canvas («Estructura de costos») nombra tres categorías sin cifras: tiempo del equipo, cómputo y almacenamiento, y mantenimiento ante cambios de fuentes. Aquí las abrimos en siete, porque en las sesiones con usuarios y en un eventual despliegue aparecen costos que el Canvas no separaba:

| Categoría | Qué incluye | Bloque 9 del Canvas | Hoy |
|---|---|---|---|
| Tiempo del equipo | Horas de personas para lanzar y revisar cada ejecución | tiempo del equipo | existe; sin tarifa |
| Cómputo | Horas de máquina donde corre el pipeline, la API y el panel | cómputo y almacenamiento | existe (un equipo propio); sin precio por hora |
| Almacenamiento | Disco para `data/`, la base SQLite y la base MySQL | cómputo y almacenamiento | existe; sin precio por GB-mes |
| Servicios de nube (si se desplegara) | Máquina, base de datos y salida de datos de un proveedor | no estaba | **no aplica hoy**: el panel y Airflow corren en una máquina local (fuera del alcance del MVP) |
| Mantenimiento por cambios de fuentes | Horas para adaptar el pipeline cuando una fuente cambia | mantenimiento ante cambios de fuentes | no medido; sin horas ni frecuencia |
| Licencias y datos | Software o datos de pago | no estaba | las fuentes actuales son abiertas ([catálogo de fuentes](../bronze/catalogo_fuentes_metadatos.md)); no hay licencias de pago conocidas |
| Soporte a personas usuarias | Atender preguntas, accesos y correcciones | no estaba | no medido; no hay usuarios todavía |

## 2. Consumo medido
Mediciones locales de una máquina, con su origen y su fecha, en [`recursos_medidos.csv`](recursos_medidos.csv). Las genera `python scripts/finanzas/medir_recursos.py [--docker]`: mide **en un clon temporal** el tiempo y el pico de memoria de `python main.py --stage all` (mediana de tres repeticiones), el tamaño de `data/`, de la base y de un zip de prueba, y reúne las mediciones que ya teníamos (suite de pruebas, latencias de la API en [EV-055](../evidencias/panel/EV-055_mediciones_panel.txt), carga a MySQL en [EV-030](../evidencias/almacenamiento/EV-030_benchmark_lotes.txt) y el DAG en vivo en [EV-064](../evidencias/endurecimiento/EV-064_airflow_en_vivo.txt)). La memoria en reposo de los contenedores de Airflow se mide con `docker stats --no-stream` solo si Docker está encendido; si no, queda «no medido». Las cifras sirven para dimensionar, no son una garantía para otro equipo.

## 3. Fórmulas (los precios son símbolos, no números)
**Símbolos y parámetros** (nombres en `parametros_costos.yaml`):
| Símbolo | Significado | Parámetro | Origen del valor |
|---|---|---|---|
| t_ej | tiempo de una ejecución completa, en segundos | — | medido (`recursos_medidos.csv`) |
| A | almacenamiento usado, en MB | — | medido |
| p_c | precio de una hora de cómputo | `precio_hora_computo` | lo aporta el equipo |
| p_a | precio de un GB-mes de almacenamiento | `precio_gb_mes_almacenamiento` | lo aporta el equipo |
| p_t | precio de un GB que sale del servicio | `precio_gb_transferencia` | lo aporta el equipo (solo si hay nube) |
| w | valor de una hora-persona | `tarifa_hora_equipo` | lo aporta el equipo |
| h_e | horas-persona por ejecución | `horas_equipo_por_ejecucion` | lo aporta el equipo |
| n | ejecuciones por mes | `ejecuciones_por_mes` | lo aporta el equipo |
| h_m, k | horas por cambio de fuente y cambios por año | `horas_mantenimiento_por_cambio_de_fuente`, `cambios_de_fuente_por_ano` | lo aporta el equipo |
| L | licencias y datos de pago por mes | `precio_licencias_y_datos_mes` | lo aporta el equipo |
| h_s | horas de soporte por mes | `horas_soporte_por_mes` | lo aporta el equipo |
| G | GB que salen del servicio por mes | — | se mediría solo con nube |

**Costo por ejecución** (lo que calcula `scripts/finanzas/costos.py`):
`C_ejec = (t_ej / 3600) × p_c + (A / 1024) × p_a / n + h_e × w`
**Costo mensual de operación** (incluye lo que no depende de cada ejecución):
`C_mes = n × C_ejec + (h_m × k / 12) × w + L + h_s × w + G × p_t`

Con parámetros vacíos, `python scripts/finanzas/costos.py` muestra el consumo medido y escribe «costo no calculado: faltan parámetros: …»; con todos los necesarios calcula, y rechaza un parámetro con valor pero sin fuente o sin fecha. Las pruebas usan valores sintéticos rotulados «valores de prueba, no son precios».

## 4. Cómo aportar un precio
1. Buscar la fuente (lista de precios del proveedor, factura propia, tarifa interna) y anotar la fecha de consulta.
2. Escribir en el YAML el `valor` y llenar `fuente` y `fecha` de ese parámetro (sin fuente y sin fecha el script lo rechaza).
3. Correr `python scripts/finanzas/costos.py`. Si faltan otros parámetros, el script dice cuáles.

## 5. Ingresos
No estimados: no hay mercado, usuarios ni disposición de pago medidos. No calculamos ingresos, margen ni punto de equilibrio.

## Alcance y límites
- **Qué afirmamos:** que dejamos las categorías de costo, las fórmulas con símbolos y el consumo medido, y que ningún precio sale de nuestra mano.
- **Con qué evidencia:** este documento, `recursos_medidos.csv`, `config/parametros_costos.yaml`, `scripts/finanzas/` y `tests/test_finanzas.py`.
- **Qué NO demuestra:** cuánto cuesta operar el panel (faltan todos los precios), cuánto costaría desplegarlo en la nube ni si el proyecto es sostenible; tampoco que las mediciones valgan en otro equipo.
