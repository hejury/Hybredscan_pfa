import { apiPostForm } from "@/lib/api/client";
import { mapAnalysisResult, type RawAnalysisResult } from "@/lib/api/mappers";
import type { AnalysisResult } from "@/lib/types/backend";

/** Same limit the API enforces (api/config.py::MAX_UPLOAD_SIZE_MB) —
 * never advertise a different value here than the server checks. */
export const MAX_UPLOAD_SIZE_MB = 200;

export const SUPPORTED_EXTENSIONS = [".exe", ".dll", ".pdf", ".docx", ".doc"] as const;

/**
 * Uploads a file to the real HybridScan pipeline
 * (api/routers/analysis.py -> analyze.analyser). The browser's filename
 * is sent as metadata only — the server never trusts it as a path.
 */
export async function submitFileForAnalysis(
  file: File,
  options: { autoQuarantine: boolean }
): Promise<AnalysisResult> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("auto_quarantine", String(options.autoQuarantine));
  const raw = await apiPostForm<RawAnalysisResult>("/api/v1/analysis/file", formData);
  return mapAnalysisResult(raw);
}
