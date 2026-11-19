"""Endpoints RESTful para Actas de Adjudicación."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.adjudications.models import ActaAdjudicacion
from app.adjudications.schemas import AdjudicationResponse
from app.adjudications.services import (
    close_auction_and_adjudicate,
    get_adjudication_by_id,
    list_my_adjudications,
)
from app.auth.services import (
    get_current_active_admin,
    get_current_active_comprador,
    get_current_active_user,
)
from app.core.database import get_db
from app.users.models import Usuario

router = APIRouter(
    prefix="/adjudications", tags=["6. Actas de Adjudicación (Adjudications)"]
)


@router.post(
    "/close-auction/{auction_id}",
    response_model=AdjudicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cerrar subasta y generar acta al mejor postor (Solo ADMINISTRADOR)",
)
def close_auction(
    auction_id: UUID,
    current_admin: Usuario = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
) -> ActaAdjudicacion:
    """Cierra la subasta, calcula el monto total final y emite código de guía de movilización."""
    return close_auction_and_adjudicate(db, auction_id)


@router.get(
    "/my-adjudications",
    response_model=List[AdjudicationResponse],
    status_code=status.HTTP_200_OK,
    summary="Consultar actas de adjudicación ganadas (Ownership - Solo COMPRADOR)",
)
def get_my_adjudications(
    current_comprador: Usuario = Depends(get_current_active_comprador),
    db: Session = Depends(get_db),
) -> List[ActaAdjudicacion]:
    """Retorna exclusivamente las actas adjudicadas al comprador autenticado."""
    return list_my_adjudications(db, current_comprador.id)


@router.get(
    "/{adjudication_id}",
    response_model=AdjudicationResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar detalle de un acta de adjudicación",
)
def get_adjudication_detail(
    adjudication_id: UUID,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ActaAdjudicacion:
    """Retorna el acta verificando Ownership del comprador ganador, ganadero vendedor o administrador."""
    return get_adjudication_by_id(db, adjudication_id, current_user)
