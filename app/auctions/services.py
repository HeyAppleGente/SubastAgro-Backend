"""Capa de servicios y reglas de negocio para Eventos de Subasta."""
from datetime import datetime, timezone
from decimal import Decimal
from typing import List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.auctions.models import EstadoSubasta, EventoSubasta
from app.auctions.schemas import (
    AuctionCreate,
    AuctionStatusUpdate,
    AuctionUpdate,
)
from app.cattle_lots.models import LoteGanado
from app.core.exceptions import (
    BusinessRuleException,
    PermissionDeniedException,
    ResourceNotFoundException,
)
from app.users.models import Usuario


def _enrich_auction(auction: EventoSubasta) -> EventoSubasta:
    """Calcula campos derivados dinámicos (oferta_actual_kilo y total_pujas)."""
    pujas = auction.pujas or []
    auction.total_pujas = len(pujas)  # type: ignore[attr-defined]
    if pujas:
        auction.oferta_actual_kilo = max(p.monto_ofertado_kilo for p in pujas)  # type: ignore[attr-defined]
    else:
        auction.oferta_actual_kilo = auction.precio_base_kilo  # type: ignore[attr-defined]
    return auction


def _auto_sync_auction_lifecycle(db: Session, auctions: List[EventoSubasta]) -> None:
    """Sincroniza automáticamente estados PROGRAMADA -> ACTIVA si alcanzó fecha_inicio."""
    now = datetime.now(timezone.utc)
    dirty = False
    for a in auctions:
        start_dt = (
            a.fecha_inicio
            if a.fecha_inicio.tzinfo is not None
            else a.fecha_inicio.replace(tzinfo=timezone.utc)
        )
        end_dt = (
            a.fecha_cierre
            if a.fecha_cierre.tzinfo is not None
            else a.fecha_cierre.replace(tzinfo=timezone.utc)
        )
        if a.estado_subasta == EstadoSubasta.PROGRAMADA.value and start_dt <= now < end_dt:
            a.estado_subasta = EstadoSubasta.ACTIVA.value
            dirty = True
    if dirty:
        db.commit()


def create_auction(
    db: Session, auction_in: AuctionCreate, current_user: Usuario
) -> EventoSubasta:
    """Programa un evento de subasta vinculando un lote disponible y validando Ownership."""
    lot = db.scalar(select(LoteGanado).where(LoteGanado.id == auction_in.lote_id))
    if not lot:
        raise ResourceNotFoundException("El lote de ganado especificado no existe.")

    is_admin = "ADMINISTRADOR" in current_user.role_names
    if not is_admin and lot.ganadero_id != current_user.id:
        raise PermissionDeniedException(
            "Violación de Ownership: Solo puede subastar sus propios lotes de ganado."
        )

    if lot.estado_lote != "DISPONIBLE":
        raise BusinessRuleException(
            f"El lote '{lot.codigo_lote}' no está disponible para subasta (estado actual: {lot.estado_lote})."
        )

    existing_auction = db.scalar(
        select(EventoSubasta).where(EventoSubasta.lote_id == lot.id)
    )
    if existing_auction:
        raise BusinessRuleException(
            "Este lote ya cuenta con un evento de subasta asociado."
        )

    auction = EventoSubasta(
        lote_id=lot.id,
        precio_base_kilo=Decimal(str(auction_in.precio_base_kilo)),
        incremento_minimo_puja=Decimal(str(auction_in.incremento_minimo_puja)),
        fecha_inicio=auction_in.fecha_inicio,
        fecha_cierre=auction_in.fecha_cierre,
        estado_subasta=auction_in.estado_subasta.value,
    )
    lot.estado_lote = "EN_SUBASTA"

    try:
        db.add(auction)
        db.commit()
        db.refresh(auction)
        return _enrich_auction(auction)
    except Exception:
        db.rollback()
        raise


