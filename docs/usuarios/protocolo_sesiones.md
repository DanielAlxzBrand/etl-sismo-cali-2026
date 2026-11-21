# Protocolo de las sesiones con personas usuarias del panel

**Ítems del checklist:** 6.1 (sesiones con personas usuarias) y, con sus resultados, 6.2, 6.3 y 3.3 (subcriterio 4). · **Estado:** material preparado; **las sesiones reales todavía no se han hecho** (solo hubo dos sesiones simuladas, en una sola ronda). Este documento dice cómo las haremos; no contiene ningún resultado.

> **Etiquetas de evidencia.** [Evidencia en el repo: `ruta`] = existe en el repositorio; [Criterio aplicado: …] = regla nuestra, explicada; [Hipótesis de diseño: …] = propuesta que todavía no se ejecutó.

## 1. Qué queremos saber y por qué
Queremos saber si una persona que no construyó el panel puede responder, solo con él, las preguntas de negocio de cada página sin leer de más: es decir, si entiende que el cambio satelital severo es un **proxy** de daño, que las tasas describen **esta muestra** de 7 comunas y que el estrato de 2015 está **confundido con la ubicación**. Lo hacemos así porque la evaluación heurística interna ([evaluacion_heuristica.md](evaluacion_heuristica.md)) solo mira el panel desde nuestra cabeza, y lo que una persona entiende solo se sabe viéndola usarlo. [Criterio aplicado: la evaluación heurística no sustituye a las sesiones; por eso 3.3 y 6.1 a 6.3 siguen dependiendo de un hecho externo]

## 2. Qué se prueba y qué no
- **Se prueba:** el panel de lectura en su navegador (ocho páginas, solo lectura) con seis tareas en lenguaje natural derivadas de las preguntas de cada página ([guion_sesion.md](guion_sesion.md)).
- **No se prueba:** la calidad de los datos, la API, el cálculo de los indicadores ni la utilidad de las decisiones que alguien tomaría con el panel. Tampoco medimos si las personas confían en las cifras: solo si entienden lo que dicen y lo que no dicen.

## 3. Perfiles
Tomamos los grupos que ya describe [02_stakeholders.md](../estrategia/02_stakeholders.md) y no inventamos personas:
| Perfil (código en los registros) | Grupo de `02_stakeholders.md` | Qué buscamos en la sesión |
|---|---|---|
| `institucional` | Usuario objetivo institucional (gestión del riesgo); **no hubo contacto con la Secretaría ni con otra entidad** | Si la tabla por comuna y las advertencias le sirven para priorizar dónde mirar primero |
| `habitante` | Habitantes de las zonas afectadas | Si entiende qué se midió, con qué incertidumbre y qué no se puede decir de su barrio |
| `academico` | Comunidad académica y estudiantil | Si lee la ausencia de diferencia como «no se detecta con este proxy» y no como «el estrato no influye» |
Una persona queda en el perfil que ella misma diga que describe mejor su relación con el tema; si no encaja en ninguno, se anota `otro` y no se fuerza.

## 4. Cuántas personas
- **Mínimo propuesto: de 3 a 5 personas.** El equipo planea hacer 2 o 3 sesiones reales; si solo se logran 2 o 3, el análisis muestra «k de n» y **no porcentajes** (con menos de 5 personas un porcentaje parecería más preciso de lo que es).
- **Limitación declarada:** es una prueba cualitativa, no estadística. Con tan pocas personas no se puede generalizar ni comparar perfiles. Si las personas son compañeras o conocidas del equipo, se anota en `origen` de la sesión y en los resultados: sabemos que tienden a ser más amables y a conocer el tema. [Hipótesis de diseño: criterio y experimento de validación propuesto, no ejecutado]

## 5. Duración y logística
- **De 20 a 25 minutos por persona:** 3 de introducción y consentimiento, unos 15 para las seis tareas, 4 para los cuestionarios y las tres preguntas abiertas.
- **Preparación del panel** (en el equipo del facilitador, con el entorno activado): `python scripts/panel/ejecutar_panel.py` arranca la API y el panel solo en `127.0.0.1` y los cierra con Ctrl+C (o con `--duracion` en segundos). Se abre la dirección que imprime el lanzador en un navegador con ventana de unos 1400 px de ancho. Cada persona empieza en la primera página con el navegador recién abierto. [Evidencia en el repo: `docs/panel/guia_de_uso.md`]
- **Sin grabación** de audio, video ni pantalla por defecto: la anotadora o el anotador escribe solo códigos, tiempos y comentarios breves. Si el equipo decidiera grabar, se pide un consentimiento aparte y la grabación **nunca** entra al repositorio.

