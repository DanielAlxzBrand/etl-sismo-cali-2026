"""Registro único de páginas y componentes del panel (datos, no lógica).

De aquí salen la navegación de la aplicación, la documentación de trazabilidad (`docs/panel/trazabilidad_ui.md`, generada por
`scripts/panel/generar_trazabilidad.py`) y las pruebas que verifican que cada componente apunta a una ruta de la API y a un campo
o KPI que existen en los archivos de salida. Los campos son las columnas del archivo de salida; la API de /comunas los renombra
(`tasa` = `valor`, `severos` = `numerador`, `n_con_datos` = `denominador`).
"""
from dataclasses import dataclass

KPIS = "data/gold/kpis_gold.csv"
SENSIB = "data/gold/kpis_sensibilidad.csv"
GOLD = "data/gold/gold_final.csv"
CALIDAD = "data/silver/quality_report.json"
CATALOGO = "docs/bronze/catalogo_fuentes.json"
MANIFIESTO = "data/bronze/manifest.jsonl"
CONFIG = "config/config.yaml"
KPIS_MD = "docs/gold/KPIs.md"

ALCANCE = "Cambio satelital severo = proxy de daño; tasas condicionales a esta muestra (7 comunas); estrato de 2015 por lados de manzana."
MUESTRA_BAJA = "Un grupo con muestra baja se muestra, pero no se ordena frente a otros."
CONFUSION = "El estrato está confundido con la ubicación; asociación no es causalidad."


@dataclass(frozen=True)
class Pagina:
    id: str
    titulo: str
    url_path: str
    pregunta: str
    rutas: tuple


@dataclass(frozen=True)
class Componente:
    id: str
    pagina: str
    titulo: str
    tipo: str          # metrica | grafico | tabla | texto | aviso | descarga
    rutas: tuple       # rutas de la API que alimentan el componente
    campos: tuple      # columnas o claves de los archivos de salida que muestra
    kpi: str           # K1..K6 o "" si no es un KPI
    advertencia: str
    fuente: str        # archivo de salida donde está el número


PAGINAS = (
    Pagina("respuesta", "Respuesta", "respuesta", "¿En esta muestra se detecta diferencia en la tasa de cambio satelital severo entre los estratos 3-5 y 1-2?", ("/kpis", "/metadata")),
    Pagina("estratos", "Estratos (K1)", "estratos", "¿Cuál es la tasa de cambio satelital severo en cada estrato y qué tan segura es?", ("/kpis/K1",)),
    Pagina("comunas", "Comunas (K6)", "comunas", "¿Cómo se reparte la tasa por comuna y en qué comunas se concentran los estratos 1-2?", ("/comunas", "/composicion")),
    Pagina("sensibilidades", "Sensibilidades (S0 a S5)", "sensibilidades", "¿Cambia la conclusión si se cambian el filtro de la llave o la definición de daño?", ("/kpis/sensibilidad",)),
    Pagina("concentracion", "Concentración (K3 y K4)", "concentracion", "¿Se concentran los casos en pocos barrios y se asocia el estrato con la tasa por barrio?", ("/kpis",)),
    Pagina("calidad", "Calidad de la llave", "calidad", "¿Qué tan confiable es la unión entre las construcciones y el estrato del barrio?", ("/calidad", "/llave/revision")),
    Pagina("construcciones", "Construcciones", "construcciones", "¿Qué construcciones hay detrás de las cifras y dónde están?", ("/construcciones", "/comunas", "/kpis/K1")),
    Pagina("fuentes", "Fuentes y sistema", "fuentes", "¿De dónde salen los datos, con qué licencia y qué no se puede concluir?", ("/fuentes", "/metadata", "/health")),
)

