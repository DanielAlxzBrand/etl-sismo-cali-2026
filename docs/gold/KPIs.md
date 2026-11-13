# KPI de Gold — Avance 2 ETL (UAO)

**Fecha de corte:** 2026-09-02 (última edición de la capa, `America/Bogota`; `config.yaml: fechas.fecha_edicion_capa`). Imágenes: pre-evento 2026-03-22, post-evento 2026-08-11 (descripción del dataset 5vy8-gpw8). El estrato es de **2015** y se mide en lados de manzana, no por construcción.
**Fuente:** capa ArcGIS `Impacto_Satelital_en_Edificaciones_por_Terremoto_Cali_2026` (catálogo datos.gov.co `5vy8-gpw8`, licencia CC BY 4.0 según `metadata.custom_fields.Common Core.License`; `copyrightText` del servicio vacío) + CSV de estrato por barrio 2015 (datos.cali.gov.co, DAPM).

### Alcance temporal
> **Alcance temporal.** El estrato por barrio es de **2015** (DAPM Cali, medido en lados de manzana). Las construcciones se evaluaron con imágenes del **2026-03-22** y del **2026-08-11**, y la capa se editó por última vez el **2026-09-02** (`config/config.yaml`, sección `fechas`). Los polígonos de barrios que usamos para validar son de 2026 y están renumerados respecto a 2015 (H13, H18). Entre el estrato y las imágenes hay unos **once años** de distancia. **Regla de lectura:** los resultados por estrato describen el estrato de 2015 asignado al barrio, no el estrato vigente. Lo que cambió en los barrios entre 2015 y 2026 es **desconocido** para nosotros y no lo estimamos.

### Población analizada
> **Población analizada.** **5.146** construcciones (**4.711** con datos satelitales) de **7 comunas** de Cali (03, 09, 10, 17, 18, 19 y 20), repartidas en **52** códigos de barrio. Criterio de inclusión: la capa solo incluye construcciones dentro de los polígonos de afectación preliminar del visor de emergencia del IGAC, según la descripción del dataset. Quedan fuera las comunas ausentes, entre ellas la **Comuna 2** (la Alcaldía la mencionó entre las de mayor pérdida), y la zona rural. El daño es un **proxy satelital** (cambio de textura entre dos imágenes), y todas las tasas son **condicionales a esta muestra**. **Regla:** las tasas describen esta muestra; no se extrapolan a las construcciones de Cali ni a la ciudad. Gold lee solo `silver_integrated.csv`.

