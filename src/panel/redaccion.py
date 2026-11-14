"""Redacción de conclusiones: textos generados desde los datos de la API con la regla de docs/gold/KPIs.md.

Regla (DP-5): si el intervalo de la diferencia incluye 0 o los intervalos se solapan, se escribe «con este proxy y esta muestra no se detecta diferencia»;
nunca se afirma que el estrato no influye ni causalidad. Los grupos con muestra baja y los estratos con cotas que se solapan nunca se ordenan.
Las funciones reciben filas ya leídas de la API (diccionarios) y no escriben ninguna cifra propia: todo número sale de ellas.
"""
from src.panel import formato

FRASE_SIN_DIFERENCIA = "con este proxy y esta muestra no se detecta diferencia"
AVISO_NO_CAUSAL = "Describe esta muestra; una asociación no establece causalidad."
AVISO_MUESTRA_BAJA = "El grupo marcado como muestra baja tiene pocos casos severos: la comparación es frágil."


def incluye_cero(inferior, superior):
    """True si 0 queda dentro del intervalo [inferior, superior]."""
    if inferior is None or superior is None:
        return False
    return inferior <= 0 <= superior


def se_solapan(a_inf, a_sup, b_inf, b_sup):
    """True si dos intervalos tienen puntos en común; None si falta algún extremo."""
    if None in (a_inf, a_sup, b_inf, b_sup):
        return None
    return max(a_inf, b_inf) <= min(a_sup, b_sup)


def _etiqueta_estrato(grupo):
    """«estrato_1» -> «estrato 1»; «estratos_1-2» -> «estratos 1-2»."""
    return str(grupo).replace("_", " ")


def conclusion_diferencia(diferencia, inferior, superior, solapan_intervalos=None, muestra_baja=False, comparacion="los estratos 3-5 y 1-2"):
    """Frase sobre la diferencia de tasas (puntos porcentuales) y su intervalo de Newcombe."""
    if diferencia is None or inferior is None or superior is None:
        return "No hay un intervalo disponible para la diferencia: no se redacta una conclusión."
    ic = formato.intervalo(inferior, superior, como="pp")
    if incluye_cero(inferior, superior):
        texto = f"La diferencia de tasas entre {comparacion} es {formato.puntos_porcentuales(diferencia)} y su intervalo {ic} incluye 0: {FRASE_SIN_DIFERENCIA}."
    elif solapan_intervalos:
        texto = f"Los intervalos de las tasas de {comparacion} se solapan: {FRASE_SIN_DIFERENCIA}."
    else:
        sentido = "mayor" if diferencia > 0 else "menor"
        texto = (f"El intervalo de la diferencia {ic} no incluye 0: en esta muestra la primera tasa es {sentido} que la segunda "
                 f"({formato.puntos_porcentuales(diferencia)}).")
    if muestra_baja:
        texto += " " + AVISO_MUESTRA_BAJA
    return texto + " " + AVISO_NO_CAUSAL


def conclusion_cotas(filas_grupos):
    """Dice si las cotas por «sin datos» de los grupos se solapan (entonces el orden no es identificable)."""
    cotas = [(f.get("cota_inf"), f.get("cota_sup")) for f in filas_grupos]
    if len(cotas) < 2 or any(None in c for c in cotas):
        return ""
    for i in range(len(cotas)):
        for j in range(i + 1, len(cotas)):
            if se_solapan(*cotas[i], *cotas[j]):
                return "Las cotas por «sin datos» se solapan: el orden entre los grupos no es identificable."
    return "Las cotas por «sin datos» de los grupos no se solapan."


def conclusion_estratos(filas_k1):
    """Texto sobre K1: no se ordena ningún estrato con muestra baja y se informa qué intervalos de Wilson se solapan entre los demás."""
    bajos = [f for f in filas_k1 if f.get("muestra_baja")]
    suficientes = [f for f in filas_k1 if not f.get("muestra_baja") and f.get("ic95_inf") is not None]
    partes = []
    if bajos:
        nombres = ", ".join(_etiqueta_estrato(f["grupo"]).replace("estrato ", "E") for f in bajos)
        partes.append(f"Con muestra baja ({nombres}): sus tasas se muestran, pero no se ordenan frente a otros estratos.")
    if len(suficientes) >= 2:
        pares_solapan, pares_separados = [], []
        for i in range(len(suficientes)):
            for j in range(i + 1, len(suficientes)):
                a, b = suficientes[i], suficientes[j]
                par = f"E{a['grupo'][-1]} y E{b['grupo'][-1]}"
                (pares_solapan if se_solapan(a["ic95_inf"], a["ic95_sup"], b["ic95_inf"], b["ic95_sup"]) else pares_separados).append(par)
        if pares_solapan:
            partes.append(f"Los intervalos de Wilson se solapan entre {', '.join(pares_solapan)}: {FRASE_SIN_DIFERENCIA} entre esos estratos.")
        if pares_separados:
            partes.append(f"Los intervalos no se solapan entre {', '.join(pares_separados)}; es una descripción de la muestra, no una explicación.")
    partes.append(AVISO_NO_CAUSAL)
    return " ".join(partes)


