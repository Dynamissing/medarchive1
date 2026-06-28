import type { Metadata } from "next";

import { ServiceDetailPage } from "@/features/service-detail/service-detail-page";
import { createSeoMetadata } from "@/lib/seo";

export const metadata: Metadata = createSeoMetadata({
  path: "/services/complete-blood-count",
  type: "article",
});

export default function CompleteBloodCountPage() {
  return <ServiceDetailPage />;
}
