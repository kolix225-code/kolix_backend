# app/api/v1/endpoints/clients.py
import csv
import io
import uuid
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import PermissionChecker, get_current_shop
from app.models.client import Client
from app.models.order import Order
from app.models.shop import Shop
from app.schemas.client import ClientResponse
from app.schemas.common import StandardResponse

router = APIRouter(prefix="/clients", tags=["Clients & CRM COD"])

@router.get("", response_model=StandardResponse[List[ClientResponse]], dependencies=[Depends(PermissionChecker("Client"))])
async def list_clients(
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)],
    search: Optional[str] = Query(None)
):
    """
    Répertoire clients COD filtré sur le statut livré.
    Seuls les clients ayant au moins une commande livrée avec succès sont récupérés.
    """
    # 1. Récupérer les commandes avec le statut livré pour la boutique courante
    stmt_orders = (
        select(Order)
        .where(
            Order.shop_id == shop.id,
            Order.is_deleted == False,
            or_(
                Order.status.ilike("%livr%"),
                Order.status.ilike("%deliver%")
            )
        )
        .order_by(Order.created_at.desc())
    )

    if search:
        term = f"%{search}%"
        stmt_orders = stmt_orders.where(
            or_(
                Order.client_name.ilike(term),
                Order.client_phone.ilike(term),
                Order.city.ilike(term)
            )
        )

    res_orders = await db.execute(stmt_orders)
    delivered_orders = res_orders.scalars().all()

    # 2. Agréger les clients uniques à partir des commandes livrées
    client_agg = {}
    for o in delivered_orders:
        clean_phone = o.client_phone.strip()
        if not clean_phone:
            continue

        if clean_phone not in client_agg:
            client_agg[clean_phone] = {
                "id": None,
                "name": o.client_name.strip(),
                "phone": clean_phone,
                "city": o.city.strip() if o.city else "Abidjan",
                "place": o.delivery_place.strip() if o.delivery_place else "Lieu habituel",
                "total_orders": 0,
                "total_spent": 0.0,
                "delivery_success_rate": 100.0,
                "last_order_date": o.created_at
            }

        client_agg[clean_phone]["total_orders"] += 1
        client_agg[clean_phone]["total_spent"] += float(o.total_amount or 0.0)
        if o.created_at and (client_agg[clean_phone]["last_order_date"] is None or o.created_at > client_agg[clean_phone]["last_order_date"]):
            client_agg[clean_phone]["last_order_date"] = o.created_at

    # 3. Lier avec les enregistrements éventuels de la table clients
    stmt_clients = select(Client).where(Client.shop_id == shop.id)
    res_c = await db.execute(stmt_clients)
    db_clients = {c.phone.strip(): c for c in res_c.scalars().all()}

    for phone, c_data in client_agg.items():
        if phone in db_clients:
            c_data["id"] = db_clients[phone].id

    # 4. Trier par nombre de commandes livrées décroissant
    sorted_clients = sorted(client_agg.values(), key=lambda x: (x["total_orders"], x["total_spent"]), reverse=True)

    result = [
        ClientResponse(
            id=c["id"] or uuid.uuid5(uuid.NAMESPACE_DNS, f"{shop.id}_{c['phone']}"),
            shop_id=shop.id,
            name=c["name"],
            phone=c["phone"],
            city=c["city"],
            place=c["place"],
            total_orders=c["total_orders"],
            total_spent=round(c["total_spent"], 2),
            delivery_success_rate=c["delivery_success_rate"],
            last_order_date=c["last_order_date"]
        )
        for c in sorted_clients
    ]

    return StandardResponse(data=result)

@router.get("/export", dependencies=[Depends(PermissionChecker("Client"))])
async def export_clients(
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Télécharger le répertoire des clients livrés sous format CSV."""
    stmt_orders = (
        select(Order)
        .where(
            Order.shop_id == shop.id,
            Order.is_deleted == False,
            or_(
                Order.status.ilike("%livr%"),
                Order.status.ilike("%deliver%")
            )
        )
        .order_by(Order.created_at.desc())
    )
    res_orders = await db.execute(stmt_orders)
    delivered_orders = res_orders.scalars().all()

    client_agg = {}
    for o in delivered_orders:
        clean_phone = o.client_phone.strip()
        if not clean_phone:
            continue
        if clean_phone not in client_agg:
            client_agg[clean_phone] = {
                "name": o.client_name.strip(),
                "phone": clean_phone,
                "city": o.city.strip() if o.city else "Abidjan",
                "place": o.delivery_place.strip() if o.delivery_place else "Lieu habituel",
                "total_orders": 0,
                "total_spent": 0.0,
            }
        client_agg[clean_phone]["total_orders"] += 1
        client_agg[clean_phone]["total_spent"] += float(o.total_amount or 0.0)

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(["Nom", "Telephone", "Commune", "Lieu_Habituel", "Commandes_Livrees", "Total_Depense_FCFA", "Score_Livraison"])

    for c in sorted(client_agg.values(), key=lambda x: x["total_orders"], reverse=True):
        writer.writerow([c["name"], c["phone"], c["city"], c["place"], c["total_orders"], f"{int(c['total_spent'])} FCFA", "100%"])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=clients_livres_{shop.slug}.csv"}
    )
