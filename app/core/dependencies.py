# app/core/dependencies.py
import uuid
from typing import Annotated, List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.models.shop import Shop
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False
)

async def get_current_user(
    token: Annotated[Optional[str], Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    if not token:
        raise UnauthorizedException("Jeton d'authentification manquant.")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str: str = payload.get("sub")
        if not user_id_str:
            raise UnauthorizedException("Jeton d'authentification invalide.")
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise UnauthorizedException("Session expirée ou jeton invalide.")

    stmt = select(User).where(User.id == user_id, User.is_deleted == False)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise UnauthorizedException("Utilisateur non trouvé.")
    if not user.is_active:
        raise ForbiddenException("Ce compte utilisateur est désactivé.")
    return user


async def get_current_shop(
    token: Annotated[Optional[str], Depends(oauth2_scheme)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Shop:
    # 1. Vérifier si un shop_id valide est encodé dans le token JWT
    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            shop_id_str = payload.get("shop_id")
            if shop_id_str:
                stmt_t = select(Shop).where(Shop.id == uuid.UUID(shop_id_str), Shop.is_deleted == False)
                res_t = await db.execute(stmt_t)
                shop = res_t.scalar_one_or_none()
                if shop:
                    return shop
        except Exception:
            pass

    # 2. Si le compte connecté est le propriétaire d'une boutique
    stmt = select(Shop).where(Shop.owner_id == current_user.id, Shop.is_deleted == False).order_by(Shop.created_at.desc())
    result = await db.execute(stmt)
    shop = result.scalar_one_or_none()
    if shop:
        return shop

    # 3. Si le compte connecté est un collaborateur
    from app.models.user import Collaborator
    stmt_collab = select(Collaborator).where(
        (Collaborator.email == current_user.email) | (Collaborator.phone == current_user.phone_number),
        Collaborator.is_deleted == False
    )
    res_collab = await db.execute(stmt_collab)
    collab = res_collab.scalar_one_or_none()
    if collab:
        stmt_shop = select(Shop).where(Shop.id == collab.shop_id, Shop.is_deleted == False)
        res_shop = await db.execute(stmt_shop)
        shop = res_shop.scalar_one_or_none()
        if shop:
            return shop

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Aucune boutique active trouvée pour ce compte."
    )


class PermissionChecker:
    def __init__(self, required_module: str):
        self.required_module = required_module

    def __call__(
        self,
        token: Annotated[Optional[str], Depends(oauth2_scheme)]
    ) -> bool:
        if not token:
            raise UnauthorizedException("Accès non authentifié.")
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_perms: List[str] = payload.get("perms", [])
            # Les propriétaires possèdent le joker '*'
            if "*" in user_perms or self.required_module in user_perms:
                return True
            raise ForbiddenException(f"Accès refusé au module '{self.required_module}'.")
        except JWTError:
            raise UnauthorizedException("Jeton invalide.")

