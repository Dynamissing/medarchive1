import type { Metadata } from "next";
import { Suspense } from "react";

import { PublicSearchHome } from "@/features/public-search/public-search-home";
import { createHomeSeo, createSeoMetadata } from "@/lib/seo";

const seo = createHomeSeo("ru", "/");

export const metadata: Metadata = createSeoMetadata({ title: seo.title, description: seo.description, path: "/" });

export default function Home() {
  return (
    <Suspense>
      <PublicSearchHome />
    </Suspense>
  );
}
