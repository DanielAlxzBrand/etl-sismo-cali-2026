"""Página «Respuesta»: pregunta de negocio, resultado de K2, frase generada y resumen de K5."""
import streamlit as st

from src.panel import claves, componentes, formato, redaccion
from src.panel.paginas._comun import avisar_falta, por_grupo, texto_ic

ID = "respuesta"
DECIMALES_K5 = {claves.K5_COBERTURA_LLAVE: 3, claves.K5_ESTRATO_VALIDO: 3, claves.K5_NOMBRE_VALIDADO: 2}
ETIQUETAS_K5 = {claves.K5_COBERTURA_LLAVE: "Cobertura de la llave", claves.K5_ESTRATO_VALIDO: "Estrato válido", claves.K5_NOMBRE_VALIDADO: "Nombre validado"}


def _detalle(fila):
    return f"{formato.numero(fila['numerador'])} severos de {formato.numero(fila['denominador'])} · Wilson {texto_ic(fila['ic95_inf'], fila['ic95_sup'])}"


def render(api):
    """Dibuja la página «Respuesta»: las cuatro cifras de K2, la frase generada y el resumen de K5.

    Las cuatro tarjetas de K2 van de dos en dos (F-01, D87) porque en una sola fila, a 1024 px, Streamlit recortaba «6,33 %» y «+0,49 pp». No decide ninguna conclusión: la frase la arma `redaccion`.
    """
    def cuerpo():
        r = api("/kpis")
        if componentes.fallo(r):
            return
        filas = r.datos
        t35, t12 = por_grupo(filas, claves.K2, claves.K2_TASA_3_5), por_grupo(filas, claves.K2, claves.K2_TASA_1_2)
        dif, razon = por_grupo(filas, claves.K2, claves.K2_DIFERENCIA), por_grupo(filas, claves.K2, claves.K2_RAZON)
        if not (t35 and t12 and dif and razon):
            avisar_falta("el indicador K2 completo")
            return
        st.subheader("Estratos 3-5 frente a 1-2")
        etiqueta = "Tasa 1-2" + (f" ({componentes.ETIQUETA_BAJA})" if t12["muestra_baja"] else "")
        componentes.tarjetas([
            ("Tasa 3-5", formato.porcentaje(t35["valor"]), _detalle(t35)),
            (etiqueta, formato.porcentaje(t12["valor"]), _detalle(t12)),
            ("Diferencia (3-5 menos 1-2)", formato.puntos_porcentuales(dif["valor"]), "Intervalo de Newcombe al 95 %: " + formato.intervalo(dif["ic95_inf"], dif["ic95_sup"], como="pp")),
            ("Razón de tasas (3-5 / 1-2)", formato.razon(razon["valor"]), "La razón no trae intervalo en Gold."),
        ])
        st.caption(f"Intervalo de la diferencia (Newcombe): {formato.intervalo(dif['ic95_inf'], dif['ic95_sup'], como='pp')}")
        solapan = redaccion.se_solapan(t35["ic95_inf"], t35["ic95_sup"], t12["ic95_inf"], t12["ic95_sup"])
        st.markdown("**Lectura generada.** " + redaccion.conclusion_diferencia(dif["valor"], dif["ic95_inf"], dif["ic95_sup"], solapan, bool(t12["muestra_baja"])))
        cotas = redaccion.conclusion_cotas([t35, t12])
        if cotas:
            st.markdown(cotas)
        st.subheader("Calidad de la unión (K5)")
        for col, grupo in zip(st.columns(len(ETIQUETAS_K5)), ETIQUETAS_K5):
            fila = por_grupo(filas, claves.K5, grupo)
            with col:
                if fila:
                    componentes.tarjeta(ETIQUETAS_K5[grupo], formato.porcentaje(fila["valor"], DECIMALES_K5[grupo]),
                                        f"{formato.numero(fila['numerador'])} de {formato.numero(fila['denominador'])}")
                else:
                    avisar_falta(ETIQUETAS_K5[grupo])

    componentes.marco(api, ID, cuerpo)
