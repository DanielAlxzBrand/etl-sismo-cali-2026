# Participante simulado 1: registro de la etapa 1

> **Sesión simulada, no realizada con una persona real.** Nadie abrió ni usó el panel como persona usuaria y nada se midió. Este registro no cuenta como sesión real; cuenta como evidencia simulada según la decisión D111, no es feedback de personas usuarias y no entra en [`../resultados.md`](../resultados.md).

| Campo | Valor |
|---|---|
| Participante | Participante simulado 1 |
| Perfil (código) | `habitante` |
| Fecha del ensayo | 2026-11-18 |
| Copia de los documentos | el estado del repositorio al 2026-11-18 |
| Documentos permitidos en la etapa 1 | `docs/usuarios/consentimiento.md`, `docs/usuarios/guia_simulacion/03_parte_b_primera_vez_con_el_panel.md`, `docs/usuarios/guia_simulacion/07_anexo_lista_del_participante.md`, `docs/panel/README.md` y `docs/panel/guia_de_uso.md`; `docs/gold/resultados.md` quedaba fuera porque es de otro perfil |
| Tareas | T1 a T6 del [guion](../guion_sesion.md), con su enunciado literal |
| Qué hay | el registro de la etapa 1 (abajo) y, desde el 2026-11-20, sus filas de [`registro.csv`](registro.csv) y [`cuestionarios.csv`](cuestionarios.csv), tomadas del texto original de la etapa 2 |
| Qué falta | que quien facilitó la sesión revise las diez capturas (visual y de privacidad) y una certificación independiente del modelo; nada de eso cambia los datos incorporados |

## De dónde sale este texto
- Es el texto que se guardó al cerrar la etapa 1, antes de pasar a la etapa 2; termina en la línea `REGISTRO DE LA ETAPA 1 CONGELADO`.
- **Limpieza:** solo los saltos de línea (CRLF a LF) y un salto de línea al final. No se cambió ninguna palabra ni se quitó ninguna línea: el texto no traía viñetas vacías, líneas sueltas de formato ni barras invertidas (se comprobó). La separación en blanco de la tarea T6 es distinta de la de T1 a T5 y se deja como está.
- **sha256 del texto guardado, antes de limpiar:** `78db8ba7958db5a77709deb927efdf438ca2997acc0eec7f1f1ee1ab5a1221c8`
- **sha256 del texto limpio** (el bloque de abajo más su salto de línea final): `507e050870b3afd24e63c08ab10c035acdb427689d64b3719e2bc826f5901c35`
- **Fuente nativa (2026-11-20):** después recuperamos la respuesta original de la etapa 1, tal como la entregó la persona simulada (12041 caracteres, sha256 `1c357e22f896ba58d91228728b8153332c92f68c5f867dfb8b75eb36552647f7`). **No es idéntica al respaldo de arriba:** trae 39 prefijos de viñeta («- ») que el respaldo no tiene y no deja líneas en blanco entre campos; tras retirar las viñetas y colapsar los espacios, los dos textos coinciden (11955 caracteres cada uno, comprobado por nosotros). El texto de arriba se deja como está porque las líneas de C1 a C8 se refieren a él; entre corchetes se da también la línea de la respuesta original, que es la fuente primaria.
- Las respuestas originales completas (etapas 1 y 2), las llamadas de lectura, los mensajes enviados, las capturas y los informes de la entrega quedan fuera del repositorio porque nombran las herramientas; sus sha256 están citados en el documento de declaración de la raíz.

