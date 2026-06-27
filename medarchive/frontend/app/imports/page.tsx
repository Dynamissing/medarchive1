import type { Metadata } from "next";

import { AppShell } from "@/components/app-shell";
import { ArchiveUploadForm } from "@/features/upload/archive-upload-form";
import { createSeoMetadata } from "@/lib/seo";

export const metadata: Metadata = createSeoMetadata({
  title: "Загрузка архива | MedPrice",
  description: "Внутренняя загрузка архивов MedPrice.",
  path: "/imports",
  robots: { index: false, follow: false },
});

export default function ImportsPage() {
  return (
    <AppShell activeNav="Imports" titleKey="upload.title" eyebrowKey="upload.eyebrow">
      <ArchiveUploadForm />
    </AppShell>
  );
}
