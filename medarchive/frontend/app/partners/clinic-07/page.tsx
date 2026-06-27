import type { Metadata } from "next";

import { PartnerDetailPage } from "@/features/partner-detail/partner-detail-page";
import { createSeoMetadata } from "@/lib/seo";

export const metadata: Metadata = createSeoMetadata({
  title: "Clinic 07 - прайс-лист партнёра | MedPrice",
  description: "Актуальные услуги, цены и история документов партнёра Clinic 07.",
  path: "/partners/clinic-07",
  type: "article",
});

export default function Clinic07Page() {
  return <PartnerDetailPage />;
}
