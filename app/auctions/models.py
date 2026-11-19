"""Modelos ORM SQLAlchemy 2.0 para Eventos de Subasta."""
import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from app.core.database import Base


class EstadoSubasta(str, enum.Enum):
    """Estados del ciclo de vida de un evento de subasta."""

    PROGRAMADA = "PROGRAMADA"
    ACTIVA = "ACTIVA"
    FINALIZADA = "FINALIZADA"
    DESIERTA = "DESIERTA"


class EventoSubasta(Base):
    """Entidad que representa la programación y reglas económicas de una subasta ganadera."""

    __tablename__ = "eventos_subasta"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    lote_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lotes_ganado.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
        index=True,
    )
    precio_base_kilo: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    incremento_minimo_puja: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    fecha_inicio: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    fecha_cierre: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    estado_subasta: Mapped[str] = mapped_column(
        String(30), default=EstadoSubasta.PROGRAMADA.value, nullable=False, index=True
    )

    lote: Mapped["LoteGanado"] = relationship(
        "LoteGanado", back_populates="evento_subasta"
    )
    pujas: Mapped[List["PujaOferta"]] = relationship(
        "PujaOferta",
        back_populates="subasta",
        order_by="PujaOferta.monto_ofertado_kilo.desc()",
    )
    acta_adjudicacion: Mapped[Optional["ActaAdjudicacion"]] = relationship(
        "ActaAdjudicacion", back_populates="subasta", uselist=False
    )

    @validates("precio_base_kilo")
    def validate_precio_base(self, key: str, value: Decimal) -> Decimal:
        if Decimal(str(value)) <= Decimal("0"):
            raise ValueError("El precio base por kilo debe ser mayor a 0.")
        return value

    @validates("incremento_minimo_puja")
    def validate_incremento(self, key: str, value: Decimal) -> Decimal:
        if Decimal(str(value)) <= Decimal("0"):
            raise ValueError("El incremento mínimo por puja debe ser mayor a 0.")
        return value

    @validates("estado_subasta")
    def validate_estado(self, key: str, value: str) -> str:
        allowed = {e.value for e in EstadoSubasta}
        upper_v = value.strip().upper()
        if upper_v not in allowed:
            raise ValueError(f"Estado de subasta inválido: {value}. Permitidos: {allowed}")
        return upper_v
