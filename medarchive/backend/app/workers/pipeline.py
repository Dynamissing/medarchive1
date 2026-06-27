from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.constants import ImportBatchStatus, PriceDocumentStatus, ProcessingStatus
from app.core.logging import get_logger
from app.db.models import ImportBatch, PriceDocument, ProcessingEvent
from app.services.document_processing import DocumentProcessingService, UnsupportedDocumentFormatError

logger = get_logger(__name__)


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

        document.status = PriceDocumentStatus.PROCESSING.value
        document.progress_percent = 10
        document.processing_attempts += 1
        document.last_error = None
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
            parsed = self.document_processor.parse_price_document(document)
            summary = {
                "parser_name": parsed.parser_name,
                "parser_format": parsed.parser_format,
                "status": parsed.status,
                "warnings": parsed.warnings,
                "tables": len(parsed.tables),
                "row_candidates": len(parsed.row_candidates),
                "pdf_row_candidates": len(parsed.pdf_row_candidates),
            }
            document.status = PriceDocumentStatus.PARSED.value
            document.progress_percent = 100
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

    def fail_document(self, document: PriceDocument, exc: Exception) -> DocumentProcessingOutcome:
        message = str(exc)
        document.status = PriceDocumentStatus.FAILED.value
        document.progress_percent = 100
        document.last_error = message
        document.parsed_summary = {}
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

    def refresh_batch_progress(self, import_batch_id: UUID) -> None:
        batch = self.db.get(ImportBatch, import_batch_id)
        if batch is None:
            return
        documents = self.db.scalars(select(PriceDocument).where(PriceDocument.import_batch_id == import_batch_id)).all()
        batch.total_files = len(documents)
        batch.processed_files = sum(1 for document in documents if document.status == PriceDocumentStatus.PARSED.value)
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
