# Implementation Log

## 2026-06-28 - Locale-Aware UI And SEO Translation Architecture

Implemented a compatibility-preserving i18n and SEO localization update for the frontend.

Created files:

- `frontend/messages/ru.json`
- `frontend/messages/kz.json`
- `frontend/messages/en.json`
- `frontend/i18n/locales.ts`
- `frontend/components/locale-boundary.tsx`
- `frontend/app/[locale]/page.tsx`
- `frontend/scripts/sync-translations.mjs`

Modified files:

- `frontend/i18n/index.tsx`
- `frontend/i18n/types.ts`
- `frontend/lib/seo.ts`
- `frontend/app/layout.tsx`
- `frontend/app/[locale]/search/page.tsx`
- `frontend/app/[locale]/services/complete-blood-count/page.tsx`
- `frontend/app/[locale]/clinics/clinic-07/page.tsx`
- `frontend/components/language-switcher.tsx`
- `frontend/components/copy-link-button.tsx`
- `frontend/components/search-metadata-updater.tsx`
- `frontend/app/robots.ts`
- `frontend/app/sitemap.ts`
- `frontend/package.json`
- Public service/search/clinic metadata wrappers

Behavior changes:

- Added locale message files as the gradual migration source while preserving the existing `useI18n()` and flat-key dictionary fallback.
- Public `/ru`, `/kz`, and `/en` routes now bind UI locale from the URL instead of localStorage.
- The language switcher changes localized public URL segments and preserves query parameters; admin/private routes continue using local UI state only.
- SEO metadata now uses localized message templates for home, search, service, clinic, login, and shared site metadata.
- `/kz` remains the route convention while Kazakh SEO uses `kk_KZ`; runtime document language is set to `kk-KZ`.
- Sitemap now includes localized home/search/service/clinic routes and excludes arbitrary query URLs.
- Added optional translation sync tooling with `i18n:check`, `i18n:sync`, and `i18n:translate`; OpenRouter is optional and not required for build/runtime.

Commands run:

- `npm run i18n:check`
- `npm run typecheck`
- `npm run lint`
- `npm run build`
- Node-based exported HTML checks for `out/ru/search.html`, `out/kz/search.html`, and `out/en/search.html`
- `Get-Content frontend\out\robots.txt`
- `Get-Content frontend\out\sitemap.xml`

Verification results:

- `npm run i18n:check` passed for `ru`, `kz`, and `en`.
- Frontend typecheck passed.
- Frontend lint passed.
- Frontend production build passed and generated 27 static routes.
- Exported search HTML for `ru`, `kz`, and `en` contains localized title, description, canonical, Open Graph, and Twitter tags.
- Exported `/kz/search.html` keeps `/kz/search` canonical/alternate URLs and includes `og:locale` as `kk_KZ`.
- Exported `robots.txt` disallows admin/private pages.
- Exported `sitemap.xml` includes localized public pages.

Known limitations:

- Because the app still has a single root `app/layout.tsx`, exported source HTML contains the root `lang="ru"` attribute for all routes. A small inline script and the i18n provider set `document.documentElement.lang` to `kk-KZ` or `en` immediately on localized routes; a full source-HTML fix would require restructuring the root route layout.
- With `output: "export"`, arbitrary query-specific search metadata is still a client-side progressive enhancement, not pre-rendered static HTML.
- Machine-generated translations are optional and can be imperfect for medical terms; Kazakh and English medical terminology should be reviewed later.

## 2026-06-27 - Frontend SEO Metadata And Shareable Search URLs

Added focused frontend SEO and share-link support for MedPrice public routes.

Created files:

- `frontend/lib/seo.ts`
- `frontend/components/copy-link-button.tsx`
- `frontend/components/search-metadata-updater.tsx`
- `frontend/public/og/medprice.svg`
- `frontend/features/auth/login-page-client.tsx`
- `frontend/app/[locale]/search/page.tsx`
- `frontend/app/[locale]/services/complete-blood-count/page.tsx`
- `frontend/app/[locale]/clinics/clinic-07/page.tsx`
- `frontend/app/robots.ts`
- `frontend/app/sitemap.ts`

Modified files:

- `.env.example`
- `frontend/app/layout.tsx`
- `frontend/app/page.tsx`
- `frontend/app/login/page.tsx`
- `frontend/app/dashboard/page.tsx`
- `frontend/app/imports/page.tsx`
- `frontend/app/documents/page.tsx`
- `frontend/app/verification/page.tsx`
- `frontend/app/unmatched/page.tsx`
- `frontend/app/quality/page.tsx`
- `frontend/app/services/complete-blood-count/page.tsx`
- `frontend/app/partners/clinic-07/page.tsx`
- `frontend/features/public-search/public-search-home.tsx`
- `frontend/features/service-detail/service-detail-page.tsx`
- `frontend/features/partner-detail/partner-detail-page.tsx`

Behavior changes:

- Added global and page-specific SEO metadata with canonical URLs, Open Graph tags, Twitter cards, robots flags, and hreflang alternates.
- Added static locale search routes for `/ru/search`, `/kz/search`, and `/en/search`.
- Added locale service and clinic routes for the existing demo service and clinic detail pages.
- Search page now restores `q`, `city`, `serviceId`, `clinicId`, `source`, and `sort` from URL parameters where supported by current mock data.
- Search input, city selector, and category filter update the URL query string without a full page reload.
- Added copy/share actions for the active search URL, service result cards, clinic result cards, and detail pages.
- Added minimal static `robots.txt` and `sitemap.xml` generation while excluding admin/private pages.
- Added `NEXT_PUBLIC_SITE_URL` to `.env.example` with local fallback.

Commands run:

- `npm run typecheck`
- `npm run lint`
- `npm run build`
- `Select-String -Path frontend\out\ru\search.html -Pattern '<title>|description|og:title|og:image|canonical'`

Verification results:

- Frontend typecheck passed.
- Frontend lint passed.
- Frontend production build passed and generated 24 static pages including `/ru/search`, `/kz/search`, `/en/search`, localized service/clinic routes, `robots.txt`, and `sitemap.xml`.
- Exported `/ru/search.html` contains title, description, canonical, Open Graph, Twitter, and alternate-language tags.

Known limitations:

- Because the frontend uses `output: "export"`, query-specific search metadata for `/ru/search?q=...` is updated client-side after load; the static HTML contains generic search metadata.
- Search and detail pages still use existing mock frontend data; no backend contracts or database schema were changed.
- The OG image is a simple static SVG asset rather than generated per service or clinic.

## 2026-06-27 - Bootstrap Skeleton

Created initial MedArchive / MedPartners repository scaffold.

Created files:

- Backend package placeholders and configuration under `backend/`.
- Frontend package placeholders and configuration under `frontend/`.
- Data and prompt placeholder files.

Modified files:

- `README.md`
- `.env.example`
- `docker-compose.yml`
- `Makefile`
- `docs/ARCHITECTURE.md`
- `docs/PROJECT_STATE.md`
- `docs/TASKS.md`
- `docs/IMPLEMENTATION_LOG.md`
- `docs/API.md`
- `docs/PARSING_STRATEGY.md`
- `docs/MATCHING_STRATEGY.md`
- `docs/DEMO_SCRIPT.md`
- `docs/PRESENTATION_OUTLINE.md`
- `docs/QUALITY_REPORT.md`
- Existing empty script placeholders in `scripts/`

