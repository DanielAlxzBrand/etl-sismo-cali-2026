# Guía de uso del panel

## 1. Cómo ejecutarlo
**Un comando** (PowerShell, en la raíz del repositorio, con el entorno virtual del proyecto):
```powershell
.\.venv\Scripts\python.exe scripts\panel\ejecutar_panel.py
```
El lanzador arranca la API y el panel en 127.0.0.1, espera a que respondan, imprime las dos direcciones (por defecto la API en el puerto 8000 y el panel en el 8501; si están ocupados elige otros libres) y, con Ctrl+C, cierra los dos procesos. Con `--almacenamiento mysql` la API sirve los datos desde MySQL; con `--verificar` arranca, comprueba la salud y cierra.

**Por separado** (dos terminales):
```powershell
.\.venv\Scripts\python.exe -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000
.\.venv\Scripts\python.exe -m streamlit run src/panel/app.py
```
La dirección de la API que usa el panel está en `config/config.yaml` (clave `panel.api_url`); solo se admiten direcciones locales.

## 2. Qué muestra cada página
Todas tienen el mismo marco: título, la pregunta de negocio que responden, el estado de la API con su almacenamiento y la fecha de corte, el **recuadro de alcance** y, al pie, la fuente y las licencias.

| Página | Qué responde | Qué hay en ella |
|---|---|---|
| Respuesta | ¿Se detecta diferencia entre los estratos 3-5 y 1-2? | las dos tasas, la diferencia con su intervalo de Newcombe, la razón, una lectura generada y el resumen de la calidad de la unión |
| Estratos (K1) | ¿Qué tan segura es la tasa de cada estrato? | gráfico de barras con barras de error, tabla con casos, sin datos y cotas, y una lectura generada |
| Comunas (K6) | ¿Cómo se reparte la tasa por comuna? | gráfico y tabla por comuna, composición por grupo de estrato y qué comuna concentra los estratos 1-2 |
| Sensibilidades (S0 a S5) | ¿Cambia la conclusión según el filtro o la definición de daño? | la diferencia por escenario con su intervalo, la razón ajustada por comuna con su advertencia y una lectura por escenario |
| Concentración (K3 y K4) | ¿Se concentran los casos en pocos barrios? | los barrios con más casos y su participación, y la correlación de Spearman |
| Calidad de la llave | ¿Qué tan confiable es la unión con el estrato? | cobertura de la llave, estrato válido, nombre validado y los códigos por revisar |
| Construcciones | ¿Qué hay detrás de las cifras? | tabla paginada con filtros, dispersión de ubicaciones y descarga en CSV de lo mostrado |
| Fuentes y sistema | ¿De dónde salen los datos y qué no se puede concluir? | fuentes con licencia y fechas, estado del sistema, los puntos de «qué no se puede concluir» y las limitaciones del panel |

## 3. Cómo leer los números
- **Tasa:** construcciones con cambio satelital severo (severo estricto, proxy de daño) entre las que tienen datos satelitales. Las construcciones sin datos no cuentan como «sin daño»: se informan aparte.
- **Intervalo de Wilson (barras de error):** muestra la incertidumbre de una tasa en esta muestra. Un intervalo ancho significa que la tasa se conoce poco.
- **Intervalo de Newcombe:** es el de la diferencia entre dos tasas. Si incluye 0, el panel escribe «con este proxy y esta muestra no se detecta diferencia»; eso no significa que el estrato no influya.
- **Muestra baja:** el grupo tiene pocos casos severos; se muestra, pero no se ordena frente a otros. Se marca con el texto «muestra baja», no solo con el color.
- **Cotas por «sin datos»:** valores extremos si todas las construcciones sin datos fueran sin daño o con daño; no son estimaciones. Si las cotas de dos grupos se solapan, el orden entre ellos no es identificable.
- **Formato:** coma decimal, punto de miles y signo menos «−»; las diferencias se dan en puntos porcentuales (pp).

## 4. Avisos y errores
Si la API está apagada, tarda demasiado o su almacenamiento no está disponible, cada página muestra un aviso en español con el motivo y mantiene visible el alcance; nunca muestra una traza. Al volver la API, basta recargar la página (un fallo no queda guardado en la caché).

## 5. Qué no se puede concluir
La página «Fuentes y sistema» lista los puntos; en resumen: el indicador mide cambio visible desde satélite y no sustituye una inspección; solo hay las comunas de la muestra y las tasas no se extrapolan a Cali; los estratos con muchas construcciones sin datos y los grupos con muestra baja no se ordenan; el estrato se asignó al barrio y es anterior al evento; la definición ampliada de daño es de baja confianza; una asociación no establece causalidad; y el grupo de estratos 1-2 está formado casi por completo por muy pocas comunas, de modo que comparar estratos es, en la práctica, comparar comunas.

## 6. Alcance y límites
- **Qué afirmamos:** la guía describe lo que el panel muestra hoy y cómo leerlo.
- **Qué NO afirmamos:** que una persona sin formación estadística entienda los intervalos a la primera; eso solo lo dirán las sesiones con usuarios, que no se han hecho.