### Indicador satelital frente a evaluación estructural
| aspecto | indicador satelital (este proyecto) | evaluación estructural (ATC-20, Alcaldía de Cali) |
|---|---|---|
| qué es | cambio de textura entre dos imágenes de satélite sobre la huella de la construcción; el severo estricto es la clase "Alta probabilidad de escombros" | inspección técnica en sitio que clasifica el predio con un sticker: rojo (inseguro), amarillo (uso restringido) o verde |
| quién lo produce | Fondo Adaptación (capa catalogada en datos.gov.co, `5vy8-gpw8`) | Alcaldía de Cali |
| cómo se obtiene | análisis de imágenes del 2026-03-22 y 2026-08-11, sin inspección directa | evaluación directa de cada predio |
| qué ve y qué no ve | ve cambio visible desde arriba; no ve daño interno ni daño sin cambio visible, y no da seguridad de uso | evalúa la seguridad de uso del predio; no tenemos sus datos por predio |
| unidad de análisis | construcción (huella catastral) | predio |
| cobertura | 5.146 construcciones de 7 comunas, dentro de los polígonos de afectación preliminar | 3.403 predios caracterizados (no conocemos su distribución por comuna) |
| cifras disponibles | 4.711 con datos satelitales; 296 severos estrictos (6,28 %) | 3.403 predios: 1.078 rojo, 1.272 amarillo y 1.053 verde, publicado por El País Cali el 23-sep-2026 (https://www.elpais.com.co/cali/alcaldia-de-cali-entrega-balance-de-gestion-tras-el-sismo-mas-de-3400-edificaciones-evaluadas-y-45000-familias-damnificadas-2338.html) |
| uso en este proyecto | es la base de todos los KPI de Gold | solo contexto: no se compara ni se mezcla con ninguna cifra de Gold |

Las cifras de la evaluación estructural son cifras reportadas por la prensa citando a la Alcaldía; no las cotejamos con una fuente oficial descargable. La unidad (predios) no es la nuestra (construcciones), por lo que no las comparamos ni las mezclamos con ninguna cifra de Gold.

## Definiciones comunes
- **Unidad:** construcción (huella catastral, `objectid`). **Denominador de toda tasa:** construcciones con datos satelitales (`sin_datos = false`). "Sin datos satelitales" sale del denominador, se reporta aparte (`n_sin_datos`, `pct_sin_datos`) y nunca se trata como "sin daño".
- **Indicador principal (D7 definitivo):** construcciones con cambio satelital severo (severo estricto, proxy de daño; columna `severo_estricto`, clase "Alta probabilidad de escombros"). `dano_visible` (escombros + techo) es solo sensibilidad S4, de baja confianza.
- **Intervalo:** Wilson al 95 % (z = 1,96), función `wilson` de `src/transform/build_gold.py` (pruebas: Wilson(5,10) = [0,2366; 0,7634]; Wilson(0,10) = [0; 0,2775]).
- **Cotas por "sin datos"** (`cota_inf`, `cota_sup`): `k / (n + n_sin_datos)` y `(k + n_sin_datos) / (n + n_sin_datos)`. Son **cotas extremas** (todo "sin datos" no severo, o todo severo); no son estimaciones. Si las cotas de dos grupos se solapan, el orden entre ellos **no es identificable**. Destaca E2: ≈ 27 % sin datos.
- **`muestra_baja`:** `true` si k < 30 severos.
- **Columnas de `kpis_gold.csv`:** `kpi_id, nombre, valor, numerador, denominador, grupo, fecha_corte, fuente, ic95_inf, ic95_sup, n_sin_datos, pct_sin_datos, muestra_baja, cota_inf, cota_sup, nota`.

## K1 · Tasa de severos estrictos por estrato (KR4)
- **Fórmula:** k / n por estrato e = 1…6, con k = construcciones con cambio satelital severo (severo estricto, proxy de daño) y n = construcciones con datos del estrato e. **Razón:** responde la parte "¿cambia entre estratos?" de la pregunta de negocio.
- **Resultado (corte 2026-09-02):** E1 20/302 = 6,62 %; E2 3/92 = 3,26 %; E3 74/1.173 = 6,31 %; E4 145/2.095 = 6,92 %; E5 53/1.031 = 5,14 %; E6 0/11 = 0 %. **E1, E2 y E6 son `muestra_baja`.** E2 tiene 27,0 % sin datos (cota sup. 29,4 %).
- **Limitaciones:** los intervalos de Wilson de E1, E3, E4 y E5 se solapan; ver "Qué NO se puede concluir".

## K2 · Estratos 3-5 frente a 1-2
- **Fórmulas:** tasa(3-5) = 272/4.299 = 6,33 %; tasa(1-2) = 23/394 = 5,84 % (**muestra_baja**, 23 severos); razón = tasa(3-5)/tasa(1-2) = 1,084 (vacía si la tasa de 1-2 es 0); diferencia = tasa(3-5) − tasa(1-2) = +0,49 pp con **intervalo de Newcombe** [−2,36; +2,55] pp. E6 queda fuera de K2 (11 construcciones).
- **Regla de redacción:** si los intervalos se solapan o la diferencia incluye 0, se escribe **"con este proxy y esta muestra no se detecta diferencia"**, nunca "el estrato no influye". Aquí aplica: la diferencia incluye 0 y los Wilson de ambos grupos se solapan. Las cotas por "sin datos" también se solapan (3-5: 5,8-13,6 %; 1-2: 5,0-20,0 %), así que el orden no es identificable.
- **Razón ajustada por comuna (Mantel-Haenszel):** `RR_MH = Σ(a·n0/N) / Σ(c·n1/N)` con a, c = severos de expuestos (3-5) y referencia (1-2), n1, n0 = tamaños **con datos**, N = n1 + n0, sobre comunas con ambos grupos. Valor S0 = 1,970, pero **solo la comuna 18 tiene ambos grupos** (se excluyen 03, 09, 10, 17, 19, 20): descansa en 44 construcciones expuestas (5 severas) y 52 de referencia (3 severas). **No es interpretable**: es una señal de que el estrato está confundido con la ubicación, no un resultado.

## K3 · Concentración de los severos estrictos (KR1)
- **Fórmula:** construcciones con cambio satelital severo (severo estricto, proxy de daño) en los 10 barrios con más severos / severos estrictos con barrio asignado (empates por código ascendente). **Resultado:** 167/295 = 56,6 % (códigos 1914, 1913, 306, 1901, 1002, 1906, 2004, 305, 1904, 1903).
- **Limitación:** esos barrios también tienen más construcciones; concentración de casos no es mayor riesgo. Se excluye 1 severo sin barrio.

## K4 · Spearman estrato moda vs tasa de severos por barrio
- **Fórmula:** `DataFrame.corr(method="spearman")` entre estrato moda del barrio y tasa de severos del barrio, solo barrios con ≥ `min_edificios_por_barrio` (10) construcciones con datos. **Resultado:** rho = 0,035, n = 45 barrios, p de permutación = 0,8218 (`random.Random(0)`, 5.000 permutaciones, p = (1 + #{|ρ\*| ≥ |ρ|})/(5.001)).
- **Limitación:** descriptivo, a nivel de barrio (falacia ecológica); no es prueba causal.

## K5 · Calidad del JOIN
Tres valores (`grupo`): `cobertura_llave` 5.140/5.146 = 99,883 %; `cobertura_estrato_valido` 5.138/5.146 = 99,845 %; `pct_nombre_validado` 4.807/5.140 = 93,52 % (llave_confianza "alta"). Coinciden con los valores esperados de la etapa Silver; no hubo que forzar nada.

## K6 · Tasa por comuna ("¿se concentra por zona?")
- **Fórmula:** k/n por comuna con Wilson, % sin datos y `muestra_baja`. **Resultado:** C03 39/550 = 7,09 %; C09 7/184 = 3,80 % (baja); C10 35/541 = 6,47 %; C17 4/87 = 4,60 % (baja); C18 8/96 = 8,33 % (baja); C19 182/2.909 = 6,26 %; C20 20/342 = 5,85 % (baja). Las 2 construcciones sin comuna quedan fuera de K6.
- **Limitación:** solo 7 comunas; la Comuna 2 no está. El estrato está **confundido con la ubicación** (los estratos 1-2 se concentran en pocas comunas; ver tabla estrato × comuna del notebook 04).

## Sensibilidades (`data/gold/kpis_sensibilidad.csv`)
Columnas: `escenario, kpi_id, grupo, k, n, tasa, ic95_inf, ic95_sup, nota`, para K1, K2 y K6.

| escenario | filtro | diferencia 3-5 menos 1-2 [Newcombe] (pp) | RR_MH |
|---|---|---|---|
| S0 | base | +0,49 [−2,36; +2,55] | 1,970 |
| S1 | `nombre_validado = true` (**sensibilidad principal de la llave**) | +0,17 [−2,81; +2,32] | 2,315 |
| S2 | `coincide_poligono = true` (secundaria; **no sustituye a S1**: el 95,19 % de las construcciones que no coinciden con el polígono tiene nombre validado, es renumeración de códigos y no mala asignación) | +0,28 [−2,96; +2,55] | vacía (ninguna comuna con ambos grupos) |
| S3 | `pureza_estrato ≥ 0,8` | −0,87 [−4,88; +1,94] | 1,894 |
| S4 | `dano_visible` en lugar de `severo_estricto` (**baja confianza**: imágenes del 22-mar y 11-ago-2026 sin control y 22,5 % de "techo") | +2,01 [−2,77; +6,37] | 1,397 |
| S5 | sin `geom_duplicada` | +0,42 [−2,45; +2,50] | 1,894 |

En los seis escenarios el intervalo de la diferencia incluye 0.

## Qué NO se puede concluir
1. El proxy mide **cambio visible desde satélite**, no daño interno ni el de construcciones de varios pisos sin cambio visible; no sustituye la inspección ATC-20.
2. Solo hay **7 comunas** (03, 09, 10, 17, 18, 19, 20); la **Comuna 2 no está**. Las tasas describen esta muestra; no se extrapolan a las construcciones de Cali ni a la ciudad.
3. **E2 tiene ≈ 27 % sin datos** y la falta de datos no es aleatoria; sus cotas (2,4 %-29,4 % de severos) no permiten ordenar E2 frente a otros estratos.
4. **Estratos con muestra baja** (k < 30): E1, E2, E6 y el grupo 1-2 de K2 (23 severos); también C09, C17, C18 y C20 en K6.
5. El estrato es de **2015, por lados de manzana, asignado a todo el barrio** (falacia ecológica); 1.480 construcciones están en barrios con pureza de estrato < 0,8.
6. `dano_visible` es de **baja confianza** (22,5 % de las construcciones con datos son "techo"; imágenes separadas ≈ 4,5 meses y sin grupo de control).
7. **Asociación no es causa.** Con este proxy y esta muestra no se detecta diferencia entre estratos, y eso no equivale a decir que el estrato no influye.
8. El grupo de estratos 1-2 está formado, casi por completo, por la Comuna 20 (342 construcciones, 20 severos) y la Comuna 18 (52, 3); K2 compara en la práctica la Comuna 20 con el resto de la muestra, y la razón ajustada por comuna solo puede usar la Comuna 18.

El README hereda estas limitaciones.

## Diccionario de columnas de `gold_final.csv` (una fila por construcción, 5.146)
| columna | descripción |
|---|---|
| `objectid` | identificador de la construcción (único) |
| `comuna`, `barrio` | códigos catastrales de 2 dígitos (texto; nulos si venían en blanco) |
| `codigo_barrio` | llave `int(comuna)*100 + int(barrio)` (texto) |
| `nombre_barrio_csv` | nombre del barrio en el CSV de estrato 2015 (nulo si no cruza) |
| `cruza_llave` | la llave existe en el CSV de estrato |
| `estrato` | estrato moda del barrio (1-6; nulo si NR o sin llave) |
| `pureza_estrato` | max(lados 1..6)/suma(lados 1..6) del barrio, sin "Sin vivienda" |
| `n_con_datos_estrato`, `n_severos_estrato`, `muestra_baja` | conteos por estrato (construcciones con datos) y bandera k < 30 |
| `npisos`, `npisos_cero` | número de pisos (entero nullable) y bandera de 0 pisos |
| `indice_escombros` | índice continuo de cambio de textura (nulo si sin datos) |
| `estado_estructural`, `clase_dano` | etiqueta original y clase (`escombros`, `techo`, `sin_cambio`, `sin_datos`) |
| `sin_datos` | sin datos satelitales |
| `severo_estricto`, `dano_visible` | banderas D7; **nulas** (no falsas) si `sin_datos` |
| `geom_duplicada` | comparte geometría idéntica con otra construcción (18 filas, 9 pares) |
| `lon`, `lat` | centroide a 7 decimales (EPSG:4326) |
| `codigo_poligono`, `nombre_poligono`, `coincide_poligono` | polígono WFS 2026 donde cae el centroide y si su código coincide con `codigo_barrio` |
| `nombre_validado` | el nombre CSV 2015 coincide (similitud ≥ 0,85) con el polígono dominante del código |
