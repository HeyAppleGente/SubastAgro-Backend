"""Conexión y gestión de sesiones de base de datos PostgreSQL con SQLAlchemy 2.0."""
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from app.core.config import settings


class Base(DeclarativeBase):
    """Clase base declarativa para todos los modelos ORM de SubastAgro."""
    pass


engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.APP_DEBUG and not settings.is_production,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    """Dependencia FastAPI que provee una sesión transaccional de base de datos."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
