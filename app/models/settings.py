# app/models/settings.py
import uuid
from typing import Optional
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import UUIDModel

class StoreSettings(UUIDModel):
    __tablename__ = "store_settings"

    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shops.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    slogan: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    currency: Mapped[str] = mapped_column(String(16), default="FCFA (XOF)", nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Marketing Pixels
    pixel_meta_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    pixel_tiktok_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    capi_token: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Formulaire COD personnalisé
    cod_form_config: Mapped[dict] = mapped_column(
        JSONB,
        default=lambda: {
            "fields": {"nom": True, "prenom": True, "tel": True, "lieu": True, "note": True, "consent": True},
            "btn_color": "#C93C72",
            "btn_shape": "round",
            "btn_text": "Commander maintenant",
            "confirm_msg": "Merci ! Votre commande est bien reçue. Notre livreur vous appelle avant de passer."
        },
        nullable=False
    )

    # Notifications Matrix (SMS, WhatsApp, Email)
    notifications_matrix: Mapped[dict] = mapped_column(
        JSONB,
        default=lambda: {
            "stock": [True, True, False],
            "order": [True, True, False],
            "pay": [True, False, True],
            "withdraw": [True, False, True],
            "weekly": [False, False, True]
        },
        nullable=False
    )

    shop: Mapped["Shop"] = relationship("Shop", back_populates="settings")

