import type { Metadata } from "next";

import { AppShell } from "@/components/app-shell";
import { QualityReportPage } from "@/features/quality/quality-report-page";
import { createSeoMetadata } from "@/lib/seo";

export const metadata: Metadata = createSeoMetadata({
  title: "Отчёт качества | MedPrice",
  description: "Внутренний отчёт качества MedPrice.",
  path: "/quality",
  robots: { index: false, follow: false },
});

export default function QualityPage() {
  return (
    <AppShell activeNav="Quality" titleKey="quality.title" eyebrowKey="quality.eyebrow">
      <QualityReportPage />
    </AppShell>
  );
}
