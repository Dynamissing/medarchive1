"use client";

import { useCallback, useEffect, useState } from "react";
import { Eye, RefreshCcw, AlertTriangle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { NoResults, ProcessingInProgress, RetryError } from "@/components/ui/states";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useI18n, type TranslationKey } from "@/i18n";
import {
  getDocument,
  getDocuments,
  previewFile,
  reprocessDocument,
  recoverStaleDocuments,
  type PriceDocumentDetail,
  type PriceDocumentSummary,
} from "@/lib/api";

type StatusFilter = "all" | "pending" | "processing" | "parsed" | "needs_review" | "failed";

const statusOptions: Array<{ value: StatusFilter; labelKey: TranslationKey }> = [
  { value: "all", labelKey: "documents.allStatuses" },
  { value: "pending", labelKey: "common.pending" },
  { value: "processing", labelKey: "common.processing" },
  { value: "parsed", labelKey: "common.parsed" },
  { value: "needs_review", labelKey: "documents.attention" },
  { value: "failed", labelKey: "common.failed" },
];

function isStaleProcessing(doc: PriceDocumentSummary, thresholdMs = 5 * 60 * 1000): boolean {
  if (doc.status !== "processing" || !doc.processing_started_at) return false;
  const started = new Date(doc.processing_started_at).getTime();
  return Date.now() - started > thresholdMs;
}

