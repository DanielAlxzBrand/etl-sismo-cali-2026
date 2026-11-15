# Instrumentos: SUS y CSAT

**Ítems del checklist:** 6.1 (instrumentos de la sesión) y 6.2 (subcriterio 3: SUS y CSAT aplicados con su puntuación) · **Estado:** instrumentos preparados; ninguno se ha aplicado a personas reales.

## 1. SUS (escala de usabilidad del sistema)
**Fuente externa:** Brooke, J. (1996). «SUS: a "quick and dirty" usability scale». En P. W. Jordan, B. Thomas, B. A. Weerdmeester e I. L. McClelland (eds.), *Usability Evaluation in Industry* (pp. 189–194). Londres: Taylor & Francis. Cuestionario de diez afirmaciones con respuesta de 1 (totalmente en desacuerdo) a 5 (totalmente de acuerdo). [Fuente externa: Brooke (1996), consultada por el equipo como referencia bibliográfica; no la reproducimos]

**Traducción del equipo.** La hicimos nosotros y **no es una versión validada** en español; la usamos porque necesitamos entender cada frase al aplicarla. Cada persona responde cada afirmación de 1 a 5.

| Ítem | Afirmación (traducción del equipo) |
|---|---|
| 1 | Creo que me gustaría usar este panel con frecuencia. |
| 2 | Encontré el panel innecesariamente complejo. |
| 3 | Pensé que el panel era fácil de usar. |
| 4 | Creo que necesitaría la ayuda de una persona con conocimientos técnicos para poder usar este panel. |
| 5 | Encontré que las distintas funciones del panel estaban bien integradas. |
| 6 | Pensé que había demasiada inconsistencia en este panel. |
| 7 | Imagino que la mayoría de las personas aprendería a usar este panel muy rápido. |
| 8 | Encontré el panel muy incómodo de usar. |
| 9 | Me sentí muy segura o seguro usando el panel. |
| 10 | Necesité aprender muchas cosas antes de poder empezar a usar este panel. |

**Cómo se puntúa (fórmula de Brooke).** Para cada persona: en los ítems impares (1, 3, 5, 7 y 9) se resta 1 a la respuesta; en los pares (2, 4, 6, 8 y 10) se resta la respuesta a 5; se suman las diez contribuciones (de 0 a 40) y se multiplican por 2,5. El resultado va de 0 a 100. Casos de referencia que usa la prueba automática: todas las respuestas en 3 dan 50; la mejor respuesta posible (5 en los impares y 1 en los pares) da 100; la peor (1 en los impares y 5 en los pares) da 0.

**Cómo se informa.** El SUS de cada persona y su media. Con menos de 5 personas **no se informa un porcentaje de nada ni se compara contra otros estudios**: se muestra la lista de puntuaciones y se aclara que un número tan pequeño de personas no permite concluir si el panel es «bueno» o «malo». La puntuación no es un porcentaje ni una nota.

## 2. CSAT (satisfacción con el panel)
**Pregunta única:** «En general, ¿qué tan satisfecha o satisfecho quedó con el panel?». Respuesta de 1 (muy insatisfecha o insatisfecho) a 5 (muy satisfecha o satisfecho). Se informa la lista de respuestas y su media; con menos de 5 personas no se informa un porcentaje de «satisfechos». [Criterio aplicado: instrumento de una sola pregunta, de uso común, que definimos nosotros; no hay una fuente externa que citar]

## 3. Preguntas abiertas
Las tres del [guion](guion_sesion.md). Se resumen en una línea cada una, sin nombres, y alimentan el [registro de fricciones](registro_de_friccion.md) con fuente `entrevista`.

## 4. Dónde se guardan las respuestas
En [`sesiones_reales/plantilla_cuestionarios.csv`](sesiones_reales/plantilla_cuestionarios.csv) (una fila por persona: código, diez respuestas SUS, CSAT y `origen`). La columna `origen` solo admite `real` en esa carpeta.

## Alcance y límites
- **Qué afirmamos:** dejamos la escala, su fuente, su fórmula y el CSAT escritos antes de aplicarlos, y la fórmula está probada con vectores conocidos en `tests/test_usuarios.py`.
- **Con qué evidencia:** este documento y `scripts/usuarios/analizar_sesiones.py`.
- **Qué NO afirmamos:** que la traducción sea equivalente a una versión validada, que la media de unas pocas personas represente a alguien más ni que una puntuación alta de SUS signifique que las personas entienden las limitaciones de los resultados (eso lo miden las tareas).
