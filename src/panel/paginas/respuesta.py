"""Página «Respuesta»: pregunta de negocio, resultado de K2, frase generada y resumen de K5.

Desde D115 se dibuja con la interfaz propia (tarjetas, paneles, glosario, guía, curiosidades, modo presentación y exportación). Las cifras, los rótulos, los avisos y la frase generada son los de siempre.
"""
import streamlit as st

from src.panel import claves, componentes, formato, redaccion
from src.panel.frontend import lectura, vista
from src.panel.frontend import respuesta as vista_respuesta
from src.panel.frontend.marco import dibujar, marco
from src.panel.paginas._comun import avisar_falta, por_grupo, texto_ic

ID = "respuesta"
DECIMALES_K5 = {claves.K5_COBERTURA_LLAVE: 3, claves.K5_ESTRATO_VALIDO: 3, claves.K5_NOMBRE_VALIDADO: 2}
ETIQUETAS_K5 = {claves.K5_COBERTURA_LLAVE: "Cobertura de la llave", claves.K5_ESTRATO_VALIDO: "Estrato válido", claves.K5_NOMBRE_VALIDADO: "Nombre validado"}


def _detalle(fila):
    return f"{formato.numero(fila['numerador'])} severos de {formato.numero(fila['denominador'])} · Wilson {texto_ic(fila['ic95_inf'], fila['ic95_sup'])}"


def tarjetas_k2(t35, t12, dif, razon):
    """Las cifras de K2 como `(etiqueta, valor, detalle)`: las dos tasas, la diferencia con su intervalo de Newcombe y la razón."""
    etiqueta = "Tasa 1-2" + (f" ({componentes.ETIQUETA_BAJA})" if t12["muestra_baja"] else "")
    tasas = [("Tasa 3-5", formato.porcentaje(t35["valor"]), _detalle(t35)), (etiqueta, formato.porcentaje(t12["valor"]), _detalle(t12))]
    comparacion = [("Diferencia (3-5 menos 1-2)", formato.puntos_porcentuales(dif["valor"]), "Intervalo de Newcombe al 95 %: " + formato.intervalo(dif["ic95_inf"], dif["ic95_sup"], como="pp")),
                   ("Razón de tasas (3-5 / 1-2)", formato.razon(razon["valor"]), "La razón no trae intervalo en Gold.")]
    return tasas, comparacion


def tarjetas_k5(filas):
    """Las cifras de K5 presentes como `(etiqueta, valor, detalle)` y los rótulos de las que la API no trajo."""
    tarjetas, faltan = [], []
    for grupo, etiqueta in ETIQUETAS_K5.items():
        fila = por_grupo(filas, claves.K5, grupo)
        if fila:
            tarjetas.append((etiqueta, formato.porcentaje(fila["valor"], DECIMALES_K5[grupo]), f"{formato.numero(fila['numerador'])} de {formato.numero(fila['denominador'])}"))
        else:
            faltan.append(etiqueta)
    return tarjetas, faltan


def render(api):
    """Dibuja la página «Respuesta»: las cuatro cifras de K2, la frase generada y el resumen de K5. No decide ninguna conclusión: la frase la arma `redaccion`."""
    def cuerpo(contexto):
        r = api("/kpis")
        dibujar(vista.cabecera(contexto.pagina, contexto.grupo, contexto.corte, contexto.metadata))
        if componentes.fallo(r):
            return
        filas = r.datos
        t35, t12 = por_grupo(filas, claves.K2, claves.K2_TASA_3_5), por_grupo(filas, claves.K2, claves.K2_TASA_1_2)
        dif, razon = por_grupo(filas, claves.K2, claves.K2_DIFERENCIA), por_grupo(filas, claves.K2, claves.K2_RAZON)
        if not (t35 and t12 and dif and razon):
            avisar_falta("el indicador K2 completo")
            return
        tasas, comparacion = tarjetas_k2(t35, t12, dif, razon)
        intervalo = f"Intervalo de la diferencia (Newcombe): {formato.intervalo(dif['ic95_inf'], dif['ic95_sup'], como='pp')}"
        solapan = redaccion.se_solapan(t35["ic95_inf"], t35["ic95_sup"], t12["ic95_inf"], t12["ic95_sup"])
        frase = redaccion.conclusion_diferencia(dif["valor"], dif["ic95_inf"], dif["ic95_sup"], solapan, bool(t12["muestra_baja"]))
        cotas = redaccion.conclusion_cotas([t35, t12])
        k5, faltan = tarjetas_k5(filas)
        html = vista_respuesta.cuerpo(comparacion, intervalo, frase, cotas, tasas, k5)
        documento = vista_respuesta.documento(contexto.pagina, contexto.grupo, contexto.corte, contexto.metadata, html, frase)
        lectura.herramientas(ID, contexto.pagina.titulo, vista.guia(ID, vista_respuesta.ejemplo(t35, t12)), vista.curiosidades(ID), documento, "respuesta_informe.html", "Exportar informe")
        dibujar(html)
        for etiqueta in faltan:
            avisar_falta(etiqueta)

    marco(api, ID, cuerpo)
