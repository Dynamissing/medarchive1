import { PartnerDetailPage } from "@/features/partner-detail/partner-detail-page";

export const dynamicParams = false;
const locales = ["ru", "kz", "en"];

export function generateStaticParams() {
  return locales.map((locale) => ({ locale, id: "__placeholder" }));
}

export default async function LocalizedClinicPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <PartnerDetailPage partnerId={id} />;
}
