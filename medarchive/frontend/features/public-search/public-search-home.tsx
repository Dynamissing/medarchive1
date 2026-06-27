"use client";

import { useMemo, useState } from "react";
import { ArrowRight, Building2, Search, Stethoscope } from "lucide-react";

import { LanguageSwitcher } from "@/components/language-switcher";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { NoResults } from "@/components/ui/states";
import { useI18n } from "@/i18n";
import { cn } from "@/lib/utils";
import { publicSearchResultsMock, quickExamples, topCategories, type PublicSearchResult } from "@/features/public-search/mock-data";

export function PublicSearchHome() {
  const { t } = useI18n();
  const [query, setQuery] = useState("blood");
  const [category, setCategory] = useState<string>("All");

  const results = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return publicSearchResultsMock.filter((result) => {
      const queryMatch =
        !normalized ||
        [result.title, result.subtitle, result.category].some((value) => value.toLowerCase().includes(normalized));
      const categoryMatch = category === "All" || result.category === category;
      return queryMatch && categoryMatch;
    });
  }, [query, category]);

  return (
    <main className="min-h-screen bg-background">
      <header className="border-b border-border">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <Stethoscope className="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <div className="text-sm font-semibold text-foreground">MedArchive</div>
              <div className="text-xs text-muted-foreground">{t("app.partnerSearch")}</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <LanguageSwitcher />
            <Button asChild variant="secondary">
              <a href="/login">{t("app.admin")}</a>
            </Button>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:py-14">
        <div className="max-w-3xl">
          <Badge variant="info">{t("app.publicSearch")}</Badge>
          <h1 className="mt-4 text-3xl font-semibold tracking-normal text-foreground sm:text-5xl">{t("public.heroTitle")}</h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-muted-foreground">
            {t("public.heroText")}
          </p>
        </div>

        <div className="mt-8 rounded-lg border border-border bg-card p-3 shadow-surface">
          <div className="flex flex-col gap-3 md:flex-row">
            <div className="relative flex-1">
              <Search className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
              <Input
                className="h-14 rounded-md pl-12 text-base"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder={t("public.placeholder")}
              />
            </div>
            <Button className="h-14 px-5 text-base">
              {t("common.search")}
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Button>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          <span className="mr-1 self-center text-xs font-medium uppercase text-muted-foreground">{t("public.examples")}</span>
          {quickExamples.map((example) => (
            <button
              key={example}
              type="button"
              className="rounded-md border border-border bg-secondary px-2.5 py-1 text-xs text-secondary-foreground transition-colors hover:bg-secondary/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              onClick={() => setQuery(example)}
            >
              {example}
            </button>
          ))}
        </div>

        <div className="mt-8 flex flex-wrap gap-2">
          {["All", ...topCategories].map((item) => (
            <button
              key={item}
              type="button"
              className={cn(
                "rounded-md border px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                category === item
                  ? "border-primary/45 bg-primary/15 text-primary"
                  : "border-border bg-card text-muted-foreground hover:bg-secondary hover:text-foreground",
              )}
              onClick={() => setCategory(item)}
            >
              {categoryLabel(item, t)}
            </button>
          ))}
        </div>

        <section className="mt-8 grid gap-4 lg:grid-cols-[minmax(0,1fr)_300px]">
          <div className="space-y-3">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <h2>{t("public.resultPreview")}</h2>
              <Badge variant="neutral">{results.length} {t("public.matches")}</Badge>
            </div>
            {results.length > 0 ? (
              results.map((result) => <ResultCard key={result.id} result={result} />)
            ) : (
              <NoResults title={t("public.noResults.title")} description={t("public.noResults.description")} className="min-h-48 bg-card" />
            )}
          </div>

          <aside className="rounded-lg border border-border bg-card p-5 shadow-surface">
            <h2>{t("public.catalogSnapshot")}</h2>
            <div className="mt-5 space-y-4">
              <Metric label={t("public.reviewedServices")} value="4,812" />
              <Metric label={t("public.activePartners")} value="38" />
              <Metric label={t("public.currentPrices")} value="6,842" />
            </div>
          </aside>
        </section>
      </section>
    </main>
  );
}

function ResultCard({ result }: { result: PublicSearchResult }) {
  const { t } = useI18n();
  return (
    <article className="rounded-lg border border-border bg-card p-4 shadow-surface">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            {result.type === "partner" ? (
              <Building2 className="h-4 w-4 text-info" aria-hidden="true" />
            ) : (
              <Stethoscope className="h-4 w-4 text-primary" aria-hidden="true" />
            )}
            <h3 className="truncate text-base">{result.title}</h3>
          </div>
          <p className="mt-2">{result.subtitle}</p>
        </div>
        <Badge variant={result.type === "partner" ? "info" : "success"}>{result.type}</Badge>
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <Detail label={t("common.category")} value={categoryLabel(result.category, t)} />
        <Detail label={t("common.priceRange")} value={result.priceRange} />
        <Detail label={t("common.partners")} value={`${result.partnerCount}`} />
      </div>
      {result.id === "svc-001" || result.id === "partner-07" ? (
        <div className="mt-4">
          <Button asChild variant="secondary">
            <a href={result.id === "svc-001" ? "/services/complete-blood-count" : "/partners/clinic-07"}>{t("public.openDetail")}</a>
          </Button>
        </div>
      ) : null}
    </article>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-background/45 p-3">
      <div className="text-xs uppercase text-muted-foreground">{label}</div>
      <div className="mt-1 truncate text-sm font-medium text-foreground">{value}</div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-2xl font-semibold text-foreground">{value}</div>
      <div className="mt-1 text-sm text-muted-foreground">{label}</div>
    </div>
  );
}

function categoryLabel(category: string, t: ReturnType<typeof useI18n>["t"]) {
  const labels: Record<string, Parameters<typeof t>[0]> = {
    All: "categories.all",
    Diagnostics: "categories.diagnostics",
    Radiology: "categories.radiology",
    Consultation: "categories.consultation",
    Laboratory: "categories.laboratory",
    "Home care": "categories.homeCare",
  };
  return labels[category] ? t(labels[category]) : category;
}
