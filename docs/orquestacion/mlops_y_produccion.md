# MLOps y prácticas de producción

**Ítem del checklist (5.4):** «Implementamos metodologías de producción (MLOps, LLMOps), orquestación y flujos programados (DAGs de Airflow).»

> **Procedimiento basado en la guía de Airflow de la asignatura (artículo de Juan Manuel Núñez Velasco).** Esta página describe las prácticas de producción del proyecto; la orquestación sigue la guía y sus diferencias están en [diferencias_con_la_guia.md](diferencias_con_la_guia.md).

El proyecto no entrena modelos: calcula indicadores estadísticos sobre construcciones evaluadas por satélite. Por eso aplicamos las prácticas de MLOps que sí tienen sentido sin modelos y declaramos N/A lo que no (D22).

## 1. Prácticas aplicadas
| Práctica | Cómo la aplicamos | Evidencia |
|---|---|---|
| Código versionado | Git con etiquetas por componente (`carga-mysql`, `orquestacion-inicio`, …) y commits lógicos | `git tag` |
| Datos versionados | Bronze inmutable con manifiesto de 8 líneas con sha256 y línea base de 9 hashes de Silver y Gold | `data/bronze/manifest.jsonl`; EV-001 |
| Artefactos versionados | La imagen se define con un Dockerfile y requisitos con las versiones exactas del entorno | `orquestacion/` |
| Reproducibilidad | El pipeline regenerado en una copia reproduce los nueve archivos byte a byte; pandas se fija en 3.0.6 porque con 3.1.1 cambiaban 3 celdas de `gold_final.csv` | [EV-035](../evidencias/orquestacion/EV-035_estabilidad_pipeline.txt); `tests/test_pipeline_reproducible.py`; D56 |
| Idempotencia | La carga relacional usa una clave de corrida determinista: repetir la ejecución responde «ya cargada» y no escribe | [carga y verificación](../almacenamiento/carga_y_verificacion.md) |
| Comparación con el repositorio | Cada tarea compara lo que produjo con lo versionado y falla si difiere; el repositorio se monta en solo lectura | D58 y D59 |
| Métricas por corrida | Cada corrida guarda sus filas, coberturas y los sha256 de sus entradas en la base relacional | tablas `corrida` y `corrida_archivo` |
| Puerta de calidad | `quality_report.json` y las pruebas de calidad (cobertura de la llave, mínimo de filas, KPI en rango) | `tests/test_quality.py` |
| Programación | Cron explícito `0 6 * * *` en America/Bogota, `catchup=False` | D64 |
| Registros | Registro de cada tarea en Airflow y `src/logger.py` con enmascarado de secretos | [operación](operacion.md) |
| Pruebas | Matriz de casos, cobertura medida, informe de esperado y obtenido y registro de defectos | [matriz](../validacion/matriz_casos_prueba.md), [informe](../validacion/informe_pruebas.md), [defectos](../validacion/registro_defectos.md) |

## 2. Lo que no aplica
| Práctica | Estado | Razón |
|---|---|---|
| Registro de modelos y despliegue de modelos | N/A justificado | no hay modelos entrenados (D22) |
| LLMOps (versionado de instrucciones, evaluación de salidas de un modelo de lenguaje) | N/A justificado | el proyecto no usa modelos de lenguaje en su ejecución (D22) |
| Monitoreo de deriva de datos en producción | no aplicado | los datos son una captura estática (capa editada el 2026-09-02) |

## 3. Arquitectura de la orquestación
El diagrama de la arquitectura de la orquestación (Windows, WSL2, Docker Desktop, Airflow, el DAG, las capas Bronze, Silver y Gold y MySQL) se genera con matplotlib al terminar la ejecución y se agrega a esta página.

## Alcance y límites
- **Qué afirmamos:** aplicamos las prácticas de la tabla 1, cada una con su evidencia.
- **Qué NO afirmamos:** que el proyecto tenga modelos, que Airflow esté endurecido para producción ni que las ejecuciones programadas cubran intervalos con el equipo apagado.
