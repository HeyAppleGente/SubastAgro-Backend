"""Esquemas Pydantic v2 para Pujas y Ofertas."""
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class BidCreate(BaseModel):
    """Esquema para emitir una puja económica en una subasta activa."""

    subasta_id: UUID = Field(..., description="UUID del evento de subasta activo")
    monto_ofertado_kilo: Decimal = Field(..., gt=0, examples=[8700.00])


class BidResponse(BaseModel):
    """Esquema de respuesta de puja registrada."""

    id: UUID
    subasta_id: UUID
    comprador_id: UUID
    monto_ofertado_kilo: Decimal
    fecha_hora_puja: datetime

    model_config = ConfigDict(from_attributes=True)
