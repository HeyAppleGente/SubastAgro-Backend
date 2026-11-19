"""Modelos ORM SQLAlchemy 2.0 para Actas de Adjudicación."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from app.core.database import Base


class ActaAdjudicacion(Base):
    """Cierre legal, sanitario y financiero de una subasta ganadera adjudicada."""

    __tablename__ = "actas_adjudicacion"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    subasta_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("eventos_subasta.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
        index=True,
    )
    comprador_ganador_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    puja_ganadora_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pujas_ofertas.id", ondelete="RESTRICT"),
        nullable=False,
    )
    monto_total_final: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    guia_movilizacion_codigo: Mapped[str] = mapped_column(
        String(60), unique=True, nullable=False, index=True
    )
    estado_pago: Mapped[str] = mapped_column(
        String(30), default="PENDIENTE", nullable=False
    )
    fecha_cierre: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    subasta: Mapped["EventoSubasta"] = relationship(
        "EventoSubasta", back_populates="acta_adjudicacion"
    )
    comprador_ganador: Mapped["Usuario"] = relationship(
        "Usuario", back_populates="actas_ganadas", foreign_keys=[comprador_ganador_id]
    )
    puja_ganadora: Mapped["PujaOferta"] = relationship("PujaOferta")

    @validates("monto_total_final")
    def validate_total(self, key: str, value: Decimal) -> Decimal:
        if Decimal(str(value)) <= Decimal("0"):
            raise ValueError("El monto total final debe ser mayor a 0.")
        return value
