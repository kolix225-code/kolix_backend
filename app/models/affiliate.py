# app/models/affiliate.py
import uuid
from typing import List, Optional
from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import UUIDModel

class Affiliate(UUIDModel):
    __tablename__ = "affiliates"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    affiliate_code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False) # e.g. AMINA10
    affiliate_slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False) # e.g. aminatraore
    available_balance: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    total_earned: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    lock_reason: Mapped[Optional[str]] = mapped_column(String(255), default="Programme sur invitation / Accès restreint", nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="affiliate_profile")
    referrals: Mapped[List["AffiliateReferral"]] = relationship("AffiliateReferral", back_populates="affiliate", cascade="all, delete-orphan")
    payouts: Mapped[List["AffiliatePayout"]] = relationship("AffiliatePayout", back_populates="affiliate", cascade="all, delete-orphan")


class AffiliateReferral(UUIDModel):
    __tablename__ = "affiliate_referrals"

    affiliate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("affiliates.id", ondelete="CASCADE"), index=True, nullable=False
    )
    referred_shop_name: Mapped[str] = mapped_column(String(128), nullable=False)
    referred_user_name: Mapped[str] = mapped_column(String(128), nullable=False)
    source: Mapped[str] = mapped_column(String(64), default="Lien direct", nullable=False) # Lien direct, Code AMINA10
    plan: Mapped[str] = mapped_column(String(32), default="Grow", nullable=False) # Start, Grow, Pro, Empire
    status: Mapped[str] = mapped_column(String(32), default="Actif", nullable=False) # Actif, Essai gratuit, Résilié
    months_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    total_months: Mapped[int] = mapped_column(Integer, default=12, nullable=False)
    earned_total: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    monthly_commission: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)

    affiliate: Mapped["Affiliate"] = relationship("Affiliate", back_populates="referrals")


class AffiliatePayout(UUIDModel):
    __tablename__ = "affiliate_payouts"

    affiliate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("affiliates.id", ondelete="CASCADE"), index=True, nullable=False
    )
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    payout_type: Mapped[str] = mapped_column(String(32), default="Transfert Portefeuille", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="Validé", nullable=False)

    affiliate: Mapped["Affiliate"] = relationship("Affiliate", back_populates="payouts")

