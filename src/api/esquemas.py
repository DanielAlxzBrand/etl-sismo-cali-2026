"""Modelos de respuesta de la API (lo que se entrega es lo que ya está en Gold; sin recálculo)."""
from typing import Any, Optional

from pydantic import BaseModel


class ErrorDetalle(BaseModel):
    codigo: str
    mensaje: str
    detalle: Optional[Any] = None


class ErrorRespuesta(BaseModel):
    error: ErrorDetalle


class Salud(BaseModel):
    estado: str
    version_api: str
    fecha_corte: Optional[str]
    base_disponible: bool
    filas_por_tabla: dict[str, int]


class FilaKpi(BaseModel):
    kpi_id: str
    nombre: Optional[str]
    valor: Optional[float]
    numerador: Optional[float]
    denominador: Optional[float]
    grupo: Optional[str]
    fecha_corte: Optional[str]
    fuente: Optional[str]
    ic95_inf: Optional[float]
    ic95_sup: Optional[float]
    n_sin_datos: Optional[float]
    pct_sin_datos: Optional[float]
    muestra_baja: Optional[bool]
    cota_inf: Optional[float]
    cota_sup: Optional[float]
    nota: Optional[str]


class FilaSensibilidad(BaseModel):
    escenario: str
    kpi_id: str
    grupo: Optional[str]
    k: Optional[float]
    n: Optional[float]
    tasa: Optional[float]
    ic95_inf: Optional[float]
    ic95_sup: Optional[float]
    nota: Optional[str]


class FilaComuna(BaseModel):
    comuna: str
    n_con_datos: Optional[float]
    severos: Optional[float]
    tasa: Optional[float]
    ic95_inf: Optional[float]
    ic95_sup: Optional[float]
    n_sin_datos: Optional[float]
    pct_sin_datos: Optional[float]
    muestra_baja: Optional[bool]


class FilaComposicion(BaseModel):
    comuna: str
    grupo_estrato: str
    n_con_datos: int
    severos: int


class Construccion(BaseModel):
    objectid: int
    comuna: Optional[str]
    barrio: Optional[str]
    codigo_barrio: Optional[str]
    nombre_barrio_csv: Optional[str]
    estrato: Optional[float]
    sin_datos: Optional[bool]
    severo_estricto: Optional[bool]
    estado_estructural: Optional[str]
    clase_dano: Optional[str]
    lon: Optional[float]
    lat: Optional[float]
    coincide_poligono: Optional[bool]
    nombre_validado: Optional[bool]


class PaginaConstrucciones(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[Construccion]


class Calidad(BaseModel):
    cobertura_llave: dict[str, Any]
    cobertura_estrato_valido: dict[str, Any]
    pct_nombre_validado: dict[str, Any]
    llave_confianza: Optional[str]


class CodigoRevision(BaseModel):
    codigo_barrio: str
    n_construcciones: int
    nombre_csv_2015: Optional[str]
    nombre_poligono_dominante: Optional[str]
    pct_coincide_poligono: float


class RevisionLlave(BaseModel):
    documento: str
    total_codigos: int
    items: list[CodigoRevision]


class Poblacion(BaseModel):
    construcciones: int
    con_datos_satelitales: int
    comunas: int
    codigos_barrio: int


class Metadata(BaseModel):
    aviso: str
    fecha_edicion_capa: Optional[str]
    fecha_imagen_pre: Optional[str]
    fecha_imagen_post: Optional[str]
    fecha_corte: Optional[str]
    poblacion: Poblacion
    alcance_temporal: str
    licencias: dict[str, str]
    fuentes: list[dict[str, Any]]
