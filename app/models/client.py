# app/models/client.py
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import UUIDModel

class Client(UUIDModel):
    __tablename__ = "clients"

    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shops.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    city: Mapped[str] = mapped_column(String(64), nullable=False)
    place: Mapped[str] = mapped_column(String(255), nullable=False)
    total_orders: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    total_spent: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    delivery_success_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=100.00, nullable=False)
    last_order_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

