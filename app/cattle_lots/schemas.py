"""Esquemas Pydantic v2 para Razas y Lotes de Ganado Vacuno."""
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class BreedCreate(BaseModel):
    """Esquema para crear una nueva raza de ganado vacuno."""

    nombre_raza: str = Field(..., min_length=2, max_length=80, examples=["Brahman"])
    proposito: str = Field(..., examples=["Carne"])

    @field_validator("proposito")
    @classmethod
    def validate_proposito(cls, v: str) -> str:
        allowed = {"CARNE", "LECHE", "DOBLE PROPÓSITO", "DOBLE PROPOSITO"}
        if v.strip().upper() not in allowed:
            raise ValueError("El propósito debe ser Carne, Leche o Doble Propósito.")
        return v.strip()


class BreedResponse(BaseModel):
    """Esquema de respuesta de raza de ganado."""

    id: UUID
    nombre_raza: str
    proposito: str
    estado: bool

    model_config = ConfigDict(from_attributes=True)


class CattleLotCreate(BaseModel):
    """Esquema para registrar un nuevo lote de ganado vacuno."""

    raza_id: UUID = Field(..., description="UUID de la raza de ganado")
    codigo_lote: str = Field(
        ..., min_length=3, max_length=50, examples=["LOT-2026-BRH-001"]
    )
    cantidad_cabezas: int = Field(..., gt=0, le=5000, examples=[25])
    peso_promedio_kg: float = Field(..., gt=20.0, le=1500.0, examples=[460.5])
    vacunacion_al_dia: bool = Field(default=True, examples=[True])
    ubicacion_hacienda: str = Field(
        ...,
        min_length=4,
        max_length=200,
        examples=["Hacienda La Esperanza, Montería - Córdoba"],
    )


class CattleLotUpdate(BaseModel):
    """Esquema para actualizar un lote de ganado existente."""

    raza_id: Optional[UUID] = None
    cantidad_cabezas: Optional[int] = Field(default=None, gt=0, le=5000)
    peso_promedio_kg: Optional[float] = Field(default=None, gt=20.0, le=1500.0)
    vacunacion_al_dia: Optional[bool] = None
    ubicacion_hacienda: Optional[str] = Field(default=None, min_length=4, max_length=200)
    estado_lote: Optional[str] = Field(default=None, examples=["DISPONIBLE"])


class CattleLotResponse(BaseModel):
    """Esquema de salida con los datos completos del lote de ganado."""

    id: UUID
    ganadero_id: UUID
    raza_id: UUID
    codigo_lote: str
    cantidad_cabezas: int
    peso_promedio_kg: float
    vacunacion_al_dia: bool
    ubicacion_hacienda: str
    estado_lote: str
    raza: Optional[BreedResponse] = None

    model_config = ConfigDict(from_attributes=True)
