"use client";

import { useState } from "react";
import { CheckCircle2, GitCompareArrows, ShieldAlert, ThumbsDown } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useI18n, type TranslationKey } from "@/i18n";
import { cn } from "@/lib/utils";
import {
  verificationQueueMock,
  type CandidateService,
  type VerificationItem,
  type VerificationPriority,
  type VerificationStatus,
} from "@/features/verification/mock-data";

export function VerificationPage() {
  const { t } = useI18n();
  const [selectedId, setSelectedId] = useState(verificationQueueMock[0]?.id ?? "");
  const selected = verificationQueueMock.find((item) => item.id === selectedId) ?? verificationQueueMock[0];

  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_420px]">
      <Card>
        <CardHeader>
          <div>
            <CardTitle>{t("verification.queueTitle")}</CardTitle>
            <CardDescription>{t("verification.queueDesc")}</CardDescription>
          </div>
          <Badge variant="warning">{verificationQueueMock.length} {t("verification.openCount")}</Badge>
        </CardHeader>
        <CardContent className="p-0">
          <div className="table-shell rounded-none border-x-0 border-b-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("verification.extractedService")}</TableHead>
                  <TableHead>{t("common.partner")}</TableHead>
                  <TableHead>{t("verification.priority")}</TableHead>
                  <TableHead>{t("common.status")}</TableHead>
                  <TableHead>{t("verification.anomalies")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {verificationQueueMock.map((item) => (
                  <TableRow
                    key={item.id}
                    className={cn("cursor-pointer", item.id === selected.id && "bg-secondary/55")}
                    onClick={() => setSelectedId(item.id)}
                  >
                    <TableCell>
                      <button
                        className="block max-w-64 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                        type="button"
                        onClick={() => setSelectedId(item.id)}
                      >
                        <span className="block truncate font-medium text-foreground">{item.extractedName}</span>
                        <span className="mt-1 block text-xs text-muted-foreground">{item.document}</span>
                      </button>
                    </TableCell>
                    <TableCell>{item.partner}</TableCell>
                    <TableCell>
                      <Badge variant={priorityTone(item.priority)}>{priorityLabel(item.priority, t)}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={statusTone(item.status)}>{statusLabel(item.status, t)}</Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {item.anomalies.slice(0, 2).map((anomaly) => (
                          <Badge key={anomaly} variant="error">
                            {shortAnomaly(anomaly)}
                          </Badge>
                        ))}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <DetailPanel item={selected} />
    </div>
  );
}

function DetailPanel({ item }: { item: VerificationItem }) {
  const { t } = useI18n();
  return (
    <Card className="xl:sticky xl:top-20 xl:self-start">
      <CardHeader>
        <div>
          <CardTitle>{t("verification.detail")}</CardTitle>
          <CardDescription>{item.id}</CardDescription>
        </div>
        <Badge variant={priorityTone(item.priority)}>{priorityLabel(item.priority, t)}</Badge>
      </CardHeader>
      <CardContent className="space-y-5">
        <section>
          <h3>{t("verification.sourceSnippet")}</h3>
          <div className="mt-3 rounded-md border border-border bg-background/55 p-3 font-mono text-xs leading-5 text-muted-foreground">
            {item.snippet}
          </div>
        </section>

        <section>
          <h3>{t("verification.extractedFields")}</h3>
          <div className="mt-3 divide-y divide-border rounded-md border border-border bg-background/45">
            {item.extractedFields.map((field) => (
              <div key={field.label} className="grid grid-cols-[130px_minmax(0,1fr)] gap-3 px-3 py-2 text-sm">
                <span className="text-muted-foreground">{field.label}</span>
                <span className="truncate text-foreground">{field.value}</span>
              </div>
            ))}
          </div>
        </section>

        <section>
          <div className="flex items-center justify-between gap-3">
            <h3>{t("verification.candidates")}</h3>
            <Badge variant="info">{item.candidates.length} {t("verification.candidateCount")}</Badge>
          </div>
          <div className="mt-3 space-y-2">
            {item.candidates.map((candidate, index) => (
              <CandidateCard key={candidate.id} candidate={candidate} selected={index === 0} />
            ))}
          </div>
        </section>

        <section>
          <h3>{t("verification.anomalyFlags")}</h3>
          <div className="mt-3 flex flex-wrap gap-2">
            {item.anomalies.map((anomaly) => (
              <Badge key={anomaly} variant="error" className="gap-1">
                <ShieldAlert className="h-3.5 w-3.5" aria-hidden="true" />
                {shortAnomaly(anomaly)}
              </Badge>
            ))}
          </div>
        </section>

        <div className="grid gap-2 sm:grid-cols-3">
          <Button type="button" aria-keyshortcuts="A">
            <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
            {t("verification.approve")}
          </Button>
          <Button type="button" variant="secondary" aria-keyshortcuts="R">
            <GitCompareArrows className="h-4 w-4" aria-hidden="true" />
            {t("verification.rematch")}
          </Button>
          <Button type="button" variant="ghost" aria-keyshortcuts="X">
            <ThumbsDown className="h-4 w-4" aria-hidden="true" />
            {t("verification.reject")}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function CandidateCard({ candidate, selected }: { candidate: CandidateService; selected: boolean }) {
  return (
    <div className={cn("rounded-md border border-border bg-background/45 p-3", selected && "border-primary/45 bg-primary/10")}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="truncate text-sm font-medium text-foreground">{candidate.name}</div>
          <div className="mt-1 text-xs text-muted-foreground">
            {candidate.code} - {candidate.reason}
          </div>
        </div>
        <Badge variant={confidenceTone(candidate.confidence)}>{candidate.confidence}%</Badge>
      </div>
      <div className="mt-3 h-2 rounded-full bg-secondary">
        <div className={confidenceBar(candidate.confidence)} style={{ width: `${candidate.confidence}%` }} />
      </div>
    </div>
  );
}

function priorityTone(priority: VerificationPriority) {
  if (priority === "high") return "error";
  if (priority === "medium") return "warning";
  return "info";
}

function statusTone(status: VerificationStatus) {
  if (status === "open") return "warning";
  if (status === "in_review") return "info";
  return "error";
}

function statusLabel(status: VerificationStatus, t: ReturnType<typeof useI18n>["t"]) {
  const labels: Record<VerificationStatus, TranslationKey> = {
    open: "common.open",
    in_review: "common.inReview",
    blocked: "common.blocked",
  };
  return t(labels[status]);
}

function priorityLabel(priority: VerificationPriority, t: ReturnType<typeof useI18n>["t"]) {
  const labels: Record<VerificationPriority, TranslationKey> = {
    high: "common.high",
    medium: "common.medium",
    low: "common.low",
  };
  return t(labels[priority]);
}

function confidenceTone(confidence: number) {
  if (confidence >= 88) return "success";
  if (confidence >= 72) return "warning";
  return "error";
}

function confidenceBar(confidence: number) {
  const base = "h-full rounded-full";
  if (confidence >= 88) return `${base} bg-success`;
  if (confidence >= 72) return `${base} bg-warning`;
  return `${base} bg-destructive`;
}

function shortAnomaly(value: string) {
  return value.replaceAll("_", " ");
}
