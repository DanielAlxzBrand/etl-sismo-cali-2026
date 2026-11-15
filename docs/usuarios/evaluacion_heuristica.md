# Evaluación heurística interna del panel

**Ítem del checklist:** 3.3 (subcriterios 1 a 3: evaluación heurística, capacidad de respuesta y coherencia visual) · **Fecha:** 2026-11-14 · **Qué es:** una evaluación hecha por el propio equipo de desarrollo con las diez heurísticas de Nielsen sobre las ocho páginas del panel, a partir de capturas y mediciones automatizadas. **No es una prueba con personas usuarias**: esas siguen pendientes ([protocolo_sesiones.md](protocolo_sesiones.md)).

> [Fuente externa: Nielsen, J. (1994). «10 Usability Heuristics for User Interface Design», Nielsen Norman Group, y su escala de severidad de 0 a 4, consultadas por el equipo como referencia.] Severidad: 0 = no es un problema de usabilidad; 1 = cosmético; 2 = menor; 3 = mayor (conviene arreglarlo pronto); 4 = catastrófico (hay que arreglarlo antes de usar el panel). Aquí la damos mirando la evidencia, sin personas, así que es una **estimación nuestra**, no una frecuencia observada.

## 1. Cómo se hizo
1. Se arrancó el panel con `scripts/panel/ejecutar_panel.py` (API y panel en `127.0.0.1`, almacenamiento SQLite) y se controló un navegador sin ventana por el protocolo DevTools, como en D79 (`scripts/evidencias/evidencia_capturas_anchos.py` y `evidencia_capturas_movil.py`).
2. Por cada página y en tres anchos (1400, 1024 y 390 px) se tomó una captura completa, se midió si el contenido se desborda en horizontal, qué elementos tienen el texto recortado por el CSS y cuánto tarda la página en dibujarse (1 carga de calentamiento y 5 medidas; medición local de una máquina), y se calculó el contraste del texto con la fórmula WCAG de `src/panel/tema.py`. Evidencias: [EV-066](../evidencias/usuarios/EV-066_capturas_anchos.txt), [EV-067](../evidencias/usuarios/EV-067_mediciones_anchos.txt), [EV-068](../evidencias/usuarios/EV-068_contraste_texto.txt) y [EV-069](../evidencias/usuarios/EV-069_capturas_390_barra_cerrada.txt).
3. Se abrieron las capturas una por una y los hallazgos salieron de lo que se veía y se midió, no de una lista previa. Varios «candidatos» que traíamos (textos de Streamlit en inglés, etiquetas de latitud, pocas filas visibles en la tabla de construcciones, falta de glosario, 390 px) se confirmaron con captura o se rebajaron de severidad: están marcados en la tabla.
4. **Nada de esto se corrigió** al hacer la evaluación (no se tocó `src/panel`): los hallazgos se documentan y se priorizan en el [registro de fricciones](registro_de_friccion.md) como iteración técnica, no como validación con personas. Los ajustes vinieron después y se reevaluaron en la sección «Reevaluación tras los ajustes».

