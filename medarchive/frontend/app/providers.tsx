"use client";

import type { ReactNode } from "react";

import { I18nProvider } from "@/i18n";
import type { Lang } from "@/i18n";

export function Providers({ children, initialLang, lockToInitial }: { children: ReactNode; initialLang?: Lang; lockToInitial?: boolean }) {
  return <I18nProvider initialLang={initialLang} lockToInitial={lockToInitial}>{children}</I18nProvider>;
}
