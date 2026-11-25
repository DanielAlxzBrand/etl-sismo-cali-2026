"""Vista de «Sensibilidades (S0 a S5)»: el documento exportable con la diferencia por escenario, su tabla y los avisos de la razón ajustada.

En pantalla la página conserva el gráfico, la tabla y los avisos nativos (con la paleta Okabe-Ito); aquí solo se arma el informe descargable con los mismos valores.
"""
from src.panel import formato
from src.panel.frontend import vista

ID = "sensibilidades"
PIE_DIFERENCIAS = ("Cada punto es la diferencia observada en ese escenario; la línea que lo cruza va del límite inferior al superior del intervalo de Newcombe al 95 % y la línea discontinua marca la ausencia de diferencia.")


def documento(pagina, grupo, corte, metadata, escenarios, difs, tabla, lectura, avisos, notas):
    """Informe HTML autónomo: figura de diferencias con su intervalo, tabla de escenarios, avisos de Mantel-Haenszel y sus notas completas."""
    desde = [d["ic95_inf"] * 100 for d in difs]
    hasta = [d["ic95_sup"] * 100 for d in difs]
    inferior, superior, marcas = vista.escala_con_signo(min(desde), max(hasta))
    items = [dict(etiqueta=e, texto=formato.puntos_porcentuales(d["tasa"]), x=d["tasa"] * 100, desde=a, hasta=b) for e, d, a, b in zip(escenarios, difs, desde, hasta)]
    svg, alto = vista.figura_svg(items, inferior, superior, marcas, "Diferencia 3-5 menos 1-2 (puntos porcentuales)", cero=True)
    cuerpo = (vista.tabla_simple(tabla, "Escenarios y resultados", "Escenarios y resultados")
              + vista.panel("detalle", "Razón ajustada por comuna (Mantel-Haenszel)", vista.parrafos(avisos) + vista.parrafos(notas)))
    return vista.documento(pagina, grupo, corte, metadata, cuerpo, lectura, (svg, alto, "Diferencia de tasas por escenario con su intervalo de Newcombe y una línea en cero.", PIE_DIFERENCIAS))


def pie_de_pagina():
    """Solo el pie con «Volver arriba», para las páginas cuyo cuerpo es nativo."""
    return vista.envolver("", analisis=False)

