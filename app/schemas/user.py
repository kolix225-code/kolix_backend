# app/schemas/user.py
import uuid
from typing import List, Optional
from pydantic import EmailStr
from app.schemas.common import BaseSchema

class CollaboratorCreate(BaseSchema):
    name: str
    phone: str
    email: EmailStr
    role: str = "Gestionnaire de commandes"
    permissions: List[str] = ["Accueil", "Commandes", "Stock", "Client"]
    password: Optional[str] = None # Mot de passe défini par le propriétaire

class CollaboratorUpdate(BaseSchema):
    name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None # Actif, Suspendu
    permissions: Optional[List[str]] = None
    password: Optional[str] = None

class CollaboratorResponse(BaseSchema):
    id: uuid.UUID
    shop_id: uuid.UUID
    name: str
    phone: str
    email: str
    role: str
    status: str
    permissions: List[str]
    is_owner: bool

