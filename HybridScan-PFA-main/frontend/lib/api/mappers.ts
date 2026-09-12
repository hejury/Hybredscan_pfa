/**
 * Raw (snake_case) shapes returned by the FastAPI bridge (api/schemas/*.py)
 * and the functions that map them into the frontend's camelCase domain
 * types (lib/types/backend.ts). This is the ONLY place that field-name
 * translation happens — every lib/api/*.ts adapter imports from here
 * rather than re-parsing responses itself.
 */
import type {
  AnalysisResult,
  FolderScanFileResult,
  FolderScanSummary,
  HistoryEntry,
  ProtectionEvent,
  ProtectionStatus,
  QuarantineAction,
  QuarantineEntry,
  VirusTotalResult,
} from "@/lib/types/backend";

export interface RawQuarantineAction {
  kind: "none" | "quarantined" | "quarantine_failed" | "auto_quarantine_disabled";
  storage_name: string | null;
  detail: string | null;
  reason: string | null;
}

export function mapQuarantineAction(raw: RawQuarantineAction): QuarantineAction {
  switch (raw.kind) {
    case "quarantined":
      return { kind: "quarantined", storageName: raw.storage_name ?? "" };
    case "quarantine_failed":
      return { kind: "quarantine_failed", detail: raw.detail ?? "" };
    case "auto_quarantine_disabled":
      return { kind: "auto_quarantine_disabled", reason: raw.reason ?? "" };
    default:
      return { kind: "none" };
  }
}

export interface RawVirusTotalResult {
  statut: string;
  detections: number | null;
  total_moteurs: number | null;
}

function mapVirusTotal(raw: RawVirusTotalResult | null): VirusTotalResult | null {
  if (!raw) return null;
  return {
    statut: raw.statut as VirusTotalResult["statut"],
    detections: raw.detections ?? undefined,
    totalMoteurs: raw.total_moteurs ?? undefined,
  };
}

export interface RawAnalysisResult {
  filename: string;
  sha256: string;
  family: AnalysisResult["family"];
  detection_source: AnalysisResult["detectionSource"];
  verdict: AnalysisResult["verdict"];
  confidence: number | null;
  detections: string | null;
  message: string;
  document_ml_supported: boolean | null;
  action: RawQuarantineAction;
  analyzed_at: string;
  virus_total: RawVirusTotalResult | null;
  file_size_bytes: number | null;
}

export function mapAnalysisResult(raw: RawAnalysisResult): AnalysisResult {
  return {
    fileName: raw.filename,
    sha256: raw.sha256,
    family: raw.family,
    detectionSource: raw.detection_source,
    verdict: raw.verdict,
    confidence: raw.confidence,
    detections: raw.detections,
    message: raw.message,
    documentMlSupported: raw.document_ml_supported,
    action: mapQuarantineAction(raw.action),
    analyzedAt: raw.analyzed_at,
    virusTotal: mapVirusTotal(raw.virus_total),
    fileSizeBytes: raw.file_size_bytes,
  };
}

export interface RawHistoryEntry {
  date: string;
  file_name: string;
  sha256: string;
  detection_source: string;
  verdict: string;
  confidence: number | null;
  detections: string | null;
  action: RawQuarantineAction;
}

export function mapHistoryEntry(raw: RawHistoryEntry): HistoryEntry {
  return {
    date: raw.date,
    fileName: raw.file_name,
    sha256: raw.sha256,
    detectionSource: raw.detection_source,
    verdict: raw.verdict,
    confidence: raw.confidence,
    detections: raw.detections,
    action: mapQuarantineAction(raw.action),
  };
}

export interface RawQuarantineEntry {
  id: string;
  status: QuarantineEntry["recordStatus"];
  display_name: string;
  quarantined_at: string | null;
  detection_source: string | null;
  reason: string | null;
  sha256: string | null;
  confidence: number | null;
  family: string | null;
  verdict: string | null;
  source_context: QuarantineEntry["sourceContext"] | null;
  original_removed: boolean | null;
  file_size_bytes: number | null;
  schema_format: QuarantineEntry["schemaFormat"];
}

export function mapQuarantineEntry(raw: RawQuarantineEntry): QuarantineEntry {
  return {
    id: raw.id,
    recordStatus: raw.status,
    displayName: raw.display_name,
    quarantinedAt: raw.quarantined_at,
    detectionSource: (raw.detection_source as QuarantineEntry["detectionSource"]) ?? null,
    reason: raw.reason,
    sha256: raw.sha256,
    confidence: raw.confidence,
    family: raw.family,
    verdict: (raw.verdict as QuarantineEntry["verdict"]) ?? null,
    sourceContext: raw.source_context,
    originalRemoved: raw.original_removed,
    fileSizeBytes: raw.file_size_bytes,
    schemaFormat: raw.schema_format,
  };
}

export interface RawFolderScanFileResult {
  file_name: string;
  relative_path: string;
  family: FolderScanFileResult["family"];
  verdict: FolderScanFileResult["verdict"];
  confidence: number | null;
  detection_source: FolderScanFileResult["detectionSource"];
  action: RawQuarantineAction;
  sha256: string | null;
}

export interface RawFolderScanSummary {
  path: string;
  recursive: boolean;
  automatic_quarantine: boolean;
  processed: number;
  malicious: number;
  healthy: number;
  indeterminate: number;
  technical_errors: number;
  skipped_subfolders: number;
  results: RawFolderScanFileResult[];
}

export function mapFolderScanSummary(raw: RawFolderScanSummary): FolderScanSummary {
  return {
    folderPath: raw.path,
    recursive: raw.recursive,
    autoQuarantine: raw.automatic_quarantine,
    filesExamined: raw.processed,
    malicious: raw.malicious,
    healthy: raw.healthy,
    indeterminate: raw.indeterminate,
    technicalErrors: raw.technical_errors,
    skippedSubfolders: raw.skipped_subfolders,
    results: raw.results.map((r) => ({
      fileName: r.file_name,
      relativePath: r.relative_path,
      family: r.family,
      verdict: r.verdict,
      confidence: r.confidence,
      detectionSource: r.detection_source,
      action: mapQuarantineAction(r.action),
      sha256: r.sha256,
    })),
  };
}

export interface RawProtectionStatus {
  active: boolean;
  configured_directories: string[];
  auto_quarantine: boolean | null;
}

export function mapProtectionStatus(raw: RawProtectionStatus): ProtectionStatus {
  return {
    active: raw.active,
    monitoredDirectories: raw.configured_directories,
    autoQuarantine: raw.auto_quarantine,
  };
}

export interface RawProtectionEvent {
  time: string;
  file_name: string;
  verdict: string;
  confidence: number | null;
  detection_source: string | null;
}

export function mapProtectionEvent(raw: RawProtectionEvent): ProtectionEvent {
  return {
    time: raw.time,
    fileName: raw.file_name,
    verdict: raw.verdict as ProtectionEvent["verdict"],
    confidence: raw.confidence,
    detectionSource: (raw.detection_source as ProtectionEvent["detectionSource"]) ?? null,
  };
}
