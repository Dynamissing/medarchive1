import type { Metadata } from "next";

import { PartnerDetailPage } from "@/features/partner-detail/partner-detail-page";
import { createSeoMetadata, type SeoLocale } from "@/lib/seo";

const locales: SeoLocale[] = ["ru", "kz", "en"];

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

export async function generateMetadata({ params }: { params: Promise<{ locale: SeoLocale }> }): Promise<Metadata> {
  const { locale: routeLocale } = await params;
  const locale = locales.includes(routeLocale) ? routeLocale : "ru";
  return createSeoMetadata({
    title: "Clinic 07 - прайс-лист партнёра | MedPrice",
    description: "Актуальные услуги, цены и история документов партнёра Clinic 07.",
    path: `/${locale}/clinics/clinic-07`,
    locale,
    type: "article",
  });
}

export default function LocaleClinic07Page() {
  return <PartnerDetailPage />;
}
