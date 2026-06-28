from __future__ import annotations

import shutil
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
import zipfile
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.auth import create_admin_token, require_admin, verify_admin_credentials
from app.core.config import get_settings
from app.core.constants import MatchDecisionStatus, PriceDocumentStatus, PriceItemVersionStatus, VerificationActionStatus
from app.core.logging import get_logger
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
from app.db.session import SessionLocal, get_db
from app.services.admin.archive_import import import_archive_bytes
from app.services.admin.service_directory_import import import_service_directory
from app.services.matching.engine import LayeredMatchingEngine
from app.services.normalization.row_normalization import PriceItemAmountPayload, PriceItemPayload
from app.services.validation.price_history import PriceHistoryService
from app.workers.pipeline import WorkerPipelineService
from app.workers.tasks import process_batch_task, process_document_task

router = APIRouter(tags=["admin"], dependencies=[Depends(require_admin)])
login_router = APIRouter(tags=["admin"])
MAX_PAGE_SIZE = 100
logger = get_logger(__name__)


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class ArchiveImportResponse(BaseModel):
    import_batch_id: UUID
    original_asset_id: UUID
    extracted_files: int
    price_documents: int
    processing_task_id: str | None = None
    warnings: list[str]


class ProcessingEnqueueResponse(BaseModel):
    task_id: str
    target_id: UUID
    target_type: str


class ServiceImportResponse(BaseModel):
    batch: str
    source_path: str
    rows_seen: int
    imported: int
    updated: int
    skipped: int
    warnings: list[str]


class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int
    pages: int


class ImportBatchSummary(BaseModel):
    id: UUID
    source_type: str
    status: str
    original_filename: str
    total_files: int
    processed_files: int
    failed_files: int
    warnings: list[str]
    created_at: datetime


class ImportBatchListResponse(BaseModel):
    items: list[ImportBatchSummary]
    meta: PageMeta


class FileAssetSummary(BaseModel):
    id: UUID
    original_filename: str
    stored_path: str
    extension: str | None = None
    mime_type: str | None = None
    size_bytes: int


class PriceDocumentSummary(BaseModel):
    id: UUID
    import_batch_id: UUID
    file_asset_id: UUID
    status: str
    detected_type: str | None = None
    progress_percent: int
    processing_attempts: int
    last_error: str | None = None
    warnings: list[str]
    parsed_summary: dict
    file: FileAssetSummary | None = None


class PriceDocumentListResponse(BaseModel):
    items: list[PriceDocumentSummary]
    meta: PageMeta


class ProcessingEventSummary(BaseModel):
    id: UUID
    event_type: str
    status: str
    message: str
    progress_percent: int | None = None
    payload: dict
    created_at: datetime


class PriceDocumentDetail(PriceDocumentSummary):
    events: list[ProcessingEventSummary] = Field(default_factory=list)


class VerificationItem(BaseModel):
    id: UUID
    anomaly_flag_id: UUID | None = None
    action_type: str
    status: str
    notes: str | None = None
    payload: dict
    anomaly_code: str | None = None
    anomaly_message: str | None = None
    severity: str | None = None


class VerificationListResponse(BaseModel):
    items: list[VerificationItem]
    meta: PageMeta


class UnmatchedCandidateSummary(BaseModel):
    id: UUID
    row_hash: str
    price_document_id: UUID | None = None
    score: float
    normalized_query: str
    source_code: str | None = None
    explanation: dict
    created_at: datetime


class UnmatchedListResponse(BaseModel):
    items: list[UnmatchedCandidateSummary]
    meta: PageMeta


class MatchAmountRequest(BaseModel):
    label: str | None = None
    amount: Decimal
    currency: str | None = None
    raw_value: str


class MatchRequest(BaseModel):
    service_name: str
    normalized_service_name: str
    source_code: str | None = None
    partner_name: str | None = None
    source_locator: dict = Field(default_factory=dict)
    raw_values: dict = Field(default_factory=dict)
    amounts: list[MatchAmountRequest] = Field(default_factory=list)
    top_k: int = Field(default=5, ge=1, le=20)
    persist_review: bool = True


class MatchCandidateResponse(BaseModel):
    service_id: UUID
    service_name: str
    service_code: str | None = None
    tariff_code: str | None = None
    score: float
    decision_status: str
    strategy: str
    explanation: dict


