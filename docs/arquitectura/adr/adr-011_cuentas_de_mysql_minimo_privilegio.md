# ADR-011: Tres cuentas de MySQL con el mínimo privilegio y ningún origen abierto

**Estado:** Vigente (implementada). **Fecha de la decisión:** 2026-11-13 (D46, D60, D65), 2026-11-14 (D67) y 2026-11-15 (D91). **D de origen:** D46, D60, D65, D67, D91. **Propietario técnico:** Daniel Alexander Brand García. **Revisión:** pendiente.

## Contexto
El proyecto guarda sus resultados en un MySQL local. La carga, la tarea del DAG que corre en un contenedor y el visor phpMyAdmin necesitan acceso, y ninguno debería poder más de lo que necesita. Además, las verificaciones destructivas no deben tocar la base real.

## Decisión
- Dos bases, `sismo_cali` (datos reales) y `sismo_cali_prueba` (verificaciones destructivas), creadas por `scripts/mysql/configurar_mysql.py` con la contraseña de `root` tecleada por la persona que la conoce y nunca guardada (D46).
- `sismo_etl`: `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `DROP`, `ALTER`, `INDEX` y `REFERENCES` solo sobre las dos bases del proyecto, sin privilegios globales ni `GRANT OPTION`.
- `sismo_airflow`: `SELECT`, `INSERT`, `CREATE`, `INDEX` y `REFERENCES` solo sobre `sismo_cali`, sin `UPDATE`, `DELETE` ni `ALTER`; la usa la tarea de carga del DAG (D60).
- `sismo_lectura`: solo `SELECT` sobre `sismo_cali`, para phpMyAdmin (D91).
- Ninguna cuenta con origen `%`. Se midió que Docker Desktop entrega al servidor la conexión del contenedor como `localhost`, así que `sismo_airflow` se crea con ese origen (D65).
- Las contraseñas las genera el script al azar y viven solo en `.env`; el escáner de secretos las busca como canarios.

## Consecuencias
### Positivas
- Un `INSERT` con la cuenta de solo lectura es rechazado por MySQL, no por la página (EV-102).
- La tarea del DAG no puede modificar ni borrar datos existentes.
- Las verificaciones destructivas corren solo sobre la base de prueba.

### Negativas
- Cualquier proceso local que tenga una contraseña puede conectarse con esa cuenta: el origen `localhost` no acota por sí solo quién conecta (D67). La protección real es el mínimo privilegio más la contraseña aleatoria.
- `sismo_etl` puede borrar las dos bases (necesita `DROP` para reconstruir la de prueba); el respaldo lógico lo cubre.
- En Docker sobre Linux nativo el origen puede ser otro y habría que volver a medirlo.

## Alternativas consideradas entonces
Registradas en `docs/DECISIONES.md`:
- usar `root` en el proyecto (D46)
- un usuario por base (D46)
- una sola base (D46)
- ampliar `sismo_etl` a otro origen (D60)
- un usuario con `%` (D60)
- que la carga a mysql corra fuera del contenedor (D60)
- el patrón de la red de docker (la conexión no entra) (D65)
- entrar con `sismo_etl` (podría borrar las bases desde la pestaña sql) (D91)
- no ofrecer ningún visor (D91)

## Alternativas que hoy descartamos y por qué
Razonamiento actual del equipo, no registrado en su momento.
- **Un gestor de secretos o un servicio de identidad.** Todo corre en una máquina local con 3 contraseñas; el `.env` fuera del repositorio, el escáner y el canario cubren lo que hoy necesitamos, y un gestor agregaría un servicio más que mantener.
- **Una sola cuenta con todos los permisos.** Facilitaría la configuración, pero entonces el visor podría borrar tablas; con tres cuentas, un permiso que el servidor no concede no se puede saltar desde el navegador.
