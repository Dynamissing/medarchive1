import type { Metadata } from "next";

import { LocaleBoundary } from "@/components/locale-boundary";
import { ServiceDetailPage } from "@/features/service-detail/service-detail-page";
import { createSeoMetadata, type SeoLocale } from "@/lib/seo";

const locales: SeoLocale[] = ["ru", "kz", "en"];

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

export async function generateMetadata({ params }: { params: Promise<{ locale: SeoLocale }> }): Promise<Metadata> {
  const { locale: routeLocale } = await params;
  const locale = locales.includes(routeLocale) ? routeLocale : "ru";
  const path = `/${locale}/services/complete-blood-count`;
  return createSeoMetadata({
    path,
    locale,
    type: "article",
  });
}

export default async function LocaleCompleteBloodCountPage({ params }: { params: Promise<{ locale: SeoLocale }> }) {
  const { locale: routeLocale } = await params;
  const locale = locales.includes(routeLocale) ? routeLocale : "ru";
  return (
    <LocaleBoundary locale={locale}>
      <ServiceDetailPage />
    </LocaleBoundary>
  );
}
