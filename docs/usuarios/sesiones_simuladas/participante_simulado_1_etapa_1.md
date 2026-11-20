# Participante simulado 1: registro de la etapa 1

> **Sesión simulada, no realizada con una persona real.** Nadie abrió ni usó el panel como persona usuaria y nada se midió. Este registro no cuenta para ningún ítem del checklist, no es feedback de personas usuarias y no entra en [`../resultados.md`](../resultados.md).

| Campo | Valor |
|---|---|
| Participante | Participante simulado 1 |
| Perfil (código) | `habitante` |
| Fecha del ensayo | 2026-11-18 |
| Copia de los documentos | commit `3157ee2a450e8adfd834c11ae43d880d9adaf57f` |
| Documentos permitidos en la etapa 1 | `docs/usuarios/consentimiento.md`, `docs/usuarios/guia_simulacion/03_parte_b_primera_vez_con_el_panel.md`, `docs/usuarios/guia_simulacion/07_anexo_lista_del_participante.md`, `docs/panel/README.md` y `docs/panel/guia_de_uso.md`; `docs/gold/resultados.md` quedaba fuera porque es de otro perfil |
| Tareas | T1 a T6 del [guion](../guion_sesion.md), con su enunciado literal |
| Qué hay | solo el registro de la etapa 1 |
| Qué falta | el registro de la etapa 2 (`registro.csv` y `cuestionarios.csv`): su texto original no está en nuestra carpeta de trabajo y no lo reconstruimos desde un informe; queda pendiente |

## De dónde sale este texto
- Es el texto que se guardó al cerrar la etapa 1, antes de pasar a la etapa 2; termina en la línea `REGISTRO DE LA ETAPA 1 CONGELADO`.
- **Limpieza:** solo los saltos de línea (CRLF a LF) y un salto de línea al final. No se cambió ninguna palabra ni se quitó ninguna línea: el texto no traía viñetas vacías, líneas sueltas de formato ni barras invertidas (se comprobó). La separación en blanco de la tarea T6 es distinta de la de T1 a T5 y se deja como está.
- **sha256 del texto guardado, antes de limpiar:** `78db8ba7958db5a77709deb927efdf438ca2997acc0eec7f1f1ee1ab5a1221c8`
- **sha256 del texto limpio** (el bloque de abajo más su salto de línea final): `507e050870b3afd24e63c08ab10c035acdb427689d64b3719e2bc826f5901c35`
- Las respuestas originales completas y los informes de la ejecución quedan fuera del repositorio porque nombran las herramientas; sus sha256 están citados en el documento de declaración de la raíz.

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

## Qué comprobó esta auditoría y qué no
- **Comprobó** con `python scripts/usuarios/inventariar_sesiones_simuladas.py --registro`: los seis enunciados literales del guion, las tres respuestas de cierre, la marca «no verificado: lectura» en «Lo que no pude comprobar» de las seis tareas, la línea de congelación una sola vez y al final, y que no hay nombres de herramientas ni de personas, guiones largos, emojis, cifras medidas ni frases que afirmen haber usado el panel.
- **No comprobó** que este sea el texto que escribió quien simuló la sesión: lo que tenemos es un respaldo, no la respuesta original. Tampoco comprobó qué archivos se abrieron en realidad: la traza de lecturas no está en el repositorio.
- Esto no demuestra que el panel sea usable ni que alguien lo haya usado.
