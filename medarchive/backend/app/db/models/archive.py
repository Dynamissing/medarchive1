from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import FileAssetKind, ImportBatchStatus, PriceDocumentStatus
from app.db.base import Base, TimestampMixin


class ImportBatch(TimestampMixin, Base):
    __tablename__ = "import_batches"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=ImportBatchStatus.PENDING.value, nullable=False)
    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    source_path: Mapped[str] = mapped_column(Text, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    total_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    warnings: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    file_assets: Mapped[list[FileAsset]] = relationship(
        back_populates="import_batch",
        cascade="all, delete-orphan",
    )
    price_documents: Mapped[list[PriceDocument]] = relationship(
        back_populates="import_batch",
        cascade="all, delete-orphan",
    )


class FileAsset(TimestampMixin, Base):
    __tablename__ = "file_assets"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    import_batch_id: Mapped[UUID] = mapped_column(
        ForeignKey("import_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_asset_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("file_assets.id", ondelete="SET NULL"),
        index=True,
    )
    asset_kind: Mapped[str] = mapped_column(String(64), default=FileAssetKind.ARCHIVE_MEMBER.value, nullable=False)
    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    stored_path: Mapped[str] = mapped_column(Text, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    extension: Mapped[str | None] = mapped_column(String(32), index=True)
    mime_type: Mapped[str | None] = mapped_column(String(255), index=True)
    warnings: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    import_batch: Mapped[ImportBatch] = relationship(back_populates="file_assets")
    parent_asset: Mapped[FileAsset | None] = relationship(remote_side="FileAsset.id")
    price_document: Mapped[PriceDocument | None] = relationship(
        back_populates="file_asset",
        cascade="all, delete-orphan",
        uselist=False,
    )


class PriceDocument(TimestampMixin, Base):
    __tablename__ = "price_documents"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    import_batch_id: Mapped[UUID] = mapped_column(
        ForeignKey("import_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("file_assets.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(32), default=PriceDocumentStatus.PENDING.value, nullable=False)
    detected_type: Mapped[str | None] = mapped_column(String(64), index=True)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processing_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text)
    parsed_summary: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    warnings: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    import_batch: Mapped[ImportBatch] = relationship(back_populates="price_documents")
    file_asset: Mapped[FileAsset] = relationship(back_populates="price_document")


class ProcessingEvent(TimestampMixin, Base):
    __tablename__ = "processing_events"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    import_batch_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("import_batches.id", ondelete="CASCADE"),
        index=True,
    )
    price_document_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("price_documents.id", ondelete="CASCADE"),
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    progress_percent: Mapped[int | None] = mapped_column(Integer)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
