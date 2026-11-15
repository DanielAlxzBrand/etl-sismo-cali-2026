# Registro de fricciones

**Ítem del checklist:** 6.3 (registro con severidad, fuente con consentimiento, priorización y decisión por fricción, y trazabilidad a cambios del panel) · **Estado:** precargado solo con los hallazgos de la [evaluación heurística interna](evaluacion_heuristica.md); **sin fricciones de observación ni de entrevista, porque no hay sesiones reales**.

> Este archivo se genera con `scripts/usuarios/precargar_friccion.py` y su CSV es [registro_de_friccion.csv](registro_de_friccion.csv). Una fricción de fuente `heuristica` es una iteración técnica interna y **no** una validación con personas usuarias.

## Cómo se usa

1. Cada fricción tiene `fuente` (`heuristica`, `observacion`, `grabacion` o `entrevista`), el participante (`P01`, `P02`… solo si la fuente es una sesión con su consentimiento; vacío en las heurísticas), la página, la severidad de 0 a 4, la frecuencia (cuántas personas la tuvieron, «no medida» si aún no hay sesiones) y su estado.
2. La `decision` empieza en `pendiente` y pasa a `corregir`, `aplazar` o `descartar` **con su razón** en la columna `razon`; no se decide sin escribir por qué.
3. Cuando se corrige, `cambio` lleva el commit, `antes` y `despues` las capturas y `verificacion` la prueba o la medición que lo comprueba; el detalle va en [trazabilidad_de_cambios.md](trazabilidad_de_cambios.md).
4. Las fricciones de sesiones reales se agregan con la plantilla [`sesiones_reales/plantilla_friccion.csv`](sesiones_reales/plantilla_friccion.csv) y solo con el consentimiento de la persona.

## Fricciones precargadas (todas de la evaluación heurística; decisión pendiente)

El orden es por severidad y es solo una **propuesta de prioridad**, no una decisión.

| Id | Fuente | Página | Severidad | Resumen | Decisión | Estado |
|---|---|---|---|---|---|---|
| F-01 | heuristica | Respuesta, Concentración, Fuentes y sistema (a 1024 px) | 3 | Las tarjetas recortan las etiquetas y hasta las cifras: «6,33…», «Tasa 1-2 (…», «+0,4…», «Participación de los barrios con má…», «202…» en lugar de la fecha. | pendiente | abierta |
| F-02 | heuristica | Todas (a 390 px) | 3 | La barra lateral de navegación se abre sola y cubre casi todo el contenido: la persona ve el menú y apenas un borde de la página. | pendiente | abierta |
| F-03 | heuristica | Estratos, Comunas, Calidad, Construcciones y Fuentes (a 390 px; Fuentes también a 1024 px) | 3 | Las tablas anchas se cortan en el borde y no se ve que hay más columnas a la derecha: «Detalle por estrato» y «Detalle por comuna» terminan en «Tasa» o a media columna; l… | pendiente | abierta |
| F-04 | heuristica | Estratos, Comunas y Construcciones (a 390 px) | 3 | En los gráficos de barras estrechos solo se dibujan la primera y la última etiqueta del eje (por ejemplo «Estrato 1» y «Estrato 6», «Comuna 03» y «Comuna 20»): las demás … | pendiente | abierta |
| F-07 | heuristica | Todas | 3 | Aparecen términos estadísticos sin explicación en pantalla: «intervalo de Wilson», «Newcombe», «Mantel-Haenszel», «Spearman», «p de permutación», «cotas por sin datos», «… | pendiente | abierta |
| F-05 | heuristica | Estratos y Comunas | 2 | Las marcas horizontales negras que cruzan las barras (cotas por «sin datos») no están explicadas en el gráfico: el pie solo explica las barras de error de Wilson, y las c… | pendiente | abierta |
| F-06 | heuristica | Sensibilidades | 2 | La misma frase («con este proxy y esta muestra no se detecta diferencia») se repite en las seis líneas de escenarios y en el resumen, y hay seis avisos casi iguales sobre… | pendiente | abierta |
| F-08 | heuristica | Sensibilidades, Construcciones, Fuentes y sistema | 2 | Identificadores de código en la interfaz: «nombre_validado = true», «coincide_poligono», «pureza_estrato >= 0,8», «dano_visible», «geom_duplicada», «sin_cambio», «escombr… | pendiente | abierta |
| F-09 | heuristica | Concentración | 2 | La tabla de K3 lista códigos de barrio («1914», «306») sin el nombre del barrio: quien conoce su barrio por el nombre no lo reconoce. | pendiente | abierta |
| F-10 | heuristica | Construcciones | 2 | La tabla muestra unas 10 filas a la vez dentro de una caja con desplazamiento aunque la página trae 50, y para recorrer las 103 páginas solo hay un campo numérico «Página… | pendiente | abierta |
| F-11 | heuristica | Todas con tablas o gráficos | 2 | Los textos de los controles de Streamlit están en inglés y el resto de la interfaz en español: «Download as CSV», «Fullscreen», «Search», «Show/hide columns», «Copy Vega-… | pendiente | abierta |
| F-12 | heuristica | Todas | 2 | Contraste calculado del texto secundario: los pies y la pregunta de cada página dan 4,05 a 1 y los rótulos, títulos y leyendas de los gráficos 3,72 a 1 (EV-068); el cuerp… | pendiente | abierta |
| F-13 | heuristica | Construcciones | 1 | Las etiquetas del eje de latitud usan coma decimal («3,440», «3,430») y pueden leerse como miles; el título dice «grados». | pendiente | abierta |
| F-14 | heuristica | Estratos, Comunas, Sensibilidades y Construcciones | 1 | Las páginas con gráfico tardan más en dibujarse que Respuesta: Respuesta 234 a 343 ms a 1400 px y entre 1,1 y 2,1 s las páginas con gráfico (Estratos, Comunas, Sensibilid… | pendiente | abierta |

## Fricciones de sesiones reales

Ninguna todavía: no se han hecho sesiones con personas usuarias.

## Alcance y límites
- **Qué afirmamos:** las fricciones listadas salen de la evaluación heurística, cada una con su captura, y ninguna se ha corregido.
- **Con qué evidencia:** [evaluacion_heuristica.md](evaluacion_heuristica.md) y EV-066 a EV-069.
- **Qué NO afirmamos:** que sean las que encontrarían las personas usuarias, que la severidad refleje su frecuencia real ni que alguna decisión esté tomada.
