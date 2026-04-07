"""add_indexes_to_listings_filter_fields

Revision ID: 68010d35de9a
Revises: a1b2c3d4e5f6
Create Date: 2026-04-07 16:38:40.468582

"""
from typing import Sequence, Union

from alembic import op


revision: str = '68010d35de9a'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE INDEX IF NOT EXISTS ix_listings_city ON listings (city)')
    op.execute('CREATE INDEX IF NOT EXISTS ix_listings_deal_type ON listings (deal_type)')
    op.execute('CREATE INDEX IF NOT EXISTS ix_listings_status ON listings (status)')
    op.execute('CREATE INDEX IF NOT EXISTS ix_listings_price ON listings (price)')
    op.execute('CREATE INDEX IF NOT EXISTS ix_listings_property_type ON listings (property_type)')


def downgrade() -> None:
    op.drop_index('ix_listings_city', table_name='listings')
    op.drop_index('ix_listings_deal_type', table_name='listings')
    op.drop_index('ix_listings_status', table_name='listings')
    op.drop_index('ix_listings_price', table_name='listings')
    op.drop_index('ix_listings_property_type', table_name='listings')
