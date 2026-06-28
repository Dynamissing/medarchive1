"use client";

import { Archive, BarChart3, FileSearch, LayoutDashboard, SearchX, ShieldCheck, Stethoscope } from "lucide-react";
import type { ReactNode } from "react";

import { LanguageSwitcher } from "@/components/language-switcher";
import { useI18n, type TranslationKey } from "@/i18n";
import { cn } from "@/lib/utils";

type NavLabel = "Dashboard" | "Imports" | "Documents" | "Verification" | "Unmatched" | "Quality";

const navItems: Array<{ label: NavLabel; labelKey: TranslationKey; icon: typeof LayoutDashboard; href: string }> = [
  { label: "Dashboard", labelKey: "nav.dashboard", icon: LayoutDashboard, href: "/dashboard" },
  { label: "Imports", labelKey: "nav.imports", icon: Archive, href: "/imports" },
  { label: "Documents", labelKey: "nav.documents", icon: FileSearch, href: "/documents" },
  { label: "Verification", labelKey: "nav.verification", icon: ShieldCheck, href: "/verification" },
  { label: "Unmatched", labelKey: "nav.unmatched", icon: SearchX, href: "/unmatched" },
  { label: "Quality", labelKey: "nav.quality", icon: BarChart3, href: "/quality" },
];

export function AppShell({
  children,
  activeNav = "Dashboard",
  titleKey = "dashboard.title",
  eyebrowKey = "dashboard.eyebrow",
}: {
  children: ReactNode;
  activeNav?: NavLabel;
  titleKey?: TranslationKey;
  eyebrowKey?: TranslationKey;
}) {
  return (
    <div className="min-h-screen bg-background">
      <Sidebar activeNav={activeNav} />
      <div className="min-h-screen lg:pl-72">
        <TopBar titleKey={titleKey} eyebrowKey={eyebrowKey} />
        <main className="mx-auto w-full max-w-7xl px-4 py-5 sm:px-6 lg:px-8">{children}</main>
      </div>
    </div>
  );
}

function Sidebar({ activeNav }: { activeNav: NavLabel }) {
  const { t } = useI18n();
  return (
    <aside className="hidden fixed inset-y-0 left-0 z-30 w-72 border-r border-border bg-card/95 lg:flex lg:flex-col">
      <div className="flex h-16 items-center gap-3 border-b border-border px-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary text-primary-foreground">
          <Stethoscope className="h-5 w-5" aria-hidden="true" />
        </div>
        <div>
          <div className="text-sm font-semibold text-foreground">MedArchive</div>
          <div className="text-xs text-muted-foreground">{t("app.ops")}</div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map((item) => (
          <a
            key={item.label}
            href={item.href}
            className={cn(
              "flex h-10 items-center gap-3 rounded-md px-3 text-sm font-medium text-muted-foreground transition-colors",
              item.label === activeNav && "bg-secondary text-foreground",
              item.label !== activeNav && "hover:bg-secondary/70 hover:text-foreground",
            )}
          >
            <item.icon className="h-4 w-4" aria-hidden="true" />
            {t(item.labelKey)}
          </a>
        ))}
      </nav>
    </aside>
  );
}

function TopBar({ titleKey, eyebrowKey }: { titleKey: TranslationKey; eyebrowKey: TranslationKey }) {
  const { t } = useI18n();
  return (
    <header className="sticky top-0 z-20 border-b border-border bg-background/95">
      <div className="flex h-16 items-center justify-between gap-3 px-4 sm:px-6 lg:px-8">
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase text-muted-foreground">{t(eyebrowKey)}</p>
          <h1 className="truncate text-xl font-semibold">{t(titleKey)}</h1>
        </div>
        <div className="flex items-center gap-2">
          <LanguageSwitcher />
        </div>
      </div>
    </header>
  );
}
