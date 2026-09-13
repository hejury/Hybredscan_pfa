"use client";

import { useEffect, useState } from "react";
import { ScanSearch, ShieldAlert, ShieldOff, ShieldCheck } from "lucide-react";
import { Card, CardHeader } from "@/components/ui/Card";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { KpiCard } from "@/components/dashboard/KpiCard";
import { VerdictDonut } from "@/components/dashboard/VerdictDonut";
import { FileTypeBars } from "@/components/dashboard/FileTypeBars";
import { RecentActivityTable } from "@/components/dashboard/RecentActivityTable";
import { QuickActions } from "@/components/dashboard/QuickActions";
import { fetchDashboardSummary, type DashboardSummary } from "@/lib/api/dashboard";
import { friendlyErrorMessage } from "@/lib/api/errorMessage";

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadToken, setLoadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- deliberate: clears a stale error from a previous attempt before this retry's fetch starts; a single clean transition, not a cascading update.
    setError(null);
    fetchDashboardSummary()
      .then((s) => {
        if (!cancelled) setSummary(s);
      })
      .catch((e) => {
        if (!cancelled) setError(friendlyErrorMessage(e));
      });
    return () => {
      cancelled = true;
    };
  }, [loadToken]);

  const header = (
    <div>
      <h1 className="text-xl font-bold text-ink">Tableau de bord</h1>
      <p className="mt-1 text-sm text-ink-secondary">
        Vue d&apos;ensemble de l&apos;activité de détection HybridScan.
      </p>
    </div>
  );

  if (error) {
    return (
      <div className="flex flex-col gap-6">
        {header}
        <Card>
          <ErrorState message={error} onRetry={() => setLoadToken((t) => t + 1)} />
        </Card>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="flex flex-col gap-6">
        {header}
        <Card>
          <LoadingState label="Chargement du tableau de bord…" />
        </Card>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {header}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard icon={ScanSearch} label="Analyses aujourd'hui" value={String(summary.kpis.analysesToday)} tone="primary" />
        <KpiCard icon={ShieldAlert} label="Menaces détectées" value={String(summary.kpis.threatsDetected)} tone="malicious" />
        <KpiCard
          icon={ShieldOff}
          label="Fichiers en quarantaine"
          value={summary.kpis.filesInQuarantine !== null ? String(summary.kpis.filesInQuarantine) : "—"}
          tone="warning"
        />
        <KpiCard
          icon={ShieldCheck}
          label="Protection"
          value={summary.kpis.protectionActive ? "Active" : "Inactive"}
          tone={summary.kpis.protectionActive ? "healthy" : "warning"}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader title="Activité récente" subtitle="Dernières analyses effectuées" />
          <RecentActivityTable entries={summary.recentActivity} />
        </Card>
        <QuickActions />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader title="Répartition des verdicts" />
          <VerdictDonut breakdown={summary.verdictBreakdown} />
        </Card>
        <Card>
          <CardHeader title="Types de fichiers analysés" subtitle="Formats pris en charge : PE, PDF, DOCX" />
          <FileTypeBars breakdown={summary.fileTypeBreakdown} />
        </Card>
      </div>
    </div>
  );
}
