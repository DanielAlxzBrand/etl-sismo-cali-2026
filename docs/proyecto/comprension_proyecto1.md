# Comprensión del Proyecto 1 — "Vulnerabilidad estructural en Cali tras el sismo del 10-ago-2026"

**Equipo:** Diego Fernando Gordillo Londoño · Jhoan Sebastián Castellanos Mayor · Daniel Alexander Brand García · **Curso:** ETL (UAO) · **Fecha de este documento:** 15-oct-2026

## Objetivo
**Objetivo del Proyecto 1** (evaluación estructural, no el indicador de este análisis): evidenciar con datos abiertos si la severidad del daño estructural en Cali se explica mejor por factores geotécnicos/constructivos de cada zona que por el estrato socioeconómico del barrio. Hoy es solo un patrón visible a simple vista (Capri, Guadalupe, Pampalinda, Tequendama, San Fernando, Cuarto de Legua: estratos 3–5, construcciones antiguas), sin análisis que lo confirme o lo descarte.

## Pregunta de negocio (Avance 1)
¿Por qué el terremoto afectó más a unas zonas de Cali que a otras, y el estrato lo explica o no?

## Variables
| Rol | Variable | Fuente prevista en Avance 1 |
|---|---|---|
| Dependiente | Severidad del daño por punto/barrio/comuna (colapso total, parcial, daño estructural): variable del Proyecto 1, basada en la evaluación estructural de la Alcaldía; en este análisis la reemplaza el proxy satelital | Repositorio Oficial, Alcaldía de Cali |
| Explicativa 1 | Nivel de amenaza sísmica oficial (alta/media/baja) | Datos Abiertos Cali (shapefile) |
| Explicativa 2 | Antigüedad constructiva | Prensa técnica (solo cualitativa) |
| Control | Estrato 1–6 por barrio/manzana | Datos Abiertos Cali / DANE |
| Contexto | Magnitud, profundidad, epicentro | SGC (no georreferenciable por barrio) |

## Alcance
Casco urbano de Cali; 5 KR: KR1 concentración de daño severo (aquí, cambio satelital severo), KR2 contraste con amenaza oficial, KR3 antigüedad (cualitativo, ≥3 fuentes), KR4 daño por estrato, KR5 avance de verificación. Usuarios: habitantes, Secretaría de Gestión del Riesgo, comunidad académica.

## Supuestos y límites que declara el Avance 1
- La hipótesis "no es el estrato" **no está comprobada**.
- Las cifras oficiales cambian a diario (el Avance 1 usa 878 verificadas de 5.545 reportes; 24 colapsos totales, 127 parciales, 192 con daño estructural).
- No hay fuente cuantitativa abierta de antigüedad por edificación.
- La causalidad es multifactorial; el estrato puede ser solo un proxy.

## Qué hereda este proyecto
- El flujo Bronze → Silver → Gold → Validación, con ≥1 API + ≥1 CSV/Excel unidos por JOIN.
- La variable de control (estrato) y la dependiente (daño), medibles con datos tabulares reales.
- Cubre KR1 y KR4 (con un proxy de daño); KR2 queda como extensión opcional; KR3 y KR5 no son ETL (cualitativo y seguimiento).

## Pregunta de negocio fijada para el ETL (refinada)
> **En las construcciones evaluadas por satélite en 7 comunas de Cali tras el sismo, ¿la proporción con cambio satelital severo (severo estricto, proxy de daño) cambia de forma relevante entre los estratos 1–6 de su barrio, o se concentra por zona sin depender del estrato?**

**Por qué se refina:** (1) es la porción del Proyecto 1 medible hoy con datos abiertos estructurados (no se halló tabla oficial de daño por barrio, solo boletines); (2) el estrato es la única variable de control con fuente tabular confirmada; (3) fija un denominador explícito (construcciones evaluadas) en vez de mezclar cifras de cortes distintos. **Costo:** el indicador es un proxy satelital, no una evaluación estructural (ATC-20) de la Alcaldía; no los mezclamos (tabla «Indicador satelital frente a evaluación estructural» en `docs/gold/KPIs.md`).

## Alerta de vigencia
Las cifras del Avance 1 son de un corte de mediados de agosto. Reportes posteriores indican 3.403 predios caracterizados (1.078 inseguros) y ~14.400 reportes ciudadanos. Citar siempre la fecha de corte en el README.

**Alcance temporal (recordatorio).** El estrato es de 2015 y las imágenes son de 2026, unos once años de distancia: los resultados por estrato describen el estrato de 2015 asignado al barrio, no el vigente. **Población (recordatorio).** Analizamos 5.146 construcciones de 7 comunas dentro de los polígonos de afectación preliminar; no se extrapolan a las construcciones de Cali. Detalle en `docs/gold/KPIs.md` y en el README. El documento de contexto del Avance 1 está en `docs/proyecto/referencias/contexto_y_problema.pdf`.
