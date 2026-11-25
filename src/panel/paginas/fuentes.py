"""Página «Fuentes y sistema»: fuentes con licencia y fechas, fecha de corte, almacenamiento activo, qué no se puede concluir y limitaciones.

Desde D115 y D116 lleva la cabecera, el glosario, la guía, las curiosidades, el modo presentación y la exportación de la interfaz propia; las cifras de población se dibujan como tarjetas del diseño
y las tablas, los límites y las limitaciones siguen siendo los componentes nativos de siempre. Los datos, el formato y los textos no cambiaron.
"""
import pandas as pd
import streamlit as st

from src.panel import componentes, formato
from src.panel.frontend import lectura
from src.panel.frontend import vista as base
from src.panel.frontend.marco import dibujar, marco

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


def tarjetas_poblacion(m):
    """Las cuatro tarjetas de fecha de corte y población como `(etiqueta, valor, detalle)`."""
    p = m["poblacion"]
    return [("Fecha de corte", m["fecha_corte"] or formato.SIN_DATO, "Última edición de la capa de edificaciones."),
            ("Construcciones", formato.numero(p["construcciones"]), f"{formato.numero(p['con_datos_satelitales'])} con datos satelitales"),
            ("Comunas", formato.numero(p["comunas"]), None),
            ("Códigos de barrio", formato.numero(p["codigos_barrio"]), None)]


def tabla_fuentes(datos):
    """DataFrame del catálogo de fuentes: nombre, rol, publicador, licencia y fechas."""
    filas = []
    for f in datos["fuentes"]:
        fechas = f.get("fechas") or {}
        filas.append({"Fuente": f["nombre"], "Rol": f["rol"], "Publicador": f["publicador"], "Licencia": f["licencia"], "Fechas": "; ".join(f"{k}: {v}" for k, v in fechas.items())})
    return pd.DataFrame(filas)


def tabla_filas(salud):
    return pd.DataFrame([{"Tabla": k, "Filas": formato.numero(v)} for k, v in salud["filas_por_tabla"].items()])


def limites(m):
    """Los ocho puntos de «qué no se puede concluir», con las cifras de la API."""
    return [punto.format(comunas=formato.numero(m["poblacion"]["comunas"])) for punto in LIMITES]


def render(api):
    """Dibuja la página «Fuentes y sistema»: fecha de corte y población, fuentes y licencias, estado del sistema y los límites del análisis.

    Los límites siguen `docs/gold/KPIs.md` y son los mismos de `LIMITES`.
    """
    def cuerpo(contexto):
        meta, fuentes, salud = api("/metadata"), api("/fuentes"), api("/health")
        dibujar(base.cabecera(contexto.pagina, contexto.grupo, contexto.corte, contexto.metadata))
        if componentes.fallo(meta):
            return
        m = meta.datos
        tarjetas = tarjetas_poblacion(m)
        imagenes = f"Imágenes: antes del evento {m['fecha_imagen_pre']}; después del evento {m['fecha_imagen_post']}. Almacenamiento activo: {m['almacenamiento']}."
        t_fuentes = tabla_fuentes(fuentes.datos) if fuentes.ok else None
        t_filas = tabla_filas(salud.datos) if salud.ok else None
        puntos = limites(m)
        informe = _informe(contexto, tarjetas, imagenes, t_fuentes, fuentes.datos["aviso"] if fuentes.ok else None, t_filas, salud.datos if salud.ok else None, puntos)
        lectura.herramientas(ID, contexto.pagina.titulo, base.guia(ID), base.curiosidades(ID), informe, "fuentes_y_sistema.html", "Exportar informe")
        with st.container(key="contenido_analitico"):
            st.subheader("Fecha de corte y población")
            dibujar(base.tarjetas(tarjetas))
            st.caption(imagenes)
            st.subheader("Fuentes y licencias")
            if not componentes.fallo(fuentes):
                componentes.tabla(t_fuentes, texto_largo=True)
                st.caption(fuentes.datos["aviso"])
            st.subheader("Estado del sistema")
            if not componentes.fallo(salud):
                componentes.tabla(t_filas)
                st.caption(f"Versión de la API: {salud.datos['version_api']}; estado: {salud.datos['estado']}.")
            st.subheader("Qué no se puede concluir")
            for punto in puntos:
                st.markdown("- " + punto)
            st.subheader("Limitaciones del panel")
            for punto in LIMITACIONES:
                st.markdown("- " + punto)
        dibujar(base.pie_pagina())

    marco(api, ID, cuerpo)


def _informe(contexto, tarjetas, imagenes, t_fuentes, aviso, t_filas, salud, puntos):
    """Informe HTML autónomo con el corte, el catálogo de fuentes, el estado del sistema, los ocho límites y las limitaciones."""
    poblacion = base.panel("detalle", "Fecha de corte y población", base.fichas_html(tarjetas) + base.parrafos([imagenes]))
    fuentes = base.panel("detalle", "Fuentes y licencias", (base.tabla_simple(t_fuentes, "Catálogo", "Catálogo de fuentes") + base.parrafos([aviso])) if t_fuentes is not None else "")
    sistema = base.panel("detalle", "Estado del sistema", (base.tabla_simple(t_filas, "Filas por tabla", "Filas por tabla") + base.parrafos([f"Versión de la API: {salud['version_api']}; estado: {salud['estado']}."])) if t_filas is not None else "")
    concluir = base.panel("detalle", "Qué no se puede concluir", base.lista(puntos))
    limitaciones = base.panel("detalle", "Limitaciones del panel", base.lista(LIMITACIONES))
    return base.documento(contexto.pagina, contexto.grupo, contexto.corte, contexto.metadata, poblacion + fuentes + sistema + concluir + limitaciones)
