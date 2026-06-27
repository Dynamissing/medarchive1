import { AppShell } from "@/components/app-shell";
import { QualityReportPage } from "@/features/quality/quality-report-page";

export default function QualityPage() {
  return (
    <AppShell activeNav="Quality" titleKey="quality.title" eyebrowKey="quality.eyebrow">
      <QualityReportPage />
    </AppShell>
  );
}
