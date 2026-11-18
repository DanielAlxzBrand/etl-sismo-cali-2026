# ADR-002: La llave del JOIN es el código catastral, no el nombre del barrio

**Estado:** Vigente (implementada). **Fecha de la decisión:** 2026-10-15. **D de origen:** D4, D-FUENTES, sección «Llave del JOIN». **Propietario técnico:** Daniel Alexander Brand García. **Revisión:** Jhoan Sebastián Castellanos Mayor, 2026-11-18.

## Contexto
Para saber el estrato de cada construcción hay que unir la capa satelital con el CSV de estrato por barrio. La decisión inicial (D4) era unir por el nombre normalizado del barrio y usar lo espacial solo si faltaba. Al verificar las fuentes resultó que las construcciones no traen el nombre del barrio, sino `COMUNA` y `BARRIO` como códigos de dos dígitos, y que el CSV trae un `Código único`.

## Decisión
La llave es `codigo_barrio = int(COMUNA) * 100 + int(BARRIO)` como texto sin ceros a la izquierda, contra el `Código único` del CSV. El JOIN es un LEFT JOIN desde las construcciones, y los registros sin pareja se guardan como huérfanos en lugar de descartarse. Los polígonos de barrios de 2026 no participan en el JOIN: solo validan la llave. D4 quedó marcada como modificada por D-FUENTES.

## Consecuencias
### Positivas
- Cobertura de llave de 99,883 % (5.140 de 5.146 construcciones) y de estrato válido de 99,845 %.
- Ninguna construcción desaparece: 6 quedan como huérfanos a la izquierda y 295 barrios del CSV como huérfanos a la derecha.
- La validación semántica (nombre del CSV contra nombre del polígono) deja la confianza de la llave en «alta» sin cambiar la llave.

### Negativas
- El código catastral difiere del código del polígono 2026 en 8,6 % de las construcciones, sobre todo por renumeración de códigos entre 2015 y 2026; D-FUENTES lo registró como riesgo.
- La revisión visual en el mapa de los códigos con diferencias sigue pendiente.

## Alternativas consideradas entonces
Registradas en `docs/DECISIONES.md`:
- código de barrio; comuna (D4)
- nombre normalizado (las edificaciones no traen nombre) (sección «Llave del JOIN»)
- punto-en-polígono con los polígonos 2026 (sección «Llave del JOIN»)

## Alternativas que hoy descartamos y por qué
Razonamiento actual del equipo, no registrado en su momento.
- **Unir por similitud de nombres.** Solo 93,52 % de las construcciones con llave están en un código cuyo nombre coincide con el del polígono, frente a 99,883 % de cobertura con el código; la similitud agregaría decisiones de umbral sin ganar cobertura.
- **Unir por polígonos 2026.** El código del polígono coincide con el derivado en 91,43 % de las construcciones, y solo 73 % de los códigos de los polígonos 2026 existen en el CSV de 2015 (D-FUENTES): una parte de las construcciones quedaría sin estrato por una renumeración y no por falta de dato.
