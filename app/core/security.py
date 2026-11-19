"""Módulo de seguridad OWASP: Hashing Bcrypt, JWT Access/Refresh y protección Timing Attack."""
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash ficticio precalculado para prevenir Timing Attacks en usuarios inexistentes
DUMMY_HASH = pwd_context.hash("SubastAgroDummyTimingProtection2026!")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña en texto plano contra su hash Bcrypt."""
    return pwd_context.verify(plain_password, hashed_password)


def verify_dummy_password(plain_password: str) -> None:
    """Ejecuta verificación contra hash ficticio para igualar tiempos de respuesta."""
    pwd_context.verify(plain_password, DUMMY_HASH)


def get_password_hash(password: str) -> str:
    """Genera un hash Bcrypt seguro a partir de una contraseña en texto plano."""
    return pwd_context.hash(password)


def validate_password_complexity(password: str) -> None:
    """Valida complejidad mínima OWASP: >= 8 caracteres, al menos una letra y un número."""
    if len(password) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres.")
    if not re.search(r"[A-Za-z]", password):
        raise ValueError("La contraseña debe incluir al menos una letra.")
    if not re.search(r"\d", password):
        raise ValueError("La contraseña debe incluir al menos un número.")


def create_access_token(
    subject: str,
    roles: Optional[list[str]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Genera un token JWT de acceso firmado con HS256."""
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "roles": roles or [],
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(
        to_encode, settings.APP_JWT_SECRET, algorithm=settings.APP_JWT_ALGORITHM
    )


def create_refresh_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Genera un token JWT de refresco firmado con HS256."""
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta
        else timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(
        to_encode, settings.APP_JWT_SECRET, algorithm=settings.APP_JWT_ALGORITHM
    )


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodifica y valida firma y expiración de un token JWT."""
    try:
        payload = jwt.decode(
            token,
            settings.APP_JWT_SECRET,
            algorithms=[settings.APP_JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        return None
