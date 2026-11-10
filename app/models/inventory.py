# app/models/inventory.py
import uuid
from typing import Optional
from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import UUIDModel

class InventoryItem(UUIDModel):
    __tablename__ = "inventory_items"

    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shops.id", ondelete="CASCADE"), index=True, nullable=False
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    num: Mapped[str] = mapped_column(String(32), index=True, nullable=False) # e.g. PRD-01
    qty_initial: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    qty_sold: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    qty_remaining: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    threshold: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    unit_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="Optimal", nullable=False) # Optimal, Faible, Critique, Rupture

    shop: Mapped["Shop"] = relationship("Shop", back_populates="inventory_items")
    product: Mapped["Product"] = relationship("Product", back_populates="inventory_item")


class StockMovement(UUIDModel):
    __tablename__ = "stock_movements"

    inventory_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory_items.id", ondelete="CASCADE"), index=True, nullable=False
    )
    type: Mapped[str] = mapped_column(String(32), nullable=False) # Entrée, Vente, Ajustement, Retour
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

