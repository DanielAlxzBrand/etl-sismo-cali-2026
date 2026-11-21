# Trazabilidad de los cambios al panel

**Ítems del checklist:** 6.3 (subcriterio 4: trazabilidad a cambios del dashboard), 6.5 y 7.4 (iteración tras la retroalimentación) · **Estado:** llena con los ajustes de la evaluación heurística interna (iteración técnica); **ningún cambio viene de sesiones con personas**.

> Esta tabla une cada fricción del [registro](registro_de_friccion.md) con el cambio que la atiende. Una fila solo se llena cuando existe el commit; no se anota un cambio «previsto» como si estuviera hecho. Un cambio que sale de una fricción de fuente `heuristica` es una **iteración técnica**; solo los que salen de sesiones reales con su consentimiento cuentan como retroalimentación de personas usuarias.

## Cómo se llena
1. Elegir una fricción con decisión `corregir` en el registro y anotar su razón allí.
2. Tomar la captura **antes** con `python scripts/evidencias/evidencia_capturas_anchos.py` (o la página y el ancho que correspondan) y guardarla.
3. Hacer el cambio en `src/panel/` en un commit pequeño que cite el id de la fricción, con una prueba que falle sin el cambio cuando sea posible.
4. Tomar la captura **después**, comprobar con la misma medición que usó la evaluación (por ejemplo, elementos con texto recortado a 1024 px) y registrar todo en la fila.
5. Actualizar el registro (`cambio`, `antes`, `despues`, `verificacion`, `estado`).

## Tabla de cambios

Todos los cambios son una **iteración técnica a partir de evaluación heurística** (D87 a D90): no vienen de sesiones con personas, y el estado de 6.1, 6.2, 6.3, 6.5 y 7.4 lo fija D111 (evidencia simulada), no estos cambios. Las capturas «antes» son EV-073 a EV-076 (y EV-069 para 390 px con la barra cerrada) y las «después» son EV-077 a EV-079; las rutas están en `docs/evidencias/ajustes_ux/` salvo EV-069 (`docs/evidencias/usuarios/`).

| Fricción | Fuente | Decisión y razón | Cambio (commit) | Captura antes | Captura después | Prueba o medición | Estado |
|---|---|---|---|---|---|---|---|
| F-01 | heuristica | corregir: La cifra central de la respuesta no se leía completa a 1024 px y el cambio no toca datos ni contratos. | «Ajustes del panel» | EV-073_captura_respuesta_1024.png; EV-073_captura_concentracion_1024.png; EV-073_captura_fuentes_1024.png | EV-077_captura_respuesta_1024.png; EV-077_captura_concentracion_1024.png; EV-077_captura_fuentes_1024.png | tests/test_panel_ajustes.py (tarjetas de dos en dos y etiquetas cortas); 0 elementos con texto recortado a 1024 px en EV-077 | corregida |
| F-02 | heuristica | corregir: A 390 px la barra lateral tapaba casi todo el contenido y basta cambiar un parámetro de la configuración de página. | «Barra lateral automática y paleta más oscura» | EV-073_captura_respuesta_390.png | EV-077_captura_respuesta_390.png | tests/test_panel_ajustes.py (initial_sidebar_state en «auto»); la captura a 390 px muestra el contenido y el botón para abrir el menú | corregida |
| F-03 | heuristica | corregir: Las tablas cortadas no avisaban que había más columnas; el aviso es la solución que cabe sin rehacer las tablas. | «Ajustes del panel» y «Aviso de tabla ancha desde cuatro columnas» | EV-069_captura_estratos_390_barra_cerrada.png; EV-073_captura_fuentes_1024.png | EV-077_captura_estratos_390.png; EV-077_captura_fuentes_1024.png | tests/test_panel_ajustes.py (cada tabla de cuatro columnas o más lleva su aviso); la tabla sigue necesitando desplazarse | corregida con residuo |
| F-04 | heuristica | corregir: A 390 px solo se dibujaban la primera y la última etiqueta de las barras; con barras horizontales y un paso fijo caben todas. | «Ajustes del panel» y «Barras horizontales con paso fijo por barra» | EV-069_captura_estratos_390_barra_cerrada.png; EV-069_captura_comunas_390_barra_cerrada.png | EV-077_captura_estratos_390.png; EV-077_captura_comunas_390.png; EV-077_captura_construcciones_390.png | tests/test_panel_ajustes.py (barras horizontales, paso fijo y etiquetas sin ocultar); las capturas muestran todas las etiquetas | corregida |
| F-05 | heuristica | corregir: Al revisar el código se vio que las rayas eran los límites del intervalo de Wilson y no las cotas por «sin datos»; el pie ahora lo dice. | «Ajustes del panel» y «Barras horizontales con paso fijo por barra» | EV-073_captura_estratos_1400.png | EV-077_captura_estratos_1400.png | tests/test_panel_ajustes.py (el pie explica la línea y las rayas) | corregida |
| F-07 | heuristica | corregir: El glosario existía solo en la documentación; un desplegable común no cambia el número de páginas. | «Glosario común del panel con un solo diccionario de términos» y «Ajustes del panel» | EV-073_captura_estratos_1400.png | EV-077_captura_estratos_1400.png | tests/test_panel_ajustes.py (cada página muestra su glosario y todo término técnico que usa tiene entrada); si se entiende lo decidirán las sesiones | corregida; falta saber si se entiende |
| F-12 | heuristica | corregir: Pies y gráficos quedaban bajo 4,5 a 1 y el cambio solo toca colores de la configuración y del texto de los gráficos. | «Barra lateral automática y paleta más oscura» y «Ajustes del panel» | EV-075_contraste_texto.txt | EV-079_contraste_texto.txt | tests/test_panel_ajustes.py (4,5 a 1 para texto y 3 a 1 para gráficos, calculados); EV-079: pies 4,86 a 1 y texto de gráficos 7,61 a 1 | corregida |
| F-13 | heuristica | corregir: Con tres decimales «3,440» se lee como miles; cuatro decimales y «grados decimales» lo evitan. | «Ajustes del panel» y «Barras horizontales con paso fijo por barra» | EV-073_captura_construcciones_1400.png | EV-077_captura_construcciones_1400.png | tests/test_panel_ajustes.py (cuatro decimales con coma y rótulo «grados decimales») | corregida |
| F-06 | heuristica | aplazar: Acortar las frases repetidas obliga a cambiar `redaccion.py`, que protege la regla de no afirmar de más; conviene decidirlo con lo que digan las sesiones. | — | — | — | — | aplazada |
| F-08 | heuristica | aplazar: Los identificadores vienen de la API y de las notas de Gold; traducirlos exige un diccionario de etiquetas y volver a probar la integración. | — | — | — | — | aplazada |
| F-09 | heuristica | aplazar: El nombre del barrio no viene en la nota de K3; pedirlo exige otra consulta o cambiar la API, que no se toca aquí. | — | — | — | — | aplazada |
| F-10 | heuristica | aplazar: Los botones de página anterior y siguiente exigen estado de sesión y cambiar la tabla; hasta ver si alguien revisa tantas construcciones no vale el riesgo. | — | — | — | — | aplazada |
| F-11 | heuristica | aplazar: Streamlit 1.67.0 escribe esos textos dentro de su front, no ofrece opción de idioma ni parámetro para ocultar la barra de herramientas, y `embedOptions` no la quita. | — | EV-066_capturas_anchos.txt | EV-080_controles_de_streamlit.txt | EV-080 (prueba en vivo con una aplicación mínima) | aplazada (razón técnica) |
| F-14 | heuristica | aplazar: Los tiempos medidos son de unos dos segundos y no hay evidencia de que molesten; acelerar exige caché de gráficos o cambiar el cliente. | — | EV-074_mediciones_anchos.txt | EV-078_mediciones_anchos.txt | — | aplazada |

