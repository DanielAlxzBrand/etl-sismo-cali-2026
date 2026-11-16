"""Genera la matriz de casos de prueba (docs/validacion/matriz_casos_prueba.md y .csv) desde una definición única: función crítica -> casos CP-nnn -> prueba que los ejecuta.

Uso:  python scripts/make_matriz_casos.py [--verificar]
Los identificadores CP se asignan en orden de definición. `verificar_definicion()` comprueba que cada prueba citada existe en `tests/` y que cada función crítica tiene
al menos un caso correcto y uno incorrecto o límite (una prueba de pytest lo exige). Con --verificar no escribe: falla si los documentos no coinciden con la definición.
"""
import argparse
import ast
import csv
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SALIDA_MD = ROOT / "docs" / "validacion" / "matriz_casos_prueba.md"
SALIDA_CSV = ROOT / "docs" / "validacion" / "matriz_casos_prueba.csv"
C, I, L = "correcto", "incorrecto", "límite"
T = "tests/"

# (id, función crítica, módulos, [(caso, tipo, resultado esperado, archivo::prueba)])
FUNCIONES = [
    ("FC-01", "Extracción y verificación de Bronze (manifiesto con sha256)", "src/common.py, src/extract/", [
        ("El manifiesto existe y tiene líneas", C, "manifest.jsonl no vacío", "test_extract.py::test_manifiesto_existe_y_no_vacio"),
        ("Cada archivo existe y su sha256 coincide con el manifiesto", C, "8 de 8 coinciden", "test_extract.py::test_archivos_existen_y_sha256_coincide"),
        ("Las páginas suman el conteo oficial de la capa", C, "5.146 filas en 3 páginas", "test_extract.py::test_paginas_suman_el_conteo_oficial"),
        ("El conteo de filas del manifiesto coincide con el contenido", L, "filas del manifiesto = filas leídas", "test_extract.py::test_rows_coherente_con_el_contenido"),
        ("El manifiesto no repite rutas", I, "ninguna ruta duplicada", "test_extract.py::test_sin_paths_duplicados"),
        ("El manifiesto no guarda tokens en sus parámetros", I, "ningún campo sensible", "test_extract.py::test_campos_del_manifiesto_sin_tokens")]),
    ("FC-02", "Limpieza de construcciones (Silver)", "src/transform/clean_api.py, src/transform/integrate.py", [
        ("Tipos esperados en Silver", C, "columnas con el tipo declarado", "test_transform.py::test_tipos_esperados_silver"),
        ("Sin duplicados por llave natural", C, "OBJECTID único", "test_transform.py::test_cero_duplicados_por_llave_natural"),
        ("Fechas en zona horaria de Bogotá", C, "zona America/Bogota", "test_transform.py::test_zona_horaria_bogota"),
        ("Reporte de calidad con todos los campos", C, "campos presentes", "test_quality.py::test_reporte_con_todos_los_campos"),
        ("Gold con el mínimo de filas y sin duplicados", L, "al menos el umbral configurado", "test_quality.py::test_gold_minimo_de_filas_y_sin_duplicados")]),
    ("FC-03", "Limpieza del estrato por barrio", "src/transform/clean_excel.py", [
        ("El CSV de estrato se lee como UTF-8 y se limpia", C, "una fila por barrio con código único", "test_casos_limite.py::test_la_limpieza_del_estrato_acepta_una_sola_fila_real"),
        ("Revisión de códigos de barrio por categoría", C, "las categorías suman las construcciones sin nombre validado", "test_empaquetado_y_revision.py::test_categorias_de_la_revision_suman_las_construcciones_sin_nombre_validado"),
        ("Revisión de códigos con los casos pedidos", I, "cada caso cae en su categoría", "test_empaquetado_y_revision.py::test_revision_de_codigos_cubre_los_casos_pedidos"),
        ("Una sola fila de estrato", L, "se limpia sin error", "test_casos_limite.py::test_la_limpieza_del_estrato_acepta_una_sola_fila_real")]),
    ("FC-04", "Llave del JOIN y cobertura", "src/transform/keys.py, src/transform/integrate.py", [
        ("Normalización de nombres", C, "texto normalizado", "test_transform.py::test_normalize_key"),
        ("Código de barrio = comuna por 100 más barrio", C, "código esperado", "test_transform.py::test_codigo_barrio"),
        ("La cobertura del JOIN supera el umbral", C, "cobertura >= 0,80", "test_quality.py::test_cobertura_join_supera_umbral"),
        ("Entradas mínimas para las llaves", L, "cadena vacía y un carácter se aceptan", "test_casos_limite.py::test_las_llaves_aceptan_entradas_minimas"),
        ("Revisión de llave coincide con Silver", C, "mismos códigos y conteos", "test_api.py::test_revision_de_llave_coincide_con_silver")]),
    ("FC-05", "Intervalos de confianza y KPI (Wilson, Newcombe, Mantel-Haenszel)", "src/transform/build_gold.py", [
        ("Vectores de Wilson", C, "límites con 4 decimales", "test_kpis.py::test_wilson_vectores"),
        ("Vector de Newcombe", C, "diferencia e intervalo", "test_kpis.py::test_newcombe_vector"),
        ("Mantel-Haenszel con una sola comuna", L, "razón calculada solo con la comuna disponible", "test_kpis.py::test_mantel_haenszel_una_comuna"),
        ("Construcciones sin datos satelitales no entran en Mantel-Haenszel", I, "se excluyen del cálculo", "test_kpis.py::test_regresion_defecto_mh_sin_datos_no_entra_en_mh"),
        ("Consistencia entre K1, K5 y K6 y rangos", C, "valores en [0, 1] y sumas consistentes", "test_kpis.py::test_consistencia_k1_k6_k5_y_rangos"),
        ("K1 recalculado desde Gold", C, "igual a kpis_gold.csv", "test_kpis.py::test_k1_recalculado_desde_gold"),
        ("Wilson con un solo registro", L, "intervalo válido dentro de [0, 1]", "test_casos_limite.py::test_wilson_con_un_solo_registro_da_un_intervalo_valido"),
        ("Wilson sin registros", L, "nan en lugar de dividir por cero", "test_casos_limite.py::test_wilson_sin_registros_da_nan_en_lugar_de_dividir_por_cero"),
        ("Newcombe con un registro por grupo", L, "diferencia observada dentro del intervalo", "test_casos_limite.py::test_newcombe_con_un_registro_por_grupo_incluye_la_diferencia_observada"),
        ("Mantel-Haenszel con un registro", L, "razón vacía y comuna excluida", "test_casos_limite.py::test_mantel_haenszel_con_un_registro_no_inventa_una_razon"),
        ("Indicadores con un solo registro", L, "grupos vacíos con denominador 0", "test_casos_limite.py::test_los_indicadores_con_un_solo_registro_se_calculan_y_los_grupos_vacios_quedan_en_cero"),
        ("KPI presentes y en rango", C, "K1 a K6 con valores válidos", "test_quality.py::test_kpis_presentes_y_en_rango")]),
    ("FC-06", "Sensibilidades S0 a S5", "src/transform/build_gold.py, src/api/", [
        ("Sensibilidades iguales al CSV", C, "filas idénticas", "test_api.py::test_kpis_y_sensibilidad_son_iguales_a_los_csv"),
        ("Escenario no válido en la API", I, "422 con el JSON de error uniforme", "test_api.py::test_parametros_invalidos_dan_422_con_el_json_uniforme"),
        ("La ruta de sensibilidades va antes que /kpis/{id}", L, "no se confunde con un id de KPI", "test_api.py::test_orden_de_rutas_sensibilidad_antes_que_kpi_id")]),
    ("FC-07", "Carga a SQLite", "src/load/load_database.py", [
        ("Contenido igual al de la base versionada", C, "4 tablas con el mismo contenido", "test_carga_sqlite.py::test_el_contenido_cargado_es_igual_al_de_la_base_versionada"),
        ("Cargar dos veces", L, "mismas tablas sin duplicar filas", "test_carga_sqlite.py::test_cargar_dos_veces_reemplaza_las_tablas_sin_duplicar_filas"),
        ("Una sola fila por tabla", L, "una fila en cada tabla", "test_carga_sqlite.py::test_con_una_sola_fila_por_tabla_se_cargan_cuatro_filas"),
        ("CSV de entrada ausente", I, "FileNotFoundError y conexión cerrada", "test_carga_sqlite.py::test_un_csv_ausente_falla_y_no_deja_la_conexion_abierta"),
        ("La carga no toca el repositorio", C, "la base versionada conserva su hash", "test_carga_sqlite.py::test_la_carga_no_modifica_el_repositorio")]),
    ("FC-08", "Carga relacional con historial (conversión, clave de corrida, transacción)", "src/load/relacional.py, src/load/esquema.py", [
        ("Conversión correcta de cada tipo", C, "valores convertidos sin pérdida", "test_carga_relacional.py::test_conversion_correcta"),
        ("Valores que perderían información", I, "ConversionError con mensaje claro", "test_carga_relacional.py::test_conversion_que_perderia_informacion_falla"),
        ("Carga completa", C, "346, 5.146, 23 y 107 filas", "test_carga_relacional.py::test_la_carga_completa_concilia_al_cien_por_ciento"),
        ("Repetir la carga", L, "responde «ya cargada» y no escribe", "test_carga_relacional.py::test_la_carga_repetida_es_idempotente"),
        ("Clave de corrida determinista y sensible a la entrada", C, "misma entrada, misma clave", "test_carga_relacional.py::test_la_clave_de_corrida_es_determinista_y_sensible_a_cada_entrada"),
        ("Entrada alterada", C, "corrida nueva y la anterior intacta", "test_carga_relacional.py::test_una_entrada_alterada_crea_una_corrida_nueva_y_conserva_la_anterior"),
        ("Fallo a mitad de carga", I, "reversión completa", "test_carga_relacional.py::test_un_fallo_a_mitad_de_la_carga_revierte_todo"),
        ("Valor ilegible", I, "falla antes de escribir nada", "test_carga_relacional.py::test_un_valor_ilegible_falla_antes_de_escribir_nada"),
        ("Una sola fila por tabla", L, "carga y concilia al 100 %", "test_casos_limite.py::test_la_carga_con_una_sola_fila_por_tabla_concilia_al_cien_por_ciento"),
        ("Entrada vacía", L, "se rechaza sin crear nada", "test_casos_limite.py::test_una_entrada_vacia_se_rechaza_sin_crear_nada_en_la_base"),
        ("Archivo de entrada ausente", I, "FileNotFoundError sin tocar la base", "test_casos_limite.py::test_un_archivo_de_entrada_ausente_se_rechaza_sin_tocar_la_base"),
        ("La carga no escribe en data/", C, "data/ conserva sus sha256", "test_carga_relacional.py::test_la_carga_no_escribe_en_data")]),
    ("FC-09", "Integridad referencial y conciliación", "src/load/esquema.py, src/load/conciliacion.py, src/load/sql/", [
        ("Esquemas de MySQL y SQLite con las mismas columnas", C, "paridad sin diferencias", "test_carga_relacional.py::test_los_dos_esquemas_declaran_las_mismas_tablas_y_columnas_en_el_mismo_orden"),
        ("Sin filas huérfanas", C, "0 en cada relación", "test_carga_relacional.py::test_la_integridad_referencial_no_deja_huerfanos"),
        ("Construcciones sin cruce de barrio", L, "se conservan con el enlace nulo", "test_carga_relacional.py::test_los_huerfanos_de_estrato_se_conservan_con_el_enlace_nulo"),
        ("Violaciones de integridad", I, "diez violaciones rechazadas", "test_carga_relacional.py::test_las_violaciones_de_integridad_se_rechazan"),
        ("Borrar una corrida con datos", I, "rechazado por RESTRICT", "test_carga_relacional.py::test_no_se_puede_borrar_una_corrida_con_datos"),
        ("La conciliación detecta un valor alterado", I, "1 diferencia en la columna alterada", "test_carga_relacional.py::test_la_conciliacion_detecta_un_valor_alterado")]),
    ("FC-10", "Configuración de MySQL y credenciales del proyecto", "scripts/mysql/configurar_mysql.py", [
        ("Primera configuración", C, "bases y usuario creados; .env con nombres", "test_configurar_mysql.py::test_primera_configuracion_crea_bases_usuario_y_escribe_solo_nombres"),
        ("La contraseña del administrador no se guarda", C, "no llega a .env, SQL ni registro", "test_configurar_mysql.py::test_la_contrasena_del_administrador_nunca_se_guarda_ni_llega_a_sql"),
        ("Privilegios incorrectos", I, "se rechazan y .env no cambia", "test_configurar_mysql.py::test_privilegios_incorrectos_se_rechazan_y_no_se_escribe_env"),
        ("Servidor anterior a 8.0", I, "se rechaza con mensaje claro", "test_configurar_mysql.py::test_servidor_antiguo_se_rechaza"),
        ("Repetir con credenciales válidas", L, "no cambia nada ni pide la contraseña", "test_configurar_mysql.py::test_con_credenciales_validas_no_cambia_nada_ni_pide_la_contrasena_del_administrador")]),
    ("FC-11", "Usuario de MySQL para Docker", "scripts/mysql/configurar_mysql.py", [
        ("Creación con permisos mínimos sobre la base real", C, "solo `sismo_cali`, sin globales ni GRANT OPTION", "test_usuario_docker.py::test_crea_el_usuario_con_permisos_solo_sobre_la_base_real_y_escribe_nombres"),
        ("Orígenes válidos", C, "IP privada, nombre exacto o red privada", "test_usuario_docker.py::test_origenes_validos"),
        ("Orígenes con comodines o públicos", I, "rechazados", "test_usuario_docker.py::test_origenes_rechazados"),
        ("Permisos distintos de los esperados", I, "se rechazan y .env no cambia", "test_usuario_docker.py::test_permisos_distintos_de_los_esperados_se_rechazan"),
        ("Repetir con el .env completo", L, "no pide contraseña y no cambia", "test_usuario_docker.py::test_es_idempotente_y_no_pide_la_contrasena_si_el_env_esta_completo")]),
    ("FC-12", "Respaldo y restauración", "scripts/mysql/respaldar_restaurar.py", [
        ("Respaldo con manifiesto", C, "un CSV por tabla y manifiesto sha256", "test_respaldo_y_medicion.py::test_el_respaldo_escribe_un_csv_por_tabla_con_manifiesto"),
        ("Restauración conciliada", C, "huellas iguales en 7 tablas", "test_respaldo_y_medicion.py::test_restaurar_reproduce_cada_tabla_con_la_misma_huella"),
        ("Respaldo alterado", I, "se rechaza antes de restaurar", "test_respaldo_y_medicion.py::test_un_respaldo_alterado_se_rechaza_antes_de_restaurar"),
        ("Destino con datos", L, "no se restaura encima", "test_respaldo_y_medicion.py::test_no_se_restaura_encima_de_datos")]),
    ("FC-13", "API de solo lectura", "src/api/", [
        ("Cada endpoint responde 200 con su estructura", C, "11 rutas válidas", "test_api.py::test_cada_endpoint_responde_200_con_la_estructura_esperada"),
        ("Parámetros inválidos", I, "422 con JSON uniforme", "test_api.py::test_parametros_invalidos_dan_422_con_el_json_uniforme"),
        ("Identificadores y rutas inexistentes", I, "404 uniforme", "test_api.py::test_ids_inexistentes_dan_404_y_rutas_desconocidas_tambien"),
        ("Límites de paginación", L, "mínimo, máximo y offset respetados", "test_api.py::test_limites_de_paginacion_y_offset"),
        ("Extremos de paginación", L, "una fila, página final y página vacía", "test_casos_limite.py::test_la_pagina_de_un_solo_registro_y_la_pagina_final"),
        ("Inyección en filtros", I, "rechazada", "test_api.py::test_la_inyeccion_en_comuna_y_estrato_se_rechaza"),
        ("Solo GET", I, "los demás métodos dan 405", "test_api.py::test_solo_existen_rutas_get_y_los_demas_metodos_dan_405"),
        ("Base ausente", I, "503 y /health degradado", "test_api.py::test_base_ausente_da_503_y_health_degradado"),
        ("Misma respuesta desde el almacén relacional", C, "17 rutas idénticas entre almacenes", "test_carga_relacional.py::test_la_api_sirve_lo_mismo_desde_el_almacen_relacional_que_desde_sqlite"),
        ("No escribe en data/ ni en la base", C, "hashes idénticos tras consultar todo", "test_api.py::test_consultar_todos_los_endpoints_no_escribe_en_data_ni_en_la_base")]),
    ("FC-14", "Catálogo de fuentes y metadatos", "scripts/make_catalogo_fuentes.py, src/api/", [
        ("El catálogo coincide con el manifiesto", C, "mismas huellas y filas", "test_catalogo.py::test_el_catalogo_coincide_con_el_manifiesto"),
        ("Cubre todas las fuentes del manifiesto", C, "ninguna fuente sin ficha", "test_catalogo.py::test_el_catalogo_cubre_todas_las_fuentes_del_manifiesto"),
        ("Dos generaciones son idénticas", L, "salida determinista", "test_catalogo.py::test_dos_generaciones_son_identicas"),
        ("El diccionario de Gold describe todas las columnas", I, "ninguna columna sin descripción", "test_catalogo.py::test_el_diccionario_de_gold_describe_todas_las_columnas")]),
    ("FC-15", "Secretos y credenciales", "scripts/escanear_secretos.py, src/logger.py", [
        ("Sin hallazgos en el árbol", C, "0 hallazgos", "test_secretos.py::test_sin_hallazgos_en_el_arbol_de_trabajo"),
        ("Un secreto sembrado por tipo", I, "se detecta cada uno", "test_secretos.py::test_detecta_un_secreto_sembrado_de_cada_tipo"),
        ("Huellas, rutas y URLs largas", L, "no se marcan como secretos", "test_secretos.py::test_no_marca_huellas_ni_rutas_ni_urls_largas"),
        ("Contraseña sembrada con canario", I, "se detecta sin imprimirla", "test_configurar_mysql.py::test_el_canario_detecta_la_contrasena_sembrada_sin_imprimirla"),
        ("Contraseña de un .env extra", I, "se detecta sin imprimirla", "test_canario_extra.py::test_detecta_la_contrasena_del_env_extra_en_el_arbol_sin_imprimirla"),
        ("Enmascarado del registro", C, "tokens y cabeceras reemplazados por ***", "test_logger.py::test_enmascara_cabeceras_y_tokens")]),
    ("FC-16", "Empaquetado (make_dist)", "scripts/make_dist.py", [
        ("Lo permitido entra y el zip se verifica", C, "zip sin entradas prohibidas", "test_dist.py::test_lo_permitido_entra_y_el_zip_pasa_la_verificacion"),
        ("Entornos virtuales y carpetas ocultas", I, "no entran", "test_dist.py::test_entorno_sin_pyvenv_cfg_no_entra_al_zip"),
        ("dags y orquestacion presentes o ausentes", L, "entran si existen y no fallan si faltan", "test_dist.py::test_orquestacion_entra_cuando_existe_y_no_falla_cuando_no_existe"),
        ("El repositorio real", C, "solo primer nivel permitido, con dags y orquestacion", "test_dist.py::test_el_repo_real_empaqueta_el_dag_y_la_carpeta_de_orquestacion")]),
    ("FC-17", "Documentación, cifras y evidencias", "README.md, docs/, scripts/evidencias/", [
        ("Cifras del análisis iguales a las salidas", C, "K5, K2 y Gold coinciden", "test_resultados_cifras.py::test_cifras_de_gold_bronze_y_silver_en_resultados"),
        ("Conteo de pruebas del README", C, "igual a la recolección", "test_readme_cifras.py::test_numero_de_pruebas_en_readme"),
        ("Estados de los 30 ítems", C, "completos y con componentes válidos", "test_estrategia.py::test_los_30_items_del_checklist_estan_completos_y_con_componentes_de_la_lista"),
        ("Alteraciones de los 30 ítems", I, "cada alteración se detecta", "test_estrategia.py::test_negativas_de_los_30_items"),
        ("Alteraciones de los criterios del MVP", I, "cada alteración se detecta", "test_estrategia.py::test_negativas_de_los_criterios_del_mvp"),
        ("Evidencias saneadas", C, "sin rutas ni usuario", "test_evidencias.py::test_las_evidencias_guardadas_estan_saneadas"),
        ("Recálculo independiente de K1", C, "diferencia máxima menor de 1e-9 frente a kpis_gold.csv", "test_informe_pruebas.py::test_el_recalculo_independiente_coincide_con_los_kpi_publicados"),
        ("Informe con esperado y obtenido, sin rutas de la máquina", C, "caso fallido marcado y sin rutas", "test_informe_pruebas.py::test_el_informe_se_genera_con_esperado_obtenido_y_sin_rutas_de_la_maquina"),
        ("Una definición de la matriz con una prueba inexistente", I, "se detecta", "test_matriz_casos.py::test_una_definicion_con_una_prueba_inexistente_se_detecta")]),
    ("FC-18", "Orquestación (DAG, imagen y requisitos)", "dags/, orquestacion/", [
        ("Identificador, parámetros y cadena de tareas", C, "4 tareas en orden con catchup=False", "test_dag_estatico.py::test_las_cuatro_tareas_tienen_los_nombres_y_el_orden_de_la_guia"),
        ("Dependencias lineales", C, "bronze >> silver >> gold >> load", "test_dag_estatico.py::test_las_dependencias_son_una_cadena_lineal"),
        ("El repositorio nunca se escribe", I, "solo se escribe en la copia de trabajo", "test_dag_estatico.py::test_nunca_se_escribe_ni_se_borra_nada_fuera_de_la_copia_de_trabajo"),
        ("Fallo inducido antes de producir salidas", I, "las cuatro tareas lo implementan", "test_dag_estatico.py::test_el_fallo_inducido_esta_en_las_cuatro_tareas_antes_de_producir_salidas"),
        ("Sin secretos ni rutas de Windows", I, "el escáner no halla nada", "test_dag_estatico.py::test_el_dag_no_lleva_rutas_de_windows_ni_contrasenas_literales"),
        ("Requisitos con las versiones del entorno", C, "versiones idénticas", "test_dag_estatico.py::test_los_requisitos_de_airflow_tienen_las_mismas_versiones_que_el_venv"),
        ("Copia del DAG con el hash registrado", L, "sha256 igual", "test_dag_estatico.py::test_la_copia_versionada_del_dag_coincide_con_el_hash_registrado"),
        ("Fallo inducido dentro del bloque que elimina la copia de trabajo", I, "la copia se elimina también al fallar (DEF-013)", "test_dag_estatico.py::test_el_fallo_inducido_de_las_tareas_con_copia_ocurre_dentro_del_try_que_elimina_la_copia")]),
    ("FC-19", "Reproducibilidad del pipeline (transformar y gold)", "src/transform/, src/load/load_database.py", [
        ("Las etapas terminan sin error en una copia", C, "código de salida 0", "test_pipeline_reproducible.py::test_las_etapas_terminan_sin_error"),
        ("Los nueve archivos de la línea base se reproducen", C, "sha256 idénticos a los versionados", "test_pipeline_reproducible.py::test_los_nueve_archivos_de_la_linea_base_se_reproducen_byte_a_byte"),
        ("Regenerar sobre salidas existentes", L, "no cambia nada", "test_pipeline_reproducible.py::test_regenerar_no_cambia_lo_que_ya_estaba_versionado_en_la_copia"),
        ("Dependencias de otra versión (pandas)", I, "la prueba falla y nombra los archivos distintos", "test_dag_estatico.py::test_pandas_es_la_version_con_la_que_se_generaron_los_archivos_de_la_linea_base"),
        ("El repositorio no se toca", C, "las nueve salidas conservan su sha256", "test_pipeline_reproducible.py::test_el_repositorio_no_se_toco")]),
    ("FC-20", "Cliente HTTP de la API (solo lectura)", "src/panel/cliente_api.py, src/panel/configuracion.py", [
        ("Respuesta correcta", C, "devuelve los datos", "test_panel_cliente.py::test_una_respuesta_correcta_devuelve_los_datos"),
        ("Solo GET y sin parámetros nulos", C, "una sola solicitud GET con los parámetros presentes", "test_panel_cliente.py::test_solo_usa_get_y_omite_los_parametros_nulos"),
        ("Cada estado HTTP de error", I, "error tipado con mensaje en español", "test_panel_cliente.py::test_cada_estado_http_se_traduce_a_un_error_tipado_en_espanol"),
        ("JSON mal formado", I, "respuesta inválida", "test_panel_cliente.py::test_json_mal_formado_es_respuesta_invalida"),
        ("Tiempo agotado", I, "error sin reintento", "test_panel_cliente.py::test_tiempo_agotado_no_se_reintenta"),
        ("API apagada", I, "un reintento y luego «api_apagada»", "test_panel_cliente.py::test_error_de_conexion_se_reintenta_una_vez_y_luego_dice_api_apagada"),
        ("Reintentos en cero", L, "falla a la primera", "test_panel_cliente.py::test_sin_reintentos_configurados_falla_a_la_primera"),
        ("La caché no guarda fallos", L, "un fallo no se queda pegado", "test_panel_cliente.py::test_la_cache_no_guarda_los_fallos_y_si_guarda_los_aciertos"),
        ("Dirección no local", I, "se rechaza", "test_panel_cliente.py::test_se_rechazan_las_direcciones_no_locales_o_sin_http")]),
    ("FC-21", "Formato de cifras del panel", "src/panel/formato.py", [
        ("Miles, coma decimal y half-up", C, "1.173; 1.234.567,9; 0,13", "test_panel_formato_redaccion.py::test_numero_con_miles_coma_decimal_y_half_up"),
        ("Porcentajes", C, "6,62 %; 100,00 %", "test_panel_formato_redaccion.py::test_porcentaje"),
        ("Puntos porcentuales con signo", C, "+0,49 pp; −2,36 pp", "test_panel_formato_redaccion.py::test_puntos_porcentuales_con_signo"),
        ("Valores no numéricos", I, "raya", "test_panel_formato_redaccion.py::test_numero_sin_dato_devuelve_raya"),
        ("99,8445 redondea hacia arriba", L, "99,845 % y no 99,844 %", "test_panel_formato_redaccion.py::test_el_formateador_redondea_9984_45_hacia_arriba_y_no_hacia_abajo")]),
    ("FC-22", "Redacción de conclusiones", "src/panel/redaccion.py", [
        ("Intervalo que incluye 0", C, "no se detecta diferencia", "test_panel_formato_redaccion.py::test_intervalo_que_incluye_cero_usa_la_frase_de_no_deteccion"),
        ("Intervalo que no incluye 0", C, "descripción de la muestra sin causalidad", "test_panel_formato_redaccion.py::test_intervalo_que_no_incluye_cero_describe_la_muestra_sin_causalidad"),
        ("Muestra baja", L, "advertencia de fragilidad", "test_panel_formato_redaccion.py::test_muestra_baja_agrega_la_advertencia"),
        ("Sin intervalo", I, "no se redacta una conclusión", "test_panel_formato_redaccion.py::test_sin_intervalo_no_se_redacta_una_conclusion"),
        ("Estratos con muestra baja", L, "no se ordenan", "test_panel_formato_redaccion.py::test_estratos_con_muestra_baja_no_se_ordenan_y_se_informa_el_solapamiento"),
        ("Ninguna rama afirma causalidad", I, "sin cadenas prohibidas", "test_panel_formato_redaccion.py::test_ninguna_rama_afirma_causalidad_ni_que_el_estrato_no_influye")]),
    ("FC-23", "Páginas del panel (interfaz y lógica)", "src/panel/paginas/, src/panel/componentes.py, src/panel/app.py", [
        ("Cada página se renderiza con su título", C, "sin excepciones", "test_panel_paginas.py::test_cada_pagina_se_renderiza_sin_excepciones_y_con_titulo_y_pregunta"),
        ("Recuadro de alcance en cada página", C, "visible en las ocho", "test_panel_paginas.py::test_cada_pagina_muestra_el_recuadro_de_alcance"),
        ("Cadenas prohibidas", I, "ninguna página las contiene", "test_panel_paginas.py::test_ninguna_pagina_contiene_cadenas_prohibidas"),
        ("API completamente caída", I, "aviso claro y sin traza", "test_panel_paginas.py::test_si_toda_la_api_falla_cada_pagina_muestra_un_aviso_claro_y_nunca_una_traza"),
        ("Respuestas vacías", L, "la página no se rompe", "test_panel_paginas.py::test_con_respuestas_vacias_cada_pagina_no_se_rompe"),
        ("Falla solo la ruta de la página", I, "el resto sigue visible", "test_panel_paginas.py::test_si_falla_solo_la_ruta_de_la_pagina_el_resto_sigue_visible"),
        ("Página fuera de rango en construcciones", L, "mensaje de página sin filas", "test_panel_paginas.py::test_construcciones_pagina_filtra_en_la_api_y_ofrece_la_descarga"),
        ("Aplicación completa sin API", I, "navegación y aviso", "test_panel_paginas.py::test_la_aplicacion_arranca_con_la_navegacion_explicita_y_degrada_sin_api")]),
    ("FC-24", "Integración interfaz, API y almacenamiento", "src/panel/, src/api/", [
        ("K2 mostrado frente a Gold recalculado", C, "valores iguales", "test_panel_integracion.py::test_respuesta_muestra_k2_igual_a_kpis_gold_y_a_lo_recalculado_de_gold_final"),
        ("K5 con el formato de los documentos", C, "99,883 %; 99,845 %; 93,52 %", "test_panel_integracion.py::test_respuesta_muestra_k5_con_el_formato_de_los_documentos"),
        ("K1 y K6 frente a gold_final.csv", C, "conteos iguales", "test_panel_integracion.py::test_estratos_coincide_con_k1_y_con_los_conteos_de_gold_final"),
        ("Composición por comuna", C, "conteos iguales", "test_panel_integracion.py::test_la_composicion_por_comuna_y_grupo_coincide_con_gold_final"),
        ("Filtros de construcciones", L, "los totales filtrados coinciden con gold_final.csv", "test_panel_integracion.py::test_construcciones_pagina_y_filtros_coinciden_con_gold_final"),
        ("El panel no modifica data", I, "la fecha de modificación de data/gold no cambia", "test_panel_integracion.py::test_el_panel_no_modifica_data_al_consultar"),
        ("API real por HTTP", C, "once rutas responden", "test_panel_humo_extremo_a_extremo.py::test_el_cliente_real_lee_por_http_las_once_rutas_de_la_api"),
        ("Valores por HTTP real frente a las salidas", C, "iguales", "test_panel_humo_extremo_a_extremo.py::test_los_valores_por_http_real_coinciden_con_las_salidas"),
        ("Intento de escritura", I, "405 y data intacta", "test_panel_humo_extremo_a_extremo.py::test_el_panel_no_puede_escribir_y_data_no_cambia")]),
    ("FC-25", "Lanzador del panel", "scripts/panel/ejecutar_panel.py", [
        ("Comando de la API con SQLite", C, "el de la documentación", "test_panel_lanzador.py::test_el_comando_de_la_api_con_sqlite_es_el_de_la_documentacion"),
        ("Entorno de Streamlit", C, "sin cabeza, local y sin telemetría", "test_panel_lanzador.py::test_el_entorno_del_panel_es_local_sin_cabeza_y_sin_telemetria"),
        ("Credenciales de MySQL", I, "no pasan al panel", "test_panel_lanzador.py::test_el_entorno_del_panel_no_recibe_credenciales_de_mysql"),
        ("Puerto ocupado", L, "se elige otro libre", "test_panel_lanzador.py::test_un_puerto_ocupado_se_reemplaza_por_otro_libre"),
        ("La API no arranca", I, "código de salida 1", "test_panel_lanzador.py::test_si_la_api_no_responde_sale_con_1_y_no_arranca_el_panel"),
        ("El panel no arranca", I, "código de salida 2 y la API se cierra", "test_panel_lanzador.py::test_si_el_panel_no_responde_sale_con_2_y_cierra_la_api"),
        ("Ctrl+C", L, "cierra los dos procesos", "test_panel_lanzador.py::test_ctrl_c_cierra_los_dos_procesos_y_sale_con_0"),
        ("Excepción al arrancar", I, "el cierre ocurre en finally", "test_panel_lanzador.py::test_el_cierre_ocurre_aunque_el_arranque_lance_una_excepcion"),
        ("Duración acotada", L, "los procesos se cierran solos y sale con 0", "test_panel_lanzador.py::test_con_duracion_los_procesos_se_cierran_solos_y_sale_con_0")]),
    ("FC-26", "Aislamiento y solo lectura del panel", "src/panel/", [
        ("Imports permitidos", C, "solo logger y el propio panel", "test_panel_registro_y_aislamiento.py::test_los_unicos_imports_de_src_son_logger_y_el_propio_panel"),
        ("Sin almacenes ni credenciales", I, "no importa sqlite3, pymysql ni capas del pipeline", "test_panel_registro_y_aislamiento.py::test_el_panel_no_importa_almacenes_ni_capas_del_pipeline_ni_credenciales"),
        ("Solo GET", I, "ningún método de escritura", "test_panel_registro_y_aislamiento.py::test_solo_hay_consultas_get_y_ninguna_llamada_peligrosa"),
        ("Sin HTML inseguro ni recursos externos", I, "ninguno", "test_panel_registro_y_aislamiento.py::test_sin_html_inseguro_javascript_recursos_externos_ni_credenciales"),
        ("Ninguna cifra escrita a mano", L, "los textos no llevan dígitos propios", "test_panel_registro_y_aislamiento.py::test_ninguna_cifra_escrita_a_mano_en_los_textos_del_panel"),
        ("Rutas del registro en el OpenAPI", C, "cada ruta existe", "test_panel_registro_y_aislamiento.py::test_cada_ruta_de_los_componentes_y_las_paginas_existe_en_el_openapi_de_la_api"),
        ("Campos del registro en las salidas", C, "cada campo existe en su archivo", "test_panel_registro_y_aislamiento.py::test_cada_campo_de_los_componentes_existe_en_el_archivo_de_salida_que_declaran"),
        ("Sin carpetas ocultas de Streamlit", I, "no existen", "test_panel_registro_y_aislamiento.py::test_no_hay_carpetas_ocultas_ni_pages_ni_streamlit_en_el_repositorio"),
        ("Contraste del texto sobre el fondo", C, "al menos 7 a 1", "test_panel_tema.py::test_el_texto_sobre_el_fondo_tiene_al_menos_7_a_1_y_sobre_el_fondo_secundario_tambien"),
        ("Contraste de los colores de los gráficos", L, "al menos 3 a 1 sobre el fondo", "test_panel_tema.py::test_los_colores_de_los_graficos_tienen_al_menos_3_a_1_sobre_el_fondo"),
        ("Un par de bajo contraste", I, "se detecta", "test_panel_tema.py::test_un_par_de_bajo_contraste_se_detecta")]),
    ("FC-27", "Decisiones y empaquetado del panel", "docs/DECISIONES.md, scripts/make_dist.py", [
        ("La cabecera nombra la siguiente decisión", C, "la última más uno", "test_decisiones.py::test_la_cabecera_nombra_la_siguiente_decision_a_la_ultima_registrada"),
        ("Un desajuste de la cabecera", I, "se detecta", "test_decisiones.py::test_la_cabecera_detecta_un_desajuste"),
        ("El zip incluye el panel y su lanzador", C, "sin carpetas ocultas ni .env", "test_dist.py::test_el_repo_real_empaqueta_el_panel_y_su_lanzador_sin_carpetas_ocultas_ni_credenciales"),
        ("Carpeta de configuración de Streamlit", I, "no entra al zip", "test_dist.py::test_una_carpeta_de_configuracion_de_streamlit_o_sus_credenciales_no_entran_al_zip")]),
]


