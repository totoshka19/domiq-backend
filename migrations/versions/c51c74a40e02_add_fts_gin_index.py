"""add_fts_gin_index

Revision ID: c51c74a40e02
Revises: 4f9085de11ed
Create Date: 2026-04-06 17:54:50.312882

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c51c74a40e02'
down_revision: Union[str, None] = '4f9085de11ed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE INDEX ix_listings_fts ON listings
        USING GIN (
            to_tsvector('russian',
                coalesce(title, '') || ' ' ||
                coalesce(address, '') || ' ' ||
                coalesce(description, '')
            )
        )
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_listings_fts")
