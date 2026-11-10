# app/api/v1/endpoints/shops.py
import uuid
from typing import Annotated, List
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import PermissionChecker, get_current_shop, get_current_user
from app.core.exceptions import NotFoundException
from app.models.shop import Shop, StoreCustomization, StoreTemplate
from app.models.user import User
from app.schemas.common import StandardResponse
from app.schemas.shop import (
    ShopCreate,
    ShopResponse,
    StoreCustomizationResponse,
    StoreCustomizationUpdate,
    StoreTemplateResponse,
)

router = APIRouter(prefix="/stores", tags=["Boutique & Thèmes"])

@router.get("/templates", response_model=StandardResponse[List[StoreTemplateResponse]])
async def list_templates(db: Annotated[AsyncSession, Depends(get_db)]):
    """Catalogue complet des templates COD de la marketplace Kolix."""
    stmt = select(StoreTemplate).order_by(StoreTemplate.created_at.desc())
    res = await db.execute(stmt)
    templates = res.scalars().all()
    return StandardResponse(data=[StoreTemplateResponse.model_validate(t) for t in templates])

@router.get("/my-stores", response_model=StandardResponse[List[ShopResponse]])
async def list_my_stores(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Liste des boutiques créées par le commerçant."""
    stmt = select(Shop).where(Shop.owner_id == current_user.id, Shop.is_deleted == False)
    res = await db.execute(stmt)
    shops = res.scalars().all()
    return StandardResponse(data=[ShopResponse.model_validate(s) for s in shops])

@router.get("/{id}/customization", response_model=StandardResponse[StoreCustomizationResponse])
async def get_customization(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Paramètres visuels (couleurs, logo, sections) du thème de la boutique."""
    stmt = select(StoreCustomization).where(StoreCustomization.shop_id == id)
    res = await db.execute(stmt)
    custom = res.scalar_one_or_none()
    if not custom:
        raise NotFoundException("Personnalisation de boutique", str(id))
    return StandardResponse(data=StoreCustomizationResponse.model_validate(custom))

@router.put(
    "/{id}/customization",
    response_model=StandardResponse[StoreCustomizationResponse],
    dependencies=[Depends(PermissionChecker("Boutique"))]
)
async def update_customization(
    id: uuid.UUID,
    data: StoreCustomizationUpdate,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Mettre à jour le thème actif, logo et l'ordre des sections."""
    stmt = select(StoreCustomization).where(StoreCustomization.shop_id == id)
    res = await db.execute(stmt)
    custom = res.scalar_one_or_none()
    if not custom:
        raise NotFoundException("Personnalisation de boutique", str(id))

    if data.template_id:
        custom.template_id = data.template_id
    if data.logo_url:
        custom.logo_url = data.logo_url
    if data.banner_url:
        custom.banner_url = data.banner_url
    if data.primary_color:
        custom.primary_color = data.primary_color
    if data.sections is not None:
        custom.sections = data.sections
    if data.is_single_product_store is not None:
        custom.is_single_product_store = data.is_single_product_store
    if data.stock_urgency_count is not None:
        custom.stock_urgency_count = data.stock_urgency_count
    if data.countdown_enabled is not None:
        custom.countdown_enabled = data.countdown_enabled
    if data.offer_config is not None:
        custom.offer_config = data.offer_config

    await db.commit()
    await db.refresh(custom)
    return StandardResponse(message="Thème personnalisé avec succès.", data=StoreCustomizationResponse.model_validate(custom))

