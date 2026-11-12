# 2. Mapeo de stakeholders y tipología de la organización

**Ítem del checklist:** «Realizamos el mapeo de stakeholders (partes interesadas) y comprendimos la tipología de la compañía para adaptar la solución propuesta.» · **Fecha:** 2026-11-11 · Índice: [indice.md](indice.md)

> **Declaración expresa.** No hubo contacto ni validación con stakeholders; este mapa se basa en el Avance 1 y en fuentes públicas. La valoración de interés e influencia es nuestra y está marcada como [Hipótesis del equipo, por validar].

## 1. Tipología de la organización destino y del proyecto
- **Organización destino (supuesto S1):** entidad pública territorial de gestión del riesgo (la Secretaría de Gestión del Riesgo de Cali) y la comunidad académica. No hubo contacto con ninguna de ellas. [Hipótesis del equipo, por validar]
- **Naturaleza del proyecto:** investigación aplicada de estudiantes; no es una compañía, no tiene clientes ni ingresos. [Evidencia en el repo: `README.md (autores y curso)`; `docs/entrega_2/seccion_1/indice.md`]
- **Tres rasgos que condicionan la solución:**
  1. *Sector público y decisiones de priorización.* El Avance 1 plantea que una entidad de gestión del riesgo podría usar un análisis que cruce fuentes dispersas para priorizar dónde reforzar estudios estructurales. La solución debe, por tanto, decir con claridad qué zonas cubre y cuáles no. [Evidencia en el repo: `docs/referencias/avance_1_contexto_y_problema.pdf, p. 2`; `docs/KPIs.md «Población analizada»`]
  2. *Restricciones de datos abiertos.* La capa satelital es de un tercero y puede cambiar, no hay datos por predio y las licencias de las fuentes difieren; por eso la reproducibilidad descansa en el snapshot de Bronze con su manifiesto y sha256. [Evidencia en el repo: `README.md §5, §6 y §11`; `data/bronze/manifest.jsonl`]
  3. *Cifras sensibles y cambiantes.* Las cifras oficiales cambian a diario y una mala lectura puede alarmar o dar falsa seguridad; por eso todas las salidas llevan fecha de corte, intervalos y porcentaje sin datos. [Evidencia en el repo: `docs/referencias/avance_1_contexto_y_problema.pdf, p. 1`; `docs/KPIs.md`] Que una mala lectura tenga ese efecto sobre la población es una apreciación nuestra. [Hipótesis del equipo, por validar]

