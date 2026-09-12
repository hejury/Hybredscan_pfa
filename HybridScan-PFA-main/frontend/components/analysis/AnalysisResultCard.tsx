import { FileText } from "lucide-react";
import { Card, CardHeader } from "@/components/ui/Card";
import { VerdictBadge } from "@/components/analysis/VerdictBadge";
import { DetectionSourceBadge } from "@/components/analysis/DetectionSourceBadge";
import { HashField } from "@/components/analysis/HashField";
import { TechnicalDetails } from "@/components/analysis/TechnicalDetails";
import { formatDateTime, FAMILY_LABELS } from "@/lib/utils";
import type { AnalysisResult } from "@/lib/types/backend";

function actionLabel(action: AnalysisResult["action"]): string {
  switch (action.kind) {
    case "none":
      return "Aucune action";
    case "quarantined":
      return `Mis en quarantaine (${action.storageName})`;
    case "quarantine_failed":
      return `Échec de la mise en quarantaine : ${action.detail}`;
    case "auto_quarantine_disabled":
      return `Quarantaine automatique désactivée : ${action.reason}`;
  }
}

/** Renders exactly what the backend's analyser() call returned — no
 * reinterpreted verdicts, no fabricated stages (cahier des charges §28). */
export function AnalysisResultCard({ result }: { result: AnalysisResult }) {
  return (
    <Card>
      <CardHeader
        icon={<FileText className="h-4.5 w-4.5" aria-hidden="true" />}
        title={result.fileName}
        subtitle={`${FAMILY_LABELS[result.family]} · analysé le ${formatDateTime(result.analyzedAt)}`}
        action={<VerdictBadge verdict={result.verdict} />}
      />
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <DetectionSourceBadge source={result.detectionSource} />
      </div>
      <div className="mb-4">
        <HashField value={result.sha256} />
      </div>
      <TechnicalDetails result={result} />
      <div className="mt-4 rounded-sm bg-canvas-subtle px-3 py-2.5 text-sm text-ink-secondary">
        {actionLabel(result.action)}
      </div>
    </Card>
  );
}