## 2. Hallazgos
| Id | Página | Heurística | Descripción (lo que se vio) | Captura | Severidad | Recomendación |
|---|---|---|---|---|---|---|
| F-01 | Respuesta, Concentración, Fuentes y sistema (a 1024 px) | H1 Visibilidad del estado | Las tarjetas recortan las etiquetas y hasta las cifras: «6,33…», «Tasa 1-2 (…», «+0,4…», «Participación de los barrios con má…», «202…» en lugar de la fecha. Se midieron 13 elementos con texto recortado a 1024 px (6, 3 y 4 en esas tres páginas). La cifra central de la respuesta no se lee completa. | `EV-066_captura_respuesta_1024.png`, `EV-066_captura_concentracion_1024.png`, `EV-066_captura_fuentes_1024.png` | 3 | Dejar que las etiquetas se partan en dos líneas, no recortar los valores y usar menos tarjetas por fila por debajo de unos 1200 px. |
| F-02 | Todas (a 390 px) | H3 Control y libertad del usuario | La barra lateral de navegación se abre sola y cubre casi todo el contenido: la persona ve el menú y apenas un borde de la página. Para ver el contenido hay que descubrir el botón de cerrar («‹‹»). Una vez cerrada, la barra se mantiene cerrada en las demás páginas. La configuración de la aplicación pide la barra expandida (`initial_sidebar_state="expanded"`). | `EV-066_captura_respuesta_390.png`, `EV-066_captura_estratos_390.png` | 3 | Abrir la barra cerrada en pantallas estrechas, o dejar la navegación en la propia página. |
| F-03 | Estratos, Comunas, Calidad, Construcciones y Fuentes (a 390 px; Fuentes también a 1024 px) | H1 Visibilidad del estado | Las tablas anchas se cortan en el borde y no se ve que hay más columnas a la derecha: «Detalle por estrato» y «Detalle por comuna» terminan en «Tasa» o a media columna; la tabla de construcciones termina en «Estr…»; las de Calidad y Fuentes están dentro de contenedores con desplazamiento horizontal (552 y 718 px dentro de 356 px) y la columna de licencias se corta aun a 1024 px. | `EV-069_captura_estratos_390_barra_cerrada.png`, `EV-069_captura_comunas_390_barra_cerrada.png`, `EV-069_captura_construcciones_390_barra_cerrada.png`, `EV-066_captura_fuentes_1024.png` | 3 | Mostrar un indicio de desplazamiento, apilar las columnas en pantallas estrechas o reducir las columnas visibles. |
| F-04 | Estratos, Comunas y Construcciones (a 390 px) | H1 Visibilidad del estado | En los gráficos de barras estrechos solo se dibujan la primera y la última etiqueta del eje (por ejemplo «Estrato 1» y «Estrato 6», «Comuna 03» y «Comuna 20»): las demás barras no se pueden identificar. El título del gráfico de construcciones se corta («…, por c…»). | `EV-069_captura_estratos_390_barra_cerrada.png`, `EV-069_captura_comunas_390_barra_cerrada.png`, `EV-069_captura_construcciones_390_barra_cerrada.png` | 3 | Etiquetar las barras de otra manera en pantallas estrechas (barras horizontales o etiquetas en vertical) y dejar que el título se parta. |
| F-05 | Estratos y Comunas | H10 Ayuda y documentación | Las marcas horizontales negras que cruzan las barras (cotas por «sin datos») no están explicadas en el gráfico: el pie solo explica las barras de error de Wilson, y las cotas se explican más abajo, junto a la tabla. | `EV-066_captura_estratos_1400.png`, `EV-066_captura_comunas_1400.png` | 2 | Agregar una frase o una leyenda de las marcas debajo del gráfico. |
| F-06 | Sensibilidades | H8 Diseño estético y minimalista | La misma frase («con este proxy y esta muestra no se detecta diferencia») se repite en las seis líneas de escenarios y en el resumen, y hay seis avisos casi iguales sobre la razón ajustada de Mantel-Haenszel. La página mide 2359 px de alto a 1400 px de ancho (la segunda más larga) y lo importante queda diluido. | `EV-066_captura_sensibilidades_1400.png` | 2 | Resumir en una sola frase lo que se repite y dejar los avisos iguales en un solo recuadro o en el desplegable. |
| F-07 | Todas | H2 Relación entre el sistema y el mundo real | Aparecen términos estadísticos sin explicación en pantalla: «intervalo de Wilson», «Newcombe», «Mantel-Haenszel», «Spearman», «p de permutación», «cotas por sin datos», «muestra baja», «proxy». No hay glosario en el panel (el glosario existe en la documentación, no en la interfaz). Si una persona sin formación estadística los entiende **no se puede saber sin sesiones**. | `EV-066_captura_estratos_1400.png`, `EV-066_captura_sensibilidades_1400.png`, `EV-066_captura_concentracion_1024.png` | 3 | Agregar un glosario corto en el panel (o ayudas en cada término) y probar la comprensión en las sesiones. |
| F-08 | Sensibilidades, Construcciones, Fuentes y sistema | H4 Consistencia y estándares | Identificadores de código en la interfaz: «nombre_validado = true», «coincide_poligono», «pureza_estrato >= 0,8», «dano_visible», «geom_duplicada», «sin_cambio», «escombros», «techo», «silver_integrated», «gold_final». Mezclan el vocabulario interno con el del resto de la página. | `EV-066_captura_sensibilidades_1400.png`, `EV-066_captura_construcciones_1400.png`, `EV-066_captura_fuentes_1024.png` | 2 | Mostrar etiquetas en lenguaje natural y dejar el identificador solo en la documentación. |
| F-09 | Concentración | H6 Reconocimiento antes que recuerdo | La tabla de K3 lista códigos de barrio («1914», «306») sin el nombre del barrio: quien conoce su barrio por el nombre no lo reconoce. | `EV-066_captura_concentracion_1024.png` | 2 | Mostrar el nombre del barrio junto al código (si la fuente lo permite sin cambiar la API). |
| F-10 | Construcciones | H7 Flexibilidad y eficiencia | La tabla muestra unas 10 filas a la vez dentro de una caja con desplazamiento aunque la página trae 50, y para recorrer las 103 páginas solo hay un campo numérico «Página» (sin «siguiente» ni salto). Es lento revisar muchas construcciones. | `EV-066_captura_construcciones_1400.png` | 2 | Botones de página anterior y siguiente, y una caja de tabla más alta. |
| F-11 | Todas con tablas o gráficos | H4 Consistencia y estándares | Los textos de los controles de Streamlit están en inglés y el resto de la interfaz en español: «Download as CSV», «Fullscreen», «Search», «Show/hide columns», «Copy Vega-Lite spec», «Download as PNG», «Show data», «Skip to main content», «Collapse sidebar», «Increment» y «Decrement». Se confirmó en la lista de etiquetas accesibles del navegador (EV-066); su aspecto al pasar el cursor no se capturó. | `EV-066_captura_comunas_1400.png` | 2 | Revisar si Streamlit permite traducirlos o reducir los menús que se muestran. |
| F-12 | Todas | H1 Visibilidad del estado | Contraste calculado del texto secundario: los pies y la pregunta de cada página dan 4,05 a 1 y los rótulos, títulos y leyendas de los gráficos 3,72 a 1 (EV-068); el cuerpo, los subtítulos y las tarjetas dan entre 7,2 y 14,76 a 1. Los grises claros son pequeños (14 px) y pueden costar a personas con baja visión. No se declara un nivel de conformidad. | `EV-066_captura_estratos_1400.png` | 2 | Oscurecer el gris de los pies y de los textos de los gráficos. |
| F-13 | Construcciones | H2 Relación entre el sistema y el mundo real | Las etiquetas del eje de latitud usan coma decimal («3,440», «3,430») y pueden leerse como miles; el título dice «grados». **Candidato rebajado:** en el resto del panel la coma ya es el separador decimal, por eso es cosmético; se deja para ver si alguna persona se confunde. | `EV-066_captura_construcciones_1400.png` | 1 | Mostrar «3,440°» o una unidad en las etiquetas. |
| F-14 | Estratos, Comunas, Sensibilidades y Construcciones | H1 Visibilidad del estado | Las páginas con gráfico tardan más en dibujarse que Respuesta: Respuesta 234 a 343 ms a 1400 px y entre 1,1 y 2,1 s las páginas con gráfico (Estratos, Comunas, Sensibilidades) y Construcciones, frente a 0,7 a 1,0 s en Concentración, Calidad y Fuentes (EV-067; medición local de una máquina, con variación entre corridas). No se midió cuántos segundos tolera una persona. | `EV-066_captura_estratos_1400.png` | 1 | Medir en las sesiones si la espera se nota; si sí, evaluar el almacenamiento de resultados. |

**Candidatos descartados o sin hallazgo:** no hay desbordamiento horizontal del documento en ningún ancho (el ancho del documento es igual al de la ventana en las 24 capturas); no se vio texto solapado; ninguna página muestra errores en pantalla.
**Lo que NO se puede evaluar sin personas** (queda para las sesiones): si se entienden los intervalos y la «muestra baja», si el recuadro de alcance se lee o se salta, y si la respuesta de la página Respuesta se interpreta como «no se detecta diferencia» y no como «el estrato no influye».

## 3. Fortalezas observadas
- El mismo marco en las ocho páginas (título, pregunta de la página, estado de la API y fecha de corte, recuadro de alcance y fuente al pie): la persona siempre sabe dónde está.
- El recuadro de alcance aparece en cada captura, junto con la advertencia de proxy, de muestra y de estrato de 2015.
- Los grupos con muestra baja se distinguen por color **y** por texto («muestra baja»), no solo por color; los colores son azul y naranja, distinguibles para la mayoría de las personas con daltonismo.
- Formato de cifras uniforme (coma decimal y punto de miles) y lenguaje que no afirma causalidad («con este proxy y esta muestra no se detecta diferencia»).
- Cada tarjeta trae un ícono de ayuda (`Help for …`) y las páginas con tabla permiten descargar CSV.
- Contraste alto en cuerpo, subtítulos, tarjetas y avisos (de 7,2 a 14,76 a 1).

## 4. Matriz heurística × página
Los números son los hallazgos de la tabla; «—» = sin hallazgo en esta evaluación.
| Heurística | Respuesta | Estratos | Comunas | Sensibilidades | Concentración | Calidad | Construcciones | Fuentes |
|---|---|---|---|---|---|---|---|---|
| H1 Visibilidad del estado | F-01, F-02, F-12 | F-02, F-03, F-04, F-12, F-14 | F-02, F-03, F-04, F-12 | F-02, F-12, F-14 | F-01, F-02, F-12 | F-02, F-03, F-12 | F-02, F-03, F-04, F-12, F-14 | F-01, F-02, F-03, F-12 |
| H2 Relación con el mundo real | F-07 | F-07 | F-07 | F-07 | F-07 | F-07 | F-07, F-13 | — |
| H3 Control y libertad | F-02 | F-02 | F-02 | F-02 | F-02 | F-02 | F-02 | F-02 |
| H4 Consistencia y estándares | F-11 | F-11 | F-11 | F-08, F-11 | F-11 | F-11 | F-08, F-11 | F-08, F-11 |
| H5 Prevención de errores | — | — | — | — | — | — | — | — |
| H6 Reconocimiento antes que recuerdo | — | — | — | — | F-09 | — | — | — |
| H7 Flexibilidad y eficiencia | — | — | — | — | — | — | F-10 | — |
| H8 Diseño estético y minimalista | — | — | — | F-06 | — | — | — | — |
| H9 Ayudar a recuperarse de errores | — | — | — | — | — | — | — | — |
| H10 Ayuda y documentación | — | F-05 | F-05 | — | — | — | — | — |
H5 y H9 quedan sin hallazgos porque el panel es de solo lectura y, en las capturas, ninguna página mostró un error; cómo se comporta ante un fallo de la API se prueba con `AppTest` (`docs/panel/pruebas_panel.md`), no con esta evaluación.

## 5. Resumen por severidad
- **Severidad 3 (mayor):** F-01, F-02, F-03, F-04, F-07.
- **Severidad 2 (menor):** F-05, F-06, F-08, F-09, F-10, F-11, F-12.
- **Severidad 1 (cosmético):** F-13, F-14.
- Cuatro de los cinco hallazgos mayores dependen del ancho de pantalla (1024 y 390 px); a 1400 px el panel se ve completo.

## Reevaluación tras los ajustes
**Qué es:** una segunda pasada **del propio equipo**, con la misma medición, sobre el panel ya modificado (decisiones D87 a D90). Es una **iteración técnica a partir de esta evaluación heurística**: no la hicieron personas usuarias y no cuenta para 6.1, 6.2, 6.3, 6.5 ni 7.4. Tomamos de nuevo las 24 capturas (8 páginas en 1400, 1024 y 390 px), los tiempos y los contrastes con `scripts/evidencias/evidencia_capturas_ajustes.py`: el «antes» está en EV-073 a EV-076 y el «después» en EV-077 a EV-079; EV-080 evalúa F-11. Abrimos las 24 capturas «después» una por una: no hay texto tapado, ni avisos de error, ni rutas, ni nombres de usuario; las únicas columnas cortadas son las de las tablas que llevan su aviso de desplazamiento. La severidad de después es otra estimación nuestra.

| Id | Severidad antes → después | Qué cambió | Qué vimos después (evidencia) |
|---|---|---|---|
| **F-01** | 3 → 0 | Tarjetas de dos en dos y etiquetas cortas. | 0 elementos con texto recortado en las 24 capturas, contra 13 a 1024 px antes (EV-073 y EV-077); la cifra de la respuesta se lee completa. |
| **F-02** | 3 → 0 | La barra lateral pasó a `initial_sidebar_state="auto"`. | A 390 px la página empieza en el contenido y la barra queda plegada con su botón (EV-077). |
| **F-03** | 3 → 2 | Aviso «Tabla ancha…» encima de toda tabla de cuatro columnas o más. | El aviso aparece, pero las tablas siguen cortándose y hay que deslizarlas: dos contenedores a 390 px y uno a 1024 px (Fuentes). Por eso queda en 2. |
| **F-04** | 3 → 0 | Barras horizontales con un paso fijo por barra y etiquetas sin ocultar; título corto; leyenda en dos columnas. | Se ven las seis etiquetas de Estratos y las siete de Comunas a 390 px, y el título de Construcciones cabe (EV-077). |
| **F-05** | 2 → 0 | Pie que explica la línea y las rayas del intervalo. | El pie está bajo cada gráfico de barras y bajo el de Sensibilidades. Al revisar el código vimos que las rayas eran los límites del intervalo de Wilson y no las cotas por «sin datos». |
| **F-07** | 3 → 2 | Glosario común, en un desplegable al final de cada página. | Las 8 páginas lo muestran (EV-077). Que se entienda no lo sabemos sin personas. |
| **F-12** | 2 → 0 | Texto más oscuro (`#0B141C`) y color propio para los textos de los gráficos (`#4A5560`). | Pies 4,86 a 1 (antes 4,05) y textos de los gráficos 7,61 a 1 (antes 3,72) (EV-075 y EV-079). |
| **F-13** | 1 → 0 | Cuatro decimales con coma y rótulo «grados decimales». | Los ejes de la dispersión dicen «3,4400» y «Latitud (grados decimales)» (EV-077). |
| **F-06, F-08, F-09, F-10** | 2 → 2 | Nada: aplazados (D87). | Sin cambio. |
| **F-11** | 2 → 2 | Nada: evaluado y aplazado por una razón técnica. | Streamlit 1.67.0 escribe esos textos dentro de su front y no ofrece opción de idioma ni forma de ocultarlos (EV-080). |
| **F-14** | 1 → 1 | Nada: aplazado. | Los tiempos varían más entre corridas que lo que podríamos atribuir a un cambio (ver abajo). |

**Resumen por severidad después de los ajustes.**
- **Severidad 3 (mayor):** ninguna (antes cinco: F-01, F-02, F-03, F-04, F-07).
- **Severidad 2 (menor):** F-03, F-06, F-07, F-08, F-09, F-10, F-11.
- **Severidad 1 (cosmético):** F-14.
- **Severidad 0 (ya no es un problema):** F-01, F-02, F-04, F-05, F-12, F-13.

**Tiempos de dibujo** (EV-078, mediana de 5 medidas por página y ancho; medición local de una máquina). Con gráfico: de 1,5 a 2,0 s a 1400 px (Estratos 1.977 ms, Comunas 1.691, Sensibilidades 1.539, Construcciones 1.940) y entre 1,6 y 1,9 s a 390 px; sin gráfico: de 0,7 a 1,0 s; Respuesta, 264 ms a 1400 px. En la corrida de «antes» (EV-074) las páginas de Estratos, Comunas y Sensibilidades a 1400 px dieron 0,6 s y Construcciones 3.044 ms, y en la medición original (EV-067) entre 1,1 y 2,1 s. **No sacamos ninguna conclusión de rapidez:** la variación entre corridas de la misma página es mayor que cualquier efecto que podamos atribuir a los cambios, así que no afirmamos que mejoraron ni que empeoraron.

**Qué NO demuestra esta reevaluación:** que las personas usuarias vean mejor el panel, que entiendan el glosario o los intervalos, que la severidad de después coincida con la que sentirían, que el panel cumpla un nivel de accesibilidad ni que los tiempos sean los de otro equipo. Todo lo que dependa de personas sigue pendiente de las sesiones ([protocolo_sesiones.md](protocolo_sesiones.md)).

## Alcance y límites
- **Qué afirmamos:** cada hallazgo sale de una captura o de una medición guardada como evidencia; la evaluación original no corrigió ninguno, y las correcciones y su reevaluación están en la sección anterior.
- **Con qué evidencia:** EV-066 a EV-069 y `scripts/evidencias/evidencia_capturas_anchos.py`, `evidencia_capturas_movil.py` (evaluación original); EV-073 a EV-080 y `evidencia_capturas_ajustes.py` (reevaluación).
- **Qué NO afirmamos:** que estos sean todos los problemas, que las severidades coincidan con lo que vería una persona real, que el panel cumpla un nivel de accesibilidad ni que alguien lo haya usado.

---
Uso de IA: ver DECLARACION_USO_IA.md
Revisión del equipo: pendiente
