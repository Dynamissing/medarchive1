"use client";

import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock3,
  FileCheck2,
  FileWarning,
  Layers3,
  ListChecks,
  ShieldAlert,
} from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useI18n, type TranslationKey } from "@/i18n";
import {
  anomalySummaries,
  dashboardMock,
  qualityMock,
  queueSummaries,
  recentImportBatches,
  type BadgeTone,
  type DocumentStatus,
  type ImportBatchStatus,
} from "@/features/dashboard/mock-data";

const kpis = [
  {
    labelKey: "dashboard.documents",
    value: dashboardMock.documents_total.toLocaleString(),
    detailKey: "common.processing",
    detailValue: dashboardMock.documents_by_status.processing,
    tone: "info" as const,
    icon: FileCheck2,
  },
  {
    labelKey: "dashboard.activePrices",
    value: dashboardMock.active_price_items.toLocaleString(),
    detailKey: "dashboard.inactiveVersions",
    detailValue: qualityMock.price_history.inactive,
    tone: "success" as const,
    icon: Layers3,
  },
  {
    labelKey: "dashboard.verification",
    value: dashboardMock.open_verification_actions.toLocaleString(),
    detailKey: "dashboard.openActions",
    detailValue: null,
    tone: "warning" as const,
    icon: ListChecks,
  },
  {
    labelKey: "dashboard.anomalies",
    value: dashboardMock.unresolved_anomalies.toLocaleString(),
    detailKey: "dashboard.unmatchedRows",
    detailValue: dashboardMock.unmatched_candidates,
    tone: "error" as const,
    icon: ShieldAlert,
  },
];

const matchingBars = [
  { labelKey: "dashboard.autoAccepted", value: qualityMock.matching.auto_accepted, tone: "success" as const },
  { labelKey: "dashboard.needsReview", value: qualityMock.matching.needs_review, tone: "warning" as const },
  { labelKey: "common.unmatched", value: qualityMock.matching.unmatched, tone: "error" as const },
];

