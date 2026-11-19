"""Servicios y dependencias de seguridad JWT, RBAC y Cookies HttpOnly."""
from typing import Callable, List, Optional
from uuid import UUID
from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.auth.models import RevokedToken
from app.auth.schemas import LoginRequest, TokenResponse
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import PermissionDeniedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_dummy_password,
    verify_password,
)
from app.users.models import Usuario
from app.users.services import get_user_by_email, get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login/form",
    auto_error=False,
)


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Configura cookies seguras HttpOnly y SameSite para prevención contra XSS y CSRF."""
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.APP_COOKIE_SAMESITE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.APP_COOKIE_SAMESITE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    """Elimina las cookies HttpOnly de autenticación al cerrar sesión."""
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")


def is_token_revoked(db: Session, token: str) -> bool:
    """Verifica si un token ha sido invalidado previamente."""
    revoked = db.scalar(select(RevokedToken).where(RevokedToken.token == token))
    return revoked is not None


def authenticate_user(db: Session, login_in: LoginRequest) -> TokenResponse:
    """Valida credenciales con protección contra Timing Attacks y emite par de tokens JWT."""
    user = get_user_by_email(db, login_in.email)
    if not user:
        verify_dummy_password(login_in.password)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(login_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.estado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta de usuario se encuentra desactivada. Contacte al administrador.",
        )

    roles = user.role_names
    access_token = create_access_token(subject=str(user.id), roles=roles)
    refresh_token = create_refresh_token(subject=str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user.id,
        email=user.email,
        nombre_completo=user.nombre_completo,
        roles=roles,
    )


def refresh_access_token(db: Session, refresh_token: Optional[str]) -> TokenResponse:
    """Renueva el Access Token validando firma, tipo 'refresh' y lista negra."""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token no proporcionado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if is_token_revoked(db, refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El refresh token ha sido invalidado. Inicie sesión nuevamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    try:
        user_uuid = UUID(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identificador de sujeto inválido en el token.",
        )

    user = get_user_by_id(db, user_uuid)
    if not user.estado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta de usuario inactiva.",
        )

    # Rotación de refresh token: invalidar el anterior y emitir nuevo par
    db.add(RevokedToken(token=refresh_token, usuario_id=user.id))
    db.commit()

    roles = user.role_names
    new_access = create_access_token(subject=str(user.id), roles=roles)
    new_refresh = create_refresh_token(subject=str(user.id))

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user.id,
        email=user.email,
        nombre_completo=user.nombre_completo,
        roles=roles,
    )


def revoke_session_tokens(
    db: Session,
    user_id: UUID,
    access_token: Optional[str] = None,
    refresh_token: Optional[str] = None,
) -> None:
    """Registra los tokens activos en la lista negra al cerrar sesión."""
    for tok in (access_token, refresh_token):
        if tok and not is_token_revoked(db, tok):
            db.add(RevokedToken(token=tok, usuario_id=user_id))
    db.commit()


def get_current_user(
    request: Request,
    bearer_token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    """Dependencia que extrae y valida el usuario desde Authorization Bearer o Cookie HttpOnly."""
    token = bearer_token or request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado. Proporcione un token Bearer válido.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if is_token_revoked(db, token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión expirada o cerrada. Inicie sesión nuevamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acceso inválido o expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    try:
        user_uuid = UUID(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token malformado.",
        )

    user = db.scalar(select(Usuario).where(Usuario.id == user_uuid))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario asociado al token no existe.",
        )
    return user


def get_current_active_user(
    current_user: Usuario = Depends(get_current_user),
) -> Usuario:
    """Verifica que el usuario autenticado tenga estado activo."""
    if not current_user.estado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado.",
        )
    return current_user


def require_roles(allowed_roles: List[str]) -> Callable[[Usuario], Usuario]:
    """Fábrica de dependencias RBAC que exige al menos uno de los roles permitidos."""

    def role_checker(
        current_user: Usuario = Depends(get_current_active_user),
    ) -> Usuario:
        user_roles = set(current_user.role_names)
        if not user_roles.intersection(set(allowed_roles)):
            raise PermissionDeniedException(
                f"Acceso denegado. Se requiere uno de los siguientes roles: {', '.join(allowed_roles)}."
            )
        return current_user

    return role_checker


# Dependencias especializadas por perfil de negocio
get_current_active_admin = require_roles(["ADMINISTRADOR"])
get_current_active_ganadero = require_roles(["GANADERO"])
get_current_active_comprador = require_roles(["COMPRADOR"])
get_current_ganadero_or_admin = require_roles(["GANADERO", "ADMINISTRADOR"])
