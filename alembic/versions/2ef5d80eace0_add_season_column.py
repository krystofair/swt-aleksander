"""add season column

Revision ID: 2ef5d80eace0
Revises: d821fa7d38b5
Create Date: 2025-01-17 16:19:38.236588

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2ef5d80eace0'
down_revision: Union[str, None] = 'd821fa7d38b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('matches', sa.Column('season', sa.String(length=16), nullable=True))


def downgrade() -> None:
    op.drop_column('matches', 'season')
