import { cn } from "@/lib/cn";
import type { ButtonHTMLAttributes, ReactNode } from "react";

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
export type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  children: ReactNode;
  /** Figma: optional leading icon slot name */
  iconLeft?: ReactNode;
}

const variantClass: Record<ButtonVariant, string> = {
  primary: "ui-button--primary",
  secondary: "ui-button--secondary",
  ghost: "ui-button--ghost",
  danger: "ui-button--danger",
};

const sizeClass: Record<ButtonSize, string> = {
  sm: "ui-button--sm",
  md: "ui-button--md",
  lg: "ui-button--lg",
};

/**
 * UI Primitive — Figma `Button` 컴포넌트와 1:1 교체 대상.
 * props(variant, size) 시그니처 유지; 내부 마크업·CSS만 Figma 스펙으로 교체.
 */
export function Button({
  variant = "primary",
  size = "md",
  className,
  children,
  iconLeft,
  ...rest
}: ButtonProps) {
  return (
    <button
      type="button"
      className={cn("ui-button", variantClass[variant], sizeClass[size], className)}
      {...rest}
    >
      {iconLeft ? <span className="ui-button__icon">{iconLeft}</span> : null}
      <span className="ui-button__label">{children}</span>
    </button>
  );
}
