# Revisión de los códigos de barrio con diferencias en la validación semántica

**Fecha:** 11-nov-2026 · **Origen:** observación de la retroalimentación recibida (profundizar la revisión de los códigos con diferencias) · **Alcance:** revisión documental. No modificamos `nombre_validado` ni ninguna otra columna o salida; las cifras de la validación (44 de 51 códigos; 93,52 % de las construcciones con nombre validado) se conservan tal cual.

Revisamos los 7 códigos con veredicto «NO coincide» en `docs/silver/validacion_llave.md` (1011, 1802, 1898, 1905, 1922, 1999 y 2098; suman 333 construcciones), el código 1920 (4 construcciones sin pareja en el CSV 2015) y las 2 construcciones sin comuna ni barrio. Leemos `data/silver/silver_integrated.csv`, `data/silver/silver_estrato_barrio.csv` y los polígonos de `data/bronze/geo/` solo en modo lectura. Esta revisión se apoya en los hallazgos H13 y H18.

## Método
- **Similitud original:** la de `validacion_llave.md` (difflib sobre `normalize_key`). La reproducimos y coincide en los siete códigos.
- **Normalización adicional (solo para este análisis):** quitamos las abreviaturas con punto («J.», «S.», «Dep.», «Urb.», «Res.»), los guiones y las palabras genéricas «Barrio», «Sector», «Urbanización», «Urb», «Unidad» y «Res». Después recalculamos la similitud con la misma métrica (difflib).
- **Categorías**, basadas solo en evidencia numérica:
  - **(a)** mismo barrio con diferencia de escritura: similitud normalizada ≥ 0,85.
  - **(b)** mismo barrio con nombre ampliado o cambiado: similitud normalizada < 0,85, el nombre más corto tiene al menos 2 palabras y todas aparecen en el más largo, y las construcciones caen en un solo polígono.
  - **(c)** indicio de cambio de límites o fusión/división: el resto de los casos con nombre en el CSV (no alcanzan ni (a) ni (b)).
  - **(d)** sin pareja en 2015: el código no existe en el CSV.
- **Código del polígono distinto:** los polígonos de 2026 están renumerados respecto a 2015 (H13/H18). Un código distinto no implica por sí solo un barrio distinto.

## Fichas por código

### Código 1011 — Barrio Departamental

| campo | valor |
|---|---|
| n construcciones (proporción de las 5.140 con llave) | 55 (1,07 %) |
| comuna | 10 |
| nombre en el CSV 2015 | Barrio Departamental |
| nombre del polígono 2026 dominante | Departamental |
| similitud original (validacion_llave.md) | 0,79 |
| nombre CSV tras normalización adicional | DEPARTAMENTAL |
| nombre polígono tras normalización adicional | DEPARTAMENTAL |
| similitud recalculada (difflib, mismo método) | 1,00 |
| % de construcciones del código que coinciden con el polígono | 100,00 % |
| polígono(s) donde caen los centroides | 1011 «Departamental» (55 constr.; existe en el CSV 2015 como «Barrio Departamental») |
| estrato moda y pureza | 4 (pureza 0,98) |
| n con datos satelitales / n severo estricto | 48 / 7 |
| categoría (evidencia numérica) | (a) mismo barrio, diferencia de escritura |
| revisión visual del equipo | pendiente |

### Código 1802 — Barrio Caldas

| campo | valor |
|---|---|
| n construcciones (proporción de las 5.140 con llave) | 9 (0,18 %) |
| comuna | 18 |
| nombre en el CSV 2015 | Barrio Caldas |
| nombre del polígono 2026 dominante | Caldas |
| similitud original (validacion_llave.md) | 0,63 |
| nombre CSV tras normalización adicional | CALDAS |
| nombre polígono tras normalización adicional | CALDAS |
| similitud recalculada (difflib, mismo método) | 1,00 |
| % de construcciones del código que coinciden con el polígono | 100,00 % |
| polígono(s) donde caen los centroides | 1802 «Caldas» (9 constr.; existe en el CSV 2015 como «Barrio Caldas») |
| estrato moda y pureza | 3 (pureza 1,00) |
| n con datos satelitales / n severo estricto | 8 / 0 |
| categoría (evidencia numérica) | (a) mismo barrio, diferencia de escritura |
| revisión visual del equipo | pendiente |

