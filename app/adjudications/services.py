"""Capa de servicios para cierre de subastas y generación de Actas de Adjudicación."""
import secrets
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.adjudications.models import ActaAdjudicacion
from app.auctions.models import EstadoSubasta, EventoSubasta
from app.bids.models import PujaOferta
from app.core.exceptions import (
    BusinessRuleException,
    PermissionDeniedException,
    ResourceNotFoundException,
)
from app.users.models import Usuario


def _generate_guia_movilizacion() -> str:
    """Genera un código único de guía sanitaria de movilización ICA."""
    year = datetime.now(timezone.utc).year
    random_hex = secrets.token_hex(4).upper()
    return f"ICA-GSM-{year}-{random_hex}"


def close_auction_and_adjudicate(
    db: Session, auction_id: UUID
) -> ActaAdjudicacion:
    """Cierra una subasta, determina el mejor postor y genera el Acta de Adjudicación."""
    auction = db.scalar(
        select(EventoSubasta)
        .where(EventoSubasta.id == auction_id)
        .with_for_update()
    )
    if not auction:
        raise ResourceNotFoundException("Evento de subasta no encontrado.")

    if auction.estado_subasta == EstadoSubasta.FINALIZADA.value:
        raise BusinessRuleException("Esta subasta ya fue finalizada y adjudicada.")

    existing_acta = db.scalar(
        select(ActaAdjudicacion).where(ActaAdjudicacion.subasta_id == auction.id)
    )
    if existing_acta:
        raise BusinessRuleException("Ya existe un acta de adjudicación para esta subasta.")

    winning_bid = db.scalar(
        select(PujaOferta)
        .where(PujaOferta.subasta_id == auction.id)
        .order_by(PujaOferta.monto_ofertado_kilo.desc(), PujaOferta.fecha_hora_puja.asc())
    )
    if not winning_bid:
        auction.estado_subasta = EstadoSubasta.DESIERTA.value
        auction.lote.estado_lote = "DISPONIBLE"
        db.commit()
        raise BusinessRuleException(
            "La subasta no recibió pujas y ha sido declarada DESIERTA."
        )

    lote = auction.lote
    peso_promedio = Decimal(str(lote.peso_promedio_kg))
    cabezas = Decimal(str(lote.cantidad_cabezas))
    precio_ganador = Decimal(str(winning_bid.monto_ofertado_kilo))

    monto_total = (peso_promedio * cabezas * precio_ganador).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    acta = ActaAdjudicacion(
        subasta_id=auction.id,
        comprador_ganador_id=winning_bid.comprador_id,
        puja_ganadora_id=winning_bid.id,
        monto_total_final=monto_total,
        guia_movilizacion_codigo=_generate_guia_movilizacion(),
        estado_pago="PENDIENTE",
    )

    auction.estado_subasta = EstadoSubasta.FINALIZADA.value
    lote.estado_lote = "VENDIDO"

    try:
        db.add(acta)
        db.commit()
        db.refresh(acta)
        return acta
    except Exception:
        db.rollback()
        raise


def list_my_adjudications(db: Session, comprador_id: UUID) -> List[ActaAdjudicacion]:
    """Lista las actas ganadas por el comprador autenticado (Ownership)."""
    stmt = (
        select(ActaAdjudicacion)
        .where(ActaAdjudicacion.comprador_ganador_id == comprador_id)
        .order_by(ActaAdjudicacion.fecha_cierre.desc())
    )
    return list(db.scalars(stmt).all())


def get_adjudication_by_id(
    db: Session, adjudication_id: UUID, current_user: Usuario
) -> ActaAdjudicacion:
    """Consulta el detalle de un acta validando Ownership (comprador ganador, ganadero vendedor o admin)."""
    acta = db.scalar(
        select(ActaAdjudicacion).where(ActaAdjudicacion.id == adjudication_id)
    )
    if not acta:
        raise ResourceNotFoundException("Acta de adjudicación no encontrada.")

    is_admin = "ADMINISTRADOR" in current_user.role_names
    is_winner = acta.comprador_ganador_id == current_user.id
    is_seller = acta.subasta.lote.ganadero_id == current_user.id

    if not (is_admin or is_winner or is_seller):
        raise PermissionDeniedException(
            "Violación de Ownership: No tiene acceso a esta acta de adjudicación."
        )
    return acta
