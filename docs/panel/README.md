# Panel de solo lectura

**Ítems del checklist:** 3.1 «Construimos componentes de UI/Frontend y dashboards interactivos para la visualización de datos e interacción del usuario.», 3.2 «Integramos el Frontend con los endpoints de API del Backend de manera modular y eficiente.» y 5.3 «Probamos la integración entre interfaz, lógica de negocio y almacenamiento.» · **Criterios del MVP:** AC28 y AC29 de [05_mvp_criterios_aceptacion.md](../estrategia/05_mvp_criterios_aceptacion.md).

El panel es una interfaz Streamlit (`src/panel/`) que muestra los resultados de Gold hablando **solo con la API** por HTTP (solo GET). No abre bases ni archivos de datos, no lee `.env` ni maneja credenciales, y no se despliega: se ejecuta en esta máquina (127.0.0.1).

| Documento | Qué contiene |
|---|---|
| [guia_de_uso.md](guia_de_uso.md) | cómo ejecutarlo, qué muestra cada página, cómo leer los intervalos y los avisos, y qué no se puede concluir |
| [arquitectura_panel.md](arquitectura_panel.md) | capas, módulos, flujo de una consulta, errores, seguridad y límites, con su diagrama |
| [trazabilidad_ui.md](trazabilidad_ui.md) | componente → ruta de la API → campo → archivo de salida → KPI → pregunta de negocio (generado) |
| [pruebas_panel.md](pruebas_panel.md) | qué cubre cada tipo de prueba y los resultados leídos de las evidencias |
| [accesibilidad_y_respuesta.md](accesibilidad_y_respuesta.md) | contrastes calculados, mediciones locales y lo que queda pendiente porque depende de personas usuarias |

## Cómo ejecutarlo
```powershell
.\.venv\Scripts\python.exe scripts\panel\ejecutar_panel.py
```
Arranca la API y el panel, imprime las dos direcciones y los cierra con Ctrl+C. La evidencia de una ejecución real está en [EV-052](../evidencias/panel/EV-052_ejecucion_real.txt).

## Evidencias (`docs/evidencias/panel/`)
EV-051 instalación de Streamlit sin tocar la línea base · EV-052 ejecución real con el lanzador · EV-053 equivalencia de los datos entre SQLite y MySQL · EV-054 capturas automatizadas de las ocho páginas · EV-055 mediciones locales · EV-056 comprobación canario · EV-057 contrastes · EV-058 a EV-060 imágenes generadas desde las salidas · EV-061 pruebas en un clon limpio.

## Alcance y límites
- **Qué afirmamos:** el panel muestra las cifras de Gold tal como las sirve la API, con el alcance visible en cada página; los valores coinciden con las salidas del pipeline y con los dos almacenamientos.
- **Qué NO afirmamos:** que la interfaz sea usable para personas reales (no se hicieron sesiones reales con usuarios; las dos simuladas no lo son), que esté desplegada ni que sirva para decidir sobre una comuna concreta: describe esta muestra.
