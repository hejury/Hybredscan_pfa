import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/Button";

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-10 text-center" role="alert">
      <span className="flex h-10 w-10 items-center justify-center rounded-full bg-malicious-bg text-malicious">
        <AlertTriangle className="h-5 w-5" aria-hidden="true" />
      </span>
      <p className="text-sm font-bold text-ink">{message}</p>
      {onRetry ? (
        <Button variant="secondary" onClick={onRetry}>
          Réessayer
        </Button>
      ) : null}
    </div>
  );
}
