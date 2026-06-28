"""merge migration heads

Revision ID: 6964316e1419
Revises: a7b8c9d0e1f2, g7h8i9j0k1l2
Create Date: 2026-06-28 11:27:02.357703
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa



revision: str = '6964316e1419'
down_revision: str | None = ('a7b8c9d0e1f2', 'g7h8i9j0k1l2')
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
