"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { ArrowRight, Search, Stethoscope } from "lucide-react";

import { CopyLinkButton } from "@/components/copy-link-button";
import { LanguageSwitcher } from "@/components/language-switcher";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { NoResults } from "@/components/ui/states";
import { useI18n } from "@/i18n";
import { searchBackend, type SearchResult } from "@/lib/api";
import type { SeoLocale } from "@/lib/seo";
import { cn } from "@/lib/utils";

const cityOptions = [
  { value: "kazakhstan", label: "Kazakhstan" },
  { value: "astana", label: "Astana" },
  { value: "almaty", label: "Almaty" },
];
const quickExamples: string[] = [];
const topCategories: string[] = [];

export function PublicSearchHome({}: { locale?: SeoLocale }) {
  const { t } = useI18n();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const defaultQuery = "";
  const [query, setQuery] = useState(searchParams.get("q") ?? defaultQuery);
  const [city, setCity] = useState(searchParams.get("city") ?? "kazakhstan");
  const [category, setCategory] = useState<string>(searchParams.get("source") ?? "All");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setQuery(searchParams.get("q") ?? defaultQuery);
    setCity(searchParams.get("city") ?? "kazakhstan");
    setCategory(searchParams.get("source") ?? "All");
  }, [defaultQuery, searchParams]);

  useEffect(() => {
    const currentQuery = query.trim();
    if (!currentQuery) {
      setResults([]);
      setError(null);
      setIsLoading(false);
      return;
    }

    const controller = new AbortController();
    setIsLoading(true);
    setError(null);
    searchBackend(currentQuery)
      .then((response) => {
        if (!controller.signal.aborted) {
          setResults(response.items);
        }
      })
      .catch((fetchError: unknown) => {
        if (!controller.signal.aborted) {
          setResults([]);
          setError(fetchError instanceof Error ? fetchError.message : "Search request failed");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      });

    return () => controller.abort();
  }, [query]);

  function updateUrl(next: { q?: string; city?: string; source?: string }) {
    const params = new URLSearchParams(searchParams.toString());
    setParam(params, "q", next.q ?? query, defaultQuery);
    setParam(params, "city", next.city ?? city, "kazakhstan");
    setParam(params, "source", next.source ?? category, "All");
    const nextUrl = params.toString() ? `${pathname}?${params.toString()}` : pathname;
    router.replace(nextUrl, { scroll: false });
  }

  function handleQueryChange(value: string) {
    setQuery(value);
    updateUrl({ q: value });
  }

  function handleCityChange(value: string) {
    setCity(value);
    updateUrl({ city: value });
  }

  function handleCategoryChange(value: string) {
    setCategory(value);
    updateUrl({ source: value });
  }

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
              <Link href="/login">{t("app.admin")}</Link>
            </Button>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:py-14">
        <div className="max-w-3xl">
          <Badge variant="info">{t("app.publicSearch")}</Badge>
          <h1 className="mt-4 text-3xl font-semibold tracking-normal text-foreground sm:text-5xl">{t("public.heroTitle")}</h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-muted-foreground">{t("public.heroText")}</p>
        </div>

        <div className="mt-8 rounded-lg border border-border bg-card p-3 shadow-surface">
          <div className="flex flex-col gap-3 md:flex-row">
            <div className="relative flex-1">
              <Search className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
              <Input
                className="h-14 rounded-md pl-12 text-base"
                value={query}
                onChange={(event) => handleQueryChange(event.target.value)}
                placeholder={t("public.placeholder")}
              />
            </div>
            <label className="sr-only" htmlFor="city-filter">
              City
            </label>
            <select
              id="city-filter"
              className="h-14 rounded-md border border-input bg-background/65 px-3 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring md:w-44"
              value={city}
              onChange={(event) => handleCityChange(event.target.value)}
            >
              {cityOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <Button className="h-14 px-5 text-base">
              {t("common.search")}
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Button>
            <CopyLinkButton variant="secondary" className="h-14" />
          </div>
        </div>

        {quickExamples.length > 0 ? (
          <div className="mt-4 flex flex-wrap gap-2">
            <span className="mr-1 self-center text-xs font-medium uppercase text-muted-foreground">{t("public.examples")}</span>
            {quickExamples.map((example) => (
              <button
                key={example}
                type="button"
                className="rounded-md border border-border bg-secondary px-2.5 py-1 text-xs text-secondary-foreground transition-colors hover:bg-secondary/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                onClick={() => handleQueryChange(example)}
              >
                {example}
              </button>
            ))}
          </div>
        ) : null}

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
              onClick={() => handleCategoryChange(item)}
            >
              {categoryLabel(item, t)}
            </button>
          ))}
        </div>

        <section className="mt-8 grid gap-4">
          <div className="space-y-3">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <h2>{t("public.resultPreview")}</h2>
              <Badge variant={error ? "error" : isLoading ? "info" : "neutral"}>
                {isLoading ? t("common.processing") : `${results.length} ${t("public.matches")}`}
              </Badge>
            </div>
            {error ? (
              <NoResults title={t("states.retry.title")} description={error} className="min-h-48 bg-card" />
            ) : results.length > 0 ? (
              results.map((result) => <ResultCard key={`${result.type}-${result.id}`} result={result} city={city} />)
            ) : (
              <NoResults title={t("public.noResults.title")} description={t("public.noResults.description")} className="min-h-48 bg-card" />
            )}
          </div>
        </section>
      </section>
    </main>
  );
}

function ResultCard({ result, city }: { result: SearchResult; city: string }) {
  const { t } = useI18n();
  const shareHref = `/search?${result.type === "service" ? "serviceId" : "clinicId"}=${encodeURIComponent(result.id)}&city=${encodeURIComponent(city)}`;

  return (
    <article className="rounded-lg border border-border bg-card p-4 shadow-surface">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h3 className="truncate text-base">{result.label}</h3>
          <p className="mt-2">{result.type === "service" ? t("common.service") : t("common.partner")}</p>
        </div>
        <Badge variant={result.type === "partner" ? "info" : "success"}>{result.type}</Badge>
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <Detail label={t("common.code")} value={stringValue(result.payload.code)} />
        <Detail label={t("common.category")} value={stringValue(result.payload.category)} />
        <Detail label={t("common.partners")} value={stringValue(result.payload.partner_count ?? result.payload.service_count ?? result.payload.active_price_count)} />
        <Detail label={t("common.priceRange")} value={priceValue(result.payload)} />
        <Detail label={t("common.date")} value={stringValue(result.payload.latest_effective_date)} />
      </div>
      <div className="mt-4">
        <CopyLinkButton href={shareHref} />
      </div>
    </article>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  const { t } = useI18n();
  return (
    <div className="rounded-md border border-border bg-background/45 p-3">
      <div className="text-xs uppercase text-muted-foreground">{label}</div>
      <div className="mt-1 truncate text-sm font-medium text-foreground">{value || t("common.notDetected")}</div>
    </div>
  );
}

function setParam(params: URLSearchParams, key: string, value: string, emptyValue: string) {
  const cleaned = value.trim();
  if (!cleaned || cleaned === emptyValue) {
    params.delete(key);
    return;
  }
  params.set(key, cleaned);
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

function stringValue(value: unknown) {
  if (typeof value === "string") return value;
  if (typeof value === "number") return String(value);
  return "";
}

function priceValue(payload: Record<string, unknown>) {
  const amount = stringValue(payload.latest_amount);
  if (!amount) return "";
  return `${amount} ${stringValue(payload.latest_currency) || "KZT"}`;
}
