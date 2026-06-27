import type { MetadataRoute } from "next";

import { absoluteUrl, supportedSeoLocales } from "@/lib/seo";

export const dynamic = "force-static";

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  const localized = supportedSeoLocales.flatMap((locale) => [
    `/${locale}/search`,
    `/${locale}/services/complete-blood-count`,
    `/${locale}/clinics/clinic-07`,
  ]);
  return ["/", "/services/complete-blood-count", "/partners/clinic-07", ...localized].map((path) => ({
    url: absoluteUrl(path),
    lastModified: now,
    changeFrequency: "weekly",
    priority: path === "/" ? 1 : 0.8,
  }));
}
