"""Capa de servicios y reglas de negocio para Razas y Lotes de Ganado."""
from typing import List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.cattle_lots.models import LoteGanado, RazaGanado
from app.cattle_lots.schemas import (
    BreedCreate,
    CattleLotCreate,
    CattleLotUpdate,
)
from app.core.exceptions import (
    BusinessRuleException,
    PermissionDeniedException,
    ResourceNotFoundException,
)
from app.users.models import Usuario


def create_breed(db: Session, breed_in: BreedCreate) -> RazaGanado:
    """Crea una raza en el catálogo verificando unicidad de nombre."""
    existing = db.scalar(
        select(RazaGanado).where(
            RazaGanado.nombre_raza.ilike(breed_in.nombre_raza.strip())
        )
    )
    if existing:
        raise BusinessRuleException(
            f"La raza '{breed_in.nombre_raza}' ya existe en el catálogo."
        )

    breed = RazaGanado(
        nombre_raza=breed_in.nombre_raza.strip(),
        proposito=breed_in.proposito.strip(),
        estado=True,
    )
    db.add(breed)
    db.commit()
    db.refresh(breed)
    return breed


def list_breeds(db: Session, only_active: bool = True) -> List[RazaGanado]:
    """Lista las razas disponibles en el catálogo."""
    stmt = select(RazaGanado).order_by(RazaGanado.nombre_raza.asc())
    if only_active:
        stmt = stmt.where(RazaGanado.estado.is_(True))
    return list(db.scalars(stmt).all())


def create_cattle_lot(
    db: Session, lot_in: CattleLotCreate, ganadero: Usuario
) -> LoteGanado:
    """Registra un lote de ganado asociado al ganadero autenticado."""
    raza = db.scalar(
        select(RazaGanado).where(
            RazaGanado.id == lot_in.raza_id, RazaGanado.estado.is_(True)
        )
    )
    if not raza:
        raise ResourceNotFoundException("La raza especificada no existe o está inactiva.")

    if not lot_in.vacunacion_al_dia:
        raise BusinessRuleException(
            "Normativa sanitaria ICA: Solo se permiten lotes con esquema de vacunación al día."
        )

    existing_code = db.scalar(
        select(LoteGanado).where(
            LoteGanado.codigo_lote == lot_in.codigo_lote.strip().upper()
        )
    )
    if existing_code:
        raise BusinessRuleException(
            f"El código de lote '{lot_in.codigo_lote}' ya está registrado."
        )

    lot = LoteGanado(
        ganadero_id=ganadero.id,
        raza_id=lot_in.raza_id,
        codigo_lote=lot_in.codigo_lote.strip().upper(),
        cantidad_cabezas=lot_in.cantidad_cabezas,
        peso_promedio_kg=lot_in.peso_promedio_kg,
        vacunacion_al_dia=lot_in.vacunacion_al_dia,
        ubicacion_hacienda=lot_in.ubicacion_hacienda.strip(),
        estado_lote="DISPONIBLE",
    )
    db.add(lot)
    db.commit()
    db.refresh(lot)
    return lot


def list_my_cattle_lots(db: Session, ganadero_id: UUID) -> List[LoteGanado]:
    """Lista exclusivamente los lotes pertenecientes al ganadero autenticado (Ownership)."""
    stmt = (
        select(LoteGanado)
        .where(
            LoteGanado.ganadero_id == ganadero_id,
            LoteGanado.estado_lote != "INACTIVO",
        )
        .order_by(LoteGanado.codigo_lote.asc())
    )
    return list(db.scalars(stmt).all())


def get_cattle_lot_by_id(db: Session, lot_id: UUID) -> LoteGanado:
    """Obtiene el detalle de un lote de ganado por su UUID."""
    lot = db.scalar(select(LoteGanado).where(LoteGanado.id == lot_id))
    if not lot:
        raise ResourceNotFoundException("Lote de ganado no encontrado.")
    return lot


def update_cattle_lot(
    db: Session, lot_id: UUID, lot_in: CattleLotUpdate, current_user: Usuario
) -> LoteGanado:
    """Actualiza un lote verificando estrictamente Ownership del ganadero o rol ADMINISTRADOR."""
    lot = get_cattle_lot_by_id(db, lot_id)
    is_admin = "ADMINISTRADOR" in current_user.role_names

    if not is_admin and lot.ganadero_id != current_user.id:
        raise PermissionDeniedException(
            "Violación de Ownership: No puede modificar un lote que pertenece a otro ganadero."
        )

    if lot.estado_lote in {"EN_SUBASTA", "VENDIDO"} and not is_admin:
        raise BusinessRuleException(
            "No se puede editar un lote que se encuentra actualmente en subasta o vendido."
        )

    if lot_in.raza_id is not None:
        raza = db.scalar(select(RazaGanado).where(RazaGanado.id == lot_in.raza_id))
        if not raza:
            raise ResourceNotFoundException("La nueva raza especificada no existe.")
        lot.raza_id = lot_in.raza_id

    if lot_in.cantidad_cabezas is not None:
        lot.cantidad_cabezas = lot_in.cantidad_cabezas
    if lot_in.peso_promedio_kg is not None:
        lot.peso_promedio_kg = lot_in.peso_promedio_kg
    if lot_in.vacunacion_al_dia is not None:
        lot.vacunacion_al_dia = lot_in.vacunacion_al_dia
    if lot_in.ubicacion_hacienda is not None:
        lot.ubicacion_hacienda = lot_in.ubicacion_hacienda.strip()
    if lot_in.estado_lote is not None:
        lot.estado_lote = lot_in.estado_lote

    db.commit()
    db.refresh(lot)
    return lot


def delete_cattle_lot(db: Session, lot_id: UUID, current_user: Usuario) -> LoteGanado:
    """Eliminación lógica (estado_lote='INACTIVO') validando Ownership."""
    lot = get_cattle_lot_by_id(db, lot_id)
    is_admin = "ADMINISTRADOR" in current_user.role_names

    if not is_admin and lot.ganadero_id != current_user.id:
        raise PermissionDeniedException(
            "Violación de Ownership: No puede eliminar un lote registrado por otro ganadero."
        )

    if lot.estado_lote in {"EN_SUBASTA", "VENDIDO"}:
        raise BusinessRuleException(
            "No se puede desactivar un lote vinculado a una subasta activa o vendida."
        )

    lot.estado_lote = "INACTIVO"
    db.commit()
    db.refresh(lot)
    return lot
