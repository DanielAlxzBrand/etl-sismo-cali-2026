# Accesibilidad técnica y tiempos de respuesta del panel

Este documento reúne **mediciones y verificaciones técnicas** reutilizables. No cierra el ítem 3.3 del checklist (usabilidad, capacidad de respuesta y coherencia visual): ese ítem necesita sesiones con personas usuarias, que no se han hecho.

## 1. Contrastes calculados
Relación de contraste según la fórmula de luminancia relativa de WCAG 2.x, calculada con `python scripts/panel/contraste.py` ([EV-057](../evidencias/panel/EV-057_contrastes.txt), regenerada con la paleta actual). Se informan los valores; no se declara un nivel de conformidad. La regla que adoptamos es de **4,5 a 1 para el texto y 3 a 1 para los elementos gráficos** (D89) y una prueba la comprueba leyendo la configuración.

| Par | Relación | Supera 3 | Supera 4,5 | Supera 7 |
|---|---|---|---|---|
| texto sobre el fondo (`#0B141C` sobre `#FFFFFF`) | 18,57 a 1 | sí | sí | sí |
| texto sobre el fondo secundario (`#F0F4F8`) | 16,8 a 1 | sí | sí | sí |
| pies y subtítulos (Streamlit los pinta al 60 % del texto) | 4,86 a 1 | sí | sí | no |
| texto de ejes y leyendas de los gráficos (`#4A5560`) | 7,61 a 1 | sí | sí | sí |
| color principal, barras y puntos (`#0072B2`) | 5,19 a 1 | sí | sí | no |
| color secundario, muestra baja y línea de cero (`#D55E00`) | 3,87 a 1 | sí | no | no |
| color de apoyo, clase de daño (`#009E73`) | 3,42 a 1 | sí | no | no |
| color neutro, clase sin cambio (`#595959`) | 7,0 a 1 | sí | sí | sí |
| barras de error (color del texto) | 18,57 a 1 | sí | sí | sí |
| principal frente al secundario | 1,34 a 1 | no | no | no |

**Qué cambió.** Antes de los ajustes (F-12) el texto daba 14,76 a 1, los pies 4,05 a 1 y los rótulos de los gráficos 3,72 a 1 (EV-075); ahora el texto es más oscuro y los gráficos tienen un color de texto propio. Medimos también lo que dibuja el navegador en las 8 páginas y 3 anchos ([EV-079](../evidencias/ajustes_ux/EV-079_contraste_texto.txt)): pies 4,86 a 1, rótulos y títulos de ejes y leyendas 7,61 a 1, y el texto de las tablas interactivas no se mide porque se dibuja en un lienzo. Corregimos además una limitación de la medición anterior: un rótulo que el propio gráfico oculta por solaparse (opacidad 0) había dado un contraste de 1,0 que no era real ([EV-076](../evidencias/ajustes_ux/EV-076_contraste_dudoso.txt)).

**Lectura.** Los colores de los gráficos superan 3 a 1 sobre el fondo; el principal y el secundario casi no se distinguen por luminosidad entre sí, por eso el significado nunca depende solo del color: la muestra baja se rotula con texto en la leyenda, en el eje y en la tabla, y las clases de daño se distinguen además por la forma del punto (paleta apta para daltonismo, D74). **No se calcula** cada elemento de la interfaz: solo una muestra por categoría.

## 2. Otras verificaciones técnicas
- Todos los gráficos tienen título, ejes con unidad y un pie que explica qué es el intervalo; llevan una descripción para lectores de pantalla (`description` de la especificación).
- Los números de los ejes usan coma decimal; los textos están en español.
- Ningún componente depende de recursos externos: el panel funciona sin conexión a Internet.
- Las ocho páginas se revisaron una por una en las capturas automatizadas de [EV-054](../evidencias/panel/EV-054_capturas_panel.txt) (ancho de 1400 px): sin texto cortado, sin avisos de error y con el recuadro de alcance visible.
- **Tres anchos.** Tras la evaluación heurística volvimos a capturar las ocho páginas a 1400, 1024 y 390 px ([EV-077](../evidencias/ajustes_ux/EV-077_capturas_anchos.txt)): el documento nunca desborda en horizontal, no hay elementos con texto recortado (a 1024 px había 13, [EV-073](../evidencias/ajustes_ux/EV-073_capturas_anchos.txt)) y quedan tres tablas que se deslizan hacia los lados (Fuentes a 1024 y 390 px, Calidad a 390 px), todas con su aviso de «Tabla ancha». A 390 px la barra lateral empieza plegada.
- Los botones de las tablas y de los gráficos que pone Streamlit siguen en inglés porque la versión fijada no permite traducirlos ni ocultarlos ([EV-080](../evidencias/ajustes_ux/EV-080_controles_de_streamlit.txt)).

## 3. Tiempos de respuesta (mediciones locales de una máquina)
[EV-055](../evidencias/panel/EV-055_mediciones_panel.txt) y [su CSV](../evidencias/panel/EV-055_mediciones_panel.csv): latencia del cliente del panel por ruta (5 de calentamiento y 30 mediciones) y tiempo de renderizado de cada página con `AppTest` (1 de calentamiento y 7 mediciones). **Son valores de este equipo, con la API local; no describen una máquina distinta ni un despliegue.** Imagen: [EV-058](../evidencias/panel/EV-058_latencias_cliente.png).

| Medición | SQLite (mediana) | MySQL (mediana) |
|---|---|---|
| Latencia de las rutas de la API leídas por el panel | de 3,6 a 13,9 ms | de 74,8 a 126,9 ms (las rutas `/fuentes` y `/calidad` no consultan el almacén y responden en menos de 12 ms con los dos) |
| Renderizado de una página, incluida la lectura de la API | de 389 a 537 ms | de 647 a 881,5 ms |

La diferencia entre almacenamientos viene de que la API abre una conexión a MySQL en cada solicitud (decisión D52).

**Tiempo de dibujo en un navegador** ([EV-078](../evidencias/ajustes_ux/EV-078_mediciones_anchos.txt), 1 carga de calentamiento y 5 medidas por página y ancho; SQLite, API y panel en el mismo equipo). Medianas en esa corrida: Respuesta, de 264 ms a 1400 px a 681 ms a 390 px; Concentración, Calidad y Fuentes, de 0,7 a 1,0 s; Estratos, Comunas, Sensibilidades y Construcciones, de 1,5 a 2,0 s. **La variabilidad es grande:** entre el mínimo y el máximo de las cinco medidas de una misma página hay hasta 1,6 s (Estratos a 1400 px: de 1.411 a 3.011 ms), y en otra corrida del mismo código (EV-074) esas páginas a 1400 px dieron 0,6 s. Por eso no usamos estos tiempos para decir que un cambio aceleró o frenó el panel: describen cómo se comportó este equipo ese día.

## 4. Lo que queda pendiente porque depende de personas usuarias
- Usabilidad, comprensión de los intervalos y de los avisos, tiempo para completar tareas y satisfacción: requieren sesiones con usuarios reales.
- Coherencia visual percibida y adecuación a lectores de pantalla en uso real.
- Todo esto es del ítem 3.3 y del componente de usuarios, UX y finanzas; aquí no se simula ni se inventa ninguna cifra.

## 5. Alcance y límites
- **Qué afirmamos:** los contrastes calculados, los tiempos medidos en este equipo (con su variabilidad), las capturas en tres anchos y las revisiones técnicas descritas.
- **Qué NO afirmamos:** conformidad con un nivel de accesibilidad, usabilidad medida con personas ni rendimiento en otro equipo.