## Registro de la etapa 1 (sin cambios)
```text
Leí el documento de consentimiento y entendí que me piden hacer seis tareas pensando en voz alta sobre lo que veo en una pantalla y contestar unas preguntas breves para ayudar a unos estudiantes a mejorar su trabajo sobre el sismo de Cali. También entendí claramente que mi participación es totalmente voluntaria y que puedo parar o retirarme en cualquier momento que yo decida, sin tener que dar ninguna explicación.

TAREA T1

Lo que me piden: «Con estos datos, ¿se nota alguna diferencia entre los estratos 3 a 5 y los estratos 1 y 2? Dígamelo con sus palabras.»
Dónde busco y por qué: Busco en docs/panel/guia_de_uso.md, en la sección «2. Qué muestra cada página» (en la fila de la página Respuesta) y en la sección «3. Cómo leer los números» (en la explicación sobre el intervalo de Newcombe), porque allí se explica cómo compara el panel esos grupos de estratos.
Lo que pienso en voz alta: Leí en la guía de uso que hay una página llamada Respuesta que trata justo sobre si se nota diferencia entre esos estratos. En el texto usan palabras como proxy e intervalo de Newcombe, que son términos técnicos que no conozco y no entiendo qué significan para una casa común y corriente. Por lo que dice el documento, entiendo que si ese cálculo incluye el cero, el sistema escribe que no se detecta diferencia entre los dos grupos en esta muestra de datos. Como no tengo el panel abierto para ver qué porcentajes salieron, no puedo saber si en las casas de mi barrio hubo más o menos daños que en las de otros barrios.
Mi respuesta, con mis palabras: Según leí en la guía de uso, el sistema compara esos dos grupos de estratos y advierte que, si el cálculo da cerca de cero, con estos datos no se nota una diferencia, aunque aclara que eso no significa que el estrato no tenga que ver. Sin embargo, en los documentos que leí no están escritos los porcentajes finales de daño para responder con certeza.
Lo que no pude comprobar: No pude comprobar los números ni las tasas exactas de daño que el panel muestra para cada grupo de estratos, ni tampoco pude ver la lectura generada en la pantalla: no verificado: lectura.
Lo que me confundió o me faltó: Me confundieron términos técnicos como intervalo de Newcombe y proxy, y me faltó ver las cifras reales de cada estrato en el documento.

TAREA T2

Lo que me piden: «¿Hay algún estrato cuyas cifras no se deberían comparar con las de los demás? ¿Por qué?»
Dónde busco y por qué: Busco en docs/panel/guia_de_uso.md, en la sección «3. Cómo leer los números» (donde explican «Muestra baja» y «Cotas por sin datos») y en la sección «5. Qué no se puede concluir».
Lo que pienso en voz alta: En la guía leí que cuando un estrato tiene muy poquitos casos graves, el sistema le pone un aviso de muestra baja y no se debe ordenar ni comparar frente a otros. También leí que si un estrato tiene muchas casas sin datos de satélite, tampoco se puede comparar con seguridad. Yo busqué a ver si nombraban un estrato en particular, como el estrato 1 o el estrato 6, pero en el texto no aparece el número exacto del estrato afectado. Entiendo la idea general de que no tiene sentido comparar un grupo donde revisaron muy poquitas viviendas con otro donde revisaron muchas, pero me quedo con la duda de cuál estrato es.
Mi respuesta, con mis palabras: Según leí en el documento, no se deben comparar las cifras de los estratos que tengan muy pocas construcciones analizadas (lo que llaman muestra baja) ni de los que tengan muchas construcciones sin información de satélite. El documento no indica el número específico del estrato que tiene este problema, pero advierte que en esos casos los resultados no son seguros para ordenar los grupos.
Lo que no pude comprobar: No pude comprobar cuál número de estrato aparece en el panel con la etiqueta de muestra baja o con exceso de datos faltantes: no verificado: lectura.
Lo que me confundió o me faltó: Me confundió no saber a qué estrato específico se referían y me faltó una lista clara en el texto con los estratos que no se pueden comparar.

TAREA T3

Lo que me piden: «¿En qué comuna se concentran las construcciones de los estratos 1 y 2? ¿Qué implica para comparar estratos?»
Dónde busco y por qué: Busco en docs/panel/guia_de_uso.md, en la sección «2. Qué muestra cada página» (en la fila de Comunas) y en la sección «5. Qué no se puede concluir».
Lo que pienso en voz alta: Revisé la parte de comunas para ver si decían el nombre de mi comuna o de alguna otra donde se concentren los estratos 1 y 2. La guía dice que en la pantalla de Comunas se ve qué comuna concentra esos estratos, pero en el texto no escribieron el número ni el nombre de ninguna comuna. Lo que sí explica el documento es que casi todas las viviendas de estratos 1 y 2 quedaron agrupadas en muy poquitas comunas. Por lo tanto, entiendo que si comparamos esos estratos con los otros, en realidad estamos comparando esas comunas en particular con el resto de la ciudad, y no la condición socioeconómica por separado.
Mi respuesta, con mis palabras: En los documentos que leí no se menciona el nombre ni el número de la comuna donde se concentran los estratos 1 y 2, pues solo dicen que esa información se muestra en la página de Comunas del panel. Lo que esto implica es que, como casi todas las casas de estratos 1 y 2 están en muy pocas comunas, comparar estratos significa en la práctica comparar esas comunas específicas frente a otras zonas de Cali, de modo que se pueden confundir los efectos del lugar con los del estrato.
Lo que no pude comprobar: No pude comprobar el número ni el nombre de la comuna que concentra las construcciones de estratos 1 y 2 porque no aparece escrito en los documentos leídos: no verificado: lectura.
Lo que me confundió o me faltó: Me faltó que el texto indicara directamente el nombre de la comuna y me confundió no poder identificar si se trataba de la zona donde yo vivo.

TAREA T4

Lo que me piden: «Si cambiamos cómo se define el daño o qué construcciones se incluyen, ¿cambia la conclusión?»
Dónde busco y por qué: Busco en docs/panel/guia_de_uso.md, en la sección «2. Qué muestra cada página» (en la fila de Sensibilidades S0 a S5) y en la sección «5. Qué no se puede concluir».
Lo que pienso en voz alta: Leí que hay una página llamada Sensibilidades que sirve para ver si cambia la conclusión cuando se usan otros filtros o definiciones de daño. La palabra sensibilidades me resulta extraña y no sé bien a qué se refiere, pero entiendo que prueban varios escenarios llamados de S0 a S5. En el texto de la guía no escribieron si al final la conclusión cambia o si sigue dando lo mismo en esos escenarios. Lo único que advierte el documento es que si se usa una definición más amplia de daño, los datos son de baja confianza, por lo que los resultados son menos seguros.
Mi respuesta, con mis palabras: Según leí en la guía de uso, el panel tiene una página para comprobar si la conclusión cambia según el filtro o la definición de daño que se elija, pero el documento no dice qué resultado da cada escenario. Solo advierte que la definición ampliada de daño es de baja confianza, por lo que no es posible saber con la pura lectura si la conclusión general se mantiene o cambia.
Lo que no pude comprobar: No pude comprobar si la conclusión cambia al pasar de un escenario a otro en la pantalla de Sensibilidades, ni qué lecturas muestra el panel para los escenarios S0 a S5: no verificado: lectura.
Lo que me confundió o me faltó: Me confundió el uso de la palabra sensibilidades en este tema y me faltó que el texto dijera claramente si el resultado final cambiaba o no.

TAREA T5

Lo que me piden: «Busque las construcciones severas de una comuna y un estrato que usted elija, y dígame cuántas encontró.»
Dónde busco y por qué: Busco en docs/panel/guia_de_uso.md, en la sección «2. Qué muestra cada página» (en la fila de Construcciones), porque allí dice que hay una tabla con filtros para buscar.
Lo que pienso en voz alta: Como habitante de una zona afectada me gustaría elegir mi comuna y mi estrato para saber cuántas viviendas tuvieron daños graves cerca de mi casa. Leí en la guía que en la página Construcciones hay una tabla con filtros y mapas de puntos para buscar edificaciones. El problema es que yo solo estoy leyendo unas guías y no tengo el programa funcionando frente a mí para poder filtrar o hacer búsquedas. Dado que en los documentos permitidos no viene impresa una lista de construcciones ni los conteos por barrio, no tengo forma de saber esa cantidad.
Mi respuesta, con mis palabras: Leí que en la página Construcciones del panel existe una tabla con filtros para buscar las viviendas según la comuna y el estrato, pero en los documentos de lectura no están los datos ni los totales de construcciones. Como no estoy manejando el sistema interactivo sino leyendo las guías, no puedo seleccionar una comuna ni decir cuántas construcciones severas se encontraron.
Lo que no pude comprobar: No pude comprobar la cantidad de construcciones severas de ninguna comuna ni de ningún estrato, porque la tabla de datos y los filtros solo existen dentro de la aplicación interactiva: no verificado: lectura.
Lo que me confundió o me faltó: Me faltó tener el programa en funcionamiento para poder buscar mi comuna y me confundió no encontrar ningún conteo de viviendas en los textos.

TAREA T6

Lo que me piden: «¿Qué cosas NO se pueden concluir con este panel? ¿De dónde salen los datos?»

Dónde busco y por qué: Busco en docs/panel/guia_de_uso.md, en la sección «5. Qué no se puede concluir» y en la sección «2. Qué muestra cada página» (en la fila de Fuentes y sistema), y en docs/panel/README.md en la sección «Alcance y límites».

Lo que pienso en voz alta: Esta parte está bien detallada en la guía, donde hay una sección completa dedicada a lo que no se puede concluir. Entiendo que los datos vienen de fotos tomadas por satélites y que eso no reemplaza una inspección en el sitio, porque desde arriba no se ve todo lo que pasa dentro de una casa. También leí que esto no se puede aplicar a todo Cali porque solo tomaron datos de ciertas comunas, y que no se puede asegurar que el estrato sea la causa de los daños. Lo que no encontré en el texto fueron los nombres exactos de las fuentes o entidades que entregaron esos datos, porque la guía dice que eso aparece en la última página del panel.

Mi respuesta, con mis palabras: Según leí en el documento, no se puede concluir el daño real de una edificación porque las fotos de satélite no reemplazan una visita técnica presencial; no se pueden extender los resultados a todo Cali porque solo se analizaron ciertas comunas; no se puede decir que el estrato sea la causa del daño; y no se pueden sacar conclusiones de los estratos con muy pocos datos. Respecto al origen de los datos, leí que provienen de imágenes tomadas por satélites y de información sobre el estrato de los barrios que existía desde antes del sismo, aunque en la guía no se mencionan los nombres de las instituciones dueñas de esa información.

Lo que no pude comprobar: No pude comprobar los nombres de las fuentes oficiales, las fechas exactas de las tomas satelitales ni las licencias que aparecen en la página de Fuentes y sistema del panel: no verificado: lectura.

Lo que me confundió o me faltó: Me confundió la frase de que una asociación no establece causalidad y me faltó ver los nombres de las instituciones o empresas de los satélites.

«¿Qué fue lo más difícil o confuso de lo que hizo?»: Lo más difícil fue toparme con palabras y conceptos estadísticos muy técnicos que no se usan en el lenguaje diario de mi comunidad.

«¿Qué cambiaría para que le resultara más claro?»: Cambiaría esos términos difíciles por explicaciones sencillas y agregaría ejemplos con los nombres de las comunas y los barrios de Cali.

«¿Qué le faltó para sentirse segura o seguro de lo que entendió?»: Me faltó ver los datos y las cifras reales de mi comuna para comprobar directamente lo que ocurrió en mi sector.

REGISTRO DE LA ETAPA 1 CONGELADO
```

