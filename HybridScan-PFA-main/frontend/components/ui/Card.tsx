import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/utils";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("rounded-md border border-border bg-surface p-6", className)}
      {...props}
    />
  );
}

export function CardHeader({
  title,
  subtitle,
  icon,
  action,
  className,
}: {
  title: ReactNode;
  subtitle?: ReactNode;
  icon?: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("mb-4 flex items-start justify-between gap-4", className)}>
      <div className="flex items-start gap-3">
        {icon ? (
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-sm bg-primary-soft text-primary">
            {icon}
          </span>
        ) : null}
        <div>
          <h2 className="text-[0.95rem] font-bold text-ink">{title}</h2>
          {subtitle ? <p className="mt-0.5 text-sm text-ink-secondary">{subtitle}</p> : null}
        </div>
      </div>
      {action}
    </div>
  );
}