def casos():
    """[(CP, FC, función, caso, tipo, esperado, nodeid)] con identificadores asignados en orden."""
    salida, n = [], 0
    for fc, nombre, _, lista in FUNCIONES:
        for caso, tipo, esperado, prueba in lista:
            n += 1
            salida.append((f"CP-{n:03d}", fc, nombre, caso, tipo, esperado, T + prueba))
    return salida


def pruebas_existentes():
    """{archivo: {nombres de pruebas de primer nivel}} leído con ast (no ejecuta nada)."""
    salida = {}
    for p in sorted((ROOT / "tests").glob("test_*.py")):
        arbol = ast.parse(p.read_text(encoding="utf-8"))
        salida[f"tests/{p.name}"] = {f.name for f in arbol.body if isinstance(f, ast.FunctionDef) and f.name.startswith("test_")}
    return salida


def verificar_definicion():
    """Errores de la definición: pruebas inexistentes, funciones sin caso correcto o sin caso incorrecto o límite, identificadores repetidos."""
    existentes, errores = pruebas_existentes(), []
    for cp, fc, _, caso, tipo, _, nodeid in casos():
        archivo, _, prueba = nodeid.partition("::")
        if prueba not in existentes.get(archivo, set()):
            errores.append(f"{cp}: la prueba {nodeid} no existe")
        if tipo not in (C, I, L):
            errores.append(f"{cp}: tipo desconocido {tipo}")
    for fc, nombre, _, lista in FUNCIONES:
        tipos = {t for _, t, _, _ in lista}
        if C not in tipos:
            errores.append(f"{fc}: sin caso correcto")
        if not tipos & {I, L}:
            errores.append(f"{fc}: sin caso incorrecto ni límite")
    ids = [c[0] for c in casos()]
    if len(ids) != len(set(ids)):
        errores.append("identificadores CP repetidos")
    return errores


