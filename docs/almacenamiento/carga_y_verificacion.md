# Carga relacional: cómo cargar, verificar, respaldar y servir desde MySQL

**Componente:** Carga relacional · **Ítems del checklist:** 4.1 (esquema y almacén), 4.2 (carga e integridad) y 4.3 (consultas y verificación) · **Modelo:** [modelo_datos.md](modelo_datos.md) · **Configuración de MySQL:** [mysql_configuracion.md](mysql_configuracion.md)

## 1. Qué hace la carga
`scripts/cargar_mysql.py` copia a MySQL el estrato por barrio de Silver (`estrato_barrio`), las construcciones de Gold (`gold_final`, que ya integra Silver) y los indicadores (`kpis_gold` y `kpis_sensibilidad`), más las coberturas de `quality_report.json`. Solo lee `data/`: no modifica el pipeline, Bronze ni `etl_sismo.db`, que sigue existiendo como almacén de referencia (D40).

```powershell
.\.venv\Scripts\python.exe scripts\cargar_mysql.py --destino mysql              # base real (sismo_cali)
.\.venv\Scripts\python.exe scripts\cargar_mysql.py --destino mysql --base prueba # base de prueba
.\.venv\Scripts\python.exe scripts\cargar_mysql.py --destino sqlite --sqlite-ruta ..\prueba.db   # sin servidor (fuera de data/)
```
Códigos de salida: 0 (cargó o ya estaba cargada), 1 (la carga falló y se revirtió), 2 (parámetros no válidos, por ejemplo una base SQLite dentro de `data/`) y 3 (no hay conexión con MySQL).

## 2. Reglas de la carga
| Regla | Cómo se cumple | Decisión |
|---|---|---|
| Historial | cada carga distinta es una **corrida** con todas sus filas; la historia es la suma de corridas | D43 |
| Idempotencia | la clave de la corrida es el sha256 de las huellas de las entradas más la versión del esquema; la misma entrada responde «ya cargada» y no escribe | D44 |
| Todo o nada | una sola transacción con `ROLLBACK` ante cualquier error; la lectura y conversión de los CSV ocurre antes de abrirla | D45 |
| Conversión estricta | vacío es NULL solo si la columna lo admite; booleanos de una tabla cerrada; enteros solo si son enteros; decimales exactos sin redondeo; textos sin truncar | D41 |
| Por lotes | `executemany` con el tamaño `almacenamiento.lote` de `config/config.yaml`, decidido por medición | D47 |
| SQL explícito | sentencias con parámetros; sin ORM y sin `LOAD DATA LOCAL` | D41 |
| Integridad | claves primarias y foráneas (`ON DELETE RESTRICT`), restricciones `CHECK` (estrato, pureza, coordenadas de Cali, banderas, coherencia entre cruce y enlace y entre sin datos y severo) | D42, D51 |

Los 4 casos de construcciones cuyo código de barrio no está en el CSV de estrato se cargan con `barrio_estrato_codigo` nulo: se conservan las 5.146 construcciones y no se inventa ningún barrio.

## 3. Verificación sin servidor (pytest)
Las pruebas automáticas no necesitan MySQL (D49). Con el mismo esquema sobre SQLite y claves foráneas activas comprueban:
- paridad de los dos archivos de esquema y diccionario de datos al día;
- conversión correcta y rechazo de todo valor que perdería información;
- carga completa con conciliación al 100 % (conteos, huellas de los archivos y ida y vuelta de **cada valor**);
- idempotencia, historial con una entrada alterada y reversión total ante un fallo inyectado a mitad de carga;
- rechazo de diez violaciones de integridad y de borrar una corrida con datos;
- la API sirve las mismas respuestas desde el almacén relacional que desde SQLite, y responde 503 uniforme si el almacén no está disponible;
- la configuración de MySQL con conexiones simuladas y el manejo de credenciales (sección 6).