export function DocumentsPage() {
  const { t } = useI18n();
  const [status, setStatus] = useState<StatusFilter>("all");
  const [rows, setRows] = useState<PriceDocumentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reprocessingIds, setReprocessingIds] = useState<Set<string>>(new Set());
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<PriceDocumentDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [recoveringAll, setRecoveringAll] = useState(false);
  const [totalDocs, setTotalDocs] = useState<number>(0);

  const refreshDocuments = useCallback(
    ({ showLoading, shouldUpdate = () => true }: { showLoading: boolean; shouldUpdate?: () => boolean }) => {
      if (showLoading) setLoading(true);
      setError(null);
      return getDocuments({ status, pageSize: 100 })
        .then((response) => {
          if (shouldUpdate()) {
            setRows(response.items);
            setTotalDocs(response.meta.total);
            setSelectedId((current) => current ?? response.items[0]?.id ?? null);
          }
        })
        .catch((fetchError: unknown) => {
          if (shouldUpdate()) {
            setRows([]);
            setError(fetchError instanceof Error ? fetchError.message : "Documents request failed");
          }
        });
    },
    [status],
  );

  useEffect(() => {
    let active = true;
    refreshDocuments({ showLoading: true, shouldUpdate: () => active })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [refreshDocuments]);

  useEffect(() => {
    if (!rows.some((document) => document.status === "pending" || document.status === "processing")) return;
    const interval = window.setInterval(() => {
      refreshDocuments({ showLoading: false });
    }, 3000);
    return () => window.clearInterval(interval);
  }, [refreshDocuments, rows]);

  useEffect(() => {
    if (!selectedId) {
      setDetail(null);
      return;
    }
    let active = true;
    setDetailLoading(true);
    getDocument(selectedId)
      .then((document) => {
        if (active) setDetail(document);
      })
      .catch((fetchError: unknown) => {
        if (active) setError(fetchError instanceof Error ? fetchError.message : "Document detail request failed");
      })
      .finally(() => {
        if (active) setDetailLoading(false);
      });
    return () => {
      active = false;
    };
  }, [selectedId]);

  async function handleReprocess(documentId: string) {
    setReprocessingIds((current) => new Set(current).add(documentId));
    setError(null);
    try {
      await reprocessDocument(documentId);
      await refreshDocuments({ showLoading: false });
      if (selectedId === documentId) {
        setDetail(await getDocument(documentId));
      }
    } catch (reprocessError: unknown) {
      setError(reprocessError instanceof Error ? reprocessError.message : "Reprocess request failed");
    } finally {
      setReprocessingIds((current) => {
        const next = new Set(current);
        next.delete(documentId);
        return next;
      });
    }
  }

  async function handlePreview(document: PriceDocumentSummary) {
    if (!document.file_asset_id) return;
    setError(null);
    try {
      const blob = await previewFile(document.file_asset_id);
      const url = window.URL.createObjectURL(blob);
      window.open(url, "_blank", "noopener,noreferrer");
      window.setTimeout(() => window.URL.revokeObjectURL(url), 60_000);
    } catch (previewError: unknown) {
      setError(previewError instanceof Error ? previewError.message : "File preview failed");
    }
  }

  const staleCount = rows.filter((doc) => isStaleProcessing(doc)).length;

  async function handleRecoverAll() {
    setRecoveringAll(true);
    setError(null);
    try {
      const result = await recoverStaleDocuments(5);
      await refreshDocuments({ showLoading: false });
      if (result.recovered > 0) {
        setStatus("all");
      }
    } catch (recoverError: unknown) {
      setError(recoverError instanceof Error ? recoverError.message : "Recover stale failed");
    } finally {
      setRecoveringAll(false);
    }
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_430px]">
      {loading ? <ProcessingInProgress /> : null}
      {error ? <RetryError description={error} onRetry={() => setStatus((value) => value)} /> : null}

      <Card>
        <CardHeader>
          <div>
            <CardTitle>{t("documents.cardTitle")}</CardTitle>
            <CardDescription>{t("documents.desc")}</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="neutral">{totalDocs} total / {rows.length} shown</Badge>
            {staleCount > 0 && (
              <Button
                type="button"
                variant="destructive"
                size="sm"
                disabled={recoveringAll}
                onClick={handleRecoverAll}
              >
                <AlertTriangle className="mr-1 h-4 w-4" />
                {recoveringAll ? "Recovering..." : `Recover ${staleCount} stuck`}
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-end gap-4">
            <label className="flex max-w-56 flex-col gap-2">
              <span className="text-xs font-medium uppercase text-muted-foreground">{t("common.status")}</span>
              <select
                className="h-9 rounded-md border border-input bg-background/65 px-3 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={status}
                onChange={(event) => setStatus(event.target.value as StatusFilter)}
              >
                {statusOptions.map((option) => (
                  <option key={option.value} value={option.value}>{t(option.labelKey)}</option>
                ))}
              </select>
            </label>
          </div>

          <div className="table-shell">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("common.file")}</TableHead>
                  <TableHead>{t("common.format")}</TableHead>
                  <TableHead>{t("common.status")}</TableHead>
                  <TableHead className="text-right">{t("common.progress")}</TableHead>
                  <TableHead>{t("common.error")}</TableHead>
                  <TableHead className="text-right">{t("common.actions")}</TableHead>
                </TableRow>
              </TableHeader>
              {rows.length > 0 ? (
                <TableBody>
                  {rows.map((document) => (
                    <TableRow
                      key={document.id}
                      className={document.id === selectedId ? "bg-secondary/45" : undefined}
                      onClick={() => setSelectedId(document.id)}
                    >
                      <TableCell>
                        <div className="font-medium text-foreground">{document.file?.original_filename ?? document.id}</div>
                        <div className="mt-1 text-xs text-muted-foreground">{document.id}</div>
                      </TableCell>
                      <TableCell><Badge variant="neutral">{document.detected_type ?? document.file?.extension ?? t("common.notDetected")}</Badge></TableCell>
                      <TableCell><Badge variant={statusTone(document.status)}>{statusLabel(document.status, t)}</Badge></TableCell>
                      <TableCell className="text-right tabular-nums">{document.progress_percent}%</TableCell>
                      <TableCell>{document.last_error ?? document.warnings[0] ?? ""}</TableCell>
                      <TableCell>
                        <div className="flex justify-end gap-1">
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            aria-label={t("documents.previewAction")}
                            onClick={(event) => {
                              event.stopPropagation();
                              handlePreview(document);
                            }}
                          >
                            <Eye className="h-4 w-4" aria-hidden="true" />
                          </Button>
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            disabled={reprocessingIds.has(document.id)}
                            aria-label={t("documents.reprocessAction")}
                            onClick={(event) => {
                              event.stopPropagation();
                              handleReprocess(document.id);
                            }}
                          >
                            <RefreshCcw className={reprocessingIds.has(document.id) ? "h-4 w-4 animate-spin" : "h-4 w-4"} aria-hidden="true" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              ) : (
                <TableBody>
                  <TableRow>
                    <TableCell colSpan={6}>
                      <NoResults title={t("documents.noMatch.title")} description={t("documents.noMatch.description")} />
                    </TableCell>
                  </TableRow>
                </TableBody>
              )}
            </Table>
          </div>
        </CardContent>
      </Card>

      <Card className="xl:sticky xl:top-20 xl:self-start">
        <CardHeader>
          <div>
            <CardTitle>{t("common.details")}</CardTitle>
            <CardDescription>{detail?.file?.original_filename ?? detail?.id ?? t("common.document")}</CardDescription>
          </div>
          {detail ? <Badge variant={statusTone(detail.status)}>{statusLabel(detail.status, t)}</Badge> : null}
        </CardHeader>
        <CardContent className="space-y-4">
          {detailLoading ? <ProcessingInProgress /> : null}
          {detail ? (
            <>
              <MetricGrid summary={detail.parsed_summary} />
              <TimingInfo detail={detail} />
              <DetailBlock title="Parser summary" value={detail.parsed_summary} />
              <DetailBlock title="Row samples" value={detail.parsed_summary.row_samples ?? []} />
              <DetailBlock title="Events" value={detail.events.slice(0, 8)} />
            </>
          ) : (
            <NoResults title={t("documents.noMatch.title")} description={t("documents.noMatch.description")} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function MetricGrid({ summary }: { summary: Record<string, unknown> }) {
  const metrics: Array<[string, unknown]> = [
    ["Rows", summary.normalized_rows],
    ["Items", summary.recorded_price_items],
    ["Auto", summary.auto_matched],
    ["Review", summary.needs_review],
    ["Unmatched", summary.unmatched],
  ];
  return (
    <div className="grid grid-cols-2 gap-2">
      {metrics.map(([label, value]) => (
        <div key={label} className="rounded-md border border-border bg-background/45 p-3">
          <div className="text-xs uppercase text-muted-foreground">{label}</div>
          <div className="mt-1 text-lg font-semibold text-foreground">{String(value ?? 0)}</div>
        </div>
      ))}
    </div>
  );
}

function TimingInfo({ detail }: { detail: PriceDocumentDetail }) {
  const items: Array<[string, string]> = [];
  if (detail.parser_stage) items.push(["Stage", detail.parser_stage]);
  if (detail.duration_ms != null) items.push(["Duration", `${(detail.duration_ms / 1000).toFixed(1)}s`]);
  if (detail.processing_started_at) items.push(["Started", new Date(detail.processing_started_at).toLocaleString()]);
  if (detail.processing_finished_at) items.push(["Finished", new Date(detail.processing_finished_at).toLocaleString()]);
  if (detail.status === "processing" && detail.processing_started_at) {
    const elapsed = Date.now() - new Date(detail.processing_started_at).getTime();
    items.push(["Elapsed", `${(elapsed / 1000).toFixed(0)}s`]);
  }
  if (!items.length) return null;
  return (
    <div className="rounded-md border border-border bg-background/45 p-3">
      <h3 className="text-xs font-medium uppercase text-muted-foreground">Timing</h3>
      <div className="mt-2 grid grid-cols-2 gap-2 text-sm">
        {items.map(([label, value]) => (
          <div key={label}>
            <span className="text-muted-foreground">{label}: </span>
            <span className="font-medium text-foreground">{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function DetailBlock({ title, value }: { title: string; value: unknown }) {
  return (
    <section className="rounded-md border border-border bg-background/45 p-3">
      <h3 className="text-xs font-medium uppercase text-muted-foreground">{title}</h3>
      <pre className="mt-2 max-h-72 overflow-auto whitespace-pre-wrap text-xs leading-5 text-muted-foreground">
        {JSON.stringify(value, null, 2)}
      </pre>
    </section>
  );
}

function statusTone(status: string) {
  if (status === "parsed" || status === "completed") return "success";
  if (status === "processing") return "info";
  if (status === "failed") return "error";
  return "warning";
}

function statusLabel(status: string, t: ReturnType<typeof useI18n>["t"]) {
  const labels: Record<string, TranslationKey> = {
    pending: "common.pending",
    processing: "common.processing",
    parsed: "common.parsed",
    needs_review: "documents.attention",
    failed: "common.failed",
  };
  return labels[status] ? t(labels[status]) : status;
}
