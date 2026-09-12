/**
 * Types modeling the REAL HybridScan Python backend concepts (analyze.py,
 * quarantine_manager.py, history.csv, watcher.py), now backed by a real
 * FastAPI bridge (see api/ and validation/NEXTJS-FASTAPI-INTEGRATION.md).
 * lib/api/*.ts adapters fetch the API's snake_case JSON and map it into
 * these camelCase types — the mapping is the ONLY place field names
 * change; nothing about backend semantics is reinterpreted there.
 *
 * Every field here traces to a specific Python source, noted in comments
 * — nothing invented beyond what the backend actually produces.
 */

/** verdict: analyze.py `r["verdict"]` / history.csv `verdict` column. */
export type Verdict = "sain" | "malveillant" | "indetermine";

/** famille: analyze.py `identifier_fichier()` / `r["famille"]`. */
export type FileFamily = "pe" | "pdf" | "doc" | "docx" | "inconnu";

/**
 * etape: analyze.py `r["etape"]`. Exactly the values the backend
 * currently produces — never invented stages (cahier des charges §17).
 */
export type DetectionSource =
  | "1 (signature)"
  | "2 (IA)"
  | "2 (ia_pdf)"
  | "2 (ia_docx)"
  | "2 (document)"
  | "2 (format invalide)";

/** action: analyze.py `r["action"]`, normalized into a discriminated shape. */
export type QuarantineAction =
  | { kind: "none" }
  | { kind: "quarantined"; storageName: string }
  | { kind: "quarantine_failed"; detail: string }
  | { kind: "auto_quarantine_disabled"; reason: string };

/** etape1: analyze.py `etape1_virustotal()` return shape. */
export interface VirusTotalResult {
  statut:
    | "malveillant"
    | "sain"
    | "inconnu"
    | "erreur_cle_absente"
    | "erreur_reseau"
    | "erreur_cle"
    | "erreur_quota"
    | "erreur_api";
  detections?: number;
  totalMoteurs?: number;
}

/**
 * The full result of one analyser() call (single file OR one row of a
 * folder scan). Field names are the English/camelCase equivalent of
 * analyze.py's `r` dict — see the trailing comment on each field for the
 * exact Python key it corresponds to.
 */
export interface AnalysisResult {
  fileName: string; // r["fichier"]
  sha256: string; // r["sha256"]
  family: FileFamily; // r["famille"]
  detectionSource: DetectionSource; // r["etape"]
  verdict: Verdict; // r["verdict"]
  /** null when the backend itself returns "" (no confidence produced). */
  confidence: number | null; // r["confiance"]
  detections: string | null; // r["detections"], e.g. "0/64"
  message: string; // r["message"]
  documentMlSupported: boolean | null; // r["document_ml_supported"], PE has none
  action: QuarantineAction; // r["action"], parsed
  analyzedAt: string; // r["date"], ISO 8601
  virusTotal: VirusTotalResult | null; // r["etape1"]
  fileSizeBytes: number | null;
}

/**
 * One row of history.csv. `verdict`/`detectionSource` are plain strings
 * (not the strict Verdict/DetectionSource unions) — a legacy or malformed
 * row can carry an unrecognized value, and it must stay visible rather
 * than fail type validation (cahier des charges §23).
 */
export interface HistoryEntry {
  date: string; // history.csv "date"
  fileName: string; // "fichier"
  sha256: string; // "sha256"
  detectionSource: string; // "etape"
  verdict: string; // "verdict"
  confidence: number | null; // "confiance"
  detections: string | null; // "detections"
  action: QuarantineAction; // "action", parsed
}

/** source_context: quarantine_manager.py SOURCE_* constants. */
export type QuarantineSourceContext = "upload" | "folder_scan" | "watcher" | "other";

/** One quarantine record — quarantine_manager.py normalized shape
 * (list_quarantine_items / get_quarantine_details), covers BOTH the
 * current metadata schema and legacy pre-MVP records. */
export interface QuarantineEntry {
  id: string;
  /** "isole" | "incomplet" | "fichier_introuvable" | "metadonnees_illisibles" | "sans_metadonnees" */
  recordStatus:
    | "isole"
    | "incomplet"
    | "fichier_introuvable"
    | "metadonnees_illisibles"
    | "sans_metadonnees";
  displayName: string; // "nom_affiche" — "Fichier non identifié" if unknown, never fabricated
  quarantinedAt: string | null; // "date_isolation"
  detectionSource: DetectionSource | null; // "detecte_par"
  reason: string | null; // "details" / "reason"
  sha256: string | null;
  confidence: number | null;
  family: string | null;
  verdict: Verdict | null;
  sourceContext: QuarantineSourceContext | null;
  /** true only for folder_scan/watcher; upload NEVER claims true (BF6). */
  originalRemoved: boolean | null;
  fileSizeBytes: number | null;
  /** "actuel" = current metadata schema, "legacy" = pre-MVP record. */
  schemaFormat: "actuel" | "legacy";
}

/** One file result inside a folder-scan run — same shape family as
 * AnalysisResult; the backend routes each candidate file (.exe/.dll/
 * .pdf/.docx — backend_shared.EXTENSIONS_SCAN_DOSSIER) through the same
 * analyser() used for single-file analysis, so `family` may be any of
 * "pe"/"pdf"/"docx" here, never PE-only. "erreur" is not a value
 * analyser() itself produces — it's the scan wrapper's own count for a
 * file whose analyser() call raised an exception entirely (see
 * app.py's folder-scan loop / api/services/folder_scan_service.py). */
export interface FolderScanFileResult {
  fileName: string;
  relativePath: string;
  family: FileFamily;
  verdict: Verdict | "erreur";
  confidence: number | null;
  detectionSource: DetectionSource | null;
  action: QuarantineAction;
  sha256: string | null;
}

export interface FolderScanSummary {
  folderPath: string;
  recursive: boolean;
  autoQuarantine: boolean;
  filesExamined: number;
  malicious: number;
  healthy: number;
  indeterminate: number;
  technicalErrors: number;
  skippedSubfolders: number;
  results: FolderScanFileResult[];
}

/** backend_shared.py::_racines_autorisees() — the configured allowed scan root(s). */
export interface FolderScanConfig {
  configured: boolean;
  allowedRoots: string[];
  supportedExtensions: string[]; // [".exe", ".dll", ".pdf", ".docx"] today — never advertise more than the backend actually supports
}

/**
 * watcher.py Protection state, as observed by the API process holding
 * the (single, never-auto-started) Protection instance.
 * `monitoredDirectories` lists watcher.py::DOSSIERS entries that exist on
 * disk, whether or not surveillance is currently running — only `active`
 * says whether they're actually being watched right now.
 */
export interface ProtectionStatus {
  active: boolean;
  monitoredDirectories: string[];
  /** null until Protection has been started at least once this process. */
  autoQuarantine: boolean | null;
}

/** watcher.py detections_rt.json entries. */
export interface ProtectionEvent {
  time: string; // "heure", e.g. "14:32:07"
  fileName: string;
  verdict: Verdict | "erreur";
  confidence: number | null;
  detectionSource: DetectionSource | null;
}

/** auth.py has no role/permission concept — a session is just a
 * verified username (verify() or verify_compte_configure()). */
export interface AuthenticatedUser {
  username: string;
  /** True only for the synthetic local-bypass session
   * (api/dependencies.py::get_current_user, always on for
   * 127.0.0.1/localhost/::1) — never true for a real, cookie-backed
   * login. Drives the topbar's user-area visibility; the security
   * decision itself stays server-side. */
  isLocalSession: boolean;
}
