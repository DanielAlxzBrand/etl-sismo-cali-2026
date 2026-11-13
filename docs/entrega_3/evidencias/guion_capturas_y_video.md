# Guion de capturas y video (esqueleto)

**Fecha:** 2026-11-12 · Las capturas de pantalla y los videos los toma el equipo; este guion se completa fase a fase. Cada captura se rotula «captura tomada por el equipo» y cada video «video grabado por el equipo»; las imágenes generadas desde salidas reales se rotulan «render generado a partir de salidas reales» y no se presentan como capturas.

## F0 · Línea base, orden y material de referencia
- Ítems: 7.1
- Capturas y videos previstos: ninguno (la evidencia de F0 son archivos de texto).

## F1 · Decisiones y sección 1
- Ítems: 1.1, 1.2, 1.3, 1.4, 1.5. Las capturas las toma el equipo (no se generaron en F1); las dos imágenes de `docs/entrega_3/img/` son diagramas renderizados desde datos, no capturas.
- **1.1:** documento `01_data_thinking.md` abierto en la tabla de equivalencia (§2) y, aparte, en la tabla de insights (§3). Nombres sugeridos: `captura_1.1_equivalencia.png`, `captura_1.1_insights.png`.
- **1.2:** `02_stakeholders.md` en la tabla de puntajes y la imagen de la matriz poder-interés (§3). Nombre: `captura_1.2_matriz.png`.
- **1.3:** `03_objetivo_alcance_okr_kpi.md` en la tabla de trazabilidad (§4). Nombre: `captura_1.3_trazabilidad.png`.
- **1.4:** `04_canvas_data_innovation_board.md` con el aviso inicial y la imagen del Canvas visibles (§2). Nombre: `captura_1.4_canvas.png`.
- **1.5:** `05_mvp_criterios_aceptacion.md` en la tabla de criterios con la columna de estado visible y, en una terminal, la salida de `python -m pytest -q -p no:cacheprovider`. Nombres: `captura_1.5_criterios.png`, `captura_1.5_pytest.png`.
- Cada captura se rotula «captura tomada por el equipo» con la fecha.

## F2 · Backend, API de solo lectura, fuentes y credenciales
- Ítems: 2.1, 2.2, 2.3. Las capturas las toma el equipo; la captura de `/docs` incluida como EV-017 es una **captura automatizada del navegador** y no sustituye a las manuales. Las cuatro imágenes `EV-021` a `EV-024` son renders generados a partir de salidas reales, no capturas.
- **Antes de grabar:** PowerShell en la raíz del repositorio, con el entorno activado (`.\.venv\Scripts\Activate.ps1`) y sin cambios sin guardar (`git status --short` no imprime nada).
- **2.1 · respuesta de `GET /health`.** Ventana: PowerShell. Comando: primero `python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000` en una terminal y, en otra, `Invoke-RestMethod http://127.0.0.1:8000/health | ConvertTo-Json -Depth 5`. Debe verse: `estado` «ok», `base_disponible` verdadero y las filas por tabla (5146, 5146, 23 y 107). Nombre: `captura_2.1_health.png`.
- **2.1 · documentación automática.** Ventana: navegador en `http://127.0.0.1:8000/docs` con las rutas desplegadas (todas con la etiqueta GET). Nombre: `captura_2.1_docs.png`.
- **2.1 · consulta a `/kpis`.** Ventana: PowerShell. Comando: `(Invoke-RestMethod "http://127.0.0.1:8000/kpis?kpi_id=K1") | Select-Object kpi_id, grupo, valor, numerador, denominador | Format-Table` (los paréntesis hacen que PowerShell recorra la lista). Debe verse K1 por estrato con numerador y denominador. Nombre: `captura_2.1_kpis.png`.
- **2.1 · resultado de pytest.** Ventana: PowerShell. Comando: `python -m pytest -q -p no:cacheprovider`. Debe verse la línea final «passed» sin fallos. Nombre: `captura_2.1_pytest.png`.
- **2.3 · salida del escáner.** Ventana: PowerShell. Comando: `python scripts\escanear_secretos.py`. Debe verse la línea final `hallazgos: 0` (y ningún valor secreto). Nombre: `captura_2.3_escaner.png`.
- **2.2 · catálogo de fuentes.** Ventana: editor con `docs/entrega_3/catalogo_fuentes_metadatos.md` en la ficha de `edificaciones` (snapshot con sha256 visible). Nombre: `captura_2.2_catalogo.png`.
- Cada captura se rotula «captura tomada por el equipo» con la fecha.
- **Guion de video del tramo de API (aprox. 3 minutos; pasos ejecutables tal como están escritos).**
  1. Terminal 1: `python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000` (esperar «Application startup complete»).
  2. Terminal 2: `Invoke-RestMethod http://127.0.0.1:8000/health` y decir «la API está viva y lee la base en solo lectura».
  3. `Invoke-RestMethod "http://127.0.0.1:8000/metadata"` y señalar el aviso «proxy satelital, no evaluación estructural», las 7 comunas y el estrato 2015.
  4. `Invoke-RestMethod "http://127.0.0.1:8000/kpis?kpi_id=K1"` y comparar con `data\gold\kpis_gold.csv`.
  5. `Invoke-RestMethod "http://127.0.0.1:8000/construcciones?limit=2&comuna=19"` y mostrar `total`, `limit` y `offset`.
  6. Demostrar el error uniforme: `Invoke-RestMethod "http://127.0.0.1:8000/kpis/K99"` (devuelve 404 con `error.codigo` = `no_encontrado`).
  7. Demostrar que no escribe: `Invoke-WebRequest -Method Post http://127.0.0.1:8000/kpis` devuelve 405.
  8. Abrir `/docs` en el navegador y mostrar las rutas.
  9. Ctrl+C en la terminal 1 (cierre ordenado) y `python scripts\escanear_secretos.py` para cerrar con `hallazgos: 0`.

## F3 · Carga relacional a MySQL
- Ítems: 4.1, 4.2, 4.3
- Capturas y videos previstos: se definen al diseñar la fase.

## F4 · Pruebas técnicas, MLOps y orquestación con Airflow en Windows
- Ítems: 2.1, 2.3, 4.1, 4.2, 5.1, 5.2, 5.4, 5.5, 5.6
- Capturas y videos previstos: se definen al diseñar la fase.

## F5 · Dashboard con Streamlit
- Ítems: 1.5, 3.1, 3.2, 3.3, 5.3
- Capturas y videos previstos: se definen al diseñar la fase.

## F6 · Usuarios, UX y finanzas
- Ítems: 3.3, 6.1, 6.2, 6.3, 6.4
- Capturas y videos previstos: se definen al diseñar la fase.

## F7 · Documentación, iteraciones y demo
- Ítems: 1.3, 6.3, 6.5, 7.2, 7.3, 7.4, 7.5
- Capturas y videos previstos: se definen al diseñar la fase.

## F8 · Checklist final y paquete
- Ítems: 1.1, 1.2, 1.3, 1.4, 1.5, 3.1, 3.2, 5.1, 5.3, 5.4, 5.5, 5.6, 6.1, 6.2, 6.4, 6.5, 7.1, 7.2, 7.3, 7.4, 7.5
- Capturas y videos previstos: se definen al diseñar la fase.
