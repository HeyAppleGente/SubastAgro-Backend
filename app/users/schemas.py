"""Esquemas Pydantic v2 para validación de Usuarios y Roles sin exponer datos sensibles."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.core.security import validate_password_complexity


class RoleResponse(BaseModel):
    """Esquema de respuesta de rol."""

    id: int
    nombre_rol: str
    descripcion: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    """Esquema de creación/registro de usuario."""

    email: EmailStr = Field(..., examples=["ganadero@subastagro.co"])
    password: str = Field(..., min_length=8, max_length=100, examples=["Ganadero2026*"])
    nombre_completo: str = Field(..., min_length=3, max_length=150, examples=["Carlos Alberto Mendoza"])
    documento_identidad: str = Field(..., min_length=5, max_length=40, examples=["1098765432"])
    telefono: Optional[str] = Field(default=None, max_length=30, examples=["+57 3104567890"])
    rol: str = Field(default="COMPRADOR", examples=["GANADERO"])

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        validate_password_complexity(v)
        return v

    @field_validator("rol")
    @classmethod
    def check_rol(cls, v: str) -> str:
        allowed = {"GANADERO", "COMPRADOR", "ADMINISTRADOR"}
        upper_v = v.strip().upper()
        if upper_v not in allowed:
            raise ValueError("El rol debe ser GANADERO, COMPRADOR o ADMINISTRADOR.")
        return upper_v


class UserUpdate(BaseModel):
    """Esquema de actualización parcial de perfil de usuario."""

    nombre_completo: Optional[str] = Field(default=None, min_length=3, max_length=150)
    telefono: Optional[str] = Field(default=None, max_length=30)


class UserStatusUpdate(BaseModel):
    """Esquema administrativo para activar o desactivar cuentas."""

    estado: bool = Field(..., examples=[True])


class UserResponse(BaseModel):
    """Esquema seguro de salida de usuario (NUNCA expone password_hash)."""

    id: UUID
    email: EmailStr
    nombre_completo: str
    documento_identidad: str
    telefono: Optional[str] = None
    estado: bool
    fecha_creacion: datetime
    roles: List[RoleResponse] = []

    model_config = ConfigDict(from_attributes=True)
