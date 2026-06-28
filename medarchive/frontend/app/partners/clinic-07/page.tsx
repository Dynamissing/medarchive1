import type { Metadata } from "next";

import { PartnerDetailPage } from "@/features/partner-detail/partner-detail-page";
import { createSeoMetadata } from "@/lib/seo";

export const metadata: Metadata = createSeoMetadata({
  path: "/partners/clinic-07",
  type: "article",
});

export default function Clinic07Page() {
  return <PartnerDetailPage />;
}
