import type { InputHTMLAttributes } from "react";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

interface CheckboxProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {
  label: string;
  description?: string;
}

export function Checkbox({ label, description, id, className, ...props }: CheckboxProps) {
  return (
    <label htmlFor={id} className={cn("flex cursor-pointer items-start gap-3", className)}>
      <span className="relative mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center">
        <input
          id={id}
          type="checkbox"
          className="peer absolute h-5 w-5 cursor-pointer appearance-none rounded-sm border border-border-strong bg-surface checked:border-primary checked:bg-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
          {...props}
        />
        <Check
          className="pointer-events-none relative h-3.5 w-3.5 text-white opacity-0 peer-checked:opacity-100"
          aria-hidden="true"
        />
      </span>
      <span>
        <span className="block text-sm font-bold text-ink">{label}</span>
        {description ? <span className="block text-xs text-ink-muted">{description}</span> : null}
      </span>
    </label>
  );
}
