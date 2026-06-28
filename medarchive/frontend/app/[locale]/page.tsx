import type { Metadata } from "next";
import { Suspense } from "react";

import { LocaleBoundary } from "@/components/locale-boundary";
import { PublicSearchHome } from "@/features/public-search/public-search-home";
import { createHomeSeo, createSeoMetadata, type SeoLocale } from "@/lib/seo";

const locales: SeoLocale[] = ["ru", "kz", "en"];

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

export async function generateMetadata({ params }: { params: Promise<{ locale: SeoLocale }> }): Promise<Metadata> {
  const { locale: routeLocale } = await params;
  const locale = locales.includes(routeLocale) ? routeLocale : "ru";
  const seo = createHomeSeo(locale, `/${locale}`);
  return createSeoMetadata({
    title: seo.title,
    description: seo.description,
    path: `/${locale}`,
    locale,
  });
}

export default async function LocaleHomePage({ params }: { params: Promise<{ locale: SeoLocale }> }) {
  const { locale: routeLocale } = await params;
  const locale = locales.includes(routeLocale) ? routeLocale : "ru";
  return (
    <LocaleBoundary locale={locale}>
      <Suspense>
        <PublicSearchHome locale={locale} />
      </Suspense>
    </LocaleBoundary>
  );
}
