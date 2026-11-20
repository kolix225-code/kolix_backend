# app/api/v1/endpoints/shops.py
import re
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.dependencies import PermissionChecker, get_current_shop, get_current_user
from app.core.exceptions import NotFoundException
from app.models.product import Product
from app.models.settings import StoreSettings
from app.models.shop import Shop, StoreCustomization, StoreTemplate
from app.models.user import User
from app.models.wallet import Wallet
from app.schemas.common import StandardResponse
from app.schemas.product import ProductResponse
from app.schemas.shop import (
    ShopCreate,
    ShopResponse,
    ShopUpdate,
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
    """Liste complète des boutiques créées par le commerçant avec stats dynamiques."""
    stmt = (
        select(Shop)
        .options(
            selectinload(Shop.customization),
            selectinload(Shop.products),
            selectinload(Shop.orders)
        )
        .where(Shop.owner_id == current_user.id, Shop.is_deleted == False)
        .order_by(Shop.created_at.desc())
    )
    res = await db.execute(stmt)
    shops = res.scalars().all()

    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    result: List[ShopResponse] = []

    for s in shops:
        active_products = [p for p in s.products if not p.is_deleted]
        orders_7d = [
            o for o in s.orders
            if not o.is_deleted and (o.created_at.replace(tzinfo=timezone.utc) if o.created_at.tzinfo is None else o.created_at) >= seven_days_ago
        ]

        tpl_name = "Kolix Essentiel"
        tpl_id = "f-0"
        logo_url = None
        if s.customization:
            if s.customization.template_id:
                tpl_id = s.customization.template_id
                if tpl_id in ("f-0", "aura_eclat"):
                    tpl_name = "Kolix Essentiel"
                elif tpl_id == "f-1":
                    tpl_name = "Kolix Vitrine"
                else:
                    tpl_name = tpl_id.replace("-", " ").title()
            logo_url = s.customization.logo_url

        resp = ShopResponse(
            id=s.id,
            name=s.name,
            slug=s.slug,
            domain=s.domain,
            custom_domain=s.custom_domain,
            plan=s.plan,
            orders_count=len(s.orders),
            max_orders=s.max_orders,
            status=s.status,
            is_active=s.is_active,
            accent_color=s.accent_color,
            products_count=len(active_products),
            orders_count_7d=len(orders_7d),
            template_id=tpl_id,
            template_name=tpl_name,
            logo_url=logo_url
        )
        result.append(resp)

    return StandardResponse(data=result)

@router.post("", response_model=StandardResponse[ShopResponse])
async def create_store(
    data: ShopCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Créer une nouvelle boutique pour le commerçant."""
    clean_name = data.name.strip()
    base_slug = data.slug or re.sub(r"[^a-z0-9]+", "-", clean_name.lower()).strip("-")
    if not base_slug:
        base_slug = f"boutique-{random.randint(100, 999)}"

    unique_suffix = str(random.randint(100, 999))
    slug = f"{base_slug[:24]}-{unique_suffix}"
    domain = f"{slug}.kolix.shop"

    max_orders_map = {
        "Start": 700,
        "Grow": 1500,
        "Pro": 999999,
        "Empire": 999999
    }
    plan = data.plan or "Grow"
    max_orders = max_orders_map.get(plan, 1500)

    shop = Shop(
        owner_id=current_user.id,
        name=clean_name,
        slug=slug,
        domain=domain,
        plan=plan,
        orders_count=0,
        max_orders=max_orders,
        status="En ligne",
        is_active=True,
        accent_color=data.accent_color or "#6C4CF1"
    )
    db.add(shop)
    await db.flush()

    # Créer la personnalisation par défaut
    custom = StoreCustomization(
        shop_id=shop.id,
        template_id=data.template_id or "aura_eclat",
        primary_color=shop.accent_color,
        sections=[
            {"id": "hero", "label": "Bannière & Slogan", "enabled": True, "order": 1},
            {"id": "featured", "label": "Produit vedette", "enabled": True, "order": 2},
            {"id": "reviews", "label": "Avis vérifiés", "enabled": True, "order": 3},
            {"id": "form", "label": "Formulaire de commande COD", "enabled": True, "order": 4},
        ]
    )
    db.add(custom)

    # Créer le portefeuille associé
    wallet = Wallet(shop_id=shop.id)
    db.add(wallet)

    # Créer les paramètres de la boutique
    st_settings = StoreSettings(
        shop_id=shop.id,
        slogan=f"Bienvenue chez {clean_name}"
    )
    db.add(st_settings)

    await db.commit()
    await db.refresh(shop)

    resp = ShopResponse(
        id=shop.id,
        name=shop.name,
        slug=shop.slug,
        domain=shop.domain,
        custom_domain=shop.custom_domain,
        plan=shop.plan,
        orders_count=0,
        max_orders=shop.max_orders,
        status=shop.status,
        is_active=shop.is_active,
        accent_color=shop.accent_color,
        products_count=0,
        orders_count_7d=0,
        template_id=custom.template_id,
        template_name="Kolix Essentiel",
        logo_url=None
    )
    return StandardResponse(message=f"Boutique '{shop.name}' créée avec succès !", data=resp)

@router.get("/{id}", response_model=StandardResponse[ShopResponse])
async def get_store(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Détails d'une boutique avec stats."""
    stmt = (
        select(Shop)
        .options(selectinload(Shop.customization), selectinload(Shop.products), selectinload(Shop.orders))
        .where(Shop.id == id, Shop.is_deleted == False)
    )
    res = await db.execute(stmt)
    s = res.scalar_one_or_none()
    if not s:
        raise NotFoundException("Boutique", str(id))

    return StandardResponse(
        data=ShopResponse(
            id=s.id,
            name=s.name,
            slug=s.slug,
            domain=s.domain,
            custom_domain=s.custom_domain,
            plan=s.plan,
            orders_count=len(s.orders),
            max_orders=s.max_orders,
            status=s.status,
            is_active=s.is_active,
            accent_color=s.accent_color,
            products_count=len([p for p in s.products if not p.is_deleted]),
            orders_count_7d=0,
            template_id=s.customization.template_id if s.customization else "aura_eclat",
            template_name="Kolix Essentiel",
            logo_url=s.customization.logo_url if s.customization else None
        )
    )

@router.put("/{id}", response_model=StandardResponse[ShopResponse])
async def update_store(
    id: uuid.UUID,
    data: ShopUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Mettre à jour les informations d'une boutique (nom, domaine personnalisé, accent_color, etc.)."""
    stmt = select(Shop).where(Shop.id == id, Shop.owner_id == current_user.id, Shop.is_deleted == False)
    res = await db.execute(stmt)
    shop = res.scalar_one_or_none()
    if not shop:
        raise NotFoundException("Boutique", str(id))

    if data.name is not None:
        shop.name = data.name.strip()
    if data.custom_domain is not None:
        shop.custom_domain = data.custom_domain.strip().lower() if data.custom_domain else None
    if data.accent_color is not None:
        shop.accent_color = data.accent_color
    if data.plan is not None:
        shop.plan = data.plan
    if data.status is not None:
        shop.status = data.status
    if data.is_active is not None:
        shop.is_active = data.is_active

    await db.commit()
    await db.refresh(shop)

    stmt_full = (
        select(Shop)
        .options(selectinload(Shop.customization), selectinload(Shop.products), selectinload(Shop.orders))
        .where(Shop.id == id)
    )
    res_full = await db.execute(stmt_full)
    s = res_full.scalar_one()

    return StandardResponse(
        message="Boutique mise à jour avec succès.",
        data=ShopResponse(
            id=s.id,
            name=s.name,
            slug=s.slug,
            domain=s.domain,
            custom_domain=s.custom_domain,
            plan=s.plan,
            orders_count=len(s.orders),
            max_orders=s.max_orders,
            status=s.status,
            is_active=s.is_active,
            accent_color=s.accent_color,
            products_count=len([p for p in s.products if not p.is_deleted]),
            orders_count_7d=0,
            template_id=s.customization.template_id if s.customization else "aura_eclat",
            template_name="Kolix Essentiel",
            logo_url=s.customization.logo_url if s.customization else None
        )
    )

@router.get("/{id}/products", response_model=StandardResponse[List[ProductResponse]])
async def list_store_products(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Liste tous les produits appartenant à une boutique spécifique."""
    stmt = (
        select(Product)
        .options(selectinload(Product.shop))
        .where(Product.shop_id == id, Product.is_deleted == False)
        .order_by(Product.created_at.desc())
    )
    res = await db.execute(stmt)
    products = res.scalars().all()
    results = []
    for p in products:
        item = ProductResponse.model_validate(p)
        if p.shop:
            item.shop_name = p.shop.name
            item.shop_domain = p.shop.domain
        results.append(item)
    return StandardResponse(data=results)

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
    if data.logo_url is not None:
        custom.logo_url = data.logo_url
    if data.banner_url is not None:
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


