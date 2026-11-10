# app/api/v1/endpoints/orders.py
import csv
import io
import uuid
from datetime import datetime, timezone
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.dependencies import PermissionChecker, get_current_shop
from app.core.exceptions import NotFoundException
from app.models.inventory import InventoryItem
from app.models.order import Order
from app.models.shop import Shop
from app.models.wallet import Wallet, WalletTransaction
from app.schemas.common import StandardResponse
from app.schemas.order import (
    OrderAssignDeliveryRequest,
    OrderItemSchema,
    OrderResponse,
    OrderUpdateStatusRequest,
)

router = APIRouter(prefix="/orders", tags=["Commandes COD"])

@router.get("", response_model=StandardResponse[List[OrderResponse]], dependencies=[Depends(PermissionChecker("Commandes"))])
async def list_orders(
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None)
):
    """Recherche et liste filtrée des commandes COD."""
    stmt = (
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.shop_id == shop.id, Order.is_deleted == False)
    )

    if status_filter and status_filter != "all":
        stmt = stmt.where(Order.status == status_filter)

    if search:
        term = f"%{search}%"
        stmt = stmt.where(
            or_(
                Order.id.ilike(term),
                Order.client_name.ilike(term),
                Order.client_phone.ilike(term),
                Order.city.ilike(term),
                Order.delivery_place.ilike(term),
            )
        )

    stmt = stmt.order_by(Order.created_at.desc())
    res = await db.execute(stmt)
    orders = res.scalars().all()

    response_items = []
    for o in orders:
        resp = OrderResponse(
            id=o.id,
            shop_id=o.shop_id,
            client_name=o.client_name,
            client_phone=o.client_phone,
            city=o.city,
            delivery_place=o.delivery_place,
            total_amount=float(o.total_amount),
            status=o.status,
            payment_mode=o.payment_mode,
            paid_at=o.paid_at,
            note=o.note,
            offer_label=o.offer_label,
            quantity=o.quantity,
            qr_payload=o.qr_payload,
            assigned_delivery_id=o.assigned_delivery_id,
            created_at=o.created_at,
            items=[
                OrderItemSchema(
                    product_id=it.product_id,
                    product_name=it.product_name,
                    variant_label=it.variant_label,
                    quantity=it.quantity,
                    unit_price=float(it.unit_price)
                ) for it in o.items
            ]
        )
        response_items.append(resp)

    return StandardResponse(data=response_items)

@router.get("/{id}", response_model=StandardResponse[OrderResponse], dependencies=[Depends(PermissionChecker("Commandes"))])
async def get_order(
    id: str,
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Fiche détaillée d'une commande COD."""
    stmt = select(Order).options(selectinload(Order.items)).where(Order.id == id, Order.shop_id == shop.id)
    res = await db.execute(stmt)
    o = res.scalar_one_or_none()
    if not o:
        raise NotFoundException("Commande", id)

    return StandardResponse(
        data=OrderResponse(
            id=o.id,
            shop_id=o.shop_id,
            client_name=o.client_name,
            client_phone=o.client_phone,
            city=o.city,
            delivery_place=o.delivery_place,
            total_amount=float(o.total_amount),
            status=o.status,
            payment_mode=o.payment_mode,
            paid_at=o.paid_at,
            note=o.note,
            offer_label=o.offer_label,
            quantity=o.quantity,
            qr_payload=o.qr_payload,
            assigned_delivery_id=o.assigned_delivery_id,
            created_at=o.created_at,
            items=[
                OrderItemSchema(
                    product_id=it.product_id,
                    product_name=it.product_name,
                    variant_label=it.variant_label,
                    quantity=it.quantity,
                    unit_price=float(it.unit_price)
                ) for it in o.items
            ]
        )
    )

@router.patch("/{id}/status", response_model=StandardResponse[dict], dependencies=[Depends(PermissionChecker("Commandes"))])
async def update_order_status(
    id: str,
    data: OrderUpdateStatusRequest,
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Changement d'état d'une commande (Livrée, Reportée, Annulée, Contestée, Injoignable)."""
    stmt = select(Order).options(selectinload(Order.items)).where(Order.id == id, Order.shop_id == shop.id)
    res = await db.execute(stmt)
    order = res.scalar_one_or_none()
    if not order:
        raise NotFoundException("Commande", id)

    old_status = order.status
    order.status = data.status

    # If transitioned to Livrée, mark payment and credit cash/momo
    if data.status == "Livrée" and old_status != "Livrée":
        order.paid_at = datetime.now(timezone.utc)
        # Credit wallet
        stmt_w = select(Wallet).where(Wallet.shop_id == shop.id)
        w_res = await db.execute(stmt_w)
        wallet = w_res.scalar_one_or_none()
        if wallet:
            if order.payment_mode == "COD_CASH":
                wallet.cash_balance += float(order.total_amount)
            else:
                wallet.digital_balance += float(order.total_amount)

            trx = WalletTransaction(
                wallet_id=wallet.id,
                ref=f"PAY-{order.id}",
                who=order.client_name,
                mode="Espèces" if order.payment_mode == "COD_CASH" else "Mobile Money",
                status="Validé",
                amount=order.total_amount,
                is_credit=True,
                is_cash=(order.payment_mode == "COD_CASH"),
                order_id=order.id
            )
            db.add(trx)

    await db.commit()
    return StandardResponse(message=f"Commande {order.id} passée au statut '{data.status}'.", data={"id": order.id, "status": order.status})

@router.post("/{id}/assign", response_model=StandardResponse[dict], dependencies=[Depends(PermissionChecker("Commandes"))])
async def assign_delivery(
    id: str,
    data: OrderAssignDeliveryRequest,
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Assigner un livreur à une commande."""
    stmt = select(Order).where(Order.id == id, Order.shop_id == shop.id)
    res = await db.execute(stmt)
    order = res.scalar_one_or_none()
    if not order:
        raise NotFoundException("Commande", id)

    order.assigned_delivery_id = data.collaborator_id
    await db.commit()
    return StandardResponse(message=f"Livreur assigné à la commande {order.id}.")

@router.get("/export/csv", dependencies=[Depends(PermissionChecker("Commandes"))])
async def export_orders_csv(
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Exportation du fichier CSV des commandes."""
    stmt = select(Order).where(Order.shop_id == shop.id).order_by(Order.created_at.desc())
    res = await db.execute(stmt)
    orders = res.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(["ID", "Client", "Telephone", "Commune", "Lieu", "Montant_FCFA", "Statut", "Mode_Paiement", "Date"])

    for o in orders:
        writer.writerow([
            o.id,
            o.client_name,
            o.client_phone,
            o.city,
            o.delivery_place,
            o.total_amount,
            o.status,
            o.payment_mode,
            o.created_at.strftime("%Y-%m-%d %H:%M")
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=commandes_{shop.slug}.csv"}
    )

