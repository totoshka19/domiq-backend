"""add_reject_reason_to_listings

Revision ID: a1b2c3d4e5f6
Revises: c51c74a40e02
Create Date: 2026-04-07

"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'c51c74a40e02'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('listings', sa.Column('reject_reason', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('listings', 'reject_reason')
