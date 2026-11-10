# app/schemas/client.py
import uuid
from datetime import datetime
from typing import Optional
from app.schemas.common import BaseSchema

class ClientResponse(BaseSchema):
    id: uuid.UUID
    name: str
    phone: str
    city: str
    place: str
    total_orders: int
    total_spent: float
    delivery_success_rate: float
    last_order_date: Optional[datetime] = None

