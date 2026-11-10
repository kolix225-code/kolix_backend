# app/api/v1/endpoints/accounting.py
from datetime import date
from typing import Annotated, List
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import PermissionChecker, get_current_shop
from app.models.accounting import Charge
from app.models.order import Order
from app.models.shop import Shop
from app.schemas.accounting import (
    AccountingDashboardResponse,
    ChargeCreate,
    ChargeResponse,
)
from app.schemas.common import StandardResponse

router = APIRouter(prefix="/accounting", tags=["Comptabilité Analytique"])

@router.get("/dashboard", response_model=StandardResponse[AccountingDashboardResponse], dependencies=[Depends(PermissionChecker("Comptabilité"))])
async def get_accounting_dashboard(
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Tableau de bord comptable (CA consolidé, charges par catégorie, résultat net)."""
    # Total revenue from delivered orders
    stmt_rev = select(func.sum(Order.total_amount)).where(Order.shop_id == shop.id, Order.status == "Livrée")
    rev_res = await db.execute(stmt_rev)
    total_rev = float(rev_res.scalar_one_or_none() or 0.0)

    # Charges by category
    stmt_charges = select(Charge.category, func.sum(Charge.amount)).where(Charge.shop_id == shop.id).group_by(Charge.category)
    c_res = await db.execute(stmt_charges)
    cat_dict = {cat: float(amt) for cat, amt in c_res.all()}

    # Ensure all standard categories exist in dictionary
    for standard_cat in ["Achat de stock", "Transport et livraison", "Publicité", "Abonnement Kolix", "Autres"]:
        cat_dict.setdefault(standard_cat, 0.0)

    total_charges = sum(cat_dict.values())
    net_profit = total_rev - total_charges
    margin_pct = (net_profit / total_rev * 100) if total_rev > 0 else 0.0

    return StandardResponse(
        data=AccountingDashboardResponse(
            period="Mois en cours",
            total_revenue=total_rev,
            total_charges=total_charges,
            net_profit=net_profit,
            margin_percentage=round(margin_pct, 1),
            charges_by_category=cat_dict,
            recent_transactions=[]
        )
    )

@router.get("/charges", response_model=StandardResponse[List[ChargeResponse]], dependencies=[Depends(PermissionChecker("Comptabilité"))])
async def list_charges(
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Liste des charges et dépenses enregistrées."""
    stmt = select(Charge).where(Charge.shop_id == shop.id).order_by(Charge.date.desc())
    res = await db.execute(stmt)
    charges = res.scalars().all()
    return StandardResponse(data=[ChargeResponse.model_validate(c) for c in charges])

@router.post("/charges", response_model=StandardResponse[ChargeResponse], dependencies=[Depends(PermissionChecker("Comptabilité"))])
async def add_charge(
    data: ChargeCreate,
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Enregistrer une nouvelle charge comptable."""
    charge = Charge(
        shop_id=shop.id,
        date=data.date,
        label=data.label,
        category=data.category,
        payment_mode=data.payment_mode,
        amount=data.amount
    )
    db.add(charge)
    await db.commit()
    await db.refresh(charge)
    return StandardResponse(message="Charge enregistrée avec succès.", data=ChargeResponse.model_validate(charge))