## 2. Tabla de stakeholders
| stakeholder | rol y fuente del rol | interés / influencia | necesidad de información | relación con nuestros indicadores | riesgo si se interpreta mal |
|---|---|---|---|---|---|
| Habitantes de las zonas afectadas | Usuario principal descrito en el Avance 1: quienes viven en las zonas más golpeadas y preguntan qué tan segura es su zona. [Evidencia en el repo: `docs/referencias/avance_1_contexto_y_problema.pdf, p. 2`] | alto / bajo [Hipótesis del equipo, por validar] | Entender qué se mide, con qué incertidumbre y qué no se puede decir de su barrio. | Tasas por comuna (K6) y por estrato (K1); porcentaje sin datos. | Leer una tasa de la muestra como la probabilidad de que su construcción esté dañada; alarma o falsa seguridad. |
| Entidad de gestión del riesgo del municipio (Secretaría de Gestión del Riesgo de Emergencias y Desastres de la Alcaldía de Cali) | Segundo grupo de usuarios del Avance 1: maneja información dispersa y podría priorizar estudios estructurales y prevención. [Evidencia en el repo: `docs/referencias/avance_1_contexto_y_problema.pdf, p. 2`] | alto / alta [Hipótesis del equipo, por validar] | Dónde hay cambio satelital severo, con qué cobertura y qué zonas no están cubiertas. | K3 (concentración), K6 (comunas), población analizada y alcance temporal. | Priorizar inspecciones solo con el proxy y sin evaluación técnica, o ignorar las comunas ausentes, incluida la Comuna 2. |
| Alcaldía de Cali como productora de cifras y de evaluaciones estructurales (ATC-20) | Publica balances de predios evaluados con sticker rojo, amarillo y verde; sus cifras son contexto externo. [Evidencia en el repo: `README.md «Indicador satelital frente a evaluación estructural»`] [Fuente externa: https://www.elpais.com.co/cali/alcaldia-de-cali-entrega-balance-de-gestion-tras-el-sismo-mas-de-3400-edificaciones-evaluadas-y-45000-familias-damnificadas-2338.html, publicada el 23-sep-2026; fecha de consulta no registrada] | alto / alta [Hipótesis del equipo, por validar] | Que nuestro indicador no se confunda con su evaluación y que las unidades (predios y construcciones) no se mezclen. | Ninguno: no comparamos ni mezclamos sus cifras con Gold. | Presentar el proxy como sustituto de la evaluación estructural. |
| Departamento Administrativo de Planeación Municipal (DAPM) de Cali | Publica el estrato por barrio 2015 (lados de manzana) y, con IDESC, los barrios. [Evidencia en el repo: `README.md §5.2`] | medio / alta [Hipótesis del equipo, por validar] | Qué uso se hace del estrato 2015 y de sus códigos, y con qué desfase. | K1, K2, K4 (usan el estrato); K5 (cobertura de la llave). | Atribuir al estrato vigente un resultado que usa el de 2015. |
| IDESC (servicio WFS de barrios y sectores) | Publica los polígonos de barrios 2026 que usamos solo para validar la llave. [Evidencia en el repo: `README.md §5.3`] | bajo / media [Hipótesis del equipo, por validar] | Qué códigos de polígono corresponden a qué códigos de 2015. | K5 (nombre validado) y la revisión de códigos de barrio. | Concluir que un código distinto significa un barrio distinto (hay renumeración). |
| Entidad que publica la capa satelital (Fondo Adaptación; catálogo datos.gov.co) | Publicadora de la capa «Impacto Satelital en Edificaciones por Terremoto. Cali 2026». [Evidencia en el repo: `README.md §5.1`] | medio / alta [Hipótesis del equipo, por validar] | Que el proxy se describa con su método, fechas de imágenes y límites. | Todos los KPI (el severo estricto sale de su clasificación). | Atribuirle conclusiones de daño estructural que la capa no hace. |
| Entidades geológicas nacionales y USGS | El Avance 1 las lista como fuente del contexto técnico del evento; el README usa el registro de USGS solo como contexto. [Evidencia en el repo: `docs/referencias/avance_1_contexto_y_problema.pdf, p. 4`; `README.md §5.4`] | medio / baja [Hipótesis del equipo, por validar] | Que el evento (magnitud, fecha) se cite correctamente. | Ninguno (contexto del evento). | Mezclar la intensidad o la magnitud con nuestros KPI sin llave espacial. |
| Unidad Nacional para la Gestión del Riesgo de Desastres (UNGRD; fuente original del RUD) | Fuente original de los datos municipales de daños del plan B; la ruta usada es un monitor de un solo mantenedor. [Evidencia en el repo: `docs/investigacion_fuentes.md (F8)`] | medio / media [Hipótesis del equipo, por validar] | Que el plan B (municipal) quede documentado y no se confunda con el plan elegido. | Ninguno: el plan elegido no usa esta fuente. | Citar datos del monitor como oficiales. |
| Comunidad académica y profesor del curso (UAO) | Tercer grupo de usuarios del Avance 1 (comunidad académica); el profesor evalúa la entrega. [Evidencia en el repo: `docs/referencias/avance_1_contexto_y_problema.pdf, p. 2`; `docs/entrega_2/retroalimentacion_avance_2.txt`] | alto / alta [Hipótesis del equipo, por validar] | Reproducibilidad, trazabilidad, honestidad sobre límites y evidencia verificable. | KPI de desempeño del proyecto (E3) y criterios del MVP (E5). | Entender que se validó con usuarios o stakeholders cuando no ocurrió. |
| Equipo del proyecto | Diseña, construye y documenta el análisis; responde por sus límites. [Evidencia en el repo: `README.md (autores)`] | alto / alta [Hipótesis del equipo, por validar] | Saber qué falta validar antes de afirmarlo. | Todos. | Afirmar sin respaldo lo que es hipótesis. |

## 3. Matriz poder-interés
Todas las ubicaciones son estimaciones nuestras. [Hipótesis del equipo, por validar]

| | **interés bajo o medio** | **interés alto** |
|---|---|---|
| **poder alto** | *Mantener satisfechos:* DAPM, Fondo Adaptación | *Gestionar de cerca:* entidad de gestión del riesgo, Alcaldía (evaluación estructural), profesor |
| **poder bajo** | *Monitorear:* IDESC, entidades geológicas y USGS, UNGRD | *Mantener informados:* habitantes, comunidad académica, equipo |

**Estrategia de comunicación propuesta por cuadrante** [Hipótesis del equipo, por validar]
- *Gestionar de cerca:* entregar el documento de resultados con los recuadros de alcance temporal, población analizada y la tabla «indicador satelital frente a evaluación estructural», y pedir observaciones antes de cualquier uso para decisiones.
- *Mantener satisfechos:* citar y atribuir correctamente cada fuente y licencia (README §17) y avisar del uso de sus datos.
- *Mantener informados:* resumen en lenguaje sencillo con los límites por delante; sin cifras de la muestra como si fueran de la ciudad.
- *Monitorear:* revisar periódicamente si publican datos nuevos (por ejemplo un estrato más reciente o datos por predio).

## 4. Cómo adaptamos la solución a cada tipo de stakeholder
| tipo | qué se entrega hoy | advertencias que siempre acompañan |
|---|---|---|
| Entidad pública de gestión del riesgo | `README.md`, `docs/KPIs.md` y las tablas de `data/gold/` (K1 a K6, sensibilidades) [Evidencia en el repo: `README.md`; `docs/KPIs.md`; `data/gold/kpis_gold.csv`] | Población analizada (7 comunas), alcance temporal (estrato 2015), proxy y no evaluación estructural, porcentaje sin datos. |
| Habitantes | Nada específico para ellos: hoy no existe un producto para esta audiencia. Podría ser un resumen futuro. [Hipótesis del equipo, por validar] | Las tasas no son prevalencias ni la probabilidad de que una construcción concreta esté dañada. |
| Productores de datos (DAPM, IDESC, Fondo Adaptación) | Atribución y licencias en `README.md` §17 y trazabilidad por sha256 [Evidencia en el repo: `README.md §17`] | Las limitaciones de sus datos (estrato 2015, polígonos 2026 renumerados) no son un juicio sobre su calidad. |
| Comunidad académica y profesor | Repositorio ejecutable, 50 pruebas, registro de decisiones y verificación de entrega [Evidencia en el repo: `docs/DECISIONES.md`; `docs/verificacion_entrega.md`; `tests/`] | No se hicieron pruebas con usuarios; no hay frontend. |

## 5. Contactos realizados
No hubo contactos con stakeholders. Este campo es para que el equipo lo complete solo si ocurrieron; sin registro, no se puede afirmar nada.

| fecha | con quién (rol) | qué se habló | dónde está el registro |
|---|---|---|---|
| (sin completar) | (sin completar) | (sin completar) | (sin completar) |
