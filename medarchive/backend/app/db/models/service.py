from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Service(TimestampMixin, Base):
    __tablename__ = "services"
    __table_args__ = (
        UniqueConstraint("import_batch", "source_hash", name="uq_services_batch_source_hash"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    import_batch: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_row_number: Mapped[int | None] = mapped_column(Integer)
    source_row_id: Mapped[str | None] = mapped_column(String(255), index=True)
    code: Mapped[str | None] = mapped_column(String(255), index=True)
    tariff_code: Mapped[str | None] = mapped_column(String(255), index=True)
    category: Mapped[str | None] = mapped_column(String(255), index=True)
    specialty: Mapped[str | None] = mapped_column(Text)
    name_ru: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_name: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    normalized_specialty: Mapped[str | None] = mapped_column(Text)
    warnings: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    raw_data: Mapped[dict[str, str | None]] = mapped_column(JSON, default=dict, nullable=False)

    synonyms: Mapped[list[ServiceSynonym]] = relationship(
        back_populates="service",
        cascade="all, delete-orphan",
    )


class ServiceSynonym(TimestampMixin, Base):
    __tablename__ = "service_synonyms"
    __table_args__ = (
        UniqueConstraint("service_id", "normalized_value", name="uq_service_synonyms_service_value"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    service_id: Mapped[UUID] = mapped_column(
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    value: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_value: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="deterministic")

    service: Mapped[Service] = relationship(back_populates="synonyms")
