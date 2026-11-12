# 4. Modelo de negocio (Canvas), propuesta de valor y Data Innovation Board

**Ítem del checklist:** «Estructuramos el Modelo de Negocio (CANVAS), Data Innovation Board y la propuesta de valor con enfoque de creación de Startups de AI/Datos.» · **Fecha:** 2026-11-11 · Índice: [indice.md](indice.md)

> **Aviso.** Este documento es un ejercicio de diseño con hipótesis sin validar. No hay clientes, usuarios ni mercado medidos, no hubo entrevistas ni pruebas con nadie, y no estimamos ingresos, precios ni costos: cuando aparecen escribimos «no estimado». Nada de lo que sigue debe leerse como un plan de negocio validado.

> **Etiquetas.** [Evidencia en el repo: `ruta`] = existe en el repositorio; [Fuente externa: URL y fecha de consulta]; [Hipótesis del equipo, por validar] = juicio nuestro, por validar.

## 1. Concepto de producto (hipótesis)
Un servicio de análisis reproducible de impacto sísmico por zonas, con incertidumbre explícita, derivado de este proyecto: tomaría fuentes abiertas, las integraría con trazabilidad y entregaría indicadores con intervalos, cobertura y límites, listo para repetirse cuando cambien las fuentes. [Hipótesis del equipo, por validar]

Lo que existe hoy es solo el pipeline, sus indicadores y su documentación para 5.146 construcciones de 7 comunas. [Evidencia en el repo: `README.md`; `data/gold/`] No existe ningún servicio, producto, interfaz ni cliente.

## 2. Modelo de negocio (Canvas)
| bloque | contenido |
|---|---|
| 1. Segmentos de clientes | Entidad pública territorial de gestión del riesgo (supuesto S1) y comunidad académica. El Avance 1 los describe como usuarios del análisis; no son clientes: no hubo contacto. [Evidencia en el repo: `docs/referencias/avance_1_contexto_y_problema.pdf, p. 2`] Que sean un segmento de clientes es [Hipótesis del equipo, por validar] |
| 2. Propuesta de valor | Un análisis reproducible del cambio satelital severo por zonas, con intervalos, porcentaje sin datos, población y alcance temporal declarados y trazabilidad hasta el dato crudo. [Hipótesis del equipo, por validar] Las capacidades que lo sustentan existen: [Evidencia en el repo: `README.md`; `docs/KPIs.md`; `data/bronze/manifest.jsonl`] |
| 3. Canales | Hoy el único canal real es el repositorio entregado al curso. [Evidencia en el repo: `README.md`] Informes, presentaciones y publicación abierta del código y de los datos derivados serían canales futuros. [Hipótesis del equipo, por validar] |
| 4. Relación con clientes | Explicación de los límites de lectura y actualización por fecha de corte cuando cambie la fuente. [Hipótesis del equipo, por validar] No existe hoy ninguna relación. |
| 5. Fuentes de ingresos | No estimado. Ni siquiera hemos definido si existirían ingresos o financiación; no hay precios, mercado ni disposición de pago medidos. |
| 6. Recursos clave | Código del pipeline, pruebas automáticas, documentación, snapshots con sha256 y datos derivados. [Evidencia en el repo: `src/`; `tests/`; `docs/`; `data/`] |
| 7. Actividades clave | Extraer, limpiar, integrar, calcular indicadores con incertidumbre, verificar y documentar. [Evidencia en el repo: `README.md §4 a §10`] |
| 8. Socios clave | Los productores de las fuentes (Fondo Adaptación, DAPM Cali, IDESC) son proveedores de datos hoy; su papel como socios sería [Hipótesis del equipo, por validar] [Evidencia en el repo: `README.md §5 y §17`] |
| 9. Estructura de costos | No estimado. Categorías que aparecerían, sin cifras: tiempo del equipo, cómputo y almacenamiento, y mantenimiento ante cambios en las fuentes. [Hipótesis del equipo, por validar] |

## 3. Propuesta de valor
### 3.1 Perfil del cliente (hipótesis)
| elemento | contenido | etiqueta |
|---|---|---|
| Trabajos | Priorizar dónde reforzar estudios estructurales o dónde concentrar esfuerzos de prevención. | [Evidencia en el repo: `docs/referencias/avance_1_contexto_y_problema.pdf, p. 2`] |
| Trabajos | Responder con evidencia a la pregunta de por qué un barrio resultó más afectado que otros cercanos. | [Evidencia en el repo: `docs/referencias/avance_1_contexto_y_problema.pdf, p. 2`] |
| Frustraciones | La información de daños y amenaza ya existe, pero está dispersa. | [Evidencia en el repo: `docs/referencias/avance_1_contexto_y_problema.pdf, p. 2`] |
| Frustraciones | Las cifras oficiales cambian a diario y se responden preguntas con rumores o supuestos. | [Evidencia en el repo: `docs/referencias/avance_1_contexto_y_problema.pdf, p. 1-2`] |
| Frustraciones | No sabemos cuáles de estas frustraciones sienten de verdad los usuarios. | [Hipótesis del equipo, por validar] |
| Beneficios esperados | Decidir con indicadores que digan cuánta muestra tienen detrás y qué zonas no cubren. | [Hipótesis del equipo, por validar] |
| Beneficios esperados | Poder repetir el análisis cuando haya un corte nuevo o un estrato más reciente. | [Hipótesis del equipo, por validar] |

