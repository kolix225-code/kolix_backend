# app/models/wallet.py
import uuid
from typing import List, Optional
from sqlalchemy import Boolean, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import UUIDModel

class Wallet(UUIDModel):
    __tablename__ = "wallets"

    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shops.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    digital_balance: Mapped[float] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    cash_balance: Mapped[float] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    pending_balance: Mapped[float] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    withdrawn_month: Mapped[float] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    kolix_commission: Mapped[float] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    is_digital_locked: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    digital_lock_reason: Mapped[Optional[str]] = mapped_column(String(255), default="Vérification KYC requise", nullable=True)

    # Relations
    shop: Mapped["Shop"] = relationship("Shop", back_populates="wallet")
    transactions: Mapped[List["WalletTransaction"]] = relationship("WalletTransaction", back_populates="wallet", cascade="all, delete-orphan")
    payout_accounts: Mapped[List["PayoutAccount"]] = relationship("PayoutAccount", back_populates="wallet", cascade="all, delete-orphan")


class PayoutAccount(UUIDModel):
    __tablename__ = "payout_accounts"

    wallet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("wallets.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    num: Mapped[str] = mapped_column(String(64), nullable=False) # Phone number or IBAN
    provider: Mapped[str] = mapped_column(String(64), nullable=False) # Wave, Orange Money, MTN MoMo, Moov Money, Virement bancaire
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    wallet: Mapped["Wallet"] = relationship("Wallet", back_populates="payout_accounts")


class WalletTransaction(UUIDModel):
    __tablename__ = "wallet_transactions"

    wallet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("wallets.id", ondelete="CASCADE"), index=True, nullable=False
    )
    ref: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False) # e.g. TRX-2041
    who: Mapped[str] = mapped_column(String(128), nullable=False)
    mode: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="Validé", nullable=False) # Validé, En cours, Échoué
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    is_credit: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_cash: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    order_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    wallet: Mapped["Wallet"] = relationship("Wallet", back_populates="transactions")

