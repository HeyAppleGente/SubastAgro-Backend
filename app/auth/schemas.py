"""Esquemas Pydantic v2 para autenticación JWT (Login, Refresh, Logout)."""
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Credenciales de acceso para inicio de sesión."""

    email: EmailStr = Field(..., examples=["ganadero@subastagro.co"])
    password: str = Field(..., min_length=6, examples=["Ganadero2026*"])


class RefreshTokenRequest(BaseModel):
    """Solicitud opcional por body para renovar el Access Token (también soporta Cookie HttpOnly)."""

    refresh_token: Optional[str] = Field(default=None)


class TokenResponse(BaseModel):
    """Respuesta estándar con Access Token, Refresh Token y metadatos de sesión."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: UUID
    email: EmailStr
    nombre_completo: str
    roles: List[str]


class LogoutResponse(BaseModel):
    """Confirmación de cierre de sesión seguro."""

    success: bool = True
    message: str = "Sesión cerrada e invalidada correctamente."
