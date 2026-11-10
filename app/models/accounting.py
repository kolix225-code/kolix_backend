# app/models/accounting.py
import uuid
from datetime import date
from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import UUIDModel

class Charge(UUIDModel):
    __tablename__ = "charges"

    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shops.id", ondelete="CASCADE"), index=True, nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(64), index=True, nullable=False) # Achat de stock, Transport et livraison, Publicité, Abonnement Kolix, Autres
    payment_mode: Mapped[str] = mapped_column(String(64), default="Mobile Money", nullable=False) # Mobile Money, Espèces, Carte bancaire
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    shop: Mapped["Shop"] = relationship("Shop", back_populates="charges")

