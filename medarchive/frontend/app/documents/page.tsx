import type { Metadata } from "next";

import { AppShell } from "@/components/app-shell";
import { DocumentsPage } from "@/features/documents/documents-page";
import { createSeoMetadata } from "@/lib/seo";

export const metadata: Metadata = createSeoMetadata({
  title: "Статус документов | MedPrice",
  description: "Внутренний мониторинг обработки документов MedPrice.",
  path: "/documents",
  robots: { index: false, follow: false },
});

export default function DocumentsStatusPage() {
  return (
    <AppShell activeNav="Documents" titleKey="documents.title" eyebrowKey="documents.eyebrow">
      <DocumentsPage />
    </AppShell>
  );
}
