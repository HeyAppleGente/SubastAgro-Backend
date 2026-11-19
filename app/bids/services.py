"""Capa de servicios y reglas de negocio en tiempo real para Pujas y Ofertas."""
from datetime import datetime, timezone
from decimal import Decimal
from typing import List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.auctions.models import EstadoSubasta, EventoSubasta
from app.bids.models import PujaOferta
from app.bids.schemas import BidCreate
from app.core.exceptions import (
    BusinessRuleException,
    ResourceNotFoundException,
)
from app.users.models import Usuario


def place_bid(db: Session, bid_in: BidCreate, comprador: Usuario) -> PujaOferta:
    """Registra una puja validando subasta activa, fechas, no auto-puja e incremento mínimo."""
    auction = db.scalar(
        select(EventoSubasta)
        .where(EventoSubasta.id == bid_in.subasta_id)
        .with_for_update()
    )
    if not auction:
        raise ResourceNotFoundException("Evento de subasta no encontrado.")

    if auction.estado_subasta != EstadoSubasta.ACTIVA.value:
        raise BusinessRuleException(
            f"La subasta no admite pujas porque su estado es '{auction.estado_subasta}'."
        )

    now = datetime.now(timezone.utc)
    end_dt = (
        auction.fecha_cierre
        if auction.fecha_cierre.tzinfo is not None
        else auction.fecha_cierre.replace(tzinfo=timezone.utc)
    )
    if now >= end_dt:
        raise BusinessRuleException("El tiempo límite de esta subasta ya ha expirado.")

    if auction.lote.ganadero_id == comprador.id:
        raise BusinessRuleException(
            "El propietario del lote no puede pujar en su propia subasta."
        )

    highest_bid = db.scalar(
        select(PujaOferta)
        .where(PujaOferta.subasta_id == auction.id)
        .order_by(PujaOferta.monto_ofertado_kilo.desc())
    )

    oferta_ofrecida = Decimal(str(bid_in.monto_ofertado_kilo))
    if highest_bid:
        minimo_requerido = highest_bid.monto_ofertado_kilo + auction.incremento_minimo_puja
    else:
        minimo_requerido = auction.precio_base_kilo

    if oferta_ofrecida < minimo_requerido:
        raise BusinessRuleException(
            f"Oferta insuficiente. El monto mínimo requerido por kilo es ${minimo_requerido:,.2f}."
        )

    new_bid = PujaOferta(
        subasta_id=auction.id,
        comprador_id=comprador.id,
        monto_ofertado_kilo=oferta_ofrecida,
    )
    db.add(new_bid)
    db.commit()
    db.refresh(new_bid)
    return new_bid


def list_bids_by_auction(db: Session, auction_id: UUID) -> List[PujaOferta]:
    """Retorna historial de pujas de una subasta ordenado de mayor a menor oferta."""
    auction = db.scalar(select(EventoSubasta).where(EventoSubasta.id == auction_id))
    if not auction:
        raise ResourceNotFoundException("Evento de subasta no encontrado.")

    stmt = (
        select(PujaOferta)
        .where(PujaOferta.subasta_id == auction_id)
        .order_by(PujaOferta.monto_ofertado_kilo.desc(), PujaOferta.fecha_hora_puja.asc())
    )
    return list(db.scalars(stmt).all())


def list_my_bids(db: Session, comprador_id: UUID) -> List[PujaOferta]:
    """Retorna exclusivamente el historial de pujas del comprador autenticado (Ownership)."""
    stmt = (
        select(PujaOferta)
        .where(PujaOferta.comprador_id == comprador_id)
        .order_by(PujaOferta.fecha_hora_puja.desc())
    )
    return list(db.scalars(stmt).all())
