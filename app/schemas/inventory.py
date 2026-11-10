# app/schemas/inventory.py
import uuid
from typing import Optional
from app.schemas.common import BaseSchema

class RestockRequest(BaseSchema):
    quantity: int
    unit_cost: Optional[float] = None
    note: Optional[str] = None

class ThresholdUpdateRequest(BaseSchema):
    threshold: int

class InventoryItemResponse(BaseSchema):
    id: uuid.UUID
    shop_id: uuid.UUID
    product_id: uuid.UUID
    product_name: Optional[str] = None
    num: str
    qty_initial: int
    qty_sold: int
    qty_remaining: int
    threshold: int
    unit_cost: float
    status: str

class StockKpisResponse(BaseSchema):
    total_value: float
    under_threshold_count: int
    pending_restock_count: int
    turnover_rate: str
    out_of_stock_count: int

