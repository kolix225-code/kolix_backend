# app/api/v1/endpoints/clients.py
import csv
import io
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import PermissionChecker, get_current_shop
from app.models.client import Client
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
    """Répertoire clients COD avec historique et score de livraison."""
    stmt = select(Client).where(Client.shop_id == shop.id)
    if search:
        term = f"%{search}%"
        stmt = stmt.where(
            or_(
                Client.name.ilike(term),
                Client.phone.ilike(term),
                Client.city.ilike(term)
            )
        )
    stmt = stmt.order_by(Client.total_orders.desc())
    res = await db.execute(stmt)
    clients = res.scalars().all()
    return StandardResponse(data=[ClientResponse.model_validate(c) for c in clients])

@router.get("/export", dependencies=[Depends(PermissionChecker("Client"))])
async def export_clients(
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Télécharger le répertoire clients sous format CSV pour remarketing."""
    stmt = select(Client).where(Client.shop_id == shop.id).order_by(Client.total_spent.desc())
    res = await db.execute(stmt)
    clients = res.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(["Nom", "Telephone", "Commune", "Lieu_Habituel", "Commandes", "Total_Depense_FCFA", "Score_Livraison"])

    for c in clients:
        writer.writerow([c.name, c.phone, c.city, c.place, c.total_orders, c.total_spent, f"{c.delivery_success_rate}%"])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=clients_{shop.slug}.csv"}
    )

