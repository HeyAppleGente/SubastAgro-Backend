"""Endpoints RESTful para Pujas y Ofertas."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.auth.services import get_current_active_comprador, get_current_active_user
from app.bids.models import PujaOferta
from app.bids.schemas import BidCreate, BidResponse
from app.bids.services import list_bids_by_auction, list_my_bids, place_bid
from app.core.database import get_db
from app.users.models import Usuario

router = APIRouter(prefix="/bids", tags=["5. Pujas y Ofertas (Bids)"])


@router.post(
    "",
    response_model=BidResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar puja económica por kilo (Solo COMPRADOR)",
)
def create_bid(
    bid_in: BidCreate,
    current_comprador: Usuario = Depends(get_current_active_comprador),
    db: Session = Depends(get_db),
) -> PujaOferta:
    """Registra una oferta validando incremento mínimo y estado activo de la subasta."""
    return place_bid(db, bid_in, current_comprador)


@router.get(
    "/auction/{auction_id}",
    response_model=List[BidResponse],
    status_code=status.HTTP_200_OK,
    summary="Consultar historial de pujas de una subasta",
)
def get_auction_bids(
    auction_id: UUID,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[PujaOferta]:
    """Retorna todas las pujas realizadas en una subasta específica."""
    return list_bids_by_auction(db, auction_id)


@router.get(
    "/my-bids",
    response_model=List[BidResponse],
    status_code=status.HTTP_200_OK,
    summary="Consultar historial propio de pujas (Ownership - Solo COMPRADOR)",
)
def get_my_bids(
    current_comprador: Usuario = Depends(get_current_active_comprador),
    db: Session = Depends(get_db),
) -> List[PujaOferta]:
    """Retorna exclusivamente las pujas efectuadas por el comprador autenticado."""
    return list_my_bids(db, current_comprador.id)
