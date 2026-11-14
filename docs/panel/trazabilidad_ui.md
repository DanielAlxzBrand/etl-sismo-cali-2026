# Trazabilidad de la interfaz: componente, ruta de la API, campo, archivo de salida y pregunta de negocio

Este documento se genera con `python scripts/panel/generar_trazabilidad.py` desde el registro único de componentes (`src/panel/registro.py`); no se edita a mano. Una prueba comprueba que cada ruta existe en el OpenAPI de la API y que cada campo y cada KPI existen en los archivos de salida.

- **Páginas:** 8. **Componentes:** 28 (1 de tipo aviso, 1 de tipo descarga, 4 de tipo grafico, 8 de tipo metrica, 9 de tipo tabla, 5 de tipo texto).
- **Cómo se lee:** el panel no abre archivos: pide la ruta a la API y muestra el campo. La columna «archivo de salida» es donde está el número que la API sirve.
- **Nombres de campos:** son las columnas del archivo de salida; la ruta `/comunas` los renombra (`tasa` = `valor`, `severos` = `numerador`, `n_con_datos` = `denominador`).

## Respuesta
**Pregunta de negocio:** ¿En esta muestra se detecta diferencia en la tasa de cambio satelital severo entre los estratos 3-5 y 1-2?
**Rutas de la API:** `/kpis`, `/metadata`. **Dirección:** `/` (página de inicio)

| Componente | Tipo | Ruta | Campos | Archivo de salida | KPI | Advertencia visible |
|---|---|---|---|---|---|---|
| Tasa de los estratos 3-5 (`respuesta.tasa_3_5`) | metrica | `/kpis` | `valor`, `numerador`, `denominador`, `ic95_inf`, `ic95_sup` | `data/gold/kpis_gold.csv` | K2 | Cambio satelital severo = proxy de daño; tasas condicionales a esta muestra (7 comunas); estrato de 2015 por lados de manzana. |
| Tasa de los estratos 1-2 (`respuesta.tasa_1_2`) | metrica | `/kpis` | `valor`, `numerador`, `denominador`, `ic95_inf`, `ic95_sup`, `muestra_baja` | `data/gold/kpis_gold.csv` | K2 | Un grupo con muestra baja se muestra, pero no se ordena frente a otros. |
| Diferencia de tasas con su intervalo de Newcombe (`respuesta.diferencia`) | metrica | `/kpis` | `valor`, `ic95_inf`, `ic95_sup` | `data/gold/kpis_gold.csv` | K2 | El estrato está confundido con la ubicación; asociación no es causalidad. |
| Razón de tasas 3-5 / 1-2 (`respuesta.razon`) | metrica | `/kpis` | `valor` | `data/gold/kpis_gold.csv` | K2 | La razón no trae intervalo en Gold. |
| Conclusión generada con la regla de redacción (`respuesta.conclusion`) | texto | `/kpis` | `valor`, `ic95_inf`, `ic95_sup`, `cota_inf`, `cota_sup` | `data/gold/kpis_gold.csv` | K2 | El estrato está confundido con la ubicación; asociación no es causalidad. |
| Resumen de la calidad de la llave (K5) (`respuesta.calidad`) | metrica | `/kpis` | `valor`, `numerador`, `denominador` | `data/gold/kpis_gold.csv` | K5 | El estrato es de 2015. |
| Alcance y aviso de la API (`respuesta.alcance`) | aviso | `/metadata` | `aviso` | `config/config.yaml` | — | Cambio satelital severo = proxy de daño; tasas condicionales a esta muestra (7 comunas); estrato de 2015 por lados de manzana. |

## Estratos (K1)
**Pregunta de negocio:** ¿Cuál es la tasa de cambio satelital severo en cada estrato y qué tan segura es?
**Rutas de la API:** `/kpis/K1`. **Dirección:** `/estratos`

