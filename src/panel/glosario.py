"""Glosario común del panel: un solo diccionario de términos y el desplegable que cada página muestra con los que usa (F-07, D88).

Lo hicimos así porque la evaluación heurística encontró términos estadísticos sin explicación en pantalla («intervalo de Wilson», «Newcombe», «muestra baja»…) y porque crear
una página nueva cambiaría el número de páginas del panel. Las definiciones siguen `docs/gold/KPIs.md`, no llevan cifras propias (D80) y no afirman causalidad (DP-5).
Qué NO hace: no lee datos ni llama a la API, y no demuestra que una persona sin formación estadística entienda los términos: eso solo lo muestran las sesiones con personas usuarias.
"""
import streamlit as st

# clave -> (término como se muestra, definición en lenguaje claro). Las definiciones no llevan cifras salvo las excepciones de D80 (95 %, 0, grupos 1-2 y 3-5).
TERMINOS = {
    "proxy de daño": (
        "Proxy de daño",
        "Una medida indirecta. El panel no inspecciona edificios: compara imágenes de satélite de antes y después del sismo y marca las construcciones cuya huella cambió mucho. "
        "Eso describe un cambio visible desde arriba; no mide daño interno ni sustituye una evaluación estructural."),
    "cambio satelital severo": (
        "Cambio satelital severo",
        "Construcción cuya imagen de después muestra alta probabilidad de escombros. Es el indicador principal de todo el panel (en la documentación, «severo estricto»). No es lo mismo que colapso."),
    "estrato": (
        "Estrato",
        "Clasificación socioeconómica de 1-6 que usa el municipio. Aquí es la anterior al evento y se asignó a cada construcción por su barrio, no por la construcción misma: por eso describe al barrio y no a cada edificio."),
    "estrato moda": (
        "Estrato moda",
        "El estrato que más se repite entre los lados de manzana de un barrio. Es el que se le asigna a todas las construcciones de ese barrio."),
    "muestra baja": (
        "Muestra baja",
        "Grupo con pocas construcciones severas. Su tasa cambia mucho con un solo caso más o menos, así que el panel la muestra pero no la ordena frente a las demás."),
    "intervalo de Wilson": (
        "Intervalo de Wilson",
        "Rango de tasas compatibles con lo observado, con un nivel de confianza de 95 %. Cuanto más ancho, más incierta es la tasa. Si los intervalos de dos grupos se solapan, no se puede decir que sus tasas sean distintas."),
    "intervalo de Newcombe": (
        "Intervalo de Newcombe",
        "El mismo tipo de rango, pero para la diferencia entre dos tasas. Si incluye 0, con este proxy y esta muestra no se detecta diferencia entre los grupos."),
    "puntos porcentuales": (
        "Puntos porcentuales (pp)",
        "Unidad de la diferencia entre dos porcentajes: si una tasa es de un porcentaje y otra es un punto mayor, la diferencia se escribe con el signo, la cifra y «pp»."),
    "razón de tasas": (
        "Razón de tasas",
        "Cociente entre la tasa de los estratos 3-5 y la de los estratos 1-2. Un valor cercano a uno indica tasas parecidas; la razón sola no dice si la diferencia es mayor que la incertidumbre."),
    "cotas por «sin datos»": (
        "Cotas por «sin datos»",
        "Límites extremos de una tasa: el inferior supone que ninguna construcción sin datos satelitales era severa y el superior que todas lo eran. No son estimaciones; si las cotas de dos grupos se solapan, su orden no se puede identificar."),
    "sin datos": (
        "Sin datos satelitales",
        "Construcciones para las que la imagen no permitió clasificar el cambio. Salen del denominador de las tasas y se informan aparte; faltar un dato no significa que no haya daño."),
    "razón ajustada (Mantel-Haenszel)": (
        "Razón ajustada por comuna (Mantel-Haenszel)",
        "Compara los grupos de estratos dentro de cada comuna y combina los resultados. Solo se puede interpretar si varias comunas tienen construcciones de ambos grupos; si es una sola, indica que estrato y ubicación van mezclados."),
    "falacia ecológica": (
        "Falacia ecológica",
        "Error de atribuir a cada construcción lo que se observa en el grupo al que pertenece (el barrio). Un resultado por barrio no dice nada seguro sobre un edificio concreto."),
    "sensibilidad": (
        "Escenario de sensibilidad",
        "Repetir el cálculo cambiando una decisión del análisis (qué construcciones se incluyen o cómo se define el daño) para ver si la conclusión cambia. Cada escenario se nombra S0 (base) a S5."),
    "daño visible": (
        "Daño visible",
        "Definición ampliada de daño que suma las construcciones con posible desaparición del techo a las de escombros. Es de baja confianza porque las imágenes están separadas por meses y no hay grupo de control."),
    "concentración": (
        "Concentración de casos",
        "Qué parte de las construcciones severas está en pocos barrios (K3). Esos barrios también tienen más construcciones, así que concentración de casos no significa mayor riesgo."),
    "correlación de Spearman": (
        "Correlación de Spearman",
        "Mide si, de un barrio a otro, un estrato mayor suele acompañarse de una tasa mayor o menor. Se acerca a 0 cuando no hay una relación clara. Es descriptiva y a nivel de barrio; no establece causalidad."),
    "p de permutación": (
        "p de permutación",
        "Qué tan raro sería ver una correlación así de fuerte si estrato y tasa no tuvieran relación, calculado barajando los datos muchas veces. Un valor alto no prueba que no exista relación: solo que estos datos no la muestran."),
    "llave": (
        "Llave de unión",
        "Código que une cada construcción con el estrato de su barrio, formado con la comuna y el barrio del catastro. Si la llave falla, la construcción queda sin estrato."),
    "cobertura de la llave": (
        "Cobertura de la llave",
        "Porcentaje de construcciones cuya llave encuentra su barrio en la tabla de estratos. Cobertura alta no garantiza que el barrio asignado sea el correcto."),
    "nombre validado": (
        "Nombre validado",
        "El nombre del barrio en la tabla de estratos se parece al del polígono donde cae la construcción. Sube la confianza en la llave, pero no la vuelve perfecta."),
    "coincidencia con el polígono": (
        "Coincidencia con el polígono",
        "Si el código de barrio de la construcción es el mismo que el del polígono de barrios donde cae su ubicación. Un código que no coincide suele ser una renumeración entre fuentes, no una mala asignación comprobada."),
    "pureza del estrato": (
        "Pureza del estrato",
        "Qué tan homogéneo es el estrato dentro de un barrio: alta si casi todos los lados de manzana tienen el mismo estrato, baja si el barrio mezcla estratos."),
    "clase de daño": (
        "Clase de daño",
        "Categoría que asigna la capa satelital: escombros (alta probabilidad de escombros), techo (posible desaparición del techo), sin cambio y sin datos."),
    "grados decimales": (
        "Grados decimales",
        "Forma de escribir la longitud y la latitud con una parte decimal (separada con coma) en lugar de grados, minutos y segundos. Las etiquetas de los ejes llevan cuatro decimales para que no se lean como miles."),
}