## Correcciones posteriores
El registro de arriba no se toca. Lo que sigue lo anotamos nosotros al leerlo contra los cinco documentos permitidos; cada fila cita la línea del bloque (la línea 1 es la del consentimiento).

| # | Línea | Tarea | Qué dice el registro | Qué dicen los documentos permitidos | Corrección posterior |
|---|---|---|---|---|---|
| C1 | 8 | T1 | «si el cálculo da cerca de cero, con estos datos no se nota una diferencia» | `docs/panel/guia_de_uso.md`, sección 3: cuando el intervalo de Newcombe incluye 0, el panel escribe «con este proxy y esta muestra no se detecta diferencia»; no dice que la condición sea que el cálculo dé cerca de cero | La condición es que el intervalo de la diferencia incluya el 0, no que la diferencia sea pequeña. |
| C2 | 16, 17 y 56 | T2 y T6 | los estratos con muestra baja o con muchas construcciones sin datos «no se deben comparar», y de los de pocos datos «no se pueden sacar conclusiones» | `docs/panel/guia_de_uso.md`, secciones 3 y 5: esos grupos se muestran pero no se ordenan frente a otros; el documento no dice que no se puedan comparar ni que no se pueda concluir nada de ellos | Lo que el documento dice es que no se ordenan. |
| C3 | 25 y 26 | T3 | comparar esas comunas «con el resto de la ciudad» y «frente a otras zonas de Cali» | `docs/panel/guia_de_uso.md`, sección 5: solo hay las comunas de la muestra y las tasas no se extrapolan a Cali; comparar estratos es, en la práctica, comparar comunas | La comparación es entre las comunas de la muestra, no con el resto de Cali. |
| C4 | 7, 16, 25, 26, 43, 44 y 46 | T1, T2, T3 y T5 | «casas», «viviendas» y «edificaciones» | `docs/panel/guia_de_uso.md`, sección 3: la unidad de las cifras es la construcción; el documento no dice que sea una vivienda | Donde dice casas o viviendas se debe leer construcciones. |
| C5 | 34 | T4 | «Lo único que advierte el documento» es que la definición ampliada de daño es de baja confianza | `docs/panel/guia_de_uso.md`, sección 2 (fila de Sensibilidades): la página también muestra la razón ajustada por comuna «con su advertencia»; la baja confianza de la definición ampliada está en la sección 5 | No es la única advertencia que trae la página. |
| C6 | 43 | T5 | la página Construcciones tiene «mapas de puntos» | `docs/panel/guia_de_uso.md`, secciones 2 y 3: dice «dispersión de ubicaciones» con ejes de latitud y longitud, no un mapa | Es una afirmación sobre lo que muestra el panel que no está en los documentos permitidos: debía llevar la marca «no verificado: lectura». |
| C7 | 44 | T5 | la tabla de Construcciones tiene filtros «según la comuna y el estrato» | `docs/panel/guia_de_uso.md`, sección 2: dice «tabla paginada con filtros» sin decir cuáles | Es una afirmación sobre lo que muestra el panel que no está en los documentos permitidos: debía llevar la marca «no verificado: lectura». |
| C8 | 54 y 56 | T6 | «fotos tomadas por satélites», «visita técnica presencial» y la razón «porque desde arriba no se ve todo lo que pasa dentro de una casa» | `docs/panel/guia_de_uso.md`, secciones 3 y 5: el indicador mide cambio visible desde satélite y no sustituye una inspección; las fotos, la visita técnica y la razón no están escritas | Son palabras de la persona simulada, no del documento: debían llevar la marca «no verificado: lectura». |

