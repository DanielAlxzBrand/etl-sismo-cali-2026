# Simulación: datos sintéticos

> **DATOS SINTÉTICOS: no son personas.** Los archivos de esta carpeta (`registro.csv` y `cuestionarios.csv`) los genera `scripts/usuarios/generar_datos_sinteticos.py` con una semilla fija (la misma semilla produce siempre los mismos archivos). Los tres participantes (`S01` a `S03`) no existen: no tienen perfil real, no hay citas ni relatos y ningún número viene de una sesión.

## Para qué sirven
Para probar `scripts/usuarios/analizar_sesiones.py --simulado` y ensayar el formato de [resultados_simulacion.md](../resultados_simulacion.md). Lo hicimos así porque un script de análisis que nunca se ejecutó con datos puede fallar justo cuando haya sesiones reales.

## Qué NO son
No cuentan para los ítems 6.1, 6.2, 6.3, 6.5 ni 7.4, no entran en [resultados.md](../resultados.md) y el script los separa de las sesiones reales: en `sesiones_reales/` rechaza cualquier fila que no diga `real`, y aquí rechaza cualquier fila que no diga `sintetico`.
