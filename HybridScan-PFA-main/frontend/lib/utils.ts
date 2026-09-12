import { clsx, type ClassValue } from "clsx";
import type { DetectionSource, FileFamily, Verdict } from "@/lib/types/backend";

export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs);
}

/** One confidence formatter used everywhere (design-system MASTER.md
 * §7.10: today's app formats it inconsistently — this fixes that). */
export function formatConfidence(confidence: number | null): string {
  if (confidence === null) return "—";
  return `${(confidence * 100).toFixed(0)} %`;
}

/** One timestamp formatter used everywhere. */
export function formatDateTime(iso: string | null): string {
  if (!iso) return "Non disponible";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatFileSize(bytes: number | null): string {
  if (bytes === null || Number.isNaN(bytes)) return "—";
  if (bytes < 1024) return `${bytes} o`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} Ko`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} Go`;
}

export const VERDICT_LABELS: Record<Verdict, string> = {
  sain: "Sain",
  malveillant: "Malveillant",
  indetermine: "Indéterminé",
};

export const FAMILY_LABELS: Record<FileFamily, string> = {
  pe: "Exécutable (PE)",
  pdf: "PDF",
  doc: "DOC",
  docx: "DOCX",
  inconnu: "Inconnu",
};

export const DETECTION_SOURCE_LABELS: Record<DetectionSource, string> = {
  "1 (signature)": "VirusTotal",
  "2 (IA)": "IA PE",
  "2 (ia_pdf)": "IA PDF (prototype de recherche)",
  "2 (ia_docx)": "IA DOCX (prototype de recherche)",
  "2 (document)": "Vérification par signature",
  "2 (format invalide)": "Format invalide",
};
