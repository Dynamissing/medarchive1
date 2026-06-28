export type RouteLocale = "ru" | "kz" | "en";
export type HtmlLocale = "ru" | "kk-KZ" | "en";

export const defaultLocale: RouteLocale = "ru";
export const supportedLocales: RouteLocale[] = ["ru", "kz", "en"];

export function isRouteLocale(value: string | null | undefined): value is RouteLocale {
  return value === "ru" || value === "kz" || value === "en";
}

export function normalizeLocale(value: string | null | undefined): RouteLocale {
  if (value === "kk") return "kz";
  return isRouteLocale(value) ? value : defaultLocale;
}

export function htmlLangForLocale(locale: RouteLocale): HtmlLocale {
  if (locale === "kz") return "kk-KZ";
  return locale;
}

export function legacyDictionaryLocale(locale: RouteLocale) {
  return locale === "kz" ? "kk" : locale;
}

export function localeFromPathname(pathname: string | null | undefined): RouteLocale | null {
  const firstSegment = pathname?.split("/").filter(Boolean)[0];
  return isRouteLocale(firstSegment) ? firstSegment : null;
}

export function switchLocalePath(pathname: string, nextLocale: RouteLocale) {
  const segments = pathname.split("/");
  const first = segments[1];
  if (isRouteLocale(first)) {
    segments[1] = nextLocale;
    return segments.join("/") || `/${nextLocale}`;
  }
  const cleaned = pathname === "/" ? "" : pathname;
  return `/${nextLocale}${cleaned}`;
}
