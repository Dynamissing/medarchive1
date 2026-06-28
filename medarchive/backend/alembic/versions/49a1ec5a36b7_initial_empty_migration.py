"""initial empty migration

Revision ID: 49a1ec5a36b7
Revises: 
Create Date: 2026-06-27 00:53:37.227559
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa



revision: str = '49a1ec5a36b7'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
