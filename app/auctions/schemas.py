"""Esquemas Pydantic v2 para Eventos de Subasta."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from app.auctions.models import EstadoSubasta
from app.cattle_lots.schemas import CattleLotResponse


class AuctionCreate(BaseModel):
    """Esquema para programar un nuevo evento de subasta ganadera."""

    lote_id: UUID = Field(..., description="UUID del lote de ganado disponible")
    precio_base_kilo: Decimal = Field(..., gt=0, examples=[8500.00])
    incremento_minimo_puja: Decimal = Field(..., gt=0, examples=[100.00])
    fecha_inicio: datetime = Field(..., examples=["2026-11-20T09:00:00Z"])
    fecha_cierre: datetime = Field(..., examples=["2026-11-20T18:00:00Z"])
    estado_subasta: EstadoSubasta = Field(
        default=EstadoSubasta.PROGRAMADA, examples=["ACTIVA"]
    )

    @model_validator(mode="after")
    def validate_dates(self) -> "AuctionCreate":
        if self.fecha_cierre <= self.fecha_inicio:
            raise ValueError("La fecha_cierre debe ser estrictamente posterior a fecha_inicio.")
        return self


class AuctionUpdate(BaseModel):
    """Esquema para actualizar parámetros de una subasta programada."""

    precio_base_kilo: Optional[Decimal] = Field(default=None, gt=0)
    incremento_minimo_puja: Optional[Decimal] = Field(default=None, gt=0)
    fecha_inicio: Optional[datetime] = None
    fecha_cierre: Optional[datetime] = None


class AuctionStatusUpdate(BaseModel):
    """Esquema para transición de estado de un evento de subasta."""

    estado_subasta: EstadoSubasta = Field(..., examples=["ACTIVA"])

    @field_validator("estado_subasta", mode="before")
    @classmethod
    def normalize_status(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().upper()
        return v


class AuctionResponse(BaseModel):
    """Esquema de respuesta con detalle completo de la subasta."""

    id: UUID
    lote_id: UUID
    precio_base_kilo: Decimal
    incremento_minimo_puja: Decimal
    fecha_inicio: datetime
    fecha_cierre: datetime
    estado_subasta: str
    oferta_actual_kilo: Optional[Decimal] = None
    total_pujas: int = 0
    lote: Optional[CattleLotResponse] = None

    model_config = ConfigDict(from_attributes=True)