class MatchResponse(BaseModel):
    row_hash: str
    normalized_query: str
    decision_status: str
    candidates: list[MatchCandidateResponse]
    warnings: list[str]


class PriceItemReviewResponse(BaseModel):
    id: UUID
    status: str
    is_active: bool
    action: str


class ManualMatchRequest(BaseModel):
    service_id: UUID


class ManualMatchResponse(BaseModel):
    candidate_id: UUID
    service_id: UUID
    created_price_items: int
    status: str


class VerificationResolveRequest(BaseModel):
    notes: str | None = None


class VerificationResolveResponse(BaseModel):
    action_id: UUID
    status: str
    resolved_anomaly: bool


class DashboardResponse(BaseModel):
    import_batches: int
    documents_total: int
    documents_by_status: dict[str, int]
    open_verification_actions: int
    unresolved_anomalies: int
    unmatched_candidates: int
    active_price_items: int
    extracted_rows: int = 0
    normalized_rows: int = 0
    auto_matched: int = 0
    needs_review: int = 0
    normalization_rate_percent: float = 0.0


class QualityReportResponse(BaseModel):
    generated_at: datetime
    parsing: dict
    matching: dict
    validation: dict
    price_history: dict
    documents: dict = Field(default_factory=dict)
    extraction: dict = Field(default_factory=dict)
    normalization: dict = Field(default_factory=dict)
    top_parser_errors: list[dict] = Field(default_factory=list)


@login_router.post("/admin/login", response_model=AdminLoginResponse)
def admin_login(request: AdminLoginRequest) -> AdminLoginResponse:
    settings = get_settings()
    if not verify_admin_credentials(request.username, request.password, settings):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return AdminLoginResponse(access_token=create_admin_token(settings), expires_in=settings.admin_token_ttl_seconds)