Behavior changes:

- No runtime business behavior was implemented.
- Placeholder commands and configs now document intended development entry points.

Commands run:

- `rg --files`
- `Get-ChildItem -Force`
- `Get-Content -Raw README.md`
- `Get-Content -Raw docs\ARCHITECTURE.md`
- `Get-Content -Raw docs\TASKS.md`
- `Get-Content -Raw docs\IMPLEMENTATION_LOG.md`
- `git rev-parse --show-toplevel`
- `Get-ChildItem -Recurse -Force -Depth 2`
- `tree -L 3`
- `git diff --stat`
- `python -m pytest`
- `Get-ChildItem -Recurse -Depth 3`
- Removed generated pytest and Python cache directories under `backend/`
- Parsed `frontend/package.json` and `backend/pyproject.toml` with Python standard libraries

Verification results:

- Initial inspection showed the scaffold existed but files were empty.
- `git rev-parse --show-toplevel` reported that this directory is not currently a Git repository.
- `tree -L 3` was rejected by Windows `tree` as unsupported syntax.
- `git diff --stat` could not run because the directory is not currently a Git repository.
- PowerShell depth-limited tree inspection confirmed the requested scaffold exists.
- `python -m pytest` from `backend/` passed with `1 passed`.
- `frontend/package.json` and `backend/pyproject.toml` parsed successfully.

Known limitations:

- APIs, parsing, matching, data models, UI screens, and production commands remain placeholders.
- No real or sensitive medical data is included.

## 2026-06-27 - Backend Foundation

Implemented the FastAPI backend foundation for MedArchive / MedPartners.

Created files:

- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/script.py.mako`
- `backend/alembic/versions/49a1ec5a36b7_initial_empty_migration.py`
- `backend/alembic/versions/.gitkeep`
- `backend/app/core/config.py`
- `backend/app/core/logging.py`
- `backend/app/core/constants.py`
- `backend/app/db/session.py`
- `backend/app/db/base.py`
- `backend/app/db/models/__init__.py`
- `backend/app/api/routes/__init__.py`
- `backend/app/api/routes/health.py`
- `backend/tests/test_health.py`

Modified files:

- `.env.example`
- `.gitignore`
- `README.md`
- `docs/API.md`
- `docs/ARCHITECTURE.md`
- `docs/PROJECT_STATE.md`
- `docs/TASKS.md`
- `docs/IMPLEMENTATION_LOG.md`
- `backend/pyproject.toml`
- `backend/app/main.py`

Removed files:

- `backend/tests/test_placeholder.py`

Behavior changes:

- FastAPI app factory now creates the backend app.
- `GET /health` returns service health metadata with HTTP 200.
- Settings load from environment and `.env` using pydantic-settings.
- SQLAlchemy base metadata, session factory, and Alembic migration environment are configured for PostgreSQL.
- JSON structured logging is configured at app startup.
- Initial shared status enums were added without domain models.

Commands run:

- `python -m pip install -e ".[dev]"`
- `alembic revision -m "initial empty migration"`
- `docker --version`
- `docker compose ps`
- `alembic upgrade head`
- `pytest -q`
- `python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`
- `Invoke-RestMethod http://127.0.0.1:8000/health`
- `python -m compileall -q app tests`
- Removed generated pytest and Python cache directories under `backend/`
- Removed generated editable-install metadata under `backend/medarchive_backend.egg-info`

Verification results:

- Editable backend install succeeded after package discovery was scoped to `app*`.
- Empty Alembic migration was generated successfully.
- `pytest -q` passed with `1 passed`.
- `python -m uvicorn app.main:app --reload` started successfully.
- `GET /health` returned `{"status":"ok","service":"MedArchive / MedPartners","environment":"local","version":"0.1.0"}`.
- Settings check confirmed defaults load and `APP_DEBUG=true` parses correctly.
- Python compile check passed.

Known limitations:

- `alembic upgrade head` could not be applied in this environment because the configured local PostgreSQL role/database is unavailable.
- Docker is installed, but Docker Desktop's Linux engine was not running, so the Compose PostgreSQL service could not be started.
- No domain models, parsing logic, matching logic, or business endpoints were implemented.

## 2026-06-27 - Service Directory Import

Implemented the service directory import pipeline for XLSX and JSON.

Created files:

- `backend/app/db/models/service.py`
- `backend/app/services/admin/__init__.py`
- `backend/app/services/admin/service_directory_import.py`
- `backend/alembic/versions/b7f9a1a3c2d4_create_services_tables.py`
- `backend/tests/unit/test_service_import.py`

Modified files:

- `backend/pyproject.toml`
- `backend/app/db/base.py`
- `backend/app/db/models/__init__.py`
- `scripts/import_services.py`
- `docs/PARSING_STRATEGY.md`
- `docs/MATCHING_STRATEGY.md`
- `docs/ARCHITECTURE.md`
- `docs/PROJECT_STATE.md`
- `docs/TASKS.md`
- `docs/IMPLEMENTATION_LOG.md`

Behavior changes:

- Added `services` and `service_synonyms` SQLAlchemy models and Alembic migration.
- Added XLSX/JSON service directory reader for organizer columns `ID`, `Специальность`, `Code`, `Name_ru`, and `TarificatrCode`.
- Spreadsheet error cells are captured as row warnings instead of failing the import.
- Rows without service names are skipped with warnings.
- Service rows store generated UUID ids, source row id, tariff code, category/specialty, raw data, warnings, normalized fields, and deterministic synonyms.
- Import is idempotent for the same batch and source hash.
- Duplicate service names and codes are allowed.

Commands run:

- `python -m pip install -e ".[dev]"`
- `pytest -q backend/tests/unit/test_service_import.py`
- `pytest -q`
- `python -m compileall -q app tests`
- `alembic heads`
- `git diff --stat`
- `git status --short`
- `git diff --stat`
- `git status --short`
- `alembic upgrade head --sql`
- `alembic upgrade head`
- `python scripts\import_services.py --help`
- Synthetic XLSX import through `scripts/import_services.py` against a temporary SQLite database
- Removed generated pytest, Python cache, and editable-install metadata under `backend/`

Verification results:

- Focused service import tests passed with `4 passed`.
- Full backend test suite passed with `5 passed`.
- Python compile check passed.
- Alembic reports `b7f9a1a3c2d4` as the current head.
- `alembic upgrade head --sql` generated SQL for `services` and `service_synonyms`.
- Synthetic CLI import created `2` services and `4` synonyms in a temporary SQLite database and logged a spreadsheet error cell as a warning.

Known limitations:

- No attached real services XLSX/JSON file was present in the workspace, so the real-directory PostgreSQL import could not be run.
- `alembic upgrade head` could not be applied to PostgreSQL because the configured local PostgreSQL role/database is unavailable.
- Docker Desktop's Linux engine is not running, so the Compose PostgreSQL service could not be started.
- Matching engine, document/archive parsing, and business API endpoints remain unimplemented.

## 2026-06-27 - Archive Upload And Storage

Implemented ZIP archive ingestion and local file storage registration.

Created files:

- `backend/app/db/models/archive.py`
- `backend/app/services/admin/archive_import.py`
- `backend/app/api/routes/admin.py`
- `backend/alembic/versions/c3d4e5f6a7b8_create_archive_import_tables.py`
- `backend/tests/integration/test_archive_import.py`

