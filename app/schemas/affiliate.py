# app/schemas/affiliate.py
import uuid
from typing import List
from app.schemas.common import BaseSchema

class AffiliateReferralResponse(BaseSchema):
    id: uuid.UUID
    referred_shop_name: str
    referred_user_name: str
    source: str
    plan: str
    status: str
    months_count: int
    total_months: int
    earned_total: float
    monthly_commission: float

class AffiliateSummaryResponse(BaseSchema):
    affiliate_code: str
    affiliate_slug: str
    affiliate_link: str
    available_balance: float
    total_earned: float
    is_locked: bool = True
    lock_reason: str = "Programme sur invitation / Accès restreint"
    monthly_gains: List[dict]
    referrals: List[AffiliateReferralResponse]

class TransferCommissionRequest(BaseSchema):
    amount: float

