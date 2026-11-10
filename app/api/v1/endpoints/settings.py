# app/api/v1/endpoints/settings.py
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import PermissionChecker, get_current_shop
from app.models.settings import StoreSettings
from app.models.shop import Shop
from app.schemas.common import StandardResponse
from app.schemas.settings import (
    StoreSettingsCodFormUpdate,
    StoreSettingsGeneralUpdate,
    StoreSettingsMarketingUpdate,
    StoreSettingsResponse,
)

router = APIRouter(prefix="/settings", tags=["Paramètres & Configurations"])

@router.get("/all", response_model=StandardResponse[StoreSettingsResponse], dependencies=[Depends(PermissionChecker("Paramètres"))])
async def get_settings(
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Configuration générale, pixels de tracking et formulaire COD de la boutique."""
    stmt = select(StoreSettings).where(StoreSettings.shop_id == shop.id)
    res = await db.execute(stmt)
    st = res.scalar_one_or_none()
    if not st:
        st = StoreSettings(shop_id=shop.id)
        db.add(st)
        await db.commit()
        await db.refresh(st)

    return StandardResponse(data=StoreSettingsResponse.model_validate(st))

@router.put("/general", response_model=StandardResponse[StoreSettingsResponse], dependencies=[Depends(PermissionChecker("Paramètres"))])
async def update_general(
    data: StoreSettingsGeneralUpdate,
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Mettre à jour le nom, slogan et coordonnées de contact de la boutique."""
    stmt = select(StoreSettings).where(StoreSettings.shop_id == shop.id)
    res = await db.execute(stmt)
    st = res.scalar_one_or_none()
    if not st:
        st = StoreSettings(shop_id=shop.id)
        db.add(st)

    if data.name:
        shop.name = data.name
    if data.slogan is not None:
        st.slogan = data.slogan
    if data.currency:
        st.currency = data.currency
    if data.phone is not None:
        st.phone = data.phone
    if data.email is not None:
        st.email = data.email
    if data.address is not None:
        st.address = data.address

    await db.commit()
    await db.refresh(st)
    return StandardResponse(message="Informations générales mises à jour.", data=StoreSettingsResponse.model_validate(st))

@router.put("/cod-form", response_model=StandardResponse[StoreSettingsResponse], dependencies=[Depends(PermissionChecker("Paramètres"))])
async def update_cod_form(
    data: StoreSettingsCodFormUpdate,
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Personnaliser les champs du formulaire COD, le style du bouton et le message de confirmation."""
    stmt = select(StoreSettings).where(StoreSettings.shop_id == shop.id)
    res = await db.execute(stmt)
    st = res.scalar_one_or_none()
    if not st:
        st = StoreSettings(shop_id=shop.id)
        db.add(st)

    current_cfg = dict(st.cod_form_config)
    if data.fields is not None:
        current_cfg["fields"] = data.fields
    if data.btn_color is not None:
        current_cfg["btn_color"] = data.btn_color
    if data.btn_shape is not None:
        current_cfg["btn_shape"] = data.btn_shape
    if data.btn_text is not None:
        current_cfg["btn_text"] = data.btn_text
    if data.confirm_msg is not None:
        current_cfg["confirm_msg"] = data.confirm_msg

    st.cod_form_config = current_cfg
    await db.commit()
    await db.refresh(st)
    return StandardResponse(message="Design du formulaire COD enregistré.", data=StoreSettingsResponse.model_validate(st))

@router.put("/marketing", response_model=StandardResponse[StoreSettingsResponse], dependencies=[Depends(PermissionChecker("Paramètres"))])
async def update_marketing(
    data: StoreSettingsMarketingUpdate,
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Configurer les identifiants Pixel Meta / TikTok et le token CAPI."""
    stmt = select(StoreSettings).where(StoreSettings.shop_id == shop.id)
    res = await db.execute(stmt)
    st = res.scalar_one_or_none()
    if not st:
        st = StoreSettings(shop_id=shop.id)
        db.add(st)

    if data.pixel_meta_id is not None:
        st.pixel_meta_id = data.pixel_meta_id
    if data.pixel_tiktok_id is not None:
        st.pixel_tiktok_id = data.pixel_tiktok_id
    if data.capi_token is not None:
        st.capi_token = data.capi_token

    await db.commit()
    await db.refresh(st)
    return StandardResponse(message="Pixels publicitaires configurés avec succès.", data=StoreSettingsResponse.model_validate(st))

