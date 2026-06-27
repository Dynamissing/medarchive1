import type { Metadata } from "next";

import { LoginPageClient } from "@/features/auth/login-page-client";
import { createSeoMetadata } from "@/lib/seo";

export const metadata: Metadata = createSeoMetadata({
  title: "Вход администратора | MedPrice",
  description: "Вход в административную панель MedPrice.",
  path: "/login",
  robots: { index: false, follow: false },
});

export default function LoginPage() {
  return <LoginPageClient />;
}
