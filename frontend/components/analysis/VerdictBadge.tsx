import { AlertTriangle, CheckCircle2, HelpCircle, ShieldAlert } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { VERDICT_LABELS } from "@/lib/utils";

/**
 * Verdict is NEVER encoded by color alone (cahier des charges §33): every
 * instance pairs an icon, a color tone, AND the French text label.
 *
 * `verdict` is a plain string, not the strict Verdict union: a legacy or
 * malformed history/quarantine row can carry an unrecognized value (see
 * lib/types/backend.ts::HistoryEntry). Such a value is shown as
 * "Erreur technique" — never silently rendered as "Indéterminé", which
 * would misrepresent a data problem as a real analysis outcome (same
 * distinction app.py draws between VERDICTS and _VERDICT_INCONNU).
 */
export function VerdictBadge({ verdict }: { verdict: string }) {
  if (verdict === "sain") {
    return (
      <Badge tone="healthy" icon={<CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />}>
        {VERDICT_LABELS.sain}
      </Badge>
    );
  }
  if (verdict === "malveillant") {
    return (
      <Badge tone="malicious" icon={<ShieldAlert className="h-3.5 w-3.5" aria-hidden="true" />}>
        {VERDICT_LABELS.malveillant}
      </Badge>
    );
  }
  if (verdict === "indetermine") {
    return (
      <Badge tone="warning" icon={<HelpCircle className="h-3.5 w-3.5" aria-hidden="true" />}>
        {VERDICT_LABELS.indetermine}
      </Badge>
    );
  }
  return (
    <Badge tone="warning" icon={<AlertTriangle className="h-3.5 w-3.5" aria-hidden="true" />}>
      Erreur technique
    </Badge>
  );
}
