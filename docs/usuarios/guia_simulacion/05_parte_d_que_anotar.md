{{para: facilitador}}
# Parte D · Qué anotar

Esta parte dice qué se anota durante y después de la sesión, en qué formato y dónde se guarda. Lo escribimos con el formato exacto porque el script de análisis rechaza una fila que no lo cumpla, y es mejor enterarse en la sesión que al juntar los resultados. Todo lo que se anota lleva **solo el código** de la persona (`P01`, `P02`, `P03`): nunca su nombre.

## D1. El consentimiento
Antes de empezar, lea en voz alta este texto. Sin un «sí» claro, la sesión no empieza.

{{incluir: docs/usuarios/consentimiento.md#texto-que-se-lee-en-voz-alta-y-que-si-se-firma-se-da-en-papel}}

**Dónde se guarda.** Si la persona firma una copia, y la tabla que une cada código con su nombre, **se guardan en una carpeta suya, fuera de la carpeta del proyecto**, y no se mandan con los resultados ni se suben al proyecto. Quien participa también puede decir que sí de palabra: en ese caso se anota en la hoja de sesión que se leyó y se aceptó de palabra.

**A quién se puede invitar.** Estas sesiones son entre personas del equipo. Aun así, nadie participa por presión: si alguien prefiere no hacerlo, no se hace.

## D2. La hoja de sesión
Es una hoja por sesión, que llena quien facilita; está en blanco en los anexos y se puede imprimir. Guarda lo que no cabe en los CSV. Qué lleva:
| Campo | Qué se anota |
|---|---|
| Código y número de sesión | `P01`, `P02` o `P03` y 1, 2 o 3 |
| Fecha y hora de inicio y de cierre | la de la sesión (formato AAAA-MM-DD) |
| Roles | «facilita y anota: la misma persona»; el código de quien participa; **ningún nombre** |
| Perfil | el que la persona diga que la describe mejor, entre `institucional`, `habitante`, `academico` u `otro`; entre personas del equipo normalmente es `otro` y no se fuerza |
| Exposición previa a las tareas | **cuatro respuestas, sí o no:** ¿facilitó una sesión antes de participar? ¿leyó o abrió el guion o las tareas antes? ¿abrió `docs/usuarios/`? ¿abrió alguna página del panel más allá de comprobar que carga? |
| Quien facilita | ¿construyó o escribió páginas del panel? (sí o no) |
| Incidencias técnicas | qué falló, en qué minuto y cómo se resolvió; **no cuentan como fricción** |
| Retiro | si la persona se retiró, se anota «una persona se retiró» y se borran sus filas |
| Observaciones | lo que le llamó la atención, sin nombres |

## D3. El registro por tarea
Es un archivo por sesión: `registro_P01.csv` (y así `P02`, `P03`). Una fila por tarea, seis filas por persona. Encabezado exacto, que ya trae la plantilla del proyecto:

{{codigo: docs/usuarios/sesiones_reales/plantilla_registro.csv | csv | lineas: 1-1}}

| Columna | Qué escribir |
|---|---|
| `participante` | el código: `P01`, `P02` o `P03` |
| `perfil` | el de la hoja de sesión |
| `fecha` | AAAA-MM-DD |
| `tarea` | `T1` a `T6` |
| `resultado` | exactamente `exito`, `exito_con_ayuda` o `fracaso` |
| `tiempo_s` | segundos que tardó, con el cronómetro, como número |
| `ayudas` | cuántas veces pidió ayuda o se la dio (número, 0 si ninguna) |
| `errores` | clics que lo alejan de la respuesta o respuestas equivocadas que corrige (número, 0 si ninguno) |
| `comentario_breve` | una frase **sin nombres**; si lleva una coma, la frase va entre comillas dobles |
| `origen` | siempre `real` |

**EJEMPLO SINTÉTICO: no son personas ni una sesión.** Son las primeras filas de los datos de práctica del proyecto (`docs/usuarios/simulacion/registro.csv`), que usan el código `S01` y el origen `sintetico`. En una sesión real el código sería `P01` y el origen `real`:

{{codigo: docs/usuarios/simulacion/registro.csv | csv | lineas: 1-4}}

## D4. Los cuestionarios
Es un archivo por sesión, `cuestionarios_P01.csv`, con **una fila por persona**: diez respuestas del SUS (de 1 a 5), el CSAT (de 1 a 5) y el origen. Encabezado exacto:

{{codigo: docs/usuarios/sesiones_reales/plantilla_cuestionarios.csv | csv | lineas: 1-1}}

**EJEMPLO SINTÉTICO** (datos de práctica, código `S01`):

{{codigo: docs/usuarios/simulacion/cuestionarios.csv | csv | lineas: 1-2}}

La persona marca las respuestas en papel o en voz alta, y usted las copia en el mismo orden de las afirmaciones. Las afirmaciones y la forma de puntuar son estas:

{{incluir: docs/usuarios/instrumentos.md#1-sus-escala-de-usabilidad-del-sistema | solo: tablas}}

{{incluir: docs/usuarios/instrumentos.md#2-csat-satisfacción-con-el-panel}}

## D5. Las fricciones
Una fricción es un momento en que la persona se confunde, se traba o malinterpreta algo del panel. Se anota **solo si la persona participa con su consentimiento y el problema es del panel**, no de la instalación. Es un archivo, `friccion_P01.csv`, con este encabezado exacto:

{{codigo: docs/usuarios/sesiones_reales/plantilla_friccion.csv | csv | lineas: 1-1}}

| Columna | Qué escribir en la sesión |
|---|---|
| `id` | `F-` y un número que siga al último del registro del proyecto; si no lo sabe, deje `F-nuevo` y se numera al juntar |
| `fuente` | `observacion` (lo vio) o `entrevista` (lo dijo en las tres preguntas finales) |
| `participante` | el código |
| `pagina` | la página del panel donde ocurrió |
| `descripcion` | qué pasó y qué frase del panel la confundió, sin nombres |
| `severidad` | de 0 a 4: 0 = no es un problema de usabilidad; 1 = cosmético; 2 = menor; 3 = mayor, conviene arreglarlo pronto; 4 = catastrófico. Es la escala de Nielsen que usa la evaluación heurística del proyecto; aquí es una estimación suya |
| `frecuencia` | en una sola sesión, `1 de 1`; al juntar las tres se recalcula |
| `decision`, `razon`, `cambio`, `antes`, `despues`, `verificacion` | **déjelas vacías**: se llenan después, con el equipo |
| `estado` | `pendiente` |

**EJEMPLO SINTÉTICO** (inventado para mostrar el formato; no es una observación):
```csv
F-nuevo,observacion,S01,Estratos,"Duda sobre qué significa «muestra baja» al leer la tabla",2,1 de 1,,,,,,,pendiente
```

## D6. Qué no anotar
- Nombres, apellidos, correos, teléfonos, fotos, grabaciones y firmas.
- El nombre de usuario de Windows, el nombre del equipo o rutas de carpetas de su equipo: aparecen en capturas y en mensajes de error.
- Notas con el nombre de la persona, aunque sean «para acordarme».
- Contraseñas o cualquier valor de configuración.
- Opiniones de quien facilita sobre la persona («le costó porque no sabe de estadística»): se anota lo que pasó, no por qué.

## D7. Capturas (opcionales)
Si quiere guardar una captura de un momento de confusión, tome solo la ventana del panel, **sin la barra de tareas ni nada que muestre su nombre de usuario**, y guárdela con un nombre como `captura_P01_T3.png` en la carpeta de la sesión. Sin consentimiento claro de la persona, no se toman.

## D8. Dónde se guarda todo
En **una carpeta propia de quien facilita, fuera de la carpeta del proyecto**: los cuatro archivos de la sesión (`registro_P01.csv`, `cuestionarios_P01.csv`, `friccion_P01.csv` y la hoja de sesión) y las capturas. El consentimiento firmado y la tabla de códigos van **aparte**, en otro lugar de esa carpeta o en otra distinta, y nunca se mandan.
