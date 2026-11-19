"""Modelos ORM SQLAlchemy 2.0 para Razas de Ganado y Lotes de Ganado Vacuno."""
import uuid
from typing import List, Optional
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from app.core.database import Base


class RazaGanado(Base):
    """Catálogo de razas de ganado vacuno (Brahman, Angus, Gyr, Holstein, etc.)."""

    __tablename__ = "razas_ganado"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nombre_raza: Mapped[str] = mapped_column(
        String(80), unique=True, nullable=False, index=True
    )
    proposito: Mapped[str] = mapped_column(String(50), nullable=False)
    estado: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    lotes: Mapped[List["LoteGanado"]] = relationship(
        "LoteGanado", back_populates="raza"
    )

    @validates("proposito")
    def validate_proposito(self, key: str, value: str) -> str:
        allowed = {"CARNE", "LECHE", "DOBLE PROPÓSITO", "DOBLE PROPOSITO"}
        upper_v = value.strip().upper()
        if upper_v not in allowed:
            raise ValueError(
                "El propósito debe ser Carne, Leche o Doble Propósito."
            )
        return "Doble Propósito" if "DOBLE" in upper_v else value.strip().capitalize()


class LoteGanado(Base):
    """Entidad que representa un lote de reses registrado por un Ganadero."""

    __tablename__ = "lotes_ganado"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ganadero_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    raza_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("razas_ganado.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    codigo_lote: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    cantidad_cabezas: Mapped[int] = mapped_column(Integer, nullable=False)
    peso_promedio_kg: Mapped[float] = mapped_column(Float, nullable=False)
    vacunacion_al_dia: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    ubicacion_hacienda: Mapped[str] = mapped_column(String(200), nullable=False)
    estado_lote: Mapped[str] = mapped_column(
        String(30), default="DISPONIBLE", nullable=False
    )

    ganadero: Mapped["Usuario"] = relationship(
        "Usuario", back_populates="lotes", foreign_keys=[ganadero_id]
    )
    raza: Mapped["RazaGanado"] = relationship("RazaGanado", back_populates="lotes")
    evento_subasta: Mapped[Optional["EventoSubasta"]] = relationship(
        "EventoSubasta", back_populates="lote", uselist=False
    )

    @validates("cantidad_cabezas")
    def validate_cabezas(self, key: str, value: int) -> int:
        if value <= 0:
            raise ValueError("La cantidad de cabezas debe ser mayor a 0.")
        return value

    @validates("peso_promedio_kg")
    def validate_peso(self, key: str, value: float) -> float:
        if value <= 0:
            raise ValueError("El peso promedio en kg debe ser mayor a 0.")
        return value

    @validates("estado_lote")
    def validate_estado_lote(self, key: str, value: str) -> str:
        allowed = {"DISPONIBLE", "EN_SUBASTA", "VENDIDO", "INACTIVO"}
        upper_v = value.strip().upper()
        if upper_v not in allowed:
            raise ValueError(f"Estado de lote inválido: {value}. Permitidos: {allowed}")
        return upper_v
