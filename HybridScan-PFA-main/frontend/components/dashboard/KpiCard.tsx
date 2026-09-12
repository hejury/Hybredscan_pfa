import type { LucideIcon } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { cn } from "@/lib/utils";

export function KpiCard({
  icon: Icon,
  label,
  value,
  tone = "primary",
}: {
  icon: LucideIcon;
  label: string;
  value: string;
  tone?: "primary" | "malicious" | "warning" | "healthy";
}) {
  const toneClasses: Record<typeof tone, string> = {
    primary: "bg-primary-soft text-primary",
    malicious: "bg-malicious-bg text-malicious",
    warning: "bg-warning-bg text-warning",
    healthy: "bg-healthy-bg text-healthy",
  };

  return (
    <Card className="flex items-center gap-4">
      <span className={cn("flex h-11 w-11 shrink-0 items-center justify-center rounded-md", toneClasses[tone])}>
        <Icon className="h-5 w-5" aria-hidden="true" />
      </span>
      <div>
        <p className="text-2xl font-bold text-ink">{value}</p>
        <p className="text-sm text-ink-secondary">{label}</p>
      </div>
    </Card>
  );
}
