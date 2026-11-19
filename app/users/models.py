"""Modelos ORM SQLAlchemy 2.0 para Usuarios, Roles y asignación N:M."""
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from app.core.database import Base

# Tabla asociativa N:M usuario_roles
usuario_roles = Table(
    "usuario_roles",
    Base.metadata,
    Column(
        "usuario_id",
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "rol_id",
        Integer,
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Rol(Base):
    """Catálogo de roles del sistema (ADMINISTRADOR, GANADERO, COMPRADOR)."""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre_rol: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    descripcion: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    usuarios: Mapped[List["Usuario"]] = relationship(
        "Usuario",
        secondary=usuario_roles,
        back_populates="roles",
    )

    @validates("nombre_rol")
    def validate_nombre_rol(self, key: str, value: str) -> str:
        allowed = {"ADMINISTRADOR", "GANADERO", "COMPRADOR"}
        upper_val = value.strip().upper()
        if upper_val not in allowed:
            raise ValueError(f"Rol inválido: {value}. Permitidos: {allowed}")
        return upper_val


class Usuario(Base):
    """Entidad de usuario del sistema SubastAgro."""

    __tablename__ = "usuarios"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(150), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre_completo: Mapped[str] = mapped_column(String(150), nullable=False)
    documento_identidad: Mapped[str] = mapped_column(
        String(40), unique=True, nullable=False, index=True
    )
    telefono: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    estado: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    roles: Mapped[List["Rol"]] = relationship(
        "Rol",
        secondary=usuario_roles,
        back_populates="usuarios",
        lazy="selectin",
    )
    lotes: Mapped[List["LoteGanado"]] = relationship(
        "LoteGanado",
        back_populates="ganadero",
        foreign_keys="LoteGanado.ganadero_id",
    )
    pujas: Mapped[List["PujaOferta"]] = relationship(
        "PujaOferta",
        back_populates="comprador",
        foreign_keys="PujaOferta.comprador_id",
    )
    actas_ganadas: Mapped[List["ActaAdjudicacion"]] = relationship(
        "ActaAdjudicacion",
        back_populates="comprador_ganador",
        foreign_keys="ActaAdjudicacion.comprador_ganador_id",
    )

    @property
    def role_names(self) -> List[str]:
        """Retorna la lista de nombres de roles asignados al usuario."""
        return [r.nombre_rol for r in self.roles]

    @validates("email")
    def validate_email(self, key: str, address: str) -> str:
        if "@" not in address:
            raise ValueError("Dirección de correo electrónico inválida.")
        return address.strip().lower()