Modified files:

- `.env.example`
- `.gitignore`
- `backend/pyproject.toml`
- `backend/app/core/config.py`
- `backend/app/core/constants.py`
- `backend/app/db/models/__init__.py`
- `backend/app/main.py`
- `scripts/import_archive.py`
- `docs/API.md`
- `docs/ARCHITECTURE.md`
- `docs/PARSING_STRATEGY.md`
- `docs/PROJECT_STATE.md`
- `docs/TASKS.md`
- `docs/IMPLEMENTATION_LOG.md`

Behavior changes:

- Added `import_batches`, `file_assets`, and `price_documents` SQLAlchemy models and migration.
- Added local filesystem storage under configurable `FILE_STORAGE_ROOT`.
- Added SHA-256 hashing for original ZIP files and extracted members.
- Added ZIP extraction with unsafe member path skipping.
- Added basic file type detection by extension and MIME guess.
- Added `POST /admin/import/archive` for ZIP upload.
- Added `scripts/import_archive.py` for path-based ZIP import.
- Each extracted member creates a pending `price_documents` row.
- Original ZIP and extracted member files are preserved.
- Duplicate file hashes are allowed and do not crash import.

Commands run:

- `python -m pip install -e ".[dev]"`
- `pytest -q backend/tests/integration/test_archive_import.py`
- `pytest -q`
- `python -m compileall -q app tests`
- `alembic heads`
- `alembic upgrade head --sql`
- `alembic upgrade head`
- Synthetic ZIP import through `scripts/import_archive.py` against a temporary SQLite database
- Endpoint upload of `C:\Users\Beknazar\Downloads\Telegram Desktop\Хакатон.zip` through `POST /admin/import/archive` against a temporary SQLite database

Verification results:

- Focused archive integration tests passed with `2 passed`.
- Full backend test suite passed with `7 passed`.
- Python compile check passed.
- Alembic reports `c3d4e5f6a7b8` as the current head.
- `alembic upgrade head --sql` generated SQL for archive import tables.
- Synthetic CLI import created `1` import batch, `3` file assets, and `2` price documents.
- Real `Хакатон.zip` endpoint upload against temporary SQLite returned HTTP `201`, created `1` import batch, `11` file assets, and `10` pending price documents.

Known limitations:

- `alembic upgrade head` could not be applied to PostgreSQL because the configured local PostgreSQL role/database is unavailable.
- Docker Desktop's Linux engine is not running, so the Compose PostgreSQL service could not be started.
- Real `Хакатон.zip` was verified through the upload endpoint against temporary SQLite, not PostgreSQL.
- File contents are not parsed yet, and Celery/background processing was not started.

## 2026-06-27 - Parser Abstraction And File-Type Detection

Implemented parser selection infrastructure without real extraction.

Created files:

- `backend/app/utils/file_detection.py`
- `backend/app/schemas/parsed_document.py`
- `backend/app/services/parsers/__init__.py`
- `backend/app/services/parsers/base.py`
- `backend/app/services/parsers/adapters.py`
- `backend/app/services/parsers/registry.py`
- `backend/app/services/document_processing.py`
- `backend/tests/unit/test_parser_registry.py`

Modified files:

- `backend/app/services/admin/archive_import.py`
- `docs/PARSING_STRATEGY.md`
- `docs/ARCHITECTURE.md`
- `docs/PROJECT_STATE.md`
- `docs/TASKS.md`
- `docs/IMPLEMENTATION_LOG.md`

Behavior changes:

- Added shared file-type detection for XLSX, XLS, DOCX, and PDF files.
- Added simple PDF text-marker heuristic to route PDFs to `pdf_text` or `pdf_ocr_candidate`.
- Added parser registry and placeholder parser adapters for `xlsx`, `xls`, `docx`, `pdf_text`, and `pdf_ocr_candidate`.
- Added typed `ParsedDocumentResult` schema.
- Added document processing service that chooses a parser from stored file metadata and local file path.
- Archive ingestion now stores parser-format names in `price_documents.detected_type`.

Commands run:

- `pytest -q backend/tests/unit/test_parser_registry.py`
- `pytest -q`
- `python -m compileall -q app tests`
- Parsed `backend/pyproject.toml` with Python standard libraries

Verification results:

- Focused parser registry tests passed with `4 passed`.
- Full backend test suite passed with `11 passed`.
- Python compile check passed.
- Unit tests cover parser selection for the real archive formats: PDF, DOCX, XLSX, and XLS.

Known limitations:

- Parser adapters return explicit placeholder `ParsedDocumentResult` objects only.
- No XLSX, XLS, DOCX, PDF text extraction, or OCR implementation was added.
- PDF text availability uses simple byte-marker heuristics and is not a final parser-quality signal.

## 2026-06-27 - XLSX/XLS Parser

Implemented spreadsheet extraction for XLSX and XLS conversion flow.

Created files:

- `backend/app/services/parsers/spreadsheet.py`
- `backend/tests/unit/test_xlsx_parser.py`
- `backend/tests/unit/test_xls_conversion_parser.py`

Modified files:

- `backend/app/schemas/parsed_document.py`
- `backend/app/services/parsers/adapters.py`
- `backend/tests/unit/test_parser_registry.py`
- `docs/PARSING_STRATEGY.md`
- `docs/ARCHITECTURE.md`
- `docs/PROJECT_STATE.md`
- `docs/TASKS.md`
- `docs/IMPLEMENTATION_LOG.md`

Behavior changes:

- XLSX parser now extracts typed spreadsheet row candidates instead of returning a placeholder.
- XLS parser converts `.xls` files to `.xlsx` with local LibreOffice before applying the XLSX parser.
- Spreadsheet extraction supports multiple sheets, delayed headers, two-row headers, merged cells, category rows, empty rows, multiple price columns, and source coordinates.
- Row candidates preserve raw values, normalized header-value mappings, source sheet, row index, source cell coordinates, category context, and all detected price variants.
- Category rows are used as context and are not emitted as normal price items.

Commands run:

- `pytest -q backend/tests/unit/test_xlsx_parser.py`
- `pytest -q backend/tests/unit/test_xls_conversion_parser.py`
- `pytest -q`
- `python -m compileall -q app tests`
- Manual extraction check against real `Хакатон.zip` XLSX workbooks from `C:\Users\Beknazar\Downloads\Telegram Desktop`
- Checked for local `soffice`/`libreoffice` executable

Verification results:

- Focused XLSX parser tests passed with `2 passed`.
- Focused XLS conversion parser test passed with `1 passed`.
- Full backend test suite passed with `14 passed`.
- Python compile check passed.
- Real clinic 6 XLSX workbook produced `5086` row candidates.
- Real clinic 8 XLSX workbook produced `1929` row candidates.

Known limitations:

- Real clinic 7 `.xls` parsing could not be verified because LibreOffice is not installed on this machine.
- XLS conversion is covered by a unit test with a monkeypatched conversion result, not a real LibreOffice subprocess run.
- Spreadsheet extraction only emits row candidates; service matching, validation rules, and normalization remain unimplemented.

## 2026-06-27 - DOCX Parser

Implemented DOCX extraction.

Created files:

- `backend/app/services/parsers/docx.py`
- `backend/tests/unit/test_docx_parser.py`

Modified files:

