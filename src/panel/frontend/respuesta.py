"""Vista de «Respuesta»: comparación de K2 (diferencia y razón), tasas de los dos grupos y calidad de la unión (K5), con las piezas compartidas de `vista.py`.

Las cifras, los rótulos y los textos son los que arma la página con `formato` y `redaccion`; aquí solo se dibujan.
"""
from src.panel import formato
from src.panel.frontend import vista

ID = "respuesta"


def cuerpo(tarjetas_diferencia, intervalo, lectura, cotas, tarjetas_tasas, tarjetas_k5):
    """Tres paneles: comparación entre grupos, tasas de los dos grupos y calidad de la unión; cada lista son tarjetas `(etiqueta, valor, detalle)`."""
    texto_lectura = f'<div class="lectura"><strong>Lectura generada</strong>{vista.e(lectura)}</div>'
    extra = vista.parrafos([cotas]) if cotas else ""
    balance = vista.panel("balance", "Comparación entre grupos", vista.fichas_html(tarjetas_diferencia) + vista.parrafos([intervalo]) + texto_lectura + extra)
    tasas = vista.panel("evidencia", "Estratos 3-5 frente a 1-2", vista.fichas_html(tarjetas_tasas))
    calidad = vista.panel("evidencia", "Calidad de la unión (K5)", vista.fichas_html(tarjetas_k5) if tarjetas_k5 else "",
                          "Estos conteos muestran cuántos registros se pudieron relacionar con el barrio.")
    return vista.envolver(balance + tasas + calidad, analisis=False)


def ejemplo(t35, t12):
    """Frase del paso «Leer los conteos» de la guía, con los conteos de K2."""
    return (f"De {formato.numero(t35['denominador'])} construcciones con clasificación en estratos 3-5, {formato.numero(t35['numerador'])} tienen cambio severo. "
            f"En estratos 1-2 son {formato.numero(t12['numerador'])} de {formato.numero(t12['denominador'])}.")


def documento(pagina, grupo, corte, metadata, cuerpo_html, lectura):
    """Informe HTML autónomo con las tarjetas, la lectura generada, el alcance, el corte y la fuente."""
    return vista.documento(pagina, grupo, corte, metadata, cuerpo_html, lectura)
