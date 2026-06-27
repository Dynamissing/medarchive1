"use client";

import Link from "next/link";
import { ArrowLeft, CalendarDays, Mail, MapPin, Phone } from "lucide-react";

import { CopyLinkButton } from "@/components/copy-link-button";
import { LanguageSwitcher } from "@/components/language-switcher";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { NoDataYet } from "@/components/ui/states";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useI18n, type TranslationKey } from "@/i18n";
import { partnerDetailMock, type PartnerDocumentHistory, type PartnerPriceRow } from "@/features/partner-detail/mock-data";

export function PartnerDetailPage() {
  const { t } = useI18n();
  return (
    <main className="min-h-screen bg-background">
      <header className="border-b border-border">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <Link className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground" href="/">
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            {t("detail.backSearch")}
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
        <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_340px]">
          <div>
            <Badge variant="info">{partnerDetailMock.region}</Badge>
            <h1 className="mt-4 text-3xl font-semibold tracking-normal text-foreground sm:text-4xl">{partnerDetailMock.name}</h1>
            <p className="mt-4 max-w-2xl text-base leading-7 text-muted-foreground">
              {t("partner.headerText")}
            </p>
          </div>
          <Card>
            <CardContent className="space-y-4">
              <ContactLine icon={Phone} label={t("partner.phone")} value={partnerDetailMock.contact.phone} />
              <ContactLine icon={Mail} label={t("partner.email")} value={partnerDetailMock.contact.email} />
              <ContactLine icon={MapPin} label={t("partner.address")} value={partnerDetailMock.contact.address} />
              <div className="rounded-md border border-border bg-background/45 p-3">
                <div className="flex items-center gap-2 text-sm font-medium text-foreground">
                  <CalendarDays className="h-4 w-4 text-info" aria-hidden="true" />
                  {t("partner.latestDocument")}
                </div>
                <div className="mt-2 text-sm text-muted-foreground">{partnerDetailMock.latestDocumentDate}</div>
              </div>
            </CardContent>
          </Card>
        </div>

        <section className="mt-6 grid gap-5 lg:grid-cols-[minmax(0,1fr)_340px]">
          <Card>
            <CardHeader>
              <div>
                <CardTitle>{t("partner.fullPriceList")}</CardTitle>
                <CardDescription>{t("partner.priceListDesc")}</CardDescription>
              </div>
              <Badge variant="neutral">{partnerDetailMock.prices.length} {t("common.services")}</Badge>
            </CardHeader>
            <CardContent className="p-0">
              <div className="table-shell rounded-none border-x-0 border-b-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t("common.service")}</TableHead>
                      <TableHead>{t("common.category")}</TableHead>
                      <TableHead className="text-right">{t("service.resident")}</TableHead>
                      <TableHead className="text-right">{t("service.nonresident")}</TableHead>
                      <TableHead>{t("service.effective")}</TableHead>
                      <TableHead>{t("common.status")}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {partnerDetailMock.prices.map((row) => (
                      <PriceRow key={row.id} row={row} />
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div>
                <CardTitle>{t("partner.priorDocuments")}</CardTitle>
                <CardDescription>{t("partner.historyDesc")}</CardDescription>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {partnerDetailMock.history.length > 0 ? (
                partnerDetailMock.history.map((document) => <HistoryItem key={document.id} document={document} />)
              ) : (
                <NoDataYet title={t("partner.noHistory.title")} description={t("partner.noHistory.description")} />
              )}
            </CardContent>
          </Card>
        </section>
      </section>
    </main>
  );
}

function ContactLine({ icon: Icon, label, value }: { icon: typeof Phone; label: string; value: string | null }) {
  const { t } = useI18n();
  return (
    <div className="rounded-md border border-border bg-background/45 p-3">
      <div className="flex items-center gap-2 text-sm font-medium text-foreground">
        <Icon className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
        {label}
      </div>
      <div className="mt-2 text-sm text-muted-foreground">{value ?? t("partner.notProvided")}</div>
    </div>
  );
}

function PriceRow({ row }: { row: PartnerPriceRow }) {
  const { t } = useI18n();
  return (
    <TableRow>
      <TableCell>
        <div className="font-medium text-foreground">{row.service}</div>
        <div className="mt-1 text-xs text-muted-foreground">{row.code}</div>
      </TableCell>
      <TableCell>{row.category}</TableCell>
      <TableCell className="text-right tabular-nums">{formatPrice(row.residentPrice, row.currency, t)}</TableCell>
      <TableCell className="text-right tabular-nums">{formatPrice(row.nonresidentPrice, row.currency, t)}</TableCell>
      <TableCell>{row.effectiveDate}</TableCell>
      <TableCell>
        <Badge variant={statusTone(row.status)}>{statusLabel(row.status, t)}</Badge>
      </TableCell>
    </TableRow>
  );
}

function HistoryItem({ document }: { document: PartnerDocumentHistory }) {
  const { t } = useI18n();
  return (
    <div className="rounded-md border border-border bg-background/45 p-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="truncate text-sm font-medium text-foreground">{document.filename}</div>
          <div className="mt-1 text-xs text-muted-foreground">
            {document.importedAt} - {document.parsedRows} {t("documents.showRows")}
          </div>
        </div>
        <Badge variant={document.status === "parsed" ? "success" : document.status === "review" ? "warning" : "error"}>{documentStatusLabel(document.status, t)}</Badge>
      </div>
    </div>
  );
}

function formatPrice(value: number | null, currency: string, t: ReturnType<typeof useI18n>["t"]) {
  return value === null ? t("common.missing") : `${value.toLocaleString("en-US")} ${currency}`;
}

function statusTone(status: PartnerPriceRow["status"]) {
  if (status === "current") return "success";
  if (status === "review") return "warning";
  return "info";
}

function statusLabel(status: PartnerPriceRow["status"], t: ReturnType<typeof useI18n>["t"]) {
  const labels: Record<PartnerPriceRow["status"], TranslationKey> = {
    current: "common.current",
    review: "common.review",
    missing: "common.missing",
  };
  return t(labels[status]);
}

function documentStatusLabel(status: PartnerDocumentHistory["status"], t: ReturnType<typeof useI18n>["t"]) {
  const labels: Record<PartnerDocumentHistory["status"], TranslationKey> = {
    parsed: "common.parsed",
    review: "common.review",
    failed: "common.failed",
  };
  return t(labels[status]);
}
