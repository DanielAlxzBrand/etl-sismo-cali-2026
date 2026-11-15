# Arquitectura del panel

![Arquitectura del panel](img/arquitectura_panel.png)

Diagrama generado con matplotlib (`python scripts/panel/make_arquitectura_panel.py`); no es una captura de pantalla.

## 1. Capas y módulos
| Módulo (`src/panel/`) | Responsabilidad |
|---|---|
| `app.py` | aplicación Streamlit: `st.set_page_config` y `st.navigation` con las ocho páginas del registro (D68) |
| `registro.py` | definición única, de solo datos, de páginas y componentes (ruta de la API, campo, archivo de salida, KPI y advertencia) |
| `cliente_api.py` | único punto de acceso a los datos: GET por HTTP, resultado tipado, un reintento de conexión y caché con tiempo de vida (D69 y D70) |
| `configuracion.py` | lee solo la clave `panel` de `config/config.yaml`; acepta `PANEL_API_URL` solo si es una dirección local |
| `formato.py` | cifras con coma decimal, punto de miles, signo menos y redondeo half-up |
| `redaccion.py` | conclusiones generadas con la regla de `docs/gold/KPIs.md` (D73) |
| `componentes.py` | marco común, recuadro de alcance, tarjetas, tablas y gráficos Altair (D71, D74 y D75) |
| `glosario.py` | un solo diccionario de términos técnicos y la lista de los que usa cada página; el marco lo muestra en un desplegable al final de la página (D88) |
| `tema.py` y `claves.py` | colores y relación de contraste; identificadores de KPI, grupos y escenarios |
| `paginas/` | una función `render(api)` por página, sin efectos al importarse |

## 2. Flujo de una consulta
1. La persona abre una página en el navegador; Streamlit ejecuta la función `render` de esa página.
2. La página pide cada dato con `api(ruta, **parámetros)`; el cliente hace un GET a la API y, si sale bien, guarda la respuesta en la caché por el tiempo configurado.
3. La API lee el repositorio del almacenamiento activo (SQLite por defecto o MySQL, según `api.almacenamiento`) en solo lectura y responde en JSON.
4. La página da formato a las cifras, genera las lecturas y dibuja tablas y gráficos.

## 2.1 Errores y degradación
Cada fallo se traduce a un aviso en español: API apagada, tiempo agotado, almacenamiento no disponible (503), recurso inexistente (404), parámetros inválidos (422) o respuesta con un formato inesperado. El marco de cada página mantiene visible el recuadro de alcance y no muestra trazas ni rutas.

## 3. Seguridad y aislamiento
- **Solo lectura:** el cliente solo usa GET; la API rechaza cualquier otro método (405).
- **Sin acceso a datos ni credenciales:** el panel no importa `sqlite3`, `pymysql` ni las capas del pipeline, no abre CSV ni bases, no lee `.env` y el lanzador no le pasa variables `MYSQL_*`. Una prueba de análisis estático lo comprueba en cada ejecución.
- **Sin recursos externos:** no usa `unsafe_allow_html`, JavaScript propio, mapas con teselas ni fuentes de red; la telemetría de Streamlit está desactivada.
- **Solo local:** el panel y la API escuchan en 127.0.0.1 y el cliente rechaza direcciones que no sean locales.

## 4. Decisiones relacionadas
D20 (Streamlit sobre la API), D23 y D67 (pruebas de integración), D68 a D80 (panel), D87 a D90 (ajustes tras la evaluación heurística).

## 5. Alcance y límites
- **Qué afirmamos:** el panel es una capa de presentación delgada: toda cifra viene de la API y toda conclusión se genera con una regla.
- **Qué NO afirmamos:** que escale a muchas personas a la vez (una conexión a MySQL por solicitud de la API) ni que esté desplegado; es un panel local.