## 6. Roles
- **Facilitador:** lee la introducción y el guion, da las tareas una por una, **no explica el panel ni da pistas** (si la persona pide ayuda, anota «ayuda» y responde «¿qué haría usted si yo no estuviera?»), y pasa a la siguiente tarea al llegar al tiempo máximo.
- **Anotador:** cronometra cada tarea, marca el resultado (éxito, éxito con ayuda o fracaso), cuenta ayudas y errores y escribe un comentario breve sin nombres.
- **Quién NO debería facilitar:** quien construyó el panel o escribió el texto de una página, porque tiende a corregir a la persona o a defender el diseño sin darse cuenta. Si el equipo es pequeño y no hay alternativa, esa persona solo anota, y se declara.

## 7. Qué se registra y qué no
- **Se registra** (en `docs/usuarios/sesiones_reales/`, con códigos `P01`, `P02`…): perfil, fecha, resultado de cada tarea, tiempo en segundos, número de ayudas y de errores, un comentario breve, los diez ítems del SUS y el CSAT. [Hipótesis de diseño: formato en `plantilla_registro.csv`, `plantilla_cuestionarios.csv` y `plantilla_friccion.csv`]
- **No se registra en el repositorio:** nombres, correos, fotos, grabaciones, firmas, el consentimiento firmado ni notas con nombres. El equipo guarda esos papeles fuera del repo y mantiene en privado la tabla que relaciona cada código con la persona.
- **Retiro:** si una persona se retira en cualquier momento, sus filas se borran de los archivos y se anota «una persona se retiró» sin más datos.

## 8. Sesgos y cómo los declaramos
| Sesgo | Qué hacemos |
|---|---|
| Amabilidad o conocimiento previo (compañeras y compañeros) | Se anota en los resultados cuántas personas eran conocidas del equipo |
| El facilitador sabe lo que el panel quiere decir | Guion fijo, sin pistas y sin explicar; si lo hizo el autor del panel, se declara |
| Tareas redactadas con las palabras del panel | Las tareas usan lenguaje natural («¿se nota diferencia entre estratos?») y no los nombres de las páginas |
| Muestra pequeña y no aleatoria | Se muestra «k de n», no porcentajes, y se declara que no se generaliza |
| Primer uso con el navegador recién abierto | Cada persona empieza igual; no medimos el aprendizaje en usos repetidos |

## 9. Qué se hace después
El equipo corre `python scripts/usuarios/analizar_sesiones.py` (genera [resultados.md](resultados.md)), anota cada fricción en [registro_de_friccion.md](registro_de_friccion.md) con su fuente y decide por cada una; los cambios al panel se enlazan en [trazabilidad_de_cambios.md](trazabilidad_de_cambios.md) con capturas antes y después. Hasta que existan sesiones reales, los ítems 6.1, 6.2, 6.3, 6.5 y 7.4 están en «Cumple con matiz» **solo por la decisión D111** (evidencia simulada, sin personas reales) y nunca en «Cumple». En una sesión **simulada** (no real), el SUS y el CSAT pueden anotarse como «simulado: N», una estimación de la persona simulada que nunca es una medición (D112); en una sesión real siguen siendo las respuestas de la persona. Los datos sintéticos de [`simulacion/`](simulacion/) solo sirven para probar el script y **no cuentan**.

## Alcance y límites
- **Qué afirmamos:** dejamos escrito cómo se harán las sesiones, con qué tareas y qué instrumentos, y que el análisis está preparado y probado con datos sintéticos rotulados.
- **Con qué evidencia:** los documentos de esta carpeta, `scripts/usuarios/` y `tests/test_usuarios.py`.
- **Qué NO afirmamos:** que alguien haya usado el panel, que el panel sea usable para personas reales ni ningún resultado. Este texto no es asesoría jurídica ni afirma cumplimiento de una norma de protección de datos.
