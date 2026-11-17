# ADR-010: La API es de solo lectura, la fuerza la conexión y escucha solo en 127.0.0.1

**Estado:** Vigente (implementada). **Fecha de la decisión:** 2026-11-12. **D de origen:** D18, D27, D28, D29, D52, D54. **Propietario técnico:** Daniel Alexander Brand García. **Revisión:** pendiente.

## Contexto
Queríamos exponer los resultados de Gold sin poner en riesgo la línea base. La API no tiene autenticación, y el panel corre en el mismo equipo.

## Decisión
- Un servicio FastAPI sin endpoints de escritura sobre Gold, con 11 rutas GET (D18).
- Los endpoints no conocen el motor: usan una interfaz `RepositorioGold` con una implementación para SQLite y otra para MySQL, elegidas con `api.almacenamiento` (D27 y D52).
- El solo lectura lo fuerza la conexión: SQLite se abre con `mode=ro`, MySQL con `SET SESSION TRANSACTION READ ONLY`, una conexión por solicitud cerrada en `finally`, y el SQL siempre va parametrizado y con listas blancas de tablas y columnas (D28).
- `host: 127.0.0.1` en `config/config.yaml`, sin middleware de CORS (D29).
- No se usa un conjunto de conexiones: con servidores locales la mediana de las rutas que usan el almacén es de unos 60 a 120 ms con MySQL frente a unos 3 a 10 ms con SQLite (D54, EV-032).

## Consecuencias
### Positivas
- Aunque hubiera un error de código, el motor rechaza escribir; una prueba lo verifica con un `INSERT`.
- Los errores usan siempre el mismo formato JSON y la documentación OpenAPI sale sola.
- La respuesta de ambos almacenes es equivalente, y una prueba lo compara.

### Negativas
- Sin autenticación, la API no puede salir del equipo; si el panel se despliega aparte hará falta una decisión nueva.
- Con MySQL caído la API contesta 503; el valor por defecto sigue siendo SQLite.
- Una conexión por solicitud cuesta unas décimas de segundo con MySQL frente a un conjunto de conexiones.

## Alternativas consideradas entonces
Registradas en `docs/DECISIONES.md`:
- servidor con la biblioteca estándar (respaldo) (D18)
- sql directo en cada endpoint (D27)
- confiar solo en que no existan endpoints de escritura (D28)
- 0.0.0.0 para probar desde otros equipos (D29)
- endpoints distintos por motor (D52)
- la api leyendo siempre sqlite (D52)
- un conjunto de conexiones reutilizables (D54)
- una conexión única compartida (D54)

## Alternativas que hoy descartamos y por qué
Razonamiento actual del equipo, no registrado en su momento.
- **Autenticación con tokens o un servicio de identidad.** El servicio es local y de una sola persona usuaria a la vez; agregaría estado y secretos que hoy no existen. Se vuelve a evaluar si la API sale de `127.0.0.1`.
- **Una API de escritura para cargar datos.** Las salidas son la línea base: se escriben por el pipeline y se verifican por sha256; una ruta de escritura abriría otra forma de alterarlas.
