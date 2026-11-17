# ADR-008: Pruebas sin servidor, casos generados y regresión por reintroducción

**Estado:** Vigente (implementada). **Fecha de la decisión:** 2026-11-13. **D de origen:** D49, D61, D62, D63. **Propietario técnico:** Daniel Alexander Brand García. **Revisión:** pendiente.

## Contexto
Queríamos una suite que cualquiera pudiera correr sin red, sin MySQL y sin Docker, y que demostrara que cada corrección está protegida. Una prueba que se omite sin servidor, o que no falla cuando el defecto vuelve, no sirve como evidencia.

## Decisión
- La suite de `pytest` no necesita MySQL: ejercita el esquema y la carga sobre SQLite con claves foráneas activas y simula las conexiones de `configurar_mysql.py`. Lo que exige el servidor vive en `scripts/mysql/verificar_mysql.py`, sobre la base de prueba, y deja evidencia (D49 y D61).
- `scripts/make_matriz_casos.py` genera la matriz de casos (CP-nnn) desde una definición única y una prueba exige que cada caso apunte a una prueba existente. `scripts/informe_pruebas.py` ejecuta la suite con `coverage` y escribe el informe de esperado y obtenido, sin umbral de cobertura impuesto (D62).
- `docs/validacion/registro_defectos.md` lista cada defecto con su causa, corrección y prueba, y `scripts/validacion/verificar_regresiones.py` reintroduce el defecto en una copia y exige que su prueba falle sin la corrección (D63).

## Consecuencias
### Positivas
- La suite corre en un clon nuevo sin omitir pruebas; en el zip se omite una sola, la que necesita el historial de Git.
- Las cifras de los documentos y de las insignias se comprueban contra lo medido.
- Hay **25 defectos** registrados (DEF-001 a DEF-025). Para 15 se demostró que su prueba de regresión falla sin la corrección. Para los otros 10 no se demostró (DEF-003, DEF-006, DEF-009, DEF-010, DEF-011, DEF-014 y DEF-022 a DEF-025) y el registro da el motivo de cada uno.

### Negativas
- La verificación contra MySQL real no corre en cada `pytest`; hay que ejecutarla cuando cambia la carga.
- SQLite no ve diferencias de motor; las cubre la verificación en vivo.
- La cobertura no cuenta lo que se ejecuta en subprocesos (el pipeline en `test_pipeline_reproducible`), así que la cifra de `src/` es una cota inferior.

## Alternativas consideradas entonces
Registradas en `docs/DECISIONES.md`:
- pruebas que requieren mysql activo (D49)
- marcadores de omisión (D49)
- un marcador `mysql` que omita las pruebas sin servidor (D61)
- una matriz escrita a mano (D62)
- fijar un umbral de cobertura (D62)
- solo narrar los defectos (D63)

## Alternativas que hoy descartamos y por qué
Razonamiento actual del equipo, no registrado en su momento.
- **Levantar un MySQL de prueba en contenedor dentro de cada ejecución de la suite.** La suite completa ya tarda de 5 a 7 minutos en esta máquina y no hay integración continua que la ejecute; sumar un servidor haría que quien solo quiere ver las cifras necesitara Docker.
- **Exigir un porcentaje mínimo de cobertura.** La cobertura de `src/` es de 78 % y los módulos con 0 % se ejecutan en subprocesos o descargan de la red; un umbral empujaría pruebas artificiales para subir un número.
