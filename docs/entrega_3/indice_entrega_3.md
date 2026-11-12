# Entrega 3: índice del checklist por fases

**Fecha:** 2026-11-12 · La Entrega 3 es un entregable distinto del Avance 2; la retroalimentación del Avance 2 ya se atendió y no es insumo de este checklist. La fecha límite y la rúbrica de la Entrega 3 no constan. [Criterio aplicado: ruta de fases del análisis previo]

## Mapa por fases
| fase | nombre | ítems que cierra | ítems que solo aporta evidencia | qué deja | dónde se guarda la evidencia |
|---|---|---|---|---|---|
| F0 | Línea base, orden y material de referencia | ninguno (prepara las demás) | 7.1 | Línea base protegida, saltos de línea fijados, repositorio reorganizado, entorno documentado | `docs/entrega_3/evidencias/f0/` |
| F1 | Decisiones y sección 1 | 1.1, 1.2, 1.3, 1.4 | 1.5 | Decisiones de arquitectura (ADR) y revalidación de la sección 1 | carpeta evidencias/f1 (se crea en esa fase) |
| F2 | Backend, API de solo lectura, fuentes y credenciales | 2.1, 2.2, 2.3 | — | API sobre Gold, catálogo de fuentes y política de credenciales | carpeta evidencias/f2 (se crea en esa fase) |
| F3 | Carga relacional a MySQL | 4.1, 4.2, 4.3 | — | Almacén relacional con claves, historial y carga por lotes | carpeta evidencias/f3 (se crea en esa fase) |
| F4 | Pruebas técnicas, MLOps y orquestación con Airflow en Windows | 5.1, 5.2, 5.4, 5.5, 5.6 | 2.1, 2.3, 4.1, 4.2 | Matriz de casos, informe de pruebas, DAG validado | carpeta evidencias/f4 (se crea en esa fase) |
| F5 | Dashboard con Streamlit | 1.5, 3.1, 3.2, 5.3 | 3.3 | Dashboard sobre la API, pruebas de integración y criterios del MVP | carpeta evidencias/f5 (se crea en esa fase) |
| F6 | Usuarios, UX y finanzas | 3.3, 6.1, 6.2, 6.3, 6.4 | — | Materiales de pruebas con usuarios y análisis de costos (las sesiones son un hecho externo) | carpeta evidencias/f6 (se crea en esa fase) |
| F7 | Documentación, iteraciones y demo | 6.5, 7.2, 7.3, 7.4, 7.5 | 1.3, 6.3 | README, arquitectura, iteraciones con evidencia real y guion de demostración | carpeta evidencias/f7 (se crea en esa fase) |
| F8 | Checklist final y paquete | 7.1 | 1.1, 1.2, 1.3, 1.4, 1.5, 3.1, 3.2, 5.1, 5.3, 5.4, 5.5, 5.6, 6.1, 6.2, 6.4, 6.5, 7.2, 7.3, 7.4, 7.5 | Checklist rellenado, manifiesto final y zip verificado en un clon limpio | carpeta evidencias/f8 (se crea en esa fase) |

## Estructura de `docs/entrega_3/`
- `entorno.md`: estado del entorno y qué falta para cada fase.
- `estado_checklist.md`: los 30 ítems con su estado actual y objetivo.
- `seccion_1/`: documentos de la sección 1 (se revalidan en F1).
- `evidencias/`: `MANIFIESTO_EVIDENCIAS.md`, `guion_capturas_y_video.md` y una carpeta por fase (`f0/` ya tiene su evidencia).

## Reglas de trabajo
- Rama `entrega-3`; etiqueta de partida `base-entrega-3`; una etiqueta por fase (`entrega3-f0`, `entrega3-f1`, …). Detalle en `docs/DECISIONES.md` (D-E3-04).
- La línea base de sha256 de Silver, Gold y del manifiesto de Bronze no cambia; el pipeline se ejecuta solo en un clon temporal (D-E3-05).
- Las capturas de pantalla y los videos los toma el equipo con un guion; nada de lo que requiera un hecho externo (sesiones con usuarios, retroalimentación, respuesta del profesor) se fabrica.