### 3.2 Mapa de valor, vinculado a capacidades reales
| elemento | contenido | capacidad real (ruta) |
|---|---|---|
| Producto o servicio | Pipeline medallion y tablas Gold con K1 a K6 y sensibilidades | [Evidencia en el repo: `src/`; `data/gold/kpis_gold.csv`; `data/gold/kpis_sensibilidad.csv`] |
| Aliviador de frustraciones | Fuentes cruzadas por una llave verificada, con huérfanos conservados | [Evidencia en el repo: `data/silver/silver_orphans_left.csv`; `docs/validacion_llave.md`; `docs/revision_codigos_barrio.md`] |
| Aliviador de frustraciones | Cada cifra lleva fecha de corte y trazabilidad al dato crudo | [Evidencia en el repo: `data/bronze/manifest.jsonl`; `docs/KPIs.md`] |
| Creador de beneficios | Incertidumbre declarada: intervalos de Wilson y Newcombe, cotas por falta de datos y seis escenarios de sensibilidad | [Evidencia en el repo: `docs/KPIs.md`; `data/gold/kpis_sensibilidad.csv`] |
| Creador de beneficios | Límites explícitos de población y de alcance temporal | [Evidencia en el repo: `docs/KPIs.md «Población analizada» y «Alcance temporal»`] |
| Creador de beneficios | Verificación automática y repetibilidad | [Evidencia en el repo: `tests/`; `docs/prueba_entorno_limpio.md`] |

Que estos elementos resuelvan un problema real de algún usuario es [Hipótesis del equipo, por validar]

## 4. Data Innovation Board
| elemento | contenido |
|---|---|
| Problema de negocio | Falta de un análisis público y verificable que explique el patrón de daño por zonas y por estrato. [Evidencia en el repo: `docs/referencias/avance_1_contexto_y_problema.pdf, p. 3`] |
| Decisión que apoya | Priorizar dónde hacer o profundizar estudios estructurales y de prevención. [Hipótesis del equipo, por validar] |
| Fuentes de datos actuales (reales) | Capa satelital por construcción (Fondo Adaptación, 5.146 filas), estrato por barrio 2015 (DAPM Cali, 346 barrios), polígonos de barrios (IDESC, 342 polígonos) y contexto del evento (USGS). [Evidencia en el repo: `README.md §5`; `data/bronze/manifest.jsonl`] |
| Datos que faltan | Evaluaciones estructurales por predio en una fuente descargable; estrato actualizado; amenaza sísmica oficial; antigüedad constructiva por construcción; las comunas ausentes, entre ellas la Comuna 2. [Evidencia en el repo: `README.md §17`; `docs/comprension_proyecto1.md`] |
| Enfoque analítico actual | Estadística descriptiva e inferencial sobre un proxy satelital: tasas con intervalo de Wilson, diferencia con intervalo de Newcombe, razón de Mantel-Haenszel, Spearman con permutación y sensibilidades. No entrenamos modelos de aprendizaje automático. [Evidencia en el repo: `README.md §9`; `docs/KPIs.md`; `src/transform/build_gold.py`] |
| Enfoques futuros posibles (no hechos) | Visión por computador sobre las imágenes para tener una medida propia de cambio en lugar de depender de la clasificación de un tercero; aprendizaje supervisado para estimar vulnerabilidad si existiera una fuente de evaluación por predio con permisos de uso; ambos requieren datos que hoy no tenemos. [Hipótesis del equipo, por validar] |
| Usuarios | Entidad pública de gestión del riesgo y comunidad académica (descritos en el Avance 1; sin contacto). [Evidencia en el repo: `docs/referencias/avance_1_contexto_y_problema.pdf, p. 2`] |
| Valor esperado (cualitativo) | Menos supuestos en la conversación sobre dónde mirar primero, y una base reproducible para actualizar. No estimado en términos económicos. [Hipótesis del equipo, por validar] |
| Riesgos y consideraciones éticas | *Sesgo de selección:* solo hay construcciones dentro de los polígonos de afectación preliminar y 7 comunas. [Evidencia en el repo: `docs/KPIs.md «Población analizada»`] *Uso indebido:* priorizar inspecciones solo con el proxy y sin evaluación técnica. [Hipótesis del equipo, por validar] *Privacidad:* `gold_final.csv` no trae nombres de propietarios ni identificadores de predio (`ID_PREDIO` se descarta), pero sí coordenadas de cada construcción. [Evidencia en el repo: `docs/verificacion_entrega.md`; `data/gold/gold_final.csv`] *Estigmatización de zonas por una tasa sin contexto.* [Hipótesis del equipo, por validar] |
| Recursos y capacidades | Código en Python, pruebas, documentación y conocimiento del equipo sobre las fuentes; sin recursos económicos definidos (no estimado). [Evidencia en el repo: `requirements.txt`; `src/`; `tests/`] |
| Métricas de éxito | Las de desempeño del proyecto (cobertura de llave, filas de Gold, pruebas, determinismo y empaquetado) [Evidencia en el repo: `docs/entrega_2/seccion_1/03_objetivo_alcance_okr_kpi.md §3.2`]; las de adopción y uso no están definidas ni medidas. [Hipótesis del equipo, por validar] |
| Hoja de ruta de validación | Primero validar la necesidad con usuarios reales (SC1, SC2, SC4), luego comparar el proxy con evaluaciones estructurales (SC3), después ver la disponibilidad de datos (SC5). Ninguno está ejecutado. [Hipótesis del equipo, por validar] |