### Código 1898 — Alto Nápoles

| campo | valor |
|---|---|
| n construcciones (proporción de las 5.140 con llave) | 3 (0,06 %) |
| comuna | 18 |
| nombre en el CSV 2015 | Alto Nápoles |
| nombre del polígono 2026 dominante | Sector Alto Nápoles |
| similitud original (validacion_llave.md) | 0,77 |
| nombre CSV tras normalización adicional | ALTO NAPOLES |
| nombre polígono tras normalización adicional | ALTO NAPOLES |
| similitud recalculada (difflib, mismo método) | 1,00 |
| % de construcciones del código que coinciden con el polígono | 0,00 % |
| polígono(s) donde caen los centroides | 1823 «Sector Alto Nápoles» (3 constr.; no existe en el CSV 2015) |
| estrato moda y pureza | 1 (pureza 0,75) |
| n con datos satelitales / n severo estricto | 2 / 0 |
| categoría (evidencia numérica) | (a) mismo barrio, diferencia de escritura |
| revisión visual del equipo | pendiente |

### Código 1905 — Barrio Eucarístico

| campo | valor |
|---|---|
| n construcciones (proporción de las 5.140 con llave) | 177 (3,44 %) |
| comuna | 19 |
| nombre en el CSV 2015 | Barrio Eucarístico |
| nombre del polígono 2026 dominante | Eucarístico |
| similitud original (validacion_llave.md) | 0,76 |
| nombre CSV tras normalización adicional | EUCARISTICO |
| nombre polígono tras normalización adicional | EUCARISTICO |
| similitud recalculada (difflib, mismo método) | 1,00 |
| % de construcciones del código que coinciden con el polígono | 100,00 % |
| polígono(s) donde caen los centroides | 1905 «Eucarístico» (177 constr.; existe en el CSV 2015 como «Barrio Eucarístico») |
| estrato moda y pureza | 4 (pureza 0,94) |
| n con datos satelitales / n severo estricto | 166 / 7 |
| categoría (evidencia numérica) | (a) mismo barrio, diferencia de escritura |
| revisión visual del equipo | pendiente |

### Código 1922 — Camino Real J. Borrero S.

| campo | valor |
|---|---|
| n construcciones (proporción de las 5.140 con llave) | 71 (1,38 %) |
| comuna | 19 |
| nombre en el CSV 2015 | Camino Real J. Borrero S. |
| nombre del polígono 2026 dominante | Camino Real - Joaquín Borrero Sinisterra |
| similitud original (validacion_llave.md) | 0,75 |
| nombre CSV tras normalización adicional | CAMINO REAL BORRERO |
| nombre polígono tras normalización adicional | CAMINO REAL JOAQUIN BORRERO SINISTERRA |
| similitud recalculada (difflib, mismo método) | 0,67 |
| % de construcciones del código que coinciden con el polígono | 100,00 % |
| polígono(s) donde caen los centroides | 1922 «Camino Real - Joaquín Borrero Sinisterra» (71 constr.; existe en el CSV 2015 como «Camino Real J. Borrero S.») |
| estrato moda y pureza | 5 (pureza 0,56) |
| n con datos satelitales / n severo estricto | 66 / 6 |
| categoría (evidencia numérica) | (b) mismo barrio, nombre ampliado o cambiado |
| revisión visual del equipo | pendiente |

### Código 1999 — U. Dep. A. Galindo Plaza Toros

