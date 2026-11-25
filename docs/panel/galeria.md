# Galería del panel

Capturas del panel de consulta en su versión vigente (interfaz propia de D115 a D117), una por página y de cada herramienta de lectura, más los estados elegidos y la vista de móvil. Son **capturas automatizadas del navegador** (no las toma una persona) sobre el panel real, arrancado con el lanzador oficial, con los datos de la API del proyecto (almacenamiento SQLite, fecha de corte 2026-09-02). No hay maquetas, cifras de ejemplo ni datos sensibles: las capturas de las ocho páginas se tomaron con la línea de estado de la API visible y el recuadro de alcance en pantalla, y el registro [EV-128](../evidencias/frontend/EV-128_capturas_definitivas_del_panel.txt) (más EV-129 para las tres del título corregido) comprobó, para las ocho páginas, que el alcance, la fecha de corte y la ausencia de errores en pantalla estaban en el texto de la página.

| | |
|---|---|
| **Cómo se obtuvieron** | `python scripts/evidencias/capturas_panel_definitivo.py`: arranca el lanzador (`scripts/panel/ejecutar_panel.py`), abre cada página en Edge sin ventana por el protocolo DevTools, acciona los controles de cada estado y guarda la captura |
| **Tamaño** | escritorio de 1440 por 900 píxeles; móvil de 390 por 844 píxeles con doble densidad (780 píxeles de ancho en el archivo) |
| **Formato** | PNG de 256 colores, sin retoques de contenido; el peso de cada imagen y su sha256 están en EV-128 |
| **Dónde están** | `docs/img/panel/`; el README usa cuatro de ellas, copiadas con los mismos bytes en `docs/img/readme/` |
| **Qué NO son** | pruebas de que la interfaz sea usable para personas reales, ni de que se vea igual en otros navegadores o pantallas |

Las capturas anteriores del panel (EV-054, EV-073 a EV-081 y la hoja de la guía de las sesiones simuladas) siguen en `docs/evidencias/` y en `docs/usuarios/` como evidencia histórica: muestran la versión que existía cuando se registraron y no la actual. Las dos hojas de EV-125 y EV-126 son de la integración y de otra resolución (1400 y 375 píxeles).

## Las ocho páginas en escritorio

### Respuesta
![Respuesta en escritorio: tarjetas de la diferencia de tasas con su intervalo de Newcombe y la razón, lectura generada y tasas de los dos grupos](../img/panel/escritorio_01_respuesta.png)

### Estratos (K1)
![Estratos en escritorio: tarjetas de cifras, recuadro de alcance y figura de tasas por estrato con intervalos de Wilson](../img/panel/escritorio_02_estratos.png)

### Comunas (K6)
![Comunas en escritorio: figura de tasas de las siete comunas con sus intervalos de Wilson](../img/panel/escritorio_03_comunas.png)

### Sensibilidades (S0 a S5)
![Sensibilidades en escritorio: gráfico de la diferencia de tasas por escenario con su intervalo de Newcombe y el título completo](../img/panel/sensibilidades_titulo_1440x900.png)

Corrección del título (D119): el título del gráfico, en dos líneas, se veía con su primera línea recortada por el borde superior del gráfico; hoy se ve completo. Las capturas de comprobación a 1440, 768 y 375 píxeles son de [EV-129](../evidencias/frontend/EV-129_titulo_del_grafico_de_sensibilidades.txt):

![Sensibilidades a 768 por 1024 píxeles con el título del gráfico completo](../img/panel/sensibilidades_titulo_768x1024.png)

![Sensibilidades a 375 por 812 píxeles con el título del gráfico completo](../img/panel/sensibilidades_titulo_375x812.png)

Las capturas [escritorio_04_sensibilidades.png](../img/panel/escritorio_04_sensibilidades.png) y [movil_04_sensibilidades_grafico.png](../img/panel/movil_04_sensibilidades_grafico.png) son de EV-128, tomadas antes de la corrección: siguen como se registraron y muestran el título recortado, así que no representan la versión vigente.

### Concentración (K3 y K4)
![Concentración en escritorio: tarjetas de K3 con la participación de los barrios líderes y su peso, y el aviso de una curiosidad de la página](../img/panel/escritorio_05_concentracion.png)

### Calidad de la llave
![Calidad de la llave en escritorio: cobertura de la llave, estrato válido y nombre validado, con la tabla de coincidencia con el polígono](../img/panel/escritorio_06_calidad.png)

