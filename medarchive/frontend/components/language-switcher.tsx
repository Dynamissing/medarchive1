"use client";

import { cn } from "@/lib/utils";
import { useI18n, type Lang } from "@/i18n";

const languages: Array<{ value: Lang; labelKey: "lang.ru" | "lang.kk" | "lang.en" }> = [
  { value: "ru", labelKey: "lang.ru" },
  { value: "kk", labelKey: "lang.kk" },
  { value: "en", labelKey: "lang.en" },
];

export function LanguageSwitcher() {
  const { lang, setLang, t } = useI18n();

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
          onClick={() => setLang(language.value)}
        >
          {t(language.labelKey)}
        </button>
      ))}
    </div>
  );
}
