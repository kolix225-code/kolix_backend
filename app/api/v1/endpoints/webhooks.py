# app/api/v1/endpoints/webhooks.py
from fastapi import APIRouter, Query, Request, Response, status
from app.core.config import settings
from app.schemas.common import StandardResponse
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks & Passerelles Tierces"])

@router.get("/whatsapp")
async def verify_whatsapp_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
    hub_verify_token: str = Query(..., alias="hub.verify_token")
):
    """Validation du Webhook Meta Cloud API."""
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN:
        return Response(content=hub_challenge, media_type="text/plain")
    return Response(status_code=status.HTTP_403_FORBIDDEN)

@router.post("/whatsapp")
async def receive_whatsapp_event(request: Request):
    """Réception des statuts de lecture ou messages entrants WhatsApp."""
    payload = await request.json()
    logger.info("Événement WhatsApp reçu", payload=payload)
    return StandardResponse(message="Événement WhatsApp acquitté.")

@router.post("/wave")
async def receive_wave_webhook(request: Request):
    """Notification de paiement instantané Wave."""
    payload = await request.json()
    logger.info("Notification Wave reçue", payload=payload)
    return StandardResponse(message="Paiement Wave traité.")

@router.post("/orange-money")
async def receive_orange_money_webhook(request: Request):
    """Notification d'encaissement Orange Money."""
    payload = await request.json()
    logger.info("Notification Orange Money reçue", payload=payload)
    return StandardResponse(message="Notification OM traitée.")

