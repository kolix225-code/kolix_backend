# app/api/v1/endpoints/auth.py
from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RegisterStep1Request,
    RegisterStep1Response,
    TokenResponse,
    VerifyOtpRequest,
)
from app.schemas.common import StandardResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentification"])

@router.post("/register/step1", response_model=StandardResponse[RegisterStep1Response])
async def register_step1(
    data: RegisterStep1Request,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Étape 1 : Création du compte et envoi du code OTP WhatsApp."""
    user, otp = await AuthService.register_step1(db, data)
    return StandardResponse(
        message="Code OTP envoyé avec succès sur votre numéro WhatsApp.",
        data=RegisterStep1Response(
            user_id=user.id,
            phone=user.phone_number,
            message="Un code de confirmation vous a été envoyé sur WhatsApp.",
            otp_debug=otp
        )
    )

@router.post("/register/verify-otp", response_model=StandardResponse[TokenResponse])
async def verify_otp(
    data: VerifyOtpRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Étape 2 & 3 : Vérification de l'OTP, activation du compte et provisionnement de la boutique."""
    tokens = await AuthService.verify_otp_and_activate(db, data)
    return StandardResponse(
        message="Compte activé et boutique initialisée avec succès !",
        data=tokens
    )

@router.post("/login", response_model=StandardResponse[TokenResponse])
async def login(
    data: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Connexion avec email ou téléphone et mot de passe Argon2id."""
    tokens = await AuthService.login(db, data.identifier, data.password)
    return StandardResponse(
        message="Connexion réussie.",
        data=tokens
    )

@router.get("/me", response_model=StandardResponse[dict])
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Profil de l'utilisateur connecté."""
    return StandardResponse(
        data={
            "id": str(current_user.id),
            "email": current_user.email,
            "full_name": current_user.full_name,
            "phone_number": current_user.phone_number,
            "role": current_user.role,
            "is_verified": current_user.is_verified,
        }
    )

