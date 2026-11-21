# Participante simulado 2: registro de la etapa 1

> **Sesión simulada, no realizada con una persona real.** Nadie abrió ni usó el panel como persona usuaria y nada se midió. Este registro no cuenta como sesión real; cuenta como evidencia simulada bajo la excepción D111, no es feedback de personas usuarias y no entra en [`../resultados.md`](../resultados.md).

| Campo | Valor |
|---|---|
| Participante | Participante simulado 2 |
| Perfil (código) | `institucional` |
| Fecha del ensayo | 2026-11-18 |
| Copia de los documentos | el estado del repositorio al 2026-11-18 |
| Documentos permitidos en la etapa 1 | `docs/usuarios/consentimiento.md`, `docs/usuarios/guia_simulacion/03_parte_b_primera_vez_con_el_panel.md`, `docs/usuarios/guia_simulacion/07_anexo_lista_del_participante.md`, `docs/panel/README.md`, `docs/panel/guia_de_uso.md` y `docs/gold/resultados.md` |
| Lecturas recuperadas | tres comandos de lectura sobre archivos permitidos (los seis de la etapa 1, una relectura de las primeras 115 líneas de `docs/gold/resultados.md` y los siete adicionales de la etapa 2); no se acredita que no hubiera otras operaciones |
| Tareas | T1 a T6 del [guion](../guion_sesion.md), con su enunciado literal |
| Qué hay | el registro de la etapa 1 (abajo) y, tomados de la etapa 2, [`registro.csv`](registro.csv) y [`cuestionarios.csv`](cuestionarios.csv) |

## De dónde sale este texto
- Es la respuesta de la etapa 1, **recuperada por copia desde la interfaz**: no hay una exportación nativa que permita acreditar que sea idéntica byte a byte al historial interno. Termina en la línea `REGISTRO DE LA ETAPA 1 CONGELADO`.
- **Limpieza:** solo un salto de línea al final del archivo (el original no lo traía). No se cambió ninguna palabra ni línea y no había viñetas vacías, barras invertidas ni otros artefactos de copiado (se comprobó).
- **sha256 del texto recuperado, antes de limpiar:** `328649c9e1d071ecc95733a76365ce57cea3d0644aa465729dc24ab500d779d5`
- **sha256 del texto limpio** (el bloque de abajo más su salto de línea final): `c4ff587fa275f5e96f00da7dcbf8894458e173d3be668917f18fe3c15bad7b44`
- La respuesta original de la etapa 2 (sha256 `7374c40b68166d347fb6ec7a2906424c4224c1341121d72b92816a793fd50a60`), los mensajes enviados, los comandos, la traza, las capturas y los informes de la ejecución quedan fuera del repositorio porque nombran herramientas; sus sha256 están citados en el documento de declaración de la raíz y la verificación de la carpeta de entrega es la evidencia EV-120.

