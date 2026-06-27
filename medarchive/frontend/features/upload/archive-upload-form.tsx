"use client";

import type { ChangeEvent, DragEvent, FormEvent } from "react";
import { useRef, useState } from "react";
import { AlertCircle, Archive, CheckCircle2, FileArchive, Loader2, UploadCloud } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ProcessingInProgress, RetryError } from "@/components/ui/states";
import { useI18n, type TranslationKey } from "@/i18n";
import { cn } from "@/lib/utils";

type UploadState = "idle" | "dragging" | "uploading" | "success" | "error";
type RecentUploadStatus = "completed" | "processing" | "failed";

type RecentUpload = {
  id: string;
  filename: string;
  status: RecentUploadStatus;
  files: number;
  uploadedAt: string;
};

const recentUploads: RecentUpload[] = [
  { id: "up-1042", filename: "clinic-08-prices.zip", status: "processing", files: 38, uploadedAt: "9 min ago" },
  { id: "up-1041", filename: "clinic-07-contracts.zip", status: "completed", files: 21, uploadedAt: "46 min ago" },
  { id: "up-1040", filename: "legacy-scan-pack.zip", status: "failed", files: 14, uploadedAt: "Yesterday" },
];

export function ArchiveUploadForm() {
  const { t } = useI18n();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [state, setState] = useState<UploadState>("idle");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);
  const [messageKey, setMessageKey] = useState<TranslationKey>("upload.zipOnly");

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;
    applySelectedFile(file);
  }

  function handleDragOver(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    if (state !== "uploading") {
      setState("dragging");
    }
  }

  function handleDragLeave(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    if (state === "dragging") {
      setState("idle");
    }
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    if (state === "uploading") {
      return;
    }
    applySelectedFile(event.dataTransfer.files[0] ?? null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedFile || state === "uploading") {
      return;
    }

    setState("uploading");
    setProgress(12);
    setMessageKey("upload.uploading");
    await mockUploadProgress(setProgress);
    setState("success");
    setProgress(100);
    setMessageKey("upload.queued");
  }

  function applySelectedFile(file: File | null) {
    setProgress(0);
    if (!file) {
      setSelectedFile(null);
      setState("idle");
      setMessageKey("upload.zipOnly");
      return;
    }
    if (!isZipFile(file)) {
      setSelectedFile(null);
      setState("error");
      setMessageKey("upload.onlyZip");
      return;
    }
    setSelectedFile(file);
    setState("idle");
    setMessageKey("upload.ready");
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
                {isUploading ? (
                  <Loader2 className="h-6 w-6 animate-spin" aria-hidden="true" />
                ) : state === "success" ? (
                  <CheckCircle2 className="h-6 w-6 text-success" aria-hidden="true" />
                ) : state === "error" ? (
                  <AlertCircle className="h-6 w-6 text-destructive" aria-hidden="true" />
                ) : (
                  <UploadCloud className="h-6 w-6" aria-hidden="true" />
                )}
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

            <div className="space-y-2">
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm text-muted-foreground">{t(messageKey)}</span>
                <span className="text-sm font-medium tabular-nums text-foreground">{progress}%</span>
              </div>
              <div className="h-2 rounded-full bg-secondary">
                <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${progress}%` }} />
              </div>
            </div>

            {state === "uploading" ? (
              <ProcessingInProgress title={t("upload.inProgress")} description={t("upload.inProgressDesc")} />
            ) : null}

            {state === "error" ? (
              <RetryError title={t("upload.rejected")} description={t(messageKey)} onRetry={() => applySelectedFile(null)} />
            ) : null}

            <div className="flex flex-col-reverse gap-3 sm:flex-row sm:items-center sm:justify-end">
              <Button type="button" variant="ghost" disabled={isUploading} onClick={() => applySelectedFile(null)}>
                {t("common.clear")}
              </Button>
              <Button type="submit" disabled={!selectedFile || isUploading}>
                {isUploading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : <Archive className="h-4 w-4" aria-hidden="true" />}
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
          {recentUploads.map((upload) => (
            <div key={upload.id} className="rounded-md border border-border bg-background/45 p-3">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="truncate text-sm font-medium text-foreground">{upload.filename}</div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    {upload.files} {t("upload.files")} - {upload.uploadedAt}
                  </div>
                </div>
                <Badge variant={recentTone(upload.status)}>{recentLabel(upload.status, t)}</Badge>
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

async function mockUploadProgress(setProgress: (value: number) => void) {
  for (const value of [28, 44, 63, 81, 94]) {
    await new Promise((resolve) => window.setTimeout(resolve, 220));
    setProgress(value);
  }
}

function formatBytes(bytes: number) {
  if (bytes < 1024 * 1024) {
    return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function stateLabel(state: UploadState, t: ReturnType<typeof useI18n>["t"]) {
  const labels: Record<UploadState, TranslationKey> = {
    idle: "upload.idle",
    dragging: "upload.dropFile",
    uploading: "upload.uploading",
    success: "upload.queuedStatus",
    error: "common.error",
  };
  return t(labels[state]);
}

function stateTone(state: UploadState) {
  if (state === "success") return "success";
  if (state === "uploading" || state === "dragging") return "info";
  if (state === "error") return "error";
  return "neutral";
}

function recentLabel(status: RecentUploadStatus, t: ReturnType<typeof useI18n>["t"]) {
  const labels: Record<RecentUploadStatus, TranslationKey> = {
    completed: "common.completed",
    processing: "common.processing",
    failed: "common.failed",
  };
  return t(labels[status]);
}

function recentTone(status: RecentUploadStatus) {
  if (status === "completed") return "success";
  if (status === "processing") return "info";
  return "error";
}
