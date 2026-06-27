import type { Metadata } from "next";

import { ServiceDetailPage } from "@/features/service-detail/service-detail-page";
import { createSeoMetadata } from "@/lib/seo";

export const metadata: Metadata = createSeoMetadata({
  title: "Общий анализ крови - цены партнёров | MedPrice",
  description: "Сравнение актуальных цен партнёров на услугу Общий анализ крови.",
  path: "/services/complete-blood-count",
  type: "article",
});

export default function CompleteBloodCountPage() {
  return <ServiceDetailPage />;
}
