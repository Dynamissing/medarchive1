import { AppShell } from "@/components/app-shell";
import { UnmatchedPage } from "@/features/unmatched/unmatched-page";

export default function UnmatchedQueuePage() {
  return (
    <AppShell activeNav="Unmatched" titleKey="unmatched.title" eyebrowKey="unmatched.eyebrow">
      <UnmatchedPage />
    </AppShell>
  );
}