- `backend/pyproject.toml`
- `backend/app/services/parsers/adapters.py`
- `backend/tests/unit/test_parser_registry.py`
- `docs/PARSING_STRATEGY.md`
- `docs/ARCHITECTURE.md`
- `docs/PROJECT_STATE.md`
- `docs/TASKS.md`
- `docs/IMPLEMENTATION_LOG.md`

Behavior changes:

- DOCX parser now extracts paragraphs, tables, raw text, and table row locators.
- Table row locators use `table:{table_index}:row:{row_index}`.
- Tracked-change detection scans DOCX OOXML for WordprocessingML change tags.
- LibreOffice fallback conversion is attempted when tracked changes are present or direct extraction quality is poor.
- Fallback failures are recorded as warnings while preserving direct extraction output.

Commands run:

- `python -m pip install -e ".[dev]"`
- `pytest -q backend/tests/unit/test_docx_parser.py`
- `pytest -q`
- `python -m compileall -q app tests`
- Parsed `backend/pyproject.toml` with Python standard libraries
- Manual extraction check against real clinic 1 DOCX from `Хакатон.zip`

Verification results:

- Focused DOCX parser tests passed with `2 passed`.
- Full backend test suite passed with `16 passed`.
- Python compile check passed.
- Real clinic 1 DOCX produced `1` table, `2726` table rows, `0` paragraphs, `160329` raw-text characters, and no tracked changes.

Known limitations:

- LibreOffice fallback path is implemented but could not be subprocess-verified because LibreOffice is not installed on this machine.
- DOCX extraction produces structured rows and raw text only; service matching, validation, and normalization remain unimplemented.
- OCR and PDF extraction were not implemented in this phase.

## 2026-06-27 - Text PDF Parser

Implemented text-PDF extraction.

Created files:

- `backend/app/services/parsers/pdf_text.py`
- `backend/tests/unit/test_pdf_text_parser.py`

Modified files:

- `backend/pyproject.toml`
- `backend/app/schemas/parsed_document.py`
- `backend/app/services/parsers/adapters.py`
- `docs/PARSING_STRATEGY.md`
- `docs/ARCHITECTURE.md`
- `docs/PROJECT_STATE.md`
- `docs/TASKS.md`
- `docs/IMPLEMENTATION_LOG.md`

Behavior changes:

- `PdfTextParser` now extracts text-PDF content instead of returning a placeholder.
- PyMuPDF is used as the primary text extractor.
- pdfplumber is used as a secondary fallback when PyMuPDF extraction is empty or materially weaker.
- Raw page text is preserved in `metadata.page_text` and joined into `extracted_text`.
- PDF row candidates are returned with page number, row index, page locator, raw lines, inferred values, and confidence.
- Fragmented lines, line-wrapped service names, and simple multi-page continuations are assembled before row candidate creation.
- Extraction confidence is scored from text volume, row density, and row-level signals.

Commands run:

- `python -m pip install -e ".[dev]"`
- `pytest -q backend/tests/unit/test_pdf_text_parser.py`
- `pytest -q`
- `python -m compileall -q app tests`
- Parsed `backend/pyproject.toml` with Python standard libraries
- Manual extraction checks against real clinic 1, clinic 4, and clinic 5 PDFs from `Хакатон.zip`

Verification results:

- Focused text-PDF parser tests passed with `2 passed`.
- Full backend test suite passed with `18 passed`.
- Python compile check passed.
- Real clinic 1 PDF produced `85` pages, `3914` row candidates, confidence `0.962`, and `178588` raw-text characters.
- Real clinic 4 PDF produced `31` pages, `523` row candidates, confidence `0.993`, and `55457` raw-text characters.
- Real clinic 5 PDF produced `15` pages, `244` row candidates, confidence `0.97`, and `13772` raw-text characters.

Known limitations:

- OCR was not implemented or run.
- PDF extraction emits row candidates only; service matching, validation, and normalization remain unimplemented.
- Row assembly and confidence scoring are heuristic and will need tuning after downstream validation.

## 2026-06-27 - Scanned PDF OCR Parser

Implemented isolated OCR-assisted PDF extraction.

Created files:

- `backend/app/services/parsers/pdf_ocr.py`
- `backend/tests/unit/test_pdf_ocr_parser.py`

Modified files:

- `backend/pyproject.toml`
- `backend/app/schemas/parsed_document.py`
- `backend/app/services/parsers/adapters.py`
- `backend/tests/unit/test_parser_registry.py`
- `docs/PARSING_STRATEGY.md`
- `docs/ARCHITECTURE.md`
- `docs/PROJECT_STATE.md`
- `docs/TASKS.md`
- `docs/IMPLEMENTATION_LOG.md`

Behavior changes:

- `PdfOcrCandidateParser` now runs an isolated OCR path instead of returning a placeholder.
- Added OCR-candidate PDF heuristics based on text scarcity and image-heavy pages.
- Added pdf2image conversion path for PDF pages.
- Added image preprocessing with grayscale, autocontrast, median filtering, and thresholding.
- Added local Tesseract OCR invocation with `rus+kaz+eng`.
- Preserved OCR audit artifacts in parsed output metadata.
- Added OCR confidence capture at page and line level when available.
- Added OCR row candidate extraction using the existing PDF row assembly logic.
- Added low-confidence row marking.
- Missing local OCR tools now produce a typed failed result with a warning instead of an unhandled exception.

Commands run:

- `python -m pip install -e ".[dev]"`
- `pytest -q backend/tests/unit/test_pdf_ocr_parser.py`
- `pytest -q`
- `python -m compileall -q app tests`
- Parsed `backend/pyproject.toml` with Python standard libraries
- Checked for local `tesseract`, `pdfinfo`, and `pdftoppm`
- Manual OCR invocation against real clinic 3 PDF from `Хакатон.zip`

Verification results:

- Focused OCR parser tests passed with `3 passed`.
- Full backend test suite passed with `21 passed`.
- Python compile check passed.
- OCR unit tests verify row extraction, OCR artifacts, line confidence capture, and low-confidence row marking.
- Manual clinic 3 OCR invocation returned a typed failed result because Poppler is not installed locally.

Known limitations:

- Real OCR could not run in this environment because Poppler tools are not installed.
- Tesseract language availability for `rus+kaz+eng` was not verified locally.
- OCR row extraction remains heuristic and emits candidates only; matching, validation, and normalization remain unimplemented.
- No external OCR APIs are used.

## 2026-06-27 - Extraction Row Normalization And Value Parsing

Implemented deterministic parser-row normalization utilities.

Created files:

- `backend/app/services/normalization/__init__.py`
- `backend/app/services/normalization/row_normalization.py`
- `backend/tests/unit/test_row_normalization.py`

Modified files:

- `docs/PARSING_STRATEGY.md`
- `docs/MATCHING_STRATEGY.md`
- `docs/ARCHITECTURE.md`
- `docs/PROJECT_STATE.md`
- `docs/TASKS.md`
- `docs/IMPLEMENTATION_LOG.md`

Behavior changes:

- Added typed `PriceItemPayload` and `PriceItemAmountPayload` structures for price-items-ready intermediate data.
- Added deterministic service name cleaning, source code normalization, price parsing, currency parsing, effective date parsing, partner name inference, and category/non-data row detection.
- Added normalization paths for spreadsheet row candidates, DOCX table rows, and PDF row candidates.
- Preserved source locators from parser output, including spreadsheet sheet/row/cell data, DOCX table row locators, and PDF page row locators.
- Kept normalization separate from service matching, anomaly/versioning logic, and database persistence.

