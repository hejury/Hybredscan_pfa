import { Info } from "lucide-react";
import { Card, CardHeader } from "@/components/ui/Card";

const POINTS = [
  "Les fichiers sont analysés statiquement, sans être exécutés.",
  "Une vérification par signature (VirusTotal) est tentée en premier ; en son absence, un modèle d'IA prend le relais selon le type de fichier (PE, PDF, DOCX).",
  "L'analyse IA PDF est un prototype de recherche : des faux positifs ont été observés lors des tests.",
  "L'analyse DOCX repose également sur un modèle expérimental (prototype de recherche), non certifié en production.",
  "Le scan de dossier utilise le même moteur d'analyse : .exe, .dll, .pdf et .docx.",
];

export function AboutAnalysisCard() {
  return (
    <Card>
      <CardHeader icon={<Info className="h-4.5 w-4.5" aria-hidden="true" />} title="À propos de l'analyse" />
      <ul className="flex flex-col gap-3 text-sm text-ink-secondary">
        {POINTS.map((point) => (
          <li key={point} className="flex gap-2">
            <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
            {point}
          </li>
        ))}
      </ul>
    </Card>
  );
}
