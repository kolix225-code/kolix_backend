# app/schemas/whatsapp.py
import uuid
from datetime import datetime
from typing import Optional
from app.schemas.common import BaseSchema

class WhatsAppCampaignCreate(BaseSchema):
    name: str
    target_type: str = "all" # all, product, date, manual
    target_criteria: dict = {}
    message_template: str
    when_type: str = "now" # now, schedule
    scheduled_at: Optional[datetime] = None

class WhatsAppCampaignResponse(BaseSchema):
    id: uuid.UUID
    name: str
    target_type: str
    when_type: str
    scheduled_at: Optional[datetime] = None
    status: str
    recipients_count: int
    sent_count: int
    read_count: int
    created_at: datetime

class SavedAudienceCreate(BaseSchema):
    name: str
    criteria: dict = {}

class SavedAudienceResponse(BaseSchema):
    id: uuid.UUID
    name: str
    criteria: dict
    contacts_count: int

