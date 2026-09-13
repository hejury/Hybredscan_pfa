"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardHeader } from "@/components/ui/Card";
import { UnifiedAnalysisCard } from "@/components/analysis/UnifiedAnalysisCard";
import { AboutAnalysisCard } from "@/components/analysis/AboutAnalysisCard";
import { RecentActivityTable } from "@/components/dashboard/RecentActivityTable";
import { LoadingState } from "@/components/ui/LoadingState";
import { fetchHistory } from "@/lib/api/history";
import { friendlyErrorMessage } from "@/lib/api/errorMessage";
import type { HistoryEntry } from "@/lib/types/backend";

export default function AnalysePage() {
  const [recent, setRecent] = useState<HistoryEntry[] | null>(null);
  const [recentError, setRecentError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchHistory()
      .then((entries) => {
        if (!cancelled) setRecent(entries.slice(0, 5));
      })
      .catch((e) => {
        if (!cancelled) setRecentError(friendlyErrorMessage(e));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-bold text-ink">Analyse</h1>
        <p className="mt-1 text-sm text-ink-secondary">
          Analysez un fichier et, si nécessaire, scannez simultanément un dossier autorisé.
        </p>
      </div>

      <UnifiedAnalysisCard />

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader
            title="Résultats récents"
            action={
              <Link href="/historique" className="text-sm font-bold text-primary hover:underline">
                Voir tout
              </Link>
            }
          />
          {recentError ? (
            <p className="py-6 text-center text-sm text-malicious">{recentError}</p>
          ) : recent === null ? (
            <LoadingState label="Chargement…" />
          ) : (
            <RecentActivityTable entries={recent} />
          )}
        </Card>
        <AboutAnalysisCard />
      </div>
    </div>
  );
}
