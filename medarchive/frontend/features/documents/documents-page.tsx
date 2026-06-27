"use client";

import { useMemo, useState } from "react";
import { Eye, MoreHorizontal, RefreshCcw, RotateCw } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { NoResults, TableSkeleton } from "@/components/ui/states";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useI18n, type TranslationKey } from "@/i18n";
import { documentsMock, type DocumentFormat, type DocumentStatus } from "@/features/documents/mock-data";

type StatusFilter = "all" | DocumentStatus;
type FormatFilter = "all" | DocumentFormat;

const statusOptions: Array<{ value: StatusFilter; labelKey: TranslationKey }> = [
  { value: "all", labelKey: "documents.allStatuses" },
  { value: "pending", labelKey: "common.pending" },
  { value: "processing", labelKey: "common.processing" },
  { value: "parsed", labelKey: "common.parsed" },
  { value: "failed", labelKey: "common.failed" },
];

const formatOptions: Array<{ value: FormatFilter; labelKey?: TranslationKey; label?: string }> = [
  { value: "all", labelKey: "documents.allFormats" },
  { value: "xlsx", label: "XLSX" },
  { value: "xls", label: "XLS" },
  { value: "docx", label: "DOCX" },
  { value: "pdf_text", label: "PDF text" },
  { value: "pdf_ocr_candidate", label: "PDF OCR" },
];

