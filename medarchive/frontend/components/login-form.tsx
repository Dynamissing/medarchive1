"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { AlertCircle, Loader2, LockKeyhole, ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useI18n } from "@/i18n";
import { adminLogin, clearAdminToken, storeAdminToken } from "@/lib/api";

type LoginState = "idle" | "loading" | "error" | "success";

export function LoginForm() {
  const { t } = useI18n();
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [state, setState] = useState<LoginState>("idle");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setState("loading");

    try {
      const result = await adminLogin(username.trim(), password);
      storeAdminToken(result.access_token);
      setState("success");
      router.push("/dashboard");
    } catch {
      clearAdminToken();
      setState("error");
    }
  }

  const isLoading = state === "loading";

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="space-y-1">
        <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-md bg-primary text-primary-foreground">
          <LockKeyhole className="h-5 w-5" aria-hidden="true" />
        </div>
        <div>
          <CardTitle className="text-xl">{t("auth.title")}</CardTitle>
          <CardDescription>{t("auth.subtitle")}</CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <Label htmlFor="username">{t("auth.username")}</Label>
            <Input
              id="username"
              name="username"
              autoComplete="username"
              value={username}
              disabled={isLoading}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="admin"
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">{t("auth.password")}</Label>
            <Input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              value={password}
              disabled={isLoading}
              onChange={(event) => setPassword(event.target.value)}
              placeholder={t("auth.passwordPlaceholder")}
              required
            />
          </div>

          {state === "error" ? (
            <div className="flex items-start gap-2 rounded-md border border-destructive/35 bg-destructive/10 p-3 text-sm text-destructive">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
              <span>{t("auth.invalid")}</span>
            </div>
          ) : null}

          {state === "success" ? (
            <div className="flex items-start gap-2 rounded-md border border-success/35 bg-success-subtle p-3 text-sm text-success">
              <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
              <span>{t("auth.accepted")}</span>
            </div>
          ) : null}

          <Button className="w-full" type="submit" disabled={isLoading}>
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : <ShieldCheck className="h-4 w-4" aria-hidden="true" />}
            {isLoading ? t("auth.signingIn") : t("auth.signIn")}
          </Button>
        </form>

        <div className="mt-4 flex items-center justify-between gap-3 border-t border-border pt-4">
          <span className="text-xs text-muted-foreground">{t("auth.protected")}</span>
          <Badge variant={state === "error" ? "error" : state === "success" ? "success" : "info"}>
            {state === "loading" ? t("common.checking") : state === "error" ? t("common.rejected") : state === "success" ? t("app.ready") : t("common.secure")}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}
