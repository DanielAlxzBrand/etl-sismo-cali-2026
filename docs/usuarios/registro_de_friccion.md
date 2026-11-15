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

## Fricciones de sesiones reales

Ninguna todavía: no se han hecho sesiones con personas usuarias.

## Alcance y límites
- **Qué afirmamos:** de las 14 fricciones, 8 se corrigieron (una con residuo), 1 se evaluó y se aplazó por una razón técnica y 5 se aplazaron sin tocar, cada una con su razón.
- **Con qué evidencia:** [evaluacion_heuristica.md](evaluacion_heuristica.md), EV-066 a EV-069 (antes de los ajustes originales), EV-073 a EV-080 (antes y después de los ajustes) y `tests/test_panel_ajustes.py`.
- **Qué NO afirmamos:** que las correcciones mejoren la experiencia de personas reales, que la severidad de después refleje su frecuencia ni que alguna fricción de sesiones esté atendida.
