# ADR-004: Cada carga a MySQL es una corrida completa, con clave determinista y una sola transacción

**Estado:** Vigente (implementada). **Fecha de la decisión:** 2026-11-13. **D de origen:** D43, D44, D45, D53. **Propietario técnico:** Daniel Alexander Brand García. **Revisión:** pendiente.

## Contexto
El almacén relacional debía conservar historia y poder repetirse sin duplicar datos ni dejar cargas a medias. El volumen de una carga es de unas cinco mil filas, y los datos son una captura del evento, no un flujo de cambios.

## Decisión
- Cada carga crea una fila en `corrida` y todas las tablas de datos llevan `corrida_id` en su clave primaria: una corrida es una copia completa del estrato por barrio, de las construcciones de Gold y de los indicadores, no un registro de cambios (D43).
- `clave_corrida` es el SHA-256 de las líneas `ruta:sha256` de los archivos de entrada, ordenadas, más la versión del esquema. Si la clave ya existe, la carga responde `ya_cargada` y no cambia nada (D44).
- Toda la carga va en una sola transacción con `ROLLBACK` ante cualquier error; la lectura y conversión de los CSV ocurre antes de tocar la base (D45).
- La carga usa lotes de 2.000 filas, fijados por medición: 0,715 s frente a 2,415 s fila a fila, con 5.622 filas de datos por carga (D53).

## Consecuencias
### Positivas
- Mismas entradas, misma clave: la carga es idempotente. Cualquier cambio de datos o de esquema genera una corrida nueva.
- Una carga a medias nunca queda visible; una prueba con un error inyectado a mitad de carga lo demuestra.
- Comparar corridas o reproducir un momento anterior se hace con consultas simples.

### Negativas
- El historial crece de forma lineal con las corridas; a esta escala es irrelevante y está documentado.
- Una transacción larga bloquearía otras escrituras; a esta escala dura menos de un segundo.
- El tamaño de lote depende del equipo y podría chocar con `max_allowed_packet` en otro servidor; con 2.000 filas de este esquema no ocurrió.

## Alternativas consideradas entonces
Registradas en `docs/DECISIONES.md`:
- tablas de cambios con vigencia (desde/hasta) (D43)
- solo la última carga (D43)
- marca de tiempo (D44)
- contador (D44)
- confirmar por tabla (D45)
- confirmar por lote (D45)
- dejar 1000 (D53)
- elegir 500 por usar menos memoria (D53)

## Alternativas que hoy descartamos y por qué
Razonamiento actual del equipo, no registrado en su momento.
- **Dimensiones de cambio lento (SCD) o captura de cambios.** La fuente es una captura única: no llegan cambios que registrar. Una corrida completa de unas 5.600 filas es más simple de consultar y de borrar que una tabla de vigencias.
- **Carga incremental.** Con 5.146 construcciones y una carga de menos de un segundo, la complejidad de calcular qué cambió no se paga; además, una corrida idéntica ya responde `ya_cargada` sin escribir.
