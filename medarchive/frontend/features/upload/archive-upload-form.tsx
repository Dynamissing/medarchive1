"use client";

import type { ChangeEvent, DragEvent, FormEvent } from "react";
import { useEffect, useRef, useState } from "react";
import { AlertCircle, Archive, FileArchive, UploadCloud } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { NoDataYet, ProcessingInProgress, RetryError } from "@/components/ui/states";
import { useI18n } from "@/i18n";
import { getImportBatches, uploadArchive, type ArchiveImportResponse, type ImportBatchSummary } from "@/lib/api";
import { cn } from "@/lib/utils";

type UploadState = "idle" | "dragging" | "uploading" | "success" | "error";

export function ArchiveUploadForm() {
  const { t } = useI18n();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [state, setState] = useState<UploadState>("idle");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [batches, setBatches] = useState<ImportBatchSummary[]>([]);
  const [loadingBatches, setLoadingBatches] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ArchiveImportResponse | null>(null);

  useEffect(() => {
    refreshBatches();
  }, []);

  function refreshBatches() {
    setLoadingBatches(true);
    getImportBatches()
      .then((response) => {
        setBatches(response.items);
      })
      .catch((fetchError: unknown) => {
        setBatches([]);
        setError(fetchError instanceof Error ? fetchError.message : "Import batch request failed");
      })
      .finally(() => setLoadingBatches(false));
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    applySelectedFile(event.target.files?.[0] ?? null);
  }

  function handleDragOver(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    if (state !== "uploading") setState("dragging");
  }

  function handleDragLeave(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    if (state === "dragging") setState("idle");
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    if (state === "uploading") return;
    applySelectedFile(event.dataTransfer.files[0] ?? null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedFile || state === "uploading") return;

    setState("uploading");
    setError(null);
    setResult(null);
    try {
      const uploadResult = await uploadArchive(selectedFile);
      setResult(uploadResult);
      setState("success");
      setSelectedFile(null);
      refreshBatches();
    } catch (uploadError: unknown) {
      setState("error");
      setError(uploadError instanceof Error ? uploadError.message : "Archive upload failed");
    }
  }

  function applySelectedFile(file: File | null) {
    setResult(null);
    setError(null);
    if (!file) {
      setSelectedFile(null);
      setState("idle");
      return;
    }
    if (!isZipFile(file)) {
      setSelectedFile(null);
      setState("error");
      setError(t("upload.onlyZip"));
      return;
    }
    setSelectedFile(file);
    setState("idle");
  }

  const isUploading = state === "uploading";

  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_380px]">
      <Card>
        <CardHeader>
          <div>
            <CardTitle>{t("upload.cardTitle")}</CardTitle>
            <CardDescription>{t("upload.desc")}</CardDescription>
          </div>
          <Badge variant={stateTone(state)}>{stateLabel(state, t)}</Badge>
        </CardHeader>
        <CardContent>
          <form className="space-y-5" onSubmit={handleSubmit}>
            <div
              className={cn(
                "flex min-h-64 flex-col items-center justify-center rounded-lg border border-dashed border-border bg-background/45 px-6 py-8 text-center transition-colors",
                state === "dragging" && "border-primary bg-primary/10",
                state === "error" && "border-destructive/50 bg-destructive/10",
                state === "success" && "border-success/45 bg-success-subtle",
              )}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-md border border-border bg-secondary text-muted-foreground">
                {state === "error" ? <AlertCircle className="h-6 w-6 text-destructive" aria-hidden="true" /> : <UploadCloud className="h-6 w-6" aria-hidden="true" />}
              </div>

              <div className="mt-5 max-w-md">
                <h2 className="text-lg font-semibold">{t("upload.dropTitle")}</h2>
                <p className="mt-2">{t("upload.dropDesc")}</p>
              </div>

              <input ref={inputRef} className="hidden" type="file" accept=".zip,application/zip" onChange={handleFileChange} />

              <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
                <Button type="button" variant="secondary" disabled={isUploading} onClick={() => inputRef.current?.click()}>
                  <FileArchive className="h-4 w-4" aria-hidden="true" />
                  {t("upload.chooseZip")}
                </Button>
                <Badge variant="info">{t("upload.acceptedFormat")}</Badge>
              </div>

              {selectedFile ? (
                <div className="mt-5 rounded-md border border-border bg-card px-3 py-2 text-sm text-foreground">
                  {selectedFile.name}
                  <span className="ml-2 text-muted-foreground">{formatBytes(selectedFile.size)}</span>
                </div>
              ) : null}
            </div>

            {isUploading ? <ProcessingInProgress title={t("upload.inProgress")} description={t("upload.inProgressDesc")} /> : null}
            {error ? <RetryError title={t("upload.rejected")} description={error} onRetry={() => applySelectedFile(null)} /> : null}
            {result ? (
              <div className="rounded-md border border-success/35 bg-success-subtle p-3 text-sm text-success">
                {t("upload.queued")} · {result.extracted_files} {t("upload.files")} · {result.price_documents} {t("documents.cardTitle")}
              </div>
            ) : null}

            <div className="flex flex-col-reverse gap-3 sm:flex-row sm:items-center sm:justify-end">
              <Button type="button" variant="ghost" disabled={isUploading} onClick={() => applySelectedFile(null)}>
                {t("common.clear")}
              </Button>
              <Button type="submit" disabled={!selectedFile || isUploading}>
                <Archive className="h-4 w-4" aria-hidden="true" />
                {t("upload.submit")}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div>
            <CardTitle>{t("upload.recent")}</CardTitle>
            <CardDescription>{t("upload.recentDesc")}</CardDescription>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {loadingBatches ? <ProcessingInProgress /> : null}
          {!loadingBatches && batches.length === 0 ? <NoDataYet title={t("upload.noRecent.title")} description={t("upload.noRecent.description")} className="min-h-56" /> : null}
          {batches.map((batch) => (
            <div key={batch.id} className="rounded-md border border-border bg-background/45 p-3">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="truncate text-sm font-medium text-foreground">{batch.original_filename}</div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    {batch.processed_files}/{batch.total_files} · {new Date(batch.created_at).toLocaleString()}
                  </div>
                </div>
                <Badge variant={statusTone(batch.status)}>{batch.status}</Badge>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

function isZipFile(file: File) {
  return file.name.toLowerCase().endsWith(".zip") || file.type === "application/zip";
}

function formatBytes(bytes: number) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function stateLabel(state: UploadState, t: ReturnType<typeof useI18n>["t"]) {
  if (state === "success") return t("upload.queuedStatus");
  if (state === "uploading") return t("upload.uploading");
  if (state === "dragging") return t("upload.dropFile");
  if (state === "error") return t("common.error");
  return t("upload.idle");
}

function stateTone(state: UploadState) {
  if (state === "success") return "success";
  if (state === "uploading" || state === "dragging") return "info";
  if (state === "error") return "error";
  return "neutral";
}

function statusTone(status: string) {
  if (status === "completed") return "success";
  if (status === "processing") return "info";
  if (status === "failed") return "error";
  return "warning";
}