def list_active_auctions(db: Session) -> List[EventoSubasta]:
    """Lista todas las subastas activas disponibles para recibir pujas."""
    all_open = list(
        db.scalars(
            select(EventoSubasta).where(
                EventoSubasta.estado_subasta.in_(
                    [EstadoSubasta.PROGRAMADA.value, EstadoSubasta.ACTIVA.value]
                )
            )
        ).all()
    )
    _auto_sync_auction_lifecycle(db, all_open)

    stmt = (
        select(EventoSubasta)
        .where(EventoSubasta.estado_subasta == EstadoSubasta.ACTIVA.value)
        .order_by(EventoSubasta.fecha_cierre.asc())
    )
    auctions = list(db.scalars(stmt).all())
    return [_enrich_auction(a) for a in auctions]


def list_all_auctions(db: Session) -> List[EventoSubasta]:
    """Lista todos los eventos de subasta."""
    auctions = list(
        db.scalars(
            select(EventoSubasta).order_by(EventoSubasta.fecha_inicio.desc())
        ).all()
    )
    return [_enrich_auction(a) for a in auctions]


def get_auction_by_id(db: Session, auction_id: UUID) -> EventoSubasta:
    """Obtiene una subasta por su UUID."""
    auction = db.scalar(select(EventoSubasta).where(EventoSubasta.id == auction_id))
    if not auction:
        raise ResourceNotFoundException("Evento de subasta no encontrado.")
    return _enrich_auction(auction)


def update_auction(
    db: Session, auction_id: UUID, auction_in: AuctionUpdate, current_user: Usuario
) -> EventoSubasta:
    """Actualiza parámetros de una subasta antes de que reciba pujas."""
    auction = get_auction_by_id(db, auction_id)
    is_admin = "ADMINISTRADOR" in current_user.role_names
    if not is_admin and auction.lote.ganadero_id != current_user.id:
        raise PermissionDeniedException(
            "No tiene permisos para modificar esta subasta."
        )

    if auction.pujas and not is_admin:
        raise BusinessRuleException(
            "No se pueden alterar los precios de una subasta que ya tiene pujas registradas."
        )

    if auction_in.precio_base_kilo is not None:
        auction.precio_base_kilo = auction_in.precio_base_kilo
    if auction_in.incremento_minimo_puja is not None:
        auction.incremento_minimo_puja = auction_in.incremento_minimo_puja
    if auction_in.fecha_inicio is not None:
        auction.fecha_inicio = auction_in.fecha_inicio
    if auction_in.fecha_cierre is not None:
        auction.fecha_cierre = auction_in.fecha_cierre

    if auction.fecha_cierre <= auction.fecha_inicio:
        raise BusinessRuleException("La fecha de cierre debe ser posterior a la de inicio.")

    db.commit()
    db.refresh(auction)
    return _enrich_auction(auction)


def update_auction_status(
    db: Session,
    auction_id: UUID,
    status_in: AuctionStatusUpdate,
    current_user: Usuario,
) -> EventoSubasta:
    """Cambia el estado de la subasta validando Ownership del ganadero o rol ADMINISTRADOR."""
    auction = get_auction_by_id(db, auction_id)
    is_admin = "ADMINISTRADOR" in current_user.role_names
    if not is_admin and auction.lote.ganadero_id != current_user.id:
        raise PermissionDeniedException(
            "No tiene permisos para cambiar el estado de esta subasta."
        )

    new_status = status_in.estado_subasta.value
    if auction.estado_subasta == EstadoSubasta.FINALIZADA.value and not is_admin:
        raise BusinessRuleException("Una subasta finalizada no puede reabrirse.")

    auction.estado_subasta = new_status
    if new_status == EstadoSubasta.DESIERTA.value:
        auction.lote.estado_lote = "DISPONIBLE"
    elif new_status in {EstadoSubasta.PROGRAMADA.value, EstadoSubasta.ACTIVA.value}:
        auction.lote.estado_lote = "EN_SUBASTA"

    db.commit()
    db.refresh(auction)
    return _enrich_auction(auction)
