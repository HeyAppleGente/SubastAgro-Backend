"""Punto de entrada principal de SubastAgro API (FastAPI + PostgreSQL 18 + OWASP)."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.adjudications.routes import router as adjudications_router
from app.auctions.routes import router as auctions_router
from app.auth.routes import router as auth_router
from app.bids.routes import router as bids_router
from app.cattle_lots.routes import router as cattle_lots_router
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.exceptions import register_exception_handlers
from app.core.middleware import OWASPSecurityHeadersMiddleware
from app.users.routes import router as users_router
from app.users.services import get_or_create_role

from app.users import models as _users_models  # noqa: F401
from app.auth import models as _auth_models  # noqa: F401
from app.cattle_lots import models as _cattle_models  # noqa: F401
from app.auctions import models as _auctions_models  # noqa: F401
from app.bids import models as _bids_models  # noqa: F401
from app.adjudications import models as _adj_models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa tablas en PostgreSQL (subastagro_db) y roles base al arrancar."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for role_name in ("ADMINISTRADOR", "GANADERO", "COMPRADOR"):
            get_or_create_role(db, role_name)
        db.commit()
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Plataforma RESTful de Subastas de Ganado Vacuno (SubastAgro). "
        "Clean Architecture, SQLAlchemy 2.0, Pydantic v2 y Seguridad OWASP Top 10."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(OWASPSecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.APP_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

register_exception_handlers(app)

app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(users_router, prefix=settings.API_V1_PREFIX)
app.include_router(cattle_lots_router, prefix=settings.API_V1_PREFIX)
app.include_router(auctions_router, prefix=settings.API_V1_PREFIX)
app.include_router(bids_router, prefix=settings.API_V1_PREFIX)
app.include_router(adjudications_router, prefix=settings.API_V1_PREFIX)


@app.get(f"{settings.API_V1_PREFIX}/health", tags=["Sistema"])
def health_check() -> dict:
    """Endpoint de verificación de salud de la API."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "database": settings.DB_NAME,
    }
