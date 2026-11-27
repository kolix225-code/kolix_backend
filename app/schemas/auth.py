# app/schemas/auth.py
import uuid
from typing import Optional
from pydantic import EmailStr, Field
from app.schemas.common import BaseSchema

class RegisterStep1Request(BaseSchema):
    name: str = Field(..., min_length=2, max_length=128)
    email: EmailStr
    dial: str = Field("+225", max_length=8)
    phone: str = Field(..., min_length=8, max_length=20)
    password: str = Field(..., min_length=6)
    activity: Optional[str] = None
    country: str = "Côte d’Ivoire"
    source: Optional[str] = None
    promo_code: Optional[str] = None
    partner_code: Optional[str] = None # Code partenaire / affiliation

class RegisterStep1Response(BaseSchema):
    user_id: uuid.UUID
    email: Optional[str] = None
    phone: str
    message: str
    otp_debug: Optional[str] = None # Affiché en dev

class VerifyOtpRequest(BaseSchema):
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    identifier: Optional[str] = None # Accepte soit l'email soit le téléphone
    otp_code: str = Field(..., min_length=6, max_length=6)

class LoginRequest(BaseSchema):
    identifier: str # Email ou Téléphone
    password: str

class TokenResponse(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
    email: str
    name: str
    role: str
    permissions: list[str] = ["*"]
    shop_id: Optional[uuid.UUID] = None
    shop_domain: Optional[str] = None

class RefreshTokenRequest(BaseSchema):
    refresh_token: str

class ForgotPasswordRequest(BaseSchema):
    email: EmailStr

class VerifyResetOtpRequest(BaseSchema):
    email: EmailStr
    otp_code: str = Field(..., min_length=6, max_length=6)

class ResetPasswordRequest(BaseSchema):
    email: EmailStr
    otp_code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=6)

