# app/schemas/accounting.py
import uuid
from datetime import date
from typing import Dict, List, Optional
from app.schemas.common import BaseSchema

class ChargeCreate(BaseSchema):
    date: Optional[date] = None
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
    momo_revenue: float = 0.0
    cash_revenue: float = 0.0
    momo_percentage: float = 0.0
    cash_percentage: float = 0.0
    charges_by_category: Dict[str, float]
    monthly_history: List[dict] = []
    recent_transactions: List[dict] = []

