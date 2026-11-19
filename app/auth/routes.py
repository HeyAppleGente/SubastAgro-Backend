"""Endpoints RESTful de Autenticación JWT, Refresh Tokens y Cookies HttpOnly."""
from typing import Optional
from fastapi import APIRouter, Body, Depends, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.auth.schemas import (
    LoginRequest,
    LogoutResponse,
    RefreshTokenRequest,
    TokenResponse,
)
from app.auth.services import (
    authenticate_user,
    clear_auth_cookies,
    get_current_active_user,
    oauth2_scheme,
    refresh_access_token,
    revoke_session_tokens,
    set_auth_cookies,
)
from app.core.database import get_db
from app.users.models import Usuario
from app.users.schemas import UserResponse

router = APIRouter(prefix="/auth", tags=["1. Autenticación (Auth & JWT)"])


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Iniciar sesión con JSON y obtener tokens JWT + Cookies HttpOnly",
)
def login(
    login_in: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Autentica correo y contraseña, devolviendo Access/Refresh Tokens y configurando Cookies HttpOnly."""
    token_data = authenticate_user(db, login_in)
    set_auth_cookies(response, token_data.access_token, token_data.refresh_token)
    return token_data


@router.post(
    "/login/form",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Iniciar sesión compatible con formulario OAuth2 de Swagger UI",
)
def login_oauth2_form(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Endpoint auxiliar para el botón Authorize de Swagger UI (/docs)."""
    login_in = LoginRequest(email=form_data.username, password=form_data.password)
    token_data = authenticate_user(db, login_in)
    set_auth_cookies(response, token_data.access_token, token_data.refresh_token)
    return token_data


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Renovar Access Token mediante Refresh Token (Cookie o JSON)",
)
def refresh_token(
    request: Request,
    response: Response,
    body: Optional[RefreshTokenRequest] = Body(default=None),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Rota el Refresh Token y emite un nuevo Access Token."""
    raw_refresh = (body.refresh_token if body else None) or request.cookies.get(
        "refresh_token"
    )
    token_data = refresh_access_token(db, raw_refresh)
    set_auth_cookies(response, token_data.access_token, token_data.refresh_token)
    return token_data


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Cerrar sesión e invalidar tokens activos",
)
def logout(
    request: Request,
    response: Response,
    bearer_token: Optional[str] = Depends(oauth2_scheme),
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LogoutResponse:
    """Revoca el Access Token y Refresh Token actuales y elimina las cookies de sesión."""
    access_tok = bearer_token or request.cookies.get("access_token")
    refresh_tok = request.cookies.get("refresh_token")
    revoke_session_tokens(db, current_user.id, access_tok, refresh_tok)
    clear_auth_cookies(response)
    return LogoutResponse()


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar perfil del usuario autenticado",
)
def read_current_user(
    current_user: Usuario = Depends(get_current_active_user),
) -> Usuario:
    """Retorna la información y roles del usuario autenticado sin campos sensibles."""
    return current_user
