from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, ForeignKey, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import (
    AnomalySeverity,
    PriceItemVersionStatus,
    VerificationActionStatus,
)
from app.db.base import Base, TimestampMixin


class PriceItemVersion(TimestampMixin, Base):
    __tablename__ = "price_item_versions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    row_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    partner_name: Mapped[str | None] = mapped_column(Text, index=True)
    service_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("services.id", ondelete="SET NULL"),
        index=True,
    )
    price_document_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("price_documents.id", ondelete="SET NULL"),
        index=True,
    )
    service_name: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_service_name: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    source_code: Mapped[str | None] = mapped_column(String(255), index=True)
    effective_date: Mapped[date | None] = mapped_column(Date, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="KZT", nullable=False, index=True)
    amount_kzt: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    amount_label: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(
        String(32),
        default=PriceItemVersionStatus.ACTIVE.value,
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    previous_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("price_item_versions.id", ondelete="SET NULL"),
        index=True,
    )
    superseded_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("price_item_versions.id", ondelete="SET NULL"),
        index=True,
    )
    supersede_reason: Mapped[str | None] = mapped_column(Text)
    source_locator: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    previous_version: Mapped["PriceItemVersion | None"] = relationship(
        foreign_keys=[previous_version_id],
        remote_side="PriceItemVersion.id",
    )
    superseded_by: Mapped["PriceItemVersion | None"] = relationship(
        foreign_keys=[superseded_by_id],
        remote_side="PriceItemVersion.id",
    )


class AnomalyFlag(TimestampMixin, Base):
    __tablename__ = "anomaly_flags"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    subject_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    subject_id: Mapped[str | None] = mapped_column(String(64), index=True)
    row_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    code: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(
        String(32),
        default=AnomalySeverity.WARNING.value,
        nullable=False,
        index=True,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    verification_actions: Mapped[list["VerificationAction"]] = relationship(
        back_populates="anomaly_flag",
        cascade="all, delete-orphan",
    )


class VerificationAction(TimestampMixin, Base):
    __tablename__ = "verification_actions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    anomaly_flag_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("anomaly_flags.id", ondelete="CASCADE"),
        index=True,
    )
    action_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(32),
        default=VerificationActionStatus.OPEN.value,
        nullable=False,
        index=True,
    )
    assigned_to: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    anomaly_flag: Mapped[AnomalyFlag | None] = relationship(back_populates="verification_actions")
