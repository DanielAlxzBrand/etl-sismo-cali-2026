"""Vista de «Estratos (K1)»: cabecera con resumen, figura de barras, puntos y tabla, detalle y lámina exportable, dibujados con los datos que entrega la API.

Usa las piezas compartidas de `vista.py`. Aquí no se calcula ninguna cifra: cada número llega ya hecho por la API (tasa, intervalo de Wilson, conteos, cotas y marca de muestra baja).
"""
from src.panel import componentes, formato
from src.panel.frontend import activos, vista
from src.panel.frontend.vista import alcance_html, escala, frase_fila, glosario_html, resaltados  # noqa: F401  (se usan desde las pruebas y las páginas)

ID = "estratos"


def cabecera(pagina, grupo, corte, metadata, filas=None):
    """Cabecera con el resumen de K1: cuántos estratos, cuántos con muestra baja y el nivel de confianza; sin filas, sin resumen."""
    contenido = activos.contenido(ID)
    resumen = ""
    if filas:
        bajas = sum(1 for f in filas if f.get("muestra_baja"))
        resumen = (f'<div class="kpis"><div><b>{formato.numero(len(filas))}</b>estratos</div><div><b class="ambar">{formato.numero(bajas)}</b>con {componentes.ETIQUETA_BAJA}</div>'
                   f'<div><b>95 %</b><details class="ayuda-ic"><summary>Intervalo de Wilson</summary><p>{vista.e(contenido["ayuda_intervalo"])}</p></details></div></div>')
    return vista.cabecera(pagina, grupo, corte, metadata, resumen)


def cuerpo(filas, etiquetas, tabla, conclusion, avisos, nota_cotas):
    """Figura, notas y detalle en un solo bloque, más el pie con «Volver arriba»."""
    contenido = activos.contenido(ID)
    interior = (vista.figura(filas, etiquetas, "Tasa por estrato", "Cambio satelital severo, con intervalo de Wilson al 95 %.") + vista.notas(conclusion, contenido["como_leer"], avisos)
                + vista.detalle(tabla, filas, "Detalle por estrato", "Tabla por estrato", contenido["como_leer_columnas"], nota_cotas))
    return vista.resaltados(len(filas)) + vista.envolver(interior)


def ejemplo(filas, etiquetas):
    """Frase del paso «Traducir la tasa» de la guía: la primera fila con muestra suficiente (o la primera, si todas son bajas)."""
    elegida = next(((f, e) for f, e in zip(filas, etiquetas) if not f.get("muestra_baja")), (filas[0], etiquetas[0]))
    return f"{elegida[1]}. {frase_fila(elegida[0])}"


def guia(filas, etiquetas):
    return vista.guia(ID, ejemplo(filas, etiquetas))


def fichas():
    return vista.curiosidades(ID)


def lamina(pagina, grupo, corte, metadata, filas, etiquetas, tabla, conclusion, nota_cotas):
    """Documento HTML autónomo con la figura, el detalle, el alcance, el corte y la fuente."""
    contenido = activos.contenido(ID)
    tope, marcas = escala(filas)
    items = [dict(etiqueta=et, texto=formato.porcentaje(f.get("valor")), x=vista.pct(f.get("valor")), desde=vista.pct(f.get("ic95_inf")), hasta=vista.pct(f.get("ic95_sup")), baja=bool(f.get("muestra_baja")))
             for f, et in zip(filas, etiquetas)]
    svg, alto = vista.figura_svg(items, 0, tope, marcas, "Cambio satelital severo (%)")
    detalle = vista.detalle(tabla, filas, "Detalle por estrato", "Tabla por estrato", contenido["como_leer_columnas"], nota_cotas)
    return vista.documento(pagina, grupo, corte, metadata, detalle, conclusion, (svg, alto, "Tasas e intervalos de Wilson por estrato. Los valores completos están en la tabla.", componentes.PIE_INTERVALO))
