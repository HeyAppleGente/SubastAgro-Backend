"""Endpoints RESTful para Eventos de Subasta."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.auctions.models import EventoSubasta
from app.auctions.schemas import (
    AuctionCreate,
    AuctionResponse,
    AuctionStatusUpdate,
    AuctionUpdate,
)
from app.auctions.services import (
    create_auction,
    get_auction_by_id,
    list_active_auctions,
    list_all_auctions,
    update_auction,
    update_auction_status,
)
from app.auth.services import (
    get_current_active_user,
    get_current_ganadero_or_admin,
)
from app.core.database import get_db
from app.users.models import Usuario

router = APIRouter(prefix="/auctions", tags=["4. Eventos de Subasta (Auctions)"])


@router.post(
    "",
    response_model=AuctionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Programar evento de subasta vinculando un lote (GANADERO o ADMINISTRADOR)",
)
def schedule_auction(
    auction_in: AuctionCreate,
    current_user: Usuario = Depends(get_current_ganadero_or_admin),
    db: Session = Depends(get_db),
) -> EventoSubasta:
    """Crea una subasta para un lote de ganado verificando disponibilidad y Ownership."""
    return create_auction(db, auction_in, current_user)


@router.get(
    "/active",
    response_model=List[AuctionResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar subastas activas disponibles para pujas",
)
def get_active_auctions(db: Session = Depends(get_db)) -> List[EventoSubasta]:
    """Catálogo de subastas activas con oferta máxima actual calculada."""
    return list_active_auctions(db)


@router.get(
    "",
    response_model=List[AuctionResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar todas las subastas registradas",
)
def get_auctions(
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[EventoSubasta]:
    """Listado histórico y vigente de eventos de subasta."""
    return list_all_auctions(db)


@router.get(
    "/{auction_id}",
    response_model=AuctionResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar detalle de una subasta por ID",
)
def get_auction_detail(
    auction_id: UUID,
    db: Session = Depends(get_db),
) -> EventoSubasta:
    """Retorna la información detallada de un evento de subasta."""
    return get_auction_by_id(db, auction_id)


@router.put(
    "/{auction_id}",
    response_model=AuctionResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar parámetros de una subasta",
)
def edit_auction(
    auction_id: UUID,
    auction_in: AuctionUpdate,
    current_user: Usuario = Depends(get_current_ganadero_or_admin),
    db: Session = Depends(get_db),
) -> EventoSubasta:
    """Modifica precios o fechas de una subasta validando Ownership."""
    return update_auction(db, auction_id, auction_in, current_user)


@router.patch(
    "/{auction_id}/status",
    response_model=AuctionResponse,
    status_code=status.HTTP_200_OK,
    summary="Cambiar estado de subasta (PROGRAMADA, ACTIVA, FINALIZADA, DESIERTA)",
)
def patch_auction_status(
    auction_id: UUID,
    status_in: AuctionStatusUpdate,
    current_user: Usuario = Depends(get_current_ganadero_or_admin),
    db: Session = Depends(get_db),
) -> EventoSubasta:
    """Actualiza el estado operativo de un evento de subasta."""
    return update_auction_status(db, auction_id, status_in, current_user)
