"""Add fiche_produit JSONB column to products

Revision ID: f4a9b2c3d5e6
Revises: e3f8a4129b01
Create Date: 2026-11-09 11:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f4a9b2c3d5e6'
down_revision: Union[str, Sequence[str], None] = 'e3f8a4129b01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('products', sa.Column('fiche_produit', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column('products', 'fiche_produit')

