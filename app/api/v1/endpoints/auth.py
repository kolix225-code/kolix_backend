# app/api/v1/endpoints/auth.py
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, status
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_shop, get_current_user, oauth2_scheme
from app.models.shop import Shop
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RegisterStep1Request,
    RegisterStep1Response,
    TokenResponse,
    VerifyOtpRequest,
    ForgotPasswordRequest,
    VerifyResetOtpRequest,
    ResetPasswordRequest,
)
from app.schemas.common import StandardResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentification"])

@router.post("/register/step1", response_model=StandardResponse[RegisterStep1Response])
async def register_step1(
    data: RegisterStep1Request,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Étape 1 : Création du compte et envoi du code OTP par Email (Brevo)."""
    user, otp = await AuthService.register_step1(db, data)
    return StandardResponse(
        message="Code OTP envoyé avec succès sur votre adresse email.",
        data=RegisterStep1Response(
            user_id=user.id,
            email=user.email,
            phone=user.phone_number,
            message=f"Un code de confirmation a été envoyé à {user.email}.",
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

@router.post("/forgot-password", response_model=StandardResponse[dict])
async def forgot_password(
    data: ForgotPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Étape 1 : Demande de réinitialisation de mot de passe et envoi du code OTP par email."""
    otp = await AuthService.forgot_password_request(db, data.email)
    return StandardResponse(
        message="Code de réinitialisation envoyé avec succès à votre adresse e-mail.",
        data={"email": data.email, "otp_debug": otp if settings.ENVIRONMENT == "development" else None}
    )

@router.post("/verify-reset-otp", response_model=StandardResponse[dict])
async def verify_reset_otp(
    data: VerifyResetOtpRequest
):
    """Étape 2 : Vérification du code OTP de réinitialisation reçu."""
    await AuthService.verify_reset_otp(data.email, data.otp_code)
    return StandardResponse(
        message="Code de confirmation validé avec succès.",
        data={"verified": True, "email": data.email}
    )

@router.post("/reset-password", response_model=StandardResponse[dict])
async def reset_password(
    data: ResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Étape 3 : Définition du nouveau mot de passe."""
    await AuthService.reset_password(db, data.email, data.otp_code, data.new_password)
    return StandardResponse(
        message="Votre mot de passe a été modifié avec succès. Vous pouvez maintenant vous connecter.",
        data={"success": True}
    )


@router.get("/me", response_model=StandardResponse[dict])
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
    token: Annotated[Optional[str], Depends(oauth2_scheme)] = None,
    shop: Annotated[Optional[Shop], Depends(get_current_shop)] = None
):
    """Profil de l'utilisateur connecté avec permissions et boutique."""
    permissions = ["*"]
    role = current_user.role
    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            if "perms" in payload:
                permissions = payload["perms"]
            if "role" in payload:
                role = payload["role"]
        except Exception:
            pass

    return StandardResponse(
        data={
            "id": str(current_user.id),
            "email": current_user.email,
            "full_name": current_user.full_name,
            "phone_number": current_user.phone_number,
            "role": role,
            "permissions": permissions,
            "shop_id": str(shop.id) if shop else None,
            "shop_domain": shop.domain if shop else None,
            "shop_name": shop.name if shop else None,
            "is_verified": current_user.is_verified,
        }
    )

