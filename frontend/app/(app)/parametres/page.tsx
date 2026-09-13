"use client";

import { useEffect, useState } from "react";
import { User, FolderCog, Info, Server } from "lucide-react";
import { Card, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { useAuth } from "@/lib/auth/AuthProvider";
import { fetchFolderScanConfig } from "@/lib/api/folderScan";
import { fetchHealth, type HealthStatus } from "@/lib/api/health";
import { SUPPORTED_EXTENSIONS } from "@/lib/api/analysis";
import type { FolderScanConfig } from "@/lib/types/backend";

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-border py-2.5 last:border-b-0">
      <span className="text-sm text-ink-secondary">{label}</span>
      <span className="max-w-[60%] text-right text-sm font-bold text-ink break-words">{value}</span>
    </div>
  );
}

export default function ParametresPage() {
  const { user } = useAuth();
  const [scanConfig, setScanConfig] = useState<FolderScanConfig | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [healthError, setHealthError] = useState(false);

  useEffect(() => {
    fetchFolderScanConfig().then(setScanConfig).catch(() => setScanConfig(null));
    fetchHealth()
      .then(setHealth)
      .catch(() => setHealthError(true));
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-bold text-ink">Paramètres</h1>
        <p className="mt-1 text-sm text-ink-secondary">Informations de compte et de configuration, en lecture seule.</p>
      </div>

      <Card>
        <CardHeader icon={<User className="h-4.5 w-4.5" aria-hidden="true" />} title="Compte" />
        <Row label="Identifiant" value={user?.username ?? "—"} />
        <Row label="Mode de session" value="Cookie serveur, en mémoire (8 h)" />
      </Card>

      <Card>
        <CardHeader
          icon={<Server className="h-4.5 w-4.5" aria-hidden="true" />}
          title="État du service"
          action={
            healthError ? (
              <Badge tone="malicious">Indisponible</Badge>
            ) : health ? (
              <Badge tone="healthy">Connecté</Badge>
            ) : (
              <Badge tone="neutral">Vérification…</Badge>
            )
          }
        />
        <Row label="Service" value={health?.service ?? "—"} />
        <Row label="Version" value={health?.version ?? "—"} />
        <Row label="Modèle PE" value={health ? (health.models.pe ? "Chargé" : "Absent") : "—"} />
        <Row label="Modèle PDF" value={health ? (health.models.pdf ? "Chargé" : "Absent") : "—"} />
        <Row label="Modèle DOCX" value={health ? (health.models.docx ? "Chargé" : "Absent") : "—"} />
      </Card>

      <Card>
        <CardHeader icon={<FolderCog className="h-4.5 w-4.5" aria-hidden="true" />} title="Formats pris en charge" />
        <Row label="Analyse de fichier" value={SUPPORTED_EXTENSIONS.join(", ")} />
        <Row label="Scan de dossier" value={scanConfig ? scanConfig.supportedExtensions.join(", ") : "—"} />
        <Row label="Scan de dossier configuré" value={scanConfig ? (scanConfig.configured ? "Oui" : "Non") : "Chargement…"} />
        <Row
          label="Racine(s) autorisée(s)"
          value={scanConfig && scanConfig.allowedRoots.length > 0 ? scanConfig.allowedRoots.join(", ") : "Aucune"}
        />
        <p className="mt-3 text-xs text-ink-muted">
          Cette configuration est définie côté serveur et ne peut pas être modifiée depuis cette interface.
        </p>
      </Card>

      <Card>
        <CardHeader icon={<Info className="h-4.5 w-4.5" aria-hidden="true" />} title="À propos de la détection" />
        <Row label="Exécutables (PE)" value="VirusTotal + modèle IA" />
        <Row label="PDF" value="VirusTotal + modèle IA (prototype de recherche)" />
        <Row label="DOCX" value="VirusTotal + modèle IA (prototype de recherche)" />
        <p className="mt-3 text-xs text-ink-muted">
          Les modèles PDF et DOCX sont des prototypes de recherche : leurs résultats ne doivent pas être considérés
          comme une détection certifiée pour la production. Les paramètres de détection (clés d&apos;API, seuils,
          modèles) sont gérés côté serveur et ne sont pas exposés ici.
        </p>
      </Card>
    </div>
  );
}
