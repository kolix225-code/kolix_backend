# app/models/user.py
import uuid
from typing import List, Optional
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import UUIDModel

class User(UUIDModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone_dial: Mapped[str] = mapped_column(String(8), default="+225", nullable=False)
    phone_number: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(128), nullable=False)
    activity_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    country: Mapped[str] = mapped_column(String(64), default="Côte d’Ivoire", nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="Propriétaire", nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relations
    shops: Mapped[List["Shop"]] = relationship("Shop", back_populates="owner", cascade="all, delete-orphan")
    affiliate_profile: Mapped[Optional["Affiliate"]] = relationship("Affiliate", back_populates="user", uselist=False)


class Collaborator(UUIDModel):
    __tablename__ = "collaborators"

    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shops.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(64), default="Gestionnaire de commandes", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="Invitation envoyée", nullable=False) # Actif, Suspendu, Invitation envoyée
    permissions: Mapped[list] = mapped_column(JSONB, default=list, nullable=False) # ['Accueil', 'Commandes', ...]
    is_owner: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    shop: Mapped["Shop"] = relationship("Shop", back_populates="collaborators")