COMPONENTES = (
    Componente("respuesta.tasa_3_5", "respuesta", "Tasa de los estratos 3-5", "metrica", ("/kpis",), ("valor", "numerador", "denominador", "ic95_inf", "ic95_sup"), "K2", ALCANCE, KPIS),
    Componente("respuesta.tasa_1_2", "respuesta", "Tasa de los estratos 1-2", "metrica", ("/kpis",), ("valor", "numerador", "denominador", "ic95_inf", "ic95_sup", "muestra_baja"), "K2", MUESTRA_BAJA, KPIS),
    Componente("respuesta.diferencia", "respuesta", "Diferencia de tasas con su intervalo de Newcombe", "metrica", ("/kpis",), ("valor", "ic95_inf", "ic95_sup"), "K2", CONFUSION, KPIS),
    Componente("respuesta.razon", "respuesta", "Razón de tasas 3-5 / 1-2", "metrica", ("/kpis",), ("valor",), "K2", "La razón no trae intervalo en Gold.", KPIS),
    Componente("respuesta.conclusion", "respuesta", "Conclusión generada con la regla de redacción", "texto", ("/kpis",), ("valor", "ic95_inf", "ic95_sup", "cota_inf", "cota_sup"), "K2", CONFUSION, KPIS),
    Componente("respuesta.calidad", "respuesta", "Resumen de la calidad de la llave (K5)", "metrica", ("/kpis",), ("valor", "numerador", "denominador"), "K5", "El estrato es de 2015.", KPIS),
    Componente("respuesta.alcance", "respuesta", "Alcance y aviso de la API", "aviso", ("/metadata",), ("aviso",), "", ALCANCE, CONFIG),
    Componente("estratos.grafico", "estratos", "Tasa por estrato con intervalo de Wilson", "grafico", ("/kpis/K1",), ("valor", "ic95_inf", "ic95_sup", "muestra_baja"), "K1", MUESTRA_BAJA, KPIS),
    Componente("estratos.tabla", "estratos", "Tabla de K1: casos, tasa, intervalo, sin datos y cotas", "tabla", ("/kpis/K1",), ("numerador", "denominador", "valor", "pct_sin_datos", "cota_inf", "cota_sup"), "K1", "E2 tiene mucha falta de datos; E6 tiene pocas construcciones.", KPIS),
    Componente("estratos.conclusion", "estratos", "Lectura generada de K1", "texto", ("/kpis/K1",), ("muestra_baja", "ic95_inf", "ic95_sup"), "K1", CONFUSION, KPIS),
    Componente("comunas.grafico", "comunas", "Tasa por comuna con intervalo de Wilson", "grafico", ("/comunas",), ("valor", "ic95_inf", "ic95_sup", "muestra_baja"), "K6", MUESTRA_BAJA, KPIS),
    Componente("comunas.tabla", "comunas", "Tabla de K6", "tabla", ("/comunas",), ("numerador", "denominador", "valor", "pct_sin_datos"), "K6", "Solo 7 comunas; la Comuna 2 no está.", KPIS),
    Componente("comunas.composicion", "comunas", "Construcciones con datos y severos por comuna y grupo de estrato", "tabla", ("/composicion",), ("comuna", "estrato", "sin_datos", "severo_estricto"), "", CONFUSION, GOLD),
    Componente("comunas.concentracion_1_2", "comunas", "Texto generado: comuna que concentra los estratos 1-2", "texto", ("/composicion",), ("comuna", "estrato", "sin_datos"), "", CONFUSION, GOLD),
    Componente("sensibilidades.grafico", "sensibilidades", "Diferencia 3-5 menos 1-2 por escenario", "grafico", ("/kpis/sensibilidad",), ("tasa", "ic95_inf", "ic95_sup"), "K2", "S4 es de baja confianza.", SENSIB),
    Componente("sensibilidades.tabla", "sensibilidades", "Escenarios, filtros y resultados", "tabla", ("/kpis/sensibilidad",), ("escenario", "grupo", "k", "n", "tasa", "nota"), "K2", "S2 no sustituye a S1.", SENSIB),
    Componente("sensibilidades.mantel_haenszel", "sensibilidades", "Razón ajustada por comuna (Mantel-Haenszel) y su advertencia", "tabla", ("/kpis/sensibilidad",), ("tasa", "nota"), "K2", "Solo la Comuna 18 tiene ambos grupos.", SENSIB),
    Componente("sensibilidades.conclusion", "sensibilidades", "Texto generado por escenario", "texto", ("/kpis/sensibilidad",), ("ic95_inf", "ic95_sup", "tasa"), "K2", CONFUSION, SENSIB),
    Componente("concentracion.k3", "concentracion", "Los 10 barrios con más severos y su participación", "tabla", ("/kpis",), ("valor", "numerador", "denominador", "nota"), "K3", "Concentración de casos no es mayor riesgo.", KPIS),
    Componente("concentracion.k4", "concentracion", "Spearman del estrato moda frente a la tasa por barrio", "metrica", ("/kpis",), ("valor", "denominador", "nota"), "K4", "Falacia ecológica; descriptivo.", KPIS),
    Componente("calidad.k5", "calidad", "Cobertura de la llave, estrato válido y nombre validado", "metrica", ("/calidad",), ("cobertura_llave", "cobertura_estrato_valido", "pct_nombre_validado", "llave_confianza"), "K5", "Qué NO demuestra: que el estrato de 2015 siga vigente.", CALIDAD),
    Componente("calidad.revision", "calidad", "Códigos de barrio con nombre no validado y su clasificación", "tabla", ("/llave/revision",), ("codigo_barrio", "nombre_barrio_csv", "nombre_poligono", "coincide_poligono"), "", "Es renumeración de códigos, no mala asignación.", GOLD),
    Componente("construcciones.tabla", "construcciones", "Tabla paginada con filtros de la API", "tabla", ("/construcciones",), ("objectid", "comuna", "barrio", "estrato", "clase_dano", "severo_estricto"), "", "Una página no representa a toda la muestra.", GOLD),
    Componente("construcciones.dispersion", "construcciones", "Dispersión lon/lat por clase de daño (no es un mapa cartográfico)", "grafico", ("/construcciones",), ("lon", "lat", "clase_dano"), "", "No es un mapa cartográfico.", GOLD),
    Componente("construcciones.descarga", "construcciones", "Descarga en CSV de lo mostrado", "descarga", ("/construcciones",), ("objectid", "comuna", "barrio", "estrato", "clase_dano"), "", "Solo las filas mostradas.", GOLD),
    Componente("fuentes.catalogo", "fuentes", "Fuentes con licencia y fechas", "tabla", ("/fuentes", "/metadata"), ("id", "rol", "licencia", "fechas"), "", "Licencias tomadas de los catálogos.", CATALOGO),
    Componente("fuentes.sistema", "fuentes", "Fecha de corte, almacenamiento activo y filas por tabla", "metrica", ("/health", "/metadata"), ("fecha_edicion_capa", "almacenamiento"), "", "Cifras de este equipo.", CONFIG),
    Componente("fuentes.limites", "fuentes", "Qué no se puede concluir y limitaciones", "texto", ("/metadata",), ("Qué NO se puede concluir",), "", ALCANCE, KPIS_MD),
)


def pagina(id_pagina):
    return next(p for p in PAGINAS if p.id == id_pagina)


def componentes_de(id_pagina):
    return tuple(c for c in COMPONENTES if c.pagina == id_pagina)
