# Sesiones reales

**Esta carpeta está vacía de resultados hasta que el equipo realice sesiones reales con personas usuarias.** Hoy solo contiene las tres plantillas, con su encabezado y ninguna fila. No hay participantes, tiempos ni respuestas, y no se inventan.

## Qué va aquí y qué no
- **Va:** una fila por tarea y persona en `registro.csv`, una fila por persona en `cuestionarios.csv` y, si el equipo lo decide, las fricciones observadas en `friccion.csv`; todos con códigos `P01`, `P02`… y con `origen = real`.
- **No va:** nombres, correos, fotos, grabaciones, firmas, el consentimiento firmado ni notas con nombres. Eso lo guarda el equipo fuera del repositorio.

## Cómo se usan las plantillas
1. Copiar `plantilla_registro.csv` como `registro.csv`, `plantilla_cuestionarios.csv` como `cuestionarios.csv` y `plantilla_friccion.csv` como `friccion.csv` (las plantillas no se editan).
2. Llenar una fila por tarea (`T1` a `T6` del [guion](../guion_sesion.md)) con `resultado` = `exito`, `exito_con_ayuda` o `fracaso`, el `tiempo_s` en segundos, el número de `ayudas` y de `errores` y un comentario breve **sin nombres**.
3. La columna `origen` **solo admite `real`** en esta carpeta: el script de análisis rechaza cualquier otra fila (en particular, las sintéticas, que viven en [`../simulacion/`](../simulacion/), y las simuladas, que viven en [`../sesiones_simuladas/`](../sesiones_simuladas/README.md) y nunca van aquí).
4. Correr `python scripts/usuarios/analizar_sesiones.py`; escribe [`../resultados.md`](../resultados.md).

## Qué NO demuestra
Que se haya hecho alguna sesión: mientras aquí solo haya plantillas, los ítems 6.1, 6.2, 6.3, 6.5 y 7.4 siguen pendientes por un hecho externo.
