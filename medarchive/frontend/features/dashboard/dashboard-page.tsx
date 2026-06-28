"use client";

import { useEffect, useState } from "react";
import { FileCheck2, Layers3, ListChecks, ShieldAlert } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { NoDataYet, ProcessingInProgress, RetryError } from "@/components/ui/states";
import { useI18n, type TranslationKey } from "@/i18n";
import { getDashboard, type DashboardResponse } from "@/lib/api";

const emptyDashboard: DashboardResponse = {
  import_batches: 0,
  documents_total: 0,
  documents_by_status: {},
  open_verification_actions: 0,
  unresolved_anomalies: 0,
  unmatched_candidates: 0,
  active_price_items: 0,
  extracted_rows: 0,
  normalized_rows: 0,
  auto_matched: 0,
  needs_review: 0,
  normalization_rate_percent: 0,
};

export function DashboardPage() {
  const { t } = useI18n();
  const [data, setData] = useState<DashboardResponse>(emptyDashboard);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setError(null);
    getDashboard()
      .then((response) => {
        if (mounted) setData(response);
      })
      .catch((fetchError: unknown) => {
        if (mounted) setError(fetchError instanceof Error ? fetchError.message : "Dashboard request failed");
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  const kpis = [
    { labelKey: "dashboard.documents", value: data.documents_total, detailKey: "common.processing", detailValue: data.documents_by_status.processing ?? 0, tone: "info" as const, icon: FileCheck2 },
    { labelKey: "dashboard.activePrices", value: data.active_price_items, detailKey: "dashboard.inactiveVersions", detailValue: null, tone: "success" as const, icon: Layers3 },
    { labelKey: "dashboard.verification", value: data.open_verification_actions, detailKey: "dashboard.openActions", detailValue: null, tone: "warning" as const, icon: ListChecks },
    { labelKey: "dashboard.anomalies", value: data.unresolved_anomalies, detailKey: "dashboard.unmatchedRows", detailValue: data.unmatched_candidates, tone: "error" as const, icon: ShieldAlert },
  ];

  return (
    <AppShell>
      <div className="space-y-5">
        {loading ? <ProcessingInProgress title={t("states.processing.title")} description={t("states.processing.description")} /> : null}
        {error ? <RetryError description={error} onRetry={() => window.location.reload()} /> : null}

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {kpis.map((kpi) => (
            <Card key={kpi.labelKey}>
              <CardContent className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <p className="text-xs font-medium uppercase text-muted-foreground">{t(kpi.labelKey as TranslationKey)}</p>
                  <div className="mt-2 text-3xl font-semibold tracking-normal text-foreground">{kpi.value.toLocaleString()}</div>
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

        <section className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_360px]">
          <Card>
            <CardHeader>
              <div>
                <CardTitle>{t("dashboard.parsingHealth")}</CardTitle>
                <CardDescription>{t("dashboard.parsingDesc")}</CardDescription>
              </div>
              <Badge variant="info">{data.import_batches} {t("common.batch")}</Badge>
            </CardHeader>
            <CardContent className="space-y-4">
              {Object.keys(data.documents_by_status).length > 0 ? (
                Object.entries(data.documents_by_status).map(([status, count]) => (
                  <StatusBar key={status} status={status} count={count} total={data.documents_total} />
                ))
              ) : (
                <NoDataYet />
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div>
                <CardTitle>{t("dashboard.anomalySummary")}</CardTitle>
                <CardDescription>{t("dashboard.anomalyDesc")}</CardDescription>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <MetricRow label={t("dashboard.unmatchedRows")} value={data.unmatched_candidates} tone="warning" />
              <MetricRow label={t("dashboard.openActions")} value={data.open_verification_actions} tone="info" />
              <MetricRow label={t("dashboard.anomalies")} value={data.unresolved_anomalies} tone="error" />
            </CardContent>
          </Card>
        </section>
      </div>
    </AppShell>
  );
}

function StatusBar({ status, count, total }: { status: string; count: number; total: number }) {
  const percent = total > 0 ? Math.round((count / total) * 100) : 0;
  return (
    <div>
      <div className="mb-2 flex items-center justify-between gap-3">
        <Badge variant={statusTone(status)}>{status}</Badge>
        <span className="text-sm font-medium tabular-nums text-foreground">{count} / {percent}%</span>
      </div>
      <div className="h-2 rounded-full bg-secondary">
        <div className="h-full rounded-full bg-primary" style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}

function MetricRow({ label, value, tone }: { label: string; value: number; tone: "warning" | "info" | "error" }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-md border border-border bg-background/45 p-3">
      <span className="text-sm text-muted-foreground">{label}</span>
      <Badge variant={tone}>{value}</Badge>
    </div>
  );
}

function statusTone(status: string) {
  if (status === "parsed" || status === "completed") return "success";
  if (status === "processing") return "info";
  if (status === "failed") return "error";
  return "warning";
}
