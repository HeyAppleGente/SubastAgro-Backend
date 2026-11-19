"""Endpoints RESTful para Razas y Lotes de Ganado Vacuno."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.auth.services import (
    get_current_active_admin,
    get_current_active_ganadero,
    get_current_active_user,
    get_current_ganadero_or_admin,
)
from app.cattle_lots.models import LoteGanado, RazaGanado
from app.cattle_lots.schemas import (
    BreedCreate,
    BreedResponse,
    CattleLotCreate,
    CattleLotResponse,
    CattleLotUpdate,
)
from app.cattle_lots.services import (
    create_breed,
    create_cattle_lot,
    delete_cattle_lot,
    get_cattle_lot_by_id,
    list_breeds,
    list_my_cattle_lots,
    update_cattle_lot,
)
from app.core.database import get_db
from app.users.models import Usuario

router = APIRouter(prefix="/cattle-lots", tags=["3. Razas y Lotes de Ganado (Cattle Lots)"])


@router.post(
    "/breeds",
    response_model=BreedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear raza de ganado vacuno (Solo ADMINISTRADOR)",
)
def add_breed(
    breed_in: BreedCreate,
    current_admin: Usuario = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
) -> RazaGanado:
    """Registra una nueva raza en el catálogo oficial."""
    return create_breed(db, breed_in)


@router.get(
    "/breeds",
    response_model=List[BreedResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar catálogo público de razas de ganado",
)
def get_breeds(db: Session = Depends(get_db)) -> List[RazaGanado]:
    """Consulta pública de razas activas."""
    return list_breeds(db, only_active=True)


@router.post(
    "",
    response_model=CattleLotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar lote de ganado vacuno (Solo GANADERO)",
)
def register_cattle_lot(
    lot_in: CattleLotCreate,
    current_ganadero: Usuario = Depends(get_current_active_ganadero),
    db: Session = Depends(get_db),
) -> LoteGanado:
    """Crea un lote de ganado vacuno asociado al ganadero autenticado."""
    return create_cattle_lot(db, lot_in, current_ganadero)


@router.get(
    "/my-lots",
    response_model=List[CattleLotResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar lotes propios del ganadero autenticado (Ownership)",
)
def get_my_lots(
    current_ganadero: Usuario = Depends(get_current_active_ganadero),
    db: Session = Depends(get_db),
) -> List[LoteGanado]:
    """Retorna exclusivamente los lotes registrados por el ganadero en sesión."""
    return list_my_cattle_lots(db, current_ganadero.id)


@router.get(
    "/{lot_id}",
    response_model=CattleLotResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar detalle de un lote de ganado por ID",
)
def get_lot_detail(
    lot_id: UUID,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LoteGanado:
    """Obtiene la ficha técnica del lote de ganado."""
    return get_cattle_lot_by_id(db, lot_id)


@router.put(
    "/{lot_id}",
    response_model=CattleLotResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar lote de ganado propio (Ownership)",
)
def edit_cattle_lot(
    lot_id: UUID,
    lot_in: CattleLotUpdate,
    current_user: Usuario = Depends(get_current_ganadero_or_admin),
    db: Session = Depends(get_db),
) -> LoteGanado:
    """Actualiza datos de un lote verificando propiedad (Ownership) o rol ADMINISTRADOR."""
    return update_cattle_lot(db, lot_id, lot_in, current_user)


@router.delete(
    "/{lot_id}",
    response_model=CattleLotResponse,
    status_code=status.HTTP_200_OK,
    summary="Desactivar lógicamente un lote de ganado propio (Ownership)",
)
def remove_cattle_lot(
    lot_id: UUID,
    current_user: Usuario = Depends(get_current_ganadero_or_admin),
    db: Session = Depends(get_db),
) -> LoteGanado:
    """Realiza eliminación lógica (estado_lote='INACTIVO') validando Ownership."""
    return delete_cattle_lot(db, lot_id, current_user)
