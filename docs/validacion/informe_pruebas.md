# Informe de pruebas: resultado esperado, obtenido y evidencia

Salida real registrada el 2026-11-13 (2026-11-13T22:54:22-05:00, America/Bogota), commit `b274ef9`. Generado con `python scripts/informe_pruebas.py`; no se edita a mano.

## Resumen

- **Pruebas ejecutadas:** 316; **pasan:** 316; **fallan:** 0; **omitidas:** 0. Duración: 72.6 s. Código de salida de pytest: 0.
- **Casos de la matriz:** 118 (funciones críticas: 19); el resultado esperado de cada uno está en [matriz_casos_prueba.md](matriz_casos_prueba.md).

## Por archivo de pruebas

| Archivo | Pruebas | Pasan | Duración (s) |
|---|---|---|---|
| `tests/test_api.py` | 17 | 17 | 1.54 |
| `tests/test_canario_extra.py` | 5 | 5 | 0.53 |
| `tests/test_carga_relacional.py` | 54 | 54 | 8.68 |
| `tests/test_carga_sqlite.py` | 5 | 5 | 2.04 |
| `tests/test_casos_limite.py` | 19 | 19 | 0.95 |
| `tests/test_catalogo.py` | 5 | 5 | 0.57 |
| `tests/test_configurar_mysql.py` | 25 | 25 | 2.87 |
| `tests/test_dag_estatico.py` | 24 | 24 | 0.08 |
| `tests/test_dist.py` | 17 | 17 | 1.38 |
| `tests/test_empaquetado_y_revision.py` | 5 | 5 | 0.24 |
| `tests/test_entorno_de_pruebas.py` | 4 | 4 | 0.01 |
| `tests/test_estrategia.py` | 14 | 14 | 20.34 |
| `tests/test_evidencias.py` | 4 | 4 | 0.06 |
| `tests/test_extract.py` | 6 | 6 | 0.18 |
| `tests/test_informe_pruebas.py` | 6 | 6 | 0.22 |
| `tests/test_kpis.py` | 6 | 6 | 0.07 |
| `tests/test_logger.py` | 2 | 2 | 0.01 |
| `tests/test_matriz_casos.py` | 7 | 7 | 0.28 |
| `tests/test_pipeline_reproducible.py` | 4 | 4 | 3.04 |
| `tests/test_quality.py` | 4 | 4 | 0.11 |
| `tests/test_readme_cifras.py` | 13 | 13 | 3.02 |
| `tests/test_respaldo_y_medicion.py` | 12 | 12 | 7.77 |
| `tests/test_secretos.py` | 10 | 10 | 12.10 |
| `tests/test_transform.py` | 7 | 7 | 0.21 |
| `tests/test_usuario_docker.py` | 41 | 41 | 0.66 |

## Por caso (resultado esperado y obtenido)

