export type QualityMetric = {
  label: string;
  value: string;
  detail: string;
  tone: "success" | "warning" | "error" | "info";
};

export type BatchQualitySummary = {
  id: string;
  name: string;
  documents: number;
  parsed: number;
  review: number;
  failed: number;
};

export type FunnelStep = {
  label: string;
  count: number;
  percent: number;
  tone: "success" | "warning" | "info";
};

export const headlineMetrics: QualityMetric[] = [
  { label: "Parse success", value: "91%", detail: "257 of 282 documents", tone: "success" },
  { label: "Auto matches", value: "83%", detail: "612 accepted candidates", tone: "success" },
  { label: "Needs review", value: "98", detail: "open verification rows", tone: "warning" },
  { label: "Critical anomalies", value: "11", detail: "high-severity flags", tone: "error" },
];

export const batchSummaries: BatchQualitySummary[] = [
  { id: "batch-042", name: "clinic-08-prices.zip", documents: 38, parsed: 27, review: 10, failed: 1 },
  { id: "batch-041", name: "clinic-07-contracts.zip", documents: 21, parsed: 21, review: 4, failed: 0 },
  { id: "batch-040", name: "organizer-services.xlsx", documents: 1, parsed: 1, review: 0, failed: 0 },
];

export const normalizationFunnel: FunnelStep[] = [
  { label: "Extracted rows", count: 912, percent: 100, tone: "info" },
  { label: "Normalized rows", count: 861, percent: 94, tone: "success" },
  { label: "Matched rows", count: 737, percent: 81, tone: "success" },
  { label: "Review queue", count: 98, percent: 11, tone: "warning" },
  { label: "Unmatched", count: 27, percent: 3, tone: "warning" },
];

export const anomalySections = [
  { label: "Price change over 50%", count: 7, severity: "high" },
  { label: "Nonresident below resident", count: 4, severity: "high" },
  { label: "Missing service name", count: 4, severity: "medium" },
  { label: "Future effective date", count: 3, severity: "low" },
];

export const unmatchedSections = [
  { label: "Low confidence text match", count: 12 },
  { label: "OCR ambiguity", count: 8 },
  { label: "No source code", count: 7 },
];
