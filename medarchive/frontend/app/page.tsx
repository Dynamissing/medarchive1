import type { Metadata } from "next";
import { Suspense } from "react";

import { PublicSearchHome } from "@/features/public-search/public-search-home";
import { createSeoMetadata } from "@/lib/seo";

export const metadata: Metadata = createSeoMetadata({
  title: "MedPrice - сравнение цен на медицинские услуги в Казахстане",
  description: "Поиск медицинских услуг, партнёров и актуальных цен в каталоге MedPrice.",
  path: "/",
});

export default function Home() {
  return (
    <Suspense>
      <PublicSearchHome />
    </Suspense>
  );
}
