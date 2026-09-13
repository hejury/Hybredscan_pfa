import { ApiError } from "@/lib/api/client";

/**
 * Maps an API failure into a consistent, French, user-facing message —
 * never a raw Python stack trace or exception repr (cahier des charges
 * §11). Most 4xx errors already carry a safe, real French message from
 * the API itself (e.g. "Ce dossier n'est pas autorisé pour l'analyse.")
 * and are passed through as-is; only generic/network-level failures get
 * a fallback message here.
 */
export function friendlyErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 0) return "Impossible de contacter le serveur.";
    if (error.status === 401) return "Votre session a expiré. Veuillez vous reconnecter.";
    if (error.status === 413) return "Le fichier dépasse la taille maximale autorisée.";
    if (error.status >= 500) return "Le service HybridScan est indisponible pour le moment.";
    if (error.message) return error.message;
  }
  return "Une erreur inattendue est survenue.";
}
