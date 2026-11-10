# app/models/whatsapp.py
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import UUIDModel

class WhatsAppCampaign(UUIDModel):
    __tablename__ = "whatsapp_campaigns"

    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shops.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    target_type: Mapped[str] = mapped_column(String(32), default="all", nullable=False) # all, product, date, manual
    target_criteria: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    message_template: Mapped[str] = mapped_column(Text, nullable=False)
    when_type: Mapped[str] = mapped_column(String(16), default="now", nullable=False) # now, schedule
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="Brouillon", nullable=False) # Brouillon, Programmé, En cours, Envoyé, Échoué
    recipients_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sent_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    read_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    shop: Mapped["Shop"] = relationship("Shop", back_populates="whatsapp_campaigns")
    messages: Mapped[List["WhatsAppMessage"]] = relationship("WhatsAppMessage", back_populates="campaign", cascade="all, delete-orphan")


class WhatsAppMessage(UUIDModel):
    __tablename__ = "whatsapp_messages"

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("whatsapp_campaigns.id", ondelete="CASCADE"), index=True, nullable=False
    )
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    client_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="En attente", nullable=False) # En attente, Envoyé, Livré, Lu, Échoué
    wa_message_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    campaign: Mapped["WhatsAppCampaign"] = relationship("WhatsAppCampaign", back_populates="messages")


class SavedAudience(UUIDModel):
    __tablename__ = "saved_audiences"

    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shops.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    criteria: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    contacts_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

