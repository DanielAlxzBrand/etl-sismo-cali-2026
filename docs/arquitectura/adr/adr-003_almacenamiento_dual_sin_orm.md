# ADR-003: SQLite como almacén de referencia, MySQL como almacén relacional y SQL explícito sin ORM

**Estado:** Vigente (implementada). **Fecha de la decisión:** 2026-10-15 (salida en CSV y SQLite) y 2026-11-13 (MySQL). **D de origen:** D10, D19, D40, D41. **Propietario técnico:** Daniel Alexander Brand García. **Revisión:** pendiente.

## Contexto
Gold se entrega como archivos CSV. Necesitábamos además una base de datos para recalcular los indicadores con SQL de forma independiente (D10) y, después, un almacén relacional con historial, claves y restricciones (D19). MySQL 8.0 ya estaba instalado y escuchando en el equipo, y el pipeline ya estaba validado con SQLite.

## Decisión
`data/gold/etl_sismo.db` (SQLite) se mantiene como almacén de referencia del pipeline: lo escribe `main.py --stage gold` y sirve para pruebas sin servidor. MySQL 8.0 se agrega como almacén relacional con historial; su carga es independiente de las etapas (`scripts/cargar_mysql.py`), solo lee `data/` y no modifica `main.py` ni `load_database.py`. La carga usa PyMySQL con sentencias SQL parametrizadas y `executemany`, sin ORM; el esquema se escribe a mano en dos archivos (`esquema_mysql.sql` y `esquema_sqlite.sql`) con una prueba de paridad.

## Consecuencias
### Positivas
- No se toca lo ya validado: SQLite sigue sirviendo sin servidor y la carga a MySQL se repite sin volver a ejecutar el pipeline.
- Con siete tablas, las sentencias SQL se pueden leer completas y revisar; la única dependencia nueva, además de PyMySQL, es `cryptography` (autenticación de MySQL 8.0).
- La API elige el motor con `api.almacenamiento` y una prueba de equivalencia compara sus respuestas.

### Negativas
- Los dos almacenes pueden divergir; lo vigilan la conciliación (conteos, sumas y ida y vuelta de valores) y la prueba de equivalencia de la API.
- Hay más SQL a mano; lo cubren las pruebas de esquema, de carga y de integridad.
- Cuando MySQL no responde, la API contesta 503; el valor por defecto sigue siendo SQLite.

## Alternativas consideradas entonces
Registradas en `docs/DECISIONES.md`:
- solo csv (D10)
- sqlalchemy (D19)
- postgresql en docker (D19)
- solo sqlite con matiz (D19)
- reemplazar sqlite por mysql (D40)
- escribir en ambos desde el pipeline (D40)
- el conector oficial de oracle (D41)

## Alternativas que hoy descartamos y por qué
Razonamiento actual del equipo, no registrado en su momento.
- **Una base columnar o un almacén en la nube.** El volumen es de 5.146 construcciones y la carga completa a MySQL (5.622 filas de datos) tarda 0,715 s con lotes de 2.000 filas; SQLite pesa 1,6 MB. No hay un problema de escala que justifique otra pieza.
- **Un ORM para generar las tablas.** El esquema tiene siete tablas y un ORM escondería el SQL que queremos que se pueda revisar en una sola lectura.
