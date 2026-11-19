"""Modelos ORM SQLAlchemy 2.0 para Pujas y Ofertas en Subastas."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from app.core.database import Base


class PujaOferta(Base):
    """Entidad que registra cada oferta económica de un Comprador en una Subasta."""

    __tablename__ = "pujas_ofertas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    subasta_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("eventos_subasta.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    comprador_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    monto_ofertado_kilo: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    fecha_hora_puja: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    subasta: Mapped["EventoSubasta"] = relationship(
        "EventoSubasta", back_populates="pujas"
    )
    comprador: Mapped["Usuario"] = relationship(
        "Usuario", back_populates="pujas", foreign_keys=[comprador_id]
    )

    @validates("monto_ofertado_kilo")
    def validate_monto(self, key: str, value: Decimal) -> Decimal:
        if Decimal(str(value)) <= Decimal("0"):
            raise ValueError("El monto ofertado por kilo debe ser mayor a 0.")
        return value
