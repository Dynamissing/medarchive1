import { ServiceDetailPage } from "@/features/service-detail/service-detail-page";

export const dynamicParams = false;

export function generateStaticParams() {
  return [{ id: "__placeholder" }];
}

export default async function ServicePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <ServiceDetailPage serviceId={id} />;
}
