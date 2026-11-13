"""Fábrica de la aplicación FastAPI: solo rutas GET, solo lectura, enlazada a 127.0.0.1 por defecto.

Ejecución: python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000
"""
import json
import time
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Path as RutaParam, Query, Request

from src.api import errores, esquemas
from src.api.repositorio import RepositorioSqlite
from src.common import ROOT, load_config, read_manifest
from src.logger import get_logger

log = get_logger(__name__)
ERRORES = {404: {"model": esquemas.ErrorRespuesta}, 422: {"model": esquemas.ErrorRespuesta}, 503: {"model": esquemas.ErrorRespuesta}}
ALCANCE = "Estrato 2015 asignado por lados de manzana (barrio); análisis de las 7 comunas con polígonos de afectación preliminar; no se generaliza a Cali."


def _leer_catalogo(ruta):
    if not ruta.is_file():
        raise errores.BaseNoDisponible(f"no existe {ruta.name}")
    return json.loads(ruta.read_text(encoding="utf-8"))


def _salida(modelo, filas):
    return [modelo(**f) for f in filas]


def crear_app(ruta_db=None):
    """Crea la aplicación; ruta_db permite probar con otra base sin tocar la configuración."""
    cfg = load_config()
    api = cfg["api"]
    ruta_base = Path(ruta_db) if ruta_db else ROOT / api["base_datos"]
    ruta_catalogo = ROOT / api["catalogo_fuentes"]
    lim_def, lim_max = api["limite_defecto"], api["limite_maximo"]

    app = FastAPI(title="API de solo lectura · Gold del sismo de Cali", version=api["version"],
                  description="Entrega los resultados ya calculados (Gold). No escribe, no recalcula. " + api["aviso"])
    errores.registrar(app)

    def repo():
        """Una conexión por solicitud; se cierra siempre al terminar."""
        r = RepositorioSqlite(ruta_base)
        try:
            yield r
        finally:
            r.cerrar()

    @app.middleware("http")
    async def registrar_solicitud(request: Request, call_next):
        t0 = time.perf_counter()
        estado = 500
        try:
            respuesta = await call_next(request)
            estado = respuesta.status_code
            return respuesta
        finally:
            log.info("%s %s -> %s en %.1f ms", request.method, request.url.path, estado, (time.perf_counter() - t0) * 1000)

    @app.get("/health", response_model=esquemas.Salud, tags=["servicio"])
    def health():
        """Estado del servicio, fecha de corte y filas por tabla."""
        base = {"estado": "ok", "version_api": api["version"], "fecha_corte": None, "base_disponible": False, "filas_por_tabla": {}}
        r = None
        try:
            r = RepositorioSqlite(ruta_base)
            base.update(fecha_corte=r.fecha_corte(), base_disponible=True, filas_por_tabla=r.filas_por_tabla())
        except errores.BaseNoDisponible:
            base["estado"] = "degradado"
        finally:
            if r is not None:
                r.cerrar()
        return base

    @app.get("/metadata", response_model=esquemas.Metadata, responses=ERRORES, tags=["servicio"])
    def metadata(r=Depends(repo)):
        """Fuentes, fechas, población analizada, alcance temporal y licencias."""
        cat = _leer_catalogo(ruta_catalogo)
        fechas = cfg["fechas"]
        fuentes = [{"source_id": m["source_id"], "filas": m["rows"], "bytes": m["bytes"], "extraido_utc": m["fetched_at_utc"], "sha256": m["sha256"]}
                   for m in read_manifest()]
        return {"aviso": api["aviso"], "fecha_edicion_capa": fechas["fecha_edicion_capa"], "fecha_imagen_pre": fechas["fecha_imagen_pre"],
                "fecha_imagen_post": fechas["fecha_imagen_post"], "fecha_corte": r.fecha_corte(), "poblacion": r.poblacion(), "alcance_temporal": ALCANCE,
                "licencias": {f["id"]: f["licencia"] for f in cat["fuentes"]}, "fuentes": fuentes}

    @app.get("/fuentes", responses=ERRORES, tags=["servicio"])
    def fuentes():
        """Catálogo de fuentes y metadatos (generado desde el manifiesto)."""
        return _leer_catalogo(ruta_catalogo)

    # /kpis/sensibilidad se declara ANTES de /kpis/{kpi_id}: si no, "sensibilidad" se leería como un kpi_id
    @app.get("/kpis/sensibilidad", response_model=list[esquemas.FilaSensibilidad], responses=ERRORES, tags=["indicadores"])
    def kpis_sensibilidad(escenario: Optional[str] = Query(None, pattern=r"^S[0-5]$"), r=Depends(repo)):
        """Filas de kpis_sensibilidad (escenarios S0 a S5)."""
        return _salida(esquemas.FilaSensibilidad, r.sensibilidad(escenario))

    @app.get("/kpis", response_model=list[esquemas.FilaKpi], responses=ERRORES, tags=["indicadores"])
    def kpis(kpi_id: Optional[str] = Query(None, pattern=r"^K\d{1,2}$"), grupo: Optional[str] = Query(None, max_length=60), r=Depends(repo)):
        """Filas de kpis_gold tal como están."""
        return _salida(esquemas.FilaKpi, r.kpis(kpi_id, grupo))

    @app.get("/kpis/{kpi_id}", response_model=list[esquemas.FilaKpi], responses=ERRORES, tags=["indicadores"])
    def kpi(kpi_id: str = RutaParam(pattern=r"^K\d{1,2}$"), r=Depends(repo)):
        """Todas las filas de un indicador."""
        filas = r.kpis(kpi_id)
        if not filas:
            raise HTTPException(status_code=404, detail=f"no existe el indicador {kpi_id}")
        return _salida(esquemas.FilaKpi, filas)

    @app.get("/comunas", response_model=list[esquemas.FilaComuna], responses=ERRORES, tags=["indicadores"])
    def comunas(r=Depends(repo)):
        """K6 por comuna, tal como está en kpis_gold."""
        return _salida(esquemas.FilaComuna, r.comunas())

    @app.get("/composicion", response_model=list[esquemas.FilaComposicion], responses=ERRORES, tags=["indicadores"])
    def composicion(r=Depends(repo)):
        """Construcciones con datos y severos por comuna y grupo de estrato (1-2, 3-5, 6)."""
        return _salida(esquemas.FilaComposicion, r.composicion())

    @app.get("/construcciones", response_model=esquemas.PaginaConstrucciones, responses=ERRORES, tags=["datos"])
    def construcciones(limit: int = Query(lim_def, ge=1, le=lim_max), offset: int = Query(0, ge=0, le=10_000_000),
                       comuna: Optional[str] = Query(None, pattern=r"^\d{2}$"), estrato: Optional[int] = Query(None, ge=1, le=6),
                       severo_estricto: Optional[bool] = None, r=Depends(repo)):
        """Construcciones paginadas y ordenadas por objectid."""
        total, items = r.construcciones(limit, offset, comuna, estrato, severo_estricto)
        return {"total": total, "limit": limit, "offset": offset, "items": items}

    @app.get("/calidad", response_model=esquemas.Calidad, responses=ERRORES, tags=["calidad"])
    def calidad():
        """Coberturas y confianza de la llave, leídas de quality_report.json."""
        ruta = ROOT / load_config()["paths_silver"]["quality_report"]
        q = _leer_catalogo(ruta)
        return {k: q[k] for k in ("cobertura_llave", "cobertura_estrato_valido", "pct_nombre_validado", "llave_confianza")}

    @app.get("/llave/revision", response_model=esquemas.RevisionLlave, responses=ERRORES, tags=["calidad"])
    def llave_revision(r=Depends(repo)):
        """Códigos de barrio con nombre no validado entre el CSV 2015 y el polígono."""
        items = r.revision_llave()
        return {"documento": "docs/revision_codigos_barrio.md", "total_codigos": len(items), "items": items}

    return app


app = crear_app()
