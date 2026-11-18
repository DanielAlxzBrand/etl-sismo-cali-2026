# ADR-005: Airflow en Docker orquesta el pipeline con cuatro tareas

**Estado:** Vigente (implementada). **Fecha de la decisión:** 2026-11-12 (D21), reemplazada en parte el 2026-11-13 (D57) y el 2026-11-15 (D92). **D de origen:** D21, D57, D64, D92. **Propietario técnico:** Daniel Alexander Brand García. **Revisión:** Jhoan Sebastián Castellanos Mayor, 2026-11-18.

## Contexto
El ítem 5.4 del checklist pide orquestación con flujos programados. Queríamos un DAG que ejecutara el pipeline sin escribir en el repositorio y que cualquier persona pudiera levantar desde el zip. D21 planeó una variante ligera de Airflow (ejecutor local, sin Redis ni Celery) por la memoria libre medida entonces; al seguir el procedimiento del artículo citado en la [sección 18 del documento de arquitectura](../arquitectura_del_sistema.md#18-glosario-y-referencias), el compose real usa CeleryExecutor, Postgres y Redis (D57). Por eso D21 quedó marcada como modificada por D57 y D92.

## Decisión
- Apache Airflow 3.3.2 en Docker Compose, con la imagen construida desde `orquestacion/Dockerfile` y las versiones del entorno; Postgres 16 y Redis 7.2 fijados por su resumen.
- El compose de `orquestacion/docker-compose.yaml` lo genera `scripts/orquestacion/generar_compose.py` a partir del oficial (se comprueba su sha256) con diferencias documentadas: carpeta del proyecto montada en solo lectura, puerto solo en `127.0.0.1`, y la clave Fernet, el secreto JWT y las contraseñas obligatorios desde el `.env` de Airflow (D92).
- El DAG `medallon_etl_sismo` tiene cuatro tareas (`validar_bronze`, `transformar_a_silver`, `integrar_a_gold`, `cargar_datawarehouse`), `schedule="0 6 * * *"` en America/Bogota y `catchup=False` (D64).
- Se valida primero a mano y luego se programa; el DAG nace en pausa, así que se activa con `airflow dags unpause`.

## Consecuencias
### Positivas
- Cada tarea deja su estado y su duración en la interfaz de Airflow; un fallo detiene las tareas siguientes.
- El zip trae el compose ya adaptado, y `scripts/orquestacion/preparar_airflow.py` prepara la carpeta de Airflow sin pedir editar archivos a mano.
- Una ejecución completa del DAG tarda de 9 a 12 segundos (EV-064 y EV-100).

### Negativas
- Airflow ocupa unos 1.970 MiB en reposo (siete contenedores), mucho más que lo que el pipeline necesita; es el componente más pesado del proyecto.
- El DAG no tiene reintentos de tareas y con `catchup=False` no recupera ejecuciones que ocurrieron con el equipo apagado.
- Si Airflow cambia su compose, el generador falla en lugar de escribir otra cosa; se prefiere ver el fallo.

## Alternativas consideradas entonces
Registradas en `docs/DECISIONES.md`:
- docker engine dentro de wsl2 (D21)
- `pip` con restricciones oficiales en wsl2 (D21)
- validación estática con matiz (D21)
- un ejecutor local sin redis ni celery (D57)
- `@daily` (en utc) (D64)
- mantener `schedule=none` (D64)
- descargar y parchear el compose al instalar (D92)
- un compose propio desde cero (D92)

## Alternativas que hoy descartamos y por qué
Razonamiento actual del equipo, no registrado en su momento.
- **Ejecutar `main.py` con el programador de tareas del sistema.** Habría bastado para 3 segundos de pipeline, pero no deja estados por tarea, ni comparación con lo versionado, ni recuperación visible; elegimos Airflow porque el ítem 5.4 pide un DAG, y aceptamos el costo de memoria como una limitación conocida.
- **Kubernetes o un orquestador administrado en la nube.** Son cuatro tareas que terminan en segundos sobre 5.146 filas, con una sola máquina local; no hay carga que repartir.
