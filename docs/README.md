# Documentación del proyecto

Índice de la documentación del ETL medallion del sismo M7.4 del 10 de agosto de 2026 (Bronze → Silver → Gold → validación, API de solo lectura, catálogo de fuentes y seguridad). Está organizada por capas: cada carpeta de `docs/` corresponde a una capa o a un tema del proyecto. El README de la raíz resume el proyecto y explica cómo ejecutarlo; aquí se encuentra el detalle.

> **Alcance de los resultados.** Los indicadores son un proxy satelital (cambio satelital severo, severo estricto), no una evaluación estructural; describen 7 comunas de Cali dentro de los polígonos de afectación preliminar, con estrato de 2015. No se generalizan a Cali.

**Cómo agregar un documento.** Cada carpeta tiene su tabla; para documentar algo nuevo basta agregar una fila a la tabla de su carpeta (y, si es un componente nuevo, mover su fila de «en construcción» al índice por capas). Las carpetas nuevas se crean solo cuando hay contenido.

## Índice por capas
### `proyecto/` · contexto y decisiones técnicas
| documento | para qué sirve |
|---|---|
| [comprension_proyecto1.md](proyecto/comprension_proyecto1.md) | qué pide el enunciado y qué heredamos del documento de contexto y problema |
| [entorno.md](proyecto/entorno.md) | estado del entorno (Python, paquetes, WSL2, Docker, MySQL) y qué falta instalar por componente |
| [decisiones_tecnicas.md](proyecto/decisiones_tecnicas.md) | decisiones técnicas de los componentes (API, almacén, panel, orquestación, MLOps) con respaldos |
| `proyecto/referencias/` | documento de contexto y problema (`contexto_y_problema.pdf`) y la imagen del enunciado del flujo |

### `estrategia/` · problema, stakeholders, objetivos y MVP
| documento | para qué sirve |
|---|---|
| [indice.md](estrategia/indice.md) | índice de la estrategia, reglas de honestidad y estado de los cinco documentos |
| [01_data_thinking.md](estrategia/01_data_thinking.md) | marco de Data Thinking, insights y problema central |
| [02_stakeholders.md](estrategia/02_stakeholders.md) | mapa de stakeholders con la rúbrica R1 y la matriz poder-interés |
| [03_objetivo_alcance_okr_kpi.md](estrategia/03_objetivo_alcance_okr_kpi.md) | objetivo, alcance, OKR, KPI, métricas de valor y trazabilidad |
| [04_canvas_data_innovation_board.md](estrategia/04_canvas_data_innovation_board.md) | Canvas, propuesta de valor, Data Innovation Board e hipótesis |
| [05_mvp_criterios_aceptacion.md](estrategia/05_mvp_criterios_aceptacion.md) | MVP, funcionalidades y 29 criterios de aceptación con su estado |
| `estrategia/img/` | matriz poder-interés y Canvas (renderizados desde los documentos; no son capturas) |

### `bronze/` · fuentes y catálogo
| documento | para qué sirve |
|---|---|
| [investigacion_fuentes.md](bronze/investigacion_fuentes.md) | investigación y selección de fuentes (fichas 1 a 11) |
| [verificacion_fuentes.md](bronze/verificacion_fuentes.md) | verificación previa de las fuentes (V1 a V14) |
| [catalogo_fuentes_metadatos.md](bronze/catalogo_fuentes_metadatos.md) | catálogo de fuentes y metadatos, generado desde el manifiesto |
| [catalogo_fuentes.json](bronze/catalogo_fuentes.json) | el mismo catálogo en JSON; lo sirve `GET /fuentes` |
| [atribucion_y_terminos_de_datos.md](bronze/atribucion_y_terminos_de_datos.md) | qué declara cada fuente sobre su licencia, cómo tratamos el estrato por barrio y la atribución sugerida |
| `bronze/muestras/` | muestras de texto de cada fuente probada (no es Bronze) |

### `silver/` · limpieza, llave y calidad
| documento | para qué sirve |
|---|---|
| [hallazgos_eda.md](silver/hallazgos_eda.md) | hallazgos H1 a H18 del análisis exploratorio |
| [reglas_silver.md](silver/reglas_silver.md) | reglas R01 a R18, cada una con su hallazgo |
| [validacion_llave.md](silver/validacion_llave.md) | validación semántica de la llave por código de barrio |
| [revision_codigos_barrio.md](silver/revision_codigos_barrio.md) | revisión de los códigos con diferencias en la validación |