| campo | valor |
|---|---|
| n construcciones (proporción de las 5.140 con llave) | 2 (0,04 %) |
| comuna | 19 |
| nombre en el CSV 2015 | U. Dep. A. Galindo Plaza Toros |
| nombre del polígono 2026 dominante | Sector Unidad Deportiva Alberto Galindo Plaza de Toros |
| similitud original (validacion_llave.md) | 0,67 |
| nombre CSV tras normalización adicional | GALINDO PLAZA TOROS |
| nombre polígono tras normalización adicional | DEPORTIVA ALBERTO GALINDO PLAZA DE TOROS |
| similitud recalculada (difflib, mismo método) | 0,64 |
| % de construcciones del código que coinciden con el polígono | 0,00 % |
| polígono(s) donde caen los centroides | 1934 «Sector Unidad Deportiva Alberto Galindo Plaza de Toros» (2 constr.; no existe en el CSV 2015) |
| estrato moda y pureza | sin estrato válido (moda original «NR»; pureza no calculable) |
| n con datos satelitales / n severo estricto | 2 / 0 |
| categoría (evidencia numérica) | (b) mismo barrio, nombre ampliado o cambiado |
| revisión visual del equipo | pendiente |

### Código 2098 — Venezuela Urb. Cañaveralejo

| campo | valor |
|---|---|
| n construcciones (proporción de las 5.140 con llave) | 16 (0,31 %) |
| comuna | 20 |
| nombre en el CSV 2015 | Venezuela Urb. Cañaveralejo |
| nombre del polígono 2026 dominante | Venezuela |
| similitud original (validacion_llave.md) | 0,51 |
| nombre CSV tras normalización adicional | VENEZUELA CANAVERALEJO |
| nombre polígono tras normalización adicional | VENEZUELA |
| similitud recalculada (difflib, mismo método) | 0,58 |
| % de construcciones del código que coinciden con el polígono | 0,00 % |
| polígono(s) donde caen los centroides | 2010 «Venezuela» (16 constr.; no existe en el CSV 2015) |
| estrato moda y pureza | 1 (pureza 0,71) |
| n con datos satelitales / n severo estricto | 16 / 0 |
| categoría (evidencia numérica) | (c) indicio de cambio de límites o fusión/división |
| revisión visual del equipo | pendiente |

### Código 1920 — sin pareja en el CSV 2015

| campo | valor |
|---|---|
| n construcciones (no cuentan entre las 5.140 con llave) | 4 |
| comuna | 19 |
| nombre en el CSV 2015 | no existe en el CSV 2015 |
| nombre del polígono 2026 dominante | Sector Unidad Deportiva Jaime Aparicio |
| similitud original (validacion_llave.md) | no aplica |
| nombre CSV tras normalización adicional | — |
| nombre polígono tras normalización adicional | DEPORTIVA JAIME APARICIO |
| similitud recalculada (difflib, mismo método) | no aplica |
| % de construcciones del código que coinciden con el polígono | no aplica (sin código en el CSV) |
| polígono(s) donde caen los centroides | 1933 «Sector Unidad Deportiva Jaime Aparicio» (4 constr.; no existe en el CSV 2015) |
| estrato moda y pureza | no aplica (sin fila en el CSV) |
| n con datos satelitales / n severo estricto | 3 / 0 |
| categoría (evidencia numérica) | (d) sin pareja en 2015 |
| revisión visual del equipo | pendiente |

### Las 2 construcciones sin comuna ni barrio

No tienen código de barrio, por eso no cruzan la llave (categoría (d), huérfanas a la izquierda). Sí tienen polígono por ubicación.

| objectid | código polígono | nombre polígono | ¿el código existe en el CSV 2015? | ¿con datos satelitales? | ¿severo estricto? |
|---|---|---|---|---|---|
| 1821 | 1913 | El Cedro | existe | sí | sí |
| 2494 | 2001 | El Cortijo | existe | sí | no |