| CP | Caso | Tipo | Resultado esperado | Resultado obtenido | Estado | Duración (s) | Evidencia |
|---|---|---|---|---|---|---|---|
| CP-001 | El manifiesto existe y tiene líneas | correcto | manifest.jsonl no vacío | cumplió lo esperado | pasa | 0.01 | `tests/test_extract.py::test_manifiesto_existe_y_no_vacio` |
| CP-002 | Cada archivo existe y su sha256 coincide con el manifiesto | correcto | 8 de 8 coinciden | cumplió lo esperado | pasa | 0.03 | `tests/test_extract.py::test_archivos_existen_y_sha256_coincide` |
| CP-003 | Las páginas suman el conteo oficial de la capa | correcto | 5.146 filas en 3 páginas | cumplió lo esperado | pasa | 0.01 | `tests/test_extract.py::test_paginas_suman_el_conteo_oficial` |
| CP-004 | El conteo de filas del manifiesto coincide con el contenido | límite | filas del manifiesto = filas leídas | cumplió lo esperado | pasa | 0.10 | `tests/test_extract.py::test_rows_coherente_con_el_contenido` |
| CP-005 | El manifiesto no repite rutas | incorrecto | ninguna ruta duplicada | cumplió lo esperado | pasa | 0.01 | `tests/test_extract.py::test_sin_paths_duplicados` |
| CP-006 | El manifiesto no guarda tokens en sus parámetros | incorrecto | ningún campo sensible | cumplió lo esperado | pasa | 0.01 | `tests/test_extract.py::test_campos_del_manifiesto_sin_tokens` |
| CP-007 | Tipos esperados en Silver | correcto | columnas con el tipo declarado | cumplió lo esperado | pasa | 0.05 | `tests/test_transform.py::test_tipos_esperados_silver` |
| CP-008 | Sin duplicados por llave natural | correcto | OBJECTID único | cumplió lo esperado | pasa | 0.11 | `tests/test_transform.py::test_cero_duplicados_por_llave_natural` |
| CP-009 | Fechas en zona horaria de Bogotá | correcto | zona America/Bogota | cumplió lo esperado | pasa | 0.04 | `tests/test_transform.py::test_zona_horaria_bogota` |
| CP-010 | Reporte de calidad con todos los campos | correcto | campos presentes | cumplió lo esperado | pasa | 0.00 | `tests/test_quality.py::test_reporte_con_todos_los_campos` |
| CP-011 | Gold con el mínimo de filas y sin duplicados | límite | al menos el umbral configurado | cumplió lo esperado | pasa | 0.05 | `tests/test_quality.py::test_gold_minimo_de_filas_y_sin_duplicados` |
| CP-012 | El CSV de estrato se lee como UTF-8 y se limpia | correcto | una fila por barrio con código único | cumplió lo esperado | pasa | 0.04 | `tests/test_casos_limite.py::test_la_limpieza_del_estrato_acepta_una_sola_fila_real` |
| CP-013 | Revisión de códigos de barrio por categoría | correcto | las categorías suman las construcciones sin nombre validado | cumplió lo esperado | pasa | 0.02 | `tests/test_empaquetado_y_revision.py::test_categorias_de_la_revision_suman_las_construcciones_sin_nombre_validado` |
| CP-014 | Revisión de códigos con los casos pedidos | incorrecto | cada caso cae en su categoría | cumplió lo esperado | pasa | 0.00 | `tests/test_empaquetado_y_revision.py::test_revision_de_codigos_cubre_los_casos_pedidos` |
| CP-015 | Una sola fila de estrato | límite | se limpia sin error | cumplió lo esperado | pasa | 0.04 | `tests/test_casos_limite.py::test_la_limpieza_del_estrato_acepta_una_sola_fila_real` |
| CP-016 | Normalización de nombres | correcto | texto normalizado | cumplió lo esperado | pasa | 0.00 | `tests/test_transform.py::test_normalize_key` |
| CP-017 | Código de barrio = comuna por 100 más barrio | correcto | código esperado | cumplió lo esperado | pasa | 0.00 | `tests/test_transform.py::test_codigo_barrio` |
| CP-018 | La cobertura del JOIN supera el umbral | correcto | cobertura >= 0,80 | cumplió lo esperado | pasa | 0.03 | `tests/test_quality.py::test_cobertura_join_supera_umbral` |
| CP-019 | Entradas mínimas para las llaves | límite | cadena vacía y un carácter se aceptan | cumplió lo esperado | pasa | 0.00 | `tests/test_casos_limite.py::test_las_llaves_aceptan_entradas_minimas` |
| CP-020 | Revisión de llave coincide con Silver | correcto | mismos códigos y conteos | cumplió lo esperado | pasa | 0.04 | `tests/test_api.py::test_revision_de_llave_coincide_con_silver` |
| CP-021 | Vectores de Wilson | correcto | límites con 4 decimales | cumplió lo esperado | pasa | 0.00 | `tests/test_kpis.py::test_wilson_vectores` |
| CP-022 | Vector de Newcombe | correcto | diferencia e intervalo | cumplió lo esperado | pasa | 0.00 | `tests/test_kpis.py::test_newcombe_vector` |
| CP-023 | Mantel-Haenszel con una sola comuna | límite | razón calculada solo con la comuna disponible | cumplió lo esperado | pasa | 0.01 | `tests/test_kpis.py::test_mantel_haenszel_una_comuna` |
| CP-024 | Construcciones sin datos satelitales no entran en Mantel-Haenszel | incorrecto | se excluyen del cálculo | cumplió lo esperado | pasa | 0.02 | `tests/test_kpis.py::test_regresion_defecto_mh_sin_datos_no_entra_en_mh` |
| CP-025 | Consistencia entre K1, K5 y K6 y rangos | correcto | valores en [0, 1] y sumas consistentes | cumplió lo esperado | pasa | 0.02 | `tests/test_kpis.py::test_consistencia_k1_k6_k5_y_rangos` |
| CP-026 | K1 recalculado desde Gold | correcto | igual a kpis_gold.csv | cumplió lo esperado | pasa | 0.02 | `tests/test_kpis.py::test_k1_recalculado_desde_gold` |
| CP-027 | Wilson con un solo registro | límite | intervalo válido dentro de [0, 1] | cumplió lo esperado | pasa | 0.00 | `tests/test_casos_limite.py::test_wilson_con_un_solo_registro_da_un_intervalo_valido` |
| CP-028 | Wilson sin registros | límite | nan en lugar de dividir por cero | cumplió lo esperado | pasa | 0.00 | `tests/test_casos_limite.py::test_wilson_sin_registros_da_nan_en_lugar_de_dividir_por_cero` |
| CP-029 | Newcombe con un registro por grupo | límite | diferencia observada dentro del intervalo | cumplió lo esperado | pasa | 0.00 | `tests/test_casos_limite.py::test_newcombe_con_un_registro_por_grupo_incluye_la_diferencia_observada` |
| CP-030 | Mantel-Haenszel con un registro | límite | razón vacía y comuna excluida | cumplió lo esperado | pasa | 0.01 | `tests/test_casos_limite.py::test_mantel_haenszel_con_un_registro_no_inventa_una_razon` |
| CP-031 | Indicadores con un solo registro | límite | grupos vacíos con denominador 0 | cumplió lo esperado | pasa | 0.02 | `tests/test_casos_limite.py::test_los_indicadores_con_un_solo_registro_se_calculan_y_los_grupos_vacios_quedan_en_cero` |
| CP-032 | KPI presentes y en rango | correcto | K1 a K6 con valores válidos | cumplió lo esperado | pasa | 0.03 | `tests/test_quality.py::test_kpis_presentes_y_en_rango` |
| CP-033 | Sensibilidades iguales al CSV | correcto | filas idénticas | cumplió lo esperado | pasa | 0.09 | `tests/test_api.py::test_kpis_y_sensibilidad_son_iguales_a_los_csv` |
| CP-034 | Escenario no válido en la API | incorrecto | 422 con el JSON de error uniforme | cumplió lo esperado | pasa | 0.09 | `tests/test_api.py::test_parametros_invalidos_dan_422_con_el_json_uniforme` |
| CP-035 | La ruta de sensibilidades va antes que /kpis/{id} | límite | no se confunde con un id de KPI | cumplió lo esperado | pasa | 0.01 | `tests/test_api.py::test_orden_de_rutas_sensibilidad_antes_que_kpi_id` |
| CP-036 | Contenido igual al de la base versionada | correcto | 4 tablas con el mismo contenido | cumplió lo esperado | pasa | 0.50 | `tests/test_carga_sqlite.py::test_el_contenido_cargado_es_igual_al_de_la_base_versionada` |
| CP-037 | Cargar dos veces | límite | mismas tablas sin duplicar filas | cumplió lo esperado | pasa | 0.75 | `tests/test_carga_sqlite.py::test_cargar_dos_veces_reemplaza_las_tablas_sin_duplicar_filas` |
| CP-038 | Una sola fila por tabla | límite | una fila en cada tabla | cumplió lo esperado | pasa | 0.23 | `tests/test_carga_sqlite.py::test_con_una_sola_fila_por_tabla_se_cargan_cuatro_filas` |
| CP-039 | CSV de entrada ausente | incorrecto | FileNotFoundError y conexión cerrada | cumplió lo esperado | pasa | 0.26 | `tests/test_carga_sqlite.py::test_un_csv_ausente_falla_y_no_deja_la_conexion_abierta` |
| CP-040 | La carga no toca el repositorio | correcto | la base versionada conserva su hash | cumplió lo esperado | pasa | 0.30 | `tests/test_carga_sqlite.py::test_la_carga_no_modifica_el_repositorio` |
| CP-041 | Conversión correcta de cada tipo | correcto | valores convertidos sin pérdida | cumplió lo esperado | pasa | 0.02 | `tests/test_carga_relacional.py::test_conversion_correcta` |
| CP-042 | Valores que perderían información | incorrecto | ConversionError con mensaje claro | cumplió lo esperado | pasa | 0.02 | `tests/test_carga_relacional.py::test_conversion_que_perderia_informacion_falla` |
| CP-043 | Carga completa | correcto | 346, 5.146, 23 y 107 filas | cumplió lo esperado | pasa | 1.34 | `tests/test_carga_relacional.py::test_la_carga_completa_concilia_al_cien_por_ciento` |
| CP-044 | Repetir la carga | límite | responde «ya cargada» y no escribe | cumplió lo esperado | pasa | 0.02 | `tests/test_carga_relacional.py::test_la_carga_repetida_es_idempotente` |
| CP-045 | Clave de corrida determinista y sensible a la entrada | correcto | misma entrada, misma clave | cumplió lo esperado | pasa | 0.05 | `tests/test_carga_relacional.py::test_la_clave_de_corrida_es_determinista_y_sensible_a_cada_entrada` |
| CP-046 | Entrada alterada | correcto | corrida nueva y la anterior intacta | cumplió lo esperado | pasa | 1.23 | `tests/test_carga_relacional.py::test_una_entrada_alterada_crea_una_corrida_nueva_y_conserva_la_anterior` |
| CP-047 | Fallo a mitad de carga | incorrecto | reversión completa | cumplió lo esperado | pasa | 1.52 | `tests/test_carga_relacional.py::test_un_fallo_a_mitad_de_la_carga_revierte_todo` |
| CP-048 | Valor ilegible | incorrecto | falla antes de escribir nada | cumplió lo esperado | pasa | 0.26 | `tests/test_carga_relacional.py::test_un_valor_ilegible_falla_antes_de_escribir_nada` |
| CP-049 | Una sola fila por tabla | límite | carga y concilia al 100 % | cumplió lo esperado | pasa | 0.24 | `tests/test_casos_limite.py::test_la_carga_con_una_sola_fila_por_tabla_concilia_al_cien_por_ciento` |
| CP-050 | Entrada vacía | límite | se rechaza sin crear nada | cumplió lo esperado | pasa | 0.23 | `tests/test_casos_limite.py::test_una_entrada_vacia_se_rechaza_sin_crear_nada_en_la_base` |
| CP-051 | Archivo de entrada ausente | incorrecto | FileNotFoundError sin tocar la base | cumplió lo esperado | pasa | 0.03 | `tests/test_casos_limite.py::test_un_archivo_de_entrada_ausente_se_rechaza_sin_tocar_la_base` |
| CP-052 | La carga no escribe en data/ | correcto | data/ conserva sus sha256 | cumplió lo esperado | pasa | 0.93 | `tests/test_carga_relacional.py::test_la_carga_no_escribe_en_data` |
| CP-053 | Esquemas de MySQL y SQLite con las mismas columnas | correcto | paridad sin diferencias | cumplió lo esperado | pasa | 0.01 | `tests/test_carga_relacional.py::test_los_dos_esquemas_declaran_las_mismas_tablas_y_columnas_en_el_mismo_orden` |
| CP-054 | Sin filas huérfanas | correcto | 0 en cada relación | cumplió lo esperado | pasa | 0.01 | `tests/test_carga_relacional.py::test_la_integridad_referencial_no_deja_huerfanos` |
| CP-055 | Construcciones sin cruce de barrio | límite | se conservan con el enlace nulo | cumplió lo esperado | pasa | 0.01 | `tests/test_carga_relacional.py::test_los_huerfanos_de_estrato_se_conservan_con_el_enlace_nulo` |
| CP-056 | Violaciones de integridad | incorrecto | diez violaciones rechazadas | cumplió lo esperado | pasa | 0.13 | `tests/test_carga_relacional.py::test_las_violaciones_de_integridad_se_rechazan` |
| CP-057 | Borrar una corrida con datos | incorrecto | rechazado por RESTRICT | cumplió lo esperado | pasa | 0.01 | `tests/test_carga_relacional.py::test_no_se_puede_borrar_una_corrida_con_datos` |
| CP-058 | La conciliación detecta un valor alterado | incorrecto | 1 diferencia en la columna alterada | cumplió lo esperado | pasa | 0.34 | `tests/test_carga_relacional.py::test_la_conciliacion_detecta_un_valor_alterado` |
| CP-059 | Primera configuración | correcto | bases y usuario creados; .env con nombres | cumplió lo esperado | pasa | 0.03 | `tests/test_configurar_mysql.py::test_primera_configuracion_crea_bases_usuario_y_escribe_solo_nombres` |
| CP-060 | La contraseña del administrador no se guarda | correcto | no llega a .env, SQL ni registro | cumplió lo esperado | pasa | 0.05 | `tests/test_configurar_mysql.py::test_la_contrasena_del_administrador_nunca_se_guarda_ni_llega_a_sql` |
| CP-061 | Privilegios incorrectos | incorrecto | se rechazan y .env no cambia | cumplió lo esperado | pasa | 0.08 | `tests/test_configurar_mysql.py::test_privilegios_incorrectos_se_rechazan_y_no_se_escribe_env` |
| CP-062 | Servidor anterior a 8.0 | incorrecto | se rechaza con mensaje claro | cumplió lo esperado | pasa | 0.02 | `tests/test_configurar_mysql.py::test_servidor_antiguo_se_rechaza` |
| CP-063 | Repetir con credenciales válidas | límite | no cambia nada ni pide la contraseña | cumplió lo esperado | pasa | 0.05 | `tests/test_configurar_mysql.py::test_con_credenciales_validas_no_cambia_nada_ni_pide_la_contrasena_del_administrador` |
| CP-064 | Creación con permisos mínimos sobre la base real | correcto | solo `sismo_cali`, sin globales ni GRANT OPTION | cumplió lo esperado | pasa | 0.04 | `tests/test_usuario_docker.py::test_crea_el_usuario_con_permisos_solo_sobre_la_base_real_y_escribe_nombres` |
| CP-065 | Orígenes válidos | correcto | IP privada, nombre exacto o red privada | cumplió lo esperado | pasa | 0.01 | `tests/test_usuario_docker.py::test_origenes_validos` |
| CP-066 | Orígenes con comodines o públicos | incorrecto | rechazados | cumplió lo esperado | pasa | 0.02 | `tests/test_usuario_docker.py::test_origenes_rechazados` |
| CP-067 | Permisos distintos de los esperados | incorrecto | se rechazan y .env no cambia | cumplió lo esperado | pasa | 0.14 | `tests/test_usuario_docker.py::test_permisos_distintos_de_los_esperados_se_rechazan` |
| CP-068 | Repetir con el .env completo | límite | no pide contraseña y no cambia | cumplió lo esperado | pasa | 0.06 | `tests/test_usuario_docker.py::test_es_idempotente_y_no_pide_la_contrasena_si_el_env_esta_completo` |
| CP-069 | Respaldo con manifiesto | correcto | un CSV por tabla y manifiesto sha256 | cumplió lo esperado | pasa | 1.53 | `tests/test_respaldo_y_medicion.py::test_el_respaldo_escribe_un_csv_por_tabla_con_manifiesto` |
| CP-070 | Restauración conciliada | correcto | huellas iguales en 7 tablas | cumplió lo esperado | pasa | 2.08 | `tests/test_respaldo_y_medicion.py::test_restaurar_reproduce_cada_tabla_con_la_misma_huella` |
| CP-071 | Respaldo alterado | incorrecto | se rechaza antes de restaurar | cumplió lo esperado | pasa | 0.71 | `tests/test_respaldo_y_medicion.py::test_un_respaldo_alterado_se_rechaza_antes_de_restaurar` |
| CP-072 | Destino con datos | límite | no se restaura encima | cumplió lo esperado | pasa | 0.83 | `tests/test_respaldo_y_medicion.py::test_no_se_restaura_encima_de_datos` |
| CP-073 | Cada endpoint responde 200 con su estructura | correcto | 11 rutas válidas | cumplió lo esperado | pasa | 0.26 | `tests/test_api.py::test_cada_endpoint_responde_200_con_la_estructura_esperada` |
| CP-074 | Parámetros inválidos | incorrecto | 422 con JSON uniforme | cumplió lo esperado | pasa | 0.09 | `tests/test_api.py::test_parametros_invalidos_dan_422_con_el_json_uniforme` |
| CP-075 | Identificadores y rutas inexistentes | incorrecto | 404 uniforme | cumplió lo esperado | pasa | 0.02 | `tests/test_api.py::test_ids_inexistentes_dan_404_y_rutas_desconocidas_tambien` |
| CP-076 | Límites de paginación | límite | mínimo, máximo y offset respetados | cumplió lo esperado | pasa | 0.09 | `tests/test_api.py::test_limites_de_paginacion_y_offset` |
| CP-077 | Extremos de paginación | límite | una fila, página final y página vacía | cumplió lo esperado | pasa | 0.09 | `tests/test_casos_limite.py::test_la_pagina_de_un_solo_registro_y_la_pagina_final` |
| CP-078 | Inyección en filtros | incorrecto | rechazada | cumplió lo esperado | pasa | 0.12 | `tests/test_api.py::test_la_inyeccion_en_comuna_y_estrato_se_rechaza` |
| CP-079 | Solo GET | incorrecto | los demás métodos dan 405 | cumplió lo esperado | pasa | 0.11 | `tests/test_api.py::test_solo_existen_rutas_get_y_los_demas_metodos_dan_405` |
| CP-080 | Base ausente | incorrecto | 503 y /health degradado | cumplió lo esperado | pasa | 0.07 | `tests/test_api.py::test_base_ausente_da_503_y_health_degradado` |
| CP-081 | Misma respuesta desde el almacén relacional | correcto | 17 rutas idénticas entre almacenes | cumplió lo esperado | pasa | 0.69 | `tests/test_carga_relacional.py::test_la_api_sirve_lo_mismo_desde_el_almacen_relacional_que_desde_sqlite` |
| CP-082 | No escribe en data/ ni en la base | correcto | hashes idénticos tras consultar todo | cumplió lo esperado | pasa | 0.36 | `tests/test_api.py::test_consultar_todos_los_endpoints_no_escribe_en_data_ni_en_la_base` |
| CP-083 | El catálogo coincide con el manifiesto | correcto | mismas huellas y filas | cumplió lo esperado | pasa | 0.05 | `tests/test_catalogo.py::test_el_catalogo_coincide_con_el_manifiesto` |
| CP-084 | Cubre todas las fuentes del manifiesto | correcto | ninguna fuente sin ficha | cumplió lo esperado | pasa | 0.01 | `tests/test_catalogo.py::test_el_catalogo_cubre_todas_las_fuentes_del_manifiesto` |
| CP-085 | Dos generaciones son idénticas | límite | salida determinista | cumplió lo esperado | pasa | 0.45 | `tests/test_catalogo.py::test_dos_generaciones_son_identicas` |
| CP-086 | El diccionario de Gold describe todas las columnas | incorrecto | ninguna columna sin descripción | cumplió lo esperado | pasa | 0.00 | `tests/test_catalogo.py::test_el_diccionario_de_gold_describe_todas_las_columnas` |
| CP-087 | Sin hallazgos en el árbol | correcto | 0 hallazgos | cumplió lo esperado | pasa | 9.45 | `tests/test_secretos.py::test_sin_hallazgos_en_el_arbol_de_trabajo` |
| CP-088 | Un secreto sembrado por tipo | incorrecto | se detecta cada uno | cumplió lo esperado | pasa | 0.03 | `tests/test_secretos.py::test_detecta_un_secreto_sembrado_de_cada_tipo` |
| CP-089 | Huellas, rutas y URLs largas | límite | no se marcan como secretos | cumplió lo esperado | pasa | 0.01 | `tests/test_secretos.py::test_no_marca_huellas_ni_rutas_ni_urls_largas` |
| CP-090 | Contraseña sembrada con canario | incorrecto | se detecta sin imprimirla | cumplió lo esperado | pasa | 0.77 | `tests/test_configurar_mysql.py::test_el_canario_detecta_la_contrasena_sembrada_sin_imprimirla` |
| CP-091 | Contraseña de un .env extra | incorrecto | se detecta sin imprimirla | cumplió lo esperado | pasa | 0.01 | `tests/test_canario_extra.py::test_detecta_la_contrasena_del_env_extra_en_el_arbol_sin_imprimirla` |
| CP-092 | Enmascarado del registro | correcto | tokens y cabeceras reemplazados por *** | cumplió lo esperado | pasa | 0.01 | `tests/test_logger.py::test_enmascara_cabeceras_y_tokens` |
| CP-093 | Lo permitido entra y el zip se verifica | correcto | zip sin entradas prohibidas | cumplió lo esperado | pasa | 0.05 | `tests/test_dist.py::test_lo_permitido_entra_y_el_zip_pasa_la_verificacion` |
| CP-094 | Entornos virtuales y carpetas ocultas | incorrecto | no entran | cumplió lo esperado | pasa | 0.04 | `tests/test_dist.py::test_entorno_sin_pyvenv_cfg_no_entra_al_zip` |
| CP-095 | dags y orquestacion presentes o ausentes | límite | entran si existen y no fallan si faltan | cumplió lo esperado | pasa | 0.15 | `tests/test_dist.py::test_orquestacion_entra_cuando_existe_y_no_falla_cuando_no_existe` |
| CP-096 | El repositorio real | correcto | solo primer nivel permitido, con dags y orquestacion | cumplió lo esperado | pasa | 0.23 | `tests/test_dist.py::test_el_repo_real_empaqueta_el_dag_y_la_carpeta_de_orquestacion` |
| CP-097 | Cifras del README iguales a las salidas | correcto | K5, K2 y Gold coinciden | cumplió lo esperado | pasa | 0.01 | `tests/test_readme_cifras.py::test_cifras_de_gold_bronze_y_silver_en_readme` |
| CP-098 | Conteo de pruebas del README | correcto | igual a la recolección | cumplió lo esperado | pasa | 2.97 | `tests/test_readme_cifras.py::test_numero_de_pruebas_en_readme` |
| CP-099 | Estados de los 30 ítems | correcto | completos y con componentes válidos | cumplió lo esperado | pasa | 0.01 | `tests/test_estrategia.py::test_los_30_items_del_checklist_estan_completos_y_con_componentes_de_la_lista` |
| CP-100 | Alteraciones de los 30 ítems | incorrecto | cada alteración se detecta | cumplió lo esperado | pasa | 0.13 | `tests/test_estrategia.py::test_negativas_de_los_30_items` |
| CP-101 | Alteraciones de los criterios del MVP | incorrecto | cada alteración se detecta | cumplió lo esperado | pasa | 0.14 | `tests/test_estrategia.py::test_negativas_de_los_criterios_del_mvp` |
| CP-102 | Evidencias saneadas | correcto | sin rutas ni usuario | cumplió lo esperado | pasa | 0.03 | `tests/test_evidencias.py::test_las_evidencias_guardadas_estan_saneadas` |
| CP-103 | Recálculo independiente de K1 | correcto | diferencia máxima menor de 1e-9 frente a kpis_gold.csv | cumplió lo esperado | pasa | 0.07 | `tests/test_informe_pruebas.py::test_el_recalculo_independiente_coincide_con_los_kpi_publicados` |
| CP-104 | Informe con esperado y obtenido, sin rutas de la máquina | correcto | caso fallido marcado y sin rutas | cumplió lo esperado | pasa | 0.14 | `tests/test_informe_pruebas.py::test_el_informe_se_genera_con_esperado_obtenido_y_sin_rutas_de_la_maquina` |
| CP-105 | Una definición de la matriz con una prueba inexistente | incorrecto | se detecta | cumplió lo esperado | pasa | 0.09 | `tests/test_matriz_casos.py::test_una_definicion_con_una_prueba_inexistente_se_detecta` |
| CP-106 | Identificador, parámetros y cadena de tareas | correcto | 4 tareas en orden con catchup=False | cumplió lo esperado | pasa | 0.00 | `tests/test_dag_estatico.py::test_las_cuatro_tareas_tienen_los_nombres_y_el_orden_de_la_guia` |
| CP-107 | Dependencias lineales | correcto | bronze >> silver >> gold >> load | cumplió lo esperado | pasa | 0.00 | `tests/test_dag_estatico.py::test_las_dependencias_son_una_cadena_lineal` |
| CP-108 | El repositorio nunca se escribe | incorrecto | solo se escribe en la copia de trabajo | cumplió lo esperado | pasa | 0.01 | `tests/test_dag_estatico.py::test_nunca_se_escribe_ni_se_borra_nada_fuera_de_la_copia_de_trabajo` |
| CP-109 | Fallo inducido antes de producir salidas | incorrecto | las cuatro tareas lo implementan | cumplió lo esperado | pasa | 0.00 | `tests/test_dag_estatico.py::test_el_fallo_inducido_esta_en_las_cuatro_tareas_antes_de_producir_salidas` |
| CP-110 | Sin secretos ni rutas de Windows | incorrecto | el escáner no halla nada | cumplió lo esperado | pasa | 0.01 | `tests/test_dag_estatico.py::test_el_dag_no_lleva_rutas_de_windows_ni_contrasenas_literales` |
| CP-111 | Requisitos con las versiones del entorno | correcto | versiones idénticas | cumplió lo esperado | pasa | 0.03 | `tests/test_dag_estatico.py::test_los_requisitos_de_airflow_tienen_las_mismas_versiones_que_el_venv` |
| CP-112 | Copia del DAG con el hash registrado | límite | sha256 igual | cumplió lo esperado | pasa | 0.00 | `tests/test_dag_estatico.py::test_la_copia_versionada_del_dag_coincide_con_el_hash_registrado` |
| CP-113 | Fallo inducido dentro del bloque que elimina la copia de trabajo | incorrecto | la copia se elimina también al fallar (DEF-013) | cumplió lo esperado | pasa | 0.00 | `tests/test_dag_estatico.py::test_el_fallo_inducido_de_las_tareas_con_copia_ocurre_dentro_del_try_que_elimina_la_copia` |
| CP-114 | Las etapas terminan sin error en una copia | correcto | código de salida 0 | cumplió lo esperado | pasa | 2.87 | `tests/test_pipeline_reproducible.py::test_las_etapas_terminan_sin_error` |
| CP-115 | Los nueve archivos de la línea base se reproducen | correcto | sha256 idénticos a los versionados | cumplió lo esperado | pasa | 0.14 | `tests/test_pipeline_reproducible.py::test_los_nueve_archivos_de_la_linea_base_se_reproducen_byte_a_byte` |
| CP-116 | Regenerar sobre salidas existentes | límite | no cambia nada | cumplió lo esperado | pasa | 0.01 | `tests/test_pipeline_reproducible.py::test_regenerar_no_cambia_lo_que_ya_estaba_versionado_en_la_copia` |
| CP-117 | Dependencias de otra versión (pandas) | incorrecto | la prueba falla y nombra los archivos distintos | cumplió lo esperado | pasa | 0.00 | `tests/test_dag_estatico.py::test_pandas_es_la_version_con_la_que_se_generaron_los_archivos_de_la_linea_base` |
| CP-118 | El repositorio no se toca | correcto | las nueve salidas conservan su sha256 | cumplió lo esperado | pasa | 0.02 | `tests/test_pipeline_reproducible.py::test_el_repositorio_no_se_toco` |

