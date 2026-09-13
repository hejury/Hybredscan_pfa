import { apiGet } from "@/lib/api/client";
import { mapHistoryEntry, type RawHistoryEntry } from "@/lib/api/mappers";
import type { FileFamily, HistoryEntry, Verdict } from "@/lib/types/backend";

/**
 * api/routers/dashboard.py aggregates history.csv + quarantine/ + the
 * watcher's status into these metrics server-side — no client-side
 * computation, no invented accuracy metric (cahier des charges §32:
 * history.csv has no ground truth, so no "taux de détection" is shown).
 */
export interface DashboardKpis {
  analysesToday: number;
  threatsDetected: number;
  /** null if the quarantine directory could not be read. */
  filesInQuarantine: number | null;
  totalAnalyzed: number;
  protectionActive: boolean;
}

export type VerdictBreakdown = Record<Verdict, number>;

/** Only the real supported families (cahier des charges §12: "not JPG/JS etc."). */
export type FileTypeBreakdown = Record<Extract<FileFamily, "pe" | "pdf" | "docx">, number>;

export interface DashboardSummary {
  kpis: DashboardKpis;
  verdictBreakdown: VerdictBreakdown;
  fileTypeBreakdown: FileTypeBreakdown;
  recentActivity: HistoryEntry[];
}

export function familyOf(entry: HistoryEntry): "pe" | "pdf" | "docx" | null {
  const name = entry.fileName.toLowerCase();
  if (name.endsWith(".exe") || name.endsWith(".dll")) return "pe";
  if (name.endsWith(".pdf")) return "pdf";
  if (name.endsWith(".docx") || name.endsWith(".doc")) return "docx";
  return null;
}

interface RawDashboardResponse {
  kpis: {
    analyses_today: number;
    threats_detected: number;
    quarantine_count: number | null;
    total_analyzed: number;
    protection_active: boolean;
  };
  verdict_breakdown: VerdictBreakdown;
  file_type_breakdown: FileTypeBreakdown;
  recent_activity: RawHistoryEntry[];
}

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  const raw = await apiGet<RawDashboardResponse>("/api/v1/dashboard");
  return {
    kpis: {
      analysesToday: raw.kpis.analyses_today,
      threatsDetected: raw.kpis.threats_detected,
      filesInQuarantine: raw.kpis.quarantine_count,
      totalAnalyzed: raw.kpis.total_analyzed,
      protectionActive: raw.kpis.protection_active,
    },
    verdictBreakdown: raw.verdict_breakdown,
    fileTypeBreakdown: raw.file_type_breakdown,
    recentActivity: raw.recent_activity.map(mapHistoryEntry),
  };
}
