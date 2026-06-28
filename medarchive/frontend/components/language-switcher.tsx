"use client";

import { Suspense } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { switchLocalePath } from "@/i18n/locales";
import { cn } from "@/lib/utils";
import { useI18n, type Lang } from "@/i18n";

const languages: Array<{ value: Lang; labelKey: "lang.ru" | "lang.kk" | "lang.en" }> = [
  { value: "ru", labelKey: "lang.ru" },
  { value: "kz", labelKey: "lang.kk" },
  { value: "en", labelKey: "lang.en" },
];

export function LanguageSwitcher() {
  return (
    <Suspense fallback={<div className="h-9 w-24 rounded-md border border-border bg-card" />}>
      <LanguageSwitcherInner />
    </Suspense>
  );
}

function LanguageSwitcherInner() {
  const { lang, setLang, t } = useI18n();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const router = useRouter();

  function switchLanguage(nextLang: Lang) {
    setLang(nextLang);
    const nextPath = localizedPath(pathname, nextLang);
    if (!nextPath) {
      return;
    }
    const query = searchParams.toString();
    router.push(query ? `${nextPath}?${query}` : nextPath);
  }

  return (
    <div className="inline-flex h-9 items-center rounded-md border border-border bg-card p-1">
      {languages.map((language) => (
        <button
          key={language.value}
          type="button"
          className={cn(
            "h-7 rounded px-2 text-xs font-medium text-muted-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
            lang === language.value && "bg-secondary text-foreground",
          )}
          onClick={() => switchLanguage(language.value)}
        >
          {t(language.labelKey)}
        </button>
      ))}
    </div>
  );
}

function localizedPath(pathname: string, nextLang: Lang) {
  if (pathname === "/" || pathname === "/ru" || pathname === "/kz" || pathname === "/en") {
    return `/${nextLang}`;
  }
  if (pathname === "/services/complete-blood-count") {
    return `/${nextLang}/services/complete-blood-count`;
  }
  if (pathname === "/partners/clinic-07") {
    return `/${nextLang}/clinics/clinic-07`;
  }
  if (/^\/(ru|kz|en)(\/|$)/.test(pathname)) {
    return switchLocalePath(pathname, nextLang);
  }
  return null;
}
