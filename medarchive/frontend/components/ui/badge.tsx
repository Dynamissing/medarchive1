import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex h-6 items-center gap-1 whitespace-nowrap rounded-md border px-2 text-xs font-medium leading-none",
  {
    variants: {
      variant: {
        neutral: "border-border bg-secondary text-secondary-foreground",
        success: "border-success/35 bg-success-subtle text-success",
        warning: "border-warning/35 bg-warning-subtle text-warning",
        error: "border-destructive/35 bg-destructive/15 text-destructive",
        info: "border-info/35 bg-info-subtle text-info",
      },
    },
    defaultVariants: {
      variant: "neutral",
    },
  },
);

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement>, VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}
