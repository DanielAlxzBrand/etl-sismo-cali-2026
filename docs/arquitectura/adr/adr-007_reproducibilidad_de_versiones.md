# ADR-007: Versiones exactas, pandas fijado en 3.0.6 y Python 3.13 como única versión soportada

**Estado:** Vigente (implementada). **Fecha de la decisión:** 2026-11-13 (D56) y 2026-11-14 (D81). **D de origen:** D56, D81. **Propietario técnico:** Daniel Alexander Brand García. **Revisión:** pendiente.

## Contexto
La línea base se produjo con pandas 3.0.6. Al reinstalar con pandas 3.1.1, `gold_final.csv` cambiaba en 3 celdas del decimal 12 y `etl_sismo.db` en 799 celdas de `indice_escombros` (DEF-011, 2026-11-13; EV-035 es la corrida estable con 3.0.6 tras restaurar la versión). No registramos la magnitud de las 799 celdas. Además, una instalación desde cero con versiones mínimas ya había hecho fallar una prueba, y varios paquetes se usaban sin estar declarados.

## Decisión
- El entorno vuelve a pandas 3.0.6, fijado en `requirements.txt` y en `orquestacion/requirements-airflow.txt`. Una prueba compara las versiones del requisito con las del entorno y otra regenera el pipeline en una copia y exige los nueve archivos de la línea base byte a byte (D56).
- `requirements.txt` fija con `==` todo paquete listado y todo paquete que el código importa. No se fijan las dependencias transitivas. La versión de Python soportada es la 3.13, escrita en el propio archivo y en el README (D81).
- `tests/test_requisitos.py` exige `==` en cada línea y que cada import de terceros de `src/`, `scripts/` y `tests/` esté declarado.

## Consecuencias
### Positivas
- Quien instala con estas versiones obtiene las salidas de la línea base, y una prueba lo comprueba byte a byte.
- Una dependencia usada sin declarar se detecta en la suite (el 2026-11-16, en el clon nuevo de EV-113, la prueba de requisitos detectó que Pillow se usaba sin estar declarado).

### Negativas
- Quien use otra versión de pandas obtiene otras cifras en el decimal 12.
- Las dependencias transitivas no están fijadas: una nueva puede cambiar entre instalaciones (D81 registró una diferencia menor).
- Con Python 3.11 pip no encuentra numpy 2.5.4 (simulación en EV-062), que exige 3.12 o más; el proyecto no se probó con otras versiones de Python.

## Alternativas consideradas entonces
Registradas en `docs/DECISIONES.md`:
- aceptar una tolerancia de 1e-9 en la comparación (D56)
- regenerar la línea base con la versión nueva (D56)
- marcadores de entorno para soportar python 3.11 con otra versión de numpy (D81)
- un archivo de restricciones con todo el `pip freeze` (D81)

## Alternativas que hoy descartamos y por qué
Razonamiento actual del equipo, no registrado en su momento.
- **Un archivo de bloqueo con todas las dependencias transitivas.** Sería lo más estricto, pero hoy solo difiere una dependencia transitiva menor entre instalaciones y las pruebas de reproducibilidad detectarían un cambio que afectara a las salidas; el costo de mantenerlo no se justifica todavía.
- **Aceptar una tolerancia numérica.** Con 3 celdas de 5.146 filas distintas en el decimal 12, una tolerancia de 1e-9 las habría aceptado; de las 799 celdas de la base no registramos su magnitud, así que no sabemos si también. Aun así, entonces ya no podríamos afirmar que las salidas coinciden byte a byte con la línea base, que es la garantía que comprueba el DAG (ADR-006).