## Reconciliación independiente de C1 a C8 (2026-11-20)
Con la respuesta original y la traza de lecturas a mano, contrastamos de nuevo cada corrección con los cinco documentos de la etapa 1 (leídos en la carpeta de trabajo, idénticos a la copia maestra). Las filas de arriba no se cambian: esta tabla dice si se sostienen y qué precisión les falta. Las líneas son las del bloque de arriba y, entre corchetes, las de la respuesta original. Solo cuentan los documentos que la persona simulada podía leer en la etapa 1: lo que diga el guion de la etapa 2 no vuelve conocimiento de la etapa 1 lo que se dijo antes de leerlo. Clasificamos cada una como confirmada, parcialmente confirmada o que requiere ajuste; ninguna resultó innecesaria ni indeterminable.

| # | Líneas | Respaldo en los documentos de la etapa 1 | Clasificación | Conclusión y acción |
|---|---|---|---|---|
| C1 | 8 [7] | `docs/panel/guia_de_uso.md`, línea 34 (sección 3, intervalo de Newcombe) y línea 22 (fila de Respuesta) | confirmada | La condición del documento es que el intervalo incluya 0. La línea 7 [6] del pensamiento en voz alta dice «incluye el cero» y es correcta: lo impreciso («cerca de cero») está solo en la respuesta de la línea 8 [7]. Se mantiene. |
| C2 | 16 [14], 17 [15] y 56 [47] | `docs/panel/guia_de_uso.md`, líneas 35 y 36 (sección 3) y 51 (sección 5) | parcialmente confirmada | El documento dice que esos grupos se muestran pero «no se ordenan» y que, si las cotas se solapan, «el orden entre ellos no es identificable». En T2 «no se deben comparar» es una lectura plausible de eso; en T6 «no se pueden sacar conclusiones» dice más que el documento. Se mantiene, con esa distinción. |
| C3 | 25 [22] y 26 [23] | `docs/panel/guia_de_uso.md`, línea 51 (sección 5) y línea 24 (fila de Comunas) | confirmada | El propio registro dice en T6 (líneas 54 [46] y 56 [47]) que solo se tomaron datos de ciertas comunas, así que «el resto de la ciudad» contradice al documento y al registro. Se mantiene. |
| C4 | 7, 16, 25, 26, 43, 44 y 46, y también 54 y 56 [6, 14, 22, 23, 38, 39, 41, 46 y 47] | `docs/panel/guia_de_uso.md`, línea 32 (sección 3: la tasa cuenta «construcciones») | requiere ajuste | El documento no dice que la unidad sea una vivienda. «Casas» y «viviendas» son además el lenguaje que el mensaje le pedía a la persona simulada («palabras de todos los días»). A la lista de la corrección le faltan las líneas 54 y 56 (T6: «una casa», «una edificación»); se completan aquí y la fila de arriba no se reescribe. |
| C5 | 34 [30] | `docs/panel/guia_de_uso.md`, línea 25 (la página muestra la razón ajustada «con su advertencia») y línea 51 (la definición ampliada es de baja confianza) | parcialmente confirmada | «Lo único» es excesivo, pero el documento no dice cuál es esa otra advertencia, así que la persona simulada no podía contarla. Se mantiene con esa precisión. |
| C6 | 43 [38] | `docs/panel/guia_de_uso.md`, líneas 28 y 44 («dispersión de ubicaciones», ejes de latitud y longitud) | parcialmente confirmada | «Mapas de puntos» es una paráfrasis plausible de «dispersión de ubicaciones», pero «mapa» no está en el documento. La marca figura en «Lo que no pude comprobar» de T5 solo para la tabla y los filtros. Se mantiene como interpretación plausible; que «debía llevar la marca» depende de cómo se lea la regla de marcar (H4). |
| C7 | 44 [39] | `docs/panel/guia_de_uso.md`, línea 28 («tabla paginada con filtros», sin decir cuáles). Solo en la etapa 2 se podía leer `docs/usuarios/guion_sesion.md`, línea 24, que sí dice «filtros de comuna y estrato» | parcialmente confirmada | En la etapa 1 esos filtros eran una inferencia del enunciado de T5, no una lectura. El guion de la etapa 2 confirma el contenido, pero no lo convierte en conocimiento de la etapa 1. La marca aparece en T5 junto a «los filtros». Se mantiene. |
| C8 | 54 [46] y 56 [47] | `docs/panel/guia_de_uso.md`, líneas 32 y 51 («cambio visible desde satélite», «no sustituye una inspección») | parcialmente confirmada | «Fotos» y «visita técnica presencial» son paráfrasis plausibles. La razón «porque desde arriba no se ve todo lo que pasa dentro de una casa» no está en ningún documento permitido: la corrección se limita a ella. |

