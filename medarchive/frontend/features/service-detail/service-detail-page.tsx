"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { ArrowLeft, CalendarDays, Search, Stethoscope } from "lucide-react";

import { CopyLinkButton } from "@/components/copy-link-button";
import { LanguageSwitcher } from "@/components/language-switcher";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useI18n, type TranslationKey } from "@/i18n";
import { serviceDetailMock, type PartnerPrice, type PartnerPriceStatus } from "@/features/service-detail/mock-data";

type SortKey = "partner" | "resident" | "nonresident" | "effectiveDate" | "status";

const sortOptions: Array<{ value: SortKey; labelKey: TranslationKey }> = [
  { value: "partner", labelKey: "common.partner" },
  { value: "resident", labelKey: "service.resident" },
  { value: "nonresident", labelKey: "service.nonresident" },
  { value: "effectiveDate", labelKey: "service.effective" },
  { value: "status", labelKey: "common.status" },
];

export function ServiceDetailPage() {
  const { t } = useI18n();
  const [sortKey, setSortKey] = useState<SortKey>("resident");

  const partners = useMemo(() => {
    return [...serviceDetailMock.partners].sort((left, right) => comparePartnerPrice(left, right, sortKey));
  }, [sortKey]);

  const currentCount = serviceDetailMock.partners.filter((partner) => partner.status === "current").length;
  const missingCount = serviceDetailMock.partners.filter((partner) => partner.status === "missing" || partner.status === "unmatched").length;

  return (
    <main className="min-h-screen bg-background">
      <header className="border-b border-border">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <Link className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground" href="/">
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            {t("common.search")}
          </Link>
          <div className="flex items-center gap-2">
            <LanguageSwitcher />
            <CopyLinkButton variant="secondary" />
            <Button asChild variant="secondary">
              <a href="/dashboard">{t("detail.adminDashboard")}</a>
            </Button>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:py-10">
        <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_320px]">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="success">{t("categories.laboratory")}</Badge>
              <Badge variant="neutral">{serviceDetailMock.code}</Badge>
              <Badge variant="info">{serviceDetailMock.specialty}</Badge>
            </div>
            <h1 className="mt-4 text-3xl font-semibold tracking-normal text-foreground sm:text-4xl">{t("service.title")}</h1>
            <p className="mt-4 max-w-2xl text-base leading-7 text-muted-foreground">{t("service.description")}</p>
          </div>

          <Card>
            <CardContent className="grid gap-4 sm:grid-cols-3 lg:grid-cols-1">
              <Metric label={t("common.partners")} value={`${serviceDetailMock.partners.length}`} />
              <Metric label={t("public.currentPrices")} value={`${currentCount}`} />
              <Metric label={t("common.missing")} value={`${missingCount}`} />
            </CardContent>
          </Card>
        </div>

        <section className="mt-6 grid gap-5 lg:grid-cols-[minmax(0,1fr)_320px]">
          <Card>
            <CardHeader>
              <div>
                <CardTitle>{t("service.partnerComparison")}</CardTitle>
                <CardDescription>{t("service.partnerComparisonDesc")}</CardDescription>
              </div>
              <label className="flex min-w-44 flex-col gap-2">
                <span className="text-xs font-medium uppercase text-muted-foreground">{t("service.sortBy")}</span>
                <select
                  className="h-9 rounded-md border border-input bg-background/65 px-3 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  value={sortKey}
                  onChange={(event) => setSortKey(event.target.value as SortKey)}
                >
                  {sortOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {t(option.labelKey)}
                    </option>
                  ))}
                </select>
              </label>
            </CardHeader>
            <CardContent className="p-0">
              <div className="hidden table-shell rounded-none border-x-0 border-b-0 md:block">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t("common.partner")}</TableHead>
                      <TableHead className="text-right">{t("service.resident")}</TableHead>
                      <TableHead className="text-right">{t("service.nonresident")}</TableHead>
                      <TableHead>{t("service.effective")}</TableHead>
                      <TableHead>{t("common.status")}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {partners.map((partner) => (
                      <TableRow key={partner.id}>
                        <TableCell className="font-medium text-foreground">{partner.partner}</TableCell>
                        <TableCell className="text-right tabular-nums">{formatPrice(partner.residentPrice, partner.currency)}</TableCell>
                        <TableCell className="text-right tabular-nums">{formatPrice(partner.nonresidentPrice, partner.currency)}</TableCell>
                        <TableCell>
                          <EffectiveDateBadge date={partner.effectiveDate} status={partner.status} />
                        </TableCell>
                        <TableCell>
                          <Badge variant={statusTone(partner.status)}>{statusLabel(partner.status, t)}</Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              <div className="space-y-3 p-4 md:hidden">
                {partners.map((partner) => (
                  <PartnerCard key={partner.id} partner={partner} />
                ))}
              </div>
            </CardContent>
          </Card>

          <aside className="space-y-5">
            <Card>
              <CardHeader>
                <div>
                  <CardTitle>{t("service.dataPlaceholders")}</CardTitle>
                  <CardDescription>{t("service.placeholdersDesc")}</CardDescription>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {serviceDetailMock.partners
                  .filter((partner) => partner.status === "missing" || partner.status === "unmatched")
                  .map((partner) => (
                    <div key={partner.id} className="rounded-md border border-border bg-background/45 p-3">
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-sm font-medium text-foreground">{partner.partner}</span>
                        <Badge variant={statusTone(partner.status)}>{statusLabel(partner.status, t)}</Badge>
                      </div>
                      <p className="mt-2 text-xs leading-5">{partner.note}</p>
                    </div>
                  ))}
              </CardContent>
            </Card>

            <Card>
              <CardContent>
                <div className="flex items-start gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-secondary text-muted-foreground">
                    <Search className="h-4 w-4" aria-hidden="true" />
                  </div>
                  <div>
                    <h3>{t("service.adapterReady")}</h3>
                    <p className="mt-2 text-xs leading-5">{t("service.adapterText")}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </aside>
        </section>
      </section>
    </main>
  );
}

function PartnerCard({ partner }: { partner: PartnerPrice }) {
  const { t } = useI18n();
  return (
    <article className="rounded-md border border-border bg-background/45 p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3>{partner.partner}</h3>
          <div className="mt-2 flex flex-wrap gap-2">
            <EffectiveDateBadge date={partner.effectiveDate} status={partner.status} />
            <Badge variant={statusTone(partner.status)}>{statusLabel(partner.status, t)}</Badge>
          </div>
        </div>
        <Stethoscope className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3">
        <Detail label={t("service.resident")} value={formatPrice(partner.residentPrice, partner.currency, t)} />
        <Detail label={t("service.nonresident")} value={formatPrice(partner.nonresidentPrice, partner.currency, t)} />
      </div>
    </article>
  );
}

function EffectiveDateBadge({ date, status }: { date: string | null; status: PartnerPriceStatus }) {
  const { t } = useI18n();
  if (!date) {
    return <Badge variant="warning">{t("common.noDate")}</Badge>;
  }
  return (
    <Badge variant={status === "outdated" ? "warning" : "info"} className="gap-1">
      <CalendarDays className="h-3.5 w-3.5" aria-hidden="true" />
      {date}
    </Badge>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-card p-3">
      <div className="text-xs uppercase text-muted-foreground">{label}</div>
      <div className="mt-1 text-sm font-medium text-foreground">{value}</div>
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

function formatPrice(value: number | null, currency: string, t?: ReturnType<typeof useI18n>["t"]) {
  if (value === null) {
    return t ? t("common.missing") : "Missing";
  }
  return `${value.toLocaleString("en-US")} ${currency}`;
}

function statusTone(status: PartnerPriceStatus) {
  if (status === "current") return "success";
  if (status === "outdated") return "warning";
  if (status === "missing") return "info";
  return "error";
}

function statusLabel(status: PartnerPriceStatus, t: ReturnType<typeof useI18n>["t"]) {
  const labels: Record<PartnerPriceStatus, TranslationKey> = {
    current: "common.current",
    outdated: "common.outdated",
    missing: "common.missing",
    unmatched: "common.unmatched",
  };
  return t(labels[status]);
}

function comparePartnerPrice(left: PartnerPrice, right: PartnerPrice, sortKey: SortKey) {
  if (sortKey === "partner") return left.partner.localeCompare(right.partner);
  if (sortKey === "resident") return numberOrInfinity(left.residentPrice) - numberOrInfinity(right.residentPrice);
  if (sortKey === "nonresident") return numberOrInfinity(left.nonresidentPrice) - numberOrInfinity(right.nonresidentPrice);
  if (sortKey === "effectiveDate") return (right.effectiveDate ?? "").localeCompare(left.effectiveDate ?? "");
  return left.status.localeCompare(right.status);
}

function numberOrInfinity(value: number | null) {
  return value ?? Number.POSITIVE_INFINITY;
}
