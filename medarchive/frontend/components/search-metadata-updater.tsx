"use client";

import { useEffect } from "react";
import { usePathname, useSearchParams } from "next/navigation";

import { absoluteUrl, createSearchSeo, htmlLocale, openGraphLocale, siteConfig, type SeoLocale } from "@/lib/seo";

export function SearchMetadataUpdater({ locale = "ru" }: { locale?: SeoLocale }) {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  useEffect(() => {
    const q = searchParams.get("q");
    const city = searchParams.get("city");
    const canonicalPath = `${pathname}${searchParams.toString() ? `?${searchParams.toString()}` : ""}`;
    const seo = createSearchSeo({ query: q, city, locale, path: canonicalPath });
    document.title = seo.title;
    setMeta("description", seo.description);
    setLink("canonical", seo.canonical);
    setProperty("og:title", seo.title);
    setProperty("og:description", seo.description);
    setProperty("og:url", seo.canonical);
    setProperty("og:locale", openGraphLocale(locale));
    setProperty("og:image", absoluteUrl(siteConfig.ogImage));
    setMeta("twitter:card", "summary_large_image");
    setMeta("twitter:title", seo.title);
    setMeta("twitter:description", seo.description);
    setMeta("twitter:image", absoluteUrl(siteConfig.ogImage));
    document.documentElement.lang = htmlLocale(locale);
  }, [locale, pathname, searchParams]);

  return null;
}

function setMeta(name: string, content: string) {
  const selector = `meta[name="${name}"]`;
  let node = document.head.querySelector<HTMLMetaElement>(selector);
  if (!node) {
    node = document.createElement("meta");
    node.name = name;
    document.head.appendChild(node);
  }
  node.content = content;
}

function setProperty(property: string, content: string) {
  const selector = `meta[property="${property}"]`;
  let node = document.head.querySelector<HTMLMetaElement>(selector);
  if (!node) {
    node = document.createElement("meta");
    node.setAttribute("property", property);
    document.head.appendChild(node);
  }
  node.content = content;
}

function setLink(rel: string, href: string) {
  const selector = `link[rel="${rel}"]`;
  let node = document.head.querySelector<HTMLLinkElement>(selector);
  if (!node) {
    node = document.createElement("link");
    node.rel = rel;
    document.head.appendChild(node);
  }
  node.href = href;
}
