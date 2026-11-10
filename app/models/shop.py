# app/models/shop.py
import uuid
from typing import List, Optional
from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import UUIDModel

class Shop(UUIDModel):
    __tablename__ = "shops"

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    domain: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    custom_domain: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    plan: Mapped[str] = mapped_column(String(32), default="Grow", nullable=False) # Start, Grow, Pro, Empire
    orders_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_orders: Mapped[int] = mapped_column(Integer, default=1500, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="En ligne", nullable=False) # En ligne, En maintenance
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    accent_color: Mapped[str] = mapped_column(String(16), default="#6C4CF1", nullable=False)

    # Relations
    owner: Mapped["User"] = relationship("User", back_populates="shops")
    collaborators: Mapped[List["Collaborator"]] = relationship("Collaborator", back_populates="shop", cascade="all, delete-orphan")
    customization: Mapped[Optional["StoreCustomization"]] = relationship("StoreCustomization", back_populates="shop", uselist=False, cascade="all, delete-orphan")
    products: Mapped[List["Product"]] = relationship("Product", back_populates="shop", cascade="all, delete-orphan")
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="shop", cascade="all, delete-orphan")
    wallet: Mapped[Optional["Wallet"]] = relationship("Wallet", back_populates="shop", uselist=False, cascade="all, delete-orphan")
    inventory_items: Mapped[List["InventoryItem"]] = relationship("InventoryItem", back_populates="shop", cascade="all, delete-orphan")
    charges: Mapped[List["Charge"]] = relationship("Charge", back_populates="shop", cascade="all, delete-orphan")
    settings: Mapped[Optional["StoreSettings"]] = relationship("StoreSettings", back_populates="shop", uselist=False, cascade="all, delete-orphan")
    whatsapp_campaigns: Mapped[List["WhatsAppCampaign"]] = relationship("WhatsAppCampaign", back_populates="shop", cascade="all, delete-orphan")


class StoreCustomization(UUIDModel):
    __tablename__ = "store_customizations"

    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shops.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    template_id: Mapped[str] = mapped_column(String(64), default="aura_eclat", nullable=False)
    logo_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    banner_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    primary_color: Mapped[str] = mapped_column(String(16), default="#6C4CF1", nullable=False)
    sections: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    is_single_product_store: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    stock_urgency_count: Mapped[int] = mapped_column(Integer, default=14, nullable=False)
    countdown_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    offer_config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    shop: Mapped["Shop"] = relationship("Shop", back_populates="customization")


class StoreTemplate(UUIDModel):
    __tablename__ = "store_templates"

    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    niche: Mapped[str] = mapped_column(String(64), nullable=False)
    style: Mapped[str] = mapped_column(String(64), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    price_label: Mapped[str] = mapped_column(String(32), default="Gratuit", nullable=False)
    is_free: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    accent_color: Mapped[str] = mapped_column(String(16), default="#6C4CF1", nullable=False)
    hero_text: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sub_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

