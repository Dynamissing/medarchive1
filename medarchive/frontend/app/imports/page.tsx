import { AppShell } from "@/components/app-shell";
import { ArchiveUploadForm } from "@/features/upload/archive-upload-form";

export default function ImportsPage() {
  return (
    <AppShell activeNav="Imports" titleKey="upload.title" eyebrowKey="upload.eyebrow">
      <ArchiveUploadForm />
    </AppShell>
  );
}
