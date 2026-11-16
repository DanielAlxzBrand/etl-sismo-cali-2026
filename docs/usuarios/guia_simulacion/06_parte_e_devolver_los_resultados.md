{{para: facilitador}}
{{sin-salto}}
# Parte E · Devolver los resultados

Cuando termine cada sesión, los resultados se juntan en una sola persona, que los une y ejecuta el análisis. Esta parte dice qué se devuelve, cómo se asegura de que no lleve nombres y qué hace quien junta. Una persona junta y no cada una por su lado, porque el script de análisis lee un solo `registro.csv` y un solo `cuestionarios.csv`.

## E1. Qué se devuelve de cada sesión
| Archivo | Formato | Se devuelve |
|---|---|---|
| `registro_P0X.csv` | CSV en UTF-8, seis filas | Sí |
| `cuestionarios_P0X.csv` | CSV en UTF-8, una fila | Sí |
| `friccion_P0X.csv` | CSV en UTF-8, una fila por fricción; solo si hubo | Sí, si existe |
| Hoja de sesión | texto o foto de la hoja **sin nombres** | Sí |
| Capturas | PNG sin nombre de usuario ni barra de tareas | Solo si las tomó |
| Consentimiento firmado y tabla de códigos | — | **Nunca** |

## E2. Revise que no haya nombres
Antes de mandar nada, abra cada archivo en un editor de texto (por ejemplo, el Bloc de notas) y busque, con Ctrl+F, **nombres de personas, correos, el nombre de usuario de Windows y rutas de carpetas**. Si encuentra alguno, bórrelo del archivo. Haga lo mismo con la hoja de sesión y mire cada captura. Esto no es una formalidad: lo que llegue al proyecto no se puede retirar del historial de Git una vez guardado.

## E3. Cómo se manda
Por el canal privado del equipo, a la persona que junta: los archivos de la sesión en un solo envío, sin renombrarlos. Los archivos solo traen códigos, pero **no se publican** ni se suben a un servicio público.

## E4. Qué hace quien junta
Trabaje en la raíz del proyecto, con las carpetas de los envíos en un lugar propio fuera de él (aquí lo llamamos `<carpeta de recibidos>`). Los comandos copian las plantillas como `registro.csv` y `cuestionarios.csv`, agregan debajo las filas de cada sesión (sin repetir el encabezado) y revisan que el resultado tenga el encabezado y el número de filas esperados:
```powershell
$destino = "docs\usuarios\sesiones_reales"
Copy-Item "$destino\plantilla_registro.csv" "$destino\registro.csv"
Copy-Item "$destino\plantilla_cuestionarios.csv" "$destino\cuestionarios.csv"
Get-ChildItem "<carpeta de recibidos>" -Filter "registro_P*.csv" | ForEach-Object { Get-Content -Encoding UTF8 $_.FullName | Select-Object -Skip 1 | Add-Content -Encoding UTF8 "$destino\registro.csv" }
Get-ChildItem "<carpeta de recibidos>" -Filter "cuestionarios_P*.csv" | ForEach-Object { Get-Content -Encoding UTF8 $_.FullName | Select-Object -Skip 1 | Add-Content -Encoding UTF8 "$destino\cuestionarios.csv" }
(Get-Content "$destino\registro.csv").Count
(Get-Content "$destino\cuestionarios.csv").Count
```
Las dos últimas líneas escriben cuántas líneas tiene cada archivo: con las tres sesiones completas, `registro.csv` debe tener **19** (el encabezado y 18 filas) y `cuestionarios.csv` **4** (el encabezado y 3 filas). Después, ejecute el análisis:
```powershell
.\.venv\Scripts\python.exe scripts\usuarios\analizar_sesiones.py
```
El script escribe `docs/usuarios/resultados.md`. Con menos de 5 personas muestra «k de n» y **no** porcentajes. Si una fila no cumple el formato, el script lo dice con el número de fila y termina con código 2: corrija el archivo de esa sesión y vuelva a juntar.

Las fricciones (`friccion_P0X.csv`) no entran al análisis: quien junta las copia, una a una, al final de `docs/usuarios/registro_de_friccion.csv`, con su número definitivo, y se anotan en el [registro de fricciones](../registro_de_friccion.md).

## E5. Qué se hace después
1. **Fricción → decisión.** El equipo lee cada fricción nueva y llena `decision` (`corregir`, `aplazar` o `descartar`) **con su razón**; no se decide sin escribir por qué.
2. **Decisión → corrección.** Lo que se decide corregir se cambia en el panel en un commit pequeño, con una captura **antes** y otra **después** y la prueba que lo comprueba, y se anota en la tabla de cambios del proyecto.
3. **Qué estados cambian** lo decide el equipo con la regla de estado del checklist y con los límites que dice la sección «Qué no demuestra este procedimiento». Esta guía no cambia ningún estado.
