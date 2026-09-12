"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";
import { cn } from "@/lib/utils";

export function HashField({ label = "SHA-256", value }: { label?: string; value: string | null }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    if (!value) return;
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard API unavailable — silently ignore, value stays selectable/visible.
    }
  }

  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs font-bold uppercase tracking-wide text-ink-secondary">{label}</span>
      <div className="flex items-center gap-2 rounded-sm border border-border bg-canvas-subtle px-3 py-2">
        <code className="font-technical flex-1 text-xs text-ink">{value ?? "Non disponible"}</code>
        {value ? (
          <button
            type="button"
            onClick={handleCopy}
            aria-label="Copier le hachage"
            className={cn(
              "flex h-6 w-6 shrink-0 items-center justify-center rounded-sm text-ink-muted hover:bg-surface hover:text-primary",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            )}
          >
            {copied ? <Check className="h-3.5 w-3.5 text-healthy" aria-hidden="true" /> : <Copy className="h-3.5 w-3.5" aria-hidden="true" />}
          </button>
        ) : null}
      </div>
    </div>
  );
}
