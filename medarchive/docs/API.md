# API

## Status

The backend exposes health, read-only public search endpoints, and authenticated typed admin operational endpoints.

## Implemented Endpoints

### `GET /health`

Returns service health metadata.

Example response:

```json
{
  "status": "ok",
  "service": "MedArchive / MedPartners",
  "environment": "local",
  "version": "0.1.0"
}
```

## Admin Authentication

Admin endpoints require a bearer token from `POST /admin/login`. Public endpoints such as `/health`, `/services`, `/partners`, and `/search` remain open.

### `POST /admin/login`

Authenticates against `ADMIN_USERNAME` and `ADMIN_PASSWORD` from environment settings.

Request:

```json
{
  "username": "admin",
  "password": "admin"
}
```

Example response:

```json
{
  "access_token": "signed-token",
  "token_type": "bearer",
  "expires_in": 3600
}
```

Use the token as `Authorization: Bearer <access_token>`. Swagger/OpenAPI exposes bearer authentication for admin route testing.

### `POST /admin/import/archive`

Accepts a multipart ZIP upload and registers archive storage rows. The endpoint preserves the original ZIP, extracts member files into local storage, creates pending price-document records, and immediately enqueues the import batch for asynchronous parsing.

Request:

- Form field `file`: `.zip` file.

Example response:

```json
{
  "import_batch_id": "00000000-0000-0000-0000-000000000000",
  "original_asset_id": "00000000-0000-0000-0000-000000000000",
  "extracted_files": 10,
  "price_documents": 10,
  "processing_task_id": "celery-task-id",
  "warnings": []
}
```

### `POST /admin/import/services`

Uploads an XLSX or JSON service directory and imports services/synonyms.

Example response:

```json
{
  "batch": "service-import-batch",
  "source_path": "data/storage/service-imports/services.json",
  "rows_seen": 10,
  "imported": 10,
  "updated": 0,
  "skipped": 0,
  "warnings": []
}
```

### `POST /admin/import/batches/{import_batch_id}/process`

Enqueues asynchronous processing for all price documents in an import batch.

Example response:

```json
{
  "task_id": "celery-task-id",
  "target_id": "00000000-0000-0000-0000-000000000000",
  "target_type": "import_batch"
}
```

### `POST /admin/import/documents/{price_document_id}/reprocess`

Resets one price document to pending and enqueues reprocessing.

Example response:

```json
{
  "task_id": "celery-task-id",
  "target_id": "00000000-0000-0000-0000-000000000000",
  "target_type": "price_document"
}
```

The canonical document reprocess endpoint is now `POST /admin/documents/{price_document_id}/reprocess`; the older import-scoped path remains available for compatibility.

### `GET /admin/import-batches`

Lists archive import batches with document counters and warnings.

Query parameters:

- `page`, `page_size`
- `status`: optional import-batch status filter.

### `GET /admin/documents`

Lists price documents with file metadata, parser status, progress, attempts, warnings, and parsed summary.

Query parameters:

- `page`, `page_size`
- `status`: optional price-document status filter.
- `import_batch_id`: optional batch UUID filter.

### `GET /admin/documents/{id}`

Returns one price document plus processing events.

### `GET /admin/verification`

Lists verification actions joined with anomaly details.

Query parameters:

- `page`, `page_size`
- `status`: optional verification-action status filter.

### `GET /unmatched`

Lists unmatched matching candidates for review.

Query parameters:

- `page`, `page_size`

### `POST /match`

Runs the matching engine for one normalized row payload and returns ranked candidates.

### `POST /admin/price-items/{id}/verify`

Marks related anomaly flags resolved and records a completed verification action.

### `POST /admin/price-items/{id}/reject`

Marks a price item inactive and records a completed rejection action.

### `GET /admin/dashboard`

Returns practical operational counts for batches, documents, verification, anomalies, unmatched candidates, and active price items.

### `GET /admin/reports/quality`

Returns aggregate parsing, matching, validation, and price-history quality metrics.

### `GET /admin/files/{id}/preview`

Serves the stored local file for a known file asset id.

### `GET /services`

Lists catalog services with pagination, sorting, and filters.

Query parameters:

- `page`, `page_size`
- `q`
- `category`
- `specialty`
- `sort`: `name`, `code`, `category`, `created_at`
- `direction`: `asc`, `desc`

### `GET /services/{id}/partners`

Lists active partners linked to a service through current price item versions.

### `GET /partners`

Lists active partners derived from current price item versions.

Query parameters:

- `page`, `page_size`
- `q`
- `sort`: `name`, `services`
- `direction`: `asc`, `desc`

### `GET /partners/{id}/services`

Lists active services and latest price metadata for a derived partner id.

### `GET /search`

Searches across services and partners.

Query parameters:

- `q`
- `type`: optional `service` or `partner`
- `page`, `page_size`

## Matching Note

The backend now has a matching service, `matching_candidates` persistence, `/match`, and `/unmatched` review read endpoints.

## Validation Note

The backend now has validation/history services and persistence for `price_item_versions`, `anomaly_flags`, and `verification_actions`, with basic verify/reject admin actions.

## Worker Note

The backend now has Celery tasks and `processing_events` persistence for document-processing status. Dedicated status query endpoints are not defined yet.

## Search Note

Public search uses portable SQL filtering in application queries and adds PostgreSQL `pg_trgm`/FTS indexes when migrations run on PostgreSQL. Partner records are currently derived from active price item versions rather than a dedicated partner table.

## Contract Policy

API routes, request bodies, and response schemas should be added only when the related backend behavior is implemented and tested. Placeholder names in this document are planning markers, not stable contracts.
