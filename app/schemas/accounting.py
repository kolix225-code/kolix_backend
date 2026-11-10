# app/schemas/accounting.py
import uuid
from datetime import date
from typing import Dict, List
from app.schemas.common import BaseSchema

class ChargeCreate(BaseSchema):
    date: date
    label: str
    category: str # Achat de stock, Transport et livraison, Publicité, Abonnement Kolix, Autres
    payment_mode: str = "Mobile Money"
    amount: float

class ChargeResponse(BaseSchema):
    id: uuid.UUID
    date: date
    label: str
    category: str
    payment_mode: str
    amount: float

class AccountingDashboardResponse(BaseSchema):
    period: str
    total_revenue: float
    total_charges: float
    net_profit: float
    margin_percentage: float
    charges_by_category: Dict[str, float]
    recent_transactions: List[dict]