| Componente | Tipo | Ruta | Campos | Archivo de salida | KPI | Advertencia visible |
|---|---|---|---|---|---|---|
| Tasa por estrato con intervalo de Wilson (`estratos.grafico`) | grafico | `/kpis/K1` | `valor`, `ic95_inf`, `ic95_sup`, `muestra_baja` | `data/gold/kpis_gold.csv` | K1 | Un grupo con muestra baja se muestra, pero no se ordena frente a otros. |
| Tabla de K1: casos, tasa, intervalo, sin datos y cotas (`estratos.tabla`) | tabla | `/kpis/K1` | `numerador`, `denominador`, `valor`, `pct_sin_datos`, `cota_inf`, `cota_sup` | `data/gold/kpis_gold.csv` | K1 | E2 tiene mucha falta de datos; E6 tiene pocas construcciones. |
| Lectura generada de K1 (`estratos.conclusion`) | texto | `/kpis/K1` | `muestra_baja`, `ic95_inf`, `ic95_sup` | `data/gold/kpis_gold.csv` | K1 | El estrato está confundido con la ubicación; asociación no es causalidad. |

## Comunas (K6)
**Pregunta de negocio:** ¿Cómo se reparte la tasa por comuna y en qué comunas se concentran los estratos 1-2?
**Rutas de la API:** `/comunas`, `/composicion`. **Dirección:** `/comunas`

| Componente | Tipo | Ruta | Campos | Archivo de salida | KPI | Advertencia visible |
|---|---|---|---|---|---|---|
| Tasa por comuna con intervalo de Wilson (`comunas.grafico`) | grafico | `/comunas` | `valor`, `ic95_inf`, `ic95_sup`, `muestra_baja` | `data/gold/kpis_gold.csv` | K6 | Un grupo con muestra baja se muestra, pero no se ordena frente a otros. |
| Tabla de K6 (`comunas.tabla`) | tabla | `/comunas` | `numerador`, `denominador`, `valor`, `pct_sin_datos` | `data/gold/kpis_gold.csv` | K6 | Solo 7 comunas; la Comuna 2 no está. |
| Construcciones con datos y severos por comuna y grupo de estrato (`comunas.composicion`) | tabla | `/composicion` | `comuna`, `estrato`, `sin_datos`, `severo_estricto` | `data/gold/gold_final.csv` | — | El estrato está confundido con la ubicación; asociación no es causalidad. |
| Texto generado: comuna que concentra los estratos 1-2 (`comunas.concentracion_1_2`) | texto | `/composicion` | `comuna`, `estrato`, `sin_datos` | `data/gold/gold_final.csv` | — | El estrato está confundido con la ubicación; asociación no es causalidad. |

## Sensibilidades (S0 a S5)
**Pregunta de negocio:** ¿Cambia la conclusión si se cambian el filtro de la llave o la definición de daño?
**Rutas de la API:** `/kpis/sensibilidad`. **Dirección:** `/sensibilidades`

| Componente | Tipo | Ruta | Campos | Archivo de salida | KPI | Advertencia visible |
|---|---|---|---|---|---|---|
| Diferencia 3-5 menos 1-2 por escenario (`sensibilidades.grafico`) | grafico | `/kpis/sensibilidad` | `tasa`, `ic95_inf`, `ic95_sup` | `data/gold/kpis_sensibilidad.csv` | K2 | S4 es de baja confianza. |
| Escenarios, filtros y resultados (`sensibilidades.tabla`) | tabla | `/kpis/sensibilidad` | `escenario`, `grupo`, `k`, `n`, `tasa`, `nota` | `data/gold/kpis_sensibilidad.csv` | K2 | S2 no sustituye a S1. |
| Razón ajustada por comuna (Mantel-Haenszel) y su advertencia (`sensibilidades.mantel_haenszel`) | tabla | `/kpis/sensibilidad` | `tasa`, `nota` | `data/gold/kpis_sensibilidad.csv` | K2 | Solo la Comuna 18 tiene ambos grupos. |
| Texto generado por escenario (`sensibilidades.conclusion`) | texto | `/kpis/sensibilidad` | `ic95_inf`, `ic95_sup`, `tasa` | `data/gold/kpis_sensibilidad.csv` | K2 | El estrato está confundido con la ubicación; asociación no es causalidad. |

## Concentración (K3 y K4)
**Pregunta de negocio:** ¿Se concentran los casos en pocos barrios y se asocia el estrato con la tasa por barrio?
**Rutas de la API:** `/kpis`. **Dirección:** `/concentracion`

