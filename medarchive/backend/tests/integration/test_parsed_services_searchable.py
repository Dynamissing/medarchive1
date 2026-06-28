from __future__ import annotations

from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.constants import FileAssetKind, ImportBatchStatus, PriceDocumentStatus
from app.db.base import Base
from app.db.models import (
    FileAsset,
    ImportBatch,
    PriceDocument,
    PriceItemVersion,
    Service,
    ServiceSynonym,
)
from app.db.session import get_db
from app.main import create_app
from app.workers.pipeline import WorkerPipelineService


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


@pytest.fixture()
def client(db_session: Session) -> Iterator[TestClient]:
    app = create_app()

    def override_get_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_parsed_rows_create_searchable_services(
    tmp_path: Path,
    db_session: Session,
    client: TestClient,
) -> None:
    batch, document = create_batch_with_xlsx(tmp_path, db_session, service_name="Blood test", price=1000)

    pipeline = WorkerPipelineService(db_session)
    outcome = pipeline.process_document(document.id)

    db_session.refresh(document)
    assert outcome.status == PriceDocumentStatus.PARSED.value

    search_response = client.get("/services", params={"q": "blood"})
    assert search_response.status_code == 200
    payload = search_response.json()
    assert payload["meta"]["total"] >= 1
    names = [item["name"] for item in payload["items"]]
    assert any("Blood test" in name for name in names)

    service = db_session.scalars(
        select(Service).where(Service.normalized_name.ilike("%blood test%"))
    ).first()
    assert service is not None
    assert service.source_type == "parsed_document"


def test_repeated_parsing_does_not_duplicate_services(
    tmp_path: Path,
    db_session: Session,
) -> None:
    batch, document = create_batch_with_xlsx(tmp_path, db_session, service_name="MRI brain", price=5000)

    pipeline = WorkerPipelineService(db_session)
    pipeline.process_document(document.id)

    services_after_first = db_session.scalars(
        select(Service).where(Service.normalized_name.ilike("%mri brain%"))
    ).all()
    assert len(services_after_first) == 1

    pipeline.process_document(document.id, force=True)

    services_after_second = db_session.scalars(
        select(Service).where(Service.normalized_name.ilike("%mri brain%"))
    ).all()
    assert len(services_after_second) == 1


def test_search_returns_services_from_parsed_documents(
    tmp_path: Path,
    db_session: Session,
    client: TestClient,
) -> None:
    batch, document = create_batch_with_xlsx(
        tmp_path, db_session, service_name="Cardiologist consultation", price=3000
    )

    pipeline = WorkerPipelineService(db_session)
    pipeline.process_document(document.id)

    search_response = client.get("/search", params={"q": "Cardiologist"})
    assert search_response.status_code == 200
    payload = search_response.json()
    service_results = [item for item in payload["items"] if item["type"] == "service"]
    assert len(service_results) >= 1
    assert any("Cardiologist" in item["label"] for item in service_results)


def test_auto_matched_rows_link_to_existing_service(
    tmp_path: Path,
    db_session: Session,
) -> None:
    existing_service = Service(
        import_batch="test-seed",
        source_type="xlsx",
        source_hash="blood-test-hash",
        code="A-1",
        name_ru="Blood test",
        normalized_name="blood test",
        warnings=[],
        raw_data={},
    )
    db_session.add(existing_service)
    db_session.commit()

    batch, document = create_batch_with_xlsx(tmp_path, db_session, service_name="Blood test", price=1000)

    pipeline = WorkerPipelineService(db_session)
    outcome = pipeline.process_document(document.id)

    db_session.refresh(document)
    assert outcome.status == PriceDocumentStatus.PARSED.value
    assert document.parsed_summary["auto_matched"] == 1

    versions = db_session.scalars(select(PriceItemVersion)).all()
    assert len(versions) >= 1
    assert all(v.service_id is not None for v in versions)
    assert all(v.service_id == existing_service.id for v in versions)


def test_synonyms_created_for_parsed_services(
    tmp_path: Path,
    db_session: Session,
) -> None:
    batch, document = create_batch_with_xlsx(tmp_path, db_session, service_name="Blood test", price=1000)

    pipeline = WorkerPipelineService(db_session)
    pipeline.process_document(document.id)

    service = db_session.scalars(
        select(Service).where(Service.normalized_name.ilike("%blood test%"))
    ).first()
    assert service is not None

    synonyms = db_session.scalars(
        select(ServiceSynonym).where(ServiceSynonym.service_id == service.id)
    ).all()
    assert len(synonyms) >= 1
    assert all(syn.source == "parsed_document" for syn in synonyms)


def test_partner_search_includes_parsed_partners(
    tmp_path: Path,
    db_session: Session,
    client: TestClient,
) -> None:
    batch, document = create_batch_with_xlsx(
        tmp_path,
        db_session,
        service_name="Blood test",
        price=1000,
        filename="Clinic 42 prices.xlsx",
    )

    pipeline = WorkerPipelineService(db_session)
    pipeline.process_document(document.id)

    partners_response = client.get("/partners", params={"q": "Clinic"})
    assert partners_response.status_code == 200
    payload = partners_response.json()
    assert payload["meta"]["total"] >= 1
    assert any("Clinic" in item["name"] for item in payload["items"])


def create_batch_with_xlsx(
    tmp_path: Path,
    db: Session,
    *,
    service_name: str = "Blood test",
    price: int = 1000,
    filename: str = "prices.xlsx",
) -> tuple[ImportBatch, PriceDocument]:
    storage_root = tmp_path / "storage"
    storage_root.mkdir()

    xlsx_path = storage_root / filename
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Prices"
    sheet.append(["Code", "Service", "Price"])
    sheet.append(["A-1", service_name, price])
    workbook.save(xlsx_path)

    batch = ImportBatch(
        source_type="zip",
        status=ImportBatchStatus.PENDING.value,
        original_filename="archive.zip",
        source_path=str(storage_root / "archive.zip"),
        sha256="test-batch-hash",
        total_files=1,
        warnings=[],
    )
    db.add(batch)
    db.flush()

    asset = FileAsset(
        import_batch_id=batch.id,
        asset_kind=FileAssetKind.ARCHIVE_MEMBER.value,
        original_filename=filename,
        stored_path=str(xlsx_path),
        sha256="test-file-hash",
        size_bytes=xlsx_path.stat().st_size,
        extension=".xlsx",
        mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        warnings=[],
    )
    db.add(asset)
    db.flush()

    document = PriceDocument(
        import_batch_id=batch.id,
        file_asset_id=asset.id,
        status=PriceDocumentStatus.PENDING.value,
        detected_type="xlsx",
        warnings=[],
    )
    db.add(document)
    db.commit()
    return batch, document
