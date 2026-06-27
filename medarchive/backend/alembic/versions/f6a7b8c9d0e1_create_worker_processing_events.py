"""create worker processing events

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-06-27 14:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "f6a7b8c9d0e1"
down_revision: str | None = "e5f6a7b8c9d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("import_batches", sa.Column("processed_files", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("import_batches", sa.Column("failed_files", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("price_documents", sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("price_documents", sa.Column("processing_attempts", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("price_documents", sa.Column("last_error", sa.Text(), nullable=True))
    op.add_column("price_documents", sa.Column("parsed_summary", sa.JSON(), nullable=False, server_default="{}"))

    op.create_table(
        "processing_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("import_batch_id", sa.Uuid(), nullable=True),
        sa.Column("price_document_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("progress_percent", sa.Integer(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["import_batch_id"],
            ["import_batches.id"],
            name=op.f("fk_processing_events_import_batch_id_import_batches"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["price_document_id"],
            ["price_documents.id"],
            name=op.f("fk_processing_events_price_document_id_price_documents"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_processing_events")),
    )
    op.create_index(op.f("ix_processing_events_event_type"), "processing_events", ["event_type"])
    op.create_index(op.f("ix_processing_events_import_batch_id"), "processing_events", ["import_batch_id"])
    op.create_index(op.f("ix_processing_events_price_document_id"), "processing_events", ["price_document_id"])
    op.create_index(op.f("ix_processing_events_status"), "processing_events", ["status"])


def downgrade() -> None:
    op.drop_index(op.f("ix_processing_events_status"), table_name="processing_events")
    op.drop_index(op.f("ix_processing_events_price_document_id"), table_name="processing_events")
    op.drop_index(op.f("ix_processing_events_import_batch_id"), table_name="processing_events")
    op.drop_index(op.f("ix_processing_events_event_type"), table_name="processing_events")
    op.drop_table("processing_events")
    op.drop_column("price_documents", "parsed_summary")
    op.drop_column("price_documents", "last_error")
    op.drop_column("price_documents", "processing_attempts")
    op.drop_column("price_documents", "progress_percent")
    op.drop_column("import_batches", "failed_files")
    op.drop_column("import_batches", "processed_files")
