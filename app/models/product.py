# app/models/product.py
import uuid
from typing import List, Optional
from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import UUIDModel

class Product(UUIDModel):
    __tablename__ = "products"

    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shops.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="Actif", nullable=False) # Actif, Brouillon, Épuisé, Archivé
    category: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    product_type: Mapped[str] = mapped_column(String(64), default="Simple", nullable=False)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    price_old: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stock_main: Mapped[str] = mapped_column(String(64), default="Entrepôt Abidjan", nullable=False)
    stock_rest: Mapped[str] = mapped_column(String(64), default="Rayon boutique", nullable=False)
    sales_30d: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    has_countdown: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    images: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    fiche_produit: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relations
    shop: Mapped["Shop"] = relationship("Shop", back_populates="products")
    inventory_item: Mapped[Optional["InventoryItem"]] = relationship("InventoryItem", back_populates="product", uselist=False, cascade="all, delete-orphan")
    order_items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="product")

