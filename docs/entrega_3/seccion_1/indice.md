# Sección 1 del checklist: diseño estratégico (Entrega 3)

**Fecha:** 2026-11-12 · **Sección del checklist:** «1. Problema, Diseño Estratégico y Stakeholders» (cinco verificaciones, 1.1 a 1.5). Este índice lista los cinco documentos de evidencia, los supuestos con los que se redactaron y la leyenda de etiquetas. La fecha límite y la rúbrica de la Entrega 3 no constan.

## Documentos y estado
| ítem | verificación (resumen) | documento | estado según la regla |
|---|---|---|---|
| 1.1 | Data Thinking, insights y problema central | [01_data_thinking.md](01_data_thinking.md) | Cumple con matiz: marco público adoptado a posteriori; sin investigación con usuarios |
| 1.2 | Mapeo de stakeholders y tipología de la organización | [02_stakeholders.md](02_stakeholders.md) | Cumple con matiz: rúbrica R1 propia; sin contacto con stakeholders |
| 1.3 | Objetivo, alcance, OKR y KPI | [03_objetivo_alcance_okr_kpi.md](03_objetivo_alcance_okr_kpi.md) | Cumple con matiz: KR2, KR3 y KR5 sin cubrir; métricas de los componentes nuevos se miden en F2 a F5 |
| 1.4 | Canvas, Data Innovation Board y propuesta de valor | [04_canvas_data_innovation_board.md](04_canvas_data_innovation_board.md) | Cumple con matiz: ejercicio de diseño con hipótesis sin validar |
| 1.5 | Criterios de aceptación del MVP | [05_mvp_criterios_aceptacion.md](05_mvp_criterios_aceptacion.md) | Cumple con matiz: criterios de API, MySQL, Airflow y dashboard se verifican en F2 a F5 |

**Regla de estado.** Cumple: evidencia concreta y reproducible para todos los subcriterios. Cumple con matiz: entregable central verificado; algún subcriterio depende de un hecho externo declarado o de una fase posterior. Pendiente (hecho externo). N/A justificado. No cumple (solo si no es técnicamente viable). Nunca «cumple» lo que requiera un evento que no ocurrió.

## Supuestos adoptados
- **S1.** Usuarios objetivo (planteamiento, no un cliente real): una entidad pública territorial de gestión del riesgo (la Secretaría de Gestión del Riesgo de Cali) y la comunidad académica. El proyecto es una investigación aplicada de estudiantes. No hubo contacto con ninguna de ellas.
- **S2.** El ítem 1.4 es un ejercicio de diseño con hipótesis sin validar y no un plan de negocio validado; **no es N/A**.
- **S3.** El MVP de la Entrega 3 incluye pipeline reproducible, Gold con KPI e incertidumbre, API de solo lectura, almacenamiento relacional con historial, DAG de orquestación, dashboard sobre la API y verificación automática (los cuatro componentes nuevos están en construcción hasta F2 a F5).

## Leyenda de etiquetas de evidencia
- [Evidencia en el repo: `ruta`]: existe en el repositorio y se puede abrir.
- [Fuente externa: URL y fecha de consulta]: viene de una página externa; si no hay fecha registrada, se dice.
- [Criterio aplicado: descripción]: regla o decisión del equipo, explicada.
- [Hipótesis de diseño: criterio y experimento de validación propuesto, no ejecutado].

## Reglas de honestidad
No hubo entrevistas, encuestas, pruebas con usuarios, estudios de mercado ni contacto con ningún stakeholder. Ningún documento afirma lo contrario. Los números de personas de los experimentos son tamaños de muestra propuestos, no cifras de mercado. Hablamos de «cambio satelital severo (severo estricto, proxy de daño)» y las tasas describen 7 comunas, no la ciudad. El concepto de inteligencia artificial aparece solo como enfoque futuro; el proyecto no entrena modelos (decisión D-E3-07 en `docs/DECISIONES.md`).

## Cambios respecto del encuadre anterior
Estos documentos se escribieron como si pertenecieran al Avance 2 y recomendaban marcar el Canvas como N/A y excluir API, dashboard y orquestación. Esas recomendaciones quedaron superadas: la Entrega 3 incluye los cuatro componentes (decisiones en `docs/entrega_3/decisiones_tecnicas.md`). Cada documento termina con un bloque «Cómo lo defendemos».

## Evidencia de F1
`docs/entrega_3/evidencias/f1/` y `docs/entrega_3/evidencias/MANIFIESTO_EVIDENCIAS.md`. Imágenes en `docs/entrega_3/img/`: la matriz poder-interés y el Canvas, generadas a partir de los datos de los documentos (no son capturas de pantalla).