export function DashboardPage() {
  const { t } = useI18n();
  const matchingTotal = matchingBars.reduce((sum, item) => sum + item.value, 0);

  return (
    <AppShell>
      <div className="space-y-5">
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {kpis.map((kpi) => (
            <Card key={kpi.labelKey}>
              <CardContent className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <p className="text-xs font-medium uppercase text-muted-foreground">{t(kpi.labelKey as TranslationKey)}</p>
                  <div className="mt-2 text-3xl font-semibold tracking-normal text-foreground">{kpi.value}</div>
                  <Badge variant={kpi.tone} className="mt-3">
                    {kpi.detailValue === null ? t(kpi.detailKey as TranslationKey) : `${kpi.detailValue} ${t(kpi.detailKey as TranslationKey)}`}
                  </Badge>
                </div>
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-border bg-secondary text-muted-foreground">
                  <kpi.icon className="h-5 w-5" aria-hidden="true" />
                </div>
              </CardContent>
            </Card>
          ))}
        </section>

        <section className="grid gap-4 lg:grid-cols-4">
          {queueSummaries.map((item) => (
            <Card key={item.label}>
              <CardContent>
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-2xl font-semibold text-foreground">{item.value}</div>
                    <p className="mt-1 text-xs uppercase text-muted-foreground">{item.label}</p>
                  </div>
                  <Badge variant={documentTone(item.status)}>{statusLabel(item.status, t)}</Badge>
                </div>
                <p className="mt-3 text-xs leading-5">{item.helper}</p>
              </CardContent>
            </Card>
          ))}
        </section>

        <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_380px]">
          <Card>
            <CardHeader>
              <div>
                <CardTitle>{t("dashboard.recentBatches")}</CardTitle>
                <CardDescription>{t("dashboard.recentBatchesDesc")}</CardDescription>
              </div>
              <Badge variant="info">{dashboardMock.import_batches} {t("common.total")}</Badge>
            </CardHeader>
            <CardContent className="p-0">
              <div className="table-shell rounded-none border-x-0 border-b-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t("common.batch")}</TableHead>
                      <TableHead>{t("common.status")}</TableHead>
                      <TableHead className="text-right">{t("common.progress")}</TableHead>
                      <TableHead className="text-right">{t("common.failed")}</TableHead>
                      <TableHead>{t("common.created")}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {recentImportBatches.map((batch) => (
                      <TableRow key={batch.id}>
                        <TableCell>
                          <div className="font-medium text-foreground">{batch.original_filename}</div>
                          <div className="mt-1 text-xs text-muted-foreground">{batch.source_type}</div>
                        </TableCell>
                        <TableCell>
                          <Badge variant={batchTone(batch.status)}>{statusLabel(batch.status, t)}</Badge>
                        </TableCell>
                        <TableCell className="text-right tabular-nums">
                          {batch.processed_files}/{batch.total_files}
                        </TableCell>
                        <TableCell className="text-right tabular-nums">{batch.failed_files}</TableCell>
                        <TableCell>{batch.created_at}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div>
                <CardTitle>{t("dashboard.matchingDistribution")}</CardTitle>
                <CardDescription>{t("dashboard.matchingDesc")}</CardDescription>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex h-36 items-end gap-3 rounded-md border border-border bg-background/45 px-4 pb-4 pt-5">
                {matchingBars.map((item) => (
                  <div key={item.labelKey} className="flex min-w-0 flex-1 flex-col items-center gap-2">
                    <div
                      className={chartBarClass(item.tone)}
                      style={{ height: `${Math.max(12, Math.round((item.value / matchingTotal) * 100))}%` }}
                    />
                    <span className="w-full truncate text-center text-xs text-muted-foreground">{t(item.labelKey as TranslationKey)}</span>
                  </div>
                ))}
              </div>
              {matchingBars.map((item) => (
                <div key={item.labelKey} className="flex items-center justify-between gap-3">
                  <span className="text-sm text-muted-foreground">{t(item.labelKey as TranslationKey)}</span>
                  <Badge variant={item.tone}>{item.value}</Badge>
                </div>
              ))}
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-5 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
          <Card>
            <CardHeader>
              <div>
                <CardTitle>{t("dashboard.anomalySummary")}</CardTitle>
                <CardDescription>{t("dashboard.anomalyDesc")}</CardDescription>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {anomalySummaries.map((item) => (
                <div key={item.code} className="flex items-center justify-between gap-4 rounded-md border border-border bg-background/45 p-3">
                  <div className="flex min-w-0 items-center gap-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-secondary text-muted-foreground">
                      <AlertTriangle className="h-4 w-4" aria-hidden="true" />
                    </div>
                    <div className="min-w-0">
                      <div className="truncate text-sm font-medium text-foreground">{item.label}</div>
                      <div className="mt-1 truncate text-xs text-muted-foreground">{item.code}</div>
                    </div>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <Badge variant={severityTone(item.severity)}>{severityLabel(item.severity, t)}</Badge>
                    <span className="w-6 text-right text-sm font-semibold tabular-nums text-foreground">{item.count}</span>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div>
                <CardTitle>{t("dashboard.parsingHealth")}</CardTitle>
                <CardDescription>{t("dashboard.parsingDesc")}</CardDescription>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {Object.entries(dashboardMock.documents_by_status).map(([status, count]) => (
                <StatusBar key={status} status={status as DocumentStatus} count={count} total={dashboardMock.documents_total} />
              ))}
              <div className="grid gap-3 sm:grid-cols-3">
                <MiniHealth icon={CheckCircle2} label={t("dashboard.accepted")} value={`${qualityMock.matching.auto_accepted}`} tone="success" />
                <MiniHealth icon={Clock3} label={t("common.review")} value={`${qualityMock.matching.needs_review}`} tone="warning" />
                <MiniHealth icon={FileWarning} label={t("common.unmatched")} value={`${qualityMock.matching.unmatched}`} tone="error" />
              </div>
            </CardContent>
          </Card>
        </section>
      </div>
    </AppShell>
  );
}

function StatusBar({ status, count, total }: { status: DocumentStatus; count: number; total: number }) {
  const { t } = useI18n();
  const percent = Math.round((count / total) * 100);
  return (
    <div>
      <div className="mb-2 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Badge variant={documentTone(status)}>{statusLabel(status, t)}</Badge>
          <span className="text-sm text-muted-foreground">{count} {t("common.services")}</span>
        </div>
        <span className="text-sm font-medium tabular-nums text-foreground">{percent}%</span>
      </div>
      <div className="h-2 rounded-full bg-secondary">
        <div className={chartBarClass(documentTone(status))} style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}

function MiniHealth({
  icon: Icon,
  label,
  value,
  tone,
}: {
  icon: typeof Activity;
  label: string;
  value: string;
  tone: Exclude<BadgeTone, "neutral">;
}) {
  return (
    <div className="rounded-md border border-border bg-background/45 p-3">
      <Icon className={`h-4 w-4 ${textToneClass(tone)}`} aria-hidden="true" />
      <div className="mt-3 text-lg font-semibold text-foreground">{value}</div>
      <p className="mt-1 text-xs text-muted-foreground">{label}</p>
    </div>
  );
}

function statusLabel(status: DocumentStatus | ImportBatchStatus, t: ReturnType<typeof useI18n>["t"]) {
  const labels: Record<DocumentStatus | ImportBatchStatus, TranslationKey> = {
    pending: "common.pending",
    processing: "common.processing",
    parsed: "common.parsed",
    failed: "common.failed",
    completed: "common.completed",
  };
  return t(labels[status]);
}

function documentTone(status: DocumentStatus): BadgeTone {
  if (status === "parsed") return "success";
  if (status === "processing") return "info";
  if (status === "failed") return "error";
  return "warning";
}

function batchTone(status: ImportBatchStatus): BadgeTone {
  if (status === "completed") return "success";
  if (status === "processing") return "info";
  if (status === "failed") return "error";
  return "warning";
}

function severityTone(severity: "high" | "medium" | "low"): BadgeTone {
  if (severity === "high") return "error";
  if (severity === "medium") return "warning";
  return "info";
}

function severityLabel(severity: "high" | "medium" | "low", t: ReturnType<typeof useI18n>["t"]) {
  const labels: Record<typeof severity, TranslationKey> = {
    high: "common.high",
    medium: "common.medium",
    low: "common.low",
  };
  return t(labels[severity]);
}

function chartBarClass(tone: BadgeTone) {
  const base = "h-full w-full rounded-full transition-colors";
  if (tone === "success") return `${base} bg-success`;
  if (tone === "warning") return `${base} bg-warning`;
  if (tone === "error") return `${base} bg-destructive`;
  if (tone === "info") return `${base} bg-info`;
  return `${base} bg-muted`;
}

function textToneClass(tone: Exclude<BadgeTone, "neutral">) {
  if (tone === "success") return "text-success";
  if (tone === "warning") return "text-warning";
  if (tone === "error") return "text-destructive";
  return "text-info";
}