## 5. Supuestos críticos y experimentos propuestos (no ejecutados)
Los números de personas son tamaños de muestra propuestos para el experimento y no son cifras de mercado. [Hipótesis del equipo, por validar]

| # | supuesto | experimento propuesto | evidencia que lo confirmaría | evidencia que lo refutaría |
|---|---|---|---|---|
| SC1 | Una entidad de gestión del riesgo necesita un análisis por zonas con incertidumbre explícita. | Entrevistas estructuradas con 3 a 5 personas de entidades de gestión del riesgo | Describen decisiones de priorización que hoy toman sin ese análisis | Dicen que ya cuentan con él o que no lo usarían |
| SC2 | Los indicadores sirven para priorizar verificaciones o estudios. | Mostrar K3 y K6 a personal técnico y comparar con su criterio de prioridad | Coinciden en qué zonas mirar primero y entienden los límites | Las zonas priorizadas no tienen que ver con las suyas |
| SC3 | El cambio satelital severo se relaciona con la evaluación estructural. | Con datos por predio disponibles, cruzar el severo estricto con el sticker ATC-20 en una muestra | Asociación clara y estable entre ambos | Asociación débil o nula |
| SC4 | Los lectores entienden que las tasas no son prevalencias de Cali. | Prueba de comprensión con 5 a 8 lectores sobre los recuadros de alcance | La mayoría contesta correctamente qué se puede y qué no se puede concluir | Muchos las leen como probabilidades de la ciudad |
| SC5 | Habrá datos futuros utilizables (estrato más reciente, datos por predio) con licencia. | Solicitud formal de datos a los productores | Entregan datos con licencia de uso | No hay datos o no hay permiso |
| SC6 | Un análisis repetible por corte vale más que uno puntual. | Preguntar a posibles usuarios si pedirían actualizaciones periódicas | Piden actualizaciones y dicen con qué frecuencia | Les basta un informe único |
| SC7 | Mantener el pipeline ante cambios de la fuente es viable para el equipo. | Repetir la extracción con `--refresh` (necesita red) y comparar snapshots | La diferencia se detecta y se documenta sin cambios de código | Cambia el esquema y rompe la limpieza |
| SC8 | Existe una vía de financiación o convenio (no estimada). | Explorar convocatorias o convenios, sin comprometer cifras | Hay una vía identificable | No hay ninguna vía razonable |

## 6. Qué no afirmamos
- Que haya clientes, usuarios, entrevistas, pruebas de usabilidad o validación de cualquier tipo.
- Que alguna entidad pidió, usa o respalda este análisis.
- Cifras de mercado, precios, ingresos, costos, número de usuarios o disposición de pago: no estimado.
- Que el proyecto sea una startup, tenga plan comercial o esté listo para operar como servicio.
- Que usemos aprendizaje automático: no lo hacemos; lo que hicimos es estadística descriptiva e inferencial.
- Que el proxy satelital sustituya una evaluación estructural.
- Que el Canvas, la propuesta de valor o el Data Innovation Board estén validados.

## 7. Nota sobre la plantilla del curso
Si el curso entrega una plantilla propia de Data Innovation Board o de Canvas, el equipo adaptará este contenido a ella; la estructura de este documento es genérica.