## Registro de la etapa 1 (sin cambios)
```text
Participante simulado 2

Entendí que me piden hacer tareas pensando en voz alta para ayudar a mejorar el panel y responder preguntas sobre mi experiencia. También entendí que puedo dejar de responder, parar o retirarme cuando quiera, sin dar explicaciones ni sufrir consecuencias.

La siguiente verbalización es una simulación basada únicamente en la lectura de los documentos autorizados.
TAREA T1
- Lo que me piden: «Con estos datos, ¿se nota alguna diferencia entre los estratos 3 a 5 y los estratos 1 y 2? Dígamelo con sus palabras.»
- Dónde busco y por qué: En docs/gold/resultados.md, sección «Respuesta a la pregunta de negocio», para encontrar la comparación y su incertidumbre.
- Lo que pienso en voz alta: Leo que la diferencia observada es pequeña y que su intervalo incluye la posibilidad de que no haya diferencia. No interpretaría eso como prueba de que el estrato no influye. Para priorizar estudios, también necesitaría considerar cómo se seleccionaron las construcciones y dónde están ubicadas.
- Mi respuesta, con mis palabras: Según el documento docs/gold/resultados.md, las tasas son 6,33 % y 5,84 %, respectivamente, y el intervalo de la diferencia incluye cero, no verificado: lectura. Con este indicador y esta muestra no se detecta una diferencia clara.
- Lo que no pude comprobar: No pude comprobar mediante interacción si el panel presenta esas cifras y advertencias de forma comprensible, no verificado: lectura.
- Lo que me confundió o me faltó: Me faltó saber cómo se complementaría esta comparación con información útil para priorizar estudios en territorio.
TAREA T2
- Lo que me piden: «¿Hay algún estrato cuyas cifras no se deberían comparar con las de los demás? ¿Por qué?»
- Dónde busco y por qué: En docs/gold/resultados.md, secciones «Cómo leer los resultados», «K1 · Tasa por estrato» y «Limitaciones y alcance», para revisar datos faltantes y muestra baja.
- Lo que pienso en voz alta: Identifico que la falta de datos puede cambiar mucho la lectura de un estrato. También veo que algunos grupos tienen pocos casos severos, por lo que sus tasas son inestables. Yo no los ordenaría para decidir prioridades como si sus diferencias fueran confiables.
- Mi respuesta, con mis palabras: El estrato 2 no se puede ordenar frente a los demás por la amplitud de las cotas asociadas a datos faltantes. Según el documento docs/gold/resultados.md, también tienen muestra baja los estratos 1 y 6, no verificado: lectura; sus tasas requieren cautela y no deberían ordenarse frente a las de otros grupos.
- Lo que no pude comprobar: No pude comprobar cómo se ven las advertencias correspondientes durante una interacción real con el panel, no verificado: lectura.
- Lo que me confundió o me faltó: Me faltó conocer mejor por qué faltan datos satelitales en esas construcciones.
TAREA T3
- Lo que me piden: «¿En qué comuna se concentran las construcciones de los estratos 1 y 2? ¿Qué implica para comparar estratos?»
- Dónde busco y por qué: En docs/gold/resultados.md, sección «Composición del grupo de estratos 1-2», para relacionar el estrato con la comuna.
- Lo que pienso en voz alta: Leo que la mayor parte de ese grupo está en una sola comuna y otra parte está en una comuna vecina de la muestra. Eso hace difícil separar una diferencia asociada al estrato de una asociada a la ubicación. Yo no usaría esa comparación, por sí sola, para atribuir el resultado a una condición socioeconómica.
- Mi respuesta, con mis palabras: Según el documento docs/gold/resultados.md, la concentración principal está en la Comuna 20 y el resto del grupo con datos está en la Comuna 18, no verificado: lectura. Comparar los grupos de estrato equivale en buena medida a comparar la Comuna 20 con el resto de la muestra.
- Lo que no pude comprobar: No pude comprobar cómo presenta el panel la composición territorial ni su advertencia durante una interacción real, no verificado: lectura.
- Lo que me confundió o me faltó: Me faltó una muestra con mayor presencia de ambos grupos de estrato en las mismas comunas.
TAREA T4
- Lo que me piden: «Si cambiamos cómo se define el daño o qué construcciones se incluyen, ¿cambia la conclusión?»
- Dónde busco y por qué: En docs/gold/resultados.md, sección «Sensibilidades S0-S5», para comparar las definiciones y los filtros documentados.
- Lo que pienso en voz alta: Veo que las cifras cambian según el escenario y que incluso cambia el sentido de la diferencia en uno de ellos. Sin embargo, el documento indica que todos los intervalos de la diferencia incluyen cero. Tomaría con especial cautela la definición ampliada de daño porque se describe como de baja confianza.
- Mi respuesta, con mis palabras: Según el documento docs/gold/resultados.md, la conclusión de que no se detecta una diferencia se mantiene en los escenarios examinados, aunque cambian las cifras y el signo en uno de ellos, no verificado: lectura. No interpretaría esa estabilidad como prueba de que nunca exista una diferencia.
- Lo que no pude comprobar: No pude comprobar cómo se presentan o seleccionan los escenarios mediante una interacción real con el panel, no verificado: lectura.
- Lo que me confundió o me faltó: Me faltó conocer cómo se validaría la definición ampliada frente a inspecciones en terreno.
TAREA T5
- Lo que me piden: «Busque las construcciones severas de una comuna y un estrato que usted elija, y dígame cuántas encontró.»
- Dónde busco y por qué: En docs/gold/resultados.md, sección «Composición del grupo de estratos 1-2», cuya tabla también incluye el estrato 6 por comuna.
- Lo que pienso en voz alta: Elijo la Comuna 19 y el estrato 6 porque la tabla documenta ese cruce de manera explícita. Leo que allí no se registran construcciones con cambio satelital severo en ese grupo. No tomaría ese resultado como prueba de ausencia de daño ni como base suficiente para descartar estudios.
- Mi respuesta, con mis palabras: Según la tabla de docs/gold/resultados.md, para la Comuna 19 y el estrato 6 hay 0 severas, no verificado: lectura. Es un dato leído en el documento, no un conteo obtenido mediante uso del panel.
- Lo que no pude comprobar: No pude comprobar el resultado de aplicar esos filtros en el panel ni inspeccionar las construcciones, no verificado: lectura.
- Lo que me confundió o me faltó: Me faltó contrastar el indicador satelital con evaluaciones técnicas en terreno.
TAREA T6
- Lo que me piden: «¿Qué cosas NO se pueden concluir con este panel? ¿De dónde salen los datos?»
- Dónde busco y por qué: En docs/panel/guia_de_uso.md, sección «Qué no se puede concluir», y en docs/gold/resultados.md, secciones «Fuentes de datos» y «Población analizada».
- Lo que pienso en voz alta: Entiendo que el cambio visible desde satélite es una medida indirecta y no me dice por sí sola si una construcción es segura. Tampoco puedo extender las tasas de esta muestra a toda la ciudad ni deducir causas de una asociación. Para confiar en una priorización municipal necesitaría más cobertura, información actualizada del territorio y contraste con inspecciones.
- Mi respuesta, con mis palabras: No se puede concluir que el estrato cause o deje de influir en el daño, ni ordenar con seguridad los grupos afectados por datos faltantes o muestra baja. Según docs/gold/resultados.md, la capa de impacto satelital proviene del Fondo Adaptación y el estrato se asigna con información por barrio del Departamento Administrativo de Planeación Municipal de Cali de 2015, no verificado: lectura. Los polígonos de barrios se usan para validar la unión, y el indicador no sustituye una inspección estructural.
- Lo que no pude comprobar: No pude comprobar la presentación de las fuentes, sus fechas ni sus advertencias mediante una interacción real con el panel, no verificado: lectura.
- Lo que me confundió o me faltó: Me faltó información comparable de toda la ciudad y resultados de inspecciones para apoyar una priorización.
¿Qué fue lo más difícil o confuso de lo que hizo? Distinguir una diferencia observada de una diferencia que pudiera sostener para orientar decisiones.

¿Qué cambiaría para que le resultara más claro? Pondría junto a cada comparación una explicación sencilla de la cobertura, los datos faltantes y el efecto de la ubicación.

¿Qué le faltó para sentirse segura o seguro de lo que entendió? Contrastar los resultados con inspecciones y comprobar directamente cómo se presentan las advertencias.

REGISTRO DE LA ETAPA 1 CONGELADO
```

