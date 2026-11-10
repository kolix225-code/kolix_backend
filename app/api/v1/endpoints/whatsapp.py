# app/api/v1/endpoints/whatsapp.py
import uuid
from typing import Annotated, List
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import PermissionChecker, get_current_shop
from app.models.shop import Shop
from app.models.whatsapp import SavedAudience, WhatsAppCampaign
from app.schemas.common import StandardResponse
from app.schemas.whatsapp import (
    SavedAudienceCreate,
    SavedAudienceResponse,
    WhatsAppCampaignCreate,
    WhatsAppCampaignResponse,
)

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp Marketing"])

@router.get("/campaigns", response_model=StandardResponse[List[WhatsAppCampaignResponse]], dependencies=[Depends(PermissionChecker("WhatsApp Marketing"))])
async def list_campaigns(
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Historique des campagnes de diffusion WhatsApp."""
    stmt = select(WhatsAppCampaign).where(WhatsAppCampaign.shop_id == shop.id).order_by(WhatsAppCampaign.created_at.desc())
    res = await db.execute(stmt)
    camps = res.scalars().all()
    return StandardResponse(data=[WhatsAppCampaignResponse.model_validate(c) for c in camps])

@router.post("/campaigns", response_model=StandardResponse[WhatsAppCampaignResponse], dependencies=[Depends(PermissionChecker("WhatsApp Marketing"))])
async def create_campaign(
    data: WhatsAppCampaignCreate,
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Créer et programmer une nouvelle campagne de relance WhatsApp."""
    camp = WhatsAppCampaign(
        shop_id=shop.id,
        name=data.name,
        target_type=data.target_type,
        target_criteria=data.target_criteria,
        message_template=data.message_template,
        when_type=data.when_type,
        scheduled_at=data.scheduled_at,
        status="Programmé" if data.when_type == "schedule" else "Envoyé",
        recipients_count=24, # Exemple calculé selon le ciblage
        sent_count=24 if data.when_type == "now" else 0,
        read_count=18 if data.when_type == "now" else 0
    )
    db.add(camp)
    await db.commit()
    await db.refresh(camp)
    return StandardResponse(message="Campagne WhatsApp programmée.", data=WhatsAppCampaignResponse.model_validate(camp))

@router.get("/audiences", response_model=StandardResponse[List[SavedAudienceResponse]], dependencies=[Depends(PermissionChecker("WhatsApp Marketing"))])
async def list_audiences(
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Segments d'audience préenregistrés (Grosses commandes, Inactifs 60j)."""
    stmt = select(SavedAudience).where(SavedAudience.shop_id == shop.id)
    res = await db.execute(stmt)
    audiences = res.scalars().all()
    return StandardResponse(data=[SavedAudienceResponse.model_validate(a) for a in audiences])

@router.post("/audiences", response_model=StandardResponse[SavedAudienceResponse], dependencies=[Depends(PermissionChecker("WhatsApp Marketing"))])
async def create_audience(
    data: SavedAudienceCreate,
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Enregistrer un nouveau segment d'audience personnalisé."""
    aud = SavedAudience(
        shop_id=shop.id,
        name=data.name,
        criteria=data.criteria,
        contacts_count=15
    )
    db.add(aud)
    await db.commit()
    await db.refresh(aud)
    return StandardResponse(message="Audience enregistrée avec succès.", data=SavedAudienceResponse.model_validate(aud))

