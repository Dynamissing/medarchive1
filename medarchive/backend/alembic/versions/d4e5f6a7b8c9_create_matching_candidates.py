"""create matching candidates

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-06-27 12:40:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "d4e5f6a7b8c9"
down_revision: str | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "matching_candidates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("row_hash", sa.String(length=64), nullable=False),
        sa.Column("price_document_id", sa.Uuid(), nullable=True),
        sa.Column("service_id", sa.Uuid(), nullable=True),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("decision_status", sa.String(length=32), nullable=False),
        sa.Column("strategy", sa.String(length=64), nullable=False),
        sa.Column("normalized_query", sa.Text(), nullable=False),
        sa.Column("source_code", sa.String(length=255), nullable=True),
        sa.Column("source_locator", sa.JSON(), nullable=False),
        sa.Column("row_payload", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["price_document_id"],
            ["price_documents.id"],
            name=op.f("fk_matching_candidates_price_document_id_price_documents"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["service_id"],
            ["services.id"],
            name=op.f("fk_matching_candidates_service_id_services"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_matching_candidates")),
    )
    op.create_index(op.f("ix_matching_candidates_decision_status"), "matching_candidates", ["decision_status"])
    op.create_index(op.f("ix_matching_candidates_price_document_id"), "matching_candidates", ["price_document_id"])
    op.create_index(op.f("ix_matching_candidates_row_hash"), "matching_candidates", ["row_hash"])
    op.create_index(op.f("ix_matching_candidates_service_id"), "matching_candidates", ["service_id"])
    op.create_index(op.f("ix_matching_candidates_source_code"), "matching_candidates", ["source_code"])


def downgrade() -> None:
    op.drop_index(op.f("ix_matching_candidates_source_code"), table_name="matching_candidates")
    op.drop_index(op.f("ix_matching_candidates_service_id"), table_name="matching_candidates")
    op.drop_index(op.f("ix_matching_candidates_row_hash"), table_name="matching_candidates")
    op.drop_index(op.f("ix_matching_candidates_price_document_id"), table_name="matching_candidates")
    op.drop_index(op.f("ix_matching_candidates_decision_status"), table_name="matching_candidates")
    op.drop_table("matching_candidates")