Commands run:

- `pytest -q backend/tests/unit/test_row_normalization.py`
- `pytest -q`
- `python -m compileall -q app tests`
- `git diff --stat`
- `git status --short`

Verification results:

- Focused row normalization tests passed with `6 passed`.
- Full backend test suite passed with `27 passed`.
- Python compile check passed.
- `git diff --stat` and `git status --short` could not run because this workspace does not contain Git repository metadata.

Known limitations:

- Normalization uses deterministic heuristics only.
- Partner names and effective dates are nullable when they cannot be inferred from filenames or content.
- Cleaned values are returned as price-item-ready payloads; normalized price item database persistence is not implemented yet.
- Service matching, anomaly/versioning logic, and external LLM calls remain out of scope.

## 2026-06-27 - Layered Matching Engine

Implemented deterministic-first service matching with persisted review candidates.

Created files:

- `backend/app/db/models/matching.py`
- `backend/app/services/matching/__init__.py`
- `backend/app/services/matching/engine.py`
- `backend/alembic/versions/d4e5f6a7b8c9_create_matching_candidates.py`
- `backend/tests/unit/test_matching_engine.py`

Modified files:

- `.env.example`
- `backend/pyproject.toml`
- `backend/app/core/config.py`
- `backend/app/core/constants.py`
- `backend/app/db/models/__init__.py`
- `docs/API.md`
- `docs/ARCHITECTURE.md`
- `docs/MATCHING_STRATEGY.md`
- `docs/PROJECT_STATE.md`
- `docs/TASKS.md`
- `docs/IMPLEMENTATION_LOG.md`

Behavior changes:

- Added `matching_candidates` persistence for manual review and unmatched candidate records.
- Added configurable thresholds for `auto_accept`, `needs_review`, and `unmatched`.
- Added exact normalized-name matching, deterministic synonym matching, source-code/tariff-code hint scoring, RapidFuzz scoring, and token-overlap scoring.
- Added structured match result and explanation payloads with methods, reasons, component scores, and warnings.
- Added disabled-by-default feature flags for sentence-transformers rerank and OpenRouter fallback.
- OpenRouter fallback state is cached by row payload hash when configured; baseline operation does not require external LLM calls.

Commands run:

- `python -m pip install -e ".[dev]"`
- `pytest -q backend/tests/unit/test_matching_engine.py`
- `pytest -q`
- `python -m compileall -q app tests`
- Parsed `backend/pyproject.toml` with Python standard libraries
- `alembic heads`
- `DATABASE_URL=sqlite+pysqlite:///./tmp_alembic_match.db alembic upgrade head`
- Sample in-memory service import and matching run against attached `Справочник услуг.xlsx`

Verification results:

- Focused matching tests passed with `6 passed`.
- Full backend test suite passed with `33 passed`.
- Python compile check passed.
- Alembic head is `d4e5f6a7b8c9`.
- Temporary SQLite Alembic upgrade applied all migrations through `create matching candidates`.
- Real attached service directory sample imported `1281` services with `5` skipped rows and `1445` warnings from known spreadsheet error cells.
- Three sample normalized extracted-row probes matched imported services with `auto_accept`, score `1.0`, and `exact_name_code_hint`.

Known limitations:

- Matching is exposed as a backend service, not as an API endpoint.
- Normalized price-item database persistence is still not implemented.
- Sentence-transformers rerank is feature-flagged but no local reranker is configured yet.
- OpenRouter fallback remains optional, disabled by default, and is not required for baseline tests.
- Scoring thresholds are conservative defaults and should be tuned with reviewed real data.

## 2026-06-27 - Validation, Anomalies, Price Versioning, And Deduplication

Implemented deterministic validation and price history services.

Created files:

- `backend/app/db/models/history.py`
- `backend/app/services/validation/__init__.py`
- `backend/app/services/validation/rules.py`
- `backend/app/services/validation/price_history.py`
- `backend/alembic/versions/e5f6a7b8c9d0_create_validation_history_tables.py`
- `backend/tests/unit/test_validation_rules.py`
- `backend/tests/unit/test_price_versioning.py`

Modified files:

- `.env.example`
- `backend/app/core/config.py`
- `backend/app/core/constants.py`
- `backend/app/db/models/__init__.py`
- `docs/API.md`
- `docs/ARCHITECTURE.md`
- `docs/MATCHING_STRATEGY.md`
- `docs/PROJECT_STATE.md`
- `docs/TASKS.md`
- `docs/QUALITY_REPORT.md`
- `docs/IMPLEMENTATION_LOG.md`

Behavior changes:

- Added `price_item_versions` for active/inactive price history with previous-version and superseded-by links.
- Added `anomaly_flags` and `verification_actions` persistence for validation failures and review tasks.
- Added positive numeric price validation, non-empty service-name validation, future effective-date warnings, nonresident/resident price ordering checks, and no-recognizable-data errors.
- Added deterministic duplicate detection for partner/service/date/source-code/amount-label keys.
- Added >50% price-change anomaly detection when a new active version supersedes a prior active version.
- Added local-configurable currency conversion hooks through `CURRENCY_CONVERSION_RATES`, preserving non-KZT original amounts when no conversion rate is configured.
- Prior accepted price versions are superseded and marked inactive rather than overwritten.

Commands run:

- `pytest -q backend/tests/unit/test_validation_rules.py`
- `pytest -q backend/tests/unit/test_price_versioning.py`
- `pytest -q`
- `python -m compileall -q app tests`
- `alembic heads`
- `DATABASE_URL=sqlite+pysqlite:///./tmp_alembic_validation.db alembic upgrade head`
- `git diff --stat`

Verification results:

- Focused validation rule tests passed with `4 passed`.
- Focused price versioning tests passed with `5 passed`.
- Full backend test suite passed with `42 passed`.
- Python compile check passed.
- Alembic head is `e5f6a7b8c9d0`.
- Temporary SQLite Alembic upgrade applied all migrations through `create validation history tables`.
- `git diff --stat` could not run because this workspace does not contain Git repository metadata.

Known limitations:

- Validation/history is exposed as backend services, not admin endpoints.
- Currency conversion is local and static; no external FX provider is implemented.
- Duplicate detection depends on normalized partner/service/date/source-code/amount-label keys and may need tuning with reviewed real data.
- Verification actions are created as open records only; no workflow UI or assignment automation is implemented.

## 2026-06-27 - Celery Redis Worker Pipeline And Reprocessing

Implemented Celery/Redis task orchestration for document processing.

Created files:

- `backend/app/workers/__init__.py`
- `backend/app/workers/celery_app.py`
- `backend/app/workers/pipeline.py`
- `backend/app/workers/tasks.py`
- `backend/alembic/versions/f6a7b8c9d0e1_create_worker_processing_events.py`
- `backend/tests/integration/test_worker_pipeline.py`

Modified files:

- `.env.example`
- `README.md`
- `docker-compose.yml`
- `backend/pyproject.toml`
- `backend/app/api/routes/admin.py`
- `backend/app/core/config.py`
- `backend/app/core/constants.py`
- `backend/app/db/models/archive.py`
- `backend/app/db/models/__init__.py`
- `docs/API.md`
- `docs/ARCHITECTURE.md`
- `docs/PROJECT_STATE.md`
- `docs/TASKS.md`
- `docs/IMPLEMENTATION_LOG.md`

