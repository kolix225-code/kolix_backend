# app/services/order_service.py
import random
import uuid
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import BadRequestException, NotFoundException
from app.models.client import Client
from app.models.inventory import InventoryItem
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.shop import Shop
from app.schemas.order import PublicCheckoutRequest

class OrderService:
    @staticmethod
    async def create_public_cod_order(db: AsyncSession, data: PublicCheckoutRequest) -> Order:
        from sqlalchemy import or_

        shop = None
        # 1. Par shop_id direct si fourni
        if data.shop_id:
            s_res = await db.execute(select(Shop).where(Shop.id == data.shop_id, Shop.is_deleted == False))
            shop = s_res.scalar_one_or_none()

        # 2. Par slug ou domaine de la boutique
        if not shop and data.shop_domain_or_slug:
            stmt_shop = select(Shop).where(
                (Shop.slug == data.shop_domain_or_slug) |
                (Shop.domain == data.shop_domain_or_slug) |
                (Shop.custom_domain == data.shop_domain_or_slug),
                Shop.is_deleted == False
            )
            shop_res = await db.execute(stmt_shop)
            shop = shop_res.scalar_one_or_none()

        # 3. Par correspondance du produit (produit_id ou nom)
        if not shop and (data.product_id or data.product_name):
            p_cond = []
            if data.product_id:
                p_cond.append(Product.id == data.product_id)
            if data.product_name:
                p_clean = data.product_name.split('(')[0].strip()
                p_cond.append(Product.name.ilike(f"%{p_clean[:12]}%"))
            p_res = await db.execute(select(Product).where(or_(*p_cond), Product.is_deleted == False))
            matched_prod_shop = p_res.scalars().first()
            if matched_prod_shop:
                s_res = await db.execute(select(Shop).where(Shop.id == matched_prod_shop.shop_id, Shop.is_deleted == False))
                shop = s_res.scalar_one_or_none()

        # 4. Repli sur la boutique la plus récente
        if not shop:
            stmt_fallback = select(Shop).where(Shop.is_deleted == False).order_by(Shop.created_at.desc()).limit(1)
            fb_res = await db.execute(stmt_fallback)
            shop = fb_res.scalar_one_or_none()
            if not shop:
                raise NotFoundException("Boutique", data.shop_domain_or_slug or "principale")

        client_name = data.client_name or (data.customer.name if data.customer else "Client")
        client_phone = data.client_phone or (data.customer.phone if data.customer else "")
        city = data.city or (data.customer.city if data.customer else "Abidjan")
        delivery_place = data.delivery_place or (data.customer.address if data.customer else "Abidjan")
        product_name = data.product_name or "BlendGo – Mixeur portable 400 ml"
        offer_label = data.offer or data.pack_or_variant or "1 mixeur"
        quantity = data.quantity or 1
        amount = data.amount or data.total or 15900.0
        payment_mode = "COD_CASH" if data.payment_mode in ["COD_CASH", "cash_on_delivery"] else "COD_MOMO"

        # Generate unique human-readable order ID: KX-XXXX
        order_id = f"KX-{random.randint(1000, 9999)}"
        # Check collision
        while (await db.execute(select(Order).where(Order.id == order_id))).scalar_one_or_none():
            order_id = f"KX-{random.randint(1000, 9999)}"

        new_order = Order(
            id=order_id,
            shop_id=shop.id,
            client_name=client_name,
            client_phone=client_phone,
            city=city,
            delivery_place=delivery_place,
            total_amount=amount,
            status="En cours",
            payment_mode=payment_mode,
            note=data.note,
            offer_label=offer_label,
            quantity=quantity,
            qr_payload=None
        )
        db.add(new_order)

        # Create OrderItem
        item = OrderItem(
            order_id=order_id,
            product_name=product_name,
            variant_label=offer_label,
            quantity=quantity,
            unit_price=amount
        )
        db.add(item)

        # Décrémenter le stock du produit si trouvé
        p_clean = product_name.split('(')[0].strip()
        stmt_p = select(Product).where(
            Product.shop_id == shop.id,
            Product.name.ilike(f"%{p_clean[:12]}%"),
            Product.is_deleted == False
        )
        p_res = await db.execute(stmt_p)
        matched_prod = p_res.scalars().first()
        if matched_prod and matched_prod.stock_quantity >= quantity:
            matched_prod.stock_quantity = max(0, matched_prod.stock_quantity - quantity)
            stmt_inv = select(InventoryItem).where(
                InventoryItem.product_id == matched_prod.id,
                InventoryItem.shop_id == shop.id
            )
            inv_res = await db.execute(stmt_inv)
            inv_item = inv_res.scalar_one_or_none()
            if inv_item:
                inv_item.qty_remaining = matched_prod.stock_quantity
                inv_item.qty_sold += quantity

        # Update Shop total orders
        shop.orders_count += 1

        # Upsert Client in CRM
        stmt_client = select(Client).where(Client.shop_id == shop.id, Client.phone == client_phone)
        cl_res = await db.execute(stmt_client)
        client = cl_res.scalar_one_or_none()

        decimal_amount = Decimal(str(amount))
        now = datetime.now(timezone.utc)
        if client:
            client.total_orders += 1
            client.total_spent = Decimal(str(client.total_spent)) + decimal_amount
            client.last_order_date = now
            client.city = city
            client.place = delivery_place
        else:
            client = Client(
                shop_id=shop.id,
                name=client_name,
                phone=client_phone,
                city=city,
                place=delivery_place,
                total_orders=1,
                total_spent=decimal_amount,
                delivery_success_rate=100.0,
                last_order_date=now
            )
            db.add(client)

        await db.commit()
        await db.refresh(new_order)
        return new_order

