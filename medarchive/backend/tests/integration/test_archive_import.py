from __future__ import annotations

import zipfile
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.constants import FileAssetKind, ImportBatchStatus, PriceDocumentStatus
from app.db.base import Base
from app.db.models import FileAsset, ImportBatch, PriceDocument
from app.db.session import get_db
from app.main import create_app
from app.services.admin.archive_import import import_archive_path


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


def create_test_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("prices/alpha.xlsx", b"same-price-content")
        archive.writestr("prices/beta.xlsx", b"same-price-content")
        archive.writestr("notes/readme.txt", b"plain notes")
        archive.writestr("../escape.txt", b"unsafe")


def test_archive_import_from_path_preserves_files_and_creates_pending_documents(
    tmp_path: Path,
    db_session: Session,
) -> None:
    archive_path = tmp_path / "archive.zip"
    storage_root = tmp_path / "storage"
    create_test_zip(archive_path)

    result = import_archive_path(db_session, archive_path, storage_root)

    batches = db_session.scalars(select(ImportBatch)).all()
    assets = db_session.scalars(select(FileAsset)).all()
    documents = db_session.scalars(select(PriceDocument)).all()

    assert result.extracted_files == 3
    assert result.price_documents == 3
    assert len(result.warnings) == 1
    assert len(batches) == 1
    assert batches[0].status == ImportBatchStatus.COMPLETED.value
    assert batches[0].total_files == 3
    assert len(assets) == 4
    assert len(documents) == 3
    assert all(document.status == PriceDocumentStatus.PENDING.value for document in documents)
    assert Path(batches[0].source_path).exists()
    assert all(Path(asset.stored_path).exists() for asset in assets)

    original_assets = [asset for asset in assets if asset.asset_kind == FileAssetKind.ORIGINAL_ARCHIVE.value]
    member_assets = [asset for asset in assets if asset.asset_kind == FileAssetKind.ARCHIVE_MEMBER.value]
    assert len(original_assets) == 1
    assert len(member_assets) == 3
    duplicate_hashes = [asset.sha256 for asset in member_assets if asset.original_filename.endswith(".xlsx")]
    assert len(set(duplicate_hashes)) == 1


def test_archive_upload_endpoint_creates_batch_assets_and_documents(
    tmp_path: Path,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    archive_path = tmp_path / "upload.zip"
    storage_root = tmp_path / "upload-storage"
    create_test_zip(archive_path)
    monkeypatch.setenv("FILE_STORAGE_ROOT", str(storage_root))
    get_settings.cache_clear()

    app = create_app()

    def override_get_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    with archive_path.open("rb") as archive_file:
        response = client.post(
            "/admin/import/archive",
            files={"file": ("upload.zip", archive_file, "application/zip")},
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["extracted_files"] == 3
    assert payload["price_documents"] == 3
    assert len(payload["warnings"]) == 1
    assert db_session.scalars(select(ImportBatch)).one()
    assert len(db_session.scalars(select(FileAsset)).all()) == 4
    assert len(db_session.scalars(select(PriceDocument)).all()) == 3
    assert storage_root.exists()

    app.dependency_overrides.clear()
    get_settings.cache_clear()
