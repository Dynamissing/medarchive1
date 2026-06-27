"use client";

import { Download, FileWarning, GitBranch, ShieldAlert } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useI18n } from "@/i18n";
import {
  anomalySections,
  batchSummaries,
  headlineMetrics,
  normalizationFunnel,
  unmatchedSections,
  type BatchQualitySummary,
  type FunnelStep,
  type QualityMetric,
} from "@/features/quality/mock-data";

export function QualityReportPage() {
  const { t } = useI18n();
  return (
    <div className="space-y-5">
      <section className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <Badge variant="info">{t("quality.title")}</Badge>
          <h1 className="mt-3 text-3xl font-semibold text-foreground">{t("quality.headline")}</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
            {t("quality.desc")}
          </p>
        </div>
        <Button variant="secondary">
          <Download className="h-4 w-4" aria-hidden="true" />
          {t("quality.export")}
        </Button>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {headlineMetrics.map((metric) => (
          <MetricCard key={metric.label} metric={metric} />
        ))}
      </section>

      <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <Card>
          <CardHeader>
            <div>
              <CardTitle>{t("quality.funnel")}</CardTitle>
              <CardDescription>{t("quality.funnelDesc")}</CardDescription>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {normalizationFunnel.map((step) => (
              <FunnelRow key={step.label} step={step} />
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div>
              <CardTitle>{t("quality.unmatchedDrivers")}</CardTitle>
              <CardDescription>{t("quality.unmatchedDesc")}</CardDescription>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {unmatchedSections.map((section) => (
              <div key={section.label} className="flex items-center justify-between rounded-md border border-border bg-background/45 p-3">
                <div className="flex items-center gap-3">
                  <GitBranch className="h-4 w-4 text-info" aria-hidden="true" />
                  <span className="text-sm text-foreground">{section.label}</span>
                </div>
                <Badge variant="warning">{section.count}</Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_360px]">
        <Card>
          <CardHeader>
            <div>
              <CardTitle>{t("quality.batchSummaries")}</CardTitle>
              <CardDescription>{t("quality.batchDesc")}</CardDescription>
            </div>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-3">
            {batchSummaries.map((batch) => (
              <BatchCard key={batch.id} batch={batch} />
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div>
              <CardTitle>{t("quality.anomalySections")}</CardTitle>
              <CardDescription>{t("quality.anomalyDesc")}</CardDescription>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {anomalySections.map((section) => (
              <div key={section.label} className="rounded-md border border-border bg-background/45 p-3">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <ShieldAlert className="h-4 w-4 text-destructive" aria-hidden="true" />
                    <span className="text-sm font-medium text-foreground">{section.label}</span>
                  </div>
                  <Badge variant={section.severity === "high" ? "error" : section.severity === "medium" ? "warning" : "info"}>{section.count}</Badge>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}

function MetricCard({ metric }: { metric: QualityMetric }) {
  return (
    <Card>
      <CardContent>
        <p className="text-xs font-medium uppercase text-muted-foreground">{metric.label}</p>
        <div className="mt-2 text-3xl font-semibold text-foreground">{metric.value}</div>
        <Badge variant={metric.tone} className="mt-3">
          {metric.detail}
        </Badge>
      </CardContent>
    </Card>
  );
}

function FunnelRow({ step }: { step: FunnelStep }) {
  return (
    <div>
      <div className="mb-2 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Badge variant={step.tone}>{step.percent}%</Badge>
          <span className="text-sm font-medium text-foreground">{step.label}</span>
        </div>
        <span className="text-sm tabular-nums text-muted-foreground">{step.count}</span>
      </div>
      <div className="h-2 rounded-full bg-secondary">
        <div className="h-full rounded-full bg-primary" style={{ width: `${step.percent}%` }} />
      </div>
    </div>
  );
}

function BatchCard({ batch }: { batch: BatchQualitySummary }) {
  const { t } = useI18n();
  return (
    <div className="rounded-md border border-border bg-background/45 p-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="truncate text-sm font-medium text-foreground">{batch.name}</div>
          <div className="mt-1 text-xs text-muted-foreground">{batch.documents} {t("documents.cardTitle")}</div>
        </div>
        <FileWarning className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
      </div>
      <div className="mt-4 grid grid-cols-3 gap-2 text-center">
        <MiniStat label={t("common.parsed")} value={batch.parsed} tone="success" />
        <MiniStat label={t("common.review")} value={batch.review} tone="warning" />
        <MiniStat label={t("common.failed")} value={batch.failed} tone="error" />
      </div>
    </div>
  );
}

function MiniStat({ label, value, tone }: { label: string; value: number; tone: "success" | "warning" | "error" }) {
  return (
    <div className="rounded-md bg-card p-2">
      <div className="text-sm font-semibold text-foreground">{value}</div>
      <Badge variant={tone} className="mt-2">
        {label}
      </Badge>
    </div>
  );
}
