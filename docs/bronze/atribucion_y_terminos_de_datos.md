# Atribución y términos de los datos

Este documento dice, fuente por fuente, **qué declara cada publicador** sobre sus datos y cómo los usa el proyecto. No es asesoría jurídica y no saca conclusiones legales: copia lo que dicen los metadatos que consultamos y marca como «no declarada» lo que no dice nada. Las licencias de cada fuente salen de los metadatos guardados en `docs/bronze/muestras/` y del catálogo [catalogo_fuentes_metadatos.md](catalogo_fuentes_metadatos.md), que se genera desde el manifiesto de Bronze. Todas las consultas se hicieron el 15-oct-2026 (hora de Bogotá).

**El código y los datos tienen términos distintos.** La licencia MIT de la raíz ([LICENSE](../../LICENSE)) cubre el código y la documentación propia del proyecto. Los archivos de `data/` y las muestras de `docs/bronze/muestras/` son datos de terceros o derivados de ellos y conservan los términos de su fuente, que son los de este documento.

## Qué declara cada fuente

| Fuente | Quién la publica | Qué declara sobre su licencia | Dónde consta | Uso en el proyecto |
|---|---|---|---|---|
| Impacto satelital en edificaciones por terremoto, Cali 2026 (`edificaciones`) | Fondo Adaptación; catalogada en datos.gov.co con el identificador `5vy8-gpw8`; servicio ArcGIS FeatureServer | CC BY 4.0, en el campo `Common Core.License` del catálogo (`https://creativecommons.org/licenses/by/4.0`). El servicio ArcGIS trae el campo `copyrightText` vacío | `docs/bronze/muestras/v3_socrata_views_5vy8.json` y `capa_meta.json` del snapshot de Bronze | Fuente principal: 5.146 construcciones, base de todos los indicadores de Gold |
| Estratificación socioeconómica según estrato, por barrio en Cali 2015 (`estrato_barrio`) | Departamento Administrativo de Planeación Municipal (DAPM) de Cali; en datos.cali.gov.co y enlazada desde datos.gov.co con el identificador `6esn-pmy5` | **Dos declaraciones distintas.** La página de datos.cali.gov.co dice «Licencia Creative Commons Attribution Share-Alike», sin indicar la versión. El catálogo de datos.gov.co indica CC0 (`https://creativecommons.org/publicdomain/zero/1.0/`) en `Common Core.License` | `docs/bronze/muestras/v4_ckan_licencia.txt` y `docs/bronze/muestras/v4_socrata_views_6esn.json` | Fuente principal: el estrato moda por barrio, asignado a cada construcción |
| Polígonos de barrios y sectores (`poligonos_barrios`) | DAPM Cali, servicio WFS del IDESC (`dapm:pdt_dpa_barrios_sectores`) | No declarada en el servicio | `docs/bronze/catalogo_fuentes_metadatos.md` | Solo validar la llave del JOIN; algunas columnas de Gold (`codigo_poligono`, `nombre_poligono`, `coincide_poligono`) se derivan de ellos |
| Evento sísmico `us6000tjl2` (`usgs`) | U.S. Geological Survey, servicio FDSN Event | No declarada en la verificación que hicimos | `docs/bronze/catalogo_fuentes_metadatos.md` | Solo contexto: una muestra de texto en `docs/bronze/muestras/`; no entra a Bronze ni al JOIN |
| Cifras de evaluación estructural de la Alcaldía de Cali | Reportadas por El País Cali | No aplica: son cifras de prensa | `docs/gold/resultados.md` (recuadro «Indicador satelital frente a evaluación estructural») | Solo contexto: se citan con su fecha y no se mezclan con ninguna cifra de Gold |

## Cómo tratamos el estrato por barrio

Los metadatos del CSV de estrato se contradicen (una página dice Creative Commons Attribution Share-Alike y otra CC0). Como no pudimos resolverlo con el publicador, **tratamos el CSV con la condición más restrictiva de las dos, por prudencia**: atribuimos siempre a DAPM Cali y, para los datos derivados de él (el estrato que lleva cada construcción en `gold_final.csv`, por ejemplo), pedimos atribución y compartir con la misma condición. Si el publicador aclarara CC0, esa atribución pasaría a ser voluntaria. La decisión está registrada en `docs/DECISIONES.md`.

## Atribución sugerida

- Capa de impacto satelital: Fondo Adaptación, catálogo datos.gov.co `5vy8-gpw8` (CC BY 4.0 según el catálogo; consulta del 15-oct-2026).
- Estratificación por barrio 2015: Departamento Administrativo de Planeación Municipal de Cali, datos.cali.gov.co (consulta del 15-oct-2026).
- Polígonos de barrios: IDESC / DAPM Cali (consulta del 15-oct-2026).
- Evento: USGS `us6000tjl2` (consulta del 15-oct-2026).
- Contexto externo: El País Cali, 11-oct-2026 y 23-sep-2026.

## Otros componentes con su propia licencia

- El archivo `orquestacion/docker-compose.yaml` se basa en el compose oficial de Apache Airflow 3.3.2, distribuido con la licencia Apache 2.0; el aviso del archivo original se conserva y los cambios están listados en `orquestacion/docker-compose.diff`.
- Las librerías de Python que fija `requirements.txt` y las imágenes de Docker (Airflow, Postgres, Redis y phpMyAdmin) conservan la licencia de su distribución; aquí no las copiamos ni las enumeramos.
