# MedArchive / MedPartners

MedArchive is a hackathon project scaffold for a medical archive and partner-service matching tool. The intended product direction is to ingest archive files, normalize metadata, and help match medical documents or service records to partner-facing workflows.

This repository currently contains the scaffold plus a FastAPI backend foundation for archive upload, parser orchestration, deterministic normalization, matching, validation, and worker-driven document processing. Final production APIs and UI flows are intentionally still limited.

## Repository Layout

- `backend/` - Python backend placeholder.
- `frontend/` - TypeScript frontend placeholder.
- `docs/` - Architecture, planning, API, parsing, matching, demo, and quality notes.
- `scripts/` - Operational script placeholders for later ingestion and reporting tasks.
- `prompts/` - Prompt drafts and agent handoff notes.
- `data/` - Local sample and fixture directories. Do not commit sensitive medical data.

## Quickstart

Prerequisites are not finalized. The expected development stack is Python for the backend and Node.js/TypeScript for the frontend.

```bash
cp .env.example .env
docker compose up -d postgres redis
cd backend
alembic upgrade head
python -m uvicorn app.main:app --reload
pytest -q
```

To run asynchronous processing locally:

```bash
cd backend
celery -A app.workers.celery_app.celery_app worker --loglevel=info
```

The backend exposes `GET /health`, archive upload, and narrow admin processing enqueue endpoints.

## Current Scope

Implemented:

- Initial repository skeleton.
- Placeholder backend and frontend package/config files.
- Project documentation outlines.
- FastAPI backend app factory and health endpoint.
- SQLAlchemy and Alembic foundation for PostgreSQL.
- ZIP archive ingestion and file registration.
- Parser registry and extraction paths for XLSX/XLS, DOCX, text PDFs, and OCR-candidate PDFs.
- Deterministic row normalization, matching, validation, anomaly flags, and price versioning services.
- Celery/Redis worker orchestration with processing events.

Not implemented:

- Production review APIs.
- Frontend user workflows.
- External OCR, LLM, or currency conversion providers.
- User interface workflows.

## Safety Note

This project may eventually handle medical archive data. Until data governance is defined, use only synthetic or explicitly approved sample data.
