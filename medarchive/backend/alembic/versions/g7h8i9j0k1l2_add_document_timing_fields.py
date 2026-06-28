"""add document timing fields

Revision ID: g7h8i9j0k1l2
Revises: f6a7b8c9d0e1
Create Date: 2026-06-28 10:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "g7h8i9j0k1l2"
down_revision: str | None = "f6a7b8c9d0e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("price_documents", sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("price_documents", sa.Column("processing_finished_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("price_documents", sa.Column("parser_stage", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("price_documents", "parser_stage")
    op.drop_column("price_documents", "processing_finished_at")
    op.drop_column("price_documents", "processing_started_at")
