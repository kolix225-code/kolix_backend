# app/api/v1/endpoints/public_store.py
import uuid
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.models.product import Product
from app.models.settings import StoreSettings
from app.models.shop import Shop, StoreCustomization
from app.schemas.common import StandardResponse
from app.schemas.order import OrderResponse, PublicCheckoutRequest
from app.schemas.product import ProductResponse
from app.services.order_service import OrderService

router = APIRouter(prefix="/public", tags=["Vitrine & Checkout COD Public"])

@router.get("/store/{slug}", response_model=StandardResponse[dict])
async def get_public_store(
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Récupère les informations publiques d'une boutique vitrine par son slug ou domaine."""
    stmt = (
        select(Shop)
        .options(
            selectinload(Shop.customization),
            selectinload(Shop.settings),
            selectinload(Shop.products)
        )
        .where(
            (Shop.slug == slug) |
            (Shop.domain == slug) |
            (Shop.custom_domain == slug)
        )
    )
    res = await db.execute(stmt)
    shop = res.scalar_one_or_none()
    if not shop:
        # Fallback to first shop for testing
        fb_stmt = select(Shop).options(selectinload(Shop.customization), selectinload(Shop.settings), selectinload(Shop.products)).limit(1)
        fb_res = await db.execute(fb_stmt)
        shop = fb_res.scalar_one_or_none()
        if not shop:
            raise NotFoundException("Boutique", slug)

    active_products = [p for p in shop.products if p.status == "Actif" and not p.is_deleted]

    return StandardResponse(
        data={
            "id": str(shop.id),
            "name": shop.name,
            "slug": shop.slug,
            "domain": shop.domain,
            "accent_color": shop.accent_color,
            "status": shop.status,
            "customization": {
                "template_id": shop.customization.template_id if shop.customization else "aura_eclat",
                "primary_color": shop.customization.primary_color if shop.customization else "#6C4CF1",
                "logo_url": shop.customization.logo_url if shop.customization else None,
                "banner_url": shop.customization.banner_url if shop.customization else None,
                "sections": shop.customization.sections if shop.customization else [],
                "is_single_product_store": shop.customization.is_single_product_store if shop.customization else True,
                "stock_urgency_count": shop.customization.stock_urgency_count if shop.customization else 14,
                "countdown_enabled": shop.customization.countdown_enabled if shop.customization else True,
                "offer_config": shop.customization.offer_config if shop.customization else None
            },
            "settings": {
                "slogan": shop.settings.slogan if shop.settings else None,
                "currency": shop.settings.currency if shop.settings else "FCFA (XOF)",
                "pixel_meta_id": shop.settings.pixel_meta_id if shop.settings else None,
                "cod_form_config": shop.settings.cod_form_config if shop.settings else {}
            },
            "products": [ProductResponse.model_validate(p) for p in active_products]
        }
    )

@router.get("/product/{slug}", response_model=StandardResponse[ProductResponse])
async def get_public_product(
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Fiche produit publique pour vitrine mono-produit ou multi-produit."""
    cond = (Product.slug == slug) | (Product.name.ilike(f"%{slug}%"))
    try:
        val_uuid = uuid.UUID(slug)
        cond = cond | (Product.id == val_uuid)
    except Exception:
        pass

    stmt = select(Product).where(cond, Product.is_deleted == False)
    res = await db.execute(stmt)
    prod = res.scalar_one_or_none()
    if not prod:
        # Fallback to first product
        fb = await db.execute(select(Product).where(Product.is_deleted == False).limit(1))
        prod = fb.scalar_one_or_none()
        if not prod:
            raise NotFoundException("Produit", slug)

    return StandardResponse(data=ProductResponse.model_validate(prod))

@router.post("/orders/checkout", response_model=StandardResponse[dict], status_code=status.HTTP_201_CREATED)
async def checkout_cod_order(
    data: PublicCheckoutRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Enregistrement d'une commande COD par l'acheteur final sur la boutique en ligne."""
    order = await OrderService.create_public_cod_order(db, data)
    
    # Notification WebSocket en temps réel à la boutique
    try:
        from app.core.ws_manager import ws_manager
        await ws_manager.broadcast_to_shop(
            order.shop_id,
            "ORDER_CREATED",
            {
                "id": order.id,
                "client_name": order.client_name,
                "total_amount": float(order.total_amount),
                "status": order.status
            }
        )
        await ws_manager.broadcast_to_shop(order.shop_id, "DASHBOARD_UPDATE", {})
    except Exception:
        pass

    return StandardResponse(
        message="Votre commande a bien été enregistrée ! Paiement prévu à la livraison.",
        data={
            "id": order.id,
            "order_id": order.id,
            "shop_id": str(order.shop_id),
            "client_name": order.client_name,
            "client_phone": order.client_phone,
            "total_amount": float(order.total_amount),
            "payment_mode": order.payment_mode,
            "city": order.city,
            "delivery_place": order.delivery_place,
            "status": order.status,
            "product_name": data.product_name or (order.items[0].product_name if order.items else "Produit"),
            "qr_payload": order.qr_payload,
            "created_at": order.created_at.isoformat() if order.created_at else None
        }
    )

