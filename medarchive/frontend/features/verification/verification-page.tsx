"use client";

import { useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { NoDataYet, ProcessingInProgress, RetryError } from "@/components/ui/states";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useI18n } from "@/i18n";
import { getVerification, resolveVerification, type VerificationItem } from "@/lib/api";

export function VerificationPage() {
  const { t } = useI18n();
  const [rows, setRows] = useState<VerificationItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resolvingId, setResolvingId] = useState<string | null>(null);

  function loadRows() {
    setLoading(true);
    setError(null);
    getVerification()
      .then((response) => {
        setRows(response.items);
        setSelectedId((current) => current ?? response.items[0]?.id ?? null);
      })
      .catch((fetchError: unknown) => {
        setRows([]);
        setSelectedId(null);
        setError(fetchError instanceof Error ? fetchError.message : "Verification queue request failed");
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

  async function handleResolve(actionId: string) {
    setResolvingId(actionId);
    setError(null);
    try {
      await resolveVerification(actionId);
      loadRows();
    } catch (resolveError: unknown) {
      setError(resolveError instanceof Error ? resolveError.message : "Verification resolve failed");
    } finally {
      setResolvingId(null);
    }
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_420px]">
      <Card>
        <CardHeader>
          <div>
            <CardTitle>{t("verification.queueTitle")}</CardTitle>
            <CardDescription>{t("verification.queueDesc")}</CardDescription>
          </div>
          <Badge variant="neutral">{rows.length} {t("verification.openCount")}</Badge>
        </CardHeader>
        <CardContent className="space-y-4">
          {loading ? <ProcessingInProgress /> : null}
          {error ? <RetryError description={error} onRetry={loadRows} /> : null}

          <div className="table-shell">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("common.type")}</TableHead>
                  <TableHead>{t("common.status")}</TableHead>
                  <TableHead>{t("verification.anomalies")}</TableHead>
                  <TableHead>{t("verification.priority")}</TableHead>
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
                        <div className="font-medium text-foreground">{row.action_type}</div>
                        <div className="mt-1 text-xs text-muted-foreground">{row.id}</div>
                      </TableCell>
                      <TableCell><Badge variant={statusTone(row.status)}>{row.status}</Badge></TableCell>
                      <TableCell>{row.anomaly_code ?? "-"}</TableCell>
                      <TableCell><Badge variant={severityTone(row.severity)}>{row.severity ?? "-"}</Badge></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              ) : (
                <TableBody>
                  <TableRow>
                    <TableCell colSpan={4}>
                      <NoDataYet title={t("verification.noData.title")} description={t("verification.noData.description")} />
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
            <CardTitle>{t("verification.detail")}</CardTitle>
            <CardDescription>{t("verification.extractedFields")}</CardDescription>
          </div>
          {selected ? <Badge variant={severityTone(selected.severity)}>{selected.severity ?? selected.status}</Badge> : null}
        </CardHeader>
        <CardContent className="space-y-4">
          {selected ? (
            <>
              <DetailRow label={t("common.type")} value={selected.action_type} />
              <DetailRow label={t("common.status")} value={selected.status} />
              <DetailRow label={t("verification.anomalyFlags")} value={selected.anomaly_message ?? selected.anomaly_code ?? "-"} />
              <DetailRow label={t("common.notes")} value={selected.notes ?? "-"} />
              <Button
                className="w-full"
                disabled={selected.status === "completed" || resolvingId === selected.id}
                onClick={() => handleResolve(selected.id)}
              >
                {resolvingId === selected.id ? t("common.processing") : "Resolve"}
              </Button>
              <section className="rounded-md border border-border bg-background/45 p-3">
                <h3 className="text-xs font-medium uppercase text-muted-foreground">{t("common.payload")}</h3>
                <pre className="mt-2 max-h-72 overflow-auto whitespace-pre-wrap text-xs leading-5 text-muted-foreground">
                  {JSON.stringify(selected.payload ?? {}, null, 2)}
                </pre>
              </section>
            </>
          ) : (
            <NoDataYet title={t("verification.noSelection.title")} description={t("verification.noSelection.description")} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-background/45 p-3">
      <div className="text-xs font-medium uppercase text-muted-foreground">{label}</div>
      <div className="mt-1 break-words text-sm text-foreground">{value}</div>
    </div>
  );
}

function statusTone(status: string) {
  if (status === "completed" || status === "verified" || status === "resolved") return "success";
  if (status === "rejected" || status === "failed") return "error";
  if (status === "in_progress") return "info";
  return "warning";
}

function severityTone(severity: string | null) {
  if (severity === "high" || severity === "critical") return "error";
  if (severity === "medium") return "warning";
  if (severity === "low") return "info";
  return "neutral";
}
