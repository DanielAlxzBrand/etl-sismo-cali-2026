# Sesiones simuladas

> **Sesión simulada, no realizada con una persona real.** Todo lo que se guarde en esta carpeta es un ensayo del proceso entre nosotros: nadie usó el panel como persona usuaria y nada se midió. No cuenta para ningún ítem del checklist, no es feedback de personas usuarias y no entra en `../resultados.md`.

**Hoy esta carpeta solo tiene plantillas.** No hay participantes simulados, tiempos ni respuestas registradas, y no se inventan (D109).

## Cómo se separa de lo demás
| Carpeta | Qué son los datos | Valor de `origen` | Qué lee el script |
|---|---|---|---|
| [`../sesiones_reales/`](../sesiones_reales/README.md) | sesiones con personas usuarias reales | `real` | `analizar_sesiones.py` |
| `sesiones_simuladas/` (esta) | sesiones simuladas, no realizadas con una persona real | `simulada` | `analizar_sesiones.py --simuladas` |
| [`../simulacion/`](../simulacion/README.md) | datos sintéticos que genera un script con semilla fija para probar el análisis | `sintetico` | `analizar_sesiones.py --simulado` |

Cada carpeta rechaza las filas de las otras: una fila `simulada` en `sesiones_reales/` hace fallar el script y una `real` aquí también. Una prueba comprueba que `sesiones_reales/` no contiene nada simulado.

## Qué se registra
- **Participantes:** `Participante simulado 1`, `Participante simulado 2`… (nunca `P01`, que es el código de una persona real).
- **Cifras:** `resultado`, `tiempo_s`, `ayudas`, `errores`, las diez respuestas del SUS y el CSAT valen exactamente `simulado, no medido`. El script rechaza un número de verdad en esta carpeta, porque una cifra escrita aquí parecería una medición y no lo es.
- **Origen:** siempre `simulada`.
- **Comentario breve:** lo que el equipo quiera anotar del ensayo, sin nombres.

## Cómo se usa
1. Copiar `plantilla_registro.csv` como `registro.csv` (y, si hace falta, el mismo formato para `cuestionarios.csv`, con las columnas de `../sesiones_reales/plantilla_cuestionarios.csv`) y llenar una fila por tarea (`T1` a `T6` del [guion](../guion_sesion.md)). La [plantilla en texto](plantilla_registro.md) explica cada campo.
2. Correr `python scripts/usuarios/analizar_sesiones.py --simuladas`; escribe [`../resultados_sesiones_simuladas.md`](../resultados_sesiones_simuladas.md), que cuenta lo registrado y no calcula tasas, tiempos ni puntuaciones.

## Qué NO demuestra
Que el panel sea usable, que alguien lo haya usado ni que se haya hecho una sesión con personas usuarias: los ítems 6.1, 6.2, 6.3, 6.5 y 7.4 siguen como antes, y el README sigue diciendo «aún sin sesiones reales».
