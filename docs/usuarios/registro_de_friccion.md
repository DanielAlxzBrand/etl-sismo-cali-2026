# Registro de fricciones

**Ítem del checklist:** 6.3 (registro con severidad, fuente con consentimiento, priorización y decisión por fricción, y trazabilidad a cambios del panel) · **Estado:** las 14 fricciones vienen de la [evaluación heurística interna](evaluacion_heuristica.md) y ya tienen decisión; **sin fricciones de observación ni de entrevista, porque no hay sesiones reales**.

> El CSV es [registro_de_friccion.csv](registro_de_friccion.csv). Se precargó con `scripts/usuarios/precargar_friccion.py` y después se actualizó a mano con las decisiones, los commits y las capturas; por eso el script ya no lo sobrescribe. Una fricción de fuente `heuristica` es una **iteración técnica** y **no** una validación con personas usuarias: 6.1, 6.2, 6.3, 6.5 y 7.4 siguen pendientes.

## Cómo se usa

1. Cada fricción tiene `fuente` (`heuristica`, `observacion`, `grabacion` o `entrevista`), el participante (`P01`, `P02`… solo si la fuente es una sesión con su consentimiento; vacío en las heurísticas), la página, la severidad de 0 a 4, la frecuencia y su estado.
2. La `decision` pasa de `pendiente` a `corregir`, `aplazar` o `descartar` **con su razón** en la columna `razon`; no se decide sin escribir por qué.
3. Cuando se corrige, `cambio` lleva el commit, `antes` y `despues` las capturas o mediciones y `verificacion` la prueba que lo comprueba; el detalle está en [trazabilidad_de_cambios.md](trazabilidad_de_cambios.md).
4. Las fricciones de sesiones reales se agregan con la plantilla [`sesiones_reales/plantilla_friccion.csv`](sesiones_reales/plantilla_friccion.csv) y solo con el consentimiento de la persona.

## Fricciones de la evaluación heurística (decisión tomada el 2026-11-14, D87)