# Términos de cada página: los que su texto usa y que una persona sin formación estadística podría no conocer. «Proxy de daño» va en todas porque el recuadro de alcance de cada página lo usa.
TERMINOS_POR_PAGINA = {
    "respuesta": ("proxy de daño", "cambio satelital severo", "estrato", "muestra baja", "intervalo de Wilson", "intervalo de Newcombe", "puntos porcentuales", "razón de tasas",
                  "cotas por «sin datos»", "llave", "cobertura de la llave", "nombre validado"),
    "estratos": ("proxy de daño", "cambio satelital severo", "estrato", "muestra baja", "intervalo de Wilson", "cotas por «sin datos»", "sin datos"),
    "comunas": ("proxy de daño", "cambio satelital severo", "estrato", "muestra baja", "intervalo de Wilson", "falacia ecológica", "sin datos"),
    "sensibilidades": ("proxy de daño", "sensibilidad", "intervalo de Newcombe", "puntos porcentuales", "razón de tasas", "razón ajustada (Mantel-Haenszel)", "llave", "nombre validado", "coincidencia con el polígono",
                       "pureza del estrato", "daño visible", "estrato"),
    "concentracion": ("proxy de daño", "concentración", "correlación de Spearman", "p de permutación", "falacia ecológica", "estrato moda", "cambio satelital severo", "estrato"),
    "calidad": ("proxy de daño", "llave", "cobertura de la llave", "nombre validado", "coincidencia con el polígono", "estrato"),
    "construcciones": ("proxy de daño", "cambio satelital severo", "clase de daño", "estrato", "nombre validado", "grados decimales", "sin datos"),
    "fuentes": ("proxy de daño", "estrato", "muestra baja", "falacia ecológica", "cotas por «sin datos»", "sin datos"),
}

# Formas con que un término técnico aparece en los textos del panel (en minúsculas) -> clave del glosario. Una prueba exige que toda página que use una de estas formas muestre su entrada.
TECNICOS = {
    "wilson": "intervalo de Wilson", "newcombe": "intervalo de Newcombe", "mantel-haenszel": "razón ajustada (Mantel-Haenszel)", "spearman": "correlación de Spearman",
    "permutación": "p de permutación", "cotas": "cotas por «sin datos»", "muestra baja": "muestra baja", "proxy": "proxy de daño", "falacia ecológica": "falacia ecológica",
    "estrato moda": "estrato moda", "razón de tasas": "razón de tasas", "sensibilidad": "sensibilidad", "nombre validado": "nombre validado", "cobertura de la llave": "cobertura de la llave",
    "grados decimales": "grados decimales", "pureza": "pureza del estrato", "daño visible": "daño visible",
}


def entradas(id_pagina):
    """[(término mostrado, definición)] de los términos de la página, en el orden en que se declararon; lista vacía si la página no está en el diccionario."""
    return [TERMINOS[clave] for clave in TERMINOS_POR_PAGINA.get(id_pagina, ())]


def desplegable(id_pagina):
    """Dibuja el desplegable «Glosario» con los términos de la página (F-07).

    Va cerrado por defecto para no alargar la página (D88) y es el mismo en todas, no una página aparte. Si la página no tiene términos, no dibuja nada.
    """
    lista = entradas(id_pagina)
    if not lista:
        return
    with st.expander("Glosario de esta página: qué significan los términos técnicos"):
        for nombre, definicion in lista:
            st.markdown(f"- **{nombre}.** {definicion}")
