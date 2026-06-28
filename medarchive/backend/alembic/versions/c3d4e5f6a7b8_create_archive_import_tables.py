"""create archive import tables

Revision ID: c3d4e5f6a7b8
Revises: b7f9a1a3c2d4
Create Date: 2026-06-27 01:30:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "c3d4e5f6a7b8"
down_revision: str | None = "b7f9a1a3c2d4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "import_batches",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("original_filename", sa.Text(), nullable=False),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("total_files", sa.Integer(), nullable=False),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_import_batches")),
    )
    op.create_index(op.f("ix_import_batches_sha256"), "import_batches", ["sha256"], unique=False)

    op.create_table(
        "file_assets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("import_batch_id", sa.Uuid(), nullable=False),
        sa.Column("parent_asset_id", sa.Uuid(), nullable=True),
        sa.Column("asset_kind", sa.String(length=64), nullable=False),
        sa.Column("original_filename", sa.Text(), nullable=False),
        sa.Column("stored_path", sa.Text(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("extension", sa.String(length=32), nullable=True),
        sa.Column("mime_type", sa.String(length=255), nullable=True),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["import_batch_id"],
            ["import_batches.id"],
            name=op.f("fk_file_assets_import_batch_id_import_batches"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["parent_asset_id"],
            ["file_assets.id"],
            name=op.f("fk_file_assets_parent_asset_id_file_assets"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_file_assets")),
    )
    op.create_index(op.f("ix_file_assets_extension"), "file_assets", ["extension"], unique=False)
    op.create_index(op.f("ix_file_assets_import_batch_id"), "file_assets", ["import_batch_id"], unique=False)
    op.create_index(op.f("ix_file_assets_mime_type"), "file_assets", ["mime_type"], unique=False)
    op.create_index(op.f("ix_file_assets_parent_asset_id"), "file_assets", ["parent_asset_id"], unique=False)
    op.create_index(op.f("ix_file_assets_sha256"), "file_assets", ["sha256"], unique=False)

    op.create_table(
        "price_documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("import_batch_id", sa.Uuid(), nullable=False),
        sa.Column("file_asset_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("detected_type", sa.String(length=64), nullable=True),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["file_asset_id"],
            ["file_assets.id"],
            name=op.f("fk_price_documents_file_asset_id_file_assets"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["import_batch_id"],
            ["import_batches.id"],
            name=op.f("fk_price_documents_import_batch_id_import_batches"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_price_documents")),
        sa.UniqueConstraint("file_asset_id", name=op.f("uq_price_documents_file_asset_id")),
    )
    op.create_index(op.f("ix_price_documents_detected_type"), "price_documents", ["detected_type"], unique=False)
    op.create_index(op.f("ix_price_documents_file_asset_id"), "price_documents", ["file_asset_id"], unique=False)
    op.create_index(op.f("ix_price_documents_import_batch_id"), "price_documents", ["import_batch_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_price_documents_import_batch_id"), table_name="price_documents")
    op.drop_index(op.f("ix_price_documents_file_asset_id"), table_name="price_documents")
    op.drop_index(op.f("ix_price_documents_detected_type"), table_name="price_documents")
    op.drop_table("price_documents")
    op.drop_index(op.f("ix_file_assets_sha256"), table_name="file_assets")
    op.drop_index(op.f("ix_file_assets_parent_asset_id"), table_name="file_assets")
    op.drop_index(op.f("ix_file_assets_mime_type"), table_name="file_assets")
    op.drop_index(op.f("ix_file_assets_import_batch_id"), table_name="file_assets")
    op.drop_index(op.f("ix_file_assets_extension"), table_name="file_assets")
    op.drop_table("file_assets")
    op.drop_index(op.f("ix_import_batches_sha256"), table_name="import_batches")
    op.drop_table("import_batches")
