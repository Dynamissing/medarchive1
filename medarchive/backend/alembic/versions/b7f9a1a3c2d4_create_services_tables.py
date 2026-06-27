"""create services tables

Revision ID: b7f9a1a3c2d4
Revises: 49a1ec5a36b7
Create Date: 2026-06-27 01:10:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "b7f9a1a3c2d4"
down_revision: str | None = "49a1ec5a36b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "services",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("import_batch", sa.String(length=128), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_hash", sa.String(length=64), nullable=False),
        sa.Column("source_row_number", sa.Integer(), nullable=True),
        sa.Column("source_row_id", sa.String(length=255), nullable=True),
        sa.Column("code", sa.String(length=255), nullable=True),
        sa.Column("tariff_code", sa.String(length=255), nullable=True),
        sa.Column("category", sa.String(length=255), nullable=True),
        sa.Column("specialty", sa.Text(), nullable=True),
        sa.Column("name_ru", sa.Text(), nullable=False),
        sa.Column("normalized_name", sa.Text(), nullable=False),
        sa.Column("normalized_specialty", sa.Text(), nullable=True),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("raw_data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_services")),
        sa.UniqueConstraint("import_batch", "source_hash", name="uq_services_batch_source_hash"),
    )
    op.create_index(op.f("ix_services_category"), "services", ["category"], unique=False)
    op.create_index(op.f("ix_services_code"), "services", ["code"], unique=False)
    op.create_index(op.f("ix_services_import_batch"), "services", ["import_batch"], unique=False)
    op.create_index(op.f("ix_services_normalized_name"), "services", ["normalized_name"], unique=False)
    op.create_index(op.f("ix_services_source_hash"), "services", ["source_hash"], unique=False)
    op.create_index(op.f("ix_services_source_row_id"), "services", ["source_row_id"], unique=False)
    op.create_index(op.f("ix_services_tariff_code"), "services", ["tariff_code"], unique=False)

    op.create_table(
        "service_synonyms",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("service_id", sa.Uuid(), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("normalized_value", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["service_id"],
            ["services.id"],
            name=op.f("fk_service_synonyms_service_id_services"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_service_synonyms")),
        sa.UniqueConstraint("service_id", "normalized_value", name="uq_service_synonyms_service_value"),
    )
    op.create_index(
        op.f("ix_service_synonyms_normalized_value"),
        "service_synonyms",
        ["normalized_value"],
        unique=False,
    )
    op.create_index(op.f("ix_service_synonyms_service_id"), "service_synonyms", ["service_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_service_synonyms_service_id"), table_name="service_synonyms")
    op.drop_index(op.f("ix_service_synonyms_normalized_value"), table_name="service_synonyms")
    op.drop_table("service_synonyms")
    op.drop_index(op.f("ix_services_tariff_code"), table_name="services")
    op.drop_index(op.f("ix_services_source_row_id"), table_name="services")
    op.drop_index(op.f("ix_services_source_hash"), table_name="services")
    op.drop_index(op.f("ix_services_normalized_name"), table_name="services")
    op.drop_index(op.f("ix_services_import_batch"), table_name="services")
    op.drop_index(op.f("ix_services_code"), table_name="services")
    op.drop_index(op.f("ix_services_category"), table_name="services")
    op.drop_table("services")
