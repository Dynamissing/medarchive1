import type { Metadata } from "next";

import { defaultLocale, htmlLangForLocale, supportedLocales, type RouteLocale } from "@/i18n/locales";
import enMessages from "@/messages/en.json";
import kzMessages from "@/messages/kz.json";
import ruMessages from "@/messages/ru.json";

export type SeoLocale = RouteLocale;

export const supportedSeoLocales = supportedLocales;

const messages: Record<RouteLocale, unknown> = {
  ru: ruMessages,
  kz: kzMessages,
  en: enMessages,
};

export const siteConfig = {
  name: "MedPrice",
  url: process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000",
  ogImage: "/og/medprice.svg",
};

export function createSeoMetadata({
  title,
  description,
  path = "/",
  locale = defaultLocale,
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
  const localizedTitle = title ?? msg(locale, "seo.siteTitle");
  const localizedDescription = description ?? msg(locale, "seo.siteDescription");
  const canonical = absoluteUrl(path);
  return {
    title: localizedTitle,
    description: localizedDescription,
    metadataBase: new URL(siteConfig.url),
    alternates: {
      canonical,
      languages: localeAlternates(path),
    },
    openGraph: {
      title: localizedTitle,
      description: localizedDescription,
      url: canonical,
      siteName: siteConfig.name,
      type,
      locale: openGraphLocale(locale),
      alternateLocale: supportedSeoLocales.filter((item) => item !== locale).map(openGraphLocale),
      images: [{ url: siteConfig.ogImage, width: 1200, height: 630, alt: siteConfig.name }],
    },
    twitter: {
      card: "summary_large_image",
      title: localizedTitle,
      description: localizedDescription,
      images: [siteConfig.ogImage],
    },
    robots,
  };
}

export function createHomeSeo(locale: SeoLocale = defaultLocale, path = "/") {
  return {
    title: msg(locale, "seo.home.title"),
    description: msg(locale, "seo.home.description"),
    canonical: absoluteUrl(path),
  };
}

export function createSearchSeo({
  query,
  city,
  locale = defaultLocale,
  path = `/${locale}/search`,
}: {
  query?: string | null;
  city?: string | null;
  locale?: SeoLocale;
  path?: string;
}) {
  const safeQuery = sanitizeSeoText(query);
  const cityLabel = cityDisplayName(city, locale);
  const titleTemplate = safeQuery ? msg(locale, "seo.search.titleWithQuery") : msg(locale, "seo.search.title");
  const descriptionTemplate = safeQuery ? msg(locale, "seo.search.descriptionWithQuery") : msg(locale, "seo.search.description");
  return {
    title: formatTemplate(titleTemplate, { query: capitalizeFirst(safeQuery), city: cityLabel }),
    description: formatTemplate(descriptionTemplate, { query: safeQuery, city: cityLabel }),
    canonical: absoluteUrl(path),
  };
}

export function createServiceSeo({
  service,
  city,
  locale = defaultLocale,
  path,
}: {
  service: string;
  city?: string | null;
  locale?: SeoLocale;
  path: string;
}) {
  const values = { service: sanitizeSeoText(service), city: cityDisplayName(city, locale) };
  return {
    title: formatTemplate(msg(locale, "seo.service.title"), values),
    description: formatTemplate(msg(locale, "seo.service.description"), values),
    canonical: absoluteUrl(path),
  };
}

export function createClinicSeo({
  clinic,
  locale = defaultLocale,
  path,
}: {
  clinic: string;
  locale?: SeoLocale;
  path: string;
}) {
  const values = { clinic: sanitizeSeoText(clinic) };
  return {
    title: formatTemplate(msg(locale, "seo.clinic.title"), values),
    description: formatTemplate(msg(locale, "seo.clinic.description"), values),
    canonical: absoluteUrl(path),
  };
}

export function absoluteUrl(path: string) {
  return new URL(path, siteConfig.url).toString();
}

export function sanitizeSeoText(value?: string | null) {
  return (value ?? "").replace(/[<>`"{}]/g, "").replace(/\s+/g, " ").trim().slice(0, 80);
}

export function cityDisplayName(city?: string | null, locale: SeoLocale = defaultLocale) {
  const normalized = sanitizeSeoText(city).toLowerCase();
  const key = normalized === "astana" || normalized === "almaty" ? normalized : "kazakhstan";
  return msg(locale, `cities.${key}`);
}

export function localePath(locale: SeoLocale, path: string) {
  const cleaned = path.startsWith("/") ? path : `/${path}`;
  return `/${locale}${cleaned}`;
}

export function openGraphLocale(locale: SeoLocale) {
  if (locale === "en") return "en_US";
  if (locale === "kz") return "kk_KZ";
  return "ru_KZ";
}

export function htmlLocale(locale: SeoLocale) {
  return htmlLangForLocale(locale);
}

export function seoMessage(locale: SeoLocale, key: string) {
  return msg(locale, key);
}

function localeAlternates(path: string) {
  const withoutLocale = path.replace(/^\/(ru|kz|en)(?=\/|$)/, "") || "/";
  return {
    ...Object.fromEntries(supportedSeoLocales.map((locale) => [locale, absoluteUrl(localePath(locale, withoutLocale))])),
    "x-default": absoluteUrl(localePath(defaultLocale, withoutLocale)),
  };
}

function msg(locale: SeoLocale, key: string) {
  return getNested(messages[locale], key) ?? getNested(messages.ru, key) ?? key;
}

function getNested(source: unknown, key: string) {
  const value = key.split(".").reduce<unknown>((current, part) => {
    if (current && typeof current === "object" && part in current) {
      return (current as Record<string, unknown>)[part];
    }
    return undefined;
  }, source);
  return typeof value === "string" ? value : undefined;
}

function formatTemplate(template: string, values: Record<string, string>) {
  return template.replace(/\{(\w+)\}/g, (_, key: string) => values[key] ?? "");
}

function capitalizeFirst(value: string) {
  return value ? value.charAt(0).toUpperCase() + value.slice(1) : value;
}