### `gold/` · indicadores
| documento | para qué sirve |
|---|---|
| [KPIs.md](gold/KPIs.md) | definición de K1 a K6, sensibilidades S0 a S5 y diccionario de columnas de Gold |
| [resultados.md](gold/resultados.md) | contexto, fuentes, capas, cómo leer los indicadores, resultados, limitaciones y glosario |

### `diagramas/` y `img/` · imágenes del README
| carpeta | para qué sirve |
|---|---|
| `diagramas/` | los dos diagramas en color aportados por Daniel, sin fuente en texto (`arquitectura_nueva.png` y `flujo_dag_nueva.png`, EV-112); el README usa sus copias en gris de `img/readme/`; además, sin uso en el README, la fuente en texto (`*.yaml`) de los diagramas de arquitectura y del DAG y su imagen en escala de grises (`*.svg`, `*.png`) dibujada con `scripts/make_diagramas.py` |
| `img/insignias/` | insignias del README (SVG), generadas con `scripts/make_insignias.py` |
| `img/readme/` | copias en escala de grises de las capturas y de los dos diagramas aportados (`arquitectura_gris.png` y `flujo_dag_gris.png`), generadas con `scripts/make_imagenes_readme.py`; el registro con el origen y el sha256 está en `docs/evidencias/readme/` |

### `api/` · capa de servicio
| documento | para qué sirve |
|---|---|
| [arquitectura.md](api/arquitectura.md) | arquitectura del backend y de la API de solo lectura (contratos, errores, seguridad, rendimiento) |
| `api/img/` | diagrama de la arquitectura del backend |

### `seguridad/` · credenciales
| documento | para qué sirve |
|---|---|
| [gestion_credenciales.md](seguridad/gestion_credenciales.md) | política de credenciales, claves y tokens, y uso del escáner de secretos |

### `validacion/` · verificaciones
| documento | para qué sirve |
|---|---|
| [verificacion_del_paquete.md](validacion/verificacion_del_paquete.md) | verificación del proyecto contra el enunciado |
| [verificacion_servicios.md](validacion/verificacion_servicios.md) | verificación de la API, las fuentes y las credenciales (subcriterios y estado) |
| [prueba_entorno_limpio.md](validacion/prueba_entorno_limpio.md) | ejecución en una copia limpia |
| [verificacion_logging.md](validacion/verificacion_logging.md) | verificación del registro de ejecución |
| [matriz_casos_prueba.md](validacion/matriz_casos_prueba.md) | casos de prueba por función crítica (generada) |
| [informe_pruebas.md](validacion/informe_pruebas.md) | resultado esperado, obtenido y evidencia por prueba, con cobertura (generado) |
| [registro_defectos.md](validacion/registro_defectos.md) | defectos corregidos y su prueba de regresión |
| `validacion/sha256_antes_logging.txt`, `validacion/sha256_despues_logging.txt` | huellas antes y después de agregar el registro |

### `checklist/` · estado y evidencias del checklist
| documento | para qué sirve |
|---|---|
| [estado_checklist.md](checklist/estado_checklist.md) | los 30 ítems del checklist con su estado, componente de cierre y cómo validarlos |
| [guia_de_evidencias.md](checklist/guia_de_evidencias.md) | por ítem: archivo principal, apoyo, texto sugerido, captura opcional y cómo validar |
| [trazabilidad.md](checklist/trazabilidad.md) y [trazabilidad.csv](checklist/trazabilidad.csv) | ítem → requisito → archivos → pruebas → evidencias → comando de los 30 ítems; el CSV es la única fuente y la tabla se genera con `python scripts/validar_checklist.py --escribir` |

### `evidencias/` · salidas registradas
| contenido | para qué sirve |
|---|---|
| [manifiesto.md](evidencias/manifiesto.md) | índice de evidencias (EV-nnn) con comando, fecha, ruta y sha256 |
| `evidencias/base/`, `evidencias/estrategia/`, `evidencias/api/` | salidas crudas registradas por tema (conservan los nombres de pruebas y rutas de su momento de captura) |

