# Pruebas y orquestación

**Componente:** Pruebas y orquestación · **Ítems del checklist:** 5.1, 5.2, 5.4, 5.5 y 5.6; criterios AC26 y AC27; revalidación del 2.3 y avance del 7.1.

> **Procedimiento basado en la guía de Airflow de la asignatura (artículo de Juan Manuel Núñez Velasco).** La guía no se copia aquí: citamos sus pasos por número, parafraseamos y adaptamos el código a nuestro proyecto.

Este componente orquesta con Apache Airflow (Docker Compose) el pipeline medallion del sismo del 10-ago-2026 y reúne las pruebas que lo respaldan. El DAG `medallon_etl_sismo` tiene las cuatro tareas de la guía (`validar_bronze → transformar_a_silver → integrar_a_gold → cargar_datawarehouse`), trabaja sobre una copia del proyecto y compara sus salidas con lo versionado, de modo que el repositorio **nunca se escribe**.

## Documentos
| Documento | Qué contiene |
|---|---|
| [diferencias_con_la_guia.md](diferencias_con_la_guia.md) | las diferencias permitidas (DF-1 a DF-12) con su motivo y los hallazgos de la guía (H-n) |
| [guia_de_implementacion.md](guia_de_implementacion.md) | los pasos 13 a 44 de la guía con su estado («tal cual» o con diferencia) y su evidencia |
| [mlops_y_produccion.md](mlops_y_produccion.md) | prácticas de producción aplicadas (versionado, datos, reproducibilidad, idempotencia, programación) y lo que no aplica |
| [operacion.md](operacion.md) | cómo levantar, parar, ver registros y resolver problemas |
| [../validacion/matriz_casos_prueba.md](../validacion/matriz_casos_prueba.md) | matriz de casos de prueba por función crítica (ítem 5.1) |
| [../validacion/informe_pruebas.md](../validacion/informe_pruebas.md) | resultado esperado, obtenido y evidencia por prueba, con cobertura y métricas del análisis (ítem 5.5) |
| [../validacion/registro_defectos.md](../validacion/registro_defectos.md) | defectos encontrados, corregidos y su prueba de regresión (ítem 5.6) |
| [../../orquestacion/README.md](../../orquestacion/README.md) | Dockerfile, requisitos y procedimiento que se copian a la carpeta `airflow-medallon` |

## Dónde está cada cosa
- **DAG versionado:** `dags/medallon_etl_dag.py`; el DAG vivo está en la carpeta hermana `airflow-medallon/dags` y `scripts/orquestacion/sincronizar_dag.py` los mantiene iguales.
- **Imagen:** `orquestacion/Dockerfile` y `orquestacion/requirements-airflow.txt` (versiones iguales a las del `.venv`, con pandas 3.0.6; D56).
- **Usuario de MySQL para el contenedor:** `scripts/mysql/configurar_mysql.py --usuario-docker` (D60; [configuración de MySQL](../almacenamiento/mysql_configuracion.md)).
- **Evidencias:** `docs/evidencias/orquestacion/` (EV-035 en adelante).

## Alcance y límites
- **Qué afirmamos:** el DAG, la imagen, los requisitos y las pruebas están definidos y se prueban de forma estática y con el pipeline en una copia; la ejecución en Docker se registra paso a paso en la guía de implementación.
- **Qué NO afirmamos:** que Airflow esté pensado para producción multiusuario (es un uso local con el compose de desarrollo de la guía), que las pruebas del laboratorio de clase (reintentos, cinco tareas, programación horaria) se hayan implementado ni que los datos sean una evaluación estructural: seguimos analizando un proxy satelital sobre construcciones de siete comunas, sin generalizar a toda Cali.
