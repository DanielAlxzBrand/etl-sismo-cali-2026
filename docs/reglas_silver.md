# Reglas de Silver

Cada regla cita el hallazgo de `docs/hallazgos_eda.md` que la justifica. La unidad de análisis son las **construcciones** (huellas catastrales).

| regla | hallazgo | columnas | filas afectadas | justificación |
|---|---|---|---|---|
| R01 | H1 | OBJECTID | 0 | Identificador = OBJECTID (único); la llave catastral se repite por predio con varias construcciones y no se deduplica. |
| R02 | H4 | COMUNA, BARRIO | 4 | Texto vacío o solo espacios pasa a nulo; no se imputa. |
| R03 | H2 | geom_duplicada | 18 | Bandera para las construcciones con geometría idéntica a otra; se conservan las filas. |
| R04 | H9 | clase_dano | 5146 | Etiqueta de Estado_Estructural a 4 clases estables; Indice_Escombros no se imputa. |
| R05 | H9, H12 | sin_datos | 435 | 'Sin datos satelitales' queda como clase propia (no es 'sin daño'); sale del denominador. |
| R06 | H10 | severo_estricto, dano_visible | 4711 | Banderas D7; nulas (no falsas) cuando no hay datos satelitales. |
| R07 | H16 | npisos, npisos_cero | 1234 | NPISOS a entero nullable sin imputar; bandera para 0 pisos; no se usa como filtro. |
| R08 | H5 | codigo_barrio | 5144 | Llave del JOIN = int(COMUNA)*100 + int(BARRIO) como texto; nula si falta COMUNA o BARRIO. |
| R09 | H13, H18 | lon, lat, codigo_poligono, nombre_poligono, coincide_poligono | 5146 | Centroide de la huella (7 decimales) ubicado en los polígonos WFS 2026; solo valida la llave, no entra al JOIN. |
| R10 | H3, H4 | OBJECTID_1, Shape__Area, Shape__Length, ID_PREDIO y demás columnas catastrales | 5146 | Se descartan columnas vacías, en grados o sin uso en Gold; ver docs/hallazgos_eda.md. |
| R11 | H6 | cod | 23 | Filas 'Comuna N' y 'Otros' (código '-') se separan; no entran al JOIN. |
| R12 | H7 | lados_e1, lados_e2, lados_e3, lados_e4, lados_e5, lados_e6, sin_vivienda | 342 | Guion y vacío = 0 lados, coma de miles eliminada, columnas a entero. |
| R13 | H7 | barrio | 26 | strip y espacios internos colapsados; el archivo se lee como UTF-8. |
| R14 | H8 | estrato | 6 | estrato = moda solo si es 1-6; 'NR' queda nulo y no se convierte en estrato. |
| R15 | H14 | pureza_estrato | 343 | max(lados 1..6)/suma(lados 1..6) sin 'Sin vivienda'; nula si el total es 0. |
| R16 | H5, H6 | codigo_barrio | 5140 | LEFT JOIN construcciones <- estrato por barrio; huérfanos guardados, no descartados. |
| R17 | H11 | n_con_datos_estrato, n_severos_estrato, muestra_baja | 5138 | Conteos por estrato sobre construcciones con datos satelitales y bandera de muestra baja (< 30 severos). |
| R18 | H18 | nombre_validado | 5140 | Validación semántica de la llave (nombre CSV vs nombre de polígono); no cambia la llave. |

**Cómo leer "filas afectadas":** cuenta filas (no celdas) salvo donde se indica. R01 = 0 porque solo fija el identificador y no modifica filas; R02 = 2 filas (4 celdas: COMUNA y BARRIO en blanco en 2 construcciones); R03 = 9 pares (18 filas con geometría idéntica); R10 = 5146 porque descarta columnas y afecta a todas las filas.
