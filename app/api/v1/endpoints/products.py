# app/api/v1/endpoints/products.py
import uuid
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.dependencies import PermissionChecker, get_current_shop
from app.core.exceptions import NotFoundException
from app.models.inventory import InventoryItem
from app.models.product import Product
from app.models.shop import Shop
from app.schemas.common import StandardResponse
from app.schemas.product import BulkStatusRequest, ProductCreate, ProductResponse, ProductUpdate

router = APIRouter(prefix="/products", tags=["Produits & Catalogue"])

@router.get("", response_model=StandardResponse[List[ProductResponse]])
async def list_products(
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)],
    category: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    shop_id: Optional[uuid.UUID] = Query(None)
):
    """Liste tous les produits du catalogue avec filtres facultatifs."""
    target_shop_id = shop_id if shop_id else shop.id
    stmt = (
        select(Product)
        .options(selectinload(Product.shop))
        .where(Product.shop_id == target_shop_id, Product.is_deleted == False)
    )
    if category and category != "all":
        stmt = stmt.where(Product.category == category)
    if status_filter and status_filter != "all":
        stmt = stmt.where(Product.status == status_filter)

    stmt = stmt.order_by(Product.created_at.desc())
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

@router.post("", response_model=StandardResponse[ProductResponse], dependencies=[Depends(PermissionChecker("Produits"))])
async def create_product(
    data: ProductCreate,
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Créer un nouveau produit COD et initialiser sa fiche de stock associée."""
    target_shop_id = data.shop_id if data.shop_id else shop.id
    unique_suffix = str(uuid.uuid4())[:6]
    base_slug = data.name.lower().replace(" ", "-")[:32]
    slug = f"{base_slug}-{unique_suffix}"
    prod = Product(
        shop_id=target_shop_id,
        name=data.name,
        slug=slug,
        category=data.category,
        product_type=data.product_type,
        price=data.price,
        price_old=data.price_old,
        stock_quantity=data.stock_quantity,
        stock_main=data.stock_main,
        stock_rest=data.stock_rest,
        status="Actif",
        has_countdown=data.has_countdown,
        description=data.description,
        images=data.images,
        fiche_produit=data.fiche_produit
    )
    db.add(prod)
    await db.flush()

    # Create associated inventory item
    sku = f"PRD-{str(uuid.uuid4())[:4].upper()}"
    inv = InventoryItem(
        shop_id=target_shop_id,
        product_id=prod.id,
        num=sku,
        qty_initial=data.stock_quantity,
        qty_sold=0,
        qty_remaining=data.stock_quantity,
        threshold=5,
        unit_cost=data.price * 0.45,
        status="Optimal" if data.stock_quantity > 5 else "Faible"
    )
    db.add(inv)

    await db.commit()
    await db.refresh(prod)
    return StandardResponse(message="Produit ajouté avec succès.", data=ProductResponse.model_validate(prod))

@router.get("/{id}", response_model=StandardResponse[ProductResponse])
async def get_product(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Détails d'un produit avec images et caractéristiques."""
    stmt = select(Product).options(selectinload(Product.shop)).where(Product.id == id, Product.is_deleted == False)
    res = await db.execute(stmt)
    prod = res.scalar_one_or_none()
    if not prod:
        raise NotFoundException("Produit", str(id))
    resp = ProductResponse.model_validate(prod)
    if prod.shop:
        resp.shop_name = prod.shop.name
        resp.shop_domain = prod.shop.domain
    return StandardResponse(data=resp)

@router.put("/{id}", response_model=StandardResponse[ProductResponse], dependencies=[Depends(PermissionChecker("Produits"))])
async def update_product(
    id: uuid.UUID,
    data: ProductUpdate,
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Modifier les attributs d'un produit."""
    stmt = (
        select(Product)
        .join(Shop, Product.shop_id == Shop.id)
        .where(
            Product.id == id,
            (Product.shop_id == shop.id) | (Shop.owner_id == shop.owner_id),
            Product.is_deleted == False
        )
    )
    res = await db.execute(stmt)
    prod = res.scalar_one_or_none()
    if not prod:
        raise NotFoundException("Produit", str(id))

    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(prod, key, val)

    await db.commit()
    await db.refresh(prod)
    return StandardResponse(message="Produit mis à jour.", data=ProductResponse.model_validate(prod))

@router.delete("/{id}", response_model=StandardResponse[None], dependencies=[Depends(PermissionChecker("Produits"))])
async def delete_product(
    id: uuid.UUID,
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Archiver un produit."""
    stmt = (
        select(Product)
        .join(Shop, Product.shop_id == Shop.id)
        .where(
            Product.id == id,
            (Product.shop_id == shop.id) | (Shop.owner_id == shop.owner_id)
        )
    )
    res = await db.execute(stmt)
    prod = res.scalar_one_or_none()
    if not prod:
        raise NotFoundException("Produit", str(id))

    prod.is_deleted = True
    prod.status = "Archivé"
    await db.commit()
    return StandardResponse(message="Produit archivé.")

@router.post("/bulk-status", response_model=StandardResponse[None], dependencies=[Depends(PermissionChecker("Produits"))])
async def bulk_status(
    data: BulkStatusRequest,
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Modifier le statut d'un lot de produits en un clic."""
    stmt = select(Product).where(Product.id.in_(data.product_ids), Product.shop_id == shop.id)
    res = await db.execute(stmt)
    products = res.scalars().all()
    for p in products:
        p.status = data.new_status
    await db.commit()
    return StandardResponse(message=f"{len(products)} produits passés au statut '{data.new_status}'.")

