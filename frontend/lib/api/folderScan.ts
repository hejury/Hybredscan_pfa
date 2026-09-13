import { apiGet, apiPost } from "@/lib/api/client";
import { mapFolderScanSummary, type RawFolderScanSummary } from "@/lib/api/mappers";
import type { FolderScanConfig, FolderScanSummary } from "@/lib/types/backend";

/** Fallback shown only before fetchFolderScanConfig() resolves — the real,
 * authoritative list always comes from FolderScanConfig.supportedExtensions
 * (backend_shared.EXTENSIONS_SCAN_DOSSIER, the single source of truth
 * shared with Streamlit and mirrored by api/config.py::FOLDER_SCAN_EXTENSIONS).
 * Never advertise more than the backend actually supports (cahier des charges §19). */
export const FOLDER_SCAN_SUPPORTED_EXTENSIONS = [".exe", ".dll", ".pdf", ".docx"] as const;

interface RawFolderScanConfig {
  configured: boolean;
  allowed_roots: string[];
  supported_extensions: string[];
}

/** api/routers/folder_scan.py -> backend_shared._racines_autorisees(). */
export async function fetchFolderScanConfig(): Promise<FolderScanConfig> {
  const raw = await apiGet<RawFolderScanConfig>("/api/v1/scan/folder/config");
  return {
    configured: raw.configured,
    allowedRoots: raw.allowed_roots,
    supportedExtensions: raw.supported_extensions,
  };
}

/**
 * api/routers/folder_scan.py -> backend_shared.valider_dossier_scan() +
 * analyze.analyser() per eligible file, executed server-side only.
 */
export async function launchFolderScan(options: {
  folderPath: string;
  recursive: boolean;
  autoQuarantine: boolean;
}): Promise<FolderScanSummary> {
  const raw = await apiPost<RawFolderScanSummary>("/api/v1/scan/folder", {
    path: options.folderPath,
    recursive: options.recursive,
    automatic_quarantine: options.autoQuarantine,
  });
  return mapFolderScanSummary(raw);
}
