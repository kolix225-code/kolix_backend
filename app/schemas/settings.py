# app/schemas/settings.py
from typing import Optional
from app.schemas.common import BaseSchema

class StoreSettingsGeneralUpdate(BaseSchema):
    name: Optional[str] = None
    slogan: Optional[str] = None
    currency: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None

class StoreSettingsCodFormUpdate(BaseSchema):
    fields: Optional[dict] = None
    btn_color: Optional[str] = None
    btn_shape: Optional[str] = None
    btn_text: Optional[str] = None
    confirm_msg: Optional[str] = None

class StoreSettingsMarketingUpdate(BaseSchema):
    pixel_meta_id: Optional[str] = None
    pixel_tiktok_id: Optional[str] = None
    capi_token: Optional[str] = None

class StoreSettingsResponse(BaseSchema):
    slogan: Optional[str] = None
    currency: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    pixel_meta_id: Optional[str] = None
    pixel_tiktok_id: Optional[str] = None
    cod_form_config: dict
    notifications_matrix: dict

