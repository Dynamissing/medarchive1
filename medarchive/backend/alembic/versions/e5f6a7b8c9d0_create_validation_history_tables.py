"""create validation history tables

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-27 13:20:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "e5f6a7b8c9d0"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "price_item_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("row_hash", sa.String(length=64), nullable=False),
        sa.Column("partner_name", sa.Text(), nullable=True),
        sa.Column("service_id", sa.Uuid(), nullable=True),
        sa.Column("price_document_id", sa.Uuid(), nullable=True),
        sa.Column("service_name", sa.Text(), nullable=False),
        sa.Column("normalized_service_name", sa.Text(), nullable=False),
        sa.Column("source_code", sa.String(length=255), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("amount_kzt", sa.Numeric(14, 2), nullable=True),
        sa.Column("amount_label", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("previous_version_id", sa.Uuid(), nullable=True),
        sa.Column("superseded_by_id", sa.Uuid(), nullable=True),
        sa.Column("supersede_reason", sa.Text(), nullable=True),
        sa.Column("source_locator", sa.JSON(), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["price_document_id"],
            ["price_documents.id"],
            name=op.f("fk_price_item_versions_price_document_id_price_documents"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["previous_version_id"],
            ["price_item_versions.id"],
            name=op.f("fk_price_item_versions_previous_version_id_price_item_versions"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["service_id"],
            ["services.id"],
            name=op.f("fk_price_item_versions_service_id_services"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["superseded_by_id"],
            ["price_item_versions.id"],
            name=op.f("fk_price_item_versions_superseded_by_id_price_item_versions"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_price_item_versions")),
    )
    op.create_index(op.f("ix_price_item_versions_currency"), "price_item_versions", ["currency"])
    op.create_index(op.f("ix_price_item_versions_effective_date"), "price_item_versions", ["effective_date"])
    op.create_index(op.f("ix_price_item_versions_is_active"), "price_item_versions", ["is_active"])
    op.create_index(op.f("ix_price_item_versions_normalized_service_name"), "price_item_versions", ["normalized_service_name"])
    op.create_index(op.f("ix_price_item_versions_partner_name"), "price_item_versions", ["partner_name"])
    op.create_index(op.f("ix_price_item_versions_previous_version_id"), "price_item_versions", ["previous_version_id"])
    op.create_index(op.f("ix_price_item_versions_price_document_id"), "price_item_versions", ["price_document_id"])
    op.create_index(op.f("ix_price_item_versions_row_hash"), "price_item_versions", ["row_hash"])
    op.create_index(op.f("ix_price_item_versions_service_id"), "price_item_versions", ["service_id"])
    op.create_index(op.f("ix_price_item_versions_source_code"), "price_item_versions", ["source_code"])
    op.create_index(op.f("ix_price_item_versions_status"), "price_item_versions", ["status"])
    op.create_index(op.f("ix_price_item_versions_superseded_by_id"), "price_item_versions", ["superseded_by_id"])

    op.create_table(
        "anomaly_flags",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("subject_type", sa.String(length=64), nullable=False),
        sa.Column("subject_id", sa.String(length=64), nullable=True),
        sa.Column("row_hash", sa.String(length=64), nullable=True),
        sa.Column("code", sa.String(length=128), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("resolved", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_anomaly_flags")),
    )
    op.create_index(op.f("ix_anomaly_flags_code"), "anomaly_flags", ["code"])
    op.create_index(op.f("ix_anomaly_flags_resolved"), "anomaly_flags", ["resolved"])
    op.create_index(op.f("ix_anomaly_flags_row_hash"), "anomaly_flags", ["row_hash"])
    op.create_index(op.f("ix_anomaly_flags_severity"), "anomaly_flags", ["severity"])
    op.create_index(op.f("ix_anomaly_flags_subject_id"), "anomaly_flags", ["subject_id"])
    op.create_index(op.f("ix_anomaly_flags_subject_type"), "anomaly_flags", ["subject_type"])

    op.create_table(
        "verification_actions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("anomaly_flag_id", sa.Uuid(), nullable=True),
        sa.Column("action_type", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("assigned_to", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["anomaly_flag_id"],
            ["anomaly_flags.id"],
            name=op.f("fk_verification_actions_anomaly_flag_id_anomaly_flags"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_verification_actions")),
    )
    op.create_index(op.f("ix_verification_actions_action_type"), "verification_actions", ["action_type"])
    op.create_index(op.f("ix_verification_actions_anomaly_flag_id"), "verification_actions", ["anomaly_flag_id"])
    op.create_index(op.f("ix_verification_actions_status"), "verification_actions", ["status"])


def downgrade() -> None:
    op.drop_index(op.f("ix_verification_actions_status"), table_name="verification_actions")
    op.drop_index(op.f("ix_verification_actions_anomaly_flag_id"), table_name="verification_actions")
    op.drop_index(op.f("ix_verification_actions_action_type"), table_name="verification_actions")
    op.drop_table("verification_actions")
    op.drop_index(op.f("ix_anomaly_flags_subject_type"), table_name="anomaly_flags")
    op.drop_index(op.f("ix_anomaly_flags_subject_id"), table_name="anomaly_flags")
    op.drop_index(op.f("ix_anomaly_flags_severity"), table_name="anomaly_flags")
    op.drop_index(op.f("ix_anomaly_flags_row_hash"), table_name="anomaly_flags")
    op.drop_index(op.f("ix_anomaly_flags_resolved"), table_name="anomaly_flags")
    op.drop_index(op.f("ix_anomaly_flags_code"), table_name="anomaly_flags")
    op.drop_table("anomaly_flags")
    op.drop_index(op.f("ix_price_item_versions_superseded_by_id"), table_name="price_item_versions")
    op.drop_index(op.f("ix_price_item_versions_status"), table_name="price_item_versions")
    op.drop_index(op.f("ix_price_item_versions_source_code"), table_name="price_item_versions")
    op.drop_index(op.f("ix_price_item_versions_service_id"), table_name="price_item_versions")
    op.drop_index(op.f("ix_price_item_versions_row_hash"), table_name="price_item_versions")
    op.drop_index(op.f("ix_price_item_versions_price_document_id"), table_name="price_item_versions")
    op.drop_index(op.f("ix_price_item_versions_previous_version_id"), table_name="price_item_versions")
    op.drop_index(op.f("ix_price_item_versions_partner_name"), table_name="price_item_versions")
    op.drop_index(op.f("ix_price_item_versions_normalized_service_name"), table_name="price_item_versions")
    op.drop_index(op.f("ix_price_item_versions_is_active"), table_name="price_item_versions")
    op.drop_index(op.f("ix_price_item_versions_effective_date"), table_name="price_item_versions")
    op.drop_index(op.f("ix_price_item_versions_currency"), table_name="price_item_versions")
    op.drop_table("price_item_versions")
