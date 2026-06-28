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
import { getServicePartners, type PartnerSummary } from "@/lib/api";

export function ServiceDetailPage({ serviceId }: { serviceId?: string }) {
  const { t } = useI18n();
  const [partners, setPartners] = useState<PartnerSummary[]>([]);
  const [loading, setLoading] = useState(Boolean(serviceId));
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!serviceId) return;
    setLoading(true);
    setError(null);
    getServicePartners(serviceId)
      .then((response) => setPartners(response.items))
      .catch((fetchError: unknown) => setError(fetchError instanceof Error ? fetchError.message : "Service partners request failed"))
      .finally(() => setLoading(false));
  }, [serviceId]);

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
              <Link href="/dashboard">{t("detail.adminDashboard")}</Link>
            </Button>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:py-10">
        <Card>
          <CardHeader>
            <div>
              <CardTitle>{t("service.partnerComparison")}</CardTitle>
              <CardDescription>{t("service.liveNotConnected")}</CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? <ProcessingInProgress /> : null}
            {error ? <RetryError description={error} /> : null}
            {!serviceId ? <NoDataYet title={t("service.noData.title")} description={t("service.noData.description")} /> : null}
            {serviceId && partners.length === 0 && !loading ? <NoDataYet title={t("service.noData.title")} description={t("service.noData.description")} /> : null}
            {partners.length > 0 ? (
              <div className="table-shell">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t("common.partner")}</TableHead>
                      <TableHead>{t("common.services")}</TableHead>
                      <TableHead>{t("common.priceRange")}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {partners.map((partner) => (
                      <TableRow key={partner.id}>
                        <TableCell><Link className="font-medium text-primary" href={`/partners/${partner.id}`}>{partner.name}</Link></TableCell>
                        <TableCell>{partner.service_count}</TableCell>
                        <TableCell>{partner.active_price_count}</TableCell>
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
