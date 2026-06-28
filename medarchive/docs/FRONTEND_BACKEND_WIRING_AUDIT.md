# Frontend ↔ Backend Wiring Audit

## Scope

This audit covers demo-critical frontend pages and backend endpoints for the MedArchive / MedPartners / MedPrice hackathon project. The current frontend is a static-export Next.js app with client components for interactive data loading. Fake data has been removed; empty states are preferred until real backend data is available.

## Backend Endpoint Inventory

### Public

| Method | Path | Auth | Response shape | Notes |
|---|---|---|---|---|
| `GET` | `/health` | none | `{ status, service, environment, version }` | Backend smoke check. |
| `GET` | `/services` | none | `{ items: ServiceSummary[], meta }` | P1 for service catalog. |
| `GET` | `/services/{service_id}/partners` | none | `{ items: PartnerSummary[], meta }` | P1 service detail wiring. |
| `GET` | `/partners` | none | `{ items: PartnerSummary[], meta }` | P1 partner catalog. |
| `GET` | `/partners/{partner_id}/services` | none | `{ items: PartnerServiceSummary[], meta }` | P1 partner detail wiring. |
| `GET` | `/search` | none | `{ items: SearchResult[], meta }` | Requires non-empty `q`; optional `type=service|partner`. No `city` filter exists backend-side yet. |

### Admin

| Method | Path | Auth | Response shape | Notes |
|---|---|---|---|---|
| `POST` | `/admin/login` | none | `{ access_token, token_type, expires_in }` | Frontend login should call this and store bearer token. |
| `POST` | `/admin/import/archive` | bearer | `{ import_batch_id, original_asset_id, extracted_files, price_documents, warnings }` | Multipart field name must be `file`. |
| `POST` | `/admin/import/services` | bearer | service import summary | P1; not wired in current frontend. |
| `GET` | `/admin/import-batches` | bearer | `{ items: ImportBatchSummary[], meta }` | Used by imports recent list. |
| `GET` | `/admin/documents` | bearer | `{ items: PriceDocumentSummary[], meta }` | Used by documents table. |
| `GET` | `/admin/documents/{id}` | bearer | `PriceDocumentDetail` | P1 details/reprocess UI. |
| `POST` | `/admin/import/batches/{id}/process` | bearer | task summary | P1 action. |
| `POST` | `/admin/documents/{id}/reprocess` | bearer | task summary | P1 action. |
| `GET` | `/admin/verification` | bearer | `{ items: VerificationItem[], meta }` | Available for P0 verification list. |
| `GET` | `/unmatched` | bearer | `{ items: UnmatchedCandidateSummary[], meta }` | Protected by admin router dependency although path has no `/admin` prefix. |
| `POST` | `/match` | bearer | match response | P1 action. |
| `POST` | `/admin/price-items/{id}/verify` | bearer | review response | P1 action. |
| `POST` | `/admin/price-items/{id}/reject` | bearer | review response | P1 action. |
| `GET` | `/admin/dashboard` | bearer | dashboard counts | P0 dashboard. |
| `GET` | `/admin/reports/quality` | bearer | quality aggregate maps | P0 quality page. |
| `GET` | `/admin/files/{id}/preview` | bearer | file stream | P1 preview action. |

## Frontend Route Inventory

| Route | Current source before P0 wiring | Backend target |
|---|---|---|
| `/`, `/ru`, `/kz`, `/en` | public search shell with empty local state | `/search` when `q` is present |
| `/ru/search`, `/kz/search`, `/en/search` | URL state only, empty results | `GET /search` |
| `/login` | real `POST /admin/login` wiring exists | `POST /admin/login` |
| `/dashboard` | local zero data | `GET /admin/dashboard` |
| `/imports` | local file selection, no upload | `POST /admin/import/archive`, then `GET /admin/import-batches` |
| `/documents` | local empty data | `GET /admin/documents` |
| `/verification` | local empty data | `GET /admin/verification` |
| `/unmatched` | local empty data | `GET /unmatched` |
| `/quality` | local empty data | `GET /admin/reports/quality` |
| `/services/complete-blood-count`, localized variants | neutral placeholder | P1: `/services/{id}/partners` needs real id/slug flow |
| `/partners/clinic-07`, localized variants | neutral placeholder | P1: `/partners/{id}/services` needs real partner id/slug flow |

