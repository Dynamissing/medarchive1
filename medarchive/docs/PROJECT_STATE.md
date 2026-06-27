# Project State

## Status

Backend foundation, service-directory import, archive ZIP ingestion, parser selection, spreadsheet extraction, DOCX extraction, text-PDF extraction, OCR-assisted PDF extraction, deterministic extracted-row normalization, layered matching, validation, anomaly flagging, price versioning, Celery/Redis worker orchestration, and read-only public search APIs are in place. The repository has the expected scaffold, a minimal FastAPI app, health/admin import endpoints, public service/partner/search endpoints, settings, structured logging, SQLAlchemy setup, Alembic migrations, XLSX/JSON service import support, ZIP storage registration, spreadsheet parsers, DOCX parser, text-PDF parser, isolated OCR-candidate parser, parse-ready row normalization utilities, deterministic-first matching, history tables, and structured processing events.

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
- Minimal frontend TypeScript package placeholder.
- Script placeholders.
- Planning documentation.

## Not Implemented

- Business logic.
- Domain APIs beyond `/health`.
- Domain APIs beyond admin archive import.
- Domain models beyond imported service and archive storage tables.
- External OCR APIs, matching/validation review APIs, admin review workflows, and a dedicated partner table.
- Authentication, authorization, and audit behavior.
- UI screens.

## Immediate Next Step

Install Poppler/Tesseract language packs and LibreOffice for local verification, run PostgreSQL/Redis locally, and then wire review APIs or quality report generation around persisted matches, anomalies, and price history.