## Hallazgos adicionales (H1 a H8)
No repiten C1 a C8. Ninguno se da por incumplimiento confirmado: son observaciones sobre lo que se pidió y lo que respondió la persona simulada, y no cambian ni el registro ni los CSV.

| # | Dónde | Qué encontramos | Tratamiento |
|---|---|---|---|
| H1 | T2, línea 16 [14] | Pone como ejemplo «el estrato 1 o el estrato 6»; los documentos de la etapa 1 nombran los estratos 1 y 2 y 3 a 5, no el 6. Es un ejemplo de la persona simulada, no una afirmación sobre el panel. | observación, sin corrección |
| H2 | T2, T3, T5 y T6 | Casi todo lo que «faltó» (qué estrato, qué comuna, cuántas construcciones, qué instituciones) es un límite del conjunto de documentos permitidos o de la modalidad: eso se ve en el panel, la guía no lo escribe y `docs/gold/resultados.md` quedaba fuera por ser de otro perfil. No son dificultades de comprensión de la guía ni del panel. | no leerlas como fricciones |
| H3 | Bloque E, correcciones posteriores | Dice que no dar las cifras de T3 y T5 «se debió exclusivamente» a la lectura sin ejecutar el panel. También influyó que los documentos permitidos no traen esas respuestas; si una persona real las encontraría en la página no se probó. | conclusión causal sin respaldo suficiente; no es incumplimiento |
| H4 | Bloque E, punto 6 | Contestó «sí» a «todo lo que no pude comprobar lleva «no verificado: lectura»». Las seis marcas están en los campos de T1 a T6, pero las seis viñetas de «lo que no pudiste comprobar» del bloque E no la llevan. La regla pide la marca para lo que se afirma del panel y no está escrito; esas viñetas son avisos de lo que no se comprobó. | no se confirma como incumplimiento: el punto 6 se redactó más amplio que la regla |
| H5 | Bloque E, fila 7.3 | Dice que la arquitectura y las pruebas técnicas «se encuentran documentadas en otros archivos del proyecto». Es cierto en el commit (`docs/arquitectura/`, `docs/validacion/informe_pruebas.md`, `docs/panel/arquitectura_panel.md`, `docs/panel/pruebas_panel.md`) y `docs/panel/README.md` (líneas 10 a 13) lo insinúa solo para el panel; la persona simulada no abrió esos archivos. | respaldo indirecto; no es incumplimiento |
| H6 | Bloque A | La fecha, la herramienta, el modelo, la versión de la copia y la declaración venían escritos en el mensaje de la etapa 2. Coinciden con él, pero no son una autodeclaración independiente. | la identificación del modelo se apoya en la selección que registró la herramienta y en lo que informó quien facilitó; no hay certificación independiente |
| H7 | Bloque E, filas del checklist | El mensaje dictó que una sesión simulada no cumple 6.1, 6.2, 6.3, 6.5 ni 7.4 y que no es el feedback de 7.3. El juicio propio queda en 3.3 y en las razones de cada fila. | no leer esas cinco respuestas como juicio independiente |
| H8 | Mensajes enviados | El de la etapa 1 nombra carpetas vecinas que no debía mirar (la copia completa y la carpeta de los mensajes) y el de la etapa 2, un script de análisis. Son datos que la persona simulada no necesitaba; las llamadas recuperadas no leen esas rutas. | observación sobre el procedimiento |

