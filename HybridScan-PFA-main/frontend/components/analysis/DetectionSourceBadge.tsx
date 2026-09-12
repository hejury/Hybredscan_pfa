import { Badge } from "@/components/ui/Badge";
import { DETECTION_SOURCE_LABELS } from "@/lib/utils";
import type { DetectionSource } from "@/lib/types/backend";

/** `source` is a plain string (not the strict DetectionSource union): a
 * legacy history/quarantine row can carry an unrecognized "etape" value,
 * which must stay visible rather than crash the label lookup. */
export function DetectionSourceBadge({ source }: { source: string | null }) {
  if (!source) return <Badge tone="neutral">Non disponible</Badge>;
  const label = DETECTION_SOURCE_LABELS[source as DetectionSource] ?? source;
  return <Badge tone="info">{label}</Badge>;
}
