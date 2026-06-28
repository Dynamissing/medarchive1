"use client";

import { useState } from "react";
import { Link2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useI18n } from "@/i18n";

export function CopyLinkButton({
  href,
  label,
  copiedLabel,
  variant = "ghost",
  className,
}: {
  href?: string;
  label?: string;
  copiedLabel?: string;
  variant?: "ghost" | "secondary";
  className?: string;
}) {
  const { t } = useI18n();
  const [copied, setCopied] = useState(false);
  const buttonLabel = label ?? t("share.copy");
  const successLabel = copiedLabel ?? t("share.copied");

  async function copyLink() {
    const value = href ? new URL(href, window.location.origin).toString() : window.location.href;
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(value);
    } else {
      window.prompt(buttonLabel, value);
    }
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  return (
    <Button type="button" variant={variant} className={className} onClick={copyLink}>
      <Link2 className="h-4 w-4" aria-hidden="true" />
      {copied ? successLabel : buttonLabel}
    </Button>
  );
}
