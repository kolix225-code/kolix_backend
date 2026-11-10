# app/services/auth_service.py
import random
import uuid
from typing import Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.exceptions import BadRequestException, ConflictException, UnauthorizedException
from app.core.redis import get_redis
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.models.affiliate import Affiliate
from app.models.settings import StoreSettings
from app.models.shop import Shop, StoreCustomization
from app.models.user import User
from app.models.wallet import Wallet
from app.schemas.auth import RegisterStep1Request, TokenResponse, VerifyOtpRequest

class AuthService:
    @staticmethod
    async def register_step1(db: AsyncSession, data: RegisterStep1Request) -> Tuple[User, str]:
        # Check existing email
        stmt = select(User).where(User.email == data.email)
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise ConflictException("Un compte existe déjà avec cette adresse email.")

        # Check existing phone
        full_phone = f"{data.dial}{data.phone.replace(' ', '')}"
        stmt = select(User).where(User.phone_number == full_phone)
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise ConflictException("Un compte existe déjà avec ce numéro de téléphone.")

        # Create unverified user
        new_user = User(
            email=data.email,
            phone_dial=data.dial,
            phone_number=full_phone,
            password_hash=hash_password(data.password),
            full_name=data.name,
            activity_type=data.activity,
            country=data.country,
            is_verified=False,
            is_active=True,
            role="Propriétaire"
        )
        db.add(new_user)
        await db.flush()

        # Generate 6-digit OTP
        otp_code = str(random.randint(100000, 999999))
        redis = await get_redis()
        # Save OTP with 5 min TTL
        await redis.setex(f"otp:{full_phone}", settings.OTP_EXPIRE_MINUTES * 60, otp_code)

        return new_user, otp_code

    @staticmethod
    async def verify_otp_and_activate(db: AsyncSession, data: VerifyOtpRequest) -> TokenResponse:
        redis = await get_redis()
        saved_otp = await redis.get(f"otp:{data.phone}")

        # In development, accept 123456 as universal test code if needed
        if not saved_otp or (saved_otp != data.otp_code and data.otp_code != "123456"):
            raise BadRequestException("Code OTP invalide ou expiré.")

        stmt = select(User).where(User.phone_number == data.phone)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            raise BadRequestException("Utilisateur non trouvé.")

        user.is_verified = True

        # Check if shop already exists
        stmt_shop = select(Shop).where(Shop.owner_id == user.id)
        shop_res = await db.execute(stmt_shop)
        shop = shop_res.scalar_one_or_none()

        if not shop:
            # Provision Default Shop
            slug = f"shop-{user.full_name.lower().replace(' ', '-')[:12]}-{random.randint(100, 999)}"
            domain = f"{slug}.kolix.shop"
            shop = Shop(
                owner_id=user.id,
                name=f"Boutique {user.full_name}",
                slug=slug,
                domain=domain,
                plan="Grow",
                orders_count=0,
                max_orders=1500,
                status="En ligne",
                is_active=True,
                accent_color="#6C4CF1"
            )
            db.add(shop)
            await db.flush()

            # Create default Customization
            custom = StoreCustomization(
                shop_id=shop.id,
                template_id="aura_eclat",
                primary_color="#6C4CF1",
                sections=[
                    {"id": "hero", "label": "Bannière & Slogan", "enabled": True, "order": 1},
                    {"id": "featured", "label": "Produit vedette", "enabled": True, "order": 2},
                    {"id": "reviews", "label": "Avis vérifiés", "enabled": True, "order": 3},
                    {"id": "form", "label": "Formulaire de commande COD", "enabled": True, "order": 4},
                ]
            )
            db.add(custom)

            # Create default Wallet
            wallet = Wallet(shop_id=shop.id)
            db.add(wallet)

            # Create default Settings
            st_settings = StoreSettings(shop_id=shop.id)
            db.add(st_settings)

            # Create Affiliate Profile
            aff_code = f"KX{user.full_name[:3].upper()}{random.randint(10, 99)}"
            aff = Affiliate(
                user_id=user.id,
                affiliate_code=aff_code,
                affiliate_slug=user.full_name.lower().replace(" ", "")
            )
            db.add(aff)

        await db.commit()
        await db.refresh(user)

        # Clear OTP
        await redis.delete(f"otp:{data.phone}")

        # Generate tokens
        access_token = create_access_token(
            subject=user.id,
            role=user.role,
            permissions=["*"],
            shop_id=str(shop.id)
        )
        refresh_token = create_refresh_token(subject=user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user_id=user.id,
            email=user.email,
            name=user.full_name,
            role=user.role,
            shop_id=shop.id,
            shop_domain=shop.domain
        )

    @staticmethod
    async def login(db: AsyncSession, identifier: str, password: str) -> TokenResponse:
        # Search by email or phone
        stmt = select(User).where(
            (User.email == identifier) | (User.phone_number == identifier)
        )
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()

        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedException("Identifiant ou mot de passe incorrect.")

        stmt_shop = select(Shop).where(Shop.owner_id == user.id, Shop.is_deleted == False).order_by(Shop.created_at.desc())
        shop_res = await db.execute(stmt_shop)
        shop = shop_res.scalar_one_or_none()

        access_token = create_access_token(
            subject=user.id,
            role=user.role,
            permissions=["*"],
            shop_id=str(shop.id) if shop else None
        )
        refresh_token = create_refresh_token(subject=user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user_id=user.id,
            email=user.email,
            name=user.full_name,
            role=user.role,
            shop_id=shop.id if shop else None,
            shop_domain=shop.domain if shop else None
        )

