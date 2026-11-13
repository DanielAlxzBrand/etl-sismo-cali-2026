"""Manejadores de error: todas las respuestas de error usan {"error": {"codigo", "mensaje", "detalle"}}."""
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.logger import get_logger

log = get_logger(__name__)

CODIGOS = {404: "no_encontrado", 405: "metodo_no_permitido", 422: "parametros_invalidos", 500: "error_interno", 503: "base_no_disponible"}


class BaseNoDisponible(Exception):
    """Un recurso de datos (base de Gold, catálogo o informe) no existe o no se puede abrir."""


def cuerpo(codigo, mensaje, detalle=None):
    return {"error": {"codigo": codigo, "mensaje": mensaje, "detalle": detalle}}


def registrar(app):
    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        return JSONResponse(cuerpo(CODIGOS.get(exc.status_code, "error_http"), str(exc.detail)), status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def _validacion(request: Request, exc: RequestValidationError):
        # solo ubicación y mensaje de cada error: nunca el valor recibido completo
        detalle = [{"campo": ".".join(str(p) for p in e["loc"]), "mensaje": e["msg"]} for e in exc.errors()]
        return JSONResponse(cuerpo("parametros_invalidos", "Algún parámetro no es válido.", detalle), status_code=422)

    @app.exception_handler(BaseNoDisponible)
    async def _base(request: Request, exc: BaseNoDisponible):
        return JSONResponse(cuerpo("base_no_disponible", "Un recurso de datos necesario no está disponible."), status_code=503)

    @app.exception_handler(Exception)
    async def _interno(request: Request, exc: Exception):
        # la traza va al registro; la respuesta no lleva trazas ni rutas locales
        log.exception("error interno en %s %s", request.method, request.url.path)
        return JSONResponse(cuerpo("error_interno", "Ocurrió un error interno."), status_code=500)
