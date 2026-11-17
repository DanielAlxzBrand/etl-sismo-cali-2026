# ADR-009: Las fuentes se aceptan por criterios verificados, sin bajar ningún umbral

**Estado:** Vigente (implementada). **Fecha de la decisión:** 2026-10-15. **D de origen:** D2, D9, D-FUENTES. **Propietario técnico:** Daniel Alexander Brand García. **Revisión:** pendiente.

## Contexto
El proyecto parte de datos abiertos de terceros. Antes de construir el pipeline había que saber si las fuentes se podían leer sin token, con columnas y cobertura suficientes. La fuente prevista, el conjunto `5vy8-gpw8` de datos.gov.co, no es tabular: responde HTTP 403 en `/resource/*.json`.

## Decisión
- Un plan alternativo se activa por un criterio de aceptación que falla, no por preferencia (D9). Los criterios G1 a G5 de D-FUENTES se evaluaron con evidencia en `docs/bronze/verificacion_fuentes.md` y `docs/bronze/muestras/`.
- No se bajó ningún umbral. G1 no se cumplía tal como estaba escrito y se evaluó sobre el FeatureServer de ArcGIS que enlaza el propio catálogo; se declaró como desviación y no como «pasa» automático.
- El plan elegido (A) usa las construcciones de la capa satelital en 7 comunas de Cali y el estrato por barrio de 2015; los polígonos de barrios solo validan la llave y USGS queda solo como contexto (D8).

## Consecuencias
### Positivas
- Las fuentes finales están documentadas con su origen, fecha de consulta y licencia declarada (`docs/bronze/atribucion_y_terminos_de_datos.md`).
- La cobertura del JOIN se midió sobre las 5.146 construcciones: 99,88 % (6 sin coincidencia).

### Negativas
- Dependemos de un servicio ArcGIS Online de un tercero; la reproducibilidad la garantiza el snapshot de Bronze y no el servicio.
- El estrato es de 2015 y por lados de manzana; entre el estrato y las imágenes hay unos once años de distancia.
- El proxy satelital no es una evaluación estructural y solo cubre 7 comunas; el plan cambió la pregunta (D9 registró ese riesgo).

## Alternativas consideradas entonces
Registradas en `docs/DECISIONES.md`:
- usgs (D2)
- sgc (D2)
- rud (D2)
- a mano (D9)

## Alternativas que hoy descartamos y por qué
Razonamiento actual del equipo, no registrado en su momento.
- **Ampliar el análisis con el plan alternativo (RUD y DIVIPOLA).** Siguen accesibles, pero son datos municipales sin grano de construcción; cambiarían la unidad de análisis y la pregunta, y el proyecto ya cubre el alcance del MVP con la capa satelital.
- **Bajar el umbral de G1 para dar la fuente por válida.** Habríamos ocultado que el endpoint previsto no era tabular. Declarar la desviación costó una línea y mantuvo la regla de no ajustar umbrales después de ver los resultados.
