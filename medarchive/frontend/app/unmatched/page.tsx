import type { Metadata } from "next";

import { AppShell } from "@/components/app-shell";
import { UnmatchedPage } from "@/features/unmatched/unmatched-page";
import { createSeoMetadata } from "@/lib/seo";

export const metadata: Metadata = createSeoMetadata({
  title: "Очередь без совпадений | MedPrice",
  description: "Внутренняя очередь ручного сопоставления MedPrice.",
  path: "/unmatched",
  robots: { index: false, follow: false },
});

export default function UnmatchedQueuePage() {
  return (
    <AppShell activeNav="Unmatched" titleKey="unmatched.title" eyebrowKey="unmatched.eyebrow">
      <UnmatchedPage />
    </AppShell>
  );
}
