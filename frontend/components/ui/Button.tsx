import type { ButtonHTMLAttributes } from "react";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

type Variant = "primary" | "secondary" | "ghost" | "danger";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  loading?: boolean;
}

const VARIANT_CLASSES: Record<Variant, string> = {
  primary: "bg-primary text-white hover:bg-primary-hover active:bg-primary-active",
  secondary:
    "bg-surface text-ink border border-border hover:bg-canvas-subtle",
  ghost: "bg-transparent text-primary hover:bg-primary-soft",
  danger:
    "bg-malicious-bg text-malicious border border-malicious/30 hover:bg-malicious-bg/70",
};

export function Button({
  variant = "primary",
  loading = false,
  disabled,
  className,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-sm px-4 py-2.5 text-sm font-bold transition-colors",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2",
        "disabled:cursor-not-allowed disabled:bg-canvas-subtle disabled:text-ink-muted disabled:border-transparent",
        VARIANT_CLASSES[variant],
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : null}
      {children}
    </button>
  );
}
