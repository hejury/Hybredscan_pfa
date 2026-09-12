import type { SelectHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
}

export function Select({ label, id, className, children, ...props }: SelectProps) {
  return (
    <div className="flex flex-col gap-1.5">
      {label ? (
        <label htmlFor={id} className="text-sm font-bold text-ink">
          {label}
        </label>
      ) : null}
      <select
        id={id}
        className={cn(
          "rounded-sm border border-border bg-surface px-3 py-2.5 text-sm text-ink",
          "focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary",
          className
        )}
        {...props}
      >
        {children}
      </select>
    </div>
  );
}
