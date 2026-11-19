"""Capa de servicios con reglas de negocio y transacciones para Usuarios."""
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.exceptions import (
    BusinessRuleException,
    PermissionDeniedException,
    ResourceNotFoundException,
)
from app.core.security import get_password_hash
from app.users.models import Rol, Usuario
from app.users.schemas import UserCreate, UserStatusUpdate, UserUpdate


def get_or_create_role(db: Session, role_name: str) -> Rol:
    """Obtiene un rol existente o lo crea en catálogo."""
    upper_name = role_name.strip().upper()
    role = db.scalar(select(Rol).where(Rol.nombre_rol == upper_name))
    if not role:
        descriptions = {
            "ADMINISTRADOR": "Control total del sistema y auditoría",
            "GANADERO": "Productor vendedor de lotes de ganado vacuno",
            "COMPRADOR": "Participante habilitado para pujar y adjudicar lotes",
        }
        role = Rol(
            nombre_rol=upper_name,
            descripcion=descriptions.get(upper_name, f"Rol {upper_name}"),
        )
        db.add(role)
        db.flush()
    return role


def create_user(
    db: Session, user_in: UserCreate, allow_admin_creation: bool = False
) -> Usuario:
    """Registra un nuevo usuario validando unicidad de email, documento y reglas de rol."""
    if user_in.rol == "ADMINISTRADOR" and not allow_admin_creation:
        raise PermissionDeniedException(
            "Solo un ADMINISTRADOR autenticado puede crear cuentas con rol ADMINISTRADOR."
        )

    existing_email = db.scalar(
        select(Usuario).where(Usuario.email == user_in.email.lower())
    )
    if existing_email:
        raise BusinessRuleException("El correo electrónico ya se encuentra registrado.")

    existing_doc = db.scalar(
        select(Usuario).where(
            Usuario.documento_identidad == user_in.documento_identidad.strip()
        )
    )
    if existing_doc:
        raise BusinessRuleException("El documento de identidad ya está registrado.")

    role_obj = get_or_create_role(db, user_in.rol)

    new_user = Usuario(
        email=user_in.email.lower(),
        password_hash=get_password_hash(user_in.password),
        nombre_completo=user_in.nombre_completo.strip(),
        documento_identidad=user_in.documento_identidad.strip(),
        telefono=user_in.telefono.strip() if user_in.telefono else None,
        estado=True,
    )
    new_user.roles.append(role_obj)

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception:
        db.rollback()
        raise


def list_users(db: Session, skip: int = 0, limit: int = 100) -> List[Usuario]:
    """Retorna listado paginado de usuarios del sistema."""
    stmt = select(Usuario).order_by(Usuario.fecha_creacion.desc()).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def get_user_by_id(db: Session, user_id: UUID) -> Usuario:
    """Obtiene un usuario por su UUID o lanza HTTP 404."""
    user = db.scalar(select(Usuario).where(Usuario.id == user_id))
    if not user:
        raise ResourceNotFoundException("Usuario no encontrado.")
    return user


def get_user_by_email(db: Session, email: str) -> Optional[Usuario]:
    """Busca un usuario por correo electrónico."""
    return db.scalar(select(Usuario).where(Usuario.email == email.strip().lower()))


def update_user_profile(
    db: Session, target_user_id: UUID, user_in: UserUpdate, current_user: Usuario
) -> Usuario:
    """Actualiza perfil validando Ownership o rol ADMINISTRADOR."""
    is_admin = "ADMINISTRADOR" in current_user.role_names
    if not is_admin and current_user.id != target_user_id:
        raise PermissionDeniedException(
            "Solo puede actualizar su propio perfil de usuario."
        )

    user = get_user_by_id(db, target_user_id)
    if user_in.nombre_completo is not None:
        user.nombre_completo = user_in.nombre_completo.strip()
    if user_in.telefono is not None:
        user.telefono = user_in.telefono.strip()

    db.commit()
    db.refresh(user)
    return user


def update_user_status(
    db: Session, target_user_id: UUID, status_in: UserStatusUpdate, current_user: Usuario
) -> Usuario:
    """Activa o desactiva lógicamente una cuenta (solo ADMINISTRADOR)."""
    if current_user.id == target_user_id and not status_in.estado:
        raise BusinessRuleException("Un administrador no puede desactivar su propia cuenta.")

    user = get_user_by_id(db, target_user_id)
    user.estado = status_in.estado
    db.commit()
    db.refresh(user)
    return user