def comuna_que_concentra(composicion, grupo="1-2"):
    """Frase calculada: qué comuna reúne la mayor parte de las construcciones con datos del grupo de estratos dado."""
    filas = [f for f in composicion if f.get("grupo_estrato") == grupo]
    total = sum(f["n_con_datos"] for f in filas)
    if not filas or total == 0:
        return f"No hay construcciones con datos del grupo de estratos {grupo} en la composición."
    mayor = max(filas, key=lambda f: f["n_con_datos"])
    parte = mayor["n_con_datos"] / total
    ordenadas = sorted(filas, key=lambda f: -f["n_con_datos"])
    segunda = ordenadas[1] if len(ordenadas) > 1 else None
    texto = (f"En el grupo de estratos {grupo}, la Comuna {mayor['comuna']} reúne {formato.numero(mayor['n_con_datos'])} de "
             f"{formato.numero(total)} construcciones con datos ({formato.porcentaje(parte, 1)})")
    if segunda is not None and segunda["n_con_datos"] > 0:
        texto += f"; sigue la Comuna {segunda['comuna']} con {formato.numero(segunda['n_con_datos'])}"
    return texto + ". El estrato está confundido con la ubicación: comparar estratos es, en la práctica, comparar comunas."


def conclusion_comunas(filas_k6):
    """Texto sobre K6: se informan las comunas con muestra baja (sin ordenarlas) y se evita un ranking."""
    bajas = [f["comuna"] for f in filas_k6 if f.get("muestra_baja")]
    partes = []
    if bajas:
        partes.append("Comunas con muestra baja: " + ", ".join(bajas) + "; sus tasas no se ordenan frente a las demás.")
    partes.append("Los intervalos de Wilson permiten leer cada tasa por separado; no se publica un ordenamiento de comunas. " + AVISO_NO_CAUSAL)
    return " ".join(partes)


def conclusion_escenario(escenario, diferencia_fila):
    """Frase por escenario de sensibilidad según el intervalo de la diferencia."""
    if not diferencia_fila or diferencia_fila.get("ic95_inf") is None:
        return f"{escenario}: sin intervalo de la diferencia."
    inf, sup = diferencia_fila["ic95_inf"], diferencia_fila["ic95_sup"]
    ic = formato.intervalo(inf, sup, como="pp")
    dif = formato.puntos_porcentuales(diferencia_fila["tasa"])
    if incluye_cero(inf, sup):
        return f"{escenario}: diferencia {dif}, intervalo {ic} que incluye 0; {FRASE_SIN_DIFERENCIA}."
    return f"{escenario}: diferencia {dif}, intervalo {ic} que no incluye 0 en este escenario; describe la muestra y no una causa."


def conclusion_sensibilidades(diferencias):
    """Resumen: en cuántos escenarios el intervalo de la diferencia incluye 0."""
    validas = [d for d in diferencias if d.get("ic95_inf") is not None]
    con_cero = [d["escenario"] for d in validas if incluye_cero(d["ic95_inf"], d["ic95_sup"])]
    if not validas:
        return "No hay intervalos de la diferencia para resumir."
    if len(con_cero) == len(validas):
        return f"En los {formato.numero(len(validas))} escenarios el intervalo de la diferencia incluye 0: {FRASE_SIN_DIFERENCIA} en ninguno de ellos."
    sin = [d["escenario"] for d in validas if d["escenario"] not in con_cero]
    return (f"El intervalo incluye 0 en {formato.numero(len(con_cero))} de {formato.numero(len(validas))} escenarios; "
            f"no lo incluye en {', '.join(sin)}. Se informa como descripción de cada escenario.")


def aviso_mantel_haenszel(fila_mh, comunas_usadas):
    """Advertencia sobre la razón ajustada por comuna: solo es interpretable con varias comunas que tengan ambos grupos."""
    if fila_mh is None or fila_mh.get("tasa") is None:
        return "En este escenario la razón ajustada por comuna no está definida (ninguna comuna tiene ambos grupos)."
    base = f"La razón ajustada por comuna (Mantel-Haenszel) vale {formato.razon(fila_mh['tasa'])}"
    if comunas_usadas is not None and comunas_usadas < 2:
        return base + f", pero descansa en {formato.numero(comunas_usadas)} comuna con ambos grupos: no es interpretable; indica que el estrato está confundido con la ubicación."
    return base + "; se interpreta con cautela porque el estrato está confundido con la ubicación."


def conclusion_concentracion(top10, spearman):
    """K3 y K4: concentración no es riesgo; correlación descriptiva a nivel de barrio."""
    partes = []
    if top10 and top10.get("valor") is not None:
        partes.append(f"Los barrios con más construcciones con cambio satelital severo (los que define K3) reúnen {formato.porcentaje(top10['valor'], 1)} de los casos "
                      f"({formato.numero(top10['numerador'])} de {formato.numero(top10['denominador'])}); esos barrios también tienen más construcciones: concentración de casos no es mayor riesgo.")
    if spearman and spearman.get("valor") is not None:
        partes.append(f"La correlación de Spearman entre el estrato moda y la tasa por barrio es {formato.numero(spearman['valor'], 3)} "
                      f"(n = {formato.numero(spearman['denominador'])} barrios); es descriptiva y a nivel de barrio (falacia ecológica).")
    return " ".join(partes) if partes else "No hay datos de K3 y K4 para redactar."