## Cambios de documentación a partir de las sesiones simuladas

> **Sesión simulada, no realizada con una persona real.** Estos cambios salen de observaciones de dos participantes simulados (registro de fricciones, ids `S-`): son solo de documentación (`docs/panel/guia_de_uso.md`), no tocan `src/`, `data/`, las salidas ni el pipeline, **no vienen de personas usuarias**: no cuentan como sesiones reales; cuentan como evidencia simulada bajo la excepción D111.

| Observación | Cambio (commit) | Qué cambió en el documento | Prueba o comprobación | Estado |
|---|---|---|---|---|
| S-01 | «Guia de uso del panel» | §3: definición de proxy en palabras sencillas y qué significa que el intervalo de Newcombe incluya 0 | `tests/test_usuarios_estructura.py` y `tests/test_criterio_de_texto.py` pasan; la definición repite la del glosario del panel | corregida; falta saber si se entiende |
| S-02 | «Guia de uso del panel» | §3: la unidad es la construcción, no necesariamente una vivienda | igual a `docs/gold/KPIs.md`, línea de la unidad | corregida |
| S-03 | «Guia de uso del panel» | §2: filtros de Construcciones, total encima de la tabla y gráfico de puntos sin mapa | leído en `src/panel/paginas/construcciones.py` sin modificarlo | corregida |
| S-04 | «Guia de uso del panel» | §2: sección «Dónde se ve cada respuesta» y publicador en Fuentes | sin cifras ni nombres que cambien con los datos | corregida |
| S-05 | «Guia de uso del panel» | §3: qué es «sin datos» y que el porqué de cada caso no está documentado | no se inventa una causa | corregida en parte |
| S-06 | «Guia de uso del panel» | §2: dónde se ve cada escenario, con enlace a `docs/gold/resultados.md` | no se copia el resultado de cada escenario | atendida con un enlace |

Las observaciones S-07, S-08 y S-09 no tienen cambio y su razón está en el [registro](registro_de_friccion.md#observaciones-de-las-sesiones-simuladas-no-son-fricciones-de-personas). Si una sesión real repite alguna, esa sí contaría como fricción de una persona.

## Alcance y límites
- **Qué afirmamos:** dejamos el formato para trazar cada fricción hasta su cambio, su captura antes y después y su prueba.
- **Con qué evidencia:** este documento y el [registro de fricciones](registro_de_friccion.md).
- **Qué NO afirmamos:** que se haya corregido algo ni que un cambio mejore la experiencia de las personas: eso solo lo muestran sesiones reales posteriores.