@router.post("/admin/import/archive", response_model=ArchiveImportResponse, status_code=status.HTTP_201_CREATED)
async def import_archive(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ArchiveImportResponse:
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

    processing_task_id: str | None = None
    if result.price_documents:
        try:
            processing_task = process_batch_task.delay(str(result.import_batch_id))
            processing_task_id = processing_task.id
        except Exception:
            logger.exception("Celery enqueue failed; processing import batch in API background task.")
            background_tasks.add_task(process_import_batch_locally, result.import_batch_id)
            processing_task_id = f"background:{result.import_batch_id}"

    return ArchiveImportResponse(
        import_batch_id=result.import_batch_id,
        original_asset_id=result.original_asset_id,
        extracted_files=result.extracted_files,
        price_documents=result.price_documents,
        processing_task_id=processing_task_id,
        warnings=result.warnings,
    )


@router.post("/admin/import/services", response_model=ServiceImportResponse, status_code=status.HTTP_201_CREATED)
async def import_services(file: UploadFile = File(...), db: Session = Depends(get_db)) -> ServiceImportResponse:
    filename = file.filename or "services.xlsx"
    if not filename.casefold().endswith((".xlsx", ".json")):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only XLSX and JSON service directories are supported")
    root = get_settings().file_storage_root / "service-imports"
    root.mkdir(parents=True, exist_ok=True)
    target_path = root / safe_upload_filename(filename)
    with target_path.open("wb") as output:
        shutil.copyfileobj(file.file, output)
    try:
        result = import_service_directory(db, target_path)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ServiceImportResponse(
        batch=result.batch,
        source_path=str(result.source_path),
        rows_seen=result.rows_seen,
        imported=result.imported,
        updated=result.updated,
        skipped=result.skipped,
        warnings=result.warnings,
    )


@router.get("/admin/import-batches", response_model=ImportBatchListResponse)
def list_import_batches(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=MAX_PAGE_SIZE),
    status_filter: str | None = Query(None, alias="status"),
) -> ImportBatchListResponse:
    page_size = clamp_page_size(page_size)
    query = select(ImportBatch)
    if status_filter:
        query = query.where(ImportBatch.status == status_filter)
    total = count_for(db, query)
    batches = db.scalars(query.order_by(ImportBatch.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return ImportBatchListResponse(items=[import_batch_summary(batch) for batch in batches], meta=page_meta(page, page_size, total))


@router.get("/admin/documents", response_model=PriceDocumentListResponse)
def list_documents(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=MAX_PAGE_SIZE),
    status_filter: str | None = Query(None, alias="status"),
    import_batch_id: UUID | None = Query(None),
) -> PriceDocumentListResponse:
    page_size = clamp_page_size(page_size)
    query = select(PriceDocument).options(selectinload(PriceDocument.file_asset))
    if status_filter:
        query = query.where(PriceDocument.status == status_filter)
    if import_batch_id:
        query = query.where(PriceDocument.import_batch_id == import_batch_id)
    total = count_for(db, query)
    documents = db.scalars(query.order_by(PriceDocument.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return PriceDocumentListResponse(items=[document_summary(document) for document in documents], meta=page_meta(page, page_size, total))


@router.get("/admin/documents/{price_document_id}", response_model=PriceDocumentDetail)
def get_document(price_document_id: UUID, db: Session = Depends(get_db)) -> PriceDocumentDetail:
    document = db.scalars(
        select(PriceDocument).options(selectinload(PriceDocument.file_asset)).where(PriceDocument.id == price_document_id)
    ).one_or_none()
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Price document not found")
    events = db.scalars(
        select(ProcessingEvent).where(ProcessingEvent.price_document_id == document.id).order_by(ProcessingEvent.created_at.desc())
    ).all()
    return PriceDocumentDetail(**document_summary(document).model_dump(), events=[event_summary(event) for event in events])


@router.post("/admin/import/batches/{import_batch_id}/process", response_model=ProcessingEnqueueResponse)
def enqueue_batch_processing(import_batch_id: UUID, db: Session = Depends(get_db)) -> ProcessingEnqueueResponse:
    exists = db.scalar(select(ImportBatch.id).where(ImportBatch.id == import_batch_id))
    if exists is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import batch not found")
    task = process_batch_task.delay(str(import_batch_id))
    return ProcessingEnqueueResponse(task_id=task.id, target_id=import_batch_id, target_type="import_batch")


@router.post("/admin/documents/{price_document_id}/reprocess", response_model=ProcessingEnqueueResponse)
def enqueue_document_reprocess(price_document_id: UUID, db: Session = Depends(get_db)) -> ProcessingEnqueueResponse:
    exists = db.scalar(select(PriceDocument.id).where(PriceDocument.id == price_document_id))
    if exists is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Price document not found")
    WorkerPipelineService(db).reset_for_reprocess(price_document_id)
    task = process_document_task.delay(str(price_document_id), force=True)
    return ProcessingEnqueueResponse(task_id=task.id, target_id=price_document_id, target_type="price_document")


@router.post("/admin/import/documents/{price_document_id}/reprocess", response_model=ProcessingEnqueueResponse)
def enqueue_legacy_document_reprocess(price_document_id: UUID, db: Session = Depends(get_db)) -> ProcessingEnqueueResponse:
    return enqueue_document_reprocess(price_document_id, db)


@router.get("/admin/verification", response_model=VerificationListResponse)
def list_verification(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=MAX_PAGE_SIZE),
    status_filter: str | None = Query(None, alias="status"),
) -> VerificationListResponse:
    page_size = clamp_page_size(page_size)
    query = select(VerificationAction, AnomalyFlag).join(AnomalyFlag, VerificationAction.anomaly_flag_id == AnomalyFlag.id, isouter=True)
    if status_filter:
        query = query.where(VerificationAction.status == status_filter)
    total = count_for(db, query)
    rows = db.execute(query.order_by(VerificationAction.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    items = [
        VerificationItem(
            id=action.id,
            anomaly_flag_id=action.anomaly_flag_id,
            action_type=action.action_type,
            status=action.status,
            notes=action.notes,
            payload=action.payload,
            anomaly_code=flag.code if flag else None,
            anomaly_message=flag.message if flag else None,
            severity=flag.severity if flag else None,
        )
        for action, flag in rows
    ]
    return VerificationListResponse(items=items, meta=page_meta(page, page_size, total))


@router.get("/unmatched", response_model=UnmatchedListResponse)
def list_unmatched(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=MAX_PAGE_SIZE),
) -> UnmatchedListResponse:
    page_size = clamp_page_size(page_size)
    query = select(MatchingCandidate).where(MatchingCandidate.decision_status == MatchDecisionStatus.UNMATCHED.value)
    total = count_for(db, query)
    candidates = db.scalars(query.order_by(MatchingCandidate.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return UnmatchedListResponse(
        items=[
            UnmatchedCandidateSummary(
                id=candidate.id,
                row_hash=candidate.row_hash,
                price_document_id=candidate.price_document_id,
                score=candidate.score,
                normalized_query=candidate.normalized_query,
                source_code=candidate.source_code,
                explanation=candidate.explanation,
                created_at=candidate.created_at,
            )
            for candidate in candidates
        ],
        meta=page_meta(page, page_size, total),
    )


@router.post("/match", response_model=MatchResponse)
def match_row(request: MatchRequest, db: Session = Depends(get_db)) -> MatchResponse:
    row = PriceItemPayload(
        service_name=request.service_name,
        normalized_service_name=request.normalized_service_name,
        source_code=request.source_code,
        partner_name=request.partner_name,
        source_locator=request.source_locator,
        raw_values=request.raw_values,
        amounts=[
            PriceItemAmountPayload(label=amount.label, amount=amount.amount, currency=amount.currency, raw_value=amount.raw_value)
            for amount in request.amounts
        ],
    )
    result = LayeredMatchingEngine(db).match_row(row, top_k=request.top_k, persist_review=request.persist_review)
    return MatchResponse(
        row_hash=result.row_hash,
        normalized_query=result.normalized_query,
        decision_status=result.decision_status.value,
        candidates=[
            MatchCandidateResponse(
                service_id=candidate.service_id,
                service_name=candidate.service_name,
                service_code=candidate.service_code,
                tariff_code=candidate.tariff_code,
                score=candidate.score,
                decision_status=candidate.decision_status.value,
                strategy=candidate.strategy,
                explanation=candidate.explanation.model_dump(mode="json"),
            )
            for candidate in result.candidates
        ],
        warnings=result.warnings,
    )


@router.post("/admin/unmatched/{candidate_id}/match", response_model=ManualMatchResponse)
def manually_match_candidate(
    candidate_id: UUID,
    request: ManualMatchRequest,
    db: Session = Depends(get_db),
) -> ManualMatchResponse:
    candidate = db.get(MatchingCandidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matching candidate not found")
    service = db.get(Service, request.service_id)
    if service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    if not candidate.row_payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Matching candidate has no row payload")

    row = PriceItemPayload.model_validate(candidate.row_payload)
    versions = PriceHistoryService(db).validate_and_record(
        row,
        service_id=service.id,
        price_document_id=candidate.price_document_id,
    )
    db.execute(delete(MatchingCandidate).where(MatchingCandidate.row_hash == candidate.row_hash))
    db.commit()
    return ManualMatchResponse(
        candidate_id=candidate_id,
        service_id=service.id,
        created_price_items=len(versions),
        status=VerificationActionStatus.COMPLETED.value,
    )


@router.post("/admin/price-items/{price_item_id}/verify", response_model=PriceItemReviewResponse)
def verify_price_item(price_item_id: UUID, db: Session = Depends(get_db)) -> PriceItemReviewResponse:
    item = db.get(PriceItemVersion, price_item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Price item not found")
    for flag in db.scalars(select(AnomalyFlag).where(AnomalyFlag.subject_id == str(item.id))).all():
        flag.resolved = True
    db.add(VerificationAction(action_type="verify_price_item", status=VerificationActionStatus.COMPLETED.value, payload={"price_item_id": str(item.id)}))
    db.commit()
    return PriceItemReviewResponse(id=item.id, status=item.status, is_active=item.is_active, action="verified")


@router.post("/admin/price-items/{price_item_id}/reject", response_model=PriceItemReviewResponse)
def reject_price_item(price_item_id: UUID, db: Session = Depends(get_db)) -> PriceItemReviewResponse:
    item = db.get(PriceItemVersion, price_item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Price item not found")
    item.status = PriceItemVersionStatus.INACTIVE.value
    item.is_active = False
    item.supersede_reason = "rejected_by_admin"
    db.add(VerificationAction(action_type="reject_price_item", status=VerificationActionStatus.COMPLETED.value, payload={"price_item_id": str(item.id)}))
    db.commit()
    return PriceItemReviewResponse(id=item.id, status=item.status, is_active=item.is_active, action="rejected")


@router.post("/admin/verification/{action_id}/resolve", response_model=VerificationResolveResponse)
def resolve_verification_action(
    action_id: UUID,
    request: VerificationResolveRequest,
    db: Session = Depends(get_db),
) -> VerificationResolveResponse:
    action = db.get(VerificationAction, action_id)
    if action is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Verification action not found")
    action.status = VerificationActionStatus.COMPLETED.value
    action.notes = request.notes
    resolved_anomaly = False
    if action.anomaly_flag is not None:
        action.anomaly_flag.resolved = True
        resolved_anomaly = True
    db.commit()
    return VerificationResolveResponse(
        action_id=action.id,
        status=action.status,
        resolved_anomaly=resolved_anomaly,
    )


@router.get("/admin/dashboard", response_model=DashboardResponse)
def dashboard(db: Session = Depends(get_db)) -> DashboardResponse:
    metrics = collect_processing_metrics(db)
    return DashboardResponse(
        import_batches=int(db.scalar(select(func.count(ImportBatch.id))) or 0),
        documents_total=int(db.scalar(select(func.count(PriceDocument.id))) or 0),
        documents_by_status=dict(db.execute(select(PriceDocument.status, func.count(PriceDocument.id)).group_by(PriceDocument.status)).all()),
        open_verification_actions=int(db.scalar(select(func.count(VerificationAction.id)).where(VerificationAction.status == VerificationActionStatus.OPEN.value)) or 0),
        unresolved_anomalies=int(db.scalar(select(func.count(AnomalyFlag.id)).where(AnomalyFlag.resolved.is_(False))) or 0),
        unmatched_candidates=int(db.scalar(select(func.count(MatchingCandidate.id)).where(MatchingCandidate.decision_status == MatchDecisionStatus.UNMATCHED.value)) or 0),
        active_price_items=int(db.scalar(select(func.count(PriceItemVersion.id)).where(PriceItemVersion.is_active.is_(True))) or 0),
        extracted_rows=metrics["extracted_rows"],
        normalized_rows=metrics["normalized_rows"],
        auto_matched=metrics["auto_matched"],
        needs_review=metrics["needs_review"],
        normalization_rate_percent=metrics["normalization_rate_percent"],
    )


@router.get("/admin/reports/quality", response_model=QualityReportResponse)
def quality_report(db: Session = Depends(get_db)) -> QualityReportResponse:
    metrics = collect_processing_metrics(db)
    documents_by_status = dict(db.execute(select(PriceDocument.status, func.count(PriceDocument.id)).group_by(PriceDocument.status)).all())
    return QualityReportResponse(
        generated_at=datetime.now(UTC),
        parsing=documents_by_status,
        matching=dict(db.execute(select(MatchingCandidate.decision_status, func.count(MatchingCandidate.id)).group_by(MatchingCandidate.decision_status)).all()),
        validation=dict(db.execute(select(AnomalyFlag.code, func.count(AnomalyFlag.id)).group_by(AnomalyFlag.code)).all()),
        price_history={
            "active": int(db.scalar(select(func.count(PriceItemVersion.id)).where(PriceItemVersion.is_active.is_(True))) or 0),
            "inactive": int(db.scalar(select(func.count(PriceItemVersion.id)).where(PriceItemVersion.is_active.is_(False))) or 0),
        },
        documents={
            "total": int(db.scalar(select(func.count(PriceDocument.id))) or 0),
            "by_status": documents_by_status,
        },
        extraction={
            "candidate_rows": metrics["extracted_rows"],
            "documents_without_rows": metrics["documents_without_rows"],
        },
        normalization={
            "normalized_rows": metrics["normalized_rows"],
            "recorded_price_items": metrics["recorded_price_items"],
            "auto_matched": metrics["auto_matched"],
            "needs_review": metrics["needs_review"],
            "unmatched": metrics["unmatched"],
            "normalization_rate_percent": metrics["normalization_rate_percent"],
        },
        top_parser_errors=metrics["top_parser_errors"],
    )


@router.get("/admin/files/{file_asset_id}/preview")
def preview_file(file_asset_id: UUID, db: Session = Depends(get_db)) -> FileResponse:
    asset = db.get(FileAsset, file_asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File asset not found")
    path = Path(asset.stored_path).resolve()
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored file not found")
    return FileResponse(path, media_type=asset.mime_type or "application/octet-stream", filename=asset.original_filename)


def clamp_page_size(page_size: int) -> int:
    return max(1, min(page_size, 100))


def page_meta(page: int, page_size: int, total: int) -> PageMeta:
    return PageMeta(page=page, page_size=page_size, total=total, pages=(total + page_size - 1) // page_size if total else 0)


def count_for(db: Session, query) -> int:
    return int(db.scalar(select(func.count()).select_from(query.order_by(None).subquery())) or 0)


def import_batch_summary(batch: ImportBatch) -> ImportBatchSummary:
    return ImportBatchSummary(
        id=batch.id,
        source_type=batch.source_type,
        status=batch.status,
        original_filename=batch.original_filename,
        total_files=batch.total_files,
        processed_files=batch.processed_files,
        failed_files=batch.failed_files,
        warnings=batch.warnings,
        created_at=batch.created_at,
    )


def file_summary(file_asset: FileAsset | None) -> FileAssetSummary | None:
    if file_asset is None:
        return None
    return FileAssetSummary(
        id=file_asset.id,
        original_filename=file_asset.original_filename,
        stored_path=file_asset.stored_path,
        extension=file_asset.extension,
        mime_type=file_asset.mime_type,
        size_bytes=file_asset.size_bytes,
    )


def document_summary(document: PriceDocument) -> PriceDocumentSummary:
    return PriceDocumentSummary(
        id=document.id,
        import_batch_id=document.import_batch_id,
        file_asset_id=document.file_asset_id,
        status=document.status,
        detected_type=document.detected_type,
        progress_percent=document.progress_percent,
        processing_attempts=document.processing_attempts,
        last_error=document.last_error,
        warnings=document.warnings,
        parsed_summary=document.parsed_summary,
        file=file_summary(document.file_asset),
    )


def event_summary(event: ProcessingEvent) -> ProcessingEventSummary:
    return ProcessingEventSummary(
        id=event.id,
        event_type=event.event_type,
        status=event.status,
        message=event.message,
        progress_percent=event.progress_percent,
        payload=event.payload,
        created_at=event.created_at,
    )


def safe_upload_filename(filename: str) -> str:
    return Path(filename).name.strip() or "upload.bin"


def collect_processing_metrics(db: Session) -> dict:
    documents = db.scalars(select(PriceDocument)).all()
    extracted_rows = 0
    normalized_rows = 0
    recorded_price_items = 0
    auto_matched = 0
    needs_review = 0
    unmatched = 0
    documents_without_rows = 0
    errors: dict[str, int] = {}
    for document in documents:
        summary = document.parsed_summary or {}
        extracted = int(summary.get("candidate_rows") or summary.get("row_candidates") or 0)
        normalized = int(summary.get("normalized_rows") or 0)
        extracted_rows += extracted
        normalized_rows += normalized
        recorded_price_items += int(summary.get("recorded_price_items") or 0)
        auto_matched += int(summary.get("auto_matched") or 0)
        needs_review += int(summary.get("needs_review") or 0)
        unmatched += int(summary.get("unmatched") or 0)
        if document.status in {PriceDocumentStatus.PARSED.value, PriceDocumentStatus.NEEDS_REVIEW.value} and normalized == 0:
            documents_without_rows += 1
        if document.last_error:
            errors[document.last_error] = errors.get(document.last_error, 0) + 1
        for warning in summary.get("parser_warnings") or []:
            errors[str(warning)] = errors.get(str(warning), 0) + 1
    rate = round((normalized_rows / extracted_rows) * 100, 2) if extracted_rows else 0.0
    return {
        "extracted_rows": extracted_rows,
        "normalized_rows": normalized_rows,
        "recorded_price_items": recorded_price_items,
        "auto_matched": auto_matched,
        "needs_review": needs_review,
        "unmatched": unmatched,
        "documents_without_rows": documents_without_rows,
        "normalization_rate_percent": rate,
        "top_parser_errors": [
            {"message": message, "count": count}
            for message, count in sorted(errors.items(), key=lambda item: item[1], reverse=True)[:5]
        ],
    }


def process_import_batch_locally(import_batch_id: UUID) -> None:
    with SessionLocal() as db:
        service = WorkerPipelineService(db)
        service.process_batch(
            import_batch_id,
            enqueue_document=lambda price_document_id: service.process_document(UUID(price_document_id)),
        )
