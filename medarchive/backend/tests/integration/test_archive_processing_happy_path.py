from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from uuid import UUID

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.constants import ImportBatchStatus, PriceDocumentStatus
from app.db.base import Base
from app.db.models import ImportBatch, PriceDocument, ProcessingEvent
from app.services.admin.archive_import import import_archive_path
from app.workers.pipeline import WorkerPipelineService
from tests.fixtures.generators import create_archive_with_xlsx, create_synthetic_xlsx


@pytest.fixture()
def db_session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    with session_factory() as session:
        yield session
    Base.metadata.drop_all(engine)


def test_archive_processing_happy_path(tmp_path: Path, db_session: Session) -> None:
    workbook_path = create_synthetic_xlsx(tmp_path / "prices.xlsx")
    archive_path = create_archive_with_xlsx(tmp_path / "archive.zip", workbook_path)
    storage_root = tmp_path / "storage"

    result = import_archive_path(db_session, archive_path, storage_root)
    batch = db_session.get(ImportBatch, result.import_batch_id)
    assert batch is not None
    document = db_session.scalars(select(PriceDocument)).one()
    pipeline = WorkerPipelineService(db_session)

    def process_now(price_document_id: str) -> None:
        pipeline.process_document(UUID(price_document_id))

    pipeline.process_batch(batch.id, enqueue_document=process_now)
    db_session.refresh(batch)
    db_session.refresh(document)

    assert batch.status == ImportBatchStatus.COMPLETED.value
    assert batch.processed_files == 1
    assert batch.failed_files == 0
    assert document.status == PriceDocumentStatus.PARSED.value
    assert document.parsed_summary["parser_format"] == "xlsx"
    assert document.parsed_summary["row_candidates"] == 2
    event_types = {event.event_type for event in db_session.scalars(select(ProcessingEvent)).all()}
    assert {"batch_processing_started", "document_processing_completed", "batch_documents_enqueued"} <= event_types
