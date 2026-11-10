# app/schemas/order.py
import uuid
from datetime import datetime
from typing import List, Optional
from app.schemas.common import BaseSchema

class OrderItemSchema(BaseSchema):
    product_id: Optional[uuid.UUID] = None
    product_name: str
    variant_label: Optional[str] = None
    quantity: int = 1
    unit_price: float

class CustomerInfo(BaseSchema):
    name: str
    phone: str
    city: str
    address: str

class PublicCheckoutRequest(BaseSchema):
    shop_domain_or_slug: Optional[str] = None
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    city: Optional[str] = None
    delivery_place: Optional[str] = None
    customer: Optional[CustomerInfo] = None
    product_name: Optional[str] = None
    offer: Optional[str] = None
    pack_or_variant: Optional[str] = None
    quantity: int = 1
    amount: Optional[float] = None
    total: Optional[float] = None
    payment_mode: str = "COD_CASH" # COD_CASH, COD_MOMO, cash_on_delivery
    note: Optional[str] = None

class OrderUpdateStatusRequest(BaseSchema):
    status: str # En cours, Livrée, Reportée, Annulée, Contestée, Injoignable

class OrderAssignDeliveryRequest(BaseSchema):
    collaborator_id: uuid.UUID

class OrderResponse(BaseSchema):
    id: str
    shop_id: uuid.UUID
    client_name: str
    client_phone: str
    city: str
    delivery_place: str
    total_amount: float
    status: str
    payment_mode: str
    paid_at: Optional[datetime] = None
    note: Optional[str] = None
    offer_label: Optional[str] = None
    quantity: int = 1
    qr_payload: Optional[str] = None
    assigned_delivery_id: Optional[uuid.UUID] = None
    created_at: datetime
    items: List[OrderItemSchema] = []

