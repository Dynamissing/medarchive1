import { PartnerDetailPage } from "@/features/partner-detail/partner-detail-page";

export const dynamicParams = false;

export function generateStaticParams() {
  return [{ id: "__placeholder" }];
}

export default async function PartnerPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <PartnerDetailPage partnerId={id} />;
}