### `retroalimentacion/` · retroalimentación recibida
| documento | para qué sirve |
|---|---|
| [retroalimentacion_recibida.txt](retroalimentacion/retroalimentacion_recibida.txt) | retroalimentación original (no se edita) |
| [registro_de_cambios.md](retroalimentacion/registro_de_cambios.md) | retroalimentación recibida y cómo la atendimos |

### Pruebas y orquestación
| documento | contenido |
|---|---|
| [orquestacion/README.md](orquestacion/README.md) | índice del componente y dónde está cada cosa |
| [diferencias_con_la_guia.md](orquestacion/diferencias_con_la_guia.md) | diferencias permitidas con la guía de Airflow y hallazgos |
| [guia_de_implementacion.md](orquestacion/guia_de_implementacion.md) | pasos 13 a 44 de la guía con su estado y evidencia |
| [mlops_y_produccion.md](orquestacion/mlops_y_produccion.md) | prácticas de producción aplicadas y lo que no aplica |
| [operacion.md](orquestacion/operacion.md) | levantar, parar, registros y solución de problemas |

### Panel
| documento | contenido |
|---|---|
| [panel/README.md](panel/README.md) | índice del componente, cómo ejecutarlo y evidencias |
| [guia_de_uso.md](panel/guia_de_uso.md) | qué muestra cada página, cómo leer intervalos y avisos, y qué no se puede concluir |
| [arquitectura_panel.md](panel/arquitectura_panel.md) | capas, flujo, errores y seguridad del panel, con su diagrama |
| [trazabilidad_ui.md](panel/trazabilidad_ui.md) | componente, ruta de la API, campo, archivo de salida y pregunta de negocio (generado) |
| [pruebas_panel.md](panel/pruebas_panel.md) | pruebas del panel y resultados de las evidencias |
| [accesibilidad_y_respuesta.md](panel/accesibilidad_y_respuesta.md) | contrastes calculados, mediciones locales y lo pendiente de usuarios |

### Usuarios y finanzas
| documento | contenido |
|---|---|
| [usuarios/README.md](usuarios/README.md) | índice del componente: qué está preparado, qué falta y los cinco pasos para las sesiones reales |
| [evaluacion_heuristica.md](usuarios/evaluacion_heuristica.md) | evaluación heurística interna del panel: hallazgos con severidad y captura, fortalezas y matriz |
| [protocolo_sesiones.md](usuarios/protocolo_sesiones.md), [guion_sesion.md](usuarios/guion_sesion.md), [consentimiento.md](usuarios/consentimiento.md) e [instrumentos.md](usuarios/instrumentos.md) | material de las sesiones con personas usuarias (preparado; sin sesiones realizadas) |
| [registro_de_friccion.md](usuarios/registro_de_friccion.md) y [trazabilidad_de_cambios.md](usuarios/trazabilidad_de_cambios.md) | las 14 fricciones de la evaluación heurística con su decisión y la tabla de cambios llena (iteración técnica, no sesiones con personas) |
| [guia_simulacion/README.md](usuarios/guia_simulacion/README.md) | guía en PDF (con su generador) para que las tres personas del equipo hagan sesiones de uso del panel en su propio equipo; material preparado, sin sesiones hechas |
| [finanzas/estructura_costos.md](finanzas/estructura_costos.md) | categorías de costo, consumo medido y fórmulas con precios como parámetros vacíos |

### Servicios locales (`instalacion/`)
| documento | contenido |
|---|---|
| [instalacion/README.md](instalacion/README.md) | guía de instalación: requisitos, qué pruebas se omiten sin Git y cuál modo elegir |
| [modo_minimo.md](instalacion/modo_minimo.md) | pipeline, API y panel con SQLite, sin Docker ni MySQL |
| [modo_completo.md](instalacion/modo_completo.md) | MySQL, panel con MySQL, Airflow y phpMyAdmin de solo lectura |
| [errores_comunes.md](instalacion/errores_comunes.md) | síntomas, causa probable y qué hacer al instalar y ejecutar |

### Decisiones
[DECISIONES.md](DECISIONES.md): todas las decisiones con alternativas, razón, riesgo y fecha (D1 a D105; las nuevas continúan desde D106).

