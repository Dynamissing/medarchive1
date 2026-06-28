import type { MetadataRoute } from "next";

import { siteConfig } from "@/lib/seo";

export const dynamic = "force-static";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: ["/", "/ru", "/kz", "/en", "/ru/search", "/kz/search", "/en/search", "/services/", "/partners/", "/ru/services/", "/kz/services/", "/en/services/", "/ru/clinics/", "/kz/clinics/", "/en/clinics/"],
        disallow: ["/dashboard", "/imports", "/documents", "/verification", "/unmatched", "/quality", "/login"],
      },
    ],
    sitemap: `${siteConfig.url}/sitemap.xml`,
    host: siteConfig.url,
  };
}
