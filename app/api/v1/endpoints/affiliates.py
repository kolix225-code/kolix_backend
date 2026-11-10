# app/api/v1/endpoints/affiliates.py
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_shop, get_current_user
from app.core.exceptions import BadRequestException, NotFoundException
from app.models.affiliate import Affiliate, AffiliatePayout, AffiliateReferral
from app.models.shop import Shop
from app.models.user import User
from app.models.wallet import Wallet, WalletTransaction
from app.schemas.affiliate import (
    AffiliateReferralResponse,
    AffiliateSummaryResponse,
    TransferCommissionRequest,
)
from app.schemas.common import StandardResponse

router = APIRouter(prefix="/affiliates", tags=["Affiliation & Partenaires"])

@router.get("/summary", response_model=StandardResponse[AffiliateSummaryResponse])
async def get_affiliate_summary(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Synthèse des gains d'affiliation, lien de parrainage et code promo."""
    stmt = select(Affiliate).where(Affiliate.user_id == current_user.id)
    res = await db.execute(stmt)
    aff = res.scalar_one_or_none()

    if not aff:
        aff = Affiliate(
            user_id=current_user.id,
            affiliate_code=f"KX{current_user.full_name[:3].upper()}10",
            affiliate_slug=current_user.full_name.lower().replace(" ", "")[:15],
            available_balance=145000.0,
            total_earned=536000.0
        )
        db.add(aff)
        await db.commit()
        await db.refresh(aff)

    # Referrals
    stmt_ref = select(AffiliateReferral).where(AffiliateReferral.affiliate_id == aff.id)
    r_res = await db.execute(stmt_ref)
    referrals = r_res.scalars().all()

    return StandardResponse(
        data=AffiliateSummaryResponse(
            affiliate_code=aff.affiliate_code,
            affiliate_slug=aff.affiliate_slug,
            affiliate_link=f"kolix.app/r/{aff.affiliate_slug}",
            available_balance=float(aff.available_balance),
            total_earned=float(aff.total_earned),
            is_locked=aff.is_locked,
            lock_reason=aff.lock_reason or "Programme sur invitation / Accès restreint",
            monthly_gains=[
                {"month": "Mai", "amount": 45000},
                {"month": "Juin", "amount": 62000},
                {"month": "Juil.", "amount": 78000},
                {"month": "Août", "amount": 94000},
                {"month": "Sept.", "amount": 112000},
                {"month": "Oct.", "amount": 145000},
            ],
            referrals=[AffiliateReferralResponse.model_validate(r) for r in referrals]
        )
    )

@router.post("/transfer", response_model=StandardResponse[dict])
async def transfer_commissions(
    data: TransferCommissionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Transférer instantanément ses gains d'affiliation vers son portefeuille marchand."""
    stmt = select(Affiliate).where(Affiliate.user_id == current_user.id)
    res = await db.execute(stmt)
    aff = res.scalar_one_or_none()
    if not aff or aff.available_balance < data.amount:
        raise BadRequestException("Solde de commissions insuffisant pour ce transfert.")

    if aff.is_locked:
        raise BadRequestException(f"L'espace partenaire est verrouillé ({aff.lock_reason or 'Accès restreint'}). Transfert impossible.")

    aff.available_balance -= data.amount

    # Credit shop wallet
    stmt_w = select(Wallet).where(Wallet.shop_id == shop.id)
    w_res = await db.execute(stmt_w)
    wallet = w_res.scalar_one_or_none()
    if wallet:
        wallet.digital_balance += data.amount
        tx = WalletTransaction(
            wallet_id=wallet.id,
            ref=f"AFF-{int(data.amount)}",
            who="Transfert Programme Partenaire",
            mode="Wave",
            status="Validé",
            amount=data.amount,
            is_credit=True,
            is_cash=False
        )
        db.add(tx)

    payout = AffiliatePayout(
        affiliate_id=aff.id,
        amount=data.amount,
        payout_type="Transfert Portefeuille",
        status="Validé"
    )
    db.add(payout)
    await db.commit()

    return StandardResponse(message=f"{int(data.amount):,} FCFA transférés vers votre portefeuille Kolix !".replace(",", " "))

