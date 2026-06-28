"use client";

import { Activity, Stethoscope } from "lucide-react";

import { LanguageSwitcher } from "@/components/language-switcher";
import { LoginForm } from "@/components/login-form";
import { Badge } from "@/components/ui/badge";
import { useI18n } from "@/i18n";

export function LoginPageClient() {
  const { t } = useI18n();
  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-10">
      <div className="w-full max-w-md">
        <div className="mb-6 flex items-center justify-between gap-4">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-border bg-card text-primary">
              <Stethoscope className="h-5 w-5" aria-hidden="true" />
            </div>
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold text-foreground">MedArchive</div>
              <div className="truncate text-xs text-muted-foreground">{t("auth.clinicalOps")}</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <LanguageSwitcher />
            <Badge variant="info" className="gap-1">
              <Activity className="h-3.5 w-3.5" aria-hidden="true" />
              {t("app.admin")}
            </Badge>
          </div>
        </div>
        <LoginForm />
      </div>
    </main>
  );
}