export function DocumentsPage() {
  const { t } = useI18n();
  const [status, setStatus] = useState<StatusFilter>("all");
  const [format, setFormat] = useState<FormatFilter>("all");
  const [loadingPreview, setLoadingPreview] = useState(false);

  const rows = useMemo(() => {
    return documentsMock.filter((document) => {
      const statusMatches = status === "all" || document.status === status;
      const formatMatches = format === "all" || document.format === format;
      return statusMatches && formatMatches;
    });
  }, [status, format]);

  return (
    <div className="space-y-5">
      <section className="grid gap-4 md:grid-cols-4">
        <SummaryCard label={t("documents.total")} value={documentsMock.length} tone="info" />
        <SummaryCard label={t("common.parsed")} value={documentsMock.filter((item) => item.status === "parsed").length} tone="success" />
        <SummaryCard label={t("common.processing")} value={documentsMock.filter((item) => item.status === "processing").length} tone="info" />
        <SummaryCard label={t("documents.attention")} value={documentsMock.filter((item) => item.status === "failed").length} tone="error" />
      </section>

      <Card>
        <CardHeader>
          <div>
            <CardTitle>{t("documents.cardTitle")}</CardTitle>
            <CardDescription>{t("documents.desc")}</CardDescription>
          </div>
          <Badge variant="neutral">{rows.length} {t("common.visible")}</Badge>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div className="flex flex-col gap-3 sm:flex-row">
              <FilterSelect label={t("common.status")} value={status} onChange={(value) => setStatus(value as StatusFilter)} options={statusOptions} />
              <FilterSelect label={t("common.format")} value={format} onChange={(value) => setFormat(value as FormatFilter)} options={formatOptions} />
            </div>
            <div className="flex flex-wrap gap-2">
              <Button className="flex-1 sm:flex-none" type="button" variant="secondary" onClick={() => setLoadingPreview((value) => !value)}>
                <RotateCw className="h-4 w-4" aria-hidden="true" />
                {loadingPreview ? t("documents.showRows") : t("documents.previewLoading")}
              </Button>
              <Button
                className="flex-1 sm:flex-none"
                type="button"
                variant="ghost"
                onClick={() => {
                  setStatus("all");
                  setFormat("all");
                  setLoadingPreview(false);
                }}
              >
                {t("common.reset")}
              </Button>
            </div>
          </div>

          <div className="table-shell">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("common.file")}</TableHead>
                  <TableHead>{t("common.partner")}</TableHead>
                  <TableHead>{t("common.date")}</TableHead>
                  <TableHead>{t("common.format")}</TableHead>
                  <TableHead>{t("common.status")}</TableHead>
                  <TableHead>{t("documents.parsedAt")}</TableHead>
                  <TableHead className="text-right">{t("common.actions")}</TableHead>
                </TableRow>
              </TableHeader>
              {loadingPreview ? (
                <TableSkeleton rows={5} columns={7} />
              ) : rows.length > 0 ? (
                <DocumentsRows rows={rows} />
              ) : (
                <TableBody>
                  <TableRow>
                    <TableCell colSpan={7}>
                      <NoResults title={t("documents.noMatch.title")} description={t("documents.noMatch.description")} />
                    </TableCell>
                  </TableRow>
                </TableBody>
              )}
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function DocumentsRows({ rows }: { rows: typeof documentsMock }) {
  const { t } = useI18n();
  return (
    <TableBody>
      {rows.map((document) => (
        <TableRow key={document.id}>
          <TableCell>
            <div className="font-medium text-foreground">{document.file}</div>
            <div className="mt-1 text-xs text-muted-foreground">{document.id}</div>
          </TableCell>
          <TableCell>{document.partner ?? t("common.unknown")}</TableCell>
          <TableCell>{document.date ?? t("common.notDetected")}</TableCell>
          <TableCell>
            <Badge variant="neutral">{formatLabel(document.format)}</Badge>
          </TableCell>
          <TableCell>
            <Badge variant={statusTone(document.status)}>{statusLabel(document.status, t)}</Badge>
          </TableCell>
          <TableCell>{document.parsed_at ?? t("common.pending")}</TableCell>
          <TableCell>
            <div className="flex justify-end gap-1">
              <Button type="button" variant="ghost" size="icon" aria-label={`${t("documents.previewAction")} ${document.file}`}>
                <Eye className="h-4 w-4" aria-hidden="true" />
              </Button>
              <Button type="button" variant="ghost" size="icon" aria-label={`${t("documents.reprocessAction")} ${document.file}`}>
                <RefreshCcw className="h-4 w-4" aria-hidden="true" />
              </Button>
              <Button type="button" variant="ghost" size="icon" aria-label={`${t("documents.moreAction")} ${document.file}`}>
                <MoreHorizontal className="h-4 w-4" aria-hidden="true" />
              </Button>
            </div>
          </TableCell>
        </TableRow>
      ))}
    </TableBody>
  );
}

function FilterSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: Array<{ value: string; labelKey?: TranslationKey; label?: string }>;
}) {
  const { t } = useI18n();
  return (
    <label className="flex min-w-44 flex-col gap-2">
      <span className="text-xs font-medium uppercase text-muted-foreground">{label}</span>
      <select
        className="h-9 rounded-md border border-input bg-background/65 px-3 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.labelKey ? t(option.labelKey) : option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function SummaryCard({ label, value, tone }: { label: string; value: number; tone: "success" | "error" | "info" }) {
  return (
    <Card>
      <CardContent>
        <p className="text-xs font-medium uppercase text-muted-foreground">{label}</p>
        <div className="mt-2 flex items-end justify-between gap-3">
          <span className="text-3xl font-semibold text-foreground">{value}</span>
          <Badge variant={tone}>{label}</Badge>
        </div>
      </CardContent>
    </Card>
  );
}

function statusTone(status: DocumentStatus) {
  if (status === "parsed") return "success";
  if (status === "processing") return "info";
  if (status === "failed") return "error";
  return "warning";
}

function statusLabel(status: DocumentStatus, t: ReturnType<typeof useI18n>["t"]) {
  const labels: Record<DocumentStatus, TranslationKey> = {
    pending: "common.pending",
    processing: "common.processing",
    parsed: "common.parsed",
    failed: "common.failed",
  };
  return t(labels[status]);
}

function formatLabel(format: DocumentFormat) {
  const labels: Record<DocumentFormat, string> = {
    xlsx: "XLSX",
    xls: "XLS",
    docx: "DOCX",
    pdf_text: "PDF text",
    pdf_ocr_candidate: "PDF OCR",
  };
  return labels[format];
}
