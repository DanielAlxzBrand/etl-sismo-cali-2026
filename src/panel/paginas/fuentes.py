"""Página «Fuentes y sistema»: fuentes con licencia y fechas, fecha de corte, almacenamiento activo, qué no se puede concluir y limitaciones."""
import pandas as pd
import streamlit as st

from src.panel import componentes, formato

ID = "fuentes"

# Los puntos de «qué no se puede concluir» siguen docs/gold/KPIs.md; las cifras, cuando hay, se leen de la API.
LIMITES = (
    "El indicador mide **cambio visible desde satélite**, no daño interno ni el de construcciones sin cambio visible; no sustituye una inspección estructural.",
    "Solo hay {comunas} comunas en la muestra; las comunas ausentes no se pueden evaluar. Las tasas describen esta muestra: no se extrapolan a Cali ni a la ciudad.",
    "Los estratos con muchas construcciones sin datos satelitales no se ordenan frente a los demás: la falta de datos no es aleatoria y sus cotas se solapan.",
    "Los grupos marcados como muestra baja se muestran, pero no se ordenan frente a otros.",
    "El estrato se asignó al barrio por lados de manzana (falacia ecológica) y es anterior al evento; lo que cambió desde entonces es desconocido.",
    "La definición ampliada de daño (escombros más techo) es de baja confianza: imágenes separadas por meses y sin grupo de control.",
    "Una asociación no establece causalidad; que no se detecte diferencia entre estratos no demuestra que el estrato carezca de efecto.",
    "El grupo de estratos 1-2 está formado casi por completo por muy pocas comunas, así que comparar estratos es, en la práctica, comparar comunas.",
)
LIMITACIONES = (
    "El panel se ejecuta solo en esta máquina (dirección local) y no está desplegado.",
    "Solo lee la API; no calcula ni modifica datos.",
    "Las latencias y tiempos que se midan son de una máquina concreta.",
    "La evaluación con personas usuarias no se ha realizado.",
)


def render(api):
    def cuerpo():
        meta, fuentes, salud = api("/metadata"), api("/fuentes"), api("/health")
        if componentes.fallo(meta):
            return
        m = meta.datos
        st.subheader("Fecha de corte y población")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            componentes.tarjeta("Fecha de corte", m["fecha_corte"] or formato.SIN_DATO, "Última edición de la capa de edificaciones.")
        with c2:
            componentes.tarjeta("Construcciones", formato.numero(m["poblacion"]["construcciones"]), f"{formato.numero(m['poblacion']['con_datos_satelitales'])} con datos satelitales")
        with c3:
            componentes.tarjeta("Comunas", formato.numero(m["poblacion"]["comunas"]))
        with c4:
            componentes.tarjeta("Códigos de barrio", formato.numero(m["poblacion"]["codigos_barrio"]))
        st.caption(f"Imágenes: antes del evento {m['fecha_imagen_pre']}; después del evento {m['fecha_imagen_post']}. Almacenamiento activo: {m['almacenamiento']}.")
        st.subheader("Fuentes y licencias")
        if not componentes.fallo(fuentes):
            filas = []
            for f in fuentes.datos["fuentes"]:
                fechas = f.get("fechas") or {}
                filas.append({"Fuente": f["nombre"], "Rol": f["rol"], "Publicador": f["publicador"], "Licencia": f["licencia"],
                              "Fechas": "; ".join(f"{k}: {v}" for k, v in fechas.items())})
            componentes.tabla(pd.DataFrame(filas))
            st.caption(fuentes.datos["aviso"])
        st.subheader("Estado del sistema")
        if not componentes.fallo(salud):
            componentes.tabla(pd.DataFrame([{"Tabla": k, "Filas": formato.numero(v)} for k, v in salud.datos["filas_por_tabla"].items()]))
            st.caption(f"Versión de la API: {salud.datos['version_api']}; estado: {salud.datos['estado']}.")
        st.subheader("Qué no se puede concluir")
        for punto in LIMITES:
            st.markdown("- " + punto.format(comunas=formato.numero(m["poblacion"]["comunas"])))
        st.subheader("Limitaciones del panel")
        for punto in LIMITACIONES:
            st.markdown("- " + punto)

    componentes.marco(api, ID, cuerpo)
