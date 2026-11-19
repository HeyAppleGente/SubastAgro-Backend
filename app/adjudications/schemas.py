"""Esquemas Pydantic v2 para Actas de Adjudicación."""
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class AdjudicationPaymentUpdate(BaseModel):
    """Esquema para actualizar estado de pago del acta."""

    estado_pago: str = Field(..., examples=["PAGADO"])


class AdjudicationResponse(BaseModel):
    """Esquema de respuesta del Acta de Adjudicación."""

    id: UUID
    subasta_id: UUID
    comprador_ganador_id: UUID
    puja_ganadora_id: UUID
    monto_total_final: Decimal
    guia_movilizacion_codigo: str
    estado_pago: str
    fecha_cierre: datetime

    model_config = ConfigDict(from_attributes=True)
