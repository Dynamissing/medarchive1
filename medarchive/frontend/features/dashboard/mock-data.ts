export type DocumentStatus = "pending" | "processing" | "parsed" | "failed";
export type ImportBatchStatus = "pending" | "processing" | "completed" | "failed";
export type BadgeTone = "neutral" | "success" | "warning" | "error" | "info";

export type DashboardResponseShape = {
  import_batches: number;
  documents_total: number;
  documents_by_status: Record<DocumentStatus, number>;
  open_verification_actions: number;
  unresolved_anomalies: number;
  unmatched_candidates: number;
  active_price_items: number;
};

export type QualityReportShape = {
  generated_at: string;
  parsing: Record<DocumentStatus, number>;
  matching: Record<"auto_accepted" | "needs_review" | "unmatched", number>;
  validation: Record<string, number>;
  price_history: {
    active: number;
    inactive: number;
  };
};

export type ImportBatchSummaryShape = {
  id: string;
  source_type: string;
  status: ImportBatchStatus;
  original_filename: string;
  total_files: number;
  processed_files: number;
  failed_files: number;
  warnings: string[];
  created_at: string;
};

export type QueueSummary = {
  label: string;
  value: number;
  status: DocumentStatus;
  helper: string;
};

export type AnomalySummary = {
  code: string;
  label: string;
  count: number;
  severity: "high" | "medium" | "low";
};

export const dashboardMock: DashboardResponseShape = {
  import_batches: 42,
  documents_total: 318,
  documents_by_status: {
    pending: 28,
    processing: 9,
    parsed: 257,
    failed: 24,
  },
  open_verification_actions: 31,
  unresolved_anomalies: 18,
  unmatched_candidates: 12,
  active_price_items: 6842,
};

export const qualityMock: QualityReportShape = {
  generated_at: "2026-06-27T09:30:00Z",
  parsing: dashboardMock.documents_by_status,
  matching: {
    auto_accepted: 612,
    needs_review: 98,
    unmatched: 27,
  },
  validation: {
    price_change_gt_50_percent: 7,
    nonresident_lt_resident: 4,
    future_effective_date: 3,
    missing_service_name: 4,
  },
  price_history: {
    active: dashboardMock.active_price_items,
    inactive: 214,
  },
};

export const recentImportBatches: ImportBatchSummaryShape[] = [
  {
    id: "batch-042",
    source_type: "archive_zip",
    status: "processing",
    original_filename: "clinic-08-prices.zip",
    total_files: 38,
    processed_files: 27,
    failed_files: 1,
    warnings: ["1 scanned PDF queued for OCR review"],
    created_at: "09:22",
  },
  {
    id: "batch-041",
    source_type: "archive_zip",
    status: "completed",
    original_filename: "clinic-07-contracts.zip",
    total_files: 21,
    processed_files: 21,
    failed_files: 0,
    warnings: [],
    created_at: "08:48",
  },
  {
    id: "batch-040",
    source_type: "service_directory",
    status: "completed",
    original_filename: "organizer-services.xlsx",
    total_files: 1,
    processed_files: 1,
    failed_files: 0,
    warnings: ["12 spreadsheet warning cells ignored"],
    created_at: "08:12",
  },
  {
    id: "batch-039",
    source_type: "archive_zip",
    status: "failed",
    original_filename: "legacy-scan-pack.zip",
    total_files: 14,
    processed_files: 10,
    failed_files: 4,
    warnings: ["4 files have no recognizable data"],
    created_at: "Yesterday",
  },
];

export const queueSummaries: QueueSummary[] = [
  { label: "Pending", value: dashboardMock.documents_by_status.pending, status: "pending", helper: "waiting for worker capacity" },
  { label: "Processing", value: dashboardMock.documents_by_status.processing, status: "processing", helper: "active parser jobs" },
  { label: "Parsed", value: dashboardMock.documents_by_status.parsed, status: "parsed", helper: "ready for matching and review" },
  { label: "Failed", value: dashboardMock.documents_by_status.failed, status: "failed", helper: "needs operator attention" },
];

export const anomalySummaries: AnomalySummary[] = [
  { code: "price_change_gt_50_percent", label: "Price change over 50%", count: 7, severity: "high" },
  { code: "nonresident_lt_resident", label: "Nonresident below resident", count: 4, severity: "medium" },
  { code: "future_effective_date", label: "Future effective date", count: 3, severity: "low" },
  { code: "missing_service_name", label: "Missing service name", count: 4, severity: "medium" },
];
