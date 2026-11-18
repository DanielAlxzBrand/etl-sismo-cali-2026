# ADR-001: Bronze guarda lo descargado sin tocarlo

**Estado:** Vigente (implementada). **Fecha de la decisión:** 2026-10-15. **D de origen:** D6. **Propietario técnico:** Daniel Alexander Brand García. **Revisión:** Jhoan Sebastián Castellanos Mayor, 2026-11-18.

## Contexto
Descargamos tres fuentes de terceros (una capa ArcGIS, un CSV de estrato y los polígonos de barrios) que pueden cambiar o desaparecer. Si el proyecto leyera siempre la versión viva de la fuente, no podríamos demostrar de dónde salió cada cifra ni repetir un análisis. Además, los resultados que entregamos se calculan una sola vez sobre una captura del evento.

## Decisión
La capa Bronze guarda la respuesta cruda de cada petición, byte a byte, en `data/bronze/`, y `data/bronze/manifest.jsonl` registra una línea por archivo con su origen, su fecha y su sha256. Los archivos se abren en modo exclusivo y nunca se sobrescriben. Una extracción cuenta como completa solo si existe el conteo posterior de la capa. Si Bronze ya existe, `main.py --stage extract` verifica los sha256 y no descarga nada; `--refresh` crea un snapshot nuevo sin tocar el anterior.

## Consecuencias
### Positivas
- Cada cifra se rastrea hasta un archivo con su sha256, y `validar_bronze` del DAG falla si algún archivo no coincide con el manifiesto.
- Las pruebas y el pipeline corren sin red: Bronze está en el repositorio (8 líneas de manifiesto, 11 MB en total en `data/`).
- Repetir la extracción no duplica nada.

### Negativas
- Hay más archivos que con un solo CSV consolidado (tres páginas de la API más los conteos, el metadato de la capa, el CSV y los polígonos).
- Un cambio en la fuente solo se ve al hacer `--refresh`; no hay una comprobación automática de esquema (ver el documento de arquitectura, sección 9).

## Alternativas consideradas entonces
Registradas en `docs/DECISIONES.md`:
- csv consolidado (D6)

## Alternativas que hoy descartamos y por qué
Razonamiento actual del equipo, no registrado en su momento.
- **Guardar las capturas en un almacenamiento de objetos o en un formato con versiones de tablas.** Bronze pesa pocos megabytes y Git ya versiona los archivos; el manifiesto con sha256 da la misma garantía de integridad sin una herramienta más.
- **Sobrescribir Bronze con la última descarga.** Rompería la reproducibilidad: las salidas de la línea base dependen de esta captura, y las pruebas comparan nueve archivos byte a byte contra ella.
