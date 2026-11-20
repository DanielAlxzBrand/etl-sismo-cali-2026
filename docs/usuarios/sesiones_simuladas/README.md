# Sesiones simuladas

> **Sesión simulada, no realizada con una persona real.** Todo lo que se guarde en esta carpeta es un ensayo del proceso entre nosotros: nadie usó el panel como persona usuaria y nada se midió. No cuenta como sesión real; cuenta como evidencia simulada bajo la excepción D111, no es feedback de personas usuarias y no entra en `../resultados.md`.

**Hoy esta carpeta tiene las plantillas, dos registros de la etapa 1 en texto** ([`participante_simulado_1_etapa_1.md`](participante_simulado_1_etapa_1.md), perfil `habitante`, y [`participante_simulado_2_etapa_1.md`](participante_simulado_2_etapa_1.md), perfil `institucional`, los dos del 2026-11-18) **y las filas de los dos participantes** en [`registro.csv`](registro.csv) y [`cuestionarios.csv`](cuestionarios.csv) (6 filas de tareas y 1 de cuestionario por participante). Ninguna cifra se midió: todas valen «simulado, no medido», no hay tiempos ni respuestas de cuestionario, y no se inventan (D109).

## Qué se incorporó y qué está pendiente
| Participante | Registro de la etapa 1 | `registro.csv` y `cuestionarios.csv` |
|---|---|---|
| Participante simulado 1 (`habitante`) | incorporado, con sus correcciones posteriores (C1 a C8) y su reconciliación independiente | incorporados el 2026-11-20, tomados de los bloques B y C del texto original de la etapa 2 |
| Participante simulado 2 (`institucional`) | incorporado, con sus correcciones posteriores (C1 a C3) | incorporados, tomados de los bloques B y C del texto original de la etapa 2 |

Solo se incorpora lo que se tiene completo y en su versión original: **un informe sobre una sesión no sustituye al texto de la sesión**, y no reconstruimos uno desde el otro. Los textos originales completos, los mensajes enviados, los comandos, las capturas y los informes de la ejecución quedan fuera del repositorio; sus sha256 están citados en el documento de declaración de la raíz.

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
- **Registro de la etapa 1:** `participante_simulado_N_etapa_1.md`, con el rótulo «Sesión simulada, no realizada con una persona real», el texto sin cambios (solo se limpian saltos de línea y artefactos de copiado, y se dice cuáles), los sha256 del texto antes y después de limpiar y, aparte, las correcciones posteriores; el registro nunca se reescribe.

## Cómo se usa
1. Copiar `plantilla_registro.csv` como `registro.csv` (y, si hace falta, el mismo formato para `cuestionarios.csv`, con las columnas de `../sesiones_reales/plantilla_cuestionarios.csv`) y llenar una fila por tarea (`T1` a `T6` del [guion](../guion_sesion.md)). La [plantilla en texto](plantilla_registro.md) explica cada campo.
2. Correr `python scripts/usuarios/analizar_sesiones.py --simuladas`; escribe [`../resultados_sesiones_simuladas.md`](../resultados_sesiones_simuladas.md), que cuenta lo registrado y no calcula tasas, tiempos ni puntuaciones.

## Qué NO demuestra
Que el panel sea usable, que alguien lo haya usado ni que se haya hecho una sesión con personas usuarias: los ítems 6.1, 6.2, 6.3, 6.5 y 7.4 solo están en «Cumple con matiz» por la excepción D111 (evidencia simulada, sin personas reales), nunca en «Cumple», y el README sigue diciendo «aún sin sesiones reales».
