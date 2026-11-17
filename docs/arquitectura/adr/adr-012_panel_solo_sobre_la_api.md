# ADR-012: El panel Streamlit solo habla con la API

**Estado:** Vigente (implementada). **Fecha de la decisión:** 2026-11-12 (D20) y 2026-11-14 (D69, D70). **D de origen:** D20, D69, D70. **Propietario técnico:** Daniel Alexander Brand García. **Revisión:** pendiente.

## Contexto
Los resultados necesitaban una interfaz que cualquiera pudiera abrir sin instalar herramientas de inteligencia de negocio y que no abriera ningún camino nuevo hacia los datos. Los indicadores son un proxy satelital con límites que la interfaz debe mostrar siempre.

## Decisión
- La interfaz consume la API y no lee la base (D20). Un único cliente, `src/panel/cliente_api.py`, hace los GET con `httpx`, traduce cada fallo (API apagada, tiempo agotado, 404, 422, 503, JSON inválido) a un aviso en español sin trazas ni rutas, reintenta una sola vez un error de conexión y solo acepta una URL local (D69).
- Las respuestas correctas se guardan 300 s en caché (`panel.ttl_cache_s`); un fallo no se guarda, para que no quede «pegado» cuando la API vuelve (D70).
- El panel tiene 8 páginas y 28 componentes definidos en un registro de solo datos, y todas las páginas muestran el recuadro de alcance.
- Una prueba de análisis estático comprueba que el panel no importa `sqlite3` ni `pymysql`, no abre archivos de datos y no lee `.env`.

## Consecuencias
### Positivas
- Un solo punto de acceso a los datos: la API, que ya es de solo lectura (ADR-010).
- Las pruebas conectan la interfaz en memoria a la API real, sin navegador ni red.
- La interfaz corre con unos 160 MiB junto con la API (medido en reposo).

### Negativas
- Si la API cambia el nombre de un campo, el panel muestra el aviso de formato inesperado; lo detectan las pruebas de integración.
- Una corrida nueva tarda hasta el tiempo de vida de la caché en verse.
- El panel no está desplegado: corre solo en local.

## Alternativas consideradas entonces
Registradas en `docs/DECISIONES.md`:
- power bi (D20)
- página estática con plotly (respaldo) (D20)
- abrir sqlite o mysql desde la interfaz (viola d20) (D69)
- `requests` (D69)
- sin caché (más lecturas a la api) (D70)
- caché que guarda errores (D70)

## Alternativas que hoy descartamos y por qué
Razonamiento actual del equipo, no registrado en su momento.
- **Una herramienta de tableros externa (Superset, Metabase u otra).** Exige un servicio más con su propia base de datos y credenciales para mostrar 8 páginas de 11 rutas de una API local; el panel se levanta con un solo comando y se prueba con la suite.
- **Una aplicación web propia con un marco de interfaz en JavaScript.** Duplicaría el trabajo de formato de cifras y redacción de conclusiones que ya hace el panel, con más superficie de ataque y sin pruebas del mismo nivel.
