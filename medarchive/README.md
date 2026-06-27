# MedArchive / MedPartners

MedArchive is a hackathon project scaffold for a medical archive and partner-service matching tool. The intended product direction is to ingest archive files, normalize metadata, and help match medical documents or service records to partner-facing workflows.

This repository currently contains the scaffold plus a FastAPI backend foundation for archive upload, parser orchestration, deterministic normalization, matching, validation, and worker-driven document processing. Final production APIs and UI flows are intentionally still limited.

## Repository Layout

- `backend/` - FastAPI backend application, worker code, migrations, and tests.
- `frontend/` - Next.js frontend for public search and admin demo screens.
- `docs/` - Architecture, planning, API, parsing, matching, demo, and quality notes.
- `scripts/` - Operational helpers for demo data, imports, reprocessing, and reporting.
- `prompts/` - Prompt drafts and agent handoff notes.
- `data/` - Local sample and fixture directories. Do not commit sensitive medical data.

## Quickstart

Prerequisites:

- Docker Desktop or another Docker Compose compatible runtime.
- `make` for the convenience targets, or run the shown `docker compose` commands directly.

```bash
cp .env.example .env
make up
make migrate
```

Local URLs:

- Backend: `http://localhost:8000`
- Swagger/OpenAPI: `http://localhost:8000/docs`
- Frontend: `http://localhost:3000`
- Postgres: `localhost:5432`
- Redis: `localhost:6379`

The full local stack includes Postgres, Redis, FastAPI backend, Celery worker, and frontend.

Frontend demo routes:

- `/` - public search home.
- `/login` - admin login UI.
- `/dashboard` - admin dashboard UI.
- `/imports` - archive upload UI.
- `/documents` - document status UI.
- `/verification` - verification queue UI.
- `/unmatched` - unmatched matching UI.
- `/quality` - quality report UI.

### Common Commands

```bash
make up
make down
make migrate
make run-tests
```

Equivalent direct commands:

```bash
docker compose up -d --build
docker compose run --rm backend alembic upgrade head
docker compose run --rm backend pytest -q
docker compose down
```

### One-Command Imports

Generate synthetic demo inputs or place approved sample files somewhere under the repository, then run:

```bash
python scripts/seed_demo_data.py
```

```bash
make import-services FILE=/app/data/samples/services.json
make import-archive FILE=/app/data/samples/archive.zip
```

The `FILE` path is evaluated inside the backend container. Files under this repository are mounted at `/app`, so `data/samples/archive.zip` on the host is `/app/data/samples/archive.zip` in the container.

Admin endpoints require login with `ADMIN_USERNAME` and `ADMIN_PASSWORD` from `.env`. Defaults are local-demo only and should be changed before showing a shared environment.

For a quick quality snapshot after processing, run:

```bash
docker compose run --rm backend python ../scripts/generate_quality_report.py
```

## Current Scope

Implemented:

- Initial repository skeleton.
- Backend and frontend package/config files.
- Project documentation outlines.
- FastAPI backend app factory and health endpoint.
- SQLAlchemy and Alembic foundation for PostgreSQL.
- ZIP archive ingestion and file registration.
- Parser registry and extraction paths for XLSX/XLS, DOCX, text PDFs, and OCR-candidate PDFs.
- Deterministic row normalization, matching, validation, anomaly flags, and price versioning services.
- Celery/Redis worker orchestration with processing events.
- Docker Compose local stack and Make targets for setup, migrations, imports, and tests.
- Frontend demo UI screens backed by mock data where live API wiring is not yet connected.

Not implemented:

- Rich production review workflows.
- Live frontend API integration for all screens.
- External OCR, LLM, or currency conversion providers.

## Safety Note

This project may eventually handle medical archive data. Until data governance is defined, use only synthetic or explicitly approved sample data.
