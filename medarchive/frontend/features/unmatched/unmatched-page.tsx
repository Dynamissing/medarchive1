"use client";

import { useMemo, useState } from "react";
import { CheckCircle2, Search, XCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { CardSkeleton, NoResults, ProcessingInProgress, RetryError } from "@/components/ui/states";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useI18n, type TranslationKey } from "@/i18n";
import { cn } from "@/lib/utils";
import {
  directoryResultsMock,
  unmatchedItemsMock,
  type DirectoryServiceResult,
  type UnmatchedItem,
  type UnmatchedStatus,
} from "@/features/unmatched/mock-data";

type PanelState = "ready" | "loading" | "error" | "empty";

export function UnmatchedPage() {
  const { t } = useI18n();
  const [selectedId, setSelectedId] = useState(unmatchedItemsMock[0]?.id ?? "");
  const [query, setQuery] = useState("blood");
  const [selectedServiceId, setSelectedServiceId] = useState(directoryResultsMock[0]?.id ?? "");
  const [panelState, setPanelState] = useState<PanelState>("ready");
  const [notes, setNotes] = useState("");

  const selectedItem = unmatchedItemsMock.find((item) => item.id === selectedId) ?? unmatchedItemsMock[0];
  const results = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) {
      return directoryResultsMock;
    }
    return directoryResultsMock.filter((service) =>
      [service.name, service.code, service.specialty].some((value) => value.toLowerCase().includes(normalized)),
    );
  }, [query]);
  const visibleResults = panelState === "empty" ? [] : results;

  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_430px]">
      <Card>
        <CardHeader>
          <div>
            <CardTitle>{t("unmatched.queueTitle")}</CardTitle>
            <CardDescription>{t("unmatched.queueDesc")}</CardDescription>
          </div>
          <Badge variant="warning">{unmatchedItemsMock.length} {t("unmatched.unresolved")}</Badge>
        </CardHeader>
        <CardContent className="p-0">
          <div className="table-shell rounded-none border-x-0 border-b-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("unmatched.extractedRow")}</TableHead>
                  <TableHead>{t("common.partner")}</TableHead>
                  <TableHead>{t("common.code")}</TableHead>
                  <TableHead>{t("common.amount")}</TableHead>
                  <TableHead>{t("common.status")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {unmatchedItemsMock.map((item) => (
                  <TableRow
                    key={item.id}
                    className={cn("cursor-pointer", item.id === selectedItem.id && "bg-secondary/55")}
                    onClick={() => {
                      setSelectedId(item.id);
                      setQuery(seedQuery(item));
                    }}
                  >
                    <TableCell>
                      <button
                        type="button"
                        className="block max-w-72 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                        onClick={() => {
                          setSelectedId(item.id);
                          setQuery(seedQuery(item));
                        }}
                      >
                        <span className="block truncate font-medium text-foreground">{item.normalizedQuery}</span>
                        <span className="mt-1 block text-xs text-muted-foreground">{item.reason}</span>
                      </button>
                    </TableCell>
                    <TableCell>{item.partner}</TableCell>
                    <TableCell>{item.sourceCode ?? t("common.none")}</TableCell>
                    <TableCell>{item.amount}</TableCell>
                    <TableCell>
                      <Badge variant={statusTone(item.status)}>{statusLabel(item.status, t)}</Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <Card className="xl:sticky xl:top-20 xl:self-start">
        <CardHeader>
          <div>
            <CardTitle>{t("unmatched.manualMatch")}</CardTitle>
            <CardDescription>{selectedItem.id}</CardDescription>
          </div>
          <Badge variant="info">{selectedItem.document}</Badge>
        </CardHeader>
        <CardContent className="space-y-5">
          <section className="rounded-md border border-border bg-background/45 p-3">
            <div className="text-xs font-medium uppercase text-muted-foreground">{t("unmatched.currentRow")}</div>
            <div className="mt-2 text-sm font-medium text-foreground">{selectedItem.normalizedQuery}</div>
            <div className="mt-2 text-xs text-muted-foreground">
              {selectedItem.partner} - {selectedItem.amount}
            </div>
          </section>

          <section className="space-y-3">
            <div>
              <label className="text-xs font-medium uppercase text-muted-foreground" htmlFor="service-search">
                {t("unmatched.searchDirectory")}
              </label>
              <div className="mt-2 flex gap-2">
                <Input
                  id="service-search"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder={t("unmatched.searchPlaceholder")}
                />
                <Button type="button" variant="secondary" size="icon" aria-label={t("common.search")}>
                  <Search className="h-4 w-4" aria-hidden="true" />
                </Button>
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <Button type="button" variant="ghost" onClick={() => setPanelState("loading")}>
                {t("unmatched.loadingState")}
              </Button>
              <Button type="button" variant="ghost" onClick={() => setPanelState("empty")}>
                {t("unmatched.emptyState")}
              </Button>
              <Button type="button" variant="ghost" onClick={() => setPanelState("error")}>
                {t("unmatched.errorState")}
              </Button>
              <Button type="button" variant="ghost" onClick={() => setPanelState("ready")}>
                {t("unmatched.results")}
              </Button>
            </div>
          </section>

          <CandidatePanel
            state={panelState}
            results={visibleResults}
            selectedServiceId={selectedServiceId}
            onSelect={setSelectedServiceId}
          />

          <section>
            <label className="text-xs font-medium uppercase text-muted-foreground" htmlFor="match-notes">
              {t("unmatched.operatorNotes")}
            </label>
            <textarea
              id="match-notes"
              className="mt-2 min-h-24 w-full rounded-md border border-input bg-background/65 px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              placeholder={t("unmatched.notesPlaceholder")}
            />
          </section>

          <div className="grid gap-2 sm:grid-cols-2">
            <Button type="button" disabled={!selectedServiceId || panelState !== "ready"}>
              <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
              {t("unmatched.manualButton")}
            </Button>
            <Button type="button" variant="secondary">
              <XCircle className="h-4 w-4" aria-hidden="true" />
              {t("unmatched.notService")}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function CandidatePanel({
  state,
  results,
  selectedServiceId,
  onSelect,
}: {
  state: PanelState;
  results: DirectoryServiceResult[];
  selectedServiceId: string;
  onSelect: (id: string) => void;
}) {
  const { t } = useI18n();
  if (state === "loading") {
    return (
      <div className="space-y-3">
        <CardSkeleton rows={3} />
        <ProcessingInProgress title={t("unmatched.searching")} description={t("unmatched.searchingDesc")} />
      </div>
    );
  }

  if (state === "error") {
    return <RetryError description={t("unmatched.searchUnavailable")} />;
  }

  if (results.length === 0) {
    return <NoResults title={t("unmatched.noMatches.title")} description={t("unmatched.noMatches.description")} className="min-h-40" />;
  }

  return (
    <section className="space-y-2">
      <div className="flex items-center justify-between">
        <h3>{t("unmatched.candidateServices")}</h3>
        <Badge variant="info">{results.length} {t("unmatched.results")}</Badge>
      </div>
      {results.map((service) => (
        <button
          key={service.id}
          type="button"
          className={cn(
            "w-full rounded-md border border-border bg-background/45 p-3 text-left transition-colors hover:bg-secondary/45 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
            selectedServiceId === service.id && "border-primary/45 bg-primary/10",
          )}
          onClick={() => onSelect(service.id)}
        >
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="truncate text-sm font-medium text-foreground">{service.name}</div>
              <div className="mt-1 text-xs text-muted-foreground">
                {service.code} - {service.specialty}
              </div>
            </div>
            <Badge variant={confidenceTone(service.confidence)}>{service.confidence}%</Badge>
          </div>
        </button>
      ))}
    </section>
  );
}

function seedQuery(item: UnmatchedItem) {
  return item.sourceCode ?? item.normalizedQuery.split(" ").slice(0, 2).join(" ");
}

function statusTone(status: UnmatchedStatus) {
  if (status === "new") return "warning";
  if (status === "reviewing") return "info";
  return "neutral";
}

function statusLabel(status: UnmatchedStatus, t: ReturnType<typeof useI18n>["t"]) {
  const labels: Record<UnmatchedStatus, TranslationKey> = {
    new: "common.new",
    reviewing: "common.reviewing",
    deferred: "common.deferred",
  };
  return t(labels[status]);
}

function confidenceTone(confidence: number) {
  if (confidence >= 80) return "success";
  if (confidence >= 65) return "warning";
  return "info";
}