Behavior changes:

- Added Redis configuration and Celery app setup.
- Added Celery tasks for batch processing and single-document processing.
- Added batch enqueue endpoint `POST /admin/import/batches/{import_batch_id}/process`.
- Added document reprocess endpoint `POST /admin/import/documents/{price_document_id}/reprocess`.
- Added `processing_events` structured event logging.
- Added progress, attempt count, last-error, and parsed-summary fields to `price_documents`.
- Added processed/failed counters to `import_batches`.
- Document processing is idempotent for already parsed documents unless forced.
- Batch processing isolates per-document failures so one failed document does not stop other documents.
- Transient `ConnectionError` and `TimeoutError` failures are configured for Celery retry with backoff.
- Docker Compose now includes Redis.

Commands run:

- `python -m pip install -e ".[dev]"`
- `pytest -q backend/tests/integration/test_worker_pipeline.py`
- `pytest -q`
- `python -m compileall -q app tests`
- `alembic heads`
- `DATABASE_URL=sqlite+pysqlite:///./tmp_alembic_worker.db alembic upgrade head`
- Parsed `backend/pyproject.toml` with Python standard libraries
- `git diff --stat`

Verification results:

- Focused worker pipeline integration tests passed with `3 passed`.
- Full backend test suite passed with `45 passed`.
- Python compile check passed.
- Alembic head is `f6a7b8c9d0e1`.
- Temporary SQLite Alembic upgrade applied all migrations through `create worker processing events`.
- `backend/pyproject.toml` parsed successfully.
- `git diff --stat` could not run because this workspace does not contain Git repository metadata.

Known limitations:

- Worker orchestration parses documents and records progress/events; it does not yet persist extracted row contents.
- Matching and validation services are not automatically run by the worker pipeline yet.
- Dedicated status query endpoints are not implemented.
- Redis/Celery worker execution was configured and tested through service-level integration tests; no long-running worker process was started in this environment.

## 2026-06-27 - Public API Search Endpoints

Implemented read-only public service, partner, and search endpoints.

Created files:

- `backend/app/api/routes/public.py`
- `backend/alembic/versions/a7b8c9d0e1f2_add_public_search_indexes.py`
- `backend/tests/api/test_public_api.py`

Modified files:

- `backend/app/main.py`
- `docs/API.md`
- `docs/ARCHITECTURE.md`
- `docs/PROJECT_STATE.md`
- `docs/TASKS.md`
- `docs/IMPLEMENTATION_LOG.md`

Behavior changes:

- Added `GET /services` with pagination, sorting, category filtering, specialty filtering, and text search across services and synonyms.
- Added `GET /services/{id}/partners` for active partners linked to a service through current price item versions.
- Added `GET /partners` with pagination, sorting, and partner-name search.
- Added `GET /partners/{id}/services` for active services and latest price metadata by derived partner id.
- Added `GET /search` across services and partners with typed OpenAPI response schemas.
- Added PostgreSQL-only `pg_trgm` and FTS indexes for public search migrations; SQLite and other dialects no-op this migration.
- Kept all public endpoints read-only and unauthenticated.

Commands run:

- `pytest -q backend/tests/api/test_public_api.py`
- `pytest -q`
- `python -m compileall -q app tests`
- `alembic heads`
- `DATABASE_URL=sqlite+pysqlite:///./tmp_alembic_public_api.db alembic upgrade head`

Verification results:

- Focused public API tests passed with `6 passed`.
- Full backend test suite passed with `51 passed`.
- Python compile check passed.
- Alembic head is `a7b8c9d0e1f2`.
- Temporary SQLite Alembic upgrade applied all migrations through `add public search indexes`.

Known limitations:

- Partner records are derived from active `price_item_versions.partner_name`; no dedicated partner table exists yet.
- Runtime search uses portable SQL `ILIKE`-style filtering for testability; PostgreSQL FTS/trigram support is provided as indexes for PostgreSQL deployments.
- Public endpoints expose read models only and do not include admin review workflow actions.

## 2026-06-27 - Admin API Endpoints

Implemented typed admin operational endpoints without changing database models.

Created files:

- `backend/tests/api/test_admin_api.py`

Modified files:

- `backend/app/api/routes/admin.py`
- `docs/API.md`
- `docs/ARCHITECTURE.md`
- `docs/PROJECT_STATE.md`
- `docs/TASKS.md`
- `docs/IMPLEMENTATION_LOG.md`

Behavior changes:

- Added `POST /admin/import/services` for XLSX/JSON service directory import.
- Added `GET /admin/import-batches` for archive batch summaries.
- Added `GET /admin/documents` and `GET /admin/documents/{id}` for document status, file metadata, parsed summary, warnings, and processing events.
- Added canonical `POST /admin/documents/{id}/reprocess` while preserving the previous import-scoped reprocess route.
- Added `GET /admin/verification` for verification actions joined with anomaly details.
- Added `GET /unmatched` for unmatched matching candidates.
- Added `POST /match` for matching one normalized row payload.
- Added `POST /admin/price-items/{id}/verify` and `POST /admin/price-items/{id}/reject`.
- Added `GET /admin/dashboard` operational metrics.
- Added `GET /admin/reports/quality` aggregate quality metrics.
- Added `GET /admin/files/{id}/preview` to serve stored local file assets by id.

Commands run:

- `pytest -q backend/tests/api/test_admin_api.py`
- `pytest -q`
- `python -m compileall -q app tests`
- `alembic heads`

Verification results:

- Focused admin API tests passed with `5 passed`.
- Full backend test suite passed with `56 passed`.
- Python compile check passed.
- Alembic head remains `a7b8c9d0e1f2`; no migration was required for this phase.
- `git diff --stat` reported 6 tracked files changed with 628 insertions and 14 deletions; `backend/tests/api/test_admin_api.py` is untracked and therefore not included in that stat.
- `git status --short` showed modified admin/docs files and untracked `backend/tests/api/test_admin_api.py`.

Known limitations:

- Admin endpoints do not implement authentication or authorization.
- File preview serves only known stored file assets by id, but no content redaction is implemented.
- Verify/reject actions are minimal status operations and do not implement a full review workflow.
- Dashboard and quality report payloads are aggregate read models, not finalized product analytics.

## 2026-06-27 - Simple Admin Authentication

Implemented environment-configured admin login with signed bearer-token protection for admin routes.

Created files:

- `backend/app/core/auth.py`
- `backend/tests/api/test_admin_auth.py`

Modified files:

- `.env.example`
- `backend/app/api/routes/admin.py`
- `backend/app/core/config.py`
- `backend/app/main.py`
- `backend/tests/api/test_admin_api.py`
- `backend/tests/integration/test_archive_import.py`
- `backend/tests/integration/test_worker_pipeline.py`
- `docs/API.md`
- `docs/ARCHITECTURE.md`
- `docs/PROJECT_STATE.md`
- `docs/TASKS.md`
- `docs/IMPLEMENTATION_LOG.md`

Behavior changes:

