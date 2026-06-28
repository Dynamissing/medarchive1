"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";

import { CopyLinkButton } from "@/components/copy-link-button";
import { LanguageSwitcher } from "@/components/language-switcher";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { NoDataYet, ProcessingInProgress, RetryError } from "@/components/ui/states";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useI18n } from "@/i18n";
import { getPartnerServices, type PartnerServiceSummary } from "@/lib/api";

export function PartnerDetailPage({ partnerId }: { partnerId?: string }) {
  const { t } = useI18n();
  const [services, setServices] = useState<PartnerServiceSummary[]>([]);
  const [loading, setLoading] = useState(Boolean(partnerId));
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!partnerId) return;
    setLoading(true);
    setError(null);
    getPartnerServices(partnerId)
      .then((response) => setServices(response.items))
      .catch((fetchError: unknown) => setError(fetchError instanceof Error ? fetchError.message : "Partner services request failed"))
      .finally(() => setLoading(false));
  }, [partnerId]);

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
              <Link href="/dashboard">{t("detail.adminDashboard")}</Link>
            </Button>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:py-10">
        <Card>
          <CardHeader>
            <div>
              <CardTitle>{t("partner.fullPriceList")}</CardTitle>
              <CardDescription>{t("partner.liveNotConnected")}</CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? <ProcessingInProgress /> : null}
            {error ? <RetryError description={error} /> : null}
            {!partnerId ? <NoDataYet title={t("partner.noData.title")} description={t("partner.noData.description")} /> : null}
            {partnerId && services.length === 0 && !loading ? <NoDataYet title={t("partner.noData.title")} description={t("partner.noData.description")} /> : null}
            {services.length > 0 ? (
              <div className="table-shell">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t("common.service")}</TableHead>
                      <TableHead>{t("common.priceRange")}</TableHead>
                      <TableHead>{t("common.date")}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {services.map((item) => (
                      <TableRow key={`${item.service.id}-${item.effective_date ?? ""}-${item.latest_amount ?? ""}`}>
                        <TableCell><Link className="font-medium text-primary" href={`/services/${item.service.id}`}>{item.service.name}</Link></TableCell>
                        <TableCell>{formatPrice(item.latest_amount, item.currency)}</TableCell>
                        <TableCell>{item.effective_date ?? "-"}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            ) : null}
          </CardContent>
        </Card>
      </section>
    </main>
  );
}

function formatPrice(amount: string | number | null, currency: string | null) {
  if (amount === null || amount === undefined || amount === "") return "-";
  return `${amount} ${currency ?? "KZT"}`;
}
