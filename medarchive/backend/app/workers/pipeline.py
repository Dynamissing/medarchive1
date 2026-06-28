from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.constants import AnomalySeverity, ImportBatchStatus, MatchDecisionStatus, PriceDocumentStatus, ProcessingStatus
from app.core.logging import get_logger
from app.db.models import ImportBatch, PriceDocument, ProcessingEvent
from app.schemas.parsed_document import ParsedDocumentResult
from app.services.document_processing import DocumentProcessingService, UnsupportedDocumentFormatError
from app.services.matching.engine import LayeredMatchingEngine
from app.services.normalization.row_normalization import (
    PriceItemPayload,
    normalize_docx_table_row,
    normalize_pdf_candidate,
    normalize_spreadsheet_candidate,
)
from app.services.validation.price_history import PriceHistoryService
from app.services.validation.rules import ValidationIssue

logger = get_logger(__name__)
ROW_SAMPLE_LIMIT = 10
TEXT_PREVIEW_LIMIT = 4000


@dataclass(frozen=True)
class DocumentProcessingOutcome:
    price_document_id: UUID
    status: str
    summary: dict
    error: str | None = None


class WorkerPipelineService:
    def __init__(self, db: Session, document_processor: DocumentProcessingService | None = None) -> None:
        self.db = db
        self.document_processor = document_processor or DocumentProcessingService()

    def process_batch(self, import_batch_id: UUID, *, enqueue_document) -> dict:
        batch = self.db.get(ImportBatch, import_batch_id)
        if batch is None:
            raise ValueError(f"Import batch not found: {import_batch_id}")
        self.log_event(
            event_type="batch_processing_started",
            status=ProcessingStatus.RUNNING.value,
            message="Batch processing started.",
            import_batch_id=batch.id,
            progress_percent=self.batch_progress(batch),
        )
        documents = self.db.scalars(
            select(PriceDocument).where(PriceDocument.import_batch_id == batch.id).order_by(PriceDocument.created_at)
        ).all()
        for document in documents:
            enqueue_document(str(document.id))
        self.refresh_batch_progress(batch.id)
        self.log_event(
            event_type="batch_documents_enqueued",
            status=ProcessingStatus.COMPLETED.value,
            message=f"Enqueued {len(documents)} documents for processing.",
            import_batch_id=batch.id,
            progress_percent=self.batch_progress(batch),
            payload={"documents": len(documents)},
        )
        self.db.commit()
        return {"import_batch_id": str(batch.id), "documents": len(documents)}

    def process_document(self, price_document_id: UUID, *, force: bool = False) -> DocumentProcessingOutcome:
        document = self.db.scalars(
            select(PriceDocument)
            .options(selectinload(PriceDocument.file_asset), selectinload(PriceDocument.import_batch))
            .where(PriceDocument.id == price_document_id)
        ).one_or_none()
        if document is None:
            raise ValueError(f"Price document not found: {price_document_id}")
        if document.status == PriceDocumentStatus.PARSED.value and not force:
            self.log_event(
                event_type="document_processing_skipped",
                status=ProcessingStatus.COMPLETED.value,
                message="Document already parsed; skipped idempotent re-run.",
                import_batch_id=document.import_batch_id,
                price_document_id=document.id,
                progress_percent=document.progress_percent,
            )
            self.db.commit()
            return DocumentProcessingOutcome(document.id, document.status, document.parsed_summary)

        started_at = datetime.now(UTC)
        document.status = PriceDocumentStatus.PROCESSING.value
        document.progress_percent = 10
        document.processing_attempts += 1
        document.last_error = None
        document.processing_started_at = started_at
        document.processing_finished_at = None
        document.parser_stage = "starting"
        self.log_event(
            event_type="document_processing_started",
            status=ProcessingStatus.RUNNING.value,
            message="Document processing started.",
            import_batch_id=document.import_batch_id,
            price_document_id=document.id,
            progress_percent=document.progress_percent,
            payload={"attempt": document.processing_attempts, "force": force},
        )
        self.db.flush()

        try:
            document.parser_stage = "parsing"
            document.progress_percent = 15
            self.db.flush()
            parse_start = time.monotonic()
            parsed = self.document_processor.parse_price_document(document)
            parse_ms = int((time.monotonic() - parse_start) * 1000)

            document.parser_stage = "normalizing"
            document.progress_percent = 40
            self.db.flush()

            summary = self.process_parsed_result(document, parsed)
            summary["parse_duration_ms"] = parse_ms

            document.parser_stage = "completed"
            document.progress_percent = 100
            document.status = (
                PriceDocumentStatus.PARSED.value
                if summary["normalized_rows"] > 0
                else PriceDocumentStatus.NEEDS_REVIEW.value
            )
            finished_at = datetime.now(UTC)
            document.processing_finished_at = finished_at
            duration_ms = int((finished_at - started_at).total_seconds() * 1000)
            summary["processing_started_at"] = started_at.isoformat()
            summary["processing_finished_at"] = finished_at.isoformat()
            summary["duration_ms"] = duration_ms
            summary["parser_stage"] = "completed"
            document.parsed_summary = summary
            document.warnings = list(parsed.warnings)
            self.log_event(
                event_type="document_processing_completed",
                status=ProcessingStatus.COMPLETED.value,
                message="Document processing completed.",
                import_batch_id=document.import_batch_id,
                price_document_id=document.id,
                progress_percent=100,
                payload=summary,
            )
            self.refresh_batch_progress(document.import_batch_id)
            self.db.commit()
            return DocumentProcessingOutcome(document.id, document.status, summary)
        except (UnsupportedDocumentFormatError, FileNotFoundError, RuntimeError, ValueError) as exc:
            return self.fail_document(document, exc)

    def process_parsed_result(self, document: PriceDocument, parsed: ParsedDocumentResult) -> dict:
        rows = normalize_parsed_rows(document, parsed)
        document.parser_stage = "matching"
        document.progress_percent = 60
        self.db.flush()
        history_service = PriceHistoryService(self.db)
        matching_engine = LayeredMatchingEngine(self.db)
        auto_matched = 0
        needs_review = 0
        unmatched = 0
        recorded_price_items = 0
        normalization_warnings: list[str] = []
        row_samples: list[dict] = []

        for i, row in enumerate(rows):
            normalization_warnings.extend(row.warnings)
            match = matching_engine.match_row(row, persist_review=True, price_document_id=document.id)
            service_id = match.candidates[0].service_id if match.candidates and match.decision_status == MatchDecisionStatus.AUTO_ACCEPT else None
            if match.decision_status == MatchDecisionStatus.AUTO_ACCEPT:
                auto_matched += 1
            elif match.decision_status == MatchDecisionStatus.NEEDS_REVIEW:
                needs_review += 1
            else:
                unmatched += 1
            versions = history_service.validate_and_record(row, service_id=service_id, price_document_id=document.id)
            recorded_price_items += len(versions)
            if len(rows) > 0 and i % max(1, len(rows) // 4) == 0:
                document.progress_percent = min(80, 60 + int((i / len(rows)) * 20))
                self.db.flush()
            if len(row_samples) < ROW_SAMPLE_LIMIT:
                row_samples.append(
                    {
                        "service_name": row.service_name,
                        "normalized_service_name": row.normalized_service_name,
                        "partner_name": row.partner_name,
                        "effective_date": row.effective_date.isoformat() if row.effective_date else None,
                        "amounts": [amount.model_dump(mode="json") for amount in row.amounts],
                        "source_locator": row.source_locator,
                        "match_status": match.decision_status.value,
                        "top_candidate": match.candidates[0].model_dump(mode="json") if match.candidates else None,
                        "warnings": row.warnings,
                    }
                )

        if not rows:
            history_service.persist_issue(
                ValidationIssue(
                    code="document_no_parseable_rows",
                    severity=AnomalySeverity.ERROR,
                    message="Document did not produce any normalized price rows.",
                    payload={"price_document_id": str(document.id), "parser_format": parsed.parser_format},
                    action_type="review_document_no_parseable_rows",
                ),
                subject_type="price_document",
                subject_id=str(document.id),
                payload={"warnings": parsed.warnings},
            )

        total_candidates = len(parsed.row_candidates) + len(parsed.pdf_row_candidates) + docx_table_row_count(parsed)
        return {
            "parser_name": parsed.parser_name,
            "parser_format": parsed.parser_format,
            "status": parsed.status,
            "warnings": parsed.warnings,
            "parser_warnings": parsed.warnings,
            "tables": len(parsed.tables),
            "tables_count": len(parsed.tables),
            "row_candidates": len(parsed.row_candidates),
            "pdf_row_candidates": len(parsed.pdf_row_candidates),
            "docx_table_rows": docx_table_row_count(parsed),
            "candidate_rows": total_candidates,
            "normalized_rows": len(rows),
            "recorded_price_items": recorded_price_items,
            "auto_matched": auto_matched,
            "needs_review": needs_review,
            "unmatched": unmatched,
            "matching": {
                "auto_matched": auto_matched,
                "needs_review": needs_review,
                "unmatched": unmatched,
            },
            "normalization_warnings": normalization_warnings[:ROW_SAMPLE_LIMIT],
            "row_samples": row_samples,
            "extracted_text_preview": (parsed.extracted_text or "")[:TEXT_PREVIEW_LIMIT],
        }

    def fail_document(self, document: PriceDocument, exc: Exception) -> DocumentProcessingOutcome:
        message = str(exc)
        finished_at = datetime.now(UTC)
        document.status = PriceDocumentStatus.FAILED.value
        document.progress_percent = 100
        document.last_error = message
        document.processing_finished_at = finished_at
        document.parser_stage = "failed"
        duration_ms = None
        if document.processing_started_at:
            duration_ms = int((finished_at - document.processing_started_at).total_seconds() * 1000)
        document.parsed_summary = {
            "processing_started_at": document.processing_started_at.isoformat() if document.processing_started_at else None,
            "processing_finished_at": finished_at.isoformat(),
            "duration_ms": duration_ms,
            "parser_stage": "failed",
            "error_type": type(exc).__name__,
        }
        warnings = list(document.warnings or [])
        warnings.append(message)
        document.warnings = warnings
        self.log_event(
            event_type="document_processing_failed",
            status=ProcessingStatus.FAILED.value,
            message=message,
            import_batch_id=document.import_batch_id,
            price_document_id=document.id,
            progress_percent=100,
            payload={"error_type": type(exc).__name__},
        )
        self.refresh_batch_progress(document.import_batch_id)
        self.db.commit()
        return DocumentProcessingOutcome(document.id, document.status, {}, error=message)

    def reset_for_reprocess(self, price_document_id: UUID) -> None:
        document = self.db.get(PriceDocument, price_document_id)
        if document is None:
            raise ValueError(f"Price document not found: {price_document_id}")
        document.status = PriceDocumentStatus.PENDING.value
        document.progress_percent = 0
        document.last_error = None
        document.parsed_summary = {}
        document.processing_started_at = None
        document.processing_finished_at = None
        document.parser_stage = None
        self.log_event(
            event_type="document_reprocess_requested",
            status=ProcessingStatus.PENDING.value,
            message="Document reprocess requested.",
            import_batch_id=document.import_batch_id,
            price_document_id=document.id,
            progress_percent=0,
        )
        self.refresh_batch_progress(document.import_batch_id)
        self.db.commit()

    def recover_stale_documents(self, stale_threshold_minutes: int = 10) -> int:
        threshold = datetime.now(UTC) - timedelta(minutes=stale_threshold_minutes)
        stale_documents = self.db.scalars(
            select(PriceDocument).where(
                PriceDocument.status == PriceDocumentStatus.PROCESSING.value,
                PriceDocument.created_at < threshold,
            )
        ).all()
        recovered = 0
        for document in stale_documents:
            document.status = PriceDocumentStatus.PENDING.value
            document.progress_percent = 0
            document.last_error = None
            document.parsed_summary = {}
            document.processing_started_at = None
            document.processing_finished_at = None
            document.parser_stage = None
            self.log_event(
                event_type="document_stale_recovery",
                status=ProcessingStatus.PENDING.value,
                message=f"Document recovered from stale processing (stuck for >{stale_threshold_minutes}min).",
                import_batch_id=document.import_batch_id,
                price_document_id=document.id,
                progress_percent=0,
            )
            self.refresh_batch_progress(document.import_batch_id)
            recovered += 1
        self.db.commit()
        return recovered

    def refresh_batch_progress(self, import_batch_id: UUID) -> None:
        batch = self.db.get(ImportBatch, import_batch_id)
        if batch is None:
            return
        documents = self.db.scalars(select(PriceDocument).where(PriceDocument.import_batch_id == import_batch_id)).all()
        batch.total_files = len(documents)
        batch.processed_files = sum(
            1 for document in documents if document.status in {PriceDocumentStatus.PARSED.value, PriceDocumentStatus.NEEDS_REVIEW.value}
        )
        batch.failed_files = sum(1 for document in documents if document.status == PriceDocumentStatus.FAILED.value)
        if documents and batch.processed_files + batch.failed_files == len(documents):
            batch.status = ImportBatchStatus.COMPLETED.value if batch.failed_files == 0 else ImportBatchStatus.FAILED.value

    def log_event(
        self,
        *,
        event_type: str,
        status: str,
        message: str,
        import_batch_id: UUID | None = None,
        price_document_id: UUID | None = None,
        progress_percent: int | None = None,
        payload: dict | None = None,
    ) -> ProcessingEvent:
        event = ProcessingEvent(
            import_batch_id=import_batch_id,
            price_document_id=price_document_id,
            event_type=event_type,
            status=status,
            message=message,
            progress_percent=progress_percent,
            payload=payload or {},
        )
        self.db.add(event)
        return event

    @staticmethod
    def batch_progress(batch: ImportBatch) -> int:
        if batch.total_files <= 0:
            return 0
        return int(((batch.processed_files + batch.failed_files) / batch.total_files) * 100)


def normalize_parsed_rows(document: PriceDocument, parsed: ParsedDocumentResult) -> list[PriceItemPayload]:
    source_filename = document.file_asset.original_filename if document.file_asset else None
    rows: list[PriceItemPayload] = []
    for candidate in parsed.row_candidates:
        row = normalize_spreadsheet_candidate(candidate, source_filename=source_filename, document_text=parsed.extracted_text)
        if row is not None:
            rows.append(row)
    for candidate in parsed.pdf_row_candidates:
        row = normalize_pdf_candidate(candidate, source_filename=source_filename, document_text=parsed.extracted_text)
        if row is not None:
            rows.append(row)
    for table in parsed.tables:
        for table_row in table.get("rows", []):
            row = normalize_docx_table_row(table_row, source_filename=source_filename, document_text=parsed.extracted_text)
            if row is not None:
                rows.append(row)
    return rows


def docx_table_row_count(parsed: ParsedDocumentResult) -> int:
    return sum(len(table.get("rows", [])) for table in parsed.tables)
