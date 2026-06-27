import type { Metadata } from "next";

import { AppShell } from "@/components/app-shell";
import { VerificationPage } from "@/features/verification/verification-page";
import { createSeoMetadata } from "@/lib/seo";

export const metadata: Metadata = createSeoMetadata({
  title: "Очередь проверки | MedPrice",
  description: "Внутренняя очередь проверки MedPrice.",
  path: "/verification",
  robots: { index: false, follow: false },
});

export default function VerificationQueuePage() {
  return (
    <AppShell activeNav="Verification" titleKey="verification.title" eyebrowKey="verification.eyebrow">
      <VerificationPage />
    </AppShell>
  );
}