- Added `POST /admin/login` returning a signed bearer token.
- Added admin credentials and token settings from environment: `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `ADMIN_TOKEN_SECRET`, and `ADMIN_TOKEN_TTL_SECONDS`.
- Added router-level bearer-token guard for admin endpoints.
- Left public endpoints open, including `/health`, `/services`, `/partners`, and `/search`.
- OpenAPI now exposes HTTP bearer authentication for Swagger admin route testing.
- Existing admin API and integration tests were updated to authenticate before calling protected endpoints.

Commands run:

- `pytest -q backend/tests/api/test_admin_auth.py`
- `pytest -q backend/tests/api/test_admin_api.py`
- `pytest -q backend/tests/api/test_admin_auth.py backend/tests/api/test_admin_api.py`
- `pytest -q backend/tests/integration/test_archive_import.py backend/tests/integration/test_worker_pipeline.py`
- `pytest -q`
- `python -m compileall -q app tests`
- `alembic heads`

Verification results:

- Focused admin auth tests passed with `5 passed`.
- Focused admin API tests passed with `5 passed`.
- Combined affected admin API/auth tests passed with `10 passed`.
- Affected archive/worker integration tests passed with `5 passed`.
- Full backend test suite passed with `61 passed`.
- Python compile check passed.
- Alembic head remains `a7b8c9d0e1f2`; no migration was required for this phase.
- `git diff --stat` reported 11 tracked files changed with 764 insertions and 15 deletions, including previously uncommitted admin-route changes.
- `git status --short` showed new untracked files `backend/app/core/auth.py`, `backend/tests/api/test_admin_api.py`, and `backend/tests/api/test_admin_auth.py`.

Known limitations:

- This is single-admin authentication only; no multi-user RBAC or user database is implemented.
- Tokens are signed with a shared environment secret and cannot be revoked individually before expiry.
- Default demo credentials must be changed outside local development.

## 2026-06-27 - Backend Tests And Sample Fixtures

Strengthened backend test coverage with lightweight synthetic fixtures and additional branch/integration tests.

Created files:

- `backend/tests/fixtures/__init__.py`
- `backend/tests/fixtures/generators.py`
- `backend/tests/fixtures/README.md`
- `backend/tests/unit/test_parser_fixtures.py`
- `backend/tests/unit/test_matching_validation_branches.py`
- `backend/tests/integration/test_archive_processing_happy_path.py`

Modified files:

- `docs/PARSING_STRATEGY.md`
- `docs/PROJECT_STATE.md`
- `docs/TASKS.md`
- `docs/IMPLEMENTATION_LOG.md`

Behavior changes:

- Added synthetic fixture generators for XLSX, DOCX, text PDF, scanned-PDF, OCR data, and ZIP archive samples.
- Added parser fixture smoke coverage across XLSX, DOCX, text PDF, and OCR-candidate PDF paths.
- Added matching branch coverage for unmatched candidate persistence.
- Added validation branch coverage for document-level no-data issues and local currency conversion.
- Added archive processing happy-path integration coverage from ZIP import through synchronous worker processing.
- Documented fixture-generation rules in `backend/tests/fixtures/README.md`.

Commands run:

- `pytest -q backend/tests/unit/test_parser_fixtures.py backend/tests/unit/test_matching_validation_branches.py`
- `pytest -q backend/tests/integration/test_archive_processing_happy_path.py`
- `pytest -q`
- `python -m compileall -q app tests`
- `alembic heads`

Verification results:

- Focused parser/matching/validation fixture tests passed with `3 passed`.
- Focused archive processing happy-path test passed with `1 passed`.
- Full backend test suite passed with `65 passed`.
- Python compile check passed.
- Alembic head remains `a7b8c9d0e1f2`; no migration was required for this phase.

Known limitations:

- Fixtures are synthetic and intentionally small; they do not replace approved real-file regression samples.
- OCR tests mock local OCR tooling and do not require Poppler or Tesseract language packs in CI.
- The archive processing happy path verifies parser orchestration and events, not downstream matching/validation persistence.

## 2026-06-27 - Docker Compose And Local Run Scripts

Added a production-like local developer stack and convenience Make targets.

Created files:

- `.dockerignore`
- `backend/Dockerfile`
- `frontend/index.html`

Modified files:

- `README.md`
- `Makefile`
- `docker-compose.yml`
- `docs/PROJECT_STATE.md`
- `docs/TASKS.md`
- `docs/IMPLEMENTATION_LOG.md`

Behavior changes:

- Docker Compose now defines `postgres`, `redis`, `backend`, `worker`, and `frontend` services.
- Backend and worker use the same Python image and explicit environment wiring.
- Frontend serves a lightweight static placeholder through Nginx on port `3000`.
- Added persistent Docker volumes for Postgres and local file storage.
- Added Make targets: `up`, `down`, `migrate`, `import-services`, `import-archive`, and `run-tests`.
- README quickstart now documents Compose startup, migrations, local URLs, test command, and one-command import flow.

Commands run:

- `docker compose config`
- `docker compose up -d --build`
- `pytest -q`
- `python -m compileall -q app tests`

Verification results:

- `docker compose config` passed and rendered the full stack configuration.
- `docker compose up -d --build` could not start because Docker Desktop's Linux engine pipe was unavailable on this machine.
- Backend test suite passed with `65 passed`.
- Python compile check passed.

Known limitations:

- Backend/frontend availability could not be confirmed because the Docker engine was not running in this environment.
- The frontend service is a static placeholder, not a product UI.
- Make import targets expect `FILE` paths that are visible inside the backend container, usually under `/app`.

## 2026-06-27 - Final Integration Hardening

Hardened demo readiness with small API, script, and documentation fixes.

Created files:

- None. Generated demo artifacts under `data/samples/` during verification were removed after smoke testing because `scripts/seed_demo_data.py` can recreate them.

Modified files:

- `README.md`
- `backend/app/api/routes/admin.py`
- `docs/API.md`
- `docs/ARCHITECTURE.md`
- `docs/DEMO_SCRIPT.md`
- `docs/PROJECT_STATE.md`
- `docs/TASKS.md`
- `docs/IMPLEMENTATION_LOG.md`
- `frontend/README.md`
- `scripts/generate_quality_report.py`
- `scripts/reprocess_document.py`
- `scripts/seed_demo_data.py`

Behavior changes:

- Admin list endpoints now validate `page` and `page_size` through FastAPI `Query` metadata and expose `status` as the documented status filter.
- `scripts/seed_demo_data.py` now creates a synthetic service directory JSON, demo XLSX price workbook, and ZIP archive for local demo imports.
- `scripts/generate_quality_report.py` now prints aggregate parsing, matching, validation, and price-history metrics as JSON.
- `scripts/reprocess_document.py` now synchronously resets and processes one price document by UUID for local fallback demos.
- README, API docs, project state, task list, frontend notes, and demo script were updated to reflect the current backend and executable demo flow.

Commands run:

- `python scripts\seed_demo_data.py`
- `python -m compileall -q app tests ..\scripts`
- `docker compose config --quiet`
- `pytest -q`
- Manual in-memory demo smoke: service import, archive import, synchronous batch processing, `/health`, and `/search?q=blood&type=service`
- `docker compose up -d --build`
- `git diff --stat`
- `git status --short`

Verification results:

- Demo generator created `services.json`, `demo_partner_prices.xlsx`, and `archive.zip` successfully during verification.
- Compile check passed.
- Docker Compose configuration validation passed.
- Full backend test suite passed with `65 passed`.
- Manual in-memory demo smoke imported 3 services, processed 1 archive document to `parsed`, produced 3 XLSX row candidates, returned `/health` 200, and returned one public service search result for `blood`.
- `docker compose up -d --build` could not start because Docker Desktop's Linux engine pipe was unavailable on this machine.
- `git diff --stat` reported 20 tracked files changed with 1326 insertions and 76 deletions, including changes from previous uncommitted phases.

Known limitations:

- Live backend/frontend container availability could not be confirmed because Docker Desktop was not running.
- Frontend remains a static placeholder, not a full review UI.
- The demo data is synthetic; real attached XLSX/ZIP files still require approved-data verification on a running local stack.
- Generated demo files are not committed and should be recreated with `python scripts/seed_demo_data.py` before running the documented import flow.

## 2026-06-28 - Manual testing roadmap

Created files:

- `docs/MANUAL_TESTING_ROADMAP.md`

Files read:

- `README.md`
- `.env.example`
- `docker-compose.yml`
- `Makefile`
- `docs/PROJECT_STATE.md`
- `docs/TASKS.md`
- `docs/API.md`
- `docs/DEMO_SCRIPT.md`
- `docs/IMPLEMENTATION_LOG.md`
- Backend route/model files under `backend/app`
- Frontend route/component/package files under `frontend`
- Helper scripts under `scripts`

Behavior changes:

- None. Documentation-only change.

Verification performed:

- Inspected actual startup commands, Docker services, Make targets, frontend routes, backend API routes, model table names, scripts, and documented demo flow.
- Created a Russian manual QA roadmap covering project startup, test data, public pages, search, admin pages, import/parser flow, API checks, database SQL checks, multilingual testing, responsive QA, error states, demo readiness, risks, go/no-go criteria, known limitations, and recommended future automated tests.

Known limitations:

- No runtime tests were executed for this documentation-only update.
- The roadmap marks frontend mock/live API gaps and unverified real attached data imports as testing risks based on the current project documentation and code inspection.

## 2026-06-28 - Remove frontend placeholder data and connect admin login

Created files:

- `frontend/features/dashboard/data.ts`
- `frontend/features/documents/data.ts`
- `frontend/features/partner-detail/data.ts`
- `frontend/features/quality/data.ts`
- `frontend/features/service-detail/data.ts`
- `frontend/features/unmatched/data.ts`
- `frontend/features/verification/data.ts`

Modified files:

- `.env.example`
- `.gitignore`
- `docker-compose.yml`
- `backend/app/core/config.py`
- `backend/app/main.py`
- Frontend public/admin pages and components under `frontend/app`, `frontend/components`, and `frontend/features`
- `frontend/i18n/dictionaries.ts`
- `frontend/messages/*.json`
- `frontend/app/sitemap.ts`
- `docs/MANUAL_TESTING_ROADMAP.md`

Removed files:

- `frontend/features/*/mock-data.ts` placeholder data files
- `frontend/features/public-search/mock-data.ts`

Behavior changes:

- Removed displayed placeholder/demo records from dashboard, documents, archive uploads, verification, unmatched matching, quality report, public search, service detail, and clinic detail screens.
- Replaced fake rows, prices, ZIP names, clinic names, quality metrics, result cards, and manual fake loading controls with honest empty states or disabled controls.
- Archive upload no longer simulates successful progress; it reports that frontend upload API wiring is not connected yet.
- Admin login now calls the real backend `POST /admin/login`, stores the returned bearer token in `localStorage`, and redirects to `/dashboard` only after a successful response.
- Added `NEXT_PUBLIC_API_BASE_URL` and `CORS_ORIGINS` local configuration.
- Added FastAPI CORS middleware for configured frontend origins.
- Removed demo service/clinic routes from sitemap and changed their metadata/content to neutral empty states.
- Added generated frontend artifacts to `.gitignore`.

Commands run:

- `rg` checks for placeholder terms in frontend source and exported `frontend/out`
- `npm run typecheck`
- `npm run lint`
- `npm run i18n:check`
- `npm run build`
- `python -m compileall -q app`
- `pytest -q`
- `docker compose config --quiet`

Verification results:

- Frontend typecheck passed.
- Frontend lint passed.
- i18n key structure check passed.
- Next static export build passed.
- Backend compile check passed.
- Backend test suite passed with `65 passed`.
- Docker Compose config validation passed.
- Grep checks found no remaining visible frontend placeholder terms such as fake clinic names, fake ZIP names, `mock`, or demo metrics outside generated/ignored artifacts.

Known limitations:

- Most frontend admin/public data screens now show empty states because live API adapters are still not implemented for those pages.
- Archive upload from the frontend is intentionally not wired yet; real archive import still works through Swagger or CLI.
- Admin bearer token is stored in localStorage for hackathon simplicity and should be revisited for production security.

## 2026-06-28 - P0 frontend-backend wiring

Created files:

- `docs/FRONTEND_BACKEND_WIRING_AUDIT.md`
- `frontend/lib/api.ts`

Modified files:

- `frontend/components/login-form.tsx`
- `frontend/features/public-search/public-search-home.tsx`
- `frontend/features/dashboard/dashboard-page.tsx`
- `frontend/features/documents/documents-page.tsx`
- `frontend/features/upload/archive-upload-form.tsx`
- `frontend/features/quality/quality-report-page.tsx`
- `frontend/features/unmatched/unmatched-page.tsx`
- `frontend/features/verification/verification-page.tsx`
- `frontend/i18n/dictionaries.ts`
- `docs/MANUAL_TESTING_ROADMAP.md`
- `docs/FRONTEND_BACKEND_WIRING_AUDIT.md`

Removed files:

- `frontend/features/dashboard/data.ts`
- `frontend/features/documents/data.ts`
- `frontend/features/partner-detail/data.ts`
- `frontend/features/quality/data.ts`
- `frontend/features/service-detail/data.ts`
- `frontend/features/unmatched/data.ts`
- `frontend/features/verification/data.ts`

Behavior changes:

- Added a shared frontend API helper using `NEXT_PUBLIC_API_BASE_URL`, bearer token attachment, consistent error parsing, and 401 handling.
- Connected localized search pages to real `GET /search` for non-empty `q` while preserving unsupported `city` params in the URL.
- Connected dashboard, documents, archive upload/import batches, quality report, unmatched queue, and verification queue pages to real backend endpoints.
- Archive upload now sends multipart field `file` to `POST /admin/import/archive` and no longer fakes successful uploads.
- Admin pages keep honest loading, empty, and error states when backend data or auth is unavailable.
- Removed leftover unused empty frontend data modules from the previous placeholder-removal step.

Commands run:

- `npm run i18n:check`
- `npm run typecheck`
- `npm run lint`
- `npm run build`
- `pytest -q`
- `docker compose config --quiet`
- `rg` checks for old mock imports and fake ZIP/clinic names

Verification results:

- i18n key structure check passed.
- Frontend typecheck passed.
- Frontend lint passed.
- Next static export build passed.
- Backend test suite passed with `65 passed`.
- Docker Compose config validation passed.
- Grep checks found no remaining references to old fake ZIP names, mock imports, or removed queue data constants in frontend source.

Known limitations:

- `/search` backend does not support city filtering yet; frontend preserves `city` in shareable URLs but only sends `q`.
- Service/partner catalog and detail routes remain P1 because stable id/slug mapping needs a separate wiring pass.
- Preview, process/reprocess, match, verify, and reject actions remain P1.
- Admin bearer token remains in localStorage for hackathon simplicity.
