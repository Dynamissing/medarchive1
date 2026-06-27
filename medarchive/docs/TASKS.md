# Tasks

## Phase 0: Bootstrap

- [x] Create repository skeleton.
- [x] Add placeholder backend and frontend package/config files.
- [x] Add documentation outlines.
- [x] Add environment and Docker Compose examples.

## Phase 1: Foundations

- [x] Confirm backend foundation stack versions.
- [x] Add FastAPI app factory.
- [x] Add pydantic-settings configuration.
- [x] Add SQLAlchemy base/session setup.
- [x] Initialize Alembic with an empty migration.
- [x] Add `/health` smoke endpoint and test.
- [ ] Define synthetic sample data shape.
- [ ] Draft initial API contract.
- [ ] Add first frontend shell.
- [ ] Add full lint/type-check commands.

## Later Phases

- [x] Implement archive ZIP upload and storage registration.
- [x] Implement parser registry and placeholder parser adapters.
- [x] Implement XLSX parser and XLS conversion parser path.
- [x] Implement DOCX parser.
- [x] Implement text-PDF parser.
- [x] Implement OCR-assisted PDF parser.
- [x] Implement service directory parsing/import strategy.
- [ ] Import the real attached service directory into PostgreSQL.
- [ ] Import the real attached archive ZIP into PostgreSQL.
- [x] Implement spreadsheet row normalization.
- [x] Implement DOCX row normalization.
- [x] Implement PDF row normalization.
- [x] Implement matching strategy.
- [x] Implement validation, anomalies, price versioning, and deduplication.
- [x] Implement Celery/Redis worker pipeline and reprocessing.
- [x] Implement public API search endpoints.
- [ ] Add quality report generation.
- [ ] Prepare demo flow.
