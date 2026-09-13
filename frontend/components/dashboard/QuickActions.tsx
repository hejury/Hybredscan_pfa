import Link from "next/link";
import { ScanSearch, History, ShieldOff, type LucideIcon } from "lucide-react";
import { Card, CardHeader } from "@/components/ui/Card";
import { cn } from "@/lib/utils";

const ACTIONS: { href: string; label: string; icon: LucideIcon }[] = [
  { href: "/analyse", label: "Nouvelle analyse", icon: ScanSearch },
  { href: "/historique", label: "Voir l'historique", icon: History },
  { href: "/quarantaine", label: "Ouvrir la quarantaine", icon: ShieldOff },
];

export function QuickActions() {
  return (
    <Card>
      <CardHeader title="Actions rapides" />
      <div className="flex flex-col gap-2">
        {ACTIONS.map((action) => {
          const Icon = action.icon;
          return (
            <Link
              key={action.href}
              href={action.href}
              className={cn(
                "flex items-center gap-3 rounded-sm border border-border px-3.5 py-3 text-sm font-bold text-ink transition-colors",
                "hover:border-primary hover:bg-primary-soft hover:text-primary-soft-ink",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
              )}
            >
              <Icon className="h-4.5 w-4.5 text-primary" aria-hidden="true" />
              {action.label}
            </Link>
          );
        })}
      </div>
    </Card>
  );
}