## Barrios del CSV más parecidos al nombre del polígono (códigos 2098, 1999 y 1920)

**Código 1999** (comparamos el nombre del polígono «Sector Unidad Deportiva Alberto Galindo Plaza de Toros», normalizado como «DEPORTIVA ALBERTO GALINDO PLAZA DE TOROS», con los barrios de la comuna 19 del CSV):

| # | código CSV | barrio CSV | similitud |
|---|---|---|---|
| 1 | 1999 | U. Dep. A. Galindo Plaza Toros (el propio código) | 0,64 |
| 2 | 1995 | Sector Cañaveralejo Guadalupe | 0,39 |
| 3 | 1910 | San Fernando Viejo | 0,38 |

Resultado: ningún otro código de la comuna supera 0,85; no vemos indicio de reasignación hacia otro barrio del CSV (el indicio apunta a cambio de límites, renumeración o renombrado). Los centroides caen en el polígono 1934, cuyo código no existe en el CSV 2015.

**Código 2098** (comparamos el nombre del polígono «Venezuela», normalizado como «VENEZUELA», con los barrios de la comuna 20 del CSV):

| # | código CSV | barrio CSV | similitud |
|---|---|---|---|
| 1 | 2098 | Venezuela Urb. Cañaveralejo (el propio código) | 0,58 |
| 2 | 2008 | Pueblo Joven | 0,29 |
| 3 | 2005 | Belén | 0,29 |

Resultado: ningún otro código de la comuna supera 0,85; no vemos indicio de reasignación hacia otro barrio del CSV (el indicio apunta a cambio de límites, renumeración o renombrado). Los centroides caen en el polígono 2010, cuyo código no existe en el CSV 2015.

**Código 1920** (comparamos el nombre del polígono «Sector Unidad Deportiva Jaime Aparicio», normalizado como «DEPORTIVA JAIME APARICIO», con los barrios de la comuna 19 del CSV):

| # | código CSV | barrio CSV | similitud |
|---|---|---|---|
| 1 | 1907 | Urbanización Nueva Granada | 0,38 |
| 2 | 1912 | 3 de Julio | 0,35 |
| 3 | 1921 | Nueva Tequendama | 0,35 |

Resultado: ningún otro código de la comuna supera 0,85; no vemos indicio de reasignación hacia otro barrio del CSV (el indicio apunta a cambio de límites, renumeración o renombrado). Los centroides caen en el polígono 1933, cuyo código no existe en el CSV 2015.

## Resumen

| categoría | códigos | lista | construcciones (de las 333) |
|---|---|---|---|
| (a) | 4 | 1011, 1802, 1898, 1905 | 244 |
| (b) | 2 | 1922, 1999 | 73 |
| (c) | 1 | 2098 | 16 |

Aparte, 6 construcciones sin pareja, categoría (d): 4 del código 1920 y 2 sin comuna ni barrio.

## Efecto ya medido en los indicadores

La sensibilidad **S1** excluye las construcciones sin nombre validado, es decir, exactamente estos siete códigos. Según `docs/gold/KPIs.md`, la diferencia entre los estratos 3-5 y 1-2 pasa de +0,49 [−2,36; +2,55] pp en el escenario base (S0, RR_MH 1,970) a +0,17 [−2,81; +2,32] pp en S1 (RR_MH 2,315). En ambos escenarios el intervalo incluye 0. No recalculamos nada aquí.

## Qué NO demuestra

- Que dos nombres se parezcan no prueba que se trate del mismo barrio, ni que no se parezcan prueba lo contrario. La similitud de nombres es un indicio, no una identificación.
- La categorización es numérica. La **revisión visual en el mapa sigue pendiente** (columna «revisión visual del equipo»): es un juicio humano que no hemos hecho ni inventado.
- No cambiamos la llave ni ninguna salida. Esta revisión documental no altera ningún resultado de Silver ni de Gold.