Severidad antes → después según la [reevaluación](evaluacion_heuristica.md#reevaluación-tras-los-ajustes); la de después es una estimación nuestra, no lo que sentiría una persona.

| Id | Página | Sev. antes → después | Decisión | Razón | Cambio (commit) | Estado |
|---|---|---|---|---|---|---|
| F-01 | Respuesta, Concentración, Fuentes y sistema (a 1024 px) | 3 → 0 | corregir | La cifra central de la respuesta no se leía completa a 1024 px y el cambio no toca datos ni contratos. | 6309c79 | corregida |
| F-02 | Todas (a 390 px) | 3 → 0 | corregir | A 390 px la barra lateral tapaba casi todo el contenido y basta cambiar un parámetro de la configuración de página. | b04f9da | corregida |
| F-03 | Estratos, Comunas, Calidad, Construcciones y Fuentes (a 390 px; Fuentes también a 1024 px) | 3 → 2 | corregir | Las tablas cortadas no avisaban que había más columnas; el aviso es la solución que cabe sin rehacer las tablas. | 6309c79 y 8b107d2 | corregida con residuo |
| F-04 | Estratos, Comunas y Construcciones (a 390 px) | 3 → 0 | corregir | A 390 px solo se dibujaban la primera y la última etiqueta de las barras; con barras horizontales y un paso fijo caben todas. | 6309c79 y 298b458 | corregida |
| F-07 | Todas | 3 → 2 | corregir | El glosario existía solo en la documentación; un desplegable común no cambia el número de páginas. | 320f9fa y 6309c79 | corregida; falta saber si se entiende |
| F-05 | Estratos y Comunas | 2 → 0 | corregir | Al revisar el código se vio que las rayas eran los límites del intervalo de Wilson y no las cotas por «sin datos»; el pie ahora lo dice. | 6309c79 y 298b458 | corregida |
| F-06 | Sensibilidades | 2 → 2 | aplazar | Acortar las frases repetidas obliga a cambiar `redaccion.py`, que protege la regla de no afirmar de más; conviene decidirlo con lo que digan las sesiones. | — | aplazada |
| F-08 | Sensibilidades, Construcciones, Fuentes y sistema | 2 → 2 | aplazar | Los identificadores vienen de la API y de las notas de Gold; traducirlos exige un diccionario de etiquetas y volver a probar la integración. | — | aplazada |
| F-09 | Concentración | 2 → 2 | aplazar | El nombre del barrio no viene en la nota de K3; pedirlo exige otra consulta o cambiar la API, que no se toca aquí. | — | aplazada |
| F-10 | Construcciones | 2 → 2 | aplazar | Los botones de página anterior y siguiente exigen estado de sesión y cambiar la tabla; hasta ver si alguien revisa tantas construcciones no vale el riesgo. | — | aplazada |
| F-11 | Todas con tablas o gráficos | 2 → 2 | aplazar | Streamlit 1.67.0 escribe esos textos dentro de su front, no ofrece opción de idioma ni parámetro para ocultar la barra de herramientas, y `embedOptions` no la quita. | — | aplazada (razón técnica) |
| F-12 | Todas | 2 → 0 | corregir | Pies y gráficos quedaban bajo 4,5 a 1 y el cambio solo toca colores de la configuración y del texto de los gráficos. | b04f9da y 6309c79 | corregida |
| F-13 | Construcciones | 1 → 0 | corregir | Con tres decimales «3,440» se lee como miles; cuatro decimales y «grados decimales» lo evitan. | 6309c79 y 298b458 | corregida |
| F-14 | Estratos, Comunas, Sensibilidades y Construcciones | 1 → 1 | aplazar | Los tiempos medidos son de unos dos segundos y no hay evidencia de que molesten; acelerar exige caché de gráficos o cambiar el cliente. | — | aplazada |

## Observaciones de las sesiones simuladas (no son fricciones de personas)

> **Sesión simulada, no realizada con una persona real.** Lo que sigue sale de lo que dijeron los dos participantes simulados al leer los documentos ([participante 1](sesiones_simuladas/participante_simulado_1_etapa_1.md) y [participante 2](sesiones_simuladas/participante_simulado_2_etapa_1.md)); nadie usó el panel y nada se midió. Son **observaciones sobre la documentación**, con su decisión, y **no** son fricciones de observación ni de entrevista: no cuentan para 6.1, 6.2, 6.3, 6.5 ni 7.4, y sus ids (`S-`) no entran en el CSV de arriba. Las que no se atienden aquí tienen su razón.

| Id | De dónde sale | Qué se observó | Decisión | Razón | Cambio (commit) | Estado |
|---|---|---|---|---|---|---|
| S-01 | participante 1, T1 | «Newcombe» y «proxy» confunden, y la respuesta se quedó en «cerca de cero» en vez de «incluye el 0». | corregir | Es solo texto de la guía de uso; el glosario del panel ya trae las definiciones y se reutilizan sus palabras. | 48a292a | corregida en la guía; falta saber si se entiende |
| S-02 | participante 1, T1, T3 y T5, y participante 2, T3 | Se habla de «casas» y «viviendas» y la guía no dice cuál es la unidad. | corregir | `docs/gold/KPIs.md` define la unidad: la construcción (huella catastral); la guía solo lo repite. | 48a292a | corregida en la guía |
| S-03 | participante 1, T5 | No sabe qué filtros tiene Construcciones, que dice cuántas construcciones cumplen ni si el gráfico es un mapa. | corregir | Se leyó en `src/panel/paginas/construcciones.py` (sin modificarlo): tres filtros, el total encima de la tabla y un gráfico de puntos por longitud y latitud. | 48a292a | corregida en la guía |
| S-04 | participante 1, T2, T3 y T6 | La guía no dice en qué página se ve cada respuesta ni quién publica los datos. | corregir | Se añade dónde mirar sin repetir cifras ni nombres que cambian con los datos; la fuente de la lectura vigente es `docs/gold/resultados.md`. | 48a292a | corregida en la guía |
| S-05 | participante 2, T2 | Quiere saber por qué faltan datos satelitales. | corregir en parte | La guía ahora dice qué es «sin datos»; el porqué de cada caso no está en ninguna documentación y no se inventa. | 48a292a | corregida en parte; el porqué sigue sin documentar |
| S-06 | participante 1, T4 | La guía no dice si la conclusión cambia en cada escenario. | corregir en parte | La guía indica dónde se ve (página Sensibilidades); el resultado de cada escenario es una cifra que cambia con los datos y no se copia aquí. | 48a292a | atendida con un enlace, no con el resultado |
| S-07 | participante 1, T2, T3 y T5 | No ve qué estrato, qué comuna ni cuántas construcciones, porque no usó el panel. | descartar | Es el límite de la modalidad (leer sin abrir el panel), no una fricción del panel ni de la guía; cuenta solo si una persona real lo vive. | — | descartada |
| S-08 | participante 1, cierre | Pide ejemplos con los nombres de las comunas y los barrios. | aplazar | El nombre del barrio no viene en la nota de K3 (F-09): pedirlo exige cambiar la API o el panel, que este bloque no toca. | — | aplazada |
| S-09 | participante 2, T3 a T6 | Echa de menos una muestra con ambos grupos en las mismas comunas, información comparable de toda la ciudad y el contraste con inspecciones en terreno. | aplazar | Exige datos que no tenemos (otras comunas, inspecciones); ya figura en las limitaciones («Qué no se puede concluir») y no se arregla con documentación. | — | aplazada |

## Fricciones de sesiones reales

Ninguna todavía: no se han hecho sesiones con personas usuarias.

## Alcance y límites
- **Qué afirmamos:** de las 14 fricciones, 8 se corrigieron (una con residuo), 1 se evaluó y se aplazó por una razón técnica y 5 se aplazaron sin tocar, cada una con su razón.
- **Con qué evidencia:** [evaluacion_heuristica.md](evaluacion_heuristica.md), EV-066 a EV-069 (antes de los ajustes originales), EV-073 a EV-080 (antes y después de los ajustes) y `tests/test_panel_ajustes.py`.
- **Qué NO afirmamos:** que las correcciones mejoren la experiencia de personas reales, que la severidad de después refleje su frecuencia ni que alguna fricción de sesiones esté atendida.
