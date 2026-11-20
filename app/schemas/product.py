# app/schemas/product.py
import uuid
from typing import List, Optional
from app.schemas.common import BaseSchema

class ProductCreate(BaseSchema):
    shop_id: Optional[uuid.UUID] = None
    name: str
    category: str
    price: float
    price_old: Optional[float] = None
    stock_quantity: int = 0
    stock_main: str = "Entrepôt Abidjan"
    stock_rest: str = "Rayon boutique"
    product_type: str = "Simple"
    has_countdown: bool = False
    description: Optional[str] = None
    images: List[str] = []
    fiche_produit: Optional[dict] = None

class ProductUpdate(BaseSchema):
    name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    price_old: Optional[float] = None
    stock_quantity: Optional[int] = None
    stock_main: Optional[str] = None
    stock_rest: Optional[str] = None
    status: Optional[str] = None
    has_countdown: Optional[bool] = None
    description: Optional[str] = None
    images: Optional[List[str]] = None
    fiche_produit: Optional[dict] = None

class ProductResponse(BaseSchema):
    id: uuid.UUID
    shop_id: uuid.UUID
    name: str
    slug: str
    category: str
    price: float
    price_old: Optional[float] = None
    stock_quantity: int
    stock_main: str
    stock_rest: str
    status: str
    sales_30d: int
    has_countdown: bool
    description: Optional[str] = None
    images: List[str]
    fiche_produit: Optional[dict] = None
    shop_name: Optional[str] = None
    shop_domain: Optional[str] = None
    shop_logo: Optional[str] = None

class BulkStatusRequest(BaseSchema):
    product_ids: List[uuid.UUID]
    new_status: str # Actif, Brouillon, Archivé

