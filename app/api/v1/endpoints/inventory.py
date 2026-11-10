# app/api/v1/endpoints/inventory.py
import uuid
from typing import Annotated, List
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.dependencies import PermissionChecker, get_current_shop
from app.core.exceptions import NotFoundException
from app.models.inventory import InventoryItem, StockMovement
from app.models.product import Product
from app.models.shop import Shop
from app.schemas.common import StandardResponse
from app.schemas.inventory import (
    InventoryItemResponse,
    RestockRequest,
    StockKpisResponse,
    ThresholdUpdateRequest,
)

router = APIRouter(prefix="/inventory", tags=["Stock & Inventaire"])

@router.get("", response_model=StandardResponse[List[InventoryItemResponse]], dependencies=[Depends(PermissionChecker("Stock"))])
async def list_inventory(
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """État du stock avec statut optimal, faible ou rupture."""
    stmt = (
        select(InventoryItem)
        .options(selectinload(InventoryItem.product))
        .where(InventoryItem.shop_id == shop.id, InventoryItem.is_deleted == False)
    )
    res = await db.execute(stmt)
    items = res.scalars().all()

    resp = []
    for it in items:
        resp.append(
            InventoryItemResponse(
                id=it.id,
                shop_id=it.shop_id,
                product_id=it.product_id,
                product_name=it.product.name if it.product else "Produit",
                num=it.num,
                qty_initial=it.qty_initial,
                qty_sold=it.qty_sold,
                qty_remaining=it.qty_remaining,
                threshold=it.threshold,
                unit_cost=float(it.unit_cost),
                status=it.status
            )
        )
    return StandardResponse(data=resp)

@router.get("/kpis", response_model=StandardResponse[StockKpisResponse], dependencies=[Depends(PermissionChecker("Stock"))])
async def get_stock_kpis(
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Indicateurs clés du stock (valeur totale, alertes, rotation)."""
    stmt = select(InventoryItem).where(InventoryItem.shop_id == shop.id, InventoryItem.is_deleted == False)
    res = await db.execute(stmt)
    items = res.scalars().all()

    total_val = sum(float(it.unit_cost) * it.qty_remaining for it in items)
    under_thresh = sum(1 for it in items if it.qty_remaining <= it.threshold and it.qty_remaining > 0)
    out_of_stock = sum(1 for it in items if it.qty_remaining <= 0)

    return StandardResponse(
        data=StockKpisResponse(
            total_value=total_val,
            under_threshold_count=under_thresh,
            pending_restock_count=under_thresh + out_of_stock,
            turnover_rate="18.4j",
            out_of_stock_count=out_of_stock
        )
    )

@router.post("/{id}/restock", response_model=StandardResponse[InventoryItemResponse], dependencies=[Depends(PermissionChecker("Stock"))])
async def restock_product(
    id: uuid.UUID,
    data: RestockRequest,
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Enregistrer une entrée de réapprovisionnement de stock."""
    stmt = select(InventoryItem).options(selectinload(InventoryItem.product)).where(InventoryItem.id == id, InventoryItem.shop_id == shop.id)
    res = await db.execute(stmt)
    item = res.scalar_one_or_none()
    if not item:
        raise NotFoundException("Ligne de stock", str(id))

    item.qty_remaining += data.quantity
    item.qty_initial += data.quantity
    if data.unit_cost is not None:
        item.unit_cost = data.unit_cost

    # Update status
    if item.qty_remaining <= 0:
        item.status = "Rupture"
    elif item.qty_remaining <= item.threshold:
        item.status = "Critique" if item.qty_remaining <= 2 else "Faible"
    else:
        item.status = "Optimal"

    # Also update product stock quantity
    if item.product:
        item.product.stock_quantity = item.qty_remaining

    # Add movement log
    mvt = StockMovement(
        inventory_item_id=item.id,
        type="Entrée",
        quantity=data.quantity,
        note=data.note or "Réapprovisionnement fournisseur"
    )
    db.add(mvt)

    await db.commit()
    await db.refresh(item)
    return StandardResponse(
        message="Stock réapprovisionné avec succès.",
        data=InventoryItemResponse(
            id=item.id,
            shop_id=item.shop_id,
            product_id=item.product_id,
            product_name=item.product.name if item.product else "",
            num=item.num,
            qty_initial=item.qty_initial,
            qty_sold=item.qty_sold,
            qty_remaining=item.qty_remaining,
            threshold=item.threshold,
            unit_cost=float(item.unit_cost),
            status=item.status
        )
    )

@router.put("/{id}/threshold", response_model=StandardResponse[dict], dependencies=[Depends(PermissionChecker("Stock"))])
async def update_threshold(
    id: uuid.UUID,
    data: ThresholdUpdateRequest,
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Modifier le seuil d'alerte critique d'un article."""
    stmt = select(InventoryItem).where(InventoryItem.id == id, InventoryItem.shop_id == shop.id)
    res = await db.execute(stmt)
    item = res.scalar_one_or_none()
    if not item:
        raise NotFoundException("Ligne de stock", str(id))

    item.threshold = data.threshold
    await db.commit()
    return StandardResponse(message=f"Seuil d'alerte mis à jour à {data.threshold} unités.")