## Bloque D de la etapa 2: no es la fuente
La persona simulada copió este registro en el bloque D de la etapa 2 y, al copiarlo, omitió el signo de apertura «¿» del enunciado de T3 (ella misma lo anotó en su autocomprobación). Al comparar nosotros el original con el bloque D: 48 líneas no vacías en cada uno, una sola línea distinta (la de T3) y coincidencia normalizada tras restaurar ese signo solo en memoria. **El registro de arriba es el original recuperado; el bloque D no se usa y nada se corrigió en ninguno de los dos.**

## `registro.csv` y `cuestionarios.csv`
- Salen de los bloques B y C de la respuesta de la etapa 2 (sha256 `7374c40b68166d347fb6ec7a2906424c4224c1341121d72b92816a793fd50a60`). Solo se cambiaron los saltos de línea (CRLF a LF) y se añadió un salto final: ningún valor se tocó.
- En `registro.csv` y `cuestionarios.csv` sus filas van después de las del Participante simulado 1 (desde el 2026-11-20 los archivos traen las de los dos). La cabecera más sus 6 filas de tareas (T1 a T6) tiene sha256 `0326f148b8d1e25ee6ae64778649a2535c3235a5827a8805199f3398466c3033`, y la cabecera más su fila de cuestionario, sha256 `81f447c53ae38a31e049972360c6b0312c849083db8179a5335061aa1aaeda2e`: son los archivos que tenía antes de que se añadieran las del otro participante.
- Todas las cifras valen «simulado, no medido» y el origen es `simulada`; `python scripts/usuarios/analizar_sesiones.py --simuladas` los acepta. Los comentarios breves los escribió la persona simulada; no traen nombres ni cifras.
- La fila de `cuestionarios.csv` la dictaba el mensaje de la etapa 2 (iba escrita en él): no es una respuesta de la persona simulada.