| Componente | Tipo | Ruta | Campos | Archivo de salida | KPI | Advertencia visible |
|---|---|---|---|---|---|---|
| Los 10 barrios con más severos y su participación (`concentracion.k3`) | tabla | `/kpis` | `valor`, `numerador`, `denominador`, `nota` | `data/gold/kpis_gold.csv` | K3 | Concentración de casos no es mayor riesgo. |
| Spearman del estrato moda frente a la tasa por barrio (`concentracion.k4`) | metrica | `/kpis` | `valor`, `denominador`, `nota` | `data/gold/kpis_gold.csv` | K4 | Falacia ecológica; descriptivo. |

## Calidad de la llave
**Pregunta de negocio:** ¿Qué tan confiable es la unión entre las construcciones y el estrato del barrio?
**Rutas de la API:** `/calidad`, `/llave/revision`. **Dirección:** `/calidad`

| Componente | Tipo | Ruta | Campos | Archivo de salida | KPI | Advertencia visible |
|---|---|---|---|---|---|---|
| Cobertura de la llave, estrato válido y nombre validado (`calidad.k5`) | metrica | `/calidad` | `cobertura_llave`, `cobertura_estrato_valido`, `pct_nombre_validado`, `llave_confianza` | `data/silver/quality_report.json` | K5 | Qué NO demuestra: que el estrato de 2015 siga vigente. |
| Códigos de barrio con nombre no validado y su clasificación (`calidad.revision`) | tabla | `/llave/revision` | `codigo_barrio`, `nombre_barrio_csv`, `nombre_poligono`, `coincide_poligono` | `data/gold/gold_final.csv` | — | Es renumeración de códigos, no mala asignación. |

## Construcciones
**Pregunta de negocio:** ¿Qué construcciones hay detrás de las cifras y dónde están?
**Rutas de la API:** `/construcciones`, `/comunas`, `/kpis/K1`. **Dirección:** `/construcciones`

| Componente | Tipo | Ruta | Campos | Archivo de salida | KPI | Advertencia visible |
|---|---|---|---|---|---|---|
| Tabla paginada con filtros de la API (`construcciones.tabla`) | tabla | `/construcciones` | `objectid`, `comuna`, `barrio`, `estrato`, `clase_dano`, `severo_estricto` | `data/gold/gold_final.csv` | — | Una página no representa a toda la muestra. |
| Dispersión lon/lat por clase de daño (no es un mapa cartográfico) (`construcciones.dispersion`) | grafico | `/construcciones` | `lon`, `lat`, `clase_dano` | `data/gold/gold_final.csv` | — | No es un mapa cartográfico. |
| Descarga en CSV de lo mostrado (`construcciones.descarga`) | descarga | `/construcciones` | `objectid`, `comuna`, `barrio`, `estrato`, `clase_dano` | `data/gold/gold_final.csv` | — | Solo las filas mostradas. |

## Fuentes y sistema
**Pregunta de negocio:** ¿De dónde salen los datos, con qué licencia y qué no se puede concluir?
**Rutas de la API:** `/fuentes`, `/metadata`, `/health`. **Dirección:** `/fuentes`

| Componente | Tipo | Ruta | Campos | Archivo de salida | KPI | Advertencia visible |
|---|---|---|---|---|---|---|
| Fuentes con licencia y fechas (`fuentes.catalogo`) | tabla | `/fuentes`, `/metadata` | `id`, `rol`, `licencia`, `fechas` | `docs/bronze/catalogo_fuentes.json` | — | Licencias tomadas de los catálogos. |
| Fecha de corte, almacenamiento activo y filas por tabla (`fuentes.sistema`) | metrica | `/health`, `/metadata` | `fecha_edicion_capa`, `almacenamiento` | `config/config.yaml` | — | Cifras de este equipo. |
| Qué no se puede concluir y limitaciones (`fuentes.limites`) | texto | `/metadata` | `Qué NO se puede concluir` | `docs/gold/KPIs.md` | — | Cambio satelital severo = proxy de daño; tasas condicionales a esta muestra (7 comunas); estrato de 2015 por lados de manzana. |

## Alcance y límites
- **Qué afirmamos:** cada componente del panel tiene una ruta de la API, un campo y un archivo de salida declarados, y una prueba que los verifica.
- **Qué NO afirmamos:** que el panel cubra todas las preguntas posibles ni que la lectura de los gráficos sustituya la lectura de las limitaciones.
