"use client";

import type { ReactNode } from "react";

import { I18nProvider, type Lang } from "@/i18n";

export function LocaleBoundary({ children, locale }: { children: ReactNode; locale: Lang }) {
  return (
    <I18nProvider initialLang={locale} lockToInitial>
      {children}
    </I18nProvider>
  );
}
