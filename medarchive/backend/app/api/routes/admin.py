from __future__ import annotations

import zipfile
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import ImportBatch, PriceDocument
from app.db.session import get_db
from app.services.admin.archive_import import import_archive_bytes
from app.workers.pipeline import WorkerPipelineService
from app.workers.tasks import process_batch_task, process_document_task

router = APIRouter(prefix="/admin/import", tags=["admin"])


class ArchiveImportResponse(BaseModel):
    import_batch_id: UUID
    original_asset_id: UUID
    extracted_files: int
    price_documents: int
    warnings: list[str]


class ProcessingEnqueueResponse(BaseModel):
    task_id: str
    target_id: UUID
    target_type: str


@router.post("/archive", response_model=ArchiveImportResponse, status_code=status.HTTP_201_CREATED)
async def import_archive(file: UploadFile = File(...), db: Session = Depends(get_db)) -> ArchiveImportResponse:
    filename = file.filename or "archive.zip"
    if not filename.casefold().endswith(".zip"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only ZIP uploads are supported")

    content = await file.read()
    try:
        result = import_archive_bytes(
            db=db,
            content=content,
            original_filename=filename,
            storage_root=get_settings().file_storage_root,
        )
    except zipfile.BadZipFile as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ZIP archive") from exc

    return ArchiveImportResponse(
        import_batch_id=result.import_batch_id,
        original_asset_id=result.original_asset_id,
        extracted_files=result.extracted_files,
        price_documents=result.price_documents,
        warnings=result.warnings,
    )


@router.post("/batches/{import_batch_id}/process", response_model=ProcessingEnqueueResponse)
def enqueue_batch_processing(import_batch_id: UUID, db: Session = Depends(get_db)) -> ProcessingEnqueueResponse:
    exists = db.scalar(select(ImportBatch.id).where(ImportBatch.id == import_batch_id))
    if exists is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import batch not found")
    task = process_batch_task.delay(str(import_batch_id))
    return ProcessingEnqueueResponse(task_id=task.id, target_id=import_batch_id, target_type="import_batch")


@router.post("/documents/{price_document_id}/reprocess", response_model=ProcessingEnqueueResponse)
def enqueue_document_reprocess(price_document_id: UUID, db: Session = Depends(get_db)) -> ProcessingEnqueueResponse:
    exists = db.scalar(select(PriceDocument.id).where(PriceDocument.id == price_document_id))
    if exists is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Price document not found")
    WorkerPipelineService(db).reset_for_reprocess(price_document_id)
    task = process_document_task.delay(str(price_document_id), force=True)
    return ProcessingEnqueueResponse(task_id=task.id, target_id=price_document_id, target_type="price_document")