## Correcciones posteriores
El registro de arriba no se toca. Lo que sigue lo anotamos nosotros al leerlo contra los seis documentos permitidos; cada fila cita la línea del bloque. La línea 1 es la de la identificación.

| # | Línea | Tarea | Qué dice el registro | Qué dicen los documentos permitidos | Corrección posterior |
|---|---|---|---|---|---|
| C1 | 23 | T3 | la otra parte del grupo «está en una comuna vecina de la muestra» | `docs/gold/resultados.md`, secciones «Composición del grupo de estratos 1-2» y «Limitaciones y alcance»: solo nombran las Comunas 20 y 18; ningún documento permitido dice que sean vecinas | No hay base para «vecina». Debía llevar la marca «no verificado: lectura»; la persona simulada también lo reconoció en su autocomprobación de la etapa 2. |
| C2 | 37 y 38 | T5 | «para la Comuna 19 y el estrato 6 hay 0 severas», sin el total | `docs/gold/resultados.md`, sección «Composición del grupo de estratos 1-2»: la celda dice «11 / 0» (11 construcciones con datos y 0 severas), y la sección K1 marca E6 con muestra baja (0,00 %, intervalo de Wilson de 0,00 % a 25,88 %) | El dato es 0 severas de 11 construcciones con datos, de un grupo con muestra baja; decir solo «0 severas» puede leerse como ausencia de daño. |
| C3 | 9 | T1 | «la diferencia observada es pequeña» | `docs/gold/resultados.md`, sección «Respuesta a la pregunta de negocio»: +0,49 puntos porcentuales, intervalo de Newcombe de −2,36 a +2,55, «no se detecta diferencia» | «Pequeña» es una valoración de la persona simulada: el documento da la cifra y dice que no se detecta diferencia, no la califica. |

**Notas de formato** (no cambian el contenido): las tres respuestas del cierre van sin las comillas «» y sin los dos puntos; el registro añade una línea con el nombre del participante y una frase sobre la verbalización simulada; y la marca «no verificado: lectura» aparece también detrás de cifras que sí están en un documento permitido, porque el mensaje pedía citarlas así.

## Qué comprobó esta auditoría y qué no
- **Comprobó:** la integridad de los 26 archivos de la entrega contra sus manifiestos y contra sha256 dados aparte; que los tres comandos recuperados solo leen archivos permitidos de su etapa; los seis enunciados literales, las tres respuestas de cierre, la marca en las seis tareas y la línea de congelación (sin hallazgos automáticos); y que las cifras y los nombres de secciones que cita el registro coinciden con `docs/gold/resultados.md`, salvo lo anotado arriba.
- **No comprobó:** que este sea el texto que quedó en el historial interno de la herramienta, la cronología completa de accesos, ni que la coincidencia de hashes excluya modificaciones temporales. Las tres comprobaciones de integridad históricas son reconstrucciones a partir de resultados comunicados y las nueve capturas son retrospectivas.
- **El mensaje de la etapa 2** dictaba los valores del bloque A, la fila del cuestionario y que las filas 3.3, 6.1, 6.2, 6.3, 6.5 y 7.4 no se cumplen; esos puntos del bloque E no son un juicio propio de la persona simulada.
- Esto no demuestra que el panel sea usable ni que alguien lo haya usado.
