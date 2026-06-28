"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { dictionaries, type TranslationKey } from "@/i18n/dictionaries";
import { htmlLangForLocale, legacyDictionaryLocale, normalizeLocale, type RouteLocale } from "@/i18n/locales";
import type { Lang } from "@/i18n/types";
import enMessages from "@/messages/en.json";
import kzMessages from "@/messages/kz.json";
import ruMessages from "@/messages/ru.json";

const STORAGE_KEY = "medarchive.lang";
const DEFAULT_LANG: Lang = "ru";

type I18nContextValue = {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: (key: TranslationKey | string) => string;
};

const I18nContext = createContext<I18nContextValue | null>(null);
const messages: Record<RouteLocale, unknown> = {
  ru: ruMessages,
  kz: kzMessages,
  en: enMessages,
};

export function I18nProvider({
  children,
  initialLang,
  lockToInitial = false,
}: {
  children: ReactNode;
  initialLang?: Lang;
  lockToInitial?: boolean;
}) {
  const normalizedInitial = initialLang ? normalizeLocale(initialLang) : undefined;
  const [lang, setLangState] = useState<Lang>(normalizedInitial ?? DEFAULT_LANG);

  useEffect(() => {
    if (normalizedInitial) {
      setLangState(normalizedInitial);
      return;
    }
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (isLang(saved)) {
      setLangState(normalizeLocale(saved));
    }
  }, [normalizedInitial]);

  const setLang = useCallback((nextLang: Lang) => {
    const normalized = normalizeLocale(nextLang);
    setLangState(normalized);
    if (!lockToInitial) {
      window.localStorage.setItem(STORAGE_KEY, normalized);
    }
    document.documentElement.lang = htmlLangForLocale(normalized);
  }, [lockToInitial]);

  useEffect(() => {
    document.documentElement.lang = htmlLangForLocale(lang);
  }, [lang]);

  const t = useCallback((key: TranslationKey | string) => {
    const messageValue = getNestedMessage(messages[lang], key);
    if (typeof messageValue === "string") {
      return messageValue;
    }
    const legacyLang = legacyDictionaryLocale(lang);
    const legacyKey = key as TranslationKey;
    return dictionaries[legacyLang][legacyKey] ?? dictionaries.ru[legacyKey] ?? key;
  }, [lang]);

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

function isLang(value: string | null) {
  return value === "ru" || value === "kz" || value === "kk" || value === "en";
}

function getNestedMessage(source: unknown, key: string) {
  return key.split(".").reduce<unknown>((current, part) => {
    if (current && typeof current === "object" && part in current) {
      return (current as Record<string, unknown>)[part];
    }
    return undefined;
  }, source);
}

export type { Lang, TranslationKey };
