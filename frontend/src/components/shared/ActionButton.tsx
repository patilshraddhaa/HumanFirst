import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "./utils";

type ActionButtonVariant = "primary" | "secondary" | "ghost";

const variantClasses: Record<ActionButtonVariant, string> = {
  primary:
    "bg-ink-base text-ink-inverse hover:bg-brand-strong focus-visible:outline-brand",
  secondary:
    "border border-line-strong bg-surface-elevated text-ink-base hover:bg-canvas-accent focus-visible:outline-brand",
  ghost:
    "bg-transparent text-ink-base hover:bg-surface-tint focus-visible:outline-brand",
};

type ActionButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  icon?: ReactNode;
  variant?: ActionButtonVariant;
};

export function ActionButton({
  children,
  className,
  disabled,
  icon,
  type = "button",
  variant = "primary",
  ...props
}: ActionButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-pill px-4 py-2.5 text-sm font-semibold transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
        variantClasses[variant],
        className,
      )}
      disabled={disabled}
      {...props}
    >
      {icon ? <span aria-hidden="true">{icon}</span> : null}
      <span>{children}</span>
    </button>
  );
}