def markdown():
    existentes = pruebas_existentes()
    total_pruebas = sum(len(v) for v in existentes.values())
    citadas = {c[6] for c in casos()}
    lista = casos()
    L_ = ["# Matriz de casos de prueba por función crítica", "",
          "Este documento se genera con `scripts/make_matriz_casos.py` desde una única definición; no se edita a mano. Cada caso lleva un identificador **CP-nnn**, su tipo "
          "(correcto, incorrecto o límite), el resultado esperado y la prueba de `pytest` que lo ejecuta. El resultado obtenido de cada prueba está en [informe_pruebas.md](informe_pruebas.md).", "",
          f"- **Funciones críticas:** {len(FUNCIONES)}. **Casos:** {len(lista)} ({sum(1 for c in lista if c[4] == C)} correctos, {sum(1 for c in lista if c[4] == I)} incorrectos y {sum(1 for c in lista if c[4] == L)} límite).",
          f"- **Pruebas de primer nivel en `tests/`:** {total_pruebas}; {len({c[6] for c in lista})} de ellas están vinculadas a un caso (otras pruebas parametrizadas o de apoyo cubren variantes de los mismos casos).",
          "- **Regla:** cada función crítica tiene al menos un caso correcto y uno incorrecto o límite; una prueba lo comprueba y comprueba que cada prueba citada exista.", ""]
    for fc, nombre, modulos, _ in FUNCIONES:
        L_ += [f"## {fc} · {nombre}", "", f"Módulos: `{modulos}`", "", "| CP | Caso | Tipo | Resultado esperado | Prueba |", "|---|---|---|---|---|"]
        L_ += [f"| {c[0]} | {c[3]} | {c[4]} | {c[5]} | `{c[6]}` |" for c in lista if c[1] == fc]
        L_.append("")
    return "\n".join(L_).rstrip() + "\n"


