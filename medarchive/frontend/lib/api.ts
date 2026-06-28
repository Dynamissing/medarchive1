export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
export const ADMIN_TOKEN_STORAGE_KEY = "medarchive.adminToken";

export type PageMeta = {
  page: number;
  page_size: number;
  total: number;
  pages: number;
};

export type PaginatedResponse<T> = {
  items: T[];
  meta: PageMeta;
};

export type SearchResult = {
  type: "service" | "partner";
  id: string;
  label: string;
  score: number;
  payload: Record<string, unknown>;
};

export type PartnerSummary = {
  id: string;
  name: string;
  service_count: number;
  active_price_count: number;
};

export type ServiceSummary = {
  id: string;
  name: string;
  normalized_name: string;
  code: string | null;
  tariff_code?: string | null;
  category?: string | null;
  specialty?: string | null;
};

export type PartnerServiceSummary = {
  service: ServiceSummary;
  partner: PartnerSummary;
  latest_amount: string | number | null;
  currency: string | null;
  effective_date: string | null;
};

export type DashboardResponse = {
  import_batches: number;
  documents_total: number;
  documents_by_status: Record<string, number>;
  open_verification_actions: number;
  unresolved_anomalies: number;
  unmatched_candidates: number;
  active_price_items: number;
  extracted_rows: number;
  normalized_rows: number;
  auto_matched: number;
  needs_review: number;
  normalization_rate_percent: number;
};

export type ImportBatchSummary = {
  id: string;
  source_type: string;
  status: string;
  original_filename: string;
  total_files: number;
  processed_files: number;
  failed_files: number;
  warnings: string[];
  created_at: string;
};

export type FileAssetSummary = {
  id: string;
  original_filename: string;
  stored_path: string;
  extension: string | null;
  mime_type: string | null;
  size_bytes: number;
};

export type PriceDocumentSummary = {
  id: string;
  import_batch_id: string;
  file_asset_id: string;
  status: string;
  detected_type: string | null;
  progress_percent: number;
  processing_attempts: number;
  last_error: string | null;
  warnings: string[];
  parsed_summary: Record<string, unknown>;
  file: FileAssetSummary | null;
  processing_started_at: string | null;
  processing_finished_at: string | null;
  duration_ms: number | null;
  parser_stage: string | null;
};

export type ProcessingEventSummary = {
  id: string;
  event_type: string;
  status: string;
  message: string;
  progress_percent: number | null;
  payload: Record<string, unknown>;
  created_at: string;
};

export type PriceDocumentDetail = PriceDocumentSummary & {
  events: ProcessingEventSummary[];
};

export type ArchiveImportResponse = {
  import_batch_id: string;
  original_asset_id: string;
  extracted_files: number;
  price_documents: number;
  processing_task_id: string | null;
  warnings: string[];
};

export type QualityReportResponse = {
  generated_at: string;
  parsing: Record<string, number>;
  matching: Record<string, number>;
  validation: Record<string, number>;
  price_history: Record<string, number>;
  documents?: Record<string, unknown>;
  extraction?: Record<string, unknown>;
  normalization?: Record<string, unknown>;
  top_parser_errors?: Array<Record<string, unknown>>;
};

export type UnmatchedCandidateSummary = {
  id: string;
  row_hash: string;
  price_document_id: string | null;
  score: number;
  normalized_query: string;
  source_code: string | null;
  explanation: Record<string, unknown>;
  created_at: string;
};

export type VerificationItem = {
  id: string;
  anomaly_flag_id: string | null;
  action_type: string;
  status: string;
  notes: string | null;
  payload: Record<string, unknown>;
  anomaly_code: string | null;
  anomaly_message: string | null;
  severity: string | null;
};

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export function getAdminToken() {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ADMIN_TOKEN_STORAGE_KEY);
}

export function storeAdminToken(token: string) {
  window.localStorage.setItem(ADMIN_TOKEN_STORAGE_KEY, token);
}

