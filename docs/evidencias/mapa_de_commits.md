# Mapa de commits

Los commits desde el primero afectado cambiaron de hash cuando se quitó el pie de sus mensajes: el árbol, el autor y las fechas de cada uno son los mismos. Los documentos y las evidencias que citan un hash viejo se dejaron como estaban; esta tabla dice a qué commit corresponde hoy.

| Hash anterior | Hash nuevo | Asunto |
|---|---|---|
| abb1d78 | 8512a2b | Contraste de la paleta: el script calcula también los pies al 60 % del texto y el texto de los gráficos (F-12) |
| 4218cc4 | 50a7921 | Evidencias de después de los ajustes con el código final: capturas, tiempos y contrastes (EV-077 a EV-079) |
| 86df557 | cff5b63 | Guía de uso y arquitectura del panel: glosario, aviso de tabla ancha, barras horizontales y barra lateral automática |
| 47b3c75 | f52f211 | Reevaluación tras los ajustes, registro de fricciones y trazabilidad de cambios con decisión, razón, antes, después y verificación de F-01 a F-14 |
| a1e2ed1 | cc763c3 | Accesibilidad y respuesta del panel: contrastes con la paleta nueva, capturas en tres anchos y tiempos de dibujo con su variabilidad (EV-057 regenerada) |
| 5d7eb1e | bf91464 | Estado del ítem 3.3 y guía de evidencias con la reevaluación; el registrador del manifiesto incluye las evidencias de los ajustes (EV-073 a EV-082) |
| ddb88a8 | 333a0c0 | Evidencia EV-081: las 12 mutaciones de los ajustes del panel fueron detectadas |
| 4dea05d | f1f4b71 | Matriz de casos y README regenerados: 880 pruebas |
| 7e3047e | d9c42f8 | Cifras de los documentos de estado: 880 pruebas y cobertura de 72,9 % de 4.726 líneas |
| 93967ef | abd295e | Informe de pruebas definitivo (880 pruebas) y manifiesto con las evidencias de los ajustes del panel (EV-073 a EV-081) |
| 4d97674 | efe422f | Evidencia EV-082: 880 pruebas en un clon con el entorno nuevo de Python 3.13, registrada en el manifiesto |
| 3c1120b | d579fab | Usuario de MySQL de solo lectura (sismo_lectura) con SELECT sobre sismo_cali, canario nuevo en el escáner y nombres en .env.example |
| e3d80e6 | 62389e5 | Compose de phpMyAdmin 5.2.3 solo en 127.0.0.1, sin credenciales y con prueba estática |
| dd46144 | b4d605d | Compose de Airflow 3.3.2 adaptado y entregado en el repositorio: generador desde el oficial, puertos solo en 127.0.0.1, carpeta del proyecto y clave Fernet por variables, imágenes fijadas por resumen |
| 82503d4 | 8d252f0 | Script para preparar la carpeta de Airflow desde el proyecto: nombre de carpeta detectado, .env que no se sobrescribe, puerto y Docker comprobados, modo --verificar de solo lectura |
| eef5866 | e91f8e0 | Portabilidad de pruebas y scripts: codificación explícita en subprocesos y archivos, marcas que no caen en cp1252 y prueba que lo vigila |
| 4d5e3d8 | bfa7de5 | El zip incluye la carpeta servicios y evidencia EV-083: suite sin variables de UTF-8 en un clon con espacios y tildes, antes de corregir |
| cb66221 | de9db4d | Diagnóstico del entorno (preparar_entorno.py): Python 3.13, entorno virtual, requisitos, .env, MySQL, Docker y puertos, con instalación opcional que pide confirmación |
| 9269446 | 9f0f0b5 | Decisiones D91 a D94 y diferencias DF-13 a DF-17 del compose de Airflow adaptado |
| f070e82 | 19a7c0b | Guía de instalación (modo mínimo, modo completo y errores comunes), borrador de phpMyAdmin, secciones de Airflow desde el zip y enlaces desde el README |
| b109dd1 | a954f5f | Airflow desde el zip: la contraseña de Postgres y el secreto JWT salen del .env de Airflow en lugar de valores de ejemplo escritos (DF-18) |
| f959091 | 6557462 | Evidencia EV-087: Airflow construido y ejecutado desde el zip en una carpeta de otro nombre, con las cuatro tareas en éxito; tiempos medidos en las guías |
| 5c6d25a | dfb3fdd | Estado del ítem 5.4 y 7.1 y guía de evidencias: Airflow desde el zip (EV-087) y avance de la guía de instalación |
| 0ebea78 | 21b0673 | Evidencia EV-085: phpMyAdmin en vivo con la cuenta de solo lectura (tablas, claves foráneas, conteos iguales a Gold y escrituras rechazadas) y guía de phpMyAdmin con sus capturas |
| e579c19 | 9b96e7a | Estado de 4.1 y 4.2 y guía de evidencias: phpMyAdmin de solo lectura como evidencia adicional (EV-085) |
| 01754a2 | fa7cd0d | Evidencia EV-084 (suite sin variables de UTF-8 después de corregir), medidas de memoria y prueba de estructura de los servicios |
| 0352e46 | d1015b6 | El registrador del manifiesto incluye las evidencias de servicios (EV-083 a EV-089) y los tests citan sus evidencias vivas |
| 8bf5c7f | 0db9922 | Evidencia EV-088: las 23 mutaciones de los servicios locales fueron detectadas |
| 1c53bfd | 4d92c85 | Matriz de casos y README regenerados con las pruebas de servicios |
| 796c906 | d450b02 | Cifras de los documentos de estado: 964 pruebas y cobertura de 73,5 % de 5.279 líneas |
| 6c17fbd | 2b6b80d | Informe de pruebas definitivo (964 pruebas) y manifiesto con las evidencias de servicios |
| 0f31986 | 0c68228 | Evidencia EV-089: 964 pruebas en un clon con espacios y tildes y sin variables de UTF-8, registrada en el manifiesto |
| a326e30 | a7cd92b | Redacción: palabras neutras en lugar de «entregar» en los textos nuevos de servicios |
| 16f29f8 | de8e274 | Pruebas que usaban .git ahora usan un repositorio temporal con el .gitignore real y se omiten con motivo visible; el commit corto tolera la falta de git; omisiones esperadas del zip documentadas |
| dce77fb | a0ea75e | Textos sin la carpeta del equipo ni rutas fuera de la raíz: D13 y D24 (solo la mención), entorno, carga SQLite en TEMP y archivo de nombres del .env de Airflow con sus 7 variables; D95 |
| d8ebea7 | ddad633 | Prueba guardiana de independencia del repositorio: rutas, enlaces, textos y zip sin .git, con lista mínima de excepciones |
| 4925856 | 522b30a | Matriz de casos y README regenerados con las pruebas de independencia |
| 904c8e1 | 2498f60 | Cifras de los documentos de estado: 974 pruebas |
| 6145f63 | 164a55c | Evidencias EV-090 y EV-091: experimentos de independencia y mutaciones de la prueba guardiana; informe de pruebas definitivo (974) |
| bfcf01d | c2c3646 | Estados del checklist corregidos a la baja por falta de evidencia (1.5, 7.1, 7.2, 7.3, 7.5): vocabulario completo, conteo calculado por script, pruebas guardianas y D96 |
| 0e4c8e7 | a2c6d33 | Textos desactualizados: orquestacion/README con el compose adaptado, índice de docs con instalación, fichas de fricción y trazabilidad llenas, cifras de EV-072, py -3.13 en el generador y riesgo del volumen de Postgres como decisión del equipo |
| 5cda27b | 15cb31a | Scripts de verificación en vivo movidos a scripts/evidencias con su documentación y una prueba estática de su forma; última ejecución real de cada uno |
| 53b505b | 82eec16 | Cifras de la auditoría: 982 pruebas en el informe, la matriz, el README y los documentos de estado |
| bf7edd3 | f957d29 | EV-092: mutaciones de las pruebas de estados y de scripts de verificación en vivo (10 de 10 detectadas) |
| 84e1353 | 39e7415 | Criterio de texto: documento aislado de la raíz sin nombrarlo (RAIZ_DOC), archivos de retroalimentación y verificación renombrados, profesor, Avance 2, etiquetas de fase y pie de la evaluación heurística reemplazados, y figura de stakeholders regenerada desde su tabla con su prueba |
| f04e8e0 | 64fd420 | Criterio de texto con su prueba y mutaciones, igualdad de código entre referencias, vocativo quitado de diez celdas de notebooks y D97 |
| 02e5fa5 | 03c31f1 | EV-093 y EV-094, nbformat declarado en requirements, lectura del PNG sin librerías de imágenes y cifras de 998 pruebas en el informe, la matriz, el README y los documentos de estado |
| 1e07bdc | d9723cc | Cifras de 1000 pruebas, patrón de cifras ampliado a cuatro dígitos, cifra histórica de EV-072 restituida, guardia de las subfilas de detalle y figura de stakeholders con nombres completos y puntos separados |
| 6dedc25 | ebc9a97 | D35: la respuesta recibida |
| cbb898c | 7a59598 | Nota de que EV-086 es un número no usado |
| 14de38a | e93591b | Etapa 4b: validar_checklist.py, trazabilidad de los 30 ítems con una sola fuente y su prueba de coherencia, fichas de 6.5 y 7.1 a 7.5, guardianes de coherencia y D98 |
| 3b628aa | 0a4bdad | EV-095 y cifras de 1007 pruebas en el informe, la matriz, el README y los documentos de estado |
| 68f53ca | 01bbccf | Trazabilidad: el comando de cada ítem corre exactamente sus pruebas y ninguno escribe documentos; la prueba lo exige |
| d23cb1c | a0d5e7d | medir_memoria_suite: sigue a todos los procesos descendientes y falla en lugar de escribir 0 |
| 8de5f0c | 0cedafb | EV-096 y EV-097: independencia repetida con el número exacto de omisiones (0, 1 y 10) y pico de memoria de la suite medido con el script movido; documentos y pruebas alineados |
| 095781c | dbfac3a | Cifras de 1008 pruebas en el informe, la matriz, el README y los documentos de estado |
| 7d4a44d | d6f1b5b | Guía de instalación: los dos picos de memoria de la suite y cuál se usa para planear el equipo; número exacto de pruebas que se omiten sin Git |
| 11ad17c | 6721b3d | Modo mínimo: lo que debe decir la comprobación del equipo antes y después de crear el entorno, y que la API no tiene página en la raíz |
| 8af5bf0 | f6c51d0 | Guía de simulación: fuentes por partes con inclusiones, generador del PDF (conversor de Markdown propio y Edge sin ventana) y los dos PDF, el completo y el del participante sin las tareas |
| 897e83c | 36aeb95 | Guía de simulación: correcciones tras seguirla como tercero (mayúsculas del hash, una prueba omitida con el zip, notas azules que no son errores, puerto a la escucha, Ctrl+C comprobado) y tiempos medidos |
| 32980ee | 43a87a1 | Pruebas de la guía de simulación y de su generador (conversor, inclusiones, perfiles, citas, cifras y formato de los archivos); el filtro de filas falla si una tabla se queda sin filas |
| 301434b | 67dc29e | Prueba: una inclusión conserva la línea en blanco que la separa del texto siguiente |
| c751244 | bfd35ee | Prueba: una barra dentro de un trozo de código no parte la celda de la tabla |
| f000754 | ea9af8f | Decisiones D99 y D100, evidencias EV-098 y EV-099 de la guía de simulación, enlaces en los índices y cifras de 1047 pruebas en el informe, la matriz, el README y los documentos de estado |
| b807fbb | 28c46d2 | Modo completo: .env sin repositorio de Git (acepta solo si .gitignore lo ignora de verdad, con aviso; con Git sigue igual de estricto) y --nombre-compose opcional con aviso de volumen de Postgres previo; pruebas de cada caso |
| f5a16bd | e51c289 | Evaluador de .gitignore sin código muerto ni caracteres invisibles |
| 2e0336b | 7ea1ae7 | configurar_mysql: la consulta a git declara su codificación (prueba de portabilidad) |
| 9fd856a | c7adb5b | Escáner de secretos sin repositorio: con un .env presente el .gitignore debe ignorarlo de verdad, avisa que no revisó historial y, con .git pero sin el programa git, termina con código 2; la regla de .gitignore vive en un módulo compartido que viaja en el zip |
| 0328742 | 85fd557 | Compose de Airflow: el chown de airflow-init salta el proyecto montado en solo lectura (DF-19), con su prueba, su diff regenerado y el documento de diferencias al día |
| 3619db3 | ef6ebc6 | Guía del modo completo en borrador (todos los comandos con su bloque «Qué debe verse», aún sin probar), su prueba guardiana y enlaces desde el modo completo y el índice de instalación |
| 90bd057 | 130685d | Guía del modo completo ajustada: requisito previo (zip y entorno), airflow-init sin garantías falsas, «Para qué sirve» y «Reemplace» en cada comando, portapapeles limpio, avisos de memoria y OneDrive, conteo de comandos automático y prueba guardiana con reglas compartidas (55 mutaciones detectadas) |
| 178f8de | d5beb02 | Guía del modo completo probada desde un zip nuevo: los 33 comandos con su salida literal enmascarada, el «Varía» y el «Tiempo» (dos bloques siguen sin probar); la prueba guardiana admite el texto propio del programa y sus negativas se adaptan a la guía llena |
| cafd740 | 391a4b4 | Compose de Airflow: airflow-init comprueba la conexión con la base de metadatos y termina con código 1 si falla (DF-20), con su prueba, 17 mutaciones detectadas, su diff regenerado y el documento de diferencias al día |
| 42d08da | 29dc22e | Guía del modo completo con DF-20: airflow-init, construcción y levantado vueltos a ejecutar con el compose nuevo y un volumen nuevo, hallazgo 4 con sus dos comportamientos (antes y ahora), bloque de «root» visto por Daniel y regla de la guardiana sobre airflow db check |
| 68188d8 | 4ca6e16 | Guía: el código de up airflow-init no es una señal fiable y airflow db check solo va vía /entrypoint (con su regla y negativas); evidencias EV-100 a EV-102, D101 a D104 y DEF-017 a DEF-021 con sus reintroducciones |
| b253a4d | 8efa0f9 | Evidencias EV-100 a EV-104 registradas con su sha256 (la guía seguida desde un zip nuevo, el hallazgo 4 y DF-20, las tres capturas de Daniel como imágenes existentes, 132 mutaciones y las regresiones de DEF-017 a DEF-021), trazabilidad, errores comunes y operación al día |
| 6aefa35 | 87bd0b0 | Cifras de 1248 pruebas en el informe, la matriz, el README y los documentos de estado |
| db5f3ac | cd1e53a | Las pruebas que ejecutan un trozo del compose con bash eligen uno que lea rutas de Windows (el de WSL del PATH las hacía fallar en la suite del clon y del zip), con su ayudante y su prueba |
| d75265d | 9a49be0 | Cifras de 1251 pruebas en el informe, la matriz, el README y los documentos de estado |
| 595f565 | 65cc637 | Las pruebas con bash ponen la carpeta de ese bash delante en el PATH (desde PowerShell el find de Windows salía con 2), con su prueba |
| 9c64dfe | 94fe6db | Cifras de 1252 pruebas en el informe, la matriz, el README y los documentos de estado |
| 0c7f027 | 9b225c1 | DEF-022 y EV-105: la suite completa en clon y zip desde PowerShell, antes y después de corregir las dos pruebas con bash (22 defectos), con su fila en el manifiesto y en la trazabilidad |
| aa4d3cc | e764ecb | Sección 11 de la guía vista por Daniel en su proyecto real (EV-106), DEF-023 (el bloque de configurar_mysql.py --solo-verificar decía sin salida y imprime dos líneas de registro) y la guardiana adaptada a una guía sin bloques pendientes |
| 094f109 | 8e46ea7 | EV-106: el archivo cambia de nombre para no chocar con el criterio de términos de proceso, y sus referencias y su fila del manifiesto se actualizan |
| 11b7a94 | cf6c72d | DEF-024 y EV-107: el bloque de docker compose up airflow-init se recaptura con 2>&1 sobre un volumen nuevo (le faltaban 24 líneas de progreso de Compose), con la auditoría de los demás bloques, el canario repetido y la fe de erratas de EV-100 y EV-101 |
| 061e9f8 | e624533 | DEF-025: el bloque de docker compose build se reemplaza por su captura completa con 2>&1 (le faltaban 12 líneas), conciliación de las 36 líneas de la recaptura de airflow-init (27 perdidas más 9 de estado) y el nombre de proyecto de ejemplo declarado en la guía |
| d99ab7d | 4efc6fa | D105: el README se escribe a mano, el análisis pasa a docs/gold/resultados.md, se retira el generador, se añade la guardiana del README, la licencia MIT en la raíz y la excepción acotada de la línea de declaración |
| cbac27b | 9023fd8 | Imágenes del README (diagramas en gris con su fuente, insignias, capturas), documento de atribución de datos, licencia con los tres nombres, cita del artículo de Airflow en la guardiana y pruebas de cifras que detectan una cifra repetida desactualizada |
| b82feda | 0f3e1ce | Los SVG de las insignias y de los diagramas se versionan con saltos LF para que su sha256 no dependa del equipo |
| fffd2e2 | e375549 | README de 20 secciones escrito a mano, con los dos diagramas aportados (EV-112), la guardiana sobre el README real y pruebas que comparan cada cifra del texto con lo medido |
| b256908 | 72245b5 | El README usa copias en gris de los dos diagramas aportados, generadas con make_imagenes_readme.py y comprobadas por la guardiana, y descompone las 132 mutaciones de EV-103 por parte con una prueba que vigila cada número |
| 3241f41 | a04d122 | README: afirmaciones verificadas contra el repositorio (defectos, contenedores, ramas, privilegios, secretos de Airflow), árbol de directorios, variables de entorno, umbrales de calidad, estrategia de carga, linaje, cifrado, escalado y ruta de contacto, con pruebas que vigilan cada cifra nueva |
| 741bf42 | 426fc49 | Gestión de credenciales: la clave Fernet y el secreto JWT de Airflow son obligatorias desde el .env de Airflow, con una prueba que compara la fila con el compose y con el script que las genera |
| dec0da2 | 90a7cfb | Dependencias: pillow declarada (el código lo importa); README: las líneas de salida del pipeline sin separador de miles, como las imprime el registro; prueba de ramas válida en un clon |
| 3307398 | 9c7329b | Mediciones del modo mínimo en un clon nuevo y de la suite en el clon y en un zip (EV-113), cobertura de src repetida (EV-114), tablas de tiempos del README con lo medido y vigiladas por prueba, informe de pruebas y cobertura regenerados sin el generador retirado y cifras de estado al día |
| e3301f0 | ad5152b | Informe de pruebas regenerado con el nombre actual de la prueba de cobertura del README |
| 7a39729 | 5879299 | EV-113: repetición de la suite en el clon y en un zip nuevo sobre el último commit; el README cita el rango medido |
| 282a85e | 693ebb4 | Documento de arquitectura del sistema (18 secciones) con 13 registros de decisión, diagramas en texto y su guardiana; D106 registra la estructura y marca D21 y D5 como modificadas |
| 6321471 | a0c31d5 | ADR-014 (Gold lee solo Silver), documento de arquitectura enlazado desde el README, el índice de docs y la fila 7.3, pruebas de sus cifras y de los errores ya corregidos en el README, y registro de sus mutaciones (EV-115) |
| d0a1257 | 48f8bb2 | Correcciones de la revisión del documento de arquitectura y los ADR: filas de MySQL, puertos y cifrado, reintentos, latencias de EV-032, hechos de ADR-007 y ADR-014, riesgo de concentración del conocimiento; prueba de Gold sin Bronze ni shapely; EV-115 regenerada (111 mutaciones detectadas de 111); recuento de pruebas en 1375 |
| 8256a2c | 77b2f53 | README seccion 13: reintentos de la descarga con la espera de 30 s por intento |
| 10be0ab | ff9e1f0 | EV-115 repetida sobre el estado final de las pruebas: 111 de 111 detectadas, con el historial de las cuatro vueltas y de los huecos que mostraron las dos primeras |
| d68d243 | f0ef3e6 | README y docs/api/arquitectura.md: texto de datos de personas sin afirmar que no se manejan datos personales; guardiana con la frase prohibida; prueba de los reintentos del README contra config.yaml y el codigo; recuento en 1377 pruebas |
| 950e54c | 3a6cc2f | EV-115 repetida sobre el estado final: 126 de 126 detectadas, con el cuadre de la vuelta 1 y la serie del README; seccion 17 y manifiesto al dia |
| 0dca001 | 0b3d067 | Informe de pruebas y cobertura regenerados con las 1377 pruebas (todas pasan); cifras de los documentos de estado al dia |
| 01127b9 | 41782db | Clausula por capa de los identificadores de predio (Bronze los trae, Silver los descarta por R10, Gold conserva las coordenadas del centroide) en el README y en el documento de arquitectura, con pruebas contra las cabeceras de los archivos; recuento en 1381 pruebas |
| 0b392e1 | c6fb2f9 | EV-115 repetida sobre el estado final con las mutaciones de la clausula de predios: 137 de 137 detectadas; seccion 17 y manifiesto al dia |
| cd6b354 | 7ed93a9 | EV-116 con las mediciones de la suite en un clon y en un zip, la cobertura de src, el informe y el escaner sobre el commit 0b392e1; informe de pruebas regenerado con las 1381 pruebas; documentos de estado con la cifra y la cita de EV-116 |
| 3961c29 | 3c19290 | ADR-015 (calidad de datos en Silver), documento de arquitectura en Revisado (0.2) con los 15 ADR revisados, estado y cifras al dia en README, indice de docs y checklist, fila de contratos de la seccion 7 y R02 de resultados.md corregidos, pruebas nuevas (ADR-015, revision con nombre y fecha, estado entre documentos), EV-115 repetida: 186 de 186 detectadas |
| d82d0aa | 26a1fa3 | PDF del documento de arquitectura y de los ADR (generador, pruebas, EV-117), encabezados del DAG y de docs/orquestacion que remiten al articulo acreditado en el README, nota fechada en D57 y D101 (seccion 11 probada, EV-106), decisiones D107 a D110, 7.2 y 7.3 en Cumple con matiz, recuento en 1396 pruebas, EV-115 repetida: 188 de 188 detectadas |
| b564037 | 2e41db2 | PDF con los ADR seguidos y dos figuras en gris (EV-117 al dia), sesiones simuladas separadas de las reales (D109: carpeta, plantilla, analisis y pruebas), 7.2 vuelve a En curso, script y pruebas del ensayo de limpieza de pies con el inventario de hashes citados, recuento en 1424 pruebas |
| 102d781 | d453991 | Ensayo de limpieza de pies: los hashes citados se comprueban contra los commits que alcanzan las ramas y las etiquetas, no contra los objetos que siguen en el repositorio |
| 3157ee2 | afe26e6 | EV-118 con el resultado del ensayo de limpieza de pies (sin problemas; la limpieza no se aplico) e inventario de hashes citados al dia |
| df97921 | 72be434 | Sesiones simuladas: registro de la etapa 1 del participante simulado 1 con sus correcciones posteriores, seccion de sesiones simuladas en la declaracion, inventario y auditoria de la carpeta de trabajo (EV-119), inventario de hashes citados al dia, regex del generador de PDF que parecia una ruta de unidad, recuento en 1447 pruebas |
| 3a5726e | 700c5ac | Sesiones simuladas: participante 1 con su entrega nativa verificada (EV-119 ampliada), reconciliacion de C1 a C8, hallazgos H1 a H8, CSV de los dos participantes, participante 2 incorporado (EV-120), declaracion, inventario con modo --nativa y recuento en 1467 pruebas |
| 9b3d1f8 | 37d0c33 | Declaracion de uso de IA al dia (herramientas, ensayo metodologico, veredictos y modelo dictados, lectura limitada de transcripciones, capturas con sha256, pendientes marcados), resumen de una linea de C1 a C8 y H1 a H8, pruebas y recuento en 1470 |
| 48a292a | 19b86d6 | Guia de uso del panel: unidad, proxy, sin datos, que significa incluir 0, filtros y total de Construcciones, publicador en Fuentes y donde se ve cada respuesta (observaciones S-01 a S-06 de las sesiones simuladas) |
| 9425939 | 3dd8497 | Registro de fricciones y trazabilidad de cambios con las observaciones S-01 a S-09 de las sesiones simuladas (decision y razon de cada una, cambio 48a292a), prueba que lo vigila, recuento en 1471 pruebas |
| 782f76d | 38badbe | Excepcion D111 para 6.1, 6.2, 6.3, 6.5 y 7.4: Cumple con matiz solo con evidencia simulada, sin personas reales (seccion 7 de la declaracion y decision nueva sin editar la regla), frase de las sesiones simuladas cambiada, pruebas de control que impiden Cumple a secas y exigen la referencia, recuento en 1474 pruebas |
| 311d0d9 | bf3ef71 | Formato simulado: N para el SUS y el CSAT de las sesiones simuladas (D112) con tres guardas: el modo real rechaza cifras simuladas, el modo simulado exige prefijo y origen y todo resumen lleva la marca; plantilla, README, protocolo y pruebas al dia, pendientes de Daniel como no verificados, recuento en 1478 pruebas |
| 1ab0efe | f0a2765 | Declaracion de uso de IA con la informacion del equipo segun ChatGPT: papel de cada herramienta, prompts de la ronda 1 (autoria y adaptaciones sin constar, envio manual), fechas, modelos sin certificar, diagramas con metadatos de procedencia pendientes de confirmacion y lo que no consta como no verificado; prueba que lo exige |
| 2300dc4 | 2a89f93 | Una sola ronda de dos sesiones simuladas: parrafo de retroalimentacion de 7.3 con lo que consta (sesiones reales 0, simuladas 2, ajustes de la guia sin volver a probar), textos de sin sesiones al dia, simulado: N y D112 como capacidad del analizador sin estimaciones registradas, pruebas que lo exigen y recuento en 1481 pruebas |
| d1d1009 | c15826b | Documento de arquitectura Aprobado, version 1.0, aprobado por los tres autores el 2026-11-20 (D113), seccion 4 de la declaracion con el texto del equipo, 7.2 pasa a Cumple con matiz, guardianas y pruebas al dia |
