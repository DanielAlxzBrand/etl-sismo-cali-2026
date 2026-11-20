# Sesión simulada, no realizada con una persona real

Plantilla de registro de una sesión simulada (D109). Se copia a `registro.csv` en esta carpeta; la plantilla no se edita. El archivo [`plantilla_registro.csv`](plantilla_registro.csv) trae las mismas columnas y una fila de ejemplo.

| Campo | Qué va |
|---|---|
| `participante` | `Participante simulado N` (N es un número: 1, 2, 3…) |
| `perfil` | el perfil que se ensaya, por ejemplo `otro` |
| `fecha` | AAAA-MM-DD del ensayo |
| `tarea` | `T1` a `T6` del [guion](../guion_sesion.md) |
| `resultado` | exactamente `simulado, no medido` |
| `tiempo_s` | exactamente `simulado, no medido` |
| `ayudas` | exactamente `simulado, no medido` |
| `errores` | exactamente `simulado, no medido` |
| `comentario_breve` | una frase sin nombres; si lleva una coma, entre comillas dobles |
| `origen` | siempre `simulada` |

## Cuestionarios (`cuestionarios.csv`) y las estimaciones del SUS y del CSAT (D112)
Las columnas son las de [`../sesiones_reales/plantilla_cuestionarios.csv`](../sesiones_reales/plantilla_cuestionarios.csv); `participante`, `perfil` y `fecha` van como arriba y `origen` es siempre `simulada`. Los diez ítems del SUS (`sus_1` a `sus_10`) y el `csat` valen **todos** `simulado, no medido` **o todos** `simulado: N`, con N un entero de 1 a 5: la estimación de la persona simulada, nunca una medición. El prefijo `simulado:` es obligatorio. El `resultado`, el `tiempo_s`, las `ayudas` y los `errores` del registro **siguen valiendo `simulado, no medido`**. `python scripts/usuarios/analizar_sesiones.py --simuladas` imprime las puntuaciones que salen de esas estimaciones siempre con la marca `simulado:` y solo con filas simuladas; el análisis de `sesiones_reales/` rechaza cualquier valor simulado.

**No se anota ninguna cifra medida:** una sesión simulada no se hizo con una persona real y no midió nada; las únicas cifras permitidas son las estimaciones `simulado: N` del SUS y del CSAT, que no son mediciones. Si alguna vez hay una sesión con una persona real, va en [`../sesiones_reales/`](../sesiones_reales/README.md) con `origen = real`.
