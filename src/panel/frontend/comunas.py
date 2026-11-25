"""Vista de «Comunas (K6)»: figura de barras, puntos y tabla por comuna, detalle, composición por grupo de estrato y lámina exportable, con las piezas compartidas de `vista.py`.

La API entrega K6 con otros nombres de campo (`tasa`, `severos`, `n_con_datos`); `normalizar` los traduce a los que usa la figura, sin cambiar ningún valor.
"""
from src.panel import componentes, formato
from src.panel.frontend import activos, vista

ID = "comunas"
INTRO_COMPOSICION = "Construcciones con datos satelitales y severas por comuna y grupo de estrato (los grupos de estrato son los que define la API)."


def normalizar(fila):
    """La fila de K6 de la API con los nombres de campo de la figura (`valor`, `numerador`, `denominador`); los valores no cambian."""
    return dict(fila, valor=fila["tasa"], numerador=fila["severos"], denominador=fila["n_con_datos"])


def cuerpo(filas, etiquetas, tabla, conclusion, composicion, comuna_concentra):
    """Figura, notas, detalle por comuna y composición por comuna y grupo de estrato, más el pie con «Volver arriba»."""
    contenido = activos.contenido(ID)
    normales = [normalizar(f) for f in filas]
    interior = (vista.figura(normales, etiquetas, "Tasa por comuna", "Cambio satelital severo, con intervalo de Wilson al 95 %.") + vista.notas(conclusion, contenido["como_leer"])
                + vista.detalle(tabla, normales, "Detalle por comuna", "Tabla por comuna", contenido["como_leer_columnas"])
                + (_composicion(composicion, comuna_concentra) if composicion is not None else ""))
    return vista.resaltados(len(filas)) + vista.envolver(interior)


def _composicion(tabla, comuna_concentra):
    return vista.tabla_simple(tabla, "Composición por comuna y grupo de estrato", "Composición por comuna", INTRO_COMPOSICION, comuna_concentra)


def guia():
    return vista.guia(ID)


def lamina(pagina, grupo, corte, metadata, filas, etiquetas, tabla, conclusion, composicion, comuna_concentra):
    contenido = activos.contenido(ID)
    normales = [normalizar(f) for f in filas]
    tope, marcas = vista.escala(normales)
    items = [dict(etiqueta=et, texto=formato.porcentaje(f.get("valor")), x=vista.pct(f.get("valor")), desde=vista.pct(f.get("ic95_inf")), hasta=vista.pct(f.get("ic95_sup")), baja=bool(f.get("muestra_baja")))
             for f, et in zip(normales, etiquetas)]
    svg, alto = vista.figura_svg(items, 0, tope, marcas, "Cambio satelital severo (%)")
    cuerpo_html = vista.detalle(tabla, normales, "Detalle por comuna", "Tabla por comuna", contenido["como_leer_columnas"])
    if composicion is not None:
        cuerpo_html += _composicion(composicion, comuna_concentra)
    return vista.documento(pagina, grupo, corte, metadata, cuerpo_html, conclusion, (svg, alto, "Tasas e intervalos de Wilson por comuna. Los valores completos están en la tabla.", componentes.PIE_INTERVALO))
