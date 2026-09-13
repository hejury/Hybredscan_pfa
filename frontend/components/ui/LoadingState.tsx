import { Loader2 } from "lucide-react";

export function LoadingState({ label = "Chargement…" }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-10 text-sm text-ink-muted" role="status">
      <Loader2 className="h-5 w-5 animate-spin text-primary" aria-hidden="true" />
      {label}
    </div>
  );
}
