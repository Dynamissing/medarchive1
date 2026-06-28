"use client";

import { useEffect, useState } from "react";
import { Download } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { NoDataYet, ProcessingInProgress, RetryError } from "@/components/ui/states";
import { useI18n } from "@/i18n";
import { getQualityReport, type QualityReportResponse } from "@/lib/api";

export function QualityReportPage() {
  const { t } = useI18n();
  const [data, setData] = useState<QualityReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setError(null);
    getQualityReport()
      .then((response) => {
        if (mounted) setData(response);
      })
      .catch((fetchError: unknown) => {
        if (mounted) setError(fetchError instanceof Error ? fetchError.message : "Quality report request failed");
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  const parsingTotal = sumValues(data?.parsing);
  const matchingTotal = sumValues(data?.matching);
  const validationTotal = sumValues(data?.validation);
  const activePrices = data?.price_history.active ?? 0;

  return (
    <div className="space-y-5">
      <section className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <Badge variant="info">{t("quality.title")}</Badge>
          <h1 className="mt-3 text-3xl font-semibold text-foreground">{t("quality.headline")}</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">{t("quality.desc")}</p>
        </div>
        <Button variant="secondary" disabled>
          <Download className="h-4 w-4" aria-hidden="true" />
          {t("quality.export")}
        </Button>
      </section>

      {loading ? <ProcessingInProgress /> : null}
      {error ? <RetryError description={error} onRetry={() => window.location.reload()} /> : null}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label={t("documents.total")} value={parsingTotal} detail={t("dashboard.documents")} tone="info" />
        <MetricCard label={t("dashboard.activePrices")} value={activePrices} detail={t("public.currentPrices")} tone="success" />
        <MetricCard label={t("dashboard.needsReview")} value={matchingTotal} detail={t("dashboard.matchingDistribution")} tone="warning" />
        <MetricCard label={t("dashboard.anomalies")} value={validationTotal} detail={t("quality.anomalySections")} tone="error" />
      </section>

      <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <MetricMapCard title={t("quality.funnel")} description={t("quality.funnelDesc")} values={data?.parsing} />
        <MetricMapCard title={t("quality.unmatchedDrivers")} description={t("quality.unmatchedDesc")} values={data?.matching} />
      </section>

      <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <MetricMapCard title="Extraction" description="Parser row output and empty-document signals." values={data?.extraction} />
        <MetricMapCard title="Normalization" description="Recorded rows, matching split, and normalization rate." values={data?.normalization} />
      </section>

      <section className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_360px]">
        <MetricMapCard title={t("quality.batchSummaries")} description={t("quality.batchDesc")} values={data?.price_history} />
        <MetricMapCard title={t("quality.anomalySections")} description={t("quality.anomalyDesc")} values={data?.validation} />
      </section>
    </div>
  );
}

function MetricCard({ label, value, detail, tone }: { label: string; value: number; detail: string; tone: "success" | "warning" | "error" | "info" }) {
  return (
    <Card>
      <CardContent>
        <p className="text-xs font-medium uppercase text-muted-foreground">{label}</p>
        <div className="mt-2 text-3xl font-semibold text-foreground">{value.toLocaleString()}</div>
        <Badge variant={tone} className="mt-3">{detail}</Badge>
      </CardContent>
    </Card>
  );
}

function MetricMapCard({ title, description, values }: { title: string; description: string; values?: Record<string, unknown> }) {
  const entries = Object.entries(values ?? {});
  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {entries.length > 0 ? entries.map(([key, value]) => (
          <div key={key} className="flex items-center justify-between gap-3 rounded-md border border-border bg-background/45 p-3">
            <span className="text-sm text-muted-foreground">{key}</span>
            <Badge variant="info">{String(value)}</Badge>
          </div>
        )) : <NoDataYet />}
      </CardContent>
    </Card>
  );
}

function sumValues(values?: Record<string, number>) {
  return Object.values(values ?? {}).reduce((sum, value) => sum + value, 0);
}
