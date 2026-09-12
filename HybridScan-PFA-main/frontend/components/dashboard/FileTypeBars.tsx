import { FAMILY_LABELS } from "@/lib/utils";
import type { FileTypeBreakdown } from "@/lib/api/dashboard";

/** Only PE/PDF/DOCX — the real supported categories (cahier des charges
 * §12: "not JPG/JS etc."). */
export function FileTypeBars({ breakdown }: { breakdown: FileTypeBreakdown }) {
  const entries = (Object.keys(breakdown) as Array<keyof FileTypeBreakdown>).map((key) => ({
    key,
    label: FAMILY_LABELS[key],
    value: breakdown[key],
  }));
  const max = Math.max(1, ...entries.map((e) => e.value));

  return (
    <div className="flex flex-col gap-4">
      {entries.map((entry) => (
        <div key={entry.key}>
          <div className="mb-1.5 flex items-center justify-between text-sm">
            <span className="text-ink-secondary">{entry.label}</span>
            <span className="font-bold text-ink">{entry.value}</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-pill bg-canvas-subtle">
            <div
              className="h-full rounded-pill bg-primary"
              style={{ width: `${(entry.value / max) * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
