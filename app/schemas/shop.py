# app/schemas/shop.py
import uuid
from typing import List, Optional
from app.schemas.common import BaseSchema

class ShopCreate(BaseSchema):
    name: str
    slug: Optional[str] = None
    activity: Optional[str] = None
    plan: Optional[str] = "Grow"
    accent_color: str = "#6C4CF1"
    template_id: Optional[str] = "aura_eclat"

class ShopUpdate(BaseSchema):
    name: Optional[str] = None
    slug: Optional[str] = None
    domain: Optional[str] = None
    custom_domain: Optional[str] = None
    plan: Optional[str] = None
    accent_color: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None

class ShopResponse(BaseSchema):
    id: uuid.UUID
    name: str
    slug: str
    domain: str
    custom_domain: Optional[str] = None
    plan: str
    orders_count: int
    max_orders: int
    status: str
    is_active: bool
    accent_color: str
    products_count: Optional[int] = 0
    orders_count_7d: Optional[int] = 0
    template_id: Optional[str] = "aura_eclat"
    template_name: Optional[str] = "Kolix Essentiel"
    logo_url: Optional[str] = None

class StoreTemplateResponse(BaseSchema):
    id: uuid.UUID
    slug: str
    name: str
    niche: str
    style: str
    price: float
    price_label: str
    is_free: bool
    accent_color: str
    hero_text: Optional[str] = None
    sub_text: Optional[str] = None

class StoreCustomizationUpdate(BaseSchema):
    template_id: Optional[str] = None
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    primary_color: Optional[str] = None
    sections: Optional[List[dict]] = None
    is_single_product_store: Optional[bool] = None
    stock_urgency_count: Optional[int] = None
    countdown_enabled: Optional[bool] = None
    offer_config: Optional[dict] = None

class StoreCustomizationResponse(BaseSchema):
    shop_id: uuid.UUID
    template_id: str
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    primary_color: str
    sections: List[dict]
    is_single_product_store: bool = True
    stock_urgency_count: int = 14
    countdown_enabled: bool = True
    offer_config: Optional[dict] = None

