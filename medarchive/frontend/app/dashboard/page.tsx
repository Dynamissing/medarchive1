import type { Metadata } from "next";

import { DashboardPage } from "@/features/dashboard/dashboard-page";
import { createSeoMetadata } from "@/lib/seo";

export const metadata: Metadata = createSeoMetadata({
  title: "Панель администратора | MedPrice",
  description: "Внутренняя панель администратора MedPrice.",
  path: "/dashboard",
  robots: { index: false, follow: false },
});

export default function AdminDashboardPage() {
  return <DashboardPage />;
}
