import type { InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
}

export function Input({ label, hint, id, className, ...props }: InputProps) {
  return (
    <div className="flex flex-col gap-1.5">
      {label ? (
        <label htmlFor={id} className="text-sm font-bold text-ink">
          {label}
        </label>
      ) : null}
      <input
        id={id}
        className={cn(
          "rounded-sm border border-border bg-surface px-3 py-2.5 text-sm text-ink placeholder:text-ink-muted",
          "focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary",
          className
        )}
        {...props}
      />
      {hint ? <p className="text-xs text-ink-muted">{hint}</p> : null}
    </div>
  );
}
