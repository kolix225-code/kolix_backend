# app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1.endpoints import (
    accounting,
    affiliates,
    ai,
    analytics,
    auth,
    clients,
    inventory,
    media,
    orders,
    products,
    public_store,
    settings,
    shops,
    users,
    webhooks,
    websocket,
    whatsapp,
)
from app.api.v1.endpoints import wallet

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(shops.router)
api_router.include_router(products.router)
api_router.include_router(orders.router)
api_router.include_router(inventory.router)
api_router.include_router(wallet.router)
api_router.include_router(accounting.router)
api_router.include_router(clients.router)
api_router.include_router(whatsapp.router)
api_router.include_router(analytics.router)
api_router.include_router(affiliates.router)
api_router.include_router(settings.router)
api_router.include_router(media.router)
api_router.include_router(ai.router)
api_router.include_router(public_store.router)
api_router.include_router(webhooks.router)
api_router.include_router(websocket.router)

