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

**No se anota ninguna cifra:** una sesión simulada no se hizo con una persona real y no midió nada. Si alguna vez hay una sesión con una persona real, va en [`../sesiones_reales/`](../sesiones_reales/README.md) con `origen = real`.
