from __future__ import annotations

import hashlib
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.constants import FileAssetKind, ImportBatchStatus, PriceDocumentStatus
from app.core.logging import get_logger
from app.db.models import FileAsset, ImportBatch, PriceDocument
from app.utils.file_detection import detect_file_type

logger = get_logger(__name__)


@dataclass(frozen=True)
class ArchiveImportResult:
    import_batch_id: UUID
    original_asset_id: UUID
    extracted_files: int
    price_documents: int
    warnings: list[str]


def import_archive_path(db: Session, source_path: Path, storage_root: Path) -> ArchiveImportResult:
    resolved_source = source_path.resolve()
    if not resolved_source.is_file():
        raise FileNotFoundError(f"Archive does not exist: {source_path}")
    with resolved_source.open("rb") as archive_file:
        return import_archive_stream(
            db=db,
            stream=archive_file,
            original_filename=resolved_source.name,
            storage_root=storage_root,
        )


def import_archive_bytes(
    db: Session,
    content: bytes,
    original_filename: str,
    storage_root: Path,
) -> ArchiveImportResult:
    temp_path = prepare_storage_root(storage_root) / "_upload_buffer.zip"
    temp_path.write_bytes(content)
    try:
        with temp_path.open("rb") as archive_file:
            return import_archive_stream(
                db=db,
                stream=archive_file,
                original_filename=original_filename,
                storage_root=storage_root,
            )
    finally:
        temp_path.unlink(missing_ok=True)


def import_archive_stream(
    db: Session,
    stream,
    original_filename: str,
    storage_root: Path,
) -> ArchiveImportResult:
    root = prepare_storage_root(storage_root)
    original_hash = sha256_stream(stream)
    stream.seek(0)

    batch = ImportBatch(
        source_type="zip",
        status=ImportBatchStatus.PENDING.value,
        original_filename=original_filename,
        source_path="",
        sha256=original_hash,
        total_files=0,
        warnings=[],
    )
    db.add(batch)
    db.flush()

    batch_dir = root / str(batch.id)
    originals_dir = batch_dir / "original"
    extracted_dir = batch_dir / "extracted"
    originals_dir.mkdir(parents=True, exist_ok=True)
    extracted_dir.mkdir(parents=True, exist_ok=True)

    original_detection = detect_file_type(original_filename)
    original_path = originals_dir / safe_filename(original_filename or "archive.zip")
    with original_path.open("wb") as output:
        shutil.copyfileobj(stream, output)

    batch.source_path = str(original_path)
    original_asset = FileAsset(
        import_batch_id=batch.id,
        asset_kind=FileAssetKind.ORIGINAL_ARCHIVE.value,
        original_filename=original_filename,
        stored_path=str(original_path),
        sha256=original_hash,
        size_bytes=original_path.stat().st_size,
        extension=original_detection.extension,
        mime_type=original_detection.mime_type,
        warnings=[],
    )
    db.add(original_asset)
    db.flush()

    extracted_count = 0
    price_document_count = 0
    warnings: list[str] = []

    try:
        with zipfile.ZipFile(original_path) as archive:
            for member in archive.infolist():
                if member.is_dir():
                    continue
                safe_member_path = safe_zip_member_path(member.filename)
                if safe_member_path is None:
                    warning = f"Skipped unsafe ZIP member path: {member.filename}"
                    warnings.append(warning)
                    logger.warning(warning)
                    continue

                target_path = unique_member_path(extracted_dir / safe_member_path)
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as member_file, target_path.open("wb") as output:
                    shutil.copyfileobj(member_file, output)

                member_hash = sha256_path(target_path)
                detection = detect_file_type(member.filename, path=target_path)
                file_warnings = []
                if archive.getinfo(member.filename).CRC != member.CRC:
                    file_warnings.append("ZIP CRC metadata mismatch")

                asset = FileAsset(
                    import_batch_id=batch.id,
                    parent_asset_id=original_asset.id,
                    asset_kind=FileAssetKind.ARCHIVE_MEMBER.value,
                    original_filename=member.filename,
                    stored_path=str(target_path),
                    sha256=member_hash,
                    size_bytes=target_path.stat().st_size,
                    extension=detection.extension,
                    mime_type=detection.mime_type,
                    warnings=file_warnings,
                )
                db.add(asset)
                db.flush()

                db.add(
                    PriceDocument(
                        import_batch_id=batch.id,
                        file_asset_id=asset.id,
                        status=PriceDocumentStatus.PENDING.value,
                        detected_type=detection.parser_format,
                        warnings=[],
                    )
                )
                extracted_count += 1
                price_document_count += 1
    except zipfile.BadZipFile:
        batch.status = ImportBatchStatus.FAILED.value
        batch.warnings = ["Uploaded file is not a valid ZIP archive"]
        db.commit()
        raise

    batch.total_files = extracted_count
    batch.warnings = warnings
    batch.status = ImportBatchStatus.COMPLETED.value
    db.commit()

    return ArchiveImportResult(
        import_batch_id=batch.id,
        original_asset_id=original_asset.id,
        extracted_files=extracted_count,
        price_documents=price_document_count,
        warnings=warnings,
    )


def prepare_storage_root(storage_root: Path) -> Path:
    root = storage_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def sha256_stream(stream) -> str:
    digest = hashlib.sha256()
    while chunk := stream.read(1024 * 1024):
        digest.update(chunk)
    return digest.hexdigest()


def sha256_path(path: Path) -> str:
    with path.open("rb") as file_obj:
        return sha256_stream(file_obj)


def safe_filename(filename: str) -> str:
    cleaned = Path(filename).name.strip()
    return cleaned or "archive.zip"


def safe_zip_member_path(member_name: str) -> Path | None:
    normalized = member_name.replace("\\", "/")
    pure_path = PurePosixPath(normalized)
    if pure_path.is_absolute() or ".." in pure_path.parts:
        return None
    parts = [part for part in pure_path.parts if part not in ("", ".")]
    if not parts:
        return None
    return Path(*parts)


def unique_member_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 1
    while True:
        candidate = parent / f"{stem}-{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1
