import { formatConfidence, formatFileSize } from "@/lib/utils";
import type { AnalysisResult } from "@/lib/types/backend";

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-border py-2.5 last:border-b-0">
      <span className="text-sm text-ink-secondary">{label}</span>
      <span className="text-right text-sm font-bold text-ink">{value}</span>
    </div>
  );
}

export function TechnicalDetails({ result }: { result: AnalysisResult }) {
  return (
    <div className="flex flex-col">
      <Row label="Taille du fichier" value={formatFileSize(result.fileSizeBytes)} />
      <Row label="Probabilité malware" value={formatConfidence(result.confidence)} />
      <Row label="Détections" value={result.detections ?? "—"} />
      {result.virusTotal ? (
        <>
          <Row label="Statut VirusTotal" value={result.virusTotal.statut} />
          {result.virusTotal.detections !== undefined && result.virusTotal.totalMoteurs !== undefined ? (
            <Row
              label="Moteurs VirusTotal"
              value={`${result.virusTotal.detections} / ${result.virusTotal.totalMoteurs}`}
            />
          ) : null}
        </>
      ) : null}
      {result.documentMlSupported !== null ? (
        <Row label="Analyse IA document" value={result.documentMlSupported ? "Prise en charge" : "Non prise en charge"} />
      ) : null}
      <Row label="Message" value={result.message || "—"} />
    </div>
  );
}
