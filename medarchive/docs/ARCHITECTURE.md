# Architecture

## Purpose

MedArchive / MedPartners is intended to help teams organize medical archive files and prepare partner-facing matches between documents, services, and operational workflows.

## Current Components

- Backend: FastAPI application package under `backend/app`.
- Backend configuration: pydantic-settings reads app settings from environment and `.env`.
- Database foundation: SQLAlchemy base metadata, session setup, service directory tables, and Alembic migrations targeting PostgreSQL.
- Service directory import: admin service layer and CLI import XLSX/JSON service directories.
- Archive import: ZIP upload/path import stores original archives, extracted file assets, and pending price document rows.
- Parser abstraction: registry and adapters select parsers for XLSX, XLS, DOCX, PDF text, and PDF OCR-candidate files.
- Spreadsheet parser: XLSX extraction and XLS via LibreOffice conversion produce row candidates without service matching.
- DOCX parser: paragraph/table extraction, raw text preservation, tracked-change detection, and LibreOffice fallback hooks.
- Text-PDF parser: PyMuPDF-first extraction with pdfplumber fallback, page text preservation, row assembly, and confidence scoring.
- OCR PDF parser: isolated pdf2image/Tesseract path for OCR-candidate PDFs, with preprocessing, audit artifacts, and low-confidence row marking.
- Row normalization: deterministic utilities convert parser row candidates into price-item-ready payloads while preserving source locators.
- Matching engine: layered deterministic-first matching service with persisted review candidates and optional disabled-by-default model hooks.
- Validation/history: deterministic validation rules, anomaly flags, verification actions, and active/inactive price item versions with supersede chains.
- Worker pipeline: Celery/Redis orchestration for batch processing, per-document processing, reprocessing, progress updates, and structured processing events.
- Public API: read-only service, partner, and search endpoints.
- API: `GET /health`, `POST /admin/import/archive`, worker enqueue endpoints, and public search endpoints.
- Frontend: placeholder TypeScript application directory under `frontend`.
- Data: local-only fixture and sample directories.
- Scripts: placeholders for import, conversion, reprocessing, demo seeding, and quality reporting.
- Docs: project planning and implementation notes.

## Target Boundaries

- Parsing should live behind backend services or workers.
- Parser selection should stay separate from extraction logic so adapters can be implemented incrementally.
- Row normalization should remain deterministic and auditable before matching.
- Matching should be isolated from API transport code.
- Price history should preserve prior accepted values and supersede versions instead of overwriting rows.
- Worker tasks should be idempotent where practical and isolate per-document failures from batch progress.
- External model-assisted matching must stay optional and explainable.
- Frontend should consume documented API contracts after they are defined.
- Public endpoints should remain read-only and stable.
- Scripts should call reusable backend modules once business logic exists.
- File storage should remain local and configurable until production storage requirements are defined.

## Non-Goals For This Phase

- No production domain API contracts.
- No external OCR APIs.
- No admin review endpoints.
- No real medical data handling.