## 4. Verificación en vivo (base de prueba)
Con `.env` creado por `configurar_mysql.py` y el servicio MySQL80 activo:

```powershell
.\.venv\Scripts\python.exe scripts\mysql\verificar_mysql.py --evidencia
```
La batería corre **solo sobre `sismo_cali_prueba`** y comprueba: conexión y privilegios mínimos; esquema creado desde cero (tablas, columnas, InnoDB, cotejamiento, claves foráneas y `CHECK`); primera carga con conciliación al 100 %; relaciones sin huérfanos; idempotencia; equivalencia de 17 rutas de la API entre MySQL y SQLite; corrida nueva ante una entrada alterada y la anterior intacta; reversión completa ante un fallo inyectado; seis violaciones de integridad rechazadas con su código de error de MySQL; sesión de solo lectura que rechaza escrituras y 503 uniforme si el almacén no responde.

Cada comprobación imprime «OK» o «FALLA» con su detalle; el código de salida es 0 solo si todas pasan. Con `--evidencia` la salida se guarda saneada en `docs/evidencias/almacenamiento/`.

### Tamaño de lote
```powershell
.\.venv\Scripts\python.exe scripts\mysql\benchmark_lotes.py --evidencia --fijar
```
Compara fila a fila con lotes de 500, 1000 y 2000 (1 carga de calentamiento y 5 repeticiones por estrategia, desde tablas vacías), informa mediana, p95 y filas por segundo y propone el lote. Criterio: menor mediana; si otro lote queda a menos de 5 % se prefiere el más pequeño. Con `--fijar` escribe el valor en `almacenamiento.lote`.

## 5. Respaldo y restauración
```powershell
.\.venv\Scripts\python.exe scripts\mysql\respaldar_restaurar.py --evidencia
```
Exporta cada tabla de la base real a CSV con un manifiesto de sha256 en una carpeta **fuera del repositorio**, verifica el manifiesto, restaura en la base de prueba reconstruida desde cero y concilia tabla por tabla comparando una huella de todas las filas (D48). Alternativa con herramientas del servidor, sin ejecutar: `mysqldump --single-transaction --no-tablespaces -u sismo_etl -p sismo_cali > respaldo.sql`; la contraseña se escribe cuando la herramienta la pide.

## 6. Credenciales
- La contraseña del proyecto vive solo en `.env`; el código la lee de la variable de entorno, nunca de `config/config.yaml`.
- El registro enmascara el valor de las variables de `.env` y cualquier par `clave=valor` sensible.
- `scripts/escanear_secretos.py` detecta `MYSQL_PASSWORD=<literal>` y, con `--canario-env`, busca los valores sensibles de `.env` en el árbol, el historial de git y el zip sin imprimirlos (D50).
- Más detalle en [gestión de credenciales](../seguridad/gestion_credenciales.md).

## 7. Servir la API desde MySQL
En `config/config.yaml`, `api.almacenamiento: mysql` (por defecto `sqlite`). La API abre una conexión de solo lectura por solicitud y responde con la **última corrida**; `/health` y `/metadata` informan el almacén activo. Si MySQL no responde, todas las rutas devuelven 503 con el JSON de error uniforme, sin datos de conexión (D52).

## 8. Alcance y límites
- **Qué afirmamos:** el esquema, la carga, la conciliación y la integridad están implementados y se prueban sin servidor; la batería en vivo los repite contra MySQL 8.0 en la base de prueba y deja evidencia saneada.
- **Con qué evidencia:** las pruebas de `tests/test_carga_relacional.py`, `tests/test_configurar_mysql.py` y `tests/test_respaldo_y_medicion.py`, y los archivos de `docs/evidencias/almacenamiento/`.
- **Qué NO afirmamos:** que el almacén relacional sea apto para varios usuarios simultáneos, que las medidas de tiempo valgan para otro equipo ni que los datos sean una evaluación estructural: es un proxy satelital sobre construcciones de siete comunas, sin generalizar a toda Cali.
