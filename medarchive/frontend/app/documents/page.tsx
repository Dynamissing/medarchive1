import { AppShell } from "@/components/app-shell";
import { DocumentsPage } from "@/features/documents/documents-page";

export default function DocumentsStatusPage() {
  return (
    <AppShell activeNav="Documents" titleKey="documents.title" eyebrowKey="documents.eyebrow">
      <DocumentsPage />
    </AppShell>
  );
}
