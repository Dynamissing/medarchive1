"use client";

import { useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { NoDataYet, ProcessingInProgress, RetryError } from "@/components/ui/states";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useI18n } from "@/i18n";
import { getUnmatched, manualMatchCandidate, searchBackend, type SearchResult, type UnmatchedCandidateSummary } from "@/lib/api";

export function UnmatchedPage() {
  const { t } = useI18n();
  const [rows, setRows] = useState<UnmatchedCandidateSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [serviceQuery, setServiceQuery] = useState("");
  const [serviceResults, setServiceResults] = useState<SearchResult[]>([]);
  const [selectedServiceId, setSelectedServiceId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function loadRows() {
    setLoading(true);
    setError(null);
    getUnmatched()
      .then((response) => {
        setRows(response.items);
        setSelectedId((current) => current ?? response.items[0]?.id ?? null);
      })
      .catch((fetchError: unknown) => {
        setRows([]);
        setSelectedId(null);
        setError(fetchError instanceof Error ? fetchError.message : "Unmatched queue request failed");
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    loadRows();
  }, []);

  const selected = useMemo(
    () => rows.find((row) => row.id === selectedId) ?? rows[0] ?? null,
    [rows, selectedId],
  );

  useEffect(() => {
    const query = serviceQuery.trim();
    if (!query) {
      setServiceResults([]);
      setSelectedServiceId(null);
      return;
    }
    const timer = window.setTimeout(() => {
      searchBackend(query, 1, 8, "service")
        .then((response) => setServiceResults(response.items))
        .catch((fetchError: unknown) => setError(fetchError instanceof Error ? fetchError.message : "Service search failed"));
    }, 250);
    return () => window.clearTimeout(timer);
  }, [serviceQuery]);

  async function handleManualMatch() {
    if (!selected || !selectedServiceId) return;
    setSubmitting(true);
    setError(null);
    try {
      await manualMatchCandidate(selected.id, selectedServiceId);
      setServiceQuery("");
      setServiceResults([]);
      setSelectedServiceId(null);
      loadRows();
    } catch (matchError: unknown) {
      setError(matchError instanceof Error ? matchError.message : "Manual match failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_430px]">
      <Card>
        <CardHeader>
          <div>
            <CardTitle>{t("unmatched.queueTitle")}</CardTitle>
            <CardDescription>{t("unmatched.queueDesc")}</CardDescription>
          </div>
          <Badge variant="neutral">{rows.length} {t("unmatched.unresolved")}</Badge>
        </CardHeader>
        <CardContent className="space-y-4">
          {loading ? <ProcessingInProgress /> : null}
          {error ? <RetryError description={error} onRetry={loadRows} /> : null}

          <div className="table-shell">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("unmatched.extractedRow")}</TableHead>
                  <TableHead>{t("common.code")}</TableHead>
                  <TableHead className="text-right">{t("common.score")}</TableHead>
                  <TableHead>{t("common.createdAt")}</TableHead>
                </TableRow>
              </TableHeader>
              {rows.length > 0 ? (
                <TableBody>
                  {rows.map((row) => (
                    <TableRow
                      key={row.id}
                      className={row.id === selected?.id ? "bg-secondary/45" : undefined}
                      onClick={() => setSelectedId(row.id)}
                    >
                      <TableCell>
                        <div className="max-w-[360px] truncate font-medium text-foreground">{row.normalized_query || row.row_hash}</div>
                        <div className="mt-1 text-xs text-muted-foreground">{row.id}</div>
                      </TableCell>
                      <TableCell>{row.source_code ?? "-"}</TableCell>
                      <TableCell className="text-right tabular-nums">{formatScore(row.score)}</TableCell>
                      <TableCell>{formatDate(row.created_at)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              ) : (
                <TableBody>
                  <TableRow>
                    <TableCell colSpan={4}>
                      <NoDataYet title={t("unmatched.noData.title")} description={t("unmatched.noData.description")} />
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
            <CardTitle>{t("unmatched.manualMatch")}</CardTitle>
            <CardDescription>{t("unmatched.currentRow")}</CardDescription>
          </div>
          {selected ? <Badge variant="warning">{formatScore(selected.score)}</Badge> : null}
        </CardHeader>
        <CardContent className="space-y-4">
          {selected ? (
            <>
              <DetailRow label={t("unmatched.extractedRow")} value={selected.normalized_query || selected.row_hash} />
              <DetailRow label={t("common.code")} value={selected.source_code ?? "-"} />
              <DetailRow label={t("common.document")} value={selected.price_document_id ?? "-"} />
              <DetailRow label={t("common.createdAt")} value={formatDate(selected.created_at)} />
              <section className="rounded-md border border-border bg-background/45 p-3">
                <h3 className="text-xs font-medium uppercase text-muted-foreground">{t("unmatched.candidateServices")}</h3>
                <Input
                  className="mt-3"
                  value={serviceQuery}
                  onChange={(event) => setServiceQuery(event.target.value)}
                  placeholder={selected.normalized_query || "Search service"}
                />
                <div className="mt-3 space-y-2">
                  {serviceResults.map((service) => (
                    <button
                      key={service.id}
                      type="button"
                      className={selectedServiceId === service.id ? "w-full rounded-md border border-primary bg-primary/10 p-2 text-left text-sm text-foreground" : "w-full rounded-md border border-border bg-card p-2 text-left text-sm text-foreground"}
                      onClick={() => setSelectedServiceId(service.id)}
                    >
                      <span className="font-medium">{service.label}</span>
                      <span className="ml-2 text-xs text-muted-foreground">{stringValue(service.payload.code)}</span>
                    </button>
                  ))}
                </div>
                <Button className="mt-3 w-full" disabled={!selectedServiceId || submitting} onClick={handleManualMatch}>
                  {submitting ? t("common.processing") : "Match"}
                </Button>
              </section>
              <section className="rounded-md border border-border bg-background/45 p-3">
                <h3 className="text-xs font-medium uppercase text-muted-foreground">{t("common.details")}</h3>
                <pre className="mt-2 max-h-72 overflow-auto whitespace-pre-wrap text-xs leading-5 text-muted-foreground">
                  {JSON.stringify(selected.explanation ?? {}, null, 2)}
                </pre>
              </section>
            </>
          ) : (
            <NoDataYet title={t("unmatched.noMatches.title")} description={t("unmatched.noMatches.description")} className="min-h-40" />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function stringValue(value: unknown) {
  if (typeof value === "string") return value;
  if (typeof value === "number") return String(value);
  return "";
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-background/45 p-3">
      <div className="text-xs font-medium uppercase text-muted-foreground">{label}</div>
      <div className="mt-1 break-words text-sm text-foreground">{value}</div>
    </div>
  );
}

function formatScore(score: number) {
  return `${Math.round(score * 100)}%`;
}

function formatDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}
