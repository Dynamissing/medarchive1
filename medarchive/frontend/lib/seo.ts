import type { Metadata } from "next";

export type SeoLocale = "ru" | "kz" | "en";

export const supportedSeoLocales: SeoLocale[] = ["ru", "kz", "en"];

export const siteConfig = {
  name: "MedPrice",
  url: process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000",
  defaultTitle: "MedPrice - сравнение цен на медицинские услуги в Казахстане",
  defaultDescription:
    "Сравнивайте цены на анализы, диагностику и приемы врачей в клиниках Казахстана. Поиск по услугам, городам, клиникам и источникам данных.",
  ogImage: "/og/medprice.svg",
};

export function createSeoMetadata({
  title = siteConfig.defaultTitle,
  description = siteConfig.defaultDescription,
  path = "/",
  locale = "ru",
  type = "website",
  robots,
}: {
  title?: string;
  description?: string;
  path?: string;
  locale?: SeoLocale;
  type?: "website" | "article";
  robots?: Metadata["robots"];
} = {}): Metadata {
  const canonical = absoluteUrl(path);
  return {
    title,
    description,
    metadataBase: new URL(siteConfig.url),
    alternates: {
      canonical,
      languages: localeAlternates(path),
    },
    openGraph: {
      title,
      description,
      url: canonical,
      siteName: siteConfig.name,
      type,
      locale: openGraphLocale(locale),
      images: [{ url: siteConfig.ogImage, width: 1200, height: 630, alt: siteConfig.name }],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [siteConfig.ogImage],
    },
    robots,
  };
}

export function createSearchSeo({
  query,
  city,
  locale = "ru",
  path = `/${locale}/search`,
}: {
  query?: string | null;
  city?: string | null;
  locale?: SeoLocale;
  path?: string;
}) {
  const safeQuery = sanitizeSeoText(query);
  const cityLabel = cityDisplayName(city, locale);
  const title = safeQuery
    ? `${capitalizeFirst(safeQuery)} в ${cityLabel} - цены клиник | ${siteConfig.name}`
    : `Поиск медицинских услуг в ${cityLabel} | ${siteConfig.name}`;
  const description = safeQuery
    ? `Сравните цены на ${safeQuery} в клиниках ${cityLabel}. Источники, стоимость, клиники и актуальность данных.`
    : `Сравнивайте цены на медицинские услуги в клиниках ${cityLabel}. Поиск по услугам, городам, клиникам и источникам данных.`;
  return { title, description, canonical: absoluteUrl(path) };
}

export function absoluteUrl(path: string) {
  return new URL(path, siteConfig.url).toString();
}

export function sanitizeSeoText(value?: string | null) {
  return (value ?? "").replace(/[<>`"{}]/g, "").replace(/\s+/g, " ").trim().slice(0, 80);
}

export function cityDisplayName(city?: string | null, locale: SeoLocale = "ru") {
  const normalized = sanitizeSeoText(city).toLowerCase();
  const labels: Record<string, Record<SeoLocale, string>> = {
    astana: { ru: "Астане", kz: "Астанада", en: "Astana" },
    almaty: { ru: "Алматы", kz: "Алматыда", en: "Almaty" },
  };
  return labels[normalized]?.[locale] ?? (locale === "en" ? "Kazakhstan" : "Казахстане");
}

export function localePath(locale: SeoLocale, path: string) {
  const cleaned = path.startsWith("/") ? path : `/${path}`;
  return `/${locale}${cleaned}`;
}

function localeAlternates(path: string) {
  const withoutLocale = path.replace(/^\/(ru|kz|en)(?=\/|$)/, "") || "/";
  return Object.fromEntries(supportedSeoLocales.map((locale) => [locale, absoluteUrl(localePath(locale, withoutLocale))]));
}

function openGraphLocale(locale: SeoLocale) {
  if (locale === "en") return "en_US";
  if (locale === "kz") return "kk_KZ";
  return "ru_KZ";
}

function capitalizeFirst(value: string) {
  return value ? value.charAt(0).toUpperCase() + value.slice(1) : value;
}
