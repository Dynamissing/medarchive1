"use client";

import type { LucideIcon } from "lucide-react";
import { AlertCircle, Database, Loader2, RefreshCw, SearchX } from "lucide-react";

import { Button } from "@/components/ui/button";
import { TableBody, TableCell, TableRow } from "@/components/ui/table";
import { useI18n } from "@/i18n";
import { cn } from "@/lib/utils";

export function TableSkeleton({
  rows = 5,
  columns = 5,
  wideColumn = 0,
}: {
  rows?: number;
  columns?: number;
  wideColumn?: number;
}) {
  return (
    <TableBody>
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <TableRow key={rowIndex}>
          {Array.from({ length: columns }).map((__, columnIndex) => (
            <TableCell key={columnIndex}>
              <div className={cn("h-3 rounded-full bg-secondary", columnIndex === wideColumn ? "w-44" : "w-20")} />
            </TableCell>
          ))}
        </TableRow>
      ))}
    </TableBody>
  );
}

export function CardSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div className="space-y-3 rounded-md border border-border bg-background/45 p-3">
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="h-14 rounded-md bg-secondary" />
      ))}
    </div>
  );
}

export function NoResults({
  title,
  description,
  className,
}: {
  title?: string;
  description?: string;
  className?: string;
}) {
  const { t } = useI18n();
  return <StateBlock icon={SearchX} title={title ?? t("states.noResults.title")} description={description ?? t("states.noResults.description")} className={className} />;
}

export function NoDataYet({
  title,
  description,
  className,
}: {
  title?: string;
  description?: string;
  className?: string;
}) {
  const { t } = useI18n();
  return <StateBlock icon={Database} title={title ?? t("states.noData.title")} description={description ?? t("states.noData.description")} className={className} />;
}

export function RetryError({
  title,
  description,
  onRetry,
}: {
  title?: string;
  description?: string;
  onRetry?: () => void;
}) {
  const { t } = useI18n();
  return (
    <div className="rounded-md border border-destructive/35 bg-destructive/10 p-4">
      <div className="flex items-start gap-3">
        <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" aria-hidden="true" />
        <div className="min-w-0">
          <h3 className="text-sm font-semibold text-destructive">{title ?? t("states.retry.title")}</h3>
          <p className="mt-1 text-xs leading-5 text-destructive">{description ?? t("states.retry.description")}</p>
          {onRetry ? (
            <Button type="button" variant="secondary" className="mt-3" onClick={onRetry}>
              <RefreshCw className="h-4 w-4" aria-hidden="true" />
              {t("common.retry")}
            </Button>
          ) : null}
        </div>
      </div>
    </div>
  );
}

export function ProcessingInProgress({
  title,
  description,
  className,
}: {
  title?: string;
  description?: string;
  className?: string;
}) {
  const { t } = useI18n();
  return (
    <div className={cn("flex items-center gap-3 rounded-md border border-info/30 bg-info-subtle p-3", className)}>
      <Loader2 className="h-4 w-4 shrink-0 animate-spin text-info" aria-hidden="true" />
      <div>
        <h3 className="text-sm font-semibold text-info">{title ?? t("states.processing.title")}</h3>
        <p className="mt-1 text-xs leading-5 text-info">{description ?? t("states.processing.description")}</p>
      </div>
    </div>
  );
}

function StateBlock({
  icon: Icon,
  title,
  description,
  className,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  className?: string;
}) {
  return (
    <div className={cn("flex min-h-44 flex-col items-center justify-center rounded-md border border-border bg-background/45 p-6 text-center", className)}>
      <div className="flex h-10 w-10 items-center justify-center rounded-md border border-border bg-secondary text-muted-foreground">
        <Icon className="h-5 w-5" aria-hidden="true" />
      </div>
      <h2 className="mt-4 text-base font-semibold text-foreground">{title}</h2>
      <p className="mt-2 max-w-sm text-sm text-muted-foreground">{description}</p>
    </div>
  );
}