## Request/Response Mismatches

| Area | Mismatch | Resolution |
|---|---|---|
| Search | Backend requires `q` with min length 1; frontend supports empty query. | Do not call backend for empty query; show empty/search prompt state. |
| Search city | Frontend has `city` URL param; backend `/search` does not filter by city. | Preserve `city` in URL only; do not send unsupported param. |
| Admin auth | Admin endpoints require `Authorization: Bearer <token>`. | Central API helper must attach stored token and surface 401. |
| Upload | Backend expects multipart field `file`. | Use `FormData.append("file", selectedFile)`. |
| Documents | Backend document file name is nested under `item.file.original_filename`. | Mapper must handle nullable `file`. |
| Quality | Backend returns aggregate dictionaries, not preformatted cards. | Frontend computes display metrics from maps. |
| Verification | Backend returns verification actions plus anomaly metadata, not source snippets/candidates. | P0 renders available action/anomaly fields only. |
| Unmatched | Backend returns unmatched candidate summaries, not full manual-match detail workflow. | P0 renders candidate rows and explanation JSON summary only. |

## Missing Connections

### P0

- `/ru/search`, `/kz/search`, `/en/search` to `GET /search`.
- `/dashboard` to `GET /admin/dashboard`.
- `/documents` to `GET /admin/documents`.
- `/imports` upload to `POST /admin/import/archive`, refresh list from `GET /admin/import-batches`.
- `/quality` to `GET /admin/reports/quality`.
- `/unmatched` to `GET /unmatched`.
- `/verification` to `GET /admin/verification`.
- Shared admin/public API helper using `NEXT_PUBLIC_API_BASE_URL`.

### P1

- Public `/services` and service detail pages.
- Public `/partners` and partner detail pages.
- Process/reprocess actions.
- Match/verify/reject actions.
- File preview.
- Service directory upload UI.

### P2

- Advanced pagination controls.
- Live city filtering once backend supports city/region.
- Route-level real slugs for services/clinics.
- Production session handling beyond localStorage.

## Priority Plan

| Priority | Work | Reason |
|---|---|---|
| P0 | Wire search, dashboard, documents, archive upload/list, quality, unmatched, verification, API helper | Demo-critical end-to-end visibility without fake data. |
| P1 | Wire service/partner catalogs and actions | Useful for richer demo but needs id/slug UX decisions. |
| P2 | Pagination polish, real city filter, preview/download polish, production auth | Improves usability after core demo path is real. |

## Audit Conclusion

Backend has the P0 endpoints needed for honest demo wiring. The frontend can remain static-export compatible because all P0 data loading can happen in client components. No backend schema changes are required for P0.

## P0 Implementation Status

Implemented frontend-to-backend wiring after this audit:

| Route | Backend endpoint | Status |
|---|---|---|
| `/ru/search`, `/kz/search`, `/en/search` | `GET /search` | Connected for non-empty `q`; URL `city` is preserved but not sent because the backend has no city filter yet. |
| `/login` | `POST /admin/login` | Connected; bearer token is stored in `localStorage`. |
| `/dashboard` | `GET /admin/dashboard` | Connected with bearer token. |
| `/documents` | `GET /admin/documents` | Connected with bearer token and status filter. |
| `/imports` | `POST /admin/import/archive`, `GET /admin/import-batches` | Connected; archive upload uses multipart field `file` and no fake success state. |
| `/quality` | `GET /admin/reports/quality` | Connected with bearer token. |
| `/unmatched` | `GET /unmatched` | Connected with bearer token. |
| `/verification` | `GET /admin/verification` | Connected with bearer token; displays available action/anomaly fields. |

Still unconnected after P0:

- Public service and partner catalog/detail routes need stable id/slug mapping and remain P1.
- Preview, process/reprocess, match, verify, and reject actions remain P1.
- Backend city filtering is not available for `/search`; the frontend preserves `city` in shareable URLs and degrades honestly.
