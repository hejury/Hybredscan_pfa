import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

type Tone = "healthy" | "malicious" | "warning" | "info" | "neutral" | "primary";

const TONE_CLASSES: Record<Tone, string> = {
  healthy: "bg-healthy-bg text-healthy",
  malicious: "bg-malicious-bg text-malicious",
  warning: "bg-warning-bg text-warning",
  info: "bg-info-bg text-info",
  neutral: "bg-canvas-subtle text-ink-secondary",
  primary: "bg-primary-soft text-primary-soft-ink",
};

export function Badge({
  tone = "neutral",
  icon,
  children,
  className,
}: {
  tone?: Tone;
  icon?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-sm px-2.5 py-1 text-xs font-bold",
        TONE_CLASSES[tone],
        className
      )}
    >
      {icon}
      {children}
    </span>
  );
}
