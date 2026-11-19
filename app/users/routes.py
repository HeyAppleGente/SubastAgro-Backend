"""Endpoints RESTful de gestión de Usuarios y Control de Roles."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.auth.services import (
    get_current_active_admin,
    get_current_active_user,
)
from app.core.database import get_db
from app.core.exceptions import PermissionDeniedException
from app.users.models import Usuario
from app.users.schemas import (
    UserCreate,
    UserResponse,
    UserStatusUpdate,
    UserUpdate,
)
from app.users.services import (
    create_user,
    get_user_by_id,
    list_users,
    update_user_profile,
    update_user_status,
)

router = APIRouter(prefix="/users", tags=["2. Usuarios y Roles (Users & RBAC)"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario (GANADERO o COMPRADOR)",
)
def register_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
) -> Usuario:
    """Permite el registro público de Ganaderos y Compradores con validación estricta Pydantic v2."""
    return create_user(db, user_in, allow_admin_creation=False)


@router.get(
    "",
    response_model=List[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar todos los usuarios registrados (Solo ADMINISTRADOR)",
)
def get_all_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    current_admin: Usuario = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
) -> List[Usuario]:
    """Retorna listado de usuarios del sistema. Acceso exclusivo para ADMINISTRADOR."""
    return list_users(db, skip=skip, limit=limit)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar perfil de usuario por ID (Propio o ADMINISTRADOR)",
)
def get_user_detail(
    user_id: UUID,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Usuario:
    """Consulta detalles de un usuario validando Ownership o rol ADMINISTRADOR."""
    if "ADMINISTRADOR" not in current_user.role_names and current_user.id != user_id:
        raise PermissionDeniedException("No tiene permisos para ver el perfil de otro usuario.")
    return get_user_by_id(db, user_id)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar datos de contacto del perfil de usuario",
)
def edit_user_profile(
    user_id: UUID,
    user_in: UserUpdate,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Usuario:
    """Permite actualizar nombre o teléfono del propietario de la cuenta o de un ADMINISTRADOR."""
    return update_user_profile(db, user_id, user_in, current_user)


@router.patch(
    "/{user_id}/status",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Activar o desactivar cuenta de usuario (Solo ADMINISTRADOR)",
)
def change_user_status(
    user_id: UUID,
    status_in: UserStatusUpdate,
    current_admin: Usuario = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
) -> Usuario:
    """Eliminación lógica / moderación de estado activo de usuario por el ADMINISTRADOR."""
    return update_user_status(db, user_id, status_in, current_admin)
