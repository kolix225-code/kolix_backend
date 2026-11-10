# app/api/v1/endpoints/wallet.py
import random
import uuid
from typing import Annotated, List
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import PermissionChecker, get_current_shop
from app.core.exceptions import BadRequestException, NotFoundException
from app.models.shop import Shop
from app.models.wallet import PayoutAccount, Wallet, WalletTransaction
from app.schemas.common import StandardResponse
from app.schemas.wallet import (
    PayoutAccountCreate,
    PayoutAccountResponse,
    WalletSummaryResponse,
    WalletTransactionResponse,
    WithdrawRequest,
)

router = APIRouter(prefix="/wallet", tags=["Portefeuille & Retraits"])

@router.get("/summary", response_model=StandardResponse[WalletSummaryResponse], dependencies=[Depends(PermissionChecker("Portefeuille"))])
async def get_wallet_summary(
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Soldes du portefeuille (Digital Mobile Money, Espèces livreurs, Commissions)."""
    stmt = select(Wallet).where(Wallet.shop_id == shop.id)
    res = await db.execute(stmt)
    wallet = res.scalar_one_or_none()
    if not wallet:
        wallet = Wallet(shop_id=shop.id)
        db.add(wallet)
        await db.commit()
        await db.refresh(wallet)

    return StandardResponse(
        data=WalletSummaryResponse(
            digital_balance=float(wallet.digital_balance),
            cash_balance=float(wallet.cash_balance),
            pending_balance=float(wallet.pending_balance),
            withdrawn_this_month=float(wallet.withdrawn_month),
            kolix_commission=float(wallet.kolix_commission),
            avg_transfer_time="24 min",
            is_digital_locked=wallet.is_digital_locked,
            digital_lock_reason=wallet.digital_lock_reason
        )
    )

@router.get("/transactions", response_model=StandardResponse[List[WalletTransactionResponse]], dependencies=[Depends(PermissionChecker("Portefeuille"))])
async def list_transactions(
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Relevé des transactions du portefeuille (crédits COD et retraits)."""
    stmt = (
        select(WalletTransaction)
        .join(Wallet, WalletTransaction.wallet_id == Wallet.id)
        .where(Wallet.shop_id == shop.id)
        .order_by(WalletTransaction.created_at.desc())
    )
    res = await db.execute(stmt)
    txs = res.scalars().all()

    return StandardResponse(
        data=[
            WalletTransactionResponse(
                id=t.id,
                ref=t.ref,
                who=t.who,
                mode=t.mode,
                status=t.status,
                amount=float(t.amount),
                is_credit=t.is_credit,
                is_cash=t.is_cash,
                order_id=t.order_id,
                created_at=t.created_at
            ) for t in txs
        ]
    )

@router.get("/accounts", response_model=StandardResponse[List[PayoutAccountResponse]], dependencies=[Depends(PermissionChecker("Portefeuille"))])
async def list_payout_accounts(
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Comptes de retrait Mobile Money enregistrés (Wave, Orange, MTN)."""
    stmt = (
        select(PayoutAccount)
        .join(Wallet, PayoutAccount.wallet_id == Wallet.id)
        .where(Wallet.shop_id == shop.id, PayoutAccount.is_deleted == False)
    )
    res = await db.execute(stmt)
    accounts = res.scalars().all()
    return StandardResponse(data=[PayoutAccountResponse.model_validate(a) for a in accounts])

@router.post("/accounts", response_model=StandardResponse[PayoutAccountResponse], dependencies=[Depends(PermissionChecker("Portefeuille"))])
async def add_payout_account(
    data: PayoutAccountCreate,
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Lier un nouveau compte de retrait Mobile Money."""
    stmt = select(Wallet).where(Wallet.shop_id == shop.id)
    res = await db.execute(stmt)
    wallet = res.scalar_one_or_none()
    if not wallet:
        raise NotFoundException("Portefeuille")

    acc = PayoutAccount(
        wallet_id=wallet.id,
        name=data.name,
        num=data.num,
        provider=data.provider,
        is_default=data.is_default
    )
    db.add(acc)
    await db.commit()
    await db.refresh(acc)
    return StandardResponse(message="Compte de retrait ajouté avec succès.", data=PayoutAccountResponse.model_validate(acc))

@router.post("/withdraw", response_model=StandardResponse[dict], dependencies=[Depends(PermissionChecker("Portefeuille"))])
async def withdraw(
    data: WithdrawRequest,
    shop: Annotated[Shop, Depends(get_current_shop)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Demande de virement instantané vers son compte Mobile Money."""
    stmt = select(Wallet).where(Wallet.shop_id == shop.id)
    res = await db.execute(stmt)
    wallet = res.scalar_one_or_none()
    if not wallet:
        raise NotFoundException("Portefeuille")

    if wallet.is_digital_locked:
        raise BadRequestException(f"Le portefeuille numérique est verrouillé ({wallet.digital_lock_reason or 'Vérification requise'}). Retrait temporairement désactivé.")

    if wallet.digital_balance < data.amount:
        raise BadRequestException("Solde digital insuffisant pour effectuer ce retrait.")

    wallet.digital_balance -= data.amount
    wallet.withdrawn_month += data.amount

    ref = f"WDR-{random.randint(1000, 9999)}"
    tx = WalletTransaction(
        wallet_id=wallet.id,
        ref=ref,
        who=f"Retrait vers Mobile Money",
        mode="Wave",
        status="Validé",
        amount=data.amount,
        is_credit=False,
        is_cash=False
    )
    db.add(tx)
    await db.commit()
    return StandardResponse(message=f"Retrait de {int(data.amount)} FCFA effectué avec succès !", data={"ref": ref, "amount": data.amount})

