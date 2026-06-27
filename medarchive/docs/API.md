# API

## Status

The backend exposes health, archive import, worker enqueue, and read-only public search endpoints. Admin review APIs remain undefined.

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

### `POST /admin/import/archive`

Accepts a multipart ZIP upload and registers archive storage rows. The endpoint preserves the original ZIP, extracts member files into local storage, and creates pending price-document records. It does not parse file contents.

Request:

- Form field `file`: `.zip` file.

Example response:

```json
{
  "import_batch_id": "00000000-0000-0000-0000-000000000000",
  "original_asset_id": "00000000-0000-0000-0000-000000000000",
  "extracted_files": 10,
  "price_documents": 10,
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

## Planned Areas

- Health and readiness checks.
- Document metadata lookup.
- Parsing status.
- Candidate service or partner matches.
- Quality report summaries.

## Matching Note

The backend now has a matching service and `matching_candidates` persistence for review workflows, but no matching API endpoint is defined yet.

## Validation Note

The backend now has validation/history services and persistence for `price_item_versions`, `anomaly_flags`, and `verification_actions`, but no admin review API endpoint is defined yet.

## Worker Note

The backend now has Celery tasks and `processing_events` persistence for document-processing status. Dedicated status query endpoints are not defined yet.

## Search Note

Public search uses portable SQL filtering in application queries and adds PostgreSQL `pg_trgm`/FTS indexes when migrations run on PostgreSQL. Partner records are currently derived from active price item versions rather than a dedicated partner table.

## Contract Policy

API routes, request bodies, and response schemas should be added only when the related backend behavior is implemented and tested. Placeholder names in this document are planning markers, not stable contracts.
