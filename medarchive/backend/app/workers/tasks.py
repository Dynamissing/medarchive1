from __future__ import annotations

from uuid import UUID

from celery.exceptions import MaxRetriesExceededError, SoftTimeLimitExceeded
from sqlalchemy import select

from app.db.models import PriceDocument
from app.db.session import SessionLocal
from app.workers.celery_app import celery_app
from app.workers.pipeline import WorkerPipelineService


@celery_app.task(bind=True, autoretry_for=(ConnectionError, TimeoutError), retry_backoff=True, max_retries=3)
def process_batch_task(self, import_batch_id: str) -> dict:
    with SessionLocal() as db:
        service = WorkerPipelineService(db)
        return service.process_batch(UUID(import_batch_id), enqueue_document=process_document_task.delay)


@celery_app.task(
    bind=True,
    max_retries=3,
    retry_backoff=True,
    soft_time_limit=180,
    time_limit=240,
)
def process_document_task(self, price_document_id: str, force: bool = False) -> dict:
    with SessionLocal() as db:
        service = WorkerPipelineService(db)
        try:
            outcome = service.process_document(UUID(price_document_id), force=force)
        except SoftTimeLimitExceeded as exc:
            doc = db.scalars(select(PriceDocument).where(PriceDocument.id == UUID(price_document_id))).one_or_none()
            if doc:
                service.fail_document(doc, exc)
            raise
        except (ConnectionError, TimeoutError) as exc:
            try:
                raise self.retry(exc=exc)
            except MaxRetriesExceededError:
                raise exc
        return {
            "price_document_id": str(outcome.price_document_id),
            "status": outcome.status,
            "summary": outcome.summary,
            "error": outcome.error,
        }


def enqueue_batch_processing(import_batch_id: str):
    return process_batch_task.delay(import_batch_id)


def enqueue_document_reprocessing(price_document_id: str):
    with SessionLocal() as db:
        WorkerPipelineService(db).reset_for_reprocess(UUID(price_document_id))
    return process_document_task.delay(price_document_id, force=True)
