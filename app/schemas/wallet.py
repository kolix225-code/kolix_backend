# app/schemas/wallet.py
import uuid
from datetime import datetime
from typing import List, Optional
from app.schemas.common import BaseSchema

class WalletSummaryResponse(BaseSchema):
    digital_balance: float
    cash_balance: float
    pending_balance: float
    withdrawn_this_month: float
    kolix_commission: float
    avg_transfer_time: str = "24 min"
    is_digital_locked: bool = True
    digital_lock_reason: Optional[str] = "Vérification KYC requise"

class PayoutAccountCreate(BaseSchema):
    name: str
    num: str
    provider: str # Wave, Orange Money, MTN MoMo, Moov Money, Virement bancaire
    is_default: bool = False

class PayoutAccountResponse(BaseSchema):
    id: uuid.UUID
    name: str
    num: str
    provider: str
    is_default: bool

class WithdrawRequest(BaseSchema):
    amount: float
    payout_account_id: uuid.UUID

class WalletTransactionResponse(BaseSchema):
    id: uuid.UUID
    ref: str
    who: str
    mode: str
    status: str
    amount: float
    is_credit: bool
    is_cash: bool
    order_id: Optional[str] = None
    created_at: datetime

