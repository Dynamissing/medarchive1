import type { Metadata } from "next";

import { ServiceDetailPage } from "@/features/service-detail/service-detail-page";
import { createSeoMetadata, type SeoLocale } from "@/lib/seo";

const locales: SeoLocale[] = ["ru", "kz", "en"];

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

export async function generateMetadata({ params }: { params: Promise<{ locale: SeoLocale }> }): Promise<Metadata> {
  const { locale: routeLocale } = await params;
  const locale = locales.includes(routeLocale) ? routeLocale : "ru";
  return createSeoMetadata({
    title: "Общий анализ крови - цены партнёров | MedPrice",
    description: "Сравнение актуальных цен партнёров на услугу Общий анализ крови.",
    path: `/${locale}/services/complete-blood-count`,
    locale,
    type: "article",
  });
}

export default function LocaleCompleteBloodCountPage() {
  return <ServiceDetailPage />;
}
