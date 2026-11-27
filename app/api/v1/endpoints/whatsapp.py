# app/api/v1/endpoints/whatsapp.py
import uuid
from typing import Annotated, List
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import PermissionChecker, get_current_shop
from app.core.exceptions import NotFoundException
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
    """Créer et enregistrer une nouvelle campagne WhatsApp."""
    criteria = data.target_criteria if isinstance(data.target_criteria, dict) else {}
    recipients_count = int(criteria.get("recipients_count", 0))
    sent_count = int(criteria.get("sent_count", recipients_count if data.when_type == "now" else 0))
    read_count = int(criteria.get("read_count", int(sent_count * 0.94) if data.when_type == "now" else 0))

    camp = WhatsAppCampaign(
        shop_id=shop.id,
        name=data.name.strip() or "Campagne WhatsApp",
        target_type=data.target_type,
        target_criteria=criteria,
        message_template=data.message_template,
        when_type=data.when_type,
        scheduled_at=data.scheduled_at,
        status="Programmée" if data.when_type == "schedule" else "Envoyée",
        recipients_count=recipients_count,
        sent_count=sent_count,
        read_count=read_count
    )
    db.add(camp)
    await db.commit()
    await db.refresh(camp)
    return StandardResponse(
        message=f"Campagne WhatsApp '{camp.name}' enregistrée avec succès.",
        data=WhatsAppCampaignResponse.model_validate(camp)
    )

@router.delete("/campaigns/{id}", response_model=StandardResponse[dict], dependencies=[Depends(PermissionChecker("WhatsApp Marketing"))])
async def delete_campaign(
    id: uuid.UUID,
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Supprimer une campagne de l'historique."""
    stmt = select(WhatsAppCampaign).where(WhatsAppCampaign.id == id, WhatsAppCampaign.shop_id == shop.id)
    res = await db.execute(stmt)
    camp = res.scalar_one_or_none()
    if not camp:
        raise NotFoundException("Campagne WhatsApp", str(id))
    await db.delete(camp)
    await db.commit()
    return StandardResponse(message="Campagne supprimée avec succès.", data={"id": str(id)})

@router.get("/audiences", response_model=StandardResponse[List[SavedAudienceResponse]], dependencies=[Depends(PermissionChecker("WhatsApp Marketing"))])
async def list_audiences(
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Segments d'audience préenregistrés."""
    stmt = select(SavedAudience).where(SavedAudience.shop_id == shop.id).order_by(SavedAudience.created_at.desc())
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
    criteria = data.criteria if isinstance(data.criteria, dict) else {}
    contacts_count = int(criteria.get("contacts_count", 0))

    aud = SavedAudience(
        shop_id=shop.id,
        name=data.name.strip(),
        criteria=criteria,
        contacts_count=contacts_count
    )
    db.add(aud)
    await db.commit()
    await db.refresh(aud)
    return StandardResponse(message=f"Audience '{aud.name}' enregistrée avec succès.", data=SavedAudienceResponse.model_validate(aud))
