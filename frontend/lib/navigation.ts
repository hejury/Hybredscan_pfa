import type { LucideIcon } from "lucide-react";
import { LayoutDashboard, ScanSearch, History, ShieldOff, ShieldCheck, Settings } from "lucide-react";

export interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
}

/**
 * Exact final order per the navigation-cleanup spec: Tableau de bord /
 * Analyse / Historique / Quarantaine / Protection / Paramètres.
 * Deliberately NO standalone "Scan de dossier" entry — folder scanning
 * lives inside /analyse.
 */
export const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Tableau de bord", icon: LayoutDashboard },
  { href: "/analyse", label: "Analyse", icon: ScanSearch },
  { href: "/historique", label: "Historique", icon: History },
  { href: "/quarantaine", label: "Quarantaine", icon: ShieldOff },
  { href: "/protection", label: "Protection", icon: ShieldCheck },
  { href: "/parametres", label: "Paramètres", icon: Settings },
];
