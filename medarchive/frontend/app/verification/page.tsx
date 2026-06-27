import { AppShell } from "@/components/app-shell";
import { VerificationPage } from "@/features/verification/verification-page";

export default function VerificationQueuePage() {
  return (
    <AppShell activeNav="Verification" titleKey="verification.title" eyebrowKey="verification.eyebrow">
      <VerificationPage />
    </AppShell>
  );
}
