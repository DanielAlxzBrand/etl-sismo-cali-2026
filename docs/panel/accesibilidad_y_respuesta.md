# Accesibilidad técnica y tiempos de respuesta del panel

Este documento reúne **mediciones y verificaciones técnicas** reutilizables. No cierra el ítem 3.3 del checklist (usabilidad, capacidad de respuesta y coherencia visual): ese ítem necesita sesiones con personas usuarias, que no se han hecho.

## 1. Contrastes calculados
Relación de contraste según la fórmula de luminancia relativa de WCAG 2.x, calculada con `python scripts/panel/contraste.py` ([EV-057](../evidencias/panel/EV-057_contrastes.txt)). Se informan los valores; no se declara un nivel de conformidad.

| Par | Relación | Supera 3 | Supera 4,5 | Supera 7 |
|---|---|---|---|---|
| texto sobre el fondo (`#1F2933` sobre `#FFFFFF`) | 14,76 a 1 | sí | sí | sí |
| texto sobre el fondo secundario (`#F0F4F8`) | 13,35 a 1 | sí | sí | sí |
| color principal, barras y puntos (`#0072B2`) | 5,19 a 1 | sí | sí | no |
| color secundario, muestra baja y línea de cero (`#D55E00`) | 3,87 a 1 | sí | no | no |
| color de apoyo, clase de daño (`#009E73`) | 3,42 a 1 | sí | no | no |
| color neutro, clase sin cambio (`#595959`) | 7,0 a 1 | sí | sí | sí |
| principal frente al secundario | 1,34 a 1 | no | no | no |

**Lectura.** Los colores de los gráficos superan 3 a 1 sobre el fondo; el principal y el secundario casi no se distinguen por luminosidad entre sí, por eso el significado nunca depende solo del color: la muestra baja se rotula con texto en la leyenda, en el eje y en la tabla, y las clases de daño se distinguen además por la forma del punto. **No se calculó** el contraste del texto secundario (pies y subtítulos) ni de los rótulos de los ejes, que dibujan Streamlit y Vega con sus propios grises.

## 2. Otras verificaciones técnicas
- Todos los gráficos tienen título, ejes con unidad y un pie que explica qué es el intervalo; llevan una descripción para lectores de pantalla (`description` de la especificación).
- Los números de los ejes usan coma decimal; los textos están en español.
- Ningún componente depende de recursos externos: el panel funciona sin conexión a Internet.
- Las ocho páginas se revisaron una por una en las capturas automatizadas de [EV-054](../evidencias/panel/EV-054_capturas_panel.txt) (ancho de 1400 px): sin texto cortado, sin avisos de error y con el recuadro de alcance visible.

## 3. Tiempos de respuesta (mediciones locales de una máquina)
[EV-055](../evidencias/panel/EV-055_mediciones_panel.txt) y [su CSV](../evidencias/panel/EV-055_mediciones_panel.csv): latencia del cliente del panel por ruta (5 de calentamiento y 30 mediciones) y tiempo de renderizado de cada página con `AppTest` (1 de calentamiento y 7 mediciones). **Son valores de este equipo, con la API local; no describen una máquina distinta ni un despliegue.** Imagen: [EV-058](../evidencias/panel/EV-058_latencias_cliente.png).

| Medición | SQLite (mediana) | MySQL (mediana) |
|---|---|---|
| Latencia de las rutas de la API leídas por el panel | de 3,6 a 13,9 ms | de 74,8 a 126,9 ms (las rutas `/fuentes` y `/calidad` no consultan el almacén y responden en menos de 12 ms con los dos) |
| Renderizado de una página, incluida la lectura de la API | de 389 a 537 ms | de 647 a 881,5 ms |

La diferencia entre almacenamientos viene de que la API abre una conexión a MySQL en cada solicitud (decisión D52). No se midió el tiempo en un navegador ni la red hacia una persona.

## 4. Lo que queda pendiente porque depende de personas usuarias
- Usabilidad, comprensión de los intervalos y de los avisos, tiempo para completar tareas y satisfacción: requieren sesiones con usuarios reales.
- Coherencia visual percibida y adecuación a lectores de pantalla en uso real.
- Todo esto es del ítem 3.3 y del componente de usuarios, UX y finanzas; aquí no se simula ni se inventa ninguna cifra.

## 5. Alcance y límites
- **Qué afirmamos:** los contrastes calculados, los tiempos medidos en este equipo y las revisiones técnicas descritas.
- **Qué NO afirmamos:** conformidad con un nivel de accesibilidad, usabilidad medida con personas ni rendimiento en otro equipo.
