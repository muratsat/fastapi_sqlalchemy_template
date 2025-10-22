"""add attempts and used columns to one_time_codes

Revision ID: a7a1cdbea83c
Revises: f7aa6f22eed4
Create Date: 2025-10-22 14:16:26.961172

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7a1cdbea83c'
down_revision: Union[str, Sequence[str], None] = 'f7aa6f22eed4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('one_time_codes', sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('one_time_codes', sa.Column('used', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('one_time_codes', 'used')
    op.drop_column('one_time_codes', 'attempts')
