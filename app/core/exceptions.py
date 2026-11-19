"""Manejo centralizado de excepciones HTTP y seguridad OWASP."""
import logging
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

logger = logging.getLogger("subastagro.security")


class BusinessRuleException(HTTPException):
    """Excepción para violaciones de reglas de negocio ganaderas (HTTP 400)."""

    def __init__(self, detail: str) -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class ResourceNotFoundException(HTTPException):
    """Excepción para recursos inexistentes en base de datos (HTTP 404)."""

    def __init__(self, detail: str = "Recurso no encontrado.") -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class PermissionDeniedException(HTTPException):
    """Excepción para violaciones de RBAC o Ownership (HTTP 403)."""

    def __init__(
        self, detail: str = "No tiene permisos o propiedad sobre este recurso."
    ) -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def register_exception_handlers(app: FastAPI) -> None:
    """Registra manejadores globales sin filtrar trazas internas ni información sensible."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "status_code": exc.status_code,
                "detail": exc.detail,
                "path": str(request.url.path),
            },
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        sanitized_errors = [
            {
                "campo": " -> ".join(str(loc) for loc in err.get("loc", [])),
                "mensaje": err.get("msg"),
                "tipo": err.get("type"),
            }
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "status_code": 422,
                "detail": "Error de validación en los datos enviados.",
                "errors": sanitized_errors,
            },
        )

    @app.exception_handler(IntegrityError)
    async def integrity_exception_handler(
        request: Request, exc: IntegrityError
    ) -> JSONResponse:
        logger.warning(f"IntegrityError en {request.url.path}: {exc.orig}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "status_code": 400,
                "detail": "Conflicto de integridad de datos (registro duplicado o referencia inválida).",
            },
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(
        request: Request, exc: SQLAlchemyError
    ) -> JSONResponse:
        logger.error(f"Database error en {request.url.path}: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "status_code": 500,
                "detail": "Error interno en el servicio de persistencia de datos.",
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error(f"Unhandled exception en {request.url.path}: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "status_code": 500,
                "detail": "Error interno inesperado del servidor.",
            },
        )
