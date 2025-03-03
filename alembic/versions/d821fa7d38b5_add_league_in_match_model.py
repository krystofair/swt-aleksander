"""add league in match model

Revision ID: d821fa7d38b5
Revises: 1febf8ec87fb
Create Date: 2025-01-17 14:31:09.368047

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd821fa7d38b5'
down_revision: Union[str, None] = '1febf8ec87fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('matches', sa.Column('league', sa.String(32), nullable=True))
    pass


def downgrade() -> None:
    op.drop_column('matches', 'league')
    pass