Casos sin resultado: 0.

## Métricas de validación del análisis (recálculo independiente)

K1 por estrato recalculado con SQL sobre `gold_final.csv` y con una fórmula de Wilson propia (no la de `src/`), frente a `kpis_gold.csv`.

| Estrato | Severas | Con datos | Tasa recalculada | Numerador en kpis_gold | Denominador en kpis_gold | Mayor diferencia (tasa e intervalo) |
|---|---|---|---|---|---|---|
| 1 | 20 | 302 | 0.066225 | 20.0 | 302.0 | 3.65e-13 |
| 2 | 3 | 92 | 0.032609 | 3.0 | 92.0 | 3.77e-13 |
| 3 | 74 | 1173 | 0.063086 | 74.0 | 1173.0 | 4.59e-13 |
| 4 | 145 | 2095 | 0.069212 | 145.0 | 2095.0 | 4.51e-13 |
| 5 | 53 | 1031 | 0.051406 | 53.0 | 1031.0 | 4.82e-13 |
| 6 | 0 | 11 | 0.000000 | 0.0 | 11.0 | 1.86e-13 |

- Mayor diferencia absoluta entre lo recalculado y lo publicado: 4.82e-13.
- Cobertura de la llave en el reporte de calidad: 0.9988; confianza de la llave: alta.

