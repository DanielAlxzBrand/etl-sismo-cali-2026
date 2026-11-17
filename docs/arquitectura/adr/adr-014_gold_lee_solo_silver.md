# ADR-014: Gold lee solo Silver y el paso espacial vive en Silver

**Estado:** Vigente (implementada). **Fecha de la decisión:** 2026-10-15. **D de origen:** D5, sección «Diseño», sección «Otras decisiones de Silver». **Propietario técnico:** Daniel Alexander Brand García. **Revisión:** pendiente.

## Contexto
Gold calcula los indicadores K1 a K6 sobre construcciones ya limpias y unidas con el estrato. Había que decidir qué capa lee a cuál, y dónde ubicar el único paso que necesita los polígonos de barrios: ubicar el centroide de cada construcción en un polígono de 2026 para validar la llave del JOIN.

## Decisión
- Gold lee solo `silver_integrated.csv` y `config/config.yaml`; nunca lee Bronze.
- El paso espacial se calcula en Silver, en la regla R09: centroide de la huella con 7 decimales y punto en polígono con `shapely`. Deja en la tabla integrada el polígono donde cae cada construcción y si su código coincide con la llave. Solo valida la llave: no entra al JOIN.
- Como consecuencia, Gold no conoce los formatos crudos de las fuentes ni necesita los polígonos. D5 quedó marcada como modificada por D106: `shapely` sí se usa, y se usa en Silver.

## Consecuencias
### Positivas
- Gold se regenera desde un solo archivo de entrada, y la línea base de nueve archivos comprueba el resultado byte a byte.
- Una regla de limpieza vive en un solo lugar: Silver, con 18 reglas (R01 a R18) cada una ligada a su hallazgo.
- Gold no depende de `shapely` ni de leer archivos de Bronze.

### Negativas
- Silver concentra más responsabilidad: un cambio en una regla de Silver cambia las entradas de todo Gold.
- Gold no puede recuperar algo que Silver descartó, como las columnas vacías o sin uso de la regla R10, sin modificar Silver.
- La validación espacial añade `shapely` a la transformación de Silver y obliga a leer los polígonos cada vez que se regenera.

## Alternativas consideradas entonces
No se registraron alternativas.

## Alternativas que hoy descartamos y por qué
Razonamiento actual del equipo, no registrado en su momento.
- **Que Gold lea Bronze directamente.** Tendría que repetir la limpieza: Bronze son 8 archivos crudos (tres páginas JSON de la API, el CSV de estrato de 16.030 bytes con miles con coma y guiones como cero, y 342 polígonos en 1.850.751 bytes), y Silver aplica 18 reglas sobre ellos. Una regla repetida en dos capas podría divergir, y la línea base de nueve archivos lo detectaría tarde.
- **Hacer el paso espacial en Gold.** Gold necesitaría `shapely` y volver a leer los 1.850.751 bytes de polígonos de Bronze solo para validar una llave que no entra al JOIN. En Silver la validación queda junto a las otras 17 reglas y se hace una vez.
