# Pruebas del panel

Las pruebas corren dentro de `pytest`, sin red externa, sin MySQL, sin navegador, sin saltos ni fallos esperados, y sin escribir en `data/` ni en el repositorio (solo en carpetas temporales). Los resultados de esta página se leen de [informe_pruebas.md](../validacion/informe_pruebas.md), [cobertura_pruebas.csv](../validacion/cobertura_pruebas.csv) y de las evidencias de [docs/evidencias/panel/](../evidencias/panel/).

## 1. Qué cubre cada tipo de prueba
| Tipo | Archivo | Pruebas | Qué verifica |
|---|---|---|---|
| Unitarias | `tests/test_panel_formato_redaccion.py` | 47 | formato de cifras (miles, coma decimal, signo menos, half-up, el caso 99,845 %) y cada rama de la regla de redacción, con valores sintéticos rotulados como tales |
| Unitarias | `tests/test_panel_cliente.py` | 29 | solo GET, cada error traducido al español, un reintento de conexión, direcciones no locales rechazadas y caché que no guarda fallos |
| Unitarias | `tests/test_panel_tema.py` | 10 | cálculo de la relación de contraste y valores mínimos de cada par de colores |
| Registro y aislamiento | `tests/test_panel_registro_y_aislamiento.py` | 39 | cada ruta del registro existe en el OpenAPI, cada campo y KPI en los archivos de salida; análisis estático: solo imports permitidos, solo GET, sin HTML inseguro, sin recursos externos, sin credenciales y sin cifras escritas a mano |
| Interfaz y lógica | `tests/test_panel_paginas.py` | 134 | cada página con `AppTest`: sin excepciones, título, alcance visible, sin cadenas prohibidas y comportamiento de los filtros; resiliencia ante API apagada, 503, respuesta vacía, 404, JSON mal formado y tiempo agotado |
| Integración interfaz, API y almacenamiento | `tests/test_panel_integracion.py` | 11 | el cliente del panel, en memoria, contra la API real sobre una copia temporal de la SQLite en solo lectura: los valores mostrados coinciden con `kpis_gold.csv`, `kpis_sensibilidad.csv`, `gold_final.csv` y `quality_report.json`, leídos y recalculados en la prueba |
| Extremo a extremo | `tests/test_panel_humo_extremo_a_extremo.py` | 5 | la API real en un subproceso, el cliente real por HTTP y las ocho páginas; un intento de escritura recibe 405 y `data/` no cambia |
| Lanzador | `tests/test_panel_lanzador.py` | 19 | comandos, entorno sin credenciales, puertos, códigos de salida 0 a 3 y cierre en `finally` con subprocesos simulados |
| Decisiones | `tests/test_decisiones.py` | 4 | la cabecera de `DECISIONES.md` y el índice coinciden con la última decisión |
| Empaquetado | `tests/test_dist.py` (2 pruebas nuevas) | 2 | el zip incluye `src/panel` y `scripts/panel` y no incluye carpetas ocultas ni `.env` |

Suman 300 pruebas nuevas; el total del proyecto está en el informe de pruebas.

## 2. Resultados de las evidencias en vivo
- **Ejecución real** ([EV-052](../evidencias/panel/EV-052_ejecucion_real.txt)): el lanzador arrancó la API y el panel, ambos respondieron `ok`, las ocho páginas se recorrieron con el cliente real y el lanzador se cerró solo con código 0, sin procesos huérfanos ni puertos abiertos; `git status` y los 19 archivos de `data/` quedaron sin cambios.
- **Equivalencia SQLite frente a MySQL** ([EV-053](../evidencias/panel/EV-053_equivalencia_almacenes.txt)): 12 de 12 respuestas que consume el panel son idénticas (se ignora solo el campo que nombra el almacenamiento) y el contenido de las ocho páginas renderizadas es idéntico con ambos.
- **Capturas automatizadas** ([EV-054](../evidencias/panel/EV-054_capturas_panel.txt)): una por página, con el recuadro de alcance visible y sin avisos de error; se revisaron una por una.
- **Canario** ([EV-056](../evidencias/panel/EV-056_canario_panel.txt)): 0 hallazgos de las contraseñas en el árbol, el historial, los registros, la carpeta de Airflow y un zip de prueba.

## 3. Cobertura de las pruebas
El informe mide la cobertura de líneas de `src/` y `scripts/`; los módulos del panel están entre 84 % y 100 % (imagen [EV-059](../evidencias/panel/EV-059_cobertura_panel.png), generada desde `cobertura_pruebas.csv`). Lo que no cubren son ramas de `ejecutar_panel.py` que solo ocurren con procesos reales (cubiertas por EV-052) y rutas de error poco probables de las páginas.

## 4. Defectos encontrados al construir el panel
La revisión visual de las primeras capturas automatizadas mostró texto cortado: las etiquetas de «muestra baja» en el eje de los gráficos y en una tarjeta de la página Respuesta, y tablas con columnas fuera de la vista (clasificación de los códigos de barrio y licencias de las fuentes). Se corrigió con etiquetas de dos líneas, etiquetas de tarjeta más cortas y tablas completas con el texto partido en líneas, y se registró como DEF-014 en [registro_defectos.md](../validacion/registro_defectos.md). Las pruebas que quedan protegen las etiquetas y la estructura de esas tablas; el dibujo se vuelve a comprobar con las capturas de [EV-054](../evidencias/panel/EV-054_capturas_panel.txt). Además, el marco de cada página captura los datos con una forma inesperada y muestra un aviso (`test_con_respuestas_vacias_cada_pagina_no_se_rompe` y `test_con_objetos_vacios_cada_pagina_no_se_rompe`).

## 5. Alcance y límites
- **Qué afirmamos:** el panel pasa pruebas unitarias, de interfaz, de integración con la API real y de extremo a extremo de solo lectura.
- **Qué NO afirmamos:** que se haya probado en un navegador por personas (las capturas son automatizadas), con varios usuarios a la vez ni con datos distintos a los de esta muestra.