## Cobertura de líneas por módulo

Medida con `coverage` sobre `src/` y `scripts/` durante la misma ejecución, sin umbrales impuestos. Total: 66.2 % de 3383 líneas.

| Módulo | Líneas | Sin ejecutar | Cobertura | Motivo si es menor de 70 % |
|---|---|---|---|---|
| `scripts/cargar_mysql.py` | 40 | 8 | 80 % |  |
| `scripts/escanear_secretos.py` | 200 | 11 | 94 % |  |
| `scripts/evidencias/saneamiento.py` | 54 | 1 | 98 % |  |
| `scripts/informe_pruebas.py` | 165 | 38 | 77 % |  |
| `scripts/make_catalogo_fuentes.py` | 113 | 6 | 95 % |  |
| `scripts/make_dist.py` | 81 | 8 | 90 % |  |
| `scripts/make_matriz_casos.py` | 83 | 12 | 86 % |  |
| `scripts/make_modelo_datos.py` | 126 | 58 | 54 % | genera el diccionario y el diagrama; el diccionario se comprueba contra el esquema y el dibujo con matplotlib no se prueba |
| `scripts/make_readme.py` | 184 | 184 | 0 % | generador del README: su salida se comprueba con test_readme_cifras (se ejecuta fuera de pytest) |
| `scripts/mysql/benchmark_lotes.py` | 118 | 75 | 36 % | necesita MySQL en vivo; su evidencia es EV-030 y se prueban las reglas de elección y el percentil |
| `scripts/mysql/configurar_mysql.py` | 283 | 36 | 87 % |  |
| `scripts/mysql/respaldar_restaurar.py` | 183 | 40 | 78 % |  |
| `scripts/mysql/verificar_mysql.py` | 208 | 151 | 27 % | batería contra MySQL en vivo; su evidencia es EV-028 y se prueban su operación solo sobre la base de prueba y el fallo sin servidor |
| `src/api/app.py` | 109 | 2 | 98 % |  |
| `src/api/errores.py` | 25 | 0 | 100 % |  |
| `src/api/esquemas.py` | 108 | 0 | 100 % |  |
| `src/api/repositorio.py` | 185 | 14 | 92 % |  |
| `src/common.py` | 61 | 22 | 64 % | descarga y escritura de Bronze (save_bronze): Bronze es inmutable y las pruebas no tocan la red ni data/bronze |
| `src/extract/extract_api.py` | 108 | 108 | 0 % | descarga de la capa ArcGIS y de los polígonos: requiere red y crearía snapshots; las pruebas verifican lo ya descargado con el manifiesto |
| `src/extract/extract_excel.py` | 57 | 39 | 32 % | descarga del CSV de estrato: requiere red; se prueba la lectura y limpieza con el archivo ya descargado |
| `src/load/conciliacion.py` | 84 | 3 | 96 % |  |
| `src/load/conexion.py` | 43 | 26 | 40 % | la rama de conexión real a MySQL se ejercita en vivo (EV-028); las pruebas cubren SQLite y los mensajes de error |
| `src/load/esquema.py` | 76 | 2 | 97 % |  |
| `src/load/load_database.py` | 31 | 0 | 100 % |  |
| `src/load/relacional.py` | 164 | 4 | 98 % |  |
| `src/logger.py` | 48 | 0 | 100 % |  |
| `src/transform/build_gold.py` | 168 | 84 | 50 % | cálculo de Gold y de sensibilidades: se ejecuta en un subproceso (test_pipeline_reproducible) que pytest-coverage no contabiliza; sus funciones estadísticas sí se prueban en proceso |
| `src/transform/clean_api.py` | 84 | 84 | 0 % | limpieza de construcciones: se ejecuta en un subproceso (test_pipeline_reproducible) y se comprueba su salida byte a byte |
| `src/transform/clean_excel.py` | 51 | 2 | 96 % |  |
| `src/transform/integrate.py` | 126 | 126 | 0 % | JOIN y reporte de calidad: se ejecuta en un subproceso (test_pipeline_reproducible) y se comprueba su salida byte a byte |
| `src/transform/keys.py` | 17 | 0 | 100 % |  |

Salida real registrada por `scripts/informe_pruebas.py`; las rutas de la máquina no aparecen en este documento.