### Construcciones
![Construcciones en escritorio: filtros por comuna, estrato y cambio severo, página y tabla seleccionable](../img/panel/escritorio_07_construcciones.png)

### Fuentes y sistema
![Fuentes y sistema en escritorio: fecha de corte, población y tabla de fuentes con sus licencias](../img/panel/escritorio_08_fuentes.png)

## Herramientas de lectura

![Respuesta con la guía de lectura abierta en el paso cuatro, que cita los conteos reales de la muestra](../img/panel/herramienta_01_respuesta_guia.png)

Guía de lectura de seis pasos, abierta en el cuarto (Respuesta).

![Estratos con la primera de sus tres curiosidades abierta](../img/panel/herramienta_02_estratos_curiosidad.png)

Curiosidades de la página, con su fundamento en el glosario o en el método (Estratos).

![Estratos en modo presentación: página a pantalla completa, sin la barra lateral y con el botón para salir](../img/panel/herramienta_03_estratos_presentacion.png)

Modo presentación (Estratos); Escape o el botón «Salir de presentación» lo cierran.

## Estados elegidos

![Estratos en la vista de puntos e intervalos con el Estrato 4 destacado en la figura y en el detalle](../img/panel/estado_04_estratos_puntos_y_seleccion.png)

Estratos en la vista de puntos e intervalos, con una fila destacada.

![Comunas con la Comuna 03 abierta en el detalle, que la lee en palabras](../img/panel/estado_05_comunas_detalle.png)

Comunas con una fila abierta: el detalle cuenta su tasa, su intervalo y los registros sin datos en palabras.

![Construcciones con la fila 2 de la primera página elegida y «Qué significa esta fila» abierto](../img/panel/estado_06_construcciones_fila_elegida.png)

Construcciones con una fila elegida: su lectura en palabras, el botón del CSV de las filas mostradas y, debajo, la dispersión de ubicaciones.

![Sensibilidades con la razón ajustada de Mantel-Haenszel y los seis avisos por escenario](../img/panel/estado_07_sensibilidades_mantel_haenszel.png)

Sensibilidades, razón ajustada por comuna de Mantel-Haenszel con el aviso de cada escenario.

![Concentración con K4: correlación de Spearman, barrios incluidos y valor p de permutación](../img/panel/estado_08_concentracion_k4.png)

Concentración, K4 con su lectura generada y su cautela de falacia ecológica.

![Calidad de la llave con los siete códigos de barrio sin nombre validado](../img/panel/estado_09_calidad_revision.png)

Calidad de la llave, códigos de barrio por revisar y el recuadro «Qué NO demuestra».

![Fuentes y sistema con los ocho puntos de lo que no se puede concluir y las limitaciones del panel](../img/panel/estado_10_fuentes_limites.png)

Fuentes y sistema, los ocho puntos de «qué no se puede concluir» y las limitaciones del panel.

## Móvil (390 píxeles de ancho)

![Las tres primeras capturas de móvil lado a lado](../img/panel/movil_00_estratos_y_construcciones.png)

| Captura | Qué muestra |
|---|---|
| [movil_01_estratos_inicio.png](../img/panel/movil_01_estratos_inicio.png) | inicio de Estratos: cabecera con su ícono, tarjetas de cifras y recuadro de alcance |
| [movil_02_estratos_figura.png](../img/panel/movil_02_estratos_figura.png) | figura de tasas de Estratos con sus intervalos |
| [movil_03_construcciones_tabla.png](../img/panel/movil_03_construcciones_tabla.png) | filtros, página y tabla de Construcciones |
| [movil_04_sensibilidades_grafico.png](../img/panel/movil_04_sensibilidades_grafico.png) | gráfico de Sensibilidades antes de la corrección del título (EV-128, con la primera línea recortada); la versión corregida a 375 píxeles es `sensibilidades_titulo_375x812.png` |

## Para repetirlas
Con el entorno virtual creado, `python scripts/evidencias/capturas_panel_definitivo.py` vuelve a generar todas las imágenes y su registro; tarda unos 15 minutos porque cada página se espera hasta que Streamlit termina de dibujarla. Si cambia la interfaz hay que volver a ejecutarlo, revisar cada imagen, registrar el resultado en el manifiesto de evidencias y copiar al README las cuatro imágenes que usa.
