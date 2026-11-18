# ADR-006: El DAG trabaja sobre una copia y compara lo que produce con lo versionado

**Estado:** Vigente (implementada). **Fecha de la decisión:** 2026-11-13. **D de origen:** D58, D59. **Propietario técnico:** Daniel Alexander Brand García. **Revisión:** Jhoan Sebastián Castellanos Mayor, 2026-11-18.

## Contexto
Las salidas del pipeline son la línea base del proyecto: nueve archivos cuyos sha256 se comprueban. Un DAG que escribiera en el repositorio podía alterarlas sin que nadie lo notara, y SQLite no escribe el archivo de base de datos igual byte a byte entre ejecuciones.

## Decisión
- El repositorio se monta en `/opt/airflow/medallon` en solo lectura y nunca se escribe. `validar_bronze` crea una copia mínima (`src`, `config`, `data` y `docs/silver/hallazgos_eda.md`) en una carpeta única por ejecución dentro del contenedor; `src` se importa solo desde esa copia, y la copia se elimina al terminar o si una tarea falla (D58).
- Cada tarea compara lo que produjo con lo versionado: CSV y JSON byte a byte (sha256) y `etl_sismo.db` tabla a tabla por contenido. Si algo difiere, la tarea falla (D59).

## Consecuencias
### Positivas
- El DAG no puede dañar la línea base: la prueba con un intento de crear un archivo en el proyecto montado respondió «Read-only file system» (EV-100).
- Cualquier diferencia entre lo que Airflow produce y lo versionado se detecta en la tarea que la causa.
- Tras un fallo inducido no queda ninguna copia de trabajo en el contenedor (EV-042).

### Negativas
- Una actualización de dependencias cambiaría las salidas y las tareas fallarían; es el comportamiento buscado, pero obliga a decidir qué hacer (ver ADR-007).
- Con un solo trabajador la copia es local al contenedor; con varios, las tareas tendrían que compartirla. El compose usa uno.
- Los documentos Markdown que regenera la transformación no se comparan.

## Alternativas consideradas entonces
Registradas en `docs/DECISIONES.md`:
- escribir en el repositorio montado (D58)
- montar `data/` con escritura (D58)
- comparar con tolerancia numérica (D59)
- comparar el archivo sqlite completo (D59)

## Alternativas que hoy descartamos y por qué
Razonamiento actual del equipo, no registrado en su momento.
- **Un volumen compartido de salidas entre tareas.** Con un trabajador y cuatro tareas que terminan en 9 a 12 segundos en total (EV-064 y EV-100), la copia local es más simple y se borra sola; un volumen compartido agregaría estado que limpiar.
- **Ejecutar el pipeline directamente en el contenedor sin comparar.** Dejaría de demostrar que Airflow no cambia los resultados, que es justo lo que queremos poder afirmar.
