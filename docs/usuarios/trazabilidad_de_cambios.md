# Trazabilidad de los cambios al panel

**Ítems del checklist:** 6.3 (subcriterio 4: trazabilidad a cambios del dashboard), 6.5 y 7.4 (iteración tras la retroalimentación) · **Estado:** plantilla vacía; **todavía no se hizo ningún cambio al panel a partir de las fricciones**. Se llena cuando el equipo decida y haga arreglos.

> Esta tabla une cada fricción del [registro](registro_de_friccion.md) con el cambio que la atiende. Una fila solo se llena cuando existe el commit; no se anota un cambio «previsto» como si estuviera hecho. Un cambio que sale de una fricción de fuente `heuristica` es una **iteración técnica**; solo los que salen de sesiones reales con su consentimiento cuentan como retroalimentación de personas usuarias.

## Cómo se llena
1. Elegir una fricción con decisión `corregir` en el registro y anotar su razón allí.
2. Tomar la captura **antes** con `python scripts/evidencias/evidencia_capturas_anchos.py` (o la página y el ancho que correspondan) y guardarla.
3. Hacer el cambio en `src/panel/` en un commit pequeño que cite el id de la fricción, con una prueba que falle sin el cambio cuando sea posible.
4. Tomar la captura **después**, comprobar con la misma medición que usó la evaluación (por ejemplo, elementos con texto recortado a 1024 px) y registrar todo en la fila.
5. Actualizar el registro (`cambio`, `antes`, `despues`, `verificacion`, `estado`).

## Tabla de cambios
| Fricción | Fuente | Decisión y razón | Cambio (commit) | Captura antes | Captura después | Prueba o medición | Estado |
|---|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — | sin cambios todavía |

## Alcance y límites
- **Qué afirmamos:** dejamos el formato para trazar cada fricción hasta su cambio, su captura antes y después y su prueba.
- **Con qué evidencia:** este documento y el [registro de fricciones](registro_de_friccion.md).
- **Qué NO afirmamos:** que se haya corregido algo ni que un cambio mejore la experiencia de las personas: eso solo lo muestran sesiones reales posteriores.
