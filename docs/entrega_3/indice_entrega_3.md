# Entrega 3: índice del checklist por fases

**Fecha:** 2026-11-12 · La Entrega 3 es un entregable distinto del Avance 2; la retroalimentación del Avance 2 ya se atendió y no es insumo de este checklist. La fecha límite y la rúbrica de la Entrega 3 no constan. [Criterio aplicado: ruta de fases del análisis previo]

## Mapa por fases
| fase | nombre | ítems que cierra | ítems que solo aporta evidencia | qué deja | dónde se guarda la evidencia |
|---|---|---|---|---|---|
| Base y orden | Línea base, orden y material de referencia | ninguno (prepara las demás) | 7.1 | Línea base protegida, saltos de línea fijados, repositorio reorganizado, entorno documentado | `docs/evidencias/base/` |
| Estrategia | Decisiones y sección 1 | 1.1, 1.2, 1.3, 1.4 | 1.5 | Decisiones de arquitectura (ADR) y revalidación de la sección 1 | carpeta evidencias/f1 (se crea en esa fase) |
| API, fuentes y credenciales | Backend, API de solo lectura, fuentes y credenciales | 2.1, 2.2, 2.3 | — | API sobre Gold, catálogo de fuentes y política de credenciales | `docs/evidencias/api/` |
| Carga relacional | Carga relacional a MySQL | 4.1, 4.2, 4.3 | — | Almacén relacional con claves, historial y carga por lotes | carpeta evidencias/f3 (se crea en esa fase) |
| Pruebas y orquestación | Pruebas técnicas, MLOps y orquestación con Airflow en Windows | 5.1, 5.2, 5.4, 5.5, 5.6 | 2.1, 2.3, 4.1, 4.2 | Matriz de casos, informe de pruebas, DAG validado | carpeta evidencias/f4 (se crea en esa fase) |
| Panel | Dashboard con Streamlit | 1.5, 3.1, 3.2, 5.3 | 3.3 | Dashboard sobre la API, pruebas de integración y criterios del MVP | carpeta evidencias/f5 (se crea en esa fase) |
| Usuarios, UX y finanzas | Usuarios, UX y finanzas | 3.3, 6.1, 6.2, 6.3, 6.4 | — | Materiales de pruebas con usuarios y análisis de costos (las sesiones son un hecho externo) | carpeta evidencias/f6 (se crea en esa fase) |
| Documentación y demostración | Documentación, iteraciones y demo | 6.5, 7.2, 7.3, 7.4, 7.5 | 1.3, 6.3 | README, arquitectura, iteraciones con evidencia real y guion de demostración | carpeta evidencias/f7 (se crea en esa fase) |
| Cierre y paquete | Checklist final y paquete | 7.1 | 1.1, 1.2, 1.3, 1.4, 1.5, 3.1, 3.2, 5.1, 5.3, 5.4, 5.5, 5.6, 6.1, 6.2, 6.4, 6.5, 7.2, 7.3, 7.4, 7.5 | Checklist rellenado, manifiesto final y zip verificado en un clon limpio | carpeta evidencias/f8 (se crea en esa fase) |

## Estructura de `docs/`
- `entorno.md`: estado del entorno y qué falta para cada fase.
- `estado_checklist.md`: los 30 ítems con su estado actual y objetivo.
- `decisiones_tecnicas.md`: decisiones técnicas de las fases API, fuentes y credenciales, Carga relacional, Pruebas y orquestación, Panel, Usuarios, UX y finanzas, Documentación y demostración y Cierre y paquete.
- `seccion_1/`: documentos de la sección 1 (se revalidan en el componente Estrategia).
- `arquitectura.md`: arquitectura del backend y de la API de solo lectura (API, fuentes y credenciales, ítem 2.1).
- `catalogo_fuentes_metadatos.md` y `catalogo_fuentes.json`: catálogo de fuentes y metadatos generado desde el manifiesto (API, fuentes y credenciales, ítem 2.2).
- `gestion_credenciales.md`: política de credenciales, claves y tokens (API, fuentes y credenciales, ítem 2.3).
- `verificacion_servicios.md`: subcriterios, brechas, evidencia y estado de los ítems 2.1 a 2.3.
- `img/`: imágenes renderizadas a partir de los documentos (matriz poder-interés, Canvas y arquitectura del backend); no son capturas de pantalla.
- `evidencias/`: `manifiesto.md`, `guia_de_evidencias.md` y una carpeta por fase (`f0/` ya tiene su evidencia).

## Reglas de trabajo
- Rama `entrega-3`; etiqueta de partida `base-entrega-3`; una etiqueta por fase (`entrega3-f0`, `entrega3-f1`, …). Detalle en `docs/DECISIONES.md` (D14).
- La línea base de sha256 de Silver, Gold y del manifiesto de Bronze no cambia; el pipeline se ejecuta solo en un clon temporal (D15).
- Política de evidencias (D35): sin video. Cada ítem se respalda con archivos adjuntables (salidas registradas, JSON, XML de pruebas, documentos e imágenes renderizadas) y, de forma opcional, capturas de pantalla; la guía por ítem es `evidencias/guia_de_evidencias.md`. Nada de lo que requiera un hecho externo (sesiones con usuarios, retroalimentación, respuesta del profesor) se fabrica.
