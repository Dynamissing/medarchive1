import type { Metadata } from "next";

import { LoginPageClient } from "@/features/auth/login-page-client";
import { createSeoMetadata, seoMessage } from "@/lib/seo";

export const metadata: Metadata = createSeoMetadata({
  title: seoMessage("ru", "seo.login.title"),
  description: seoMessage("ru", "seo.login.description"),
  path: "/login",
  robots: { index: false, follow: false },
});

export default function LoginPage() {
  return <LoginPageClient />;
}
