import { cn } from "@/lib/cn";
import type { HTMLAttributes, ReactNode } from "react";

export type BadgeKind = "system" | "user" | "unknown";

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  kind: BadgeKind;
  children: ReactNode;
}

/** Figma `Badge / Classification` 교체 대상 */
export function Badge({ kind, className, children, ...rest }: BadgeProps) {
  return (
    <span className={cn("ui-badge", `ui-badge--${kind}`, className)} {...rest}>
      {children}
    </span>
  );
}
