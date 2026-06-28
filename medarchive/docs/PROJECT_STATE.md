# Project State

## Status

Backend foundation, service-directory import, archive ZIP ingestion, parser selection, spreadsheet extraction, DOCX extraction, text-PDF extraction, OCR-assisted PDF extraction, deterministic extracted-row normalization, layered matching, validation, anomaly flagging, price versioning, Celery/Redis worker orchestration, read-only public search APIs, admin operational APIs, and simple admin bearer-token auth are in place. The repository has the expected scaffold, a minimal FastAPI app, authenticated admin endpoints, public service/partner/search endpoints, settings, structured logging, SQLAlchemy setup, Alembic migrations, XLSX/JSON service import support, ZIP storage registration, spreadsheet parsers, DOCX parser, text-PDF parser, isolated OCR-candidate parser, parse-ready row normalization utilities, deterministic-first matching, history tables, and structured processing events.

## Implemented

- Repository structure.
- Minimal environment and Docker Compose examples.
- Minimal FastAPI backend app factory.
- `GET /health` endpoint.
- pydantic-settings configuration.
- JSON structured logging.
- SQLAlchemy base/session setup.
- Empty initial Alembic migration.
- `services` and `service_synonyms` database models and migration.
- XLSX/JSON service directory import service and CLI command.
- Deterministic service synonym generation.
- `import_batches`, `file_assets`, and `price_documents` database models and migration.
- ZIP archive upload endpoint and path-based CLI import.
- Local filesystem storage with SHA-256 hashing and basic file type detection.
- Parser registry and placeholder parser adapters for XLSX, XLS, DOCX, PDF text, and PDF OCR candidates.
- `ParsedDocumentResult` schema for future extraction output.
- XLSX extraction and XLS conversion-to-XLSX parsing with spreadsheet row candidates.
- DOCX paragraph/table extraction with raw text, table row locators, tracked-change detection, and LibreOffice fallback path.
- Text-PDF extraction with raw page text, page-located row candidates, fragmented-line assembly, multi-page continuation handling, and confidence scoring.
- OCR-assisted PDF extraction with pdf2image, Tesseract `rus+kaz+eng`, preprocessing, OCR audit artifacts, and low-confidence row marking.
- Deterministic row normalization for spreadsheet, DOCX, and PDF parser candidates.
- Price-item-ready payloads with cleaned service names, normalized source codes, parsed amounts/currencies/dates, partner hints, category filtering, warnings, and preserved locators.
- Layered matching engine with exact, synonym, source-code hint, RapidFuzz, token-overlap scoring, explanation payloads, configurable thresholds, and persisted review candidates.
- Optional sentence-transformers and OpenRouter hooks are feature-flagged and disabled by default.
- Validation rules for positive prices, nonresident/resident ordering, non-empty service names, future effective dates, non-KZT preservation, and no-recognizable-data errors.
- Price item versioning with active/inactive rows, supersede chains, deterministic duplicate handling, and >50% price-change anomaly flags.
- `anomaly_flags` and `verification_actions` models and migration.
- Celery/Redis worker pipeline for batch processing, document processing, retryable transient failures, per-document reprocessing, progress updates, and `processing_events`.
- Admin enqueue endpoints for batch processing and document reprocessing.
- Read-only public endpoints for services, partners, partner-service relationships, and search.
- PostgreSQL `pg_trgm`/FTS search indexes for service and partner search when running on PostgreSQL.
- Admin endpoints for service import, import batches, documents, document reprocessing, verification, unmatched candidates, matching, price item verify/reject, dashboard metrics, quality report metrics, and local file preview.
- `POST /admin/login` with environment-configured username/password and signed bearer tokens for admin endpoints.
- Lightweight synthetic backend fixtures and tests covering parser formats, matching/validation branches, API smoke paths, and archive processing happy path.
- Production-like local Docker Compose stack for Postgres, Redis, backend, worker, and frontend placeholder.
- Make targets for stack control, migrations, imports, and tests.
- Minimal static frontend placeholder.
- Operational scripts for import, synchronous reprocessing, quality metrics, and synthetic demo data generation.
- Planning documentation.

## Not Implemented

- Full production review workflows.
- Dedicated partner table; partner read models are derived from active price versions.
- Full frontend user workflows.
- External OCR APIs, production LLM review, and live currency conversion providers.
- Multi-user authentication, RBAC, and audit behavior.
- Real approved golden-data import has not been verified in this environment.

## Immediate Next Step

Start Docker Desktop, run the local Compose stack, generate synthetic demo data with `python scripts/seed_demo_data.py`, run migrations, import the demo service directory and archive, then process the batch and verify public search plus admin dashboard/quality report responses.