## Resumen de una línea de C1 a C8 y H1 a H8
Para leer de un vistazo lo que dicen las tablas de arriba. Ningún texto original se tocó; «ajuste» es lo que cambió en cómo leemos la corrección o la observación.

| # | Qué afirmaba | Qué resultó | Qué se ajustó |
|---|---|---|---|
| C1 | Que el panel escribe «no se detecta diferencia» si el cálculo da cerca de cero. | Confirmada: la condición es que el intervalo incluya 0. | Se aclaró que el pensamiento en voz alta ya decía «incluye el cero» y solo la respuesta es imprecisa. |
| C2 | Que los grupos con muestra baja o muchas construcciones sin datos «no se deben comparar» y de los de pocos datos «no se pueden sacar conclusiones». | Parcial: el documento dice que no se ordenan. | Se separó T2 (lectura plausible) de T6 (dice más que el documento). |
| C3 | Que comparar estratos es comparar esas comunas con «el resto de la ciudad». | Confirmada: contradice al documento y al propio T6. | Nada. |
| C4 | Que «casas», «viviendas» y «edificaciones» deben leerse como construcciones. | Requiere ajuste: el documento dice construcciones, pero la persona debía hablar con palabras de todos los días y la lista de líneas estaba incompleta. | Se completó con las líneas 54 y 56 de T6 y se reconoció que es lenguaje de la persona simulada, no un error de lectura. |
| C5 | Que «lo único» que advierte el documento es la baja confianza de la definición ampliada. | Parcial: hay otra advertencia (la de la razón ajustada), pero el documento no dice cuál. | Se añadió que la persona no podía contarla porque no está escrita. |
| C6 | Que «mapas de puntos» no estaba en el documento y debía llevar la marca. | Parcial: es paráfrasis plausible de «dispersión de ubicaciones»; «mapa» no está. | De «debía llevar la marca» a «interpretación plausible»; la marca depende de la regla (H4). |
| C7 | Que los filtros «según la comuna y el estrato» no estaban en el documento. | Parcial: era una inferencia del enunciado en la etapa 1; el guion de la etapa 2 la confirma. | Se dejó dicho que un documento de la etapa 2 no vuelve conocimiento de la etapa 1 lo dicho antes. |
| C8 | Que «fotos», «visita técnica» y la razón de la casa no estaban en el documento. | Parcial: las dos primeras son paráfrasis; la razón no tiene respaldo. | La corrección se limita a la razón «porque desde arriba no se ve todo lo que pasa dentro de una casa». |
| H1 | Ejemplo «estrato 6» en T2. | Los documentos de la etapa 1 no lo nombran; es un ejemplo, no una afirmación. | Nada: observación. |
| H2 | Lo que «faltó» en T2, T3, T5 y T6. | Casi todo es un límite de los documentos permitidos o de la modalidad, no de comprensión. | No se leen como fricciones del panel. |
| H3 | Que no dar las cifras de T3 y T5 fue «exclusivamente» por la modalidad. | Sin respaldo con esa fuerza: también influyó lo que traían los documentos. | Queda como conclusión causal sin respaldo, no como incumplimiento; la declaración no la usa. |
| H4 | Un «sí» al punto 6 del bloque E, cuyas viñetas finales no llevan la marca. | Ambigüedad: la regla pide la marca para lo afirmado del panel, no para avisos. | Nada: no se confirma incumplimiento. |
| H5 | Que arquitectura y pruebas técnicas están documentadas en otros archivos. | Cierto en el commit; respaldo indirecto solo para el panel. | Nada: no es incumplimiento. |
| H6 | La identificación del bloque A como autodeclaración. | Venía dictada por el mensaje. | La declaración la trata como dictada y no como evidencia de cumplimiento. |
| H7 | Los veredictos del bloque E sobre las filas del checklist. | Cinco venían dictados por el mensaje. | La declaración dice que no son juicio independiente y no se usan como evidencia. |
| H8 | Los mensajes nombran carpetas vecinas y un script. | Información de más, sin lecturas de esas rutas. | Nada: observación del procedimiento. |

