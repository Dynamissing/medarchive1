"""Synchronously reprocess one price document by id."""

from __future__ import annotations

import argparse
from uuid import UUID

from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.workers.pipeline import WorkerPipelineService


def main() -> None:
    parser = argparse.ArgumentParser(description="Reprocess one MedArchive price document.")
    parser.add_argument("price_document_id", type=UUID, help="Price document UUID.")
    args = parser.parse_args()

    configure_logging()
    with SessionLocal() as db:
        pipeline = WorkerPipelineService(db)
        pipeline.reset_for_reprocess(args.price_document_id)
        outcome = pipeline.process_document(args.price_document_id, force=True)

    print(
        "Reprocessed document "
        f"id={outcome.price_document_id} status={outcome.status} "
        f"rows={outcome.summary.get('row_candidates', 0)} "
        f"pdf_rows={outcome.summary.get('pdf_row_candidates', 0)}"
    )
    if outcome.error:
        print(f"error={outcome.error}")


if __name__ == "__main__":
    main()
