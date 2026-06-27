# Demo Script

## Goal

Show the MedArchive / MedPartners happy path with synthetic data: import a service directory, import a partner price archive, process documents, inspect operational status, and run public search.

## Setup Commands

```bash
cp .env.example .env
python scripts/seed_demo_data.py
make up
make migrate
curl http://localhost:8000/health
```

## Frontend Walkthrough

Open `http://localhost:3000`.

- Public search: `/`
- Admin login UI: `/login`
- Admin dashboard UI: `/dashboard`
- Archive upload UI: `/imports`
- Document status UI: `/documents`
- Verification queue UI: `/verification`
- Unmatched matching UI: `/unmatched`
- Quality report UI: `/quality`

## Import Flow

1. Import the service directory:

   ```bash
   make import-services FILE=/app/data/samples/services.json
   ```

2. Import the partner archive:

   ```bash
   make import-archive FILE=/app/data/samples/archive.zip
   ```

3. Open Swagger at `http://localhost:8000/docs`.

4. Call `POST /admin/login` using `ADMIN_USERNAME` and `ADMIN_PASSWORD` from `.env`, then authorize Swagger with the returned bearer token.

5. Call `GET /admin/import-batches` and copy the latest batch id.

6. Call `POST /admin/import/batches/{import_batch_id}/process` to enqueue document processing.

7. Watch status with:

   ```bash
   curl -H "Authorization: Bearer <token>" "http://localhost:8000/admin/documents?status=parsed"
   curl -H "Authorization: Bearer <token>" "http://localhost:8000/admin/dashboard"
   ```

## Search Flow

1. Search imported services:

   ```bash
   curl "http://localhost:8000/search?q=blood&type=service"
   ```

2. List services:

   ```bash
   curl "http://localhost:8000/services?page=1&page_size=10"
   ```

3. Show the quality report:

   ```bash
   curl -H "Authorization: Bearer <token>" "http://localhost:8000/admin/reports/quality"
   ```

## Visual Flow

Use the frontend pages for the presentation-friendly version of the same workflow:

1. Start at public search.
2. Open a service or partner detail page from the result cards.
3. Move to admin dashboard.
4. Show archive upload, document status, verification, unmatched matching, and quality report screens.

## Fallback Commands

If Redis or the worker is unavailable, process one document synchronously inside the backend container:

```bash
docker compose run --rm backend python ../scripts/reprocess_document.py <price_document_id>
```

To print the quality report without Swagger:

```bash
docker compose run --rm backend python ../scripts/generate_quality_report.py
```

## Expected Talking Points

- Public search and service APIs are unauthenticated read models.
- Admin import, dashboard, file preview, reprocess, verification, and quality endpoints require bearer-token auth.
- Parsers preserve source locators and raw audit output where possible.
- Matching is deterministic-first; optional LLM paths are feature-flagged and disabled by default.
- Synthetic demo data is intentionally small and does not represent real medical records.

## Known Demo Limits

- Frontend screens use mock data where live API wiring is not yet connected.
- Partner APIs derive partners from active price items; there is no dedicated partner table yet.
- Docker Desktop must be running before `make up` can start containers.
- Real attached XLSX/ZIP files still require local approved-data verification.
