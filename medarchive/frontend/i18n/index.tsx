"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { dictionaries, type TranslationKey } from "@/i18n/dictionaries";
import type { Lang } from "@/i18n/types";

const STORAGE_KEY = "medarchive.lang";
const DEFAULT_LANG: Lang = "ru";

type I18nContextValue = {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: (key: TranslationKey) => string;
};

const I18nContext = createContext<I18nContextValue | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(DEFAULT_LANG);

  useEffect(() => {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (isLang(saved)) {
      setLangState(saved);
    }
  }, []);

  const setLang = useCallback((nextLang: Lang) => {
    setLangState(nextLang);
    window.localStorage.setItem(STORAGE_KEY, nextLang);
    document.documentElement.lang = nextLang;
  }, []);

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  const t = useCallback((key: TranslationKey) => dictionaries[lang][key], [lang]);

  const value = useMemo(() => ({ lang, setLang, t }), [lang, setLang, t]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error("useI18n must be used inside I18nProvider");
  }
  return context;
}

function isLang(value: string | null): value is Lang {
  return value === "ru" || value === "kk" || value === "en";
}

export type { Lang, TranslationKey };