## Los seis comentarios de `registro.csv`
Los entregó la persona simulada y se incorporan tal cual; esta tabla dice qué hacer al leerlos. No son mediciones ni observaciones de personas.

| Tarea | Qué trae | Tratamiento |
|---|---|---|
| T1 | términos técnicos que confunden y cifras ausentes del texto | se mantiene como observación documental; «no vi las cifras» es un límite de la modalidad (H2) |
| T2 | repite «no se deben comparar» y no sabe cuál estrato | se matiza con C2 («no se ordenan»); «cuál estrato» es un límite del conjunto de documentos (H2) |
| T3 | «viviendas» y la comuna no nombrada | se matiza con C4; que no nombre la comuna es un límite del conjunto de documentos (H2) |
| T4 | hay varios escenarios y el documento no trae sus resultados | se mantiene: lo respalda `docs/panel/guia_de_uso.md`, línea 25 |
| T5 | no pudo buscar por no tener el sistema abierto y «conteos de viviendas» | no se usa como hallazgo de usabilidad: es la modalidad; «viviendas» se matiza con C4 |
| T6 | «fotos de satélite», que le faltaron las entidades y que «comprendió» | se matiza con C8; las entidades se ven en la página de Fuentes y sistema, no en la guía; «comprendí» es su valoración, no una medida de comprensión |