export function clearAdminToken() {
  window.localStorage.removeItem(ADMIN_TOKEN_STORAGE_KEY);
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit & { auth?: boolean } = {},
): Promise<T> {
  const { auth = false, headers, ...requestOptions } = options;
  const requestHeaders = new Headers(headers);

  if (!(requestOptions.body instanceof FormData) && !requestHeaders.has("Content-Type")) {
    requestHeaders.set("Content-Type", "application/json");
  }

  if (auth) {
    const token = getAdminToken();
    if (!token) {
      throw new ApiError("Admin authentication is required.", 401);
    }
    requestHeaders.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...requestOptions,
    headers: requestHeaders,
  });

  if (!response.ok) {
    throw new ApiError(await errorMessage(response), response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export async function adminLogin(username: string, password: string) {
  return apiFetch<{ access_token: string; token_type: string; expires_in: number }>("/admin/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export function searchBackend(query: string, page = 1, pageSize = 20, type?: "service" | "partner") {
  const params = new URLSearchParams({ q: query, page: String(page), page_size: String(pageSize) });
  if (type) params.set("type", type);
  return apiFetch<PaginatedResponse<SearchResult>>(`/search?${params.toString()}`);
}

export function getServicePartners(serviceId: string) {
  return apiFetch<PaginatedResponse<PartnerSummary>>(`/services/${serviceId}/partners`);
}

export function getPartnerServices(partnerId: string) {
  return apiFetch<PaginatedResponse<PartnerServiceSummary>>(`/partners/${partnerId}/services`);
}

export function getDashboard() {
  return apiFetch<DashboardResponse>("/admin/dashboard", { auth: true });
}

export function getImportBatches() {
  return apiFetch<PaginatedResponse<ImportBatchSummary>>("/admin/import-batches", { auth: true });
}

export function uploadArchive(file: File) {
  const body = new FormData();
  body.append("file", file);
  return apiFetch<ArchiveImportResponse>("/admin/import/archive", {
    method: "POST",
    body,
    auth: true,
  });
}

export function getDocuments(params: { status?: string; page?: number; pageSize?: number } = {}) {
  const query = new URLSearchParams({
    page: String(params.page ?? 1),
    page_size: String(params.pageSize ?? 20),
  });
  if (params.status && params.status !== "all") {
    query.set("status", params.status);
  }
  return apiFetch<PaginatedResponse<PriceDocumentSummary>>(`/admin/documents?${query.toString()}`, { auth: true });
}

export function getDocument(priceDocumentId: string) {
  return apiFetch<PriceDocumentDetail>(`/admin/documents/${priceDocumentId}`, { auth: true });
}

export function reprocessDocument(priceDocumentId: string) {
  return apiFetch<{ task_id: string; target_id: string; target_type: string }>(`/admin/documents/${priceDocumentId}/reprocess`, {
    method: "POST",
    auth: true,
  });
}

export function recoverStaleDocuments(thresholdMinutes?: number) {
  const params = thresholdMinutes ? `?threshold_minutes=${thresholdMinutes}` : "";
  return apiFetch<{ recovered: number }>(`/admin/documents/recover-stale${params}`, {
    method: "POST",
    auth: true,
  });
}

export function filePreviewUrl(fileAssetId: string) {
  return `${API_BASE_URL}/admin/files/${fileAssetId}/preview`;
}

export async function previewFile(fileAssetId: string) {
  const token = getAdminToken();
  if (!token) throw new ApiError("Admin authentication is required.", 401);
  const response = await fetch(filePreviewUrl(fileAssetId), {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new ApiError(await errorMessage(response), response.status);
  }
  return response.blob();
}

export function getQualityReport() {
  return apiFetch<QualityReportResponse>("/admin/reports/quality", { auth: true });
}

export function getUnmatched() {
  return apiFetch<PaginatedResponse<UnmatchedCandidateSummary>>("/unmatched", { auth: true });
}

export function manualMatchCandidate(candidateId: string, serviceId: string) {
  return apiFetch<{ candidate_id: string; service_id: string; created_price_items: number; status: string }>(
    `/admin/unmatched/${candidateId}/match`,
    {
      method: "POST",
      body: JSON.stringify({ service_id: serviceId }),
      auth: true,
    },
  );
}

export function getVerification() {
  return apiFetch<PaginatedResponse<VerificationItem>>("/admin/verification", { auth: true });
}

export function resolveVerification(actionId: string, notes: string | null = null) {
  return apiFetch<{ action_id: string; status: string; resolved_anomaly: boolean }>(`/admin/verification/${actionId}/resolve`, {
    method: "POST",
    body: JSON.stringify({ notes }),
    auth: true,
  });
}

async function errorMessage(response: Response) {
  try {
    const payload = await response.json();
    if (typeof payload.detail === "string") return payload.detail;
    if (Array.isArray(payload.detail)) {
      return payload.detail
        .map((item: { msg?: string }) => item.msg ?? "Validation error")
        .join(", ");
    }
  } catch {
    // Fall through to status text.
  }
  return response.statusText || "Request failed";
}
