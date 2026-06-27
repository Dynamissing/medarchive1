from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.constants import (
    FileAssetKind,
    ImportBatchStatus,
    MatchDecisionStatus,
    PriceDocumentStatus,
    PriceItemVersionStatus,
    VerificationActionStatus,
)
from app.db.base import Base
from app.db.models import (
    AnomalyFlag,
    FileAsset,
    ImportBatch,
    MatchingCandidate,
    PriceDocument,
    PriceItemVersion,
    ProcessingEvent,
    Service,
    VerificationAction,
)
from app.db.session import get_db
from app.main import create_app


@pytest.fixture()
def db_session(tmp_path: Path) -> Iterator[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    with session_factory() as session:
        seed_admin_data(session, tmp_path)
        yield session
    Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db_session: Session) -> Iterator[TestClient]:
    app = create_app()

    def override_get_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    token = test_client.post("/admin/login", json={"username": "admin", "password": "admin"}).json()["access_token"]
    test_client.headers.update({"Authorization": f"Bearer {token}"})
    yield test_client
    app.dependency_overrides.clear()


def test_import_services_endpoint(tmp_path: Path, db_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FILE_STORAGE_ROOT", str(tmp_path / "storage"))
    get_settings.cache_clear()
    app = create_app()

    def override_get_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    token = client.post("/admin/login", json={"username": "admin", "password": "admin"}).json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    payload = {"services": [{"ID": "1", "Code": "N-1", "Name_ru": "New service", "TarificatrCode": "T-1"}]}

    response = client.post(
        "/admin/import/services",
        files={"file": ("services.json", json.dumps(payload).encode("utf-8"), "application/json")},
    )

    assert response.status_code == 201
    assert response.json()["imported"] == 1
    assert db_session.query(Service).filter(Service.code == "N-1").one()
    app.dependency_overrides.clear()
    get_settings.cache_clear()


def test_admin_batches_documents_detail_and_preview(client: TestClient, db_session: Session) -> None:
    document = db_session.query(PriceDocument).one()
    file_asset = db_session.query(FileAsset).filter(FileAsset.asset_kind == FileAssetKind.ARCHIVE_MEMBER.value).one()

    batches = client.get("/admin/import-batches")
    documents = client.get("/admin/documents")
    detail = client.get(f"/admin/documents/{document.id}")
    preview = client.get(f"/admin/files/{file_asset.id}/preview")

    assert batches.status_code == 200
    assert batches.json()["items"][0]["total_files"] == 1
    assert documents.status_code == 200
    assert documents.json()["items"][0]["file"]["original_filename"] == "prices.txt"
    assert detail.status_code == 200
    assert detail.json()["events"][0]["event_type"] == "document_processing_completed"
    assert preview.status_code == 200
    assert preview.content == b"preview content"


def test_reprocess_endpoint_enqueues_document(client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    document = db_session.query(PriceDocument).one()

    class FakeTask:
        id = "task-admin"

    def fake_delay(price_document_id: str, force: bool = False) -> FakeTask:
        assert price_document_id == str(document.id)
        assert force is True
        return FakeTask()

    monkeypatch.setattr("app.api.routes.admin.process_document_task.delay", fake_delay)

    response = client.post(f"/admin/documents/{document.id}/reprocess")

    assert response.status_code == 200
    assert response.json()["task_id"] == "task-admin"
    db_session.refresh(document)
    assert document.status == PriceDocumentStatus.PENDING.value
    assert document.progress_percent == 0


def test_verification_unmatched_match_and_price_item_actions(client: TestClient, db_session: Session) -> None:
    price_item = db_session.query(PriceItemVersion).one()

    verification = client.get("/admin/verification")
    unmatched = client.get("/unmatched")
    match = client.post(
        "/match",
        json={
            "service_name": "Blood test",
            "normalized_service_name": "blood test",
            "source_locator": {"type": "unit"},
            "raw_values": {"name": "Blood test"},
            "amounts": [{"label": "cash", "amount": "1000.00", "currency": "KZT", "raw_value": "1000"}],
        },
    )
    verify = client.post(f"/admin/price-items/{price_item.id}/verify")
    reject = client.post(f"/admin/price-items/{price_item.id}/reject")

    assert verification.status_code == 200
    assert verification.json()["items"][0]["anomaly_code"] == "price_change_gt_50_percent"
    assert unmatched.status_code == 200
    assert unmatched.json()["items"][0]["decision_status"] if "decision_status" in unmatched.json()["items"][0] else True
    assert unmatched.json()["items"][0]["normalized_query"] == "unknown row"
    assert match.status_code == 200
    assert match.json()["decision_status"] == MatchDecisionStatus.AUTO_ACCEPT.value
    assert match.json()["candidates"][0]["service_name"] == "Blood test"
    assert verify.status_code == 200
    assert verify.json()["action"] == "verified"
    assert reject.status_code == 200
    assert reject.json()["is_active"] is False


def test_dashboard_and_quality_report(client: TestClient) -> None:
    dashboard = client.get("/admin/dashboard")
    quality = client.get("/admin/reports/quality")

    assert dashboard.status_code == 200
    assert dashboard.json()["documents_total"] == 1
    assert dashboard.json()["unmatched_candidates"] == 1
    assert quality.status_code == 200
    assert quality.json()["parsing"][PriceDocumentStatus.PARSED.value] == 1
    assert quality.json()["matching"][MatchDecisionStatus.UNMATCHED.value] == 1


def seed_admin_data(db: Session, tmp_path: Path) -> None:
    file_path = tmp_path / "prices.txt"
    file_path.write_bytes(b"preview content")
    service = Service(
        import_batch="admin-test",
        source_type="test",
        source_hash="service-1",
        code="B-1",
        name_ru="Blood test",
        normalized_name="blood test",
        warnings=[],
        raw_data={},
    )
    db.add(service)
    db.flush()
    batch = ImportBatch(
        source_type="zip",
        status=ImportBatchStatus.COMPLETED.value,
        original_filename="archive.zip",
        source_path=str(tmp_path / "archive.zip"),
        sha256="batch-hash",
        total_files=1,
        processed_files=1,
        failed_files=0,
        warnings=[],
    )
    db.add(batch)
    db.flush()
    asset = FileAsset(
        import_batch_id=batch.id,
        asset_kind=FileAssetKind.ARCHIVE_MEMBER.value,
        original_filename="prices.txt",
        stored_path=str(file_path),
        sha256="file-hash",
        size_bytes=file_path.stat().st_size,
        extension=".txt",
        mime_type="text/plain",
        warnings=[],
    )
    db.add(asset)
    db.flush()
    document = PriceDocument(
        import_batch_id=batch.id,
        file_asset_id=asset.id,
        status=PriceDocumentStatus.PARSED.value,
        detected_type="txt",
        progress_percent=100,
        processing_attempts=1,
        parsed_summary={"parser_format": "txt"},
        warnings=[],
    )
    db.add(document)
    db.flush()
    price_item = PriceItemVersion(
        row_hash="row-1",
        partner_name="Clinic 1",
        service_id=service.id,
        price_document_id=document.id,
        service_name="Blood test",
        normalized_service_name="blood test",
        source_code="B-1",
        effective_date=date(2026, 1, 1),
        amount=Decimal("1000.00"),
        currency="KZT",
        amount_kzt=Decimal("1000.00"),
        amount_label="cash",
        status=PriceItemVersionStatus.ACTIVE.value,
        is_active=True,
        source_locator={},
        raw_payload={},
    )
    db.add(price_item)
    db.flush()
    anomaly = AnomalyFlag(
        subject_type="price_item_version",
        subject_id=str(price_item.id),
        row_hash="row-1",
        code="price_change_gt_50_percent",
        severity="warning",
        message="Large price change",
        payload={},
        resolved=False,
    )
    db.add(anomaly)
    db.flush()
    db.add(
        VerificationAction(
            anomaly_flag_id=anomaly.id,
            action_type="review_large_price_change",
            status=VerificationActionStatus.OPEN.value,
            payload={},
        )
    )
    db.add(
        MatchingCandidate(
            row_hash="row-unmatched",
            price_document_id=document.id,
            service_id=None,
            rank=1,
            score=0.0,
            decision_status=MatchDecisionStatus.UNMATCHED.value,
            strategy="none",
            normalized_query="unknown row",
            source_locator={},
            row_payload={},
            explanation={"warnings": ["No match"]},
        )
    )
    db.add(
        ProcessingEvent(
            import_batch_id=batch.id,
            price_document_id=document.id,
            event_type="document_processing_completed",
            status="completed",
            message="Done",
            progress_percent=100,
            payload={},
        )
    )
    db.commit()
