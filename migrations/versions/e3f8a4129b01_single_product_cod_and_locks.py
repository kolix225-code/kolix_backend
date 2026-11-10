"""Single product COD and lock flags

Revision ID: e3f8a4129b01
Revises: 98782f91ba9a
Create Date: 2026-11-09 11:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e3f8a4129b01'
down_revision: Union[str, Sequence[str], None] = '98782f91ba9a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply schema updates for single product COD, lock flags on wallet and affiliate."""
    # 1. Orders: qr_payload becomes nullable, add offer_label and quantity
    op.alter_column('orders', 'qr_payload',
               existing_type=sa.String(length=255),
               nullable=True)
    op.add_column('orders', sa.Column('offer_label', sa.String(length=128), nullable=True))
    op.add_column('orders', sa.Column('quantity', sa.Integer(), server_default='1', nullable=False))

    # 2. Wallets: digital wallet lock flags
    op.add_column('wallets', sa.Column('is_digital_locked', sa.Boolean(), server_default=sa.text('true'), nullable=False))
    op.add_column('wallets', sa.Column('digital_lock_reason', sa.String(length=255), server_default='Vérification KYC requise', nullable=True))

    # 3. Affiliates: partner program lock flags
    op.add_column('affiliates', sa.Column('is_locked', sa.Boolean(), server_default=sa.text('true'), nullable=False))
    op.add_column('affiliates', sa.Column('lock_reason', sa.String(length=255), server_default='Programme sur invitation / Accès restreint', nullable=True))

    # 4. Store Customizations: single product page COD settings
    op.add_column('store_customizations', sa.Column('is_single_product_store', sa.Boolean(), server_default=sa.text('true'), nullable=False))
    op.add_column('store_customizations', sa.Column('stock_urgency_count', sa.Integer(), server_default='14', nullable=False))
    op.add_column('store_customizations', sa.Column('countdown_enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False))
    op.add_column('store_customizations', sa.Column('offer_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    """Revert schema updates."""
    # 4. Revert Store Customizations
    op.drop_column('store_customizations', 'offer_config')
    op.drop_column('store_customizations', 'countdown_enabled')
    op.drop_column('store_customizations', 'stock_urgency_count')
    op.drop_column('store_customizations', 'is_single_product_store')

    # 3. Revert Affiliates
    op.drop_column('affiliates', 'lock_reason')
    op.drop_column('affiliates', 'is_locked')

    # 2. Revert Wallets
    op.drop_column('wallets', 'digital_lock_reason')
    op.drop_column('wallets', 'is_digital_locked')

    # 1. Revert Orders
    op.drop_column('orders', 'quantity')
    op.drop_column('orders', 'offer_label')
    op.alter_column('orders', 'qr_payload',
               existing_type=sa.String(length=255),
               nullable=False)