## La etapa 2 que entregó
- **Bloques B y C:** son el contenido de `registro.csv` y `cuestionarios.csv` (6 filas de tareas y 1 de cuestionario) y salen de la respuesta original de la etapa 2 (sha256 `bd816b0b20cd9179c712a4e72ac2ec453a8ea9c7dc1da056d4e07c72d737b395`) sin cambiar nada. La cabecera más sus 6 filas de tareas tiene sha256 `61b33af5154a77c3cd924cafcaa470f328df3d08cbf47b14e9f0684a0d645621` y la cabecera más su fila de cuestionario, sha256 `3603749cabc9b406d7614111524b439a8ea2c862a4a5a79f4bcacb96651429cf`; en los archivos del repositorio sus filas van primero y las del Participante simulado 2 después. Los 35 campos de medición valen «simulado, no medido», el origen es `simulada`, las cabeceras son las de las plantillas y ningún comentario trae dígitos ni nombres. El CSV del registro es idéntico, byte a byte, al candidato que se había guardado antes de tener la respuesta original. `python scripts/usuarios/analizar_sesiones.py --simuladas` los acepta.
- **Bloque D:** copia literal del registro de la etapa 1 (12009 caracteres antes de la línea de congelación, 12007 sin los extremos): coincide con la respuesta original, no incluye la línea de congelación y no trae correcciones posteriores. Las correcciones de la persona simulada están en el bloque E, no en el D.
- **Bloque E, las ocho autocomprobaciones** (todas «sí»): la 1, 2, 3, 5, 7 y 8 se sostienen contra lo que comprobamos (campos «simulado, no medido», ningún nombre de persona salvo «Newcombe», que es el nombre de un método y viene del documento, ninguna frase de uso del panel, nada de herramientas en B y C, bloque D literal y cabeceras iguales a las plantillas). La 4 se sostiene en las doce lecturas recuperadas, no más allá de ellas. La 6 se sostiene en su primera mitad (doce rutas permitidas, ninguna del checklist) y no es literal en la segunda para el bloque E (H4).
- **Correcciones posteriores:** una sola, sobre T3 y T5 (H3). No menciona ninguna de C1 a C8.
- **Siete filas del checklist** (3.3, 6.1, 6.2, 6.3, 6.5, 7.3 y 7.4): contesta «no se cumple» en las siete, siempre sobre lo que entrega (la sesión simulada) y no sobre el proyecto, y en la 7.3 solo respecto al feedback. Esto no cambia ninguna fila del checklist: esta sesión no promueve ni degrada ningún estado, que sigue dependiendo de las demás evidencias (H7).
- **Lo que no pudo comprobar:** seis puntos, todos de la modalidad (carga, apariencia, tabla y filtros, valores, comuna y estrato marcados, comprensión de una persona real).

## Qué comprobó esta auditoría y qué no
- **Comprobó** con `python scripts/usuarios/inventariar_sesiones_simuladas.py --registro` el registro de arriba (los seis enunciados literales del guion, las tres respuestas de cierre, la marca «no verificado: lectura» en «Lo que no pude comprobar» de las seis tareas, la línea de congelación una sola vez y al final, y que no hay nombres de herramientas ni de personas, guiones largos, emojis, cifras medidas ni frases que afirmen haber usado el panel), y con `--entrega ... --nativa` la entrega recuperada (EV-119): 46 archivos, 44 manifestados con tamaño y sha256 correctos, los dos manifiestos equivalentes, 12 sha256 dados aparte, los 13 documentos iguales a la copia maestra, 12 lecturas de documentos permitidos con 385 líneas idénticas a la carpeta de trabajo y a la copia maestra, y ninguna lectura del checklist.
- **No comprobó** las transcripciones nativas: no las abrimos, solo medimos su tamaño y su sha256. Que las dos respuestas originales sean idénticas al contenido de esas transcripciones, y la selección del modelo que registró la herramienta, lo afirma el informe de la entrega; queda pendiente de autorización para leer ese campo concreto. Tampoco comprobó las diez capturas más allá de su firma, sus dimensiones y su sha256: son retrospectivas (2026-11-19) y su revisión visual y de privacidad le corresponde a quien facilitó la sesión.
- Las doce lecturas son las que quedaron registradas: no demuestran que no hubiera otras operaciones ni un aislamiento técnico fuerte, y que los hashes coincidan hoy no excluye modificaciones temporales.
- Esto no demuestra que el panel sea usable ni que alguien lo haya usado.
