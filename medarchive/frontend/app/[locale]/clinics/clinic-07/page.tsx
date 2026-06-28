import type { Metadata } from "next";

import { LocaleBoundary } from "@/components/locale-boundary";
import { PartnerDetailPage } from "@/features/partner-detail/partner-detail-page";
import { createSeoMetadata, type SeoLocale } from "@/lib/seo";

const locales: SeoLocale[] = ["ru", "kz", "en"];

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

export async function generateMetadata({ params }: { params: Promise<{ locale: SeoLocale }> }): Promise<Metadata> {
  const { locale: routeLocale } = await params;
  const locale = locales.includes(routeLocale) ? routeLocale : "ru";
  const path = `/${locale}/clinics/clinic-07`;
  return createSeoMetadata({
    path,
    locale,
    type: "article",
  });
}

export default async function LocaleClinic07Page({ params }: { params: Promise<{ locale: SeoLocale }> }) {
  const { locale: routeLocale } = await params;
  const locale = locales.includes(routeLocale) ? routeLocale : "ru";
  return (
    <LocaleBoundary locale={locale}>
      <PartnerDetailPage />
    </LocaleBoundary>
  );
}
