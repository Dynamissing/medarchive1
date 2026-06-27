"""add public search indexes

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-06-27 14:40:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "a7b8c9d0e1f2"
down_revision: str | None = "f6a7b8c9d0e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_services_public_fts "
        "ON services USING GIN (to_tsvector('simple', coalesce(name_ru, '') || ' ' || coalesce(code, '') || ' ' || coalesce(category, '') || ' ' || coalesce(specialty, '')))"
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_services_name_ru_trgm ON services USING GIN (name_ru gin_trgm_ops)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_price_item_versions_partner_trgm ON price_item_versions USING GIN (partner_name gin_trgm_ops)")


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("DROP INDEX IF EXISTS ix_price_item_versions_partner_trgm")
    op.execute("DROP INDEX IF EXISTS ix_services_name_ru_trgm")
    op.execute("DROP INDEX IF EXISTS ix_services_public_fts")
