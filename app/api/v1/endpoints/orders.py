# app/api/v1/endpoints/orders.py
import csv
import io
import random
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.dependencies import PermissionChecker, get_current_shop
from app.core.exceptions import NotFoundException
from app.models.client import Client
from app.models.inventory import InventoryItem
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.shop import Shop
from app.models.wallet import Wallet, WalletTransaction
from app.schemas.common import StandardResponse
from app.schemas.order import (
    OrderAssignDeliveryRequest,
    OrderCreateRequest,
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

@router.post("", response_model=StandardResponse[OrderResponse], dependencies=[Depends(PermissionChecker("Commandes"))])
async def create_order(
    data: OrderCreateRequest,
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Créer manuellement une nouvelle commande depuis le tableau de bord marchand."""
    order_id = f"KX-{random.randint(1000, 9999)}"
    while (await db.execute(select(Order).where(Order.id == order_id))).scalar_one_or_none():
        order_id = f"KX-{random.randint(1000, 9999)}"

    new_order = Order(
        id=order_id,
        shop_id=shop.id,
        client_name=data.client_name.strip(),
        client_phone=data.client_phone.strip(),
        city=data.city.strip(),
        delivery_place=data.delivery_place.strip(),
        total_amount=data.amount,
        status=data.status or "En cours",
        payment_mode=data.payment_mode or "COD_CASH",
        note=data.note,
        offer_label=data.offer_label or data.product_name,
        quantity=data.quantity or 1,
        qr_payload=f"KOLIX-PAY:{order_id}:{int(data.amount)}:XOF:{data.client_name.strip().upper().replace(' ', '-')}"
    )
    db.add(new_order)

    # Order Item
    item = OrderItem(
        order_id=order_id,
        product_name=data.product_name,
        variant_label=data.offer_label or data.product_name,
        quantity=data.quantity or 1,
        unit_price=data.amount
    )
    db.add(item)

    # Décrémenter le stock produit si trouvé
    p_clean = data.product_name.split('(')[0].strip()
    stmt_prod = select(Product).where(
        Product.shop_id == shop.id,
        Product.name.ilike(f"%{p_clean[:12]}%"),
        Product.is_deleted == False
    )
    p_res = await db.execute(stmt_prod)
    matched_prod = p_res.scalars().first()
    if matched_prod and matched_prod.stock_quantity >= data.quantity:
        matched_prod.stock_quantity = max(0, matched_prod.stock_quantity - data.quantity)
        stmt_inv = select(InventoryItem).where(
            InventoryItem.product_id == matched_prod.id,
            InventoryItem.shop_id == shop.id
        )
        inv_res = await db.execute(stmt_inv)
        inv_item = inv_res.scalar_one_or_none()
        if inv_item:
            inv_item.qty_remaining = matched_prod.stock_quantity
            inv_item.qty_sold += data.quantity

    # Mettre à jour / Créer le client dans le CRM
    stmt_client = select(Client).where(Client.shop_id == shop.id, Client.phone == data.client_phone.strip())
    cl_res = await db.execute(stmt_client)
    client = cl_res.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    decimal_amount = Decimal(str(data.amount))
    if client:
        client.total_orders += 1
        client.total_spent = Decimal(str(client.total_spent)) + decimal_amount
        client.last_order_date = now
        client.city = data.city.strip()
        client.place = data.delivery_place.strip()
    else:
        client = Client(
            shop_id=shop.id,
            name=data.client_name.strip(),
            phone=data.client_phone.strip(),
            city=data.city.strip(),
            place=data.delivery_place.strip(),
            total_orders=1,
            total_spent=decimal_amount,
            delivery_success_rate=100.0,
            last_order_date=now
        )
        db.add(client)

    shop.orders_count += 1
    await db.commit()
    await db.refresh(new_order)

    return StandardResponse(
        message=f"Commande {new_order.id} enregistrée avec succès.",
        data=OrderResponse(
            id=new_order.id,
            shop_id=new_order.shop_id,
            client_name=new_order.client_name,
            client_phone=new_order.client_phone,
            city=new_order.city,
            delivery_place=new_order.delivery_place,
            total_amount=float(new_order.total_amount),
            status=new_order.status,
            payment_mode=new_order.payment_mode,
            paid_at=new_order.paid_at,
            note=new_order.note,
            offer_label=new_order.offer_label,
            quantity=new_order.quantity,
            qr_payload=new_order.qr_payload,
            created_at=new_order.created_at,
            items=[
                OrderItemSchema(
                    product_id=None,
                    product_name=item.product_name,
                    variant_label=item.variant_label,
                    quantity=item.quantity,
                    unit_price=float(item.unit_price)
                )
            ]
        )
    )

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