### Almacenamiento relacional (MySQL)
| documento | contenido |
|---|---|
| [modelo_datos.md](almacenamiento/modelo_datos.md) | diccionario de datos y diagrama entidad-relación, generados del esquema SQL |
| [mysql_configuracion.md](almacenamiento/mysql_configuracion.md) | qué crea `configurar_mysql.py`, privilegios, rotación, fallos y revocación |
| [carga_y_verificacion.md](almacenamiento/carga_y_verificacion.md) | cómo cargar, verificar, medir lotes, respaldar y servir la API desde MySQL |
| [gestion_credenciales.md](seguridad/gestion_credenciales.md) | variables `MYSQL_*`, alta segura del usuario y comprobación canario |
| [verificacion_servicios.md](validacion/verificacion_servicios.md) | verificación de los ítems 4.1, 4.2 y 4.3 y revalidación del 2.3 (sección «Carga relacional») |

## Componentes en construcción
| componente | estado |
|---|---|
| Documentación y demostración | en construcción: falta el diagrama de la arquitectura del sistema, la sección de primera vez del README y el guion de demostración |
| Cierre y paquete | en construcción: falta publicar el repositorio y armar el paquete final |

Las evidencias del almacenamiento relacional están en `docs/evidencias/almacenamiento/`; las de la orquestación están en `docs/evidencias/orquestacion/`; las del panel, en `docs/evidencias/panel/`; las del endurecimiento (instalación desde cero, mutaciones y Airflow en vivo), en `docs/evidencias/endurecimiento/`; las de los servicios locales, en `docs/evidencias/servicios/`; las de la evaluación del panel y sus ajustes, en `docs/evidencias/usuarios/` y `docs/evidencias/ajustes_ux/`; las de la auditoría intermedia (independencia del repositorio), en `docs/evidencias/auditoria/`.

## Componentes del proyecto y los ítems del checklist que cierran
| componente | ítems que cierra | estado |
|---|---|---|
| Base y orden | ninguno (deja la línea base protegida y el entorno documentado) | hecho |
| Estrategia | 1.1, 1.2, 1.3, 1.4 | hecho |
| API, fuentes y credenciales | 2.1, 2.2, 2.3 | hecho |
| Carga relacional | 4.1, 4.2, 4.3 | hecho |
| Pruebas y orquestación | 5.1, 5.2, 5.4, 5.5, 5.6 | hecho |
| Panel | 1.5, 3.1, 3.2, 5.3 | hecho |
| Usuarios, UX y finanzas | 3.3, 6.1, 6.2, 6.3, 6.4 | hecho en lo técnico; 6.1, 6.2 y 6.3 esperan sesiones reales (hecho externo) |
| Servicios locales | avance de 7.1; revalida 4.1, 4.2 y 5.4 | hecho |
| Documentación y demostración | 6.5, 7.2, 7.3, 7.4, 7.5 | en construcción |
| Cierre y paquete | 7.1 | en construcción |

El detalle de cada ítem (estado, evidencia y cómo validarlo) está en `docs/checklist/estado_checklist.md`.

## Dónde está cada cosa
| si buscas… | está en… |
|---|---|
| cómo ejecutar el proyecto | `README.md` (raíz) |
| cómo instalar el proyecto en otro equipo | `docs/instalacion/README.md` |
| de dónde vienen los datos y qué licencia tienen | `docs/bronze/catalogo_fuentes_metadatos.md` |
| por qué una regla de limpieza existe | `docs/silver/reglas_silver.md` y `docs/silver/hallazgos_eda.md` |
| cómo se calcula un indicador | `docs/gold/KPIs.md` |
| los endpoints de la API y sus errores | `docs/api/arquitectura.md` |
| cómo ejecutar y leer el panel | `docs/panel/guia_de_uso.md` |
| dónde va una credencial | `docs/seguridad/gestion_credenciales.md` |
| el estado de cada ítem del checklist | `docs/checklist/estado_checklist.md` |
| qué archivo adjuntar como evidencia de un ítem | `docs/checklist/guia_de_evidencias.md` |
| por qué se decidió algo | `docs/DECISIONES.md` |
| qué se pidió en la retroalimentación y cómo respondimos | `docs/retroalimentacion/registro_de_cambios.md` |

## Notas
- `data/silver/quality_report.json` conserva en el texto de la regla R10 la ruta anterior del documento de hallazgos (`docs/hallazgos_eda.md`): es una salida protegida (su sha256 es parte de la línea base) y el código que la genera conserva ese texto para que regenerar el pipeline dé exactamente los mismos bytes. El documento está hoy en `docs/silver/hallazgos_eda.md`.
