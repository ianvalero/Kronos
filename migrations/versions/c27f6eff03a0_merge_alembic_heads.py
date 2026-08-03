"""merge alembic heads

Revision ID: c27f6eff03a0
Revises: 03bf3c61b2a1, cf1f872623b8
Create Date: 2026-08-03 13:56:39.269099

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'c27f6eff03a0'
down_revision: Union[str, Sequence[str], None] = ('03bf3c61b2a1', 'cf1f872623b8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
