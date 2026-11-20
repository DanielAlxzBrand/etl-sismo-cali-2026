# Usuarios y experiencia de uso del panel

**Ítems del checklist:** 3.3 (usabilidad, capacidad de respuesta y coherencia visual) y 6.1 a 6.3 (sesiones con personas usuarias, métricas de experiencia y fricciones). Los costos están en [docs/finanzas/](../finanzas/estructura_costos.md).

> **Dónde estamos, dicho sin rodeos.** Preparamos todo lo que el equipo necesita para hacer sesiones con personas usuarias y evaluamos el panel por dentro con las heurísticas de Nielsen, pero **todavía no hubo ninguna sesión con personas**: no hay participantes, tiempos ni respuestas. Los ítems 6.1, 6.2, 6.3, 6.5 y 7.4 están en «Cumple con matiz» solo por la excepción D111 (evidencia simulada, sin personas reales); los hechos externos siguen sin ocurrir y nunca los marcamos «Cumple».

## Qué hay en esta carpeta
| Archivo o carpeta | Para qué sirve | Estado |
|---|---|---|
| [evaluacion_heuristica.md](evaluacion_heuristica.md) | Evaluación heurística interna: 14 hallazgos con severidad y captura, fortalezas y matriz heurística × página | hecha (interna); 8 de 14 corregidos y reevaluados (iteración técnica) |
| [protocolo_sesiones.md](protocolo_sesiones.md) | Cómo haremos las sesiones: perfiles, número de personas, roles, qué se registra y sesgos | preparado |
| [guion_sesion.md](guion_sesion.md) | Introducción hablada, seis tareas con criterio de éxito y cierre con SUS, CSAT y tres preguntas | preparado |
| [consentimiento.md](consentimiento.md) | Texto de consentimiento y reglas de reclutamiento (no es asesoría jurídica) | preparado |
| [instrumentos.md](instrumentos.md) | SUS (con su fuente y fórmula) y CSAT | preparado |
| [`sesiones_reales/`](sesiones_reales/README.md) | Donde el equipo guarda los registros reales; hoy solo plantillas | **vacía** |
| [resultados.md](resultados.md) | Lo genera `scripts/usuarios/analizar_sesiones.py`; hoy dice «no hay sesiones reales» | sin datos |
| [`sesiones_simuladas/`](sesiones_simuladas/README.md) y [resultados_sesiones_simuladas.md](resultados_sesiones_simuladas.md) | Sesiones **simuladas, no realizadas con una persona real** (D109): participantes «Participante simulado N», cifras «simulado, no medido» y `origen = simulada`; no cuentan | plantillas, **dos registros de la etapa 1** (Participantes simulados 1 y 2) y las filas de los dos participantes |
| [`simulacion/`](simulacion/README.md) y [resultados_simulacion.md](resultados_simulacion.md) | **Datos sintéticos rotulados** para probar el script; no son personas y no cuentan | ensayo |
| [`guia_simulacion/`](guia_simulacion/README.md) | Guía en PDF y su generador para que las tres personas del equipo hagan sesiones de uso del panel en su equipo (modo mínimo); sesgo declarado | preparada; sin sesiones |
| [registro_de_friccion.md](registro_de_friccion.md) y `.csv` | Las 14 fricciones de la evaluación heurística, cada una con su decisión (D87); ninguna viene de personas usuarias | con decisión |
| [trazabilidad_de_cambios.md](trazabilidad_de_cambios.md) | Tabla fricción → cambio → commit → captura antes y después → prueba, llena con los 8 ajustes de la iteración técnica (D87 a D90) | llena (iteración técnica) |

## Qué debe hacer el equipo con las sesiones reales (en cinco pasos)
1. **Reclutar** de 3 a 5 personas (si solo logran 2 o 3, el análisis mostrará «k de n» sin porcentajes) siguiendo el [protocolo](protocolo_sesiones.md) y el texto de [consentimiento](consentimiento.md); quien construyó el panel no facilita.
2. **Hacer la sesión** de 20 a 25 minutos con el [guion](guion_sesion.md): arrancar el panel con `python scripts/panel/ejecutar_panel.py`, leer la introducción, pedir el consentimiento y dar las seis tareas sin pistas.
3. **Registrar** en `sesiones_reales/` copiando las plantillas a `registro.csv`, `cuestionarios.csv` y `friccion.csv` con códigos `P01`, `P02`… y `origen = real`; los nombres y los consentimientos firmados se guardan **fuera** del repositorio.
4. **Analizar** con `python scripts/usuarios/analizar_sesiones.py` (genera `resultados.md`) y anotar cada fricción nueva en el [registro](registro_de_friccion.md) con su decisión y su razón.
5. **Arreglar y trazar:** los cambios al panel se hacen después, en commits pequeños, con capturas antes y después en la [trazabilidad](trazabilidad_de_cambios.md); solo entonces se actualizan 6.1, 6.2, 6.3, 6.5 y 7.4.

## Cómo se produjo lo medido
Las capturas, los tiempos y los contrastes salen de `scripts/evidencias/evidencia_capturas_anchos.py` y `evidencia_capturas_movil.py` (navegador sin ventana por DevTools, como en D79) y están registradas en [EV-066 a EV-069](../evidencias/usuarios/EV-066_capturas_anchos.txt). Son mediciones locales de una máquina.

## Alcance y límites
- **Qué afirmamos:** el material de las sesiones está preparado, el análisis está probado con datos sintéticos rotulados y la evaluación heurística interna documenta 14 fricciones con su captura.
- **Con qué evidencia:** esta carpeta, `scripts/usuarios/`, `tests/test_usuarios.py`, `tests/test_usuarios_estructura.py` y EV-065 a EV-069.
- **Qué NO afirmamos:** que alguien haya usado el panel, que sea usable para personas reales ni que los 8 ajustes hechos al panel (iteración técnica, D87 a D90) mejoren la experiencia de personas reales.
