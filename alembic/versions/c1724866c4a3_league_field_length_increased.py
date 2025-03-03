"""Expand length of league field

Revision ID: c1724866c4a3
Revises: 2ef5d80eace0
Create Date: 2025-02-12 03:25:49.909567

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1724866c4a3'
down_revision: Union[str, None] = '2ef5d80eace0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('matches', 'league',
               existing_type=sa.VARCHAR(length=32),
               type_=sa.VARCHAR(length=64),
               existing_nullable=True)


def downgrade() -> None:
    op.alter_column('matches', 'league',
               existing_type=sa.VARCHAR(length=64),
               type_=sa.VARCHAR(length=32),
               existing_nullable=True)