def csv_texto():
    b = io.StringIO()
    w = csv.writer(b, lineterminator="\n")
    w.writerow(["cp", "funcion_critica", "nombre", "caso", "tipo", "resultado_esperado", "prueba"])
    w.writerows(casos())
    return b.getvalue()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--verificar", action="store_true")
    a = ap.parse_args(argv)
    errores = verificar_definicion()
    if errores:
        print("\n".join(errores))
        return 1
    md, cs = markdown(), csv_texto()
    if a.verificar:
        actual = [(SALIDA_MD.read_text(encoding="utf-8") if SALIDA_MD.exists() else "").replace("\r\n", "\n"), (SALIDA_CSV.read_text(encoding="utf-8") if SALIDA_CSV.exists() else "").replace("\r\n", "\n")]
        if actual != [md, cs]:
            print("la matriz de casos no coincide con su definición: ejecute scripts/make_matriz_casos.py")
            return 1
        print("la matriz de casos coincide con su definición")
        return 0
    SALIDA_MD.parent.mkdir(parents=True, exist_ok=True)
    SALIDA_MD.write_text(md, encoding="utf-8", newline="\n")
    SALIDA_CSV.write_text(cs, encoding="utf-8", newline="\n")
    print(f"escritos {SALIDA_MD.relative_to(ROOT)} y {SALIDA_CSV.relative_to(ROOT)} ({len(casos())} casos)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
