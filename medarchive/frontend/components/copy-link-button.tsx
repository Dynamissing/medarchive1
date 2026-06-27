"use client";

import { useState } from "react";
import { Link2 } from "lucide-react";

import { Button } from "@/components/ui/button";

export function CopyLinkButton({
  href,
  label = "Поделиться",
  copiedLabel = "Ссылка скопирована",
  variant = "ghost",
  className,
}: {
  href?: string;
  label?: string;
  copiedLabel?: string;
  variant?: "ghost" | "secondary";
  className?: string;
}) {
  const [copied, setCopied] = useState(false);

  async function copyLink() {
    const value = href ? new URL(href, window.location.origin).toString() : window.location.href;
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(value);
    } else {
      window.prompt(label, value);
    }
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  return (
    <Button type="button" variant={variant} className={className} onClick={copyLink}>
      <Link2 className="h-4 w-4" aria-hidden="true" />
      {copied ? copiedLabel : label}
    </Button>
  );
}
