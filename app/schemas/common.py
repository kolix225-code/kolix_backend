# app/schemas/common.py
from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class StandardResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Opération réussie"
    data: Optional[T] = None
    meta: Optional[dict] = None

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int

